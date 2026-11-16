// GitHub 数据层客户端：PAT 首次绑定 + 设备接力配对 + 私有仓库 JSON 读写
// 架构：GitHub Pages 托管前端 → api.github.com 当数据库，零服务器

const TOKEN_KEY = 'ag_token'
const USER_KEY = 'ag_username'

export function getToken() { return localStorage.getItem(TOKEN_KEY) || '' }
export function getUsername() { return localStorage.getItem(USER_KEY) || '' }

export function saveSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token)
  if (username) localStorage.setItem(USER_KEY, username)
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// ===== 配置（由仓库根 config.js 注入）=====
export const GH = {
  owner: (typeof window !== 'undefined' && window.AG_GH_OWNER) || '',
  repo: (typeof window !== 'undefined' && window.AG_GH_REPO) || '',
  dataPath: (typeof window !== 'undefined' && window.AG_GH_DATA_PATH) || 'data/learning-data.json',
  pairRepo: (typeof window !== 'undefined' && window.AG_GH_PAIR_REPO) || '',
  configured: false
}
GH.configured = !!(GH.owner && GH.repo && GH.pairRepo)
const PAIR_TTL = 5 * 60 * 1000 // 配对码有效期 5 分钟

const API = 'https://api.github.com'

function ghHeaders(token, extra = {}) {
  return {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...extra
  }
}

// ===== 用户校验 =====
export async function fetchUser(token) {
  const res = await fetch(`${API}/user`, { headers: ghHeaders(token) })
  if (res.status === 401) throw new Error('令牌无效或已过期')
  if (!res.ok) { const err = new Error('GitHub 连接失败'); err.isNetwork = true; throw err }
  return res.json()
}

// ===== 确保数据仓库存在（首次绑定时自动创建，用户无需手动建仓库）=====
export async function ensureRepo(token) {
  const res = await fetch(`${API}/repos/${GH.owner}/${GH.repo}`, { headers: ghHeaders(token) })
  if (res.status === 200) return { created: false }
  if (res.status === 404) {
    const create = await fetch(`${API}/user/repos`, {
      method: 'POST',
      headers: ghHeaders(token, { 'Content-Type': 'application/json' }),
      body: JSON.stringify({ name: GH.repo, private: true, description: 'My Space 学习中心私有数据仓库（Agent 版自动创建）' })
    })
    if (create.status === 201) return { created: true }
    if (create.status === 403 || create.status === 404) throw new Error('令牌缺少「创建仓库」权限，请重新生成并勾选 Repositories 权限')
    throw new Error('自动创建仓库失败（' + create.status + '）')
  }
  if (res.status === 401) throw new Error('令牌无效或已过期')
  const err = new Error('无法访问仓库'); err.isNetwork = true; throw err
}

// ===== 首次绑定（粘贴 PAT 一次，之后所有设备走接力）=====
export async function bindToken(token) {
  const user = await fetchUser(token)
  await ensureRepo(token)
  saveSession(token, user.login)
  return user.login
}

// ===== 设备接力配对（8 位码，跨设备零粘贴）=====
const PAIR_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
export function genPairCode() {
  const arr = new Uint8Array(8)
  crypto.getRandomValues(arr)
  return Array.from(arr, b => PAIR_CHARS[b % PAIR_CHARS.length]).join('')
}

async function pairKey(code) {
  const enc = new TextEncoder()
  const km = await crypto.subtle.importKey('raw', enc.encode(code), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: enc.encode('ag-pair-' + GH.owner), iterations: 100000, hash: 'SHA-256' }, km, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt'])
}

function b64buf(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
}
function bufB64(b64) {
  const bin = atob(b64)
  const arr = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i)
  return arr
}

async function pairFileMeta(code) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(code + ':' + GH.owner))
  const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('')
  return `handshake/pair-${hash.slice(0, 20)}.json`
}

// 旧设备：把 token 用配对码加密写入公开中转仓库（密文 + 用后即删 + 5 分钟过期）
export async function authorizePair(code) {
  const token = getToken()
  if (!token) throw new Error('本设备未登录')
  const key = await pairKey(code)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const enc = new TextEncoder()
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(JSON.stringify({ t: token, u: getUsername() })))
  const path = await pairFileMeta(code)
  const body = { c: b64buf(ct), iv: b64buf(iv), at: new Date().toISOString(), from: getUsername() }
  const url = `${API}/repos/${GH.owner}/${GH.pairRepo}/contents/${path}`
  const head = await fetch(url, { headers: ghHeaders(token) })
  const payload = { message: 'pair: authorize new device', content: btoa(unescape(encodeURIComponent(JSON.stringify(body)))) }
  if (head.status === 200) payload.sha = (await head.json()).sha
  const res = await fetch(url, { method: 'PUT', headers: ghHeaders(token, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
  if (!res.ok) throw new Error('写入配对信息失败（' + res.status + '）· 请确认令牌对仓库有 Contents 写权限')
  return true
}

// 新设备（无令牌）：匿名轮询公开中转仓库的配对文件，解密后获得 token 并删除文件
export async function pollPair(code) {
  const key = await pairKey(code)
  const path = await pairFileMeta(code)
  const url = `${API}/repos/${GH.owner}/${GH.pairRepo}/contents/${path}`
  // 匿名 GET（新设备尚无令牌，公开仓库可匿名读，限速内完成）
  const res = await fetch(url, { headers: { 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' } })
  if (res.status === 404) return { status: 'pending' }
  if (res.status === 403) return { status: 'ratelimit' }
  if (!res.ok) return { status: 'pending' }
  const j = await res.json()
  let body
  try { body = JSON.parse(decodeURIComponent(escape(atob(j.content.replace(/\n/g, ''))))) } catch { return { status: 'pending' } }
  if (Date.now() - Date.parse(body.at) > PAIR_TTL) return { status: 'expired' }
  let pt
  try {
    const dec = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: bufB64(body.iv) }, key, bufB64(body.c))
    pt = JSON.parse(new TextDecoder().decode(dec))
  } catch { return { status: 'pending' } }
  // 解密成功：用新 token 删除配对文件（用后即删）
  const del = await fetch(url, {
    method: 'DELETE',
    headers: ghHeaders(pt.t, { 'Content-Type': 'application/json' }),
    body: JSON.stringify({ message: 'pair: consumed', sha: j.sha })
  })
  return { status: 'ok', token: pt.t, username: pt.u, cleaned: del.ok }
}

// ===== 私有仓库 JSON 读写（Contents API）=====
function b64encode(str) { return btoa(unescape(encodeURIComponent(str))) }
function b64decode(b64) { return decodeURIComponent(escape(atob(b64.replace(/\n/g, '')))) }

export async function pullData() {
  const token = getToken()
  const url = `${API}/repos/${GH.owner}/${GH.repo}/contents/${GH.dataPath}`
  const res = await fetch(url, { headers: ghHeaders(token) })
  if (res.status === 404) return { exists: false, data: null }
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效，请重新登录') }
  if (!res.ok) { const err = new Error('拉取失败'); err.isNetwork = true; throw err }
  const j = await res.json()
  return { exists: true, sha: j.sha, data: JSON.parse(b64decode(j.content)) }
}

export async function pushData(dataObj, retry = true) {
  const token = getToken()
  const url = `${API}/repos/${GH.owner}/${GH.repo}/contents/${GH.dataPath}`
  const content = b64encode(JSON.stringify(dataObj, null, 2))
  let sha
  const head = await fetch(url, { headers: ghHeaders(token) })
  if (head.status === 200) sha = (await head.json()).sha
  else if (head.status !== 404) { const err = new Error('同步前检查失败'); err.isNetwork = true; throw err }

  const res = await fetch(url, {
    method: 'PUT',
    headers: ghHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      message: `sync: ${new Date().toISOString().slice(0, 19).replace('T', ' ')}`,
      content,
      ...(sha ? { sha } : {})
    })
  })
  if (res.status === 409 && retry) return pushData(dataObj, false)
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效，请重新登录') }
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    const err = new Error(`上传失败（${res.status}）${body.slice(0, 60)}`)
    err.isNetwork = true
    throw err
  }
  return { saved: true }
}

// GitHub 数据层客户端（多用户自助版）：PAT 首次绑定 + 设备接力配对 + 私有仓库 JSON 读写
// 每个用户绑定自己的 GitHub：数据/令牌/仓库全在用户自己账号下，天然隔离

const TOKEN_KEY = 'ag_token'
const USER_KEY = 'ag_username'
const OWNER_KEY = 'ag_owner'

export function getToken() { return localStorage.getItem(TOKEN_KEY) || '' }
export function getUsername() { return localStorage.getItem(USER_KEY) || '' }
export function getOwner() { return localStorage.getItem(OWNER_KEY) || getUsername() || '' }

export function saveSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token)
  if (username) {
    localStorage.setItem(USER_KEY, username)
    localStorage.setItem(OWNER_KEY, username)
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(OWNER_KEY)
}

// ===== 配置 =====
const cfg = typeof window !== 'undefined' ? window : {}
export const GH = {
  repo: cfg.AG_GH_REPO || 'travel-tracker-data',            // 私有数据仓（自动创建于用户账号下）
  dataPath: cfg.AG_GH_DATA_PATH || 'data/learning-data.json',
  pairRepo: cfg.AG_GH_PAIR_REPO || 'travel-tracker-handshake', // 公开接力中转仓（自动创建于用户账号下）
  configured: !!(cfg.AG_GH_REPO || 'travel-tracker-data')
}

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

// ===== 确保仓库存在（首次绑定时自动创建）=====
async function ensureOneRepo(token, owner, name, isPrivate) {
  const res = await fetch(`${API}/repos/${owner}/${name}`, { headers: ghHeaders(token) })
  if (res.status === 200) return { created: false }
  if (res.status === 404) {
    const create = await fetch(`${API}/user/repos`, {
      method: 'POST',
      headers: ghHeaders(token, { 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        name,
        private: isPrivate,
        description: isPrivate
          ? 'My Space 学习中心私有数据仓库（Agent 版自动创建）'
          : 'My Space 学习中心设备接力中转仓库（内容全程 AES 加密、用后即删）'
      })
    })
    if (create.status === 201) return { created: true }
    if (create.status === 403 || create.status === 404) throw new Error('令牌缺少「创建仓库」权限，请生成时勾选 Repositories 权限')
    throw new Error('自动创建仓库失败（' + create.status + '）')
  }
  if (res.status === 401) throw new Error('令牌无效或已过期')
  const err = new Error('无法访问仓库'); err.isNetwork = true; throw err
}

// ===== 首次绑定（粘贴 PAT 一次；之后所有设备走接力/密码登录）=====
export async function bindToken(token, syncPassword) {
  const user = await fetchUser(token)          // 自动识别用户身份，无需输入用户名
  const owner = user.login
  await ensureOneRepo(token, owner, GH.repo, true)       // 私有数据仓
  await ensureOneRepo(token, owner, GH.pairRepo, false)  // 公开接力中转仓
  saveSession(token, user.login)
  if (syncPassword) await saveCredential(token, owner, syncPassword)
  return user.login
}

// ===== 密码登录（任意设备直接登录，无需其他设备参与）=====
// 原理：同步密码作为加密钥匙，解开存在公开中转仓里的令牌密文
const CRED_PATH = 'auth/credentials.json'

async function passKey(password, saltBuf) {
  const enc = new TextEncoder()
  const km = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: saltBuf, iterations: 310000, hash: 'SHA-256' },
    km, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )
}

// 已登录设备：用同步密码加密令牌，存入公开中转仓（凭密码+用户名即可从任何设备取回）
export async function saveCredential(token, owner, password) {
  if (!token || !owner) throw new Error('本设备未登录')
  if (typeof password !== 'string' || password.length < 6) throw new Error('同步密码至少 6 位（建议 8 位以上并包含字母与数字）')
  await ensureOneRepo(token, owner, GH.pairRepo, false).catch(() => {})
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const key = await passKey(password, salt)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const enc = new TextEncoder()
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(JSON.stringify({ t: token, u: owner })))
  const body = { c: b64buf(ct), iv: b64buf(iv), salt: b64buf(salt), at: new Date().toISOString() }
  const url = `${API}/repos/${owner}/${GH.pairRepo}/contents/${CRED_PATH}`
  const head = await fetch(url, { headers: ghHeaders(token) })
  const payload = { message: 'auth: update credential', content: btoa(unescape(encodeURIComponent(JSON.stringify(body)))) }
  if (head.status === 200) payload.sha = (await head.json()).sha
  const res = await fetch(url, { method: 'PUT', headers: ghHeaders(token, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
  if (!res.ok) throw new Error('保存密码凭据失败（' + res.status + '）')
  return true
}

// 任意设备：输用户名+同步密码 → 匿名拉取密文 → 解密得令牌 → 登录
export async function loginWithPassword(owner, password) {
  if (!/^[A-Za-z0-9-]{1,39}$/.test(owner || '')) throw new Error('请输入正确的 GitHub 用户名')
  if (!password) throw new Error('请输入同步密码')
  const url = `${API}/repos/${owner}/${GH.pairRepo}/contents/${CRED_PATH}`
  const res = await fetch(url, { headers: { 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' } })
  if (res.status === 404) throw new Error('该账号尚未设置密码登录（先在任一已登录设备上设置，或改用接力/首次绑定）')
  if (res.status === 403) throw new Error('GitHub 匿名请求额度已用完，请稍后再试或改用接力登录')
  if (!res.ok) throw new Error('拉取凭据失败（' + res.status + '）')
  const j = await res.json()
  let body
  try { body = JSON.parse(decodeURIComponent(escape(atob(j.content.replace(/\n/g, ''))))) } catch { throw new Error('凭据文件异常') }
  let pt
  try {
    const key = await passKey(password, bufB64(body.salt))
    const dec = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: bufB64(body.iv) }, key, bufB64(body.c))
    pt = JSON.parse(new TextDecoder().decode(dec))
  } catch { throw new Error('同步密码错误') }
  await fetchUser(pt.t) // 校验令牌仍有效
  saveSession(pt.t, pt.u)
  return pt.u
}

// ===== 设备接力配对（8 位码，跨设备零粘贴）=====
const PAIR_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
const PAIR_TTL = 5 * 60 * 1000
export function genPairCode() {
  const arr = new Uint8Array(8)
  crypto.getRandomValues(arr)
  return Array.from(arr, b => PAIR_CHARS[b % PAIR_CHARS.length]).join('')
}

async function pairKey(code, owner) {
  const enc = new TextEncoder()
  const km = await crypto.subtle.importKey('raw', enc.encode(code), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: enc.encode('ag-pair-' + owner), iterations: 100000, hash: 'SHA-256' }, km, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt'])
}

function b64buf(buf) { return btoa(String.fromCharCode(...new Uint8Array(buf))) }
function bufB64(b64) {
  const bin = atob(b64)
  const arr = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i)
  return arr
}

async function pairFileMeta(code, owner) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(code + ':' + owner))
  const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('')
  return `handshake/pair-${hash.slice(0, 20)}.json`
}

// 旧设备：把 token 用配对码加密写入自己的公开中转仓（仓不存在时自动补建，兼容早期绑定）
export async function authorizePair(code) {
  const token = getToken()
  const owner = getOwner()
  if (!token || !owner) throw new Error('本设备未登录')
  try { await ensureOneRepo(token, owner, GH.pairRepo, false) } catch (e) { /* 已存在或无权限时交由后续写入报具体错误 */ }
  const key = await pairKey(code, owner)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const enc = new TextEncoder()
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(JSON.stringify({ t: token, u: getUsername() })))
  const path = await pairFileMeta(code, owner)
  const body = { c: b64buf(ct), iv: b64buf(iv), at: new Date().toISOString(), from: getUsername() }
  const url = `${API}/repos/${owner}/${GH.pairRepo}/contents/${path}`
  const head = await fetch(url, { headers: ghHeaders(token) })
  const payload = { message: 'pair: authorize new device', content: btoa(unescape(encodeURIComponent(JSON.stringify(body)))) }
  if (head.status === 200) payload.sha = (await head.json()).sha
  const res = await fetch(url, { method: 'PUT', headers: ghHeaders(token, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
  if (!res.ok) throw new Error('写入配对信息失败（' + res.status + '）· 请确认令牌对仓库有 Contents 写权限')
  return true
}

// 新设备（无令牌）：匿名轮询指定账号下的公开中转仓，解密后获得 token 并删除文件
export async function pollPair(code, owner) {
  const key = await pairKey(code, owner)
  const path = await pairFileMeta(code, owner)
  const url = `${API}/repos/${owner}/${GH.pairRepo}/contents/${path}`
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
  const del = await fetch(url, {
    method: 'DELETE',
    headers: ghHeaders(pt.t, { 'Content-Type': 'application/json' }),
    body: JSON.stringify({ message: 'pair: consumed', sha: j.sha })
  })
  return { status: 'ok', token: pt.t, username: pt.u, cleaned: del.ok }
}

// ===== 私有仓库 JSON 读写（Contents API，支持多文件）=====
function b64encode(str) { return btoa(unescape(encodeURIComponent(str))) }
function b64decode(b64) { return decodeURIComponent(escape(atob(b64.replace(/\n/g, '')))) }

export async function pullData(path = 'data/learning-data.json') {
  const token = getToken()
  const owner = getOwner()
  const url = `${API}/repos/${owner}/${GH.repo}/contents/${path}`
  const res = await fetch(url, { headers: ghHeaders(token) })
  if (res.status === 404) return { exists: false, data: null }
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效，请重新登录') }
  if (!res.ok) { const err = new Error('拉取失败'); err.isNetwork = true; throw err }
  const j = await res.json()
  return { exists: true, sha: j.sha, data: JSON.parse(b64decode(j.content)) }
}

export async function pushData(dataObj, retry = true, path = 'data/learning-data.json') {
  const token = getToken()
  const owner = getOwner()
  const url = `${API}/repos/${owner}/${GH.repo}/contents/${path}`
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
  if (res.status === 409 && retry) return pushData(dataObj, false, path)
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效，请重新登录') }
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    const err = new Error(`上传失败（${res.status}）${body.slice(0, 60)}`)
    err.isNetwork = true
    throw err
  }
  return { saved: true }
}

// ===== 旧模块（地图/地铁/西语练习等）数据同步：独立 misc 文件，与学习数据互不覆盖 =====
export const MISC_PATH = 'data/misc.json'
export async function pullMisc() { return pullData(MISC_PATH) }
export async function pushMisc(dataObj) { return pushData(dataObj, true, MISC_PATH) }


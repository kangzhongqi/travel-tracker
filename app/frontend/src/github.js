// GitHub 数据层客户端：OAuth 设备授权码登录 + 私有仓库 JSON 读写
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

// ===== 配置（由仓库根 config.js 注入，改配置无需重新构建）=====
export const GH = {
  clientId: (typeof window !== 'undefined' && window.AG_GH_CLIENT_ID) || '',
  owner: (typeof window !== 'undefined' && window.AG_GH_OWNER) || '',
  repo: (typeof window !== 'undefined' && window.AG_GH_REPO) || '',
  dataPath: (typeof window !== 'undefined' && window.AG_GH_DATA_PATH) || 'data/learning-data.json',
  configured: false
}
GH.configured = !!(GH.clientId && GH.owner && GH.repo)

const API = 'https://api.github.com'

function ghHeaders(token, extra = {}) {
  return {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...extra
  }
}

// ===== 设备授权码流程（Device Flow，RFC 8628）=====
export async function requestCode() {
  const res = await fetch('https://github.com/login/device/code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ client_id: GH.clientId, scope: 'repo' })
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`无法发起设备授权（${res.status}）${body.slice(0, 80)}`)
  }
  return res.json() // { device_code, user_code, verification_uri, expires_in, interval }
}

export async function pollToken(deviceCode, intervalSec, onSlowDown) {
  let interval = (intervalSec || 5) * 1000
  while (true) {
    await new Promise(r => setTimeout(r, interval))
    const res = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        client_id: GH.clientId,
        device_code: deviceCode,
        grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
      })
    })
    const data = await res.json().catch(() => ({}))
    if (data.access_token) return data.access_token
    if (data.error === 'authorization_pending') continue
    if (data.error === 'slow_down') { interval += 5000; onSlowDown && onSlowDown(); continue }
    // expired_token / unsupported_grant_type / incorrect_client_credentials / ...
    const err = new Error(data.error_description || data.error || '授权失败')
    err.code = data.error
    throw err
  }
}

// ===== 已有 token 的校验 / 用户信息 =====
export async function fetchUser(token) {
  const res = await fetch(`${API}/user`, { headers: ghHeaders(token) })
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效') }
  if (!res.ok) { const err = new Error('GitHub 连接失败'); err.isNetwork = true; throw err }
  return res.json() // { login, ... }
}

// ===== 私有仓库 JSON 读写（Contents API）=====
function b64encode(str) {
  return btoa(unescape(encodeURIComponent(str)))
}
function b64decode(b64) {
  return decodeURIComponent(escape(atob(b64.replace(/\n/g, ''))))
}

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
  if (res.status === 409 && retry) return pushData(dataObj, false) // sha 冲突，重取再试
  if (res.status === 401) { clearSession(); throw new Error('令牌已失效，请重新登录') }
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    const err = new Error(`上传失败（${res.status}）${body.slice(0, 60)}`)
    err.isNetwork = true
    throw err
  }
  return { saved: true }
}

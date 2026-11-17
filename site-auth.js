/* My Space 全站登录徽章 + 旧模块数据自动云同步（原生 JS 零依赖）
   已登录时：
   · 右上角显示用户名与登出
   · 自动上传：本地打卡/练习数据变化后数秒内推送 GitHub 私有仓库
   · 自动下载：打开页面时补全本地缺失的数据（新设备一键恢复）
   凭证与 Vue 版共享同一 localStorage */
;(function () {
  var MISC_PATH = 'data/misc.json'
  var REPO = window.AG_GH_REPO || 'travel-tracker-data'
  // 全站旧模块数据键（与 sync.html 权威清单一致；ag* 学习键由学习中心单独同步）
  var KEYS = [
    'visited', 'china_travel_visited', 'china_travel_v2',
    'county_visited_v2', 'county_visited_v4',
    'beijing_subway_visited', 'bj_subway_v2', 'subway_checked',
    'spanish_verb_hist', 'sp_daily', 'sp_history', 'lang_test_h',
    'fin_exam_state_v1', 'fin_wrongbook_v1', 'fin_history_v1', 'fin_srs_v1',
    'agv_mark_v2', 'es_srs_v1'
  ]
  var API = 'https://api.github.com'
  var gh = { token: '', owner: '' }

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn)
    else fn()
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }
  function b64e(s) { return btoa(unescape(encodeURIComponent(s))) }

  function collect() {
    var d = {}
    for (var i = 0; i < KEYS.length; i++) {
      var v = localStorage.getItem(KEYS[i])
      if (v != null) d[KEYS[i]] = v
    }
    return d
  }

  function apiHeaders(extra) {
    return Object.assign({
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Authorization': 'Bearer ' + gh.token
    }, extra || {})
  }

  function pullMisc() {
    return fetch(API + '/repos/' + gh.owner + '/' + REPO + '/contents/' + MISC_PATH, { headers: apiHeaders() })
      .then(function (r) {
        if (r.status === 404) return null
        if (!r.ok) throw new Error('pull ' + r.status)
        return r.json()
      })
      .then(function (j) {
        if (!j) return null
        try { return { sha: j.sha, data: JSON.parse(decodeURIComponent(escape(atob((j.content || '').replace(/\n/g, ''))))) } }
        catch (e) { return null }
      })
  }

  function pushMisc(mergedData) {
    var url = API + '/repos/' + gh.owner + '/' + REPO + '/contents/' + MISC_PATH
    return fetch(url, { headers: apiHeaders() })
      .then(function (h) {
        var payload = {
          message: 'sync-misc: ' + new Date().toISOString().slice(0, 19).replace('T', ' '),
          content: b64e(JSON.stringify({ data: mergedData, updatedAt: new Date().toISOString() }, null, 2))
        }
        if (h.status === 200) return h.json().then(function (j) {
          payload.sha = j.sha
          return fetch(url, { method: 'PUT', headers: apiHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        })
        return fetch(url, { method: 'PUT', headers: apiHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
      })
      .then(function (r) { if (!r.ok) throw new Error('push ' + r.status) })
  }

  // —— 自动同步核心 ——
  var lastSnap = null
  var snapTimer = null
  var syncBusy = false

  function snapshotChanged() {
    var s = JSON.stringify(collect())
    if (s === lastSnap) return false
    lastSnap = s
    return true
  }

  function uploadNow() {
    if (syncBusy || !gh.token) return Promise.resolve(false)
    syncBusy = true
    var local = collect()
    return pullMisc()
      .then(function (remote) {
        var merged = (remote && remote.data && remote.data.data) ? JSON.parse(JSON.stringify(remote.data.data)) : {}
        Object.keys(local).forEach(function (k) { merged[k] = local[k] }) // 本地值优先
        if (remote && JSON.stringify(merged) === JSON.stringify(remote.data.data)) return false
        return pushMisc(merged).then(function () { return true })
      })
      .catch(function () { return false })
      .then(function (ok) { syncBusy = false; flashBadge(ok); return ok })
  }

  function downloadIfMissing() {
    if (!gh.token) return
    pullMisc().then(function (remote) {
      if (!remote || !remote.data || !remote.data.data) return
      var wrote = 0
      Object.keys(remote.data.data).forEach(function (k) {
        if (KEYS.indexOf(k) >= 0 && localStorage.getItem(k) == null) {
          localStorage.setItem(k, remote.data.data[k])
          wrote++
        }
      })
      lastSnap = JSON.stringify(collect())
      if (wrote > 0 && !sessionStorage.getItem('ag_misc_reloaded')) {
        sessionStorage.setItem('ag_misc_reloaded', '1')
        location.reload()
      }
    }).catch(function () {})
  }

  function startAutoSync() {
    if (snapshotChanged()) {
      clearTimeout(snapTimer)
      snapTimer = setTimeout(uploadNow, 2500)
    }
  }

  // —— 徽章 UI ——
  var wrap
  function flashBadge(ok) {
    if (!wrap) return
    wrap.style.transition = 'box-shadow .3s'
    wrap.style.boxShadow = ok ? '0 0 14px rgba(52,211,153,.8)' : 'none'
    setTimeout(function () { wrap.style.boxShadow = 'none' }, 900)
  }

  function render() {
    var token = localStorage.getItem('ag_token')
    var uname = localStorage.getItem('ag_username') || ''
    gh.token = token || ''
    gh.owner = localStorage.getItem('ag_owner') || uname || ''
    wrap.innerHTML = ''
    if (token && uname) {
      var chip = document.createElement('a')
      chip.href = 'study.html'
      chip.title = '账号与同步中心'
      chip.innerHTML = '👤 ' + esc(uname)
      chip.style.cssText = 'pointer-events:auto;text-decoration:none;cursor:pointer;font-size:13px;font-weight:600;line-height:1;padding:8px 14px;border-radius:999px;background:rgba(17,24,39,.88);color:#34d399;border:1px solid rgba(16,185,129,.55);white-space:nowrap;max-width:44vw;overflow:hidden;text-overflow:ellipsis;display:inline-block'
      var cloud = document.createElement('span')
      cloud.textContent = '☁'
      cloud.title = '立即同步到云端'
      cloud.style.cssText = 'pointer-events:auto;cursor:pointer;user-select:none;font-size:13px;padding:8px 11px;border-radius:999px;background:rgba(17,24,39,.88);color:#34d399;border:1px solid #1f2937;line-height:1'
      cloud.onclick = function (e) { e.preventDefault(); uploadNow() }
      var out = document.createElement('span')
      out.textContent = '⎋'
      out.title = '退出登录'
      out.style.cssText = 'pointer-events:auto;cursor:pointer;user-select:none;font-size:13px;padding:8px 11px;border-radius:999px;background:rgba(17,24,39,.88);color:#9ca3af;border:1px solid #1f2937;line-height:1'
      out.onclick = function (e) {
        e.preventDefault()
        localStorage.removeItem('ag_token')
        localStorage.removeItem('ag_username')
        localStorage.removeItem('ag_owner')
        gh.token = ''; gh.owner = ''
        render()
      }
      wrap.appendChild(chip)
      wrap.appendChild(cloud)
      wrap.appendChild(out)
      // 登录态：启动自动同步
      lastSnap = JSON.stringify(collect())
      downloadIfMissing()
      if (!startAutoSync._timer) startAutoSync._timer = setInterval(startAutoSync, 3000)
    } else {
      var login = document.createElement('a')
      login.href = 'study.html'
      login.textContent = '☁️ 登录'
      login.title = '登录 · 接力 / 密码 / 首次绑定'
      login.style.cssText = 'pointer-events:auto;text-decoration:none;cursor:pointer;font-size:13px;font-weight:600;padding:8px 14px;border-radius:999px;background:rgba(16,185,129,.14);color:#34d399;border:1px solid rgba(16,185,129,.55);line-height:1'
      wrap.appendChild(login)
    }
  }

  ready(function () {
    wrap = document.createElement('div')
    wrap.id = 'site-auth-badge'
    wrap.style.cssText = 'position:fixed;top:10px;right:10px;z-index:2147483000;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;display:flex;align-items:center;gap:6px;max-width:76vw;pointer-events:none'
    document.body.appendChild(wrap)
    render()
    window.addEventListener('storage', function (e) {
      if (['ag_token', 'ag_username', 'ag_owner'].indexOf(e.key) >= 0) render()
      else if (KEYS.indexOf(e.key) >= 0 && gh.token) startAutoSync()
    })
  })
})()

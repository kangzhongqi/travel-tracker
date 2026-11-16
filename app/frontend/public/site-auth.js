/* My Space 全站登录徽章（原生 JS 零依赖）
   旧模块页面引入本文件后，右上角显示统一登录状态：
   已登录：👤 用户名（点击进学习中心）+ 登出；未登录：☁️ 登录
   凭证与 Vue 版共享同一 localStorage（同域名自动通用） */
;(function () {
  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn)
    else fn()
  }
  ready(function () {
    var wrap = document.createElement('div')
    wrap.id = 'site-auth-badge'
    wrap.style.cssText = [
      'position:fixed', 'top:10px', 'right:10px', 'z-index:2147483000',
      'font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif',
      'display:flex', 'align-items:center', 'gap:6px', 'max-width:70vw', 'pointer-events:none'
    ].join(';')

    function esc(s) {
      return String(s).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
      })
    }

    function render() {
      var token = localStorage.getItem('ag_token')
      var uname = localStorage.getItem('ag_username') || ''
      wrap.innerHTML = ''
      if (token && uname) {
        var chip = document.createElement('a')
        chip.href = 'study.html'
        chip.title = '进入学习中心'
        chip.innerHTML = '👤 ' + esc(uname)
        chip.style.cssText = [
          'pointer-events:auto', 'text-decoration:none', 'cursor:pointer',
          'font-size:13px', 'font-weight:600', 'line-height:1',
          'padding:8px 14px', 'border-radius:999px',
          'background:rgba(17,24,39,.88)', 'color:#34d399',
          'border:1px solid rgba(16,185,129,.55)', 'white-space:nowrap',
          'max-width:52vw', 'overflow:hidden', 'text-overflow:ellipsis', 'display:inline-block'
        ].join(';')
        var out = document.createElement('span')
        out.textContent = '⎋'
        out.title = '退出登录'
        out.style.cssText = [
          'pointer-events:auto', 'cursor:pointer', 'user-select:none',
          'font-size:13px', 'padding:8px 11px', 'border-radius:999px',
          'background:rgba(17,24,39,.88)', 'color:#9ca3af',
          'border:1px solid #1f2937', 'line-height:1'
        ].join(';')
        out.onclick = function (e) {
          e.preventDefault()
          localStorage.removeItem('ag_token')
          localStorage.removeItem('ag_username')
          localStorage.removeItem('ag_owner')
          render()
        }
        wrap.appendChild(chip)
        wrap.appendChild(out)
      } else {
        var login = document.createElement('a')
        login.href = 'study.html'
        login.textContent = '☁️ 登录'
        login.title = '登录 · 接力 / 密码 / 首次绑定'
        login.style.cssText = [
          'pointer-events:auto', 'text-decoration:none', 'cursor:pointer',
          'font-size:13px', 'font-weight:600', 'padding:8px 14px',
          'border-radius:999px', 'background:rgba(16,185,129,.14)',
          'color:#34d399', 'border:1px solid rgba(16,185,129,.55)', 'line-height:1'
        ].join(';')
        wrap.appendChild(login)
      }
    }

    render()
    // 多标签页间登录状态变化时同步徽章
    window.addEventListener('storage', function (e) {
      if (['ag_token', 'ag_username', 'ag_owner'].indexOf(e.key) >= 0) render()
    })
    document.body.appendChild(wrap)
  })
})()

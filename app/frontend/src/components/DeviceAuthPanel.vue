<script setup>
import { ref, defineEmits, onMounted, onUnmounted } from 'vue'
import { GH, genPairCode, pollPair, bindToken, saveSession, fetchUser } from '../github.js'
import { store } from '../store.js'

const emit = defineEmits(['close'])

const mode = ref('pair') // pair（新设备接力） | bind（首次绑定）
const ghUsername = ref('')
const pairCode = ref('')
const pairState = ref('idle') // idle | waiting | ok | error
const pairErr = ref('')
const patInput = ref('')
const bindState = ref('idle') // idle | busy | ok | error
const bindErr = ref('')
let timer = null
let cancelled = false

onMounted(() => { pairCode.value = genPairCode() })

function startPoll() {
  const owner = ghUsername.value.trim()
  if (!/^[A-Za-z0-9-]{1,39}$/.test(owner)) {
    pairErr.value = '请先输入你的 GitHub 用户名'
    return
  }
  pairErr.value = ''
  pairState.value = 'waiting'
  timer = setInterval(async () => {
    try {
      const r = await pollPair(pairCode.value, owner)
      if (cancelled) return
      if (r.status === 'ok') {
        saveSession(r.token, r.username)
        const u = await fetchUser(r.token)
        store.username = u.login
        store.cloud = 'on'
        pairState.value = 'ok'
        clearInterval(timer)
        setTimeout(() => emit('close'), 800)
      } else if (r.status === 'expired') {
        pairState.value = 'error'
        pairErr.value = '配对码已过期（5 分钟），请重新发起'
        clearInterval(timer)
      }
    } catch (e) { /* 网络波动时继续等待 */ }
  }, 10000)
}

function restartPair() {
  pairCode.value = genPairCode()
  pairState.value = 'idle'
  pairErr.value = ''
}

async function doBind() {
  const t = patInput.value.trim()
  if (t.length < 20) { bindErr.value = '请粘贴完整的访问令牌（token）'; return }
  bindState.value = 'busy'
  bindErr.value = ''
  try {
    const login = await bindToken(t)
    patInput.value = ''
    store.username = login
    store.cloud = 'on'
    bindState.value = 'ok'
    setTimeout(() => emit('close'), 800)
  } catch (e) {
    bindState.value = 'error'
    bindErr.value = e.message
  }
}

onUnmounted(() => { cancelled = true; clearInterval(timer) })
</script>

<template>
  <div class="auth-modal" @click.self="emit('close')">
    <div class="auth-box">
      <template v-if="mode === 'pair'">
        <h3>{{ pairState === 'ok' ? '🤝 接力成功' : '接力登录' }}</h3>
        <div class="mode" v-if="pairState === 'idle'">
          已在任一设备登录过？输入你的 GitHub 用户名并生成配对码，把这台设备接进来。
        </div>
        <template v-if="pairState === 'idle'">
          <input v-model="ghUsername" placeholder="你的 GitHub 用户名" maxlength="39" @keyup.enter="startPoll">
          <div class="devcode">{{ pairCode }}</div>
          <div class="mode" style="text-align:center">
            在<b>已登录的设备</b>上打开本站 → 学习中心 → 点「🤝 授权新设备」→ 输入上面的码
          </div>
          <div class="auth-err" v-if="pairErr">{{ pairErr }}</div>
          <button class="btn" style="width:100%;margin-top:12px" @click="startPoll">开始等待授权 →</button>
          <div class="mode" style="text-align:center;margin-top:10px">
            <span class="hint" style="cursor:pointer" @click="mode = 'bind'">第一次使用？做一次首次绑定（需一次性粘贴 GitHub 令牌）→</span>
          </div>
        </template>
        <template v-else-if="pairState === 'waiting'">
          <div class="devcode">{{ pairCode }}</div>
          <div class="pulse" style="text-align:center">⏳ 正在等待另一台设备确认授权…</div>
          <div class="mode" style="text-align:center;margin-top:8px">每 10 秒自动检测，授权后本设备自动登录 · 配对码 5 分钟内有效</div>
          <button class="btn ghost" style="width:100%;margin-top:14px" @click="restartPair">换个码重试</button>
        </template>
        <template v-else-if="pairState === 'ok'">
          <div style="text-align:center;padding:16px 0">
            <div style="font-size:48px">🤝</div>
            <div class="mode" style="margin-top:8px">已接管 <b>{{ store.username }}</b> 的学习数据 · 即将自动同步</div>
          </div>
        </template>
        <template v-else>
          <div class="auth-err">{{ pairErr }}</div>
          <button class="btn" style="width:100%" @click="restartPair">重新发起</button>
        </template>
      </template>

      <template v-else>
        <h3>首次绑定（仅此一次）</h3>
        <div class="mode">
          点 <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener" style="color:var(--accent2);font-weight:700">生成新令牌 →</a>
          （令牌名随意，如 myspace）；Resource owner 选<b>你自己</b>；Repository access 选「<b>All repositories</b>」；
          权限勾 <b>Administration: Read and write</b>（建仓）与 <b>Contents: Read and write</b>（存数据）→ 生成后复制，粘贴到下面。<br>
          绑定后自动在你的账号下创建<b>私有数据仓</b>与<b>接力中转仓</b>，你的身份由令牌自动识别，无需输入密码；
          以后所有新设备用接力码登录，<b>不再粘贴任何字符</b>。数据只存在你自己的 GitHub 里。
        </div>
        <input v-model="patInput" type="password" placeholder="粘贴 github_pat_ 开头的令牌（仅存本机浏览器）" style="font-size:12px">
        <div class="auth-err">{{ bindErr }}</div>
        <button class="btn" style="width:100%" :disabled="bindState === 'busy'" @click="doBind">
          {{ bindState === 'busy' ? '正在绑定并创建仓库…' : '绑定并初始化' }}
        </button>
        <div class="mode" style="text-align:center;margin-top:10px">
          <span class="hint" style="cursor:pointer" @click="mode = 'pair'">已有其他设备登录过？返回接力登录 →</span>
        </div>
      </template>

      <div style="text-align:center;margin-top:14px">
        <span class="hint" style="cursor:pointer" @click="emit('close')">暂不登录，单机使用 →</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.devcode{font-size:32px;font-weight:900;letter-spacing:6px;text-align:center;padding:16px;border:2px dashed var(--accent);border-radius:12px;margin:12px 0;cursor:pointer;color:var(--accent2);user-select:all}
.pulse{font-size:12px;color:var(--accent2);animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
</style>

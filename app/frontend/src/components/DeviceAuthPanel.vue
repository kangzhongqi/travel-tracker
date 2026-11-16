<script setup>
import { ref, defineEmits, onMounted, onUnmounted } from 'vue'
import { GH, genPairCode, pollPair, bindToken, loginWithPassword, saveSession, fetchUser } from '../github.js'
import { store } from '../store.js'

const emit = defineEmits(['close'])

const mode = ref('pair') // pair（接力） | password（密码直接登录） | bind（首次绑定）

// —— 接力 ——
const ghUsername = ref('')
const pairCode = ref('')
const pairState = ref('idle')
const pairErr = ref('')
let timer = null
let cancelled = false

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

// —— 密码直接登录 ——
const pwOwner = ref('')
const pwPass = ref('')
const pwState = ref('idle') // idle | busy | ok
const pwErr = ref('')

async function doPasswordLogin() {
  pwState.value = 'busy'
  pwErr.value = ''
  try {
    const u = await loginWithPassword(pwOwner.value.trim(), pwPass.value)
    pwPass.value = ''
    store.username = u
    store.cloud = 'on'
    pwState.value = 'ok'
    setTimeout(() => emit('close'), 800)
  } catch (e) {
    pwState.value = 'idle'
    pwErr.value = e.message
  }
}

// —— 首次绑定 ——
const patInput = ref('')
const bindPass = ref('')
const bindState = ref('idle')
const bindErr = ref('')

async function doBind() {
  const t = patInput.value.trim()
  if (t.length < 20) { bindErr.value = '请粘贴完整的访问令牌（token）'; return }
  if (bindPass.value && bindPass.value.length < 6) { bindErr.value = '同步密码至少 6 位'; return }
  bindState.value = 'busy'
  bindErr.value = ''
  try {
    const login = await bindToken(t, bindPass.value || null)
    patInput.value = ''
    bindPass.value = ''
    store.username = login
    store.cloud = 'on'
    bindState.value = 'ok'
    setTimeout(() => emit('close'), 800)
  } catch (e) {
    bindState.value = 'error'
    bindErr.value = e.message
  }
}

onMounted(() => { pairCode.value = genPairCode() })
onUnmounted(() => { cancelled = true; clearInterval(timer) })
</script>

<template>
  <div class="auth-modal" @click.self="emit('close')">
    <div class="auth-box">
      <div class="mode" style="margin-bottom:14px;display:flex;gap:6px;flex-wrap:wrap">
        <span class="mtab" :class="{ on: mode === 'pair' }" @click="mode = 'pair'">🤝 接力登录</span>
        <span class="mtab" :class="{ on: mode === 'password' }" @click="mode = 'password'">🔑 密码登录</span>
        <span class="mtab" :class="{ on: mode === 'bind' }" @click="mode = 'bind'">🚀 首次绑定</span>
      </div>

      <!-- 接力 -->
      <template v-if="mode === 'pair'">
        <h3>{{ pairState === 'ok' ? '🤝 接力成功' : '接力登录' }}</h3>
        <div class="mode" v-if="pairState === 'idle'">手边有已登录的设备？生成配对码，在旧设备上输码确认即可。</div>
        <template v-if="pairState === 'idle'">
          <input v-model="ghUsername" placeholder="你的 GitHub 用户名" maxlength="39" @keyup.enter="startPoll">
          <div class="devcode">{{ pairCode }}</div>
          <div class="mode" style="text-align:center">在<b>已登录的设备</b>上打开本站 → 学习中心 → 点「🤝 授权新设备」→ 输入上面的码</div>
          <div class="auth-err" v-if="pairErr">{{ pairErr }}</div>
          <button class="btn" style="width:100%;margin-top:12px" @click="startPoll">开始等待授权 →</button>
          <div class="mode" style="text-align:center;margin-top:10px"><span class="hint" style="cursor:pointer" @click="mode = 'password'">旧设备不在手边？用密码直接登录 →</span></div>
        </template>
        <template v-else-if="pairState === 'waiting'">
          <div class="devcode">{{ pairCode }}</div>
          <div class="pulse" style="text-align:center">⏳ 正在等待另一台设备确认授权…</div>
          <div class="mode" style="text-align:center;margin-top:8px">每 10 秒自动检测 · 配对码 5 分钟内有效</div>
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

      <!-- 密码登录 -->
      <template v-else-if="mode === 'password'">
        <h3>{{ pwState === 'ok' ? '✅ 登录成功' : '密码直接登录' }}</h3>
        <div class="mode" v-if="pwState !== 'ok'">
          输入 GitHub 用户名 + 同步密码，任意设备直接登录，<b>无需其他设备参与</b>。
          同步密码可在首次绑定时设置，或之后在学习中心顶栏「🔒 密码登录」里设置。
        </div>
        <template v-if="pwState !== 'ok'">
          <input v-model="pwOwner" placeholder="你的 GitHub 用户名" maxlength="39" @keyup.enter="doPasswordLogin">
          <input v-model="pwPass" type="password" placeholder="同步密码" maxlength="64" @keyup.enter="doPasswordLogin">
          <div class="auth-err">{{ pwErr }}</div>
          <button class="btn" style="width:100%" :disabled="pwState === 'busy'" @click="doPasswordLogin">
            {{ pwState === 'busy' ? '正在登录…' : '登录' }}
          </button>
          <div class="mode" style="text-align:center;margin-top:10px"><span class="hint" style="cursor:pointer" @click="mode = 'pair'">有已登录设备在旁？接力更快 →</span></div>
        </template>
        <template v-else>
          <div style="text-align:center;padding:16px 0">
            <div style="font-size:48px">✅</div>
            <div class="mode" style="margin-top:8px">欢迎回来，<b>{{ store.username }}</b> · 即将自动同步</div>
          </div>
        </template>
      </template>

      <!-- 首次绑定 -->
      <template v-else>
        <h3>首次绑定（仅此一次）</h3>
        <div class="mode">
          点 <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener" style="color:var(--accent2);font-weight:700">生成新令牌 →</a>
          （令牌名随意；Resource owner 选<b>你自己</b>；Repository access 选「<b>All repositories</b>」；
          权限勾 <b>Administration: Read and write</b> + <b>Contents: Read and write</b>）→ 粘贴到下面。<br>
          下方同步密码<b>可选但强烈建议设置</b>：设了之后，以后任何设备输「用户名+密码」即可直接登录。
        </div>
        <input v-model="patInput" type="password" placeholder="粘贴 github_pat_ 开头的令牌（仅存本机浏览器）" style="font-size:12px">
        <input v-model="bindPass" type="password" placeholder="同步密码（可选 · ≥6 位 · 用于任何设备密码直登）" maxlength="64">
        <div class="auth-err">{{ bindErr }}</div>
        <button class="btn" style="width:100%" :disabled="bindState === 'busy'" @click="doBind">
          {{ bindState === 'busy' ? '正在绑定并创建仓库…' : '绑定并初始化' }}
        </button>
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
.mtab{font-size:12px;font-weight:700;padding:6px 12px;border-radius:999px;border:1px solid var(--border);background:var(--card2);color:var(--text2);cursor:pointer}
.mtab.on{background:rgba(16,185,129,.15);color:var(--accent2);border-color:var(--accent)}
</style>

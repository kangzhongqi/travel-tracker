<script setup>
import { ref, defineEmits, onUnmounted } from 'vue'
import { GH, requestCode, pollToken, fetchUser, saveSession } from '../github.js'
import { store } from '../store.js'

const emit = defineEmits(['close'])

const step = ref('intro') // intro | waiting | success | error
const userCode = ref('')
const verifyUrl = ref('')
const intervalSec = ref(5)
const errMsg = ref('')
const errMsgZh = {
  expired_token: '授权码已过期，请重新发起',
  unsupported_grant_type: '此 OAuth App 尚未开通设备授权（需 GitHub 批准），请先用过渡方式',
  incorrect_client_credentials: 'Client ID 配置有误，请检查 config.js'
}
let cancelled = false
let deviceCode = ''

async function start() {
  if (!GH.configured) { errMsg.value = '尚未配置 Client ID（config.js），请按网站指引完成 GitHub 三步配置'; step.value = 'error'; return }
  try {
    const r = await requestCode()
    deviceCode = r.device_code
    userCode.value = r.user_code
    verifyUrl.value = r.verification_uri
    intervalSec.value = r.interval || 5
    step.value = 'waiting'
    const token = await pollToken(deviceCode, r.interval, null)
    if (cancelled) return
    const user = await fetchUser(token)
    saveSession(token, user.login)
    store.username = user.login
    store.cloud = 'on'
    step.value = 'success'
    setTimeout(() => emit('close'), 900)
  } catch (e) {
    if (cancelled) return
    errMsg.value = errMsgZh[e.code] || e.message
    step.value = 'error'
  }
}

function copyCode() {
  navigator.clipboard?.writeText(userCode.value).catch(() => {})
}

function restart() { step.value = 'intro'; errMsg.value = '' }

onUnmounted(() => { cancelled = true })
</script>

<template>
  <div class="auth-modal" @click.self="emit('close')">
    <div class="auth-box">
      <template v-if="step === 'intro'">
        <h3>登录学习中心</h3>
        <div class="mode">
          通过 GitHub 账号授权，学习数据将加密保存在你的私有仓库中，任何设备登录后自动同步。
          无需记忆额外密码，也不用粘贴任何长字符。
        </div>
        <button class="btn" style="width:100%" @click="start">🔐 用 GitHub 账号授权登录</button>
        <div style="text-align:center;margin-top:12px">
          <span class="hint" style="cursor:pointer" @click="emit('close')">暂不登录，单机使用 →</span>
        </div>
      </template>

      <template v-else-if="step === 'waiting'">
        <h3>在任意设备完成授权</h3>
        <div class="mode">
          第 1 步：打开下面链接（可用本机浏览器或手机）<br>
          第 2 步：输入这串授权码，点击「Authorize」授权
        </div>
        <a :href="verifyUrl" target="_blank" rel="noopener" class="btn" style="display:block;text-align:center;text-decoration:none;margin-bottom:14px">
          {{ verifyUrl }} ↗
        </a>
        <div class="devcode" @click="copyCode" title="点击复制">{{ userCode }}</div>
        <div class="mode" style="text-align:center">{{ userCode ? '点击授权码可复制 · ' : '' }}授权后会自动完成登录…</div>
        <div class="pulse" style="text-align:center;margin-top:10px">⏳ 正在等待你在 GitHub 完成授权</div>
        <button class="btn ghost" style="width:100%;margin-top:14px" @click="emit('close')">取消</button>
      </template>

      <template v-else-if="step === 'success'">
        <div style="text-align:center;padding:20px 0">
          <div style="font-size:52px">✅</div>
          <h3 style="margin-top:10px">登录成功</h3>
          <div class="mode">欢迎回来，{{ store.username }} · 即将开始自动同步</div>
        </div>
      </template>

      <template v-else>
        <h3>登录失败</h3>
        <div class="auth-err" style="min-height:auto;margin:10px 0 16px">{{ errMsg }}</div>
        <button class="btn" style="width:100%" @click="restart">重试</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.devcode{font-size:30px;font-weight:900;letter-spacing:4px;text-align:center;padding:16px;border:2px dashed var(--accent);border-radius:12px;margin-bottom:12px;cursor:pointer;color:var(--accent2);user-select:all}
.pulse{font-size:12px;color:var(--accent2);animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
</style>

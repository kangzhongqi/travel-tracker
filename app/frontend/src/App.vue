<script setup>
import { ref, onMounted, computed } from 'vue'
import DeviceAuthPanel from './components/DeviceAuthPanel.vue'
import PairAuthorizePanel from './components/PairAuthorizePanel.vue'
import PassSetupPanel from './components/PassSetupPanel.vue'
import FinanceModule from './components/FinanceModule.vue'
import SpanishModule from './components/SpanishModule.vue'
import { store, uploadCloud, pullCloud, setSyncMsg, LS_KEYS, lsGet } from './store.js'
import { GH, getToken, getUsername, clearSession, fetchUser } from './github.js'

const tab = ref('finance')
const showAuth = ref(false)
const showPair = ref(false)
const showPass = ref(false)
const logged = computed(() => store.cloud === 'on' && store.username)
const configured = computed(() => GH.configured)

onMounted(async () => {
  store.username = getUsername()
  if (!getToken() || !GH.configured) { store.cloud = 'off'; store.username = ''; return }
  try {
    const u = await fetchUser(getToken())
    store.cloud = 'on'
    store.username = u.login
    // 登录态打开页面：自动拉取云端最新
    await pullCloud(false)
  } catch (e) {
    store.cloud = 'off'
    store.username = ''
  }
})

function logout() {
  clearSession()
  store.username = ''
  store.cloud = 'off'
  setSyncMsg('已退出登录')
}

async function manualUpload() { await uploadCloud(true) }
async function manualPull() { await pullCloud(true) }

function onAuthClose() {
  showAuth.value = false
  // 新登录：立即拉取云端
  if (logged.value) pullCloud(false)
}

// 供导航栏提示
function learnStatus() {
  const w = lsGet(LS_KEYS.finance.wrong, []).length
  const m = Object.keys(lsGet(LS_KEYS.spanish.mark, {})).length
  return { w, m }
}
</script>

<template>
  <div>
    <div class="topbar">
      <a class="back" href="./">← 首页</a>
      <h1><span class="grad">🤖 学习中心</span></h1>
      <span class="badge">Agent 版 · Vue + GitHub</span>
      <div class="userbox">
        <template v-if="logged">
          <span class="uname">👤 {{ store.username }}</span>
          <button class="btn ghost" @click="manualUpload">⬆️ 立即上传</button>
          <button class="btn ghost" @click="manualPull">⬇️ 云端拉取</button>
          <button class="btn ghost" @click="showPair = true">🤝 授权新设备</button>
          <button class="btn ghost" @click="showPass = true">🔒 同步密码</button>
          <button class="btn ghost" @click="logout">登出</button>
        </template>
        <template v-else-if="configured">
          <button class="btn" @click="showAuth = true">登录 · 接力/首次绑定</button>
        </template>
        <template v-else>
          <span class="offbadge">☁️ 待配置（见首页指引）</span>
        </template>
      </div>
      <div class="sync-msg" v-if="store.syncMsg">{{ store.syncMsg }}</div>
    </div>
    <p class="sub">
      <template v-if="logged">已通过 GitHub 授权 · 学习数据自动同步到你的私有仓库 · 任何设备登录即恢复</template>
      <template v-else-if="configured">用 GitHub 账号一键授权登录，跨设备自动同步；不登录也可单机使用（数据存本机浏览器）</template>
      <template v-else>云同步待配置：完成首页的三步 GitHub 配置后，即可在任何设备授权登录并自动同步 · 当前可正常单机使用</template>
    </p>

    <DeviceAuthPanel v-if="showAuth" @close="onAuthClose" />
    <PairAuthorizePanel v-if="showPair" @close="showPair = false" />
    <PassSetupPanel v-if="showPass" @close="showPass = false" />

    <div class="tabs">
      <button class="tab" :class="{ on: tab === 'finance' }" @click="tab = 'finance'">💰 金融知识测评</button>
      <button class="tab" :class="{ on: tab === 'spanish' }" @click="tab = 'spanish'">🇪🇸 西语 A2 复习</button>
    </div>

    <FinanceModule v-show="tab === 'finance'" />
    <SpanishModule v-show="tab === 'spanish'" />

    <p class="note">🤖 Agent 版架构：Vue 3 前端（GitHub Pages 托管）+ GitHub 私有仓库数据层（零服务器）· 接力码登录 · 数据自动同步<br>
    All data stored in your own private GitHub repo · No third-party servers · No tracking</p>
  </div>
</template>

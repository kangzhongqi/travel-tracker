<script setup>
import { ref, onMounted, computed } from 'vue'
import DeviceAuthPanel from './components/DeviceAuthPanel.vue'
import PairAuthorizePanel from './components/PairAuthorizePanel.vue'
import PassSetupPanel from './components/PassSetupPanel.vue'
import { store } from './store.js'
import { GH, getToken, getUsername, clearSession, fetchUser, pullData, pullMisc, pushMisc } from './github.js'
import { VOCAB } from './data.js'

const showAuth = ref(false)
const showPair = ref(false)
const showPass = ref(false)
const logged = computed(() => store.cloud === 'on' && store.username)

// 与 site-auth.js 保持一致的全站数据键
const SITE_KEYS = [
  'visited', 'china_travel_visited', 'china_travel_v2',
  'county_visited_v2', 'county_visited_v4',
  'beijing_subway_visited', 'bj_subway_v2', 'subway_checked',
  'spanish_verb_hist', 'sp_daily', 'sp_history', 'lang_test_h',
  'fin_exam_state_v1', 'fin_wrongbook_v1', 'fin_history_v1', 'fin_srs_v1',
  'agv_mark_v2', 'es_srs_v1'
]

// ===== 云端数据状态 =====
const miscInfo = ref(null)
const learnInfo = ref(null)
const busy = ref('')
const syncMsg = ref('')

async function refreshCloud() {
  if (!logged.value) return
  busy.value = '加载中…'
  try {
    const misc = await pullMisc()
    miscInfo.value = misc && misc.exists
      ? { keys: Object.keys(misc.data.data || {}).length, updatedAt: (misc.data.updatedAt || '').replace('T', ' ').slice(0, 16) }
      : { keys: 0, updatedAt: '—' }
  } catch (e) { miscInfo.value = { error: e.message } }
  try {
    const learn = await pullData()
    if (learn && learn.exists) {
      learnInfo.value = { finance: (learn.data.finance?.wrongSet || []).length, spanish: Object.keys(learn.data.spanish?.VMARK || {}).length }
      store._learnRaw = learn.data
    } else { learnInfo.value = null; store._learnRaw = null }
  } catch (e) { learnInfo.value = null; store._learnRaw = null }
  busy.value = ''
}

function lsGet(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d } catch { return d } }

// ===== 全站数据上传/恢复 =====
async function uploadAll() {
  if (!logged.value) return
  busy.value = '上传中…'
  const data = {}
  SITE_KEYS.forEach(k => { const v = localStorage.getItem(k); if (v != null) data[k] = v })
  try {
    const remote = await pullMisc()
    const merged = remote && remote.exists ? { ...(remote.data.data || {}), ...data } : data
    await pushMisc({ data: merged, updatedAt: new Date().toISOString() })
    syncMsg.value = '✅ 已上传 ' + Object.keys(merged).length + ' 项数据'
  } catch (e) { syncMsg.value = '❌ ' + e.message }
  busy.value = ''
  refreshCloud()
}

async function pullAll() {
  if (!logged.value) return
  busy.value = '拉取中…'
  try {
    const remote = await pullMisc()
    if (!remote || !remote.exists || !remote.data.data) { syncMsg.value = '云端暂无数据'; busy.value = ''; return }
    let wrote = 0
    Object.keys(remote.data.data).forEach(k => {
      if (SITE_KEYS.includes(k) && localStorage.getItem(k) == null) {
        localStorage.setItem(k, remote.data.data[k]); wrote++
      }
    })
    syncMsg.value = wrote ? ('✅ 恢复了 ' + wrote + ' 项，刷新页面后生效') : '本机数据已是最新（缺失项为 0）'
  } catch (e) { syncMsg.value = '❌ ' + e.message }
  busy.value = ''
}

// ===== 旧版数据一键迁移 =====
// v1 索引 → 合体版 id 映射（v1 与 v2 重复的 2 题映射到 v2 等价题）
const FIN_MAP = i => (i === 0 ? 'q001' : i === 12 ? 'q031' : 'v1-' + String(i + 1).padStart(2, '0'))
const OLD_KEYS = { wrong: 'agfin_wrong', hist: 'agfin_hist', mark: 'agv_mark' }

function scanMigration() {
  const items = []
  const wrong = lsGet(OLD_KEYS.wrong, [])
  const hist = lsGet(OLD_KEYS.hist, [])
  const mark = lsGet(OLD_KEYS.mark, {})
  const learnRaw = store._learnRaw
  if (wrong.length) items.push({ name: '金融错题本', n: wrong.length, from: '本机旧版' })
  if (hist.length) items.push({ name: '金融测评记录', n: hist.length, from: '本机旧版' })
  if (Object.keys(mark).length) items.push({ name: '西语词汇标记', n: Object.keys(mark).length, from: '本机旧版' })
  if (learnRaw) {
    const lw = (learnRaw.finance?.wrongSet || []).length
    const ls = Object.keys(learnRaw.spanish?.VMARK || {}).length
    if (lw) items.push({ name: '金融错题（云端旧版）', n: lw, from: 'learning-data.json' })
    if (ls) items.push({ name: '西语标记（云端旧版）', n: ls, from: 'learning-data.json' })
  }
  return items
}
const migItems = ref([])
const migDone = ref('')

function doMigrate() {
  const finWrong = lsGet('fin_wrongbook_v1', [])
  const finHist = lsGet('fin_history_v1', [])
  const markV2 = lsGet('agv_mark_v2', {})
  const srs = lsGet('fin_srs_v1', {})
  let added = 0
  const addWrong = i => {
    const id = FIN_MAP(i)
    if (!finWrong.includes(id)) { finWrong.push(id); srs[id] = srs[id] || { due: Date.now(), streak: 0 }; added++ }
  }
  const addMark = (i, lv) => {
    const w = VOCAB[+i] && VOCAB[+i][0]
    if (w && !markV2[w]) { markV2[w] = lv; added++ }
  }
  // 1) 本机旧键
  lsGet(OLD_KEYS.wrong, []).forEach(addWrong)
  lsGet(OLD_KEYS.hist, []).forEach(r => {
    finHist.unshift({ d: r.d, m: (r.m || '旧版') + '（迁移）', s: r.s, t: r.t, rate: Math.round(r.s / r.t * 100) }); added++
  })
  Object.entries(lsGet(OLD_KEYS.mark, {})).forEach(([i, lv]) => addMark(i, lv))
  // 2) 云端旧版
  const learnRaw = store._learnRaw
  if (learnRaw) {
    ;(learnRaw.finance?.wrongSet || []).forEach(addWrong)
    ;(learnRaw.finance?.histArr || []).forEach(r => {
      finHist.unshift({ d: r.d, m: (r.m || '旧版') + '（云端迁移）', s: r.s, t: r.t, rate: Math.round(r.s / r.t * 100) }); added++
    })
    Object.entries(learnRaw.spanish?.VMARK || {}).forEach(([i, lv]) => addMark(i, lv))
  }
  localStorage.setItem('fin_wrongbook_v1', JSON.stringify(finWrong.slice(0, 120)))
  localStorage.setItem('fin_history_v1', JSON.stringify(finHist.slice(0, 30)))
  localStorage.setItem('fin_srs_v1', JSON.stringify(srs))
  localStorage.setItem('agv_mark_v2', JSON.stringify(markV2))
  // 3) 清理旧键（Vue 学习版已退役，防止数据分叉）
  localStorage.removeItem('agfin_wrong')
  localStorage.removeItem('agfin_hist')
  localStorage.removeItem('agv_mark')
  migDone.value = added ? '✅ 已并入合体版（新增 ' + added + ' 条）并清理旧键' : '无需迁移：没有发现旧版数据'
  migItems.value = []
}

onMounted(async () => {
  store.username = getUsername()
  if (!getToken() || !GH.configured) { store.cloud = 'off'; store.username = ''; return }
  try {
    const u = await fetchUser(getToken())
    store.cloud = 'on'
    store.username = u.login
    await refreshCloud()
    migItems.value = scanMigration()
  } catch (e) {
    store.cloud = e.isNetwork ? 'off' : 'on'
    if (e.isNetwork) store.username = ''
  }
})

function onAuthClose() {
  showAuth.value = false
  if (logged.value) { refreshCloud().then(() => { migItems.value = scanMigration() }) }
}

function logout() {
  clearSession()
  store.username = ''
  store.cloud = 'off'
  miscInfo.value = null
  migItems.value = []
}
</script>

<template>
  <div>
    <div class="topbar">
      <a class="back" href="./">← 首页</a>
      <h1><span class="grad">🛰️ 账号与同步中心</span></h1>
      <span class="badge">Agent 版 · 全站统一</span>
      <div class="userbox">
        <template v-if="logged">
          <span class="uname">👤 {{ store.username }}</span>
          <button class="btn ghost" @click="showPair = true">🤝 授权新设备</button>
          <button class="btn ghost" @click="showPass = true">🔒 同步密码</button>
          <button class="btn ghost" @click="logout">登出</button>
        </template>
        <template v-else-if="GH.configured">
          <button class="btn" @click="showAuth = true">登录 · 接力 / 密码 / 首次绑定</button>
        </template>
      </div>
    </div>
    <p class="sub">全站唯一账号中心：登录一次全站通用 · 学习与打卡数据自动同步 · 新设备接力或密码直登</p>

    <DeviceAuthPanel v-if="showAuth" @close="onAuthClose" />
    <PairAuthorizePanel v-if="showPair" @close="showPair = false" />
    <PassSetupPanel v-if="showPass" @close="showPass = false" />

    <div class="card">
      <h3>📚 学习入口</h3>
      <div class="hint">学习功能已全部收拢到以下两个合体版模块，本页只管账号与数据同步：</div>
      <div class="links">
        <a class="mod" href="agent-finance.html">💰 金融测评 · 合体版<span>114 题 8 章 · 考试/练习/错题复习/12 篇深度讲解</span></a>
        <a class="mod" href="agent-spanish.html">🇪🇸 西语 A2 · 合体版<span>272 词 · 20 张语法卡 · 114 动词变位 · 遗忘曲线</span></a>
      </div>
    </div>

    <div class="card" v-if="logged">
      <h3>☁️ 数据同步</h3>
      <div class="hint" style="margin-bottom:10px">覆盖全站 18 项数据键（地图/地铁打卡、金融错题/续考/复习队列、西语标记/复习队列等），登录设备间自动同步；此处可手动全量操作。</div>
      <div class="statrow">
        <span>云端 misc.json：<b v-if="miscInfo && !miscInfo.error">{{ miscInfo.keys }} 项 · {{ miscInfo.updatedAt }}</b><b v-else-if="miscInfo && miscInfo.error" style="color:var(--danger)">{{ miscInfo.error }}</b><b v-else>—</b></span>
        <span v-if="learnInfo">旧版 learning-data.json：金融 {{ learnInfo.finance }} · 西语 {{ learnInfo.spanish }}（可迁移）</span>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px">
        <button class="btn" :disabled="!!busy" @click="uploadAll">⬆️ 上传全部到云端</button>
        <button class="btn ghost" :disabled="!!busy" @click="pullAll">⬇️ 恢复本机缺失项</button>
        <span v-if="busy" class="hint">{{ busy }}</span>
        <span v-if="syncMsg" class="okmsg">{{ syncMsg }}</span>
      </div>
    </div>
    <div class="card" v-else>
      <h3>☁️ 数据同步</h3>
      <div class="hint">登录后此处可查看云端状态、手动上传 / 恢复全站数据。</div>
    </div>

    <div class="card" v-if="logged">
      <h3>🔄 旧版数据迁移</h3>
      <template v-if="migItems.length">
        <div class="hint" style="margin-bottom:8px">检测到旧学习版（Vue 学习中心 / v1 单机版）的数据：</div>
        <div class="statrow">
          <span v-for="it in migItems" :key="it.name">{{ it.name }}：<b>{{ it.n }}</b> 条（{{ it.from }}）</span>
        </div>
        <button class="btn" style="margin-top:10px" @click="doMigrate">一键迁移到合体版 →</button>
        <div class="hint" style="margin-top:6px">规则：错题与词汇标记并入合体版错题本/复习队列（自动去重），测评记录并入历史，迁移后清理旧键防止两套数据分叉。</div>
      </template>
      <template v-else>
        <div class="hint">{{ migDone || '未检测到旧版学习数据（或已迁移完毕），无需操作。' }}</div>
      </template>
      <div v-if="migDone" class="okmsg" style="margin-top:8px">{{ migDone }}</div>
    </div>

    <div class="card">
      <h3>❓ 常见问题</h3>
      <div class="hint faq">
        <p><b>换新设备怎么登录？</b> 打开本页 → 登录 → 「接力登录」（在已登录设备输 8 位码）或「密码登录」（输 GitHub 用户名 + 同步密码），无需粘贴任何长字符。</p>
        <p><b>数据存在哪？</b> 全部在你自己的 GitHub 私有仓库（travel-tracker-data），本站零服务器、零第三方。</p>
        <p><b>旧版页面还在吗？</b> agent-finance-v1 / agent-spanish-v1 保留可访问但不再维护；地图、地铁、西语辅助工具（听写跟读 / 每日一句 / 动词练习）照常使用并自动同步。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.links{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}
.mod{flex:1;min-width:240px;display:block;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.4);border-radius:14px;padding:16px;color:var(--accent2);text-decoration:none;font-weight:800;font-size:14px}
.mod span{display:block;font-size:12px;color:var(--text2);font-weight:400;margin-top:6px}
.statrow{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--text2)}
.statrow b{color:var(--accent2)}
.okmsg{font-size:12.5px;color:var(--accent2)}
.faq p{margin-bottom:8px}
.faq b{color:var(--accent2)}
</style>

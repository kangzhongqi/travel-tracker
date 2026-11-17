<script setup>
import { ref, onMounted } from 'vue'
import DeviceAuthPanel from './components/DeviceAuthPanel.vue'
import PassSetupPanel from './components/PassSetupPanel.vue'
import { GH, getToken, getUsername, clearSession, fetchUser } from './github.js'

const showAuth = ref(false)
const showPass = ref(false)

const sections = [
  {
    title: '🤖 学习中心（主力）', cards: [
      { icon: '💰', name: '金融测评 · 合体版', desc: '114 题 8 章 · 60 分钟考试断点续考 · 错题遗忘曲线 · 12 篇深度讲解', tag: '主力', href: 'agent-finance.html', hot: true },
      { icon: '🇪🇸', name: '西语 A2 · 合体版', desc: '272 词 · 20 语法卡 · 114 动词变位与练习 · 句子训练/每日一句 · 遗忘曲线', tag: '主力', href: 'agent-spanish.html', hot: true },
      { icon: '🛰️', name: '账号与同步中心', desc: '登录/接力/密码 · 全站数据云同步 · 旧版数据一键迁移', tag: '账号', href: 'study.html' }
    ]
  },
  {
    title: '🗺️ Travel Maps', cards: [
      { icon: '🇨🇳', name: '中国足迹 · 地级市', desc: '360+ 地级行政区打卡', tag: '地图', href: '中国旅行足迹地图.html' },
      { icon: '🗺️', name: '中国足迹 · 县级', desc: '2,800+ 县级行政区打卡', tag: '地图', href: '中国旅行足迹-县级.html' },
      { icon: '🚇', name: '北京地铁打卡', desc: '27 条线路 · 410 站点', tag: '地图', href: '北京地铁打卡地图.html' }
    ]
  },
  {
    title: '📱 Mobile', cards: [
      { icon: '🇨🇳', name: '中国足迹 · iPhone', desc: '地级市触屏优化版', tag: '移动端', href: '中国旅行足迹-iPhone.html' },
      { icon: '🚇', name: '北京地铁 · iPhone', desc: '地铁触屏优化版', tag: '移动端', href: '北京地铁打卡-iPhone.html' }
    ]
  }
]

const cloud = ref('checking')
const username = ref('')

async function check() {
  username.value = getUsername()
  if (!GH.configured) { cloud.value = 'notconfig'; return }
  if (!getToken()) { cloud.value = 'off'; return }
  try {
    const u = await fetchUser(getToken())
    username.value = u.login
    cloud.value = 'on'
  } catch (e) {
    cloud.value = 'off'
    username.value = ''
  }
}
onMounted(check)

function onAuthClose() {
  showAuth.value = false
  check()
}

function logout() {
  clearSession()
  username.value = ''
  cloud.value = 'off'
}
</script>

<template>
  <div>
    <div class="header">
      <div class="avatar">🌏</div>
      <h1>My Space</h1>
      <p>探索 · 记录 · 学习</p>
    </div>

    <div v-if="cloud === 'on'" class="cloudbar">
      ✅ 已登录 <b>{{ username }}</b> · 学习数据自动同步中 · <a href="study.html">进入学习中心 →</a>
      <a class="lgout" style="margin-left:10px" @click="showPass = true">🔒 同步密码</a>
      <span class="lgout" @click="logout">退出</span>
    </div>
    <div v-else-if="cloud === 'off'" class="cloudbar">
      ☁️ 全站统一登录：<a href="javascript:void(0)" @click="showAuth = true" style="font-weight:800">点此登录</a>（接力 / 密码 / 首次绑定三选一，登录一次全站通用）
      · 首次使用需一次性绑定
      <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">生成令牌→粘贴</a>，约 2 分钟；
      不登录也可单机使用；任何人也可用自己的 GitHub 账号开启自己的同步
    </div>
    <div v-else class="cloudbar">
      ☁️ 正在检查云同步状态…
    </div>

    <DeviceAuthPanel v-if="showAuth" @close="onAuthClose" />
    <PassSetupPanel v-if="showPass" @close="showPass = false" />

    <div v-for="sec in sections" :key="sec.title" class="section">
      <div class="section-title">{{ sec.title }}</div>
      <div class="cards">
        <a v-for="c in sec.cards" :key="c.name" class="pcard" :class="{ hot: c.hot }" :href="c.href">
          <span class="icon">{{ c.icon }}</span>
          <h3>{{ c.name }}</h3>
          <div class="desc">{{ c.desc }}</div>
          <span class="tag">{{ c.tag }}</span>
        </a>
      </div>
    </div>

    <div class="footer">
      <p>All data stored locally in your browser · No tracking · No uploads</p>
      <p class="vbadge">🤖 My Space · Vue 3 + GitHub 数据层（零服务器）· Agent 版</p>
    </div>
  </div>
</template>

<style scoped>
.header{padding:36px 0 32px;text-align:center}
.header .avatar{width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,var(--accent),#059669);display:inline-flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:16px}
.header h1{font-size:26px;font-weight:800;letter-spacing:-.5px;background:linear-gradient(135deg,#e5e7eb 20%,var(--accent2) 80%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.header p{color:var(--text2);font-size:13px;margin-top:6px}
.cloudbar{border:1px solid var(--accent);background:rgba(16,185,129,.08);color:var(--accent2);border-radius:12px;padding:10px 16px;font-size:12.5px;margin-bottom:26px;line-height:1.7}
.cloudbar.off{border-color:var(--border);background:var(--card);color:var(--text2)}
.cloudbar code{background:rgba(16,185,129,.12);padding:1px 6px;border-radius:6px;font-size:11.5px}
.cloudbar a{color:var(--accent2);font-weight:700}
.cloudbar .lgout{float:right;color:var(--text2);cursor:pointer;margin-left:12px}
.cloudbar .lgout:hover{color:var(--danger)}
.section{margin-bottom:36px}
.section-title{font-size:13px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;padding-left:2px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:760px){.cards{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.cards{grid-template-columns:1fr}}
.pcard{position:relative;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;text-decoration:none;color:inherit;transition:all .3s cubic-bezier(.4,0,.2,1);overflow:hidden}
.pcard::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:0;transition:opacity .3s}
.pcard:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 8px 30px rgba(0,0,0,.3),0 0 60px rgba(16,185,129,.1);background:var(--card2)}
.pcard:hover::after{opacity:1}
.pcard .icon{font-size:32px;margin-bottom:10px;display:block}
.pcard h3{font-size:15px;font-weight:700;margin-bottom:4px}
.pcard .desc{font-size:12px;color:var(--text2);line-height:1.5}
.pcard .tag{display:inline-block;margin-top:10px;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:600;letter-spacing:.2px;background:rgba(16,185,129,.08);color:var(--accent2)}
.pcard.hot{border-color:var(--accent);background:linear-gradient(180deg,rgba(16,185,129,.09),var(--card))}
.footer{margin-top:40px;padding-top:24px;border-top:1px solid var(--border);text-align:center}
.footer p{font-size:11px;color:var(--text3);line-height:1.8}
.footer .vbadge{margin-top:4px}
</style>

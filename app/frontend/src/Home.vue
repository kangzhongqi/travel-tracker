<script setup>
import { ref, onMounted } from 'vue'
import { GH, getToken, getUsername, clearSession, fetchUser } from './github.js'

const sections = [
  {
    title: '🗺️ Travel Maps', cards: [
      { icon: '🇨🇳', name: '中国足迹 · 地级市', desc: '360+ 地级行政区打卡', tag: '地图', href: '中国旅行足迹地图.html' },
      { icon: '🗺️', name: '中国足迹 · 县级', desc: '2,800+ 县级行政区打卡', tag: '地图', href: '中国旅行足迹-县级.html' },
      { icon: '🚇', name: '北京地铁打卡', desc: '27 条线路 · 410 站点', tag: '地图', href: '北京地铁打卡地图.html' }
    ]
  },
  {
    title: '📚 Language', cards: [
      { icon: '🇪🇸', name: '西语动词变位', desc: '现在时 · 简单过去时 · 120+ 动词', tag: '学习', href: 'spanish-verbs.html' },
      { icon: '📖', name: '西语 A2 手册', desc: '语法速查 · 260+词汇 · 听写跟读', tag: '学习', href: 'spanish-grammar.html' },
      { icon: '✍️', name: '西语练习', desc: '每日一句 · 旅行手册 · 句子训练', tag: '练习', href: 'spanish-practice.html' },
      { icon: '📝', name: '多语种水平测试', desc: '日语 · 西语 · 德语', tag: '测试', href: 'japanese-test.html' }
    ]
  },
  {
    title: '📱 Mobile', cards: [
      { icon: '🇨🇳', name: '中国足迹 · iPhone', desc: '地级市触屏优化版', tag: '移动端', href: '中国旅行足迹-iPhone.html' },
      { icon: '🚇', name: '北京地铁 · iPhone', desc: '地铁触屏优化版', tag: '移动端', href: '北京地铁打卡-iPhone.html' }
    ]
  },
  {
    title: '🔧 Tools', cards: [
      { icon: '📱', name: '多端同步', desc: '二维码 / 文本码跨设备同步数据', tag: '工具', href: 'sync.html' }
    ]
  },
  {
    title: '🤖 Agent 学习中心', cards: [
      { icon: '🎓', name: '学习中心（跨设备云同步）', desc: 'GitHub 授权登录 · 错题/历史/词汇自动同步 · 金融测评 + 西语 A2', tag: 'Agent 版 · Vue', href: 'study.html', hot: true },
      { icon: '💰', name: '金融知识测评 · 单机版', desc: '题库中心 · 在线测评 · 学生卷/教师卷 · 知识点卡片', tag: 'Agent 版', href: 'agent-finance.html' },
      { icon: '🇪🇸', name: '西语 A2 复习 · 单机版', desc: '语法笔记 · 词汇三档复习 · 错词本 · 综合小测', tag: 'Agent 版', href: 'agent-spanish.html' }
    ]
  }
]

const cloud = ref('checking')
const username = ref('')

onMounted(async () => {
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
})

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
      <span class="lgout" @click="logout">退出</span>
    </div>
    <div v-else-if="cloud === 'off'" class="cloudbar">
      ☁️ 跨设备云同步已就绪 · <a href="study.html">登录学习中心 →</a>（首次绑定
      <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">生成令牌→粘贴</a>，约 2 分钟；
      之后所有新设备接力登录，无需粘贴；不登录可单机使用；任何人也可用自己的 GitHub 账号开启自己的同步）
    </div>
    <div v-else class="cloudbar">
      ☁️ 正在检查云同步状态…
    </div>

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

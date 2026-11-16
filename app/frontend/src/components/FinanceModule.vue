<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { CATS, QB, CARDS } from '../data.js'
import { store, LS_KEYS, lsGet, lsSet } from '../store.js'

const tab = ref('bank')
const bankCat = ref(-1)
const bankOpen = ref({})
const flipSet = ref({})

// 组卷状态
const mode = ref('student')
const pickN = ref(10)
const pickCats = ref([])
const paper = ref([])
const picks = ref([])
const submitted = ref(false)
const score = ref(null)

// 错题本 / 历史
const wrongSet = ref([])
const histArr = ref([])

function reloadLocal() {
  wrongSet.value = lsGet(LS_KEYS.finance.wrong, [])
  histArr.value = lsGet(LS_KEYS.finance.hist, [])
}
onMounted(reloadLocal)
watch(() => store.syncTick, reloadLocal)

const bankList = computed(() =>
  QB.map((q, i) => ({ q, i })).filter(x => bankCat.value === -1 || x.q.c === bankCat.value)
)

function bankTag(q) { return '✓ 答案：' + 'ABCD'[q.a] }

function startTest() {
  const pool = QB.map((q, i) => i).filter(i => pickCats.value.length === 0 || pickCats.value.includes(QB[i].c))
  paper.value = shuffle(pool).slice(0, Math.min(pickN.value, pool.length))
  picks.value = paper.value.map(() => -1)
  submitted.value = false
  score.value = null
  tab.value = 'test'
}

function shuffle(a) {
  a = a.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function pick(n, j) {
  if (submitted.value || mode.value === 'teacher') return
  picks.value[n] = j
}

function optClass(item, n, j) {
  if (mode.value === 'teacher' || submitted.value) {
    if (j === item.a) return 'opt right'
    if (submitted.value && j === picks.value[n]) return 'opt wrong'
    return 'opt'
  }
  return picks.value[n] === j ? 'opt sel' : 'opt'
}

function submitTest() {
  const un = picks.value.filter(p => p < 0).length
  if (un > 0 && !confirm(`还有 ${un} 题未作答，确定交卷？`)) return
  let right = 0
  paper.value.forEach((qi, n) => {
    const item = QB[qi]
    const ok = picks.value[n] === item.a
    if (ok) right++
    else if (!wrongSet.value.includes(qi)) wrongSet.value.push(qi)
  })
  submitted.value = true
  score.value = { right, total: paper.value.length }
  lsSet(LS_KEYS.finance.wrong, wrongSet.value)
  histArr.value.unshift({
    d: new Date().toLocaleString('zh-CN'),
    s: right, t: paper.value.length, m: '学生卷'
  })
  histArr.value = histArr.value.slice(0, 20)
  lsSet(LS_KEYS.finance.hist, histArr.value)
  window.scrollTo(0, 0)
}

function clearWrong() {
  if (!confirm('清空全部错题？')) return
  wrongSet.value = []
  lsSet(LS_KEYS.finance.wrong, wrongSet.value)
}

function clearHist() {
  if (!confirm('清空全部历史？')) return
  histArr.value = []
  lsSet(LS_KEYS.finance.hist, histArr.value)
}

const wrongList = computed(() => wrongSet.value.map(qi => QB[qi]))
</script>

<template>
  <div>
    <div class="tabs">
      <button class="tab" :class="{ on: tab === 'bank' }" @click="tab = 'bank'">📚 题库中心</button>
      <button class="tab" :class="{ on: tab === 'test' }" @click="tab = 'test'">✍️ 在线测评</button>
      <button class="tab" :class="{ on: tab === 'cards' }" @click="tab = 'cards'">🃏 知识点卡片</button>
      <button class="tab" :class="{ on: tab === 'wrong' }" @click="tab = 'wrong'">❌ 错题本 ({{ wrongSet.length }})</button>
      <button class="tab" :class="{ on: tab === 'hist' }" @click="tab = 'hist'">📊 测评历史</button>
    </div>

    <!-- 题库中心 -->
    <div v-if="tab === 'bank'" class="panel">
      <div class="card">
        <h3>分类筛选</h3>
        <div class="chips">
          <span class="chip" :class="{ on: bankCat === -1 }" @click="bankCat = -1">全部</span>
          <span v-for="(c, i) in CATS" :key="i" class="chip" :class="{ on: bankCat === i }" @click="bankCat = i">{{ c }}</span>
        </div>
        <div class="hint">点击题目可展开答案与解析。题库共 {{ QB.length }} 题。</div>
      </div>
      <div v-for="(x, n) in bankList" :key="n" class="q">
        <div class="meta">
          <span class="cat">{{ CATS[x.q.c] }}</span><span>第 {{ n + 1 }} 题</span>
          <span v-if="bankOpen[n]" class="tag2">{{ bankTag(x.q) }}</span>
        </div>
        <div class="stem" style="cursor:pointer" @click="bankOpen[n] = !bankOpen[n]">{{ x.q.q }}</div>
        <div v-for="(o, j) in x.q.o" :key="j" class="opt" :class="{ right: bankOpen[n] && j === x.q.a }">{{ 'ABCD'[j] }}. {{ o }}</div>
        <div class="exp" v-show="bankOpen[n]"><b>解析：</b>{{ x.q.e }}</div>
      </div>
    </div>

    <!-- 在线测评 -->
    <div v-if="tab === 'test'" class="panel">
      <div class="card">
        <h3>📋 组卷设置</h3>
        <div class="hint" style="margin-bottom:10px">学生卷需逐题作答后统一评分；教师卷直接展示全部答案与解析，适合打印。</div>
        <div class="chips">
          <span class="chip" :class="{ on: mode === 'student' }" @click="mode = 'student'">🎓 学生卷</span>
          <span class="chip" :class="{ on: mode === 'teacher' }" @click="mode = 'teacher'">🧑‍🏫 教师卷</span>
        </div>
        <div class="chips">
          <span class="chip" :class="{ on: pickN === 10 }" @click="pickN = 10">10 题</span>
          <span class="chip" :class="{ on: pickN === 20 }" @click="pickN = 20">20 题</span>
          <span class="chip" :class="{ on: pickN === 42 }" @click="pickN = 42">全部</span>
        </div>
        <div class="hint" style="margin:6px 0 4px">分类范围（不选 = 全部）</div>
        <div class="chips">
          <span v-for="(c, i) in CATS" :key="i" class="chip"
            :class="{ on: pickCats.includes(i) }"
            @click="pickCats.includes(i) ? pickCats.splice(pickCats.indexOf(i), 1) : pickCats.push(i)">{{ c }}</span>
        </div>
        <div style="margin-top:14px"><button class="btn" @click="startTest">{{ paper.length ? '重新组卷 →' : '开始测评 →' }}</button></div>
      </div>

      <template v-if="paper.length">
        <div class="scorebox" v-if="score">
          <div class="big">{{ score.right }} / {{ score.total }}</div>
          <div class="hint">得分率 {{ Math.round(score.right / score.total * 100) }}% · 答错的题已自动加入错题本</div>
        </div>
        <div class="card flexbar">
          <span class="hint">{{ mode === 'student' ? '🎓 学生卷' : '🧑‍🏫 教师卷' }} · 共 {{ paper.length }} 题</span>
          <span>
            <template v-if="mode === 'teacher'">
              <button class="btn ghost" @click="window.print()">🖨 打印 / 导出 PDF</button>
            </template>
            <template v-else-if="!submitted">
              <button class="btn" @click="submitTest">交卷评分</button>
            </template>
          </span>
        </div>
        <div v-for="(qi, n) in paper" :key="n" class="q">
          <div class="meta">
            <span class="cat">{{ CATS[QB[qi].c] }}</span><span>第 {{ n + 1 }} 题</span>
            <span v-if="mode === 'teacher'" class="tag2">✓ 答案：{{ 'ABCD'[QB[qi].a] }}</span>
          </div>
          <div class="stem">{{ QB[qi].q }}</div>
          <div v-for="(o, j) in QB[qi].o" :key="j" class="opt" :class="optClass(QB[qi], n, j)" @click="pick(n, j)">{{ 'ABCD'[j] }}. {{ o }}</div>
          <div class="exp" v-show="mode === 'teacher' || submitted"><b>解析：</b>{{ QB[qi].e }}</div>
        </div>
      </template>
    </div>

    <!-- 知识点卡片 -->
    <div v-if="tab === 'cards'" class="panel">
      <div class="card"><h3>🃏 核心概念 · 点击卡片翻面</h3><div class="hint">点击卡片查看解释，再点翻回。</div></div>
      <div class="kgrid">
        <div v-for="(c, i) in CARDS" :key="i" class="kcard" :class="{ flip: flipSet[i] }" @click="flipSet[i] = !flipSet[i]">
          <div class="kin">
            <div class="kface"><div class="kt">{{ c[0] }}</div><div class="ks">🃏 点击查看解释</div></div>
            <div class="kface kback"><div class="kt">{{ c[0] }}</div><div class="kd">{{ c[1] }}</div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错题本 -->
    <div v-if="tab === 'wrong'" class="panel">
      <div class="card flexbar">
        <div>
          <h3>❌ 我的错题</h3>
          <div class="hint">学生卷答错的题会自动收进来。当前共 {{ wrongSet.length }} 道。</div>
        </div>
        <button class="btn danger" v-if="wrongSet.length" @click="clearWrong">清空错题</button>
      </div>
      <div v-if="!wrongSet.length" class="empty">暂无错题 🎉</div>
      <div v-for="(item, n) in wrongList" :key="n" class="q">
        <div class="meta"><span class="cat">{{ CATS[item.c] }}</span><span>错题 {{ n + 1 }}</span><span class="tag2">✓ 答案：{{ 'ABCD'[item.a] }}</span></div>
        <div class="stem">{{ item.q }}</div>
        <div v-for="(o, j) in item.o" :key="j" class="opt" :class="{ right: j === item.a }">{{ 'ABCD'[j] }}. {{ o }}</div>
        <div class="exp"><b>解析：</b>{{ item.e }}</div>
      </div>
    </div>

    <!-- 测评历史 -->
    <div v-if="tab === 'hist'" class="panel">
      <div class="card flexbar">
        <div><h3>📊 测评记录</h3><div class="hint">本机保存最近 20 次成绩。</div></div>
        <button class="btn danger" v-if="histArr.length" @click="clearHist">清空历史</button>
      </div>
      <div class="card">
          <table v-if="histArr.length">
            <thead><tr><th>时间</th><th>卷型</th><th>得分</th><th>得分率</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in histArr" :key="i">
                <td>{{ r.d }}</td><td>{{ r.m }}</td><td>{{ r.s }} / {{ r.t }}</td><td>{{ Math.round(r.s / r.t * 100) }}%</td>
              </tr>
            </tbody>
          </table>
        <div v-else class="empty">暂无测评记录</div>
      </div>
    </div>
  </div>
</template>

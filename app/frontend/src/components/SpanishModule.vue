<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { GRAM, VOCAB, QB2 } from '../data.js'
import { store, LS_KEYS, lsGet, lsSet } from '../store.js'

const tab = ref('gram')
const lang = ref('zh')
const openSet = ref({})

const VMARK = ref({})
const wordIdx = ref(null)
const quizItems = ref([])
const quizIdx = ref(0)
const quizRight = ref(0)
const quizDone = ref(false)
const quizAnswered = ref(-1)

const I18N = {
  zh: { t1: '📖 语法笔记', t2: '🃏 词汇复习', t3: '❌ 错词本', t4: '📝 综合小测', skip: '跳过', next: '下一个 →', ok: '✅ 认识', mid: '🟡 模糊', no: '❌ 不认识', again: '再测一次', start: '开始小测 →', nextQ: '下一题 →', finish: '交卷评分', qcount: '第', qof: '题', aciertos: '已答对', click: '🃏 点击展开要点', weakTitle: '🟡❌ 需要重点复习的词', weakEmpty: '暂无需要复习的词 🎉', weakStart: '开始复习错词', weakClear: '清空错词本', weakCount: w => `共 ${w} 个词标记为模糊/不认识。`, quizDesc: '每次从词汇与语法题库随机抽 15 题：词汇 10 题 + 语法 5 题，做完即时评分。' },
  es: { t1: '📖 Gramática', t2: '🃏 Vocabulario', t3: '❌ Mis errores', t4: '📝 Miniprueba', skip: 'Saltar', next: 'Siguiente →', ok: '✅ Lo sé', mid: '🟡 Más o menos', no: '❌ No lo sé', again: 'Otra vez', start: 'Empezar →', nextQ: 'Siguiente →', finish: 'Terminar', qcount: 'Pregunta ', qof: '', aciertos: 'Aciertos: ', click: '🃏 Haz clic para ver', weakTitle: '🟡❌ Palabras para repasar', weakEmpty: 'Nada que repasar 🎉', weakStart: 'Repasar errores', weakClear: 'Vaciar lista', weakCount: w => `Hay ${w} palabras marcadas.`, quizDesc: '15 preguntas aleatorias: 10 de vocabulario y 5 de gramática, con nota inmediata.' }
}
const T = computed(() => I18N[lang.value])

function reloadLocal() {
  VMARK.value = lsGet(LS_KEYS.spanish.mark, {})
}
onMounted(() => { reloadLocal(); showWord() })
watch(() => store.syncTick, () => { reloadLocal(); showWord() })

function mLevel(i) { return VMARK.value[i] || 0 }
const stat = computed(() => {
  let ok = 0, mid = 0, no = 0
  for (let i = 0; i < VOCAB.length; i++) {
    const l = mLevel(i)
    if (l === 1) ok++; else if (l === 2) mid++; else if (l === 3) no++
  }
  return { ok, mid, no }
})
const weakIdx = computed(() => {
  const a = []
  for (let i = 0; i < VOCAB.length; i++) if (mLevel(i) >= 2) a.push(i)
  return a
})

function showWord() {
  const cand = []
  for (let i = 0; i < VOCAB.length; i++) {
    const l = mLevel(i)
    cand.push({ i, w: l === 3 ? 0 : l === 2 ? 1 : 2 })
  }
  cand.sort((a, b) => a.w - b.w || Math.random() - .5)
  wordIdx.value = cand[Math.floor(Math.random() * Math.min(cand.length, 8))].i
}
const currentWord = computed(() => VOCAB[wordIdx.value] || VOCAB[0])

function mark(level) {
  VMARK.value[wordIdx.value] = level
  lsSet(LS_KEYS.spanish.mark, VMARK.value)
  showWord()
}
function skipWord() {
  delete VMARK.value[wordIdx.value]
  lsSet(LS_KEYS.spanish.mark, VMARK.value)
  showWord()
}
function clearWeak() {
  if (!confirm(lang.value === 'zh' ? '把所有 🟡/❌ 标记清空？' : '¿Vaciar todas las marcas?')) return
  for (const i of weakIdx.value) delete VMARK.value[i]
  lsSet(LS_KEYS.spanish.mark, VMARK.value)
}
function markKnown(i) {
  VMARK.value[i] = 1
  lsSet(LS_KEYS.spanish.mark, VMARK.value)
}

function shuffle(a) {
  a = a.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function startQuiz() {
  const vs = []
  shuffle(VOCAB.map((v, i) => i)).slice(0, 10).forEach(i => {
    const v = VOCAB[i]
    const distr = shuffle(VOCAB.filter((x, j) => j !== i).map(x => x[1])).slice(0, 3)
    const opts = shuffle(distr.concat([v[1]]))
    vs.push({ q: `“${v[0]}” 的意思是？`, o: opts, a: opts.indexOf(v[1]), e: `“${v[0]}” = ${v[1]}。例句：${v[2]}（${v[3]}）`, vi: i })
  })
  quizItems.value = vs.concat(shuffle(QB2).slice(0, 5))
  quizIdx.value = 0
  quizRight.value = 0
  quizDone.value = false
  quizAnswered.value = -1
}
const qItem = computed(() => quizItems.value[quizIdx.value])

function answerQuiz(j) {
  if (quizAnswered.value >= 0) return
  quizAnswered.value = j
  const it = qItem.value
  if (j === it.a) quizRight.value++
  else if (it.vi !== undefined) {
    const cur = mLevel(it.vi)
    if (cur < 3) { VMARK.value[it.vi] = cur === 2 ? 3 : 2; lsSet(LS_KEYS.spanish.mark, VMARK.value) }
  }
}
function nextQuiz() {
  quizAnswered.value = -1
  quizIdx.value++
  if (quizIdx.value >= quizItems.value.length) quizDone.value = true
}
</script>

<template>
  <div>
    <div class="topbar" style="margin-bottom:10px">
      <span class="hint">DELE A2 · 多邻国 Section 4 对齐</span>
      <button class="btn ghost" style="margin-left:auto" @click="lang = lang === 'zh' ? 'es' : 'zh'">
        {{ lang === 'zh' ? 'ES' : '中文' }}
      </button>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ on: tab === 'gram' }" @click="tab = 'gram'">{{ T.t1 }}</button>
      <button class="tab" :class="{ on: tab === 'vocab' }" @click="tab = 'vocab'; showWord()">{{ T.t2 }}</button>
      <button class="tab" :class="{ on: tab === 'weak' }" @click="tab = 'weak'">{{ T.t3 }} ({{ weakIdx.length }})</button>
      <button class="tab" :class="{ on: tab === 'quiz' }" @click="tab = 'quiz'">{{ T.t4 }}</button>
    </div>

    <!-- 语法笔记 -->
    <div v-if="tab === 'gram'" class="panel">
      <div class="ggrid">
        <div v-for="(g, i) in GRAM" :key="i" class="gcard" @click="openSet[i] = !openSet[i]">
          <div class="gt">{{ i + 1 }}. {{ g.t }}</div>
          <div class="gs" v-if="!openSet[i]">{{ T.click }}</div>
          <div class="gp" v-else>
            {{ lang === 'zh' ? g.zh : g.es }}
            <div class="gex" v-for="(e, k) in g.ex" :key="k"><b>{{ e[0] }}</b><br><i>{{ e[1] }}</i></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 词汇复习 -->
    <div v-if="tab === 'vocab'" class="panel">
      <div class="stat">
        <span class="s1">✅ {{ stat.ok }}</span>
        <span class="s2">🟡 {{ stat.mid }}</span>
        <span class="s3">❌ {{ stat.no }}</span>
        <span>{{ lang === 'zh' ? '总计 ' + VOCAB.length + ' 词' : 'Total: ' + VOCAB.length }}</span>
      </div>
      <div class="vbox">
        <div class="ves">{{ currentWord[0] }}</div>
        <div class="vez">{{ currentWord[1] }}</div>
        <div class="vex">💬 {{ currentWord[2] }}<i>{{ currentWord[3] }}</i></div>
        <div class="mark3">
          <button class="mk ok" @click="mark(1)">{{ T.ok }}</button>
          <button class="mk mid" @click="mark(2)">{{ T.mid }}</button>
          <button class="mk no" @click="mark(3)">{{ T.no }}</button>
        </div>
      </div>
      <div class="vnav">
        <button class="btn ghost" @click="skipWord">← {{ T.skip }}</button>
        <button class="btn" @click="showWord()">{{ T.next }}</button>
      </div>
    </div>

    <!-- 错词本 -->
    <div v-if="tab === 'weak'" class="panel">
      <div class="card flexbar">
        <div>
          <h3>{{ T.weakTitle }}</h3>
          <div class="hint">{{ weakIdx.length ? T.weakCount(weakIdx.length) : T.weakEmpty }}</div>
        </div>
        <span>
          <button class="btn ghost" v-if="weakIdx.length" @click="tab = 'vocab'; showWord()">{{ T.weakStart }}</button>
          <button class="btn danger" v-if="weakIdx.length" @click="clearWeak">{{ T.weakClear }}</button>
        </span>
      </div>
      <div v-if="!weakIdx.length" class="empty">{{ T.weakEmpty }}</div>
      <div class="ggrid">
        <div v-for="i in weakIdx" :key="i" class="gcard" style="cursor:default">
          <div class="gt">{{ mLevel(i) === 3 ? '❌ ' : '🟡 ' }}{{ VOCAB[i][0] }} <span style="font-size:12px;color:var(--text2)">{{ VOCAB[i][1] }}</span></div>
          <div class="gp" style="margin-top:8px">
            <div class="gex"><b>{{ VOCAB[i][2] }}</b><br><i>{{ VOCAB[i][3] }}</i></div>
            <div class="mark3"><button class="mk ok" style="width:auto" @click="markKnown(i)">✅</button></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 综合小测 -->
    <div v-if="tab === 'quiz'" class="panel">
      <div class="card" v-if="!quizItems.length || quizDone">
        <div class="scorebox" v-if="quizDone">
          <div class="big">{{ quizRight }} / {{ quizItems.length }}</div>
          <div class="hint">{{ lang === 'zh' ? '得分率 ' : 'Aciertos: ' }}{{ Math.round(quizRight / quizItems.length * 100) }}%</div>
        </div>
        <h3>{{ T.t4 }}</h3>
        <div class="hint" style="margin-bottom:12px">{{ T.quizDesc }}</div>
        <button class="btn" @click="startQuiz">{{ quizDone ? T.again : T.start }}</button>
      </div>
      <div class="card" v-else>
        <div class="hint" style="margin-bottom:12px">{{ T.qcount }} {{ quizIdx + 1 }} / {{ quizItems.length }}{{ T.qof }} · {{ T.aciertos }}{{ quizRight }}</div>
        <div class="stem" style="font-size:15px;font-weight:700;margin-bottom:14px">{{ qItem.q }}</div>
        <div v-for="(o, j) in qItem.o" :key="j" class="opt"
          :class="{ right: quizAnswered >= 0 && j === qItem.a, wrong: quizAnswered === j && j !== qItem.a }"
          @click="answerQuiz(j)">{{ o }}</div>
        <div class="exp" v-if="quizAnswered >= 0">
          <b>{{ quizAnswered === qItem.a ? '✅' : '❌' }}</b> {{ qItem.e }}
        </div>
        <div class="vnav" v-if="quizAnswered >= 0" style="margin-top:16px">
          <span></span>
          <button class="btn" @click="nextQuiz">{{ quizIdx === quizItems.length - 1 ? T.finish : T.nextQ }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

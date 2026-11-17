# -*- coding: utf-8 -*-
"""组装西语合体版 agent-spanish.html：100词+手册229词 / 20张透彻语法卡 / 114动词变位速查 / SRS复习 / 中西切换"""
import json, re

OUT = "/Users/kangzhongqi/Desktop/travel-tracker-pages/.temp-fin"
DEST = "/Users/kangzhongqi/Desktop/travel-tracker-pages/agent-spanish.html"

# ===== 数据准备 =====
grammar = json.load(open(OUT + "/grammar_v2.json", encoding="utf-8"))
manual = json.load(open(OUT + "/vocab_manual.json", encoding="utf-8"))
verbs = json.load(open(OUT + "/verbs_verbDict.json", encoding="utf-8"))
import subprocess, os
# 原 100 词从旧版提取（agent-finance-v1 备份同目录的旧 agent-spanish）
src = open("/Users/kangzhongqi/Desktop/travel-tracker-pages/.temp-fin/old_spanish.html", encoding="utf-8").read() if os.path.exists(OUT + "/old_spanish.html") else None
if not src:
    # 从 git 取当前线上版
    r = subprocess.run(["git", "show", "HEAD:agent-spanish.html"], capture_output=True, text=True, cwd="/Users/kangzhongqi/Desktop/travel-tracker-pages")
    src = r.stdout
    open(OUT + "/old_spanish.html", "w", encoding="utf-8").write(src)
m = re.search(r'var VOCAB=(\[.*?\]);\n', src, re.S)
assert m, "VOCAB not found"
nc = "const v=" + m.group(1) + ";require('fs').writeFileSync(" + json.dumps(OUT + "/vocab_old.json") + ",JSON.stringify(v))"
r = subprocess.run(["node", "-e", nc], capture_output=True, text=True)
assert r.returncode == 0, r.stderr[:200]
vocab_old = json.load(open(OUT + "/vocab_old.json", encoding="utf-8"))
print("旧词库:", len(vocab_old), "动词:", len(verbs), "新卡:", len(grammar))

# 合并词汇：旧 100 词保留例句；手册词补充（无例句），按 es 文本去重
merged = []
seen = set()
for w in vocab_old:
    if w[0] not in seen:
        merged.append({"es": w[0], "zh": w[1], "ex": w[2], "exz": w[3], "src": "core"})
        seen.add(w[0])
GROUP_NAMES = {"comida": "餐饮", "viajes": "旅行", "casa": "家居", "trabajo": "工作", "cuerpo": "身体",
               "emocion": "情绪", "tiempo": "时间", "numeros": "数字", "clima": "天气", "ropa": "衣物", "calle": "街道"}
for g, ws in manual.items():
    for w in ws:
        if w["es"] not in seen:
            merged.append({"es": w["es"], "zh": w["zh"], "ex": "", "exz": "", "src": GROUP_NAMES.get(g, g)})
            seen.add(w["es"])
print("合并词库:", len(merged))
json.dump(merged, open(OUT + "/vocab_merged.json", "w", encoding="utf-8"), ensure_ascii=False)

# 旧 VMARK(索引键) → 新文本键 的迁移映射
mig = {str(i): w[0] for i, w in enumerate(vocab_old)}

ext = {}
for name in ["dailyBank", "travelData", "sentenceBank", "verbBank"]:
    ext[name] = json.load(open(OUT + "/ext_" + name + ".json", encoding="utf-8"))

DATA = json.dumps({
    "grammar": grammar, "vocab": merged, "verbs": verbs, "mig": mig,
    "daily": ext["dailyBank"], "travel": ext["travelData"],
    "sent": ext["sentenceBank"], "verbQuiz": ext["verbBank"]
}, ensure_ascii=False, separators=(",", ":")) + ";"

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>西语 A2 学习中心 · Agent 合体版</title>
<style>
:root{--bg:#090d15;--card:#111827;--card2:#1a2235;--text:#e5e7eb;--text2:#9ca3af;--text3:#6b7280;--border:#1f2937;--accent:#10b981;--accent2:#34d399;--danger:#f87171;--warn:#fbbf24;--radius:16px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(16,185,129,.06),transparent 70%)}
.container{position:relative;z-index:1;max-width:900px;margin:0 auto;padding:24px 20px 60px}
.topbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.back{display:inline-flex;align-items:center;color:var(--text2);text-decoration:none;font-size:13px;padding:6px 12px;border:1px solid var(--border);border-radius:10px;background:var(--card)}
h1{font-size:21px;font-weight:800}
h1 .grad{background:linear-gradient(135deg,#e5e7eb 20%,var(--accent2) 80%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.badge{font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;background:linear-gradient(135deg,rgba(16,185,129,.18),rgba(52,211,153,.08));color:var(--accent2);border:1px solid rgba(16,185,129,.35)}
.langbtn{margin-left:auto;padding:6px 14px;border-radius:999px;border:1px solid var(--accent);background:rgba(16,185,129,.1);color:var(--accent2);font-size:12px;font-weight:700;cursor:pointer}
.sub{color:var(--text2);font-size:12px;margin-top:6px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}
.tab{padding:8px 14px;border-radius:12px;border:1px solid var(--border);background:var(--card);color:var(--text2);font-size:13px;font-weight:600;cursor:pointer}
.tab.on{background:rgba(16,185,129,.12);color:var(--accent2);border-color:var(--accent)}
.panel{display:none;animation:fadeIn .3s}
.panel.on{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin-bottom:14px}
.card h3{font-size:15px;margin-bottom:8px}
.hint{font-size:12px;color:var(--text3);line-height:1.7}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.chip{padding:5px 12px;border-radius:999px;border:1px solid var(--border);background:var(--card2);color:var(--text2);font-size:12px;cursor:pointer;user-select:none;white-space:nowrap}
.chip.on{background:rgba(16,185,129,.15);color:var(--accent2);border-color:var(--accent)}
.btn{display:inline-block;padding:9px 18px;border-radius:12px;border:none;background:linear-gradient(135deg,var(--accent),#059669);color:#fff;font-size:13px;font-weight:700;cursor:pointer}
.btn.ghost{background:var(--card2);color:var(--text2);border:1px solid var(--border)}
.btn.danger{background:var(--card2);color:var(--danger);border:1px solid rgba(248,113,113,.4)}
.stat{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;font-size:11px}
.stat span{padding:4px 10px;border-radius:999px;border:1px solid var(--border);background:var(--card2);color:var(--text3)}
.ggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.gcard{border:1px solid var(--border);border-radius:var(--radius);background:var(--card);padding:16px;cursor:pointer}
.gcard:hover{border-color:var(--accent)}
.gcard .gt{font-size:14.5px;font-weight:800;color:var(--accent2);margin-bottom:8px}
.gcard .gs{font-size:11px;color:var(--text3)}
.gcard .gp{font-size:12.5px;color:var(--text2);line-height:1.8;display:none}
.gcard.open .gp{display:block}
.gcard.open .gs{display:none}
.gex{margin-top:10px;padding:9px 12px;border-left:3px solid var(--accent);background:var(--card2);border-radius:8px;font-size:12.5px;line-height:1.9}
.gex b{color:var(--accent2)}
.gex i{color:var(--text3);font-style:normal;font-size:11.5px}
.vbox{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:30px 22px;text-align:center}
.vbox .ves{font-size:36px;font-weight:900}
.vbox .vez{font-size:16px;color:var(--accent2);margin-top:8px;font-weight:700}
.vbox .vex{margin-top:12px;font-size:12.5px;color:var(--text2);line-height:1.7}
.vbox .vex i{display:block;color:var(--text3);font-size:11px;margin-top:2px}
.mark3{display:flex;gap:8px;margin-top:14px}
.mk{flex:1;min-width:80px;padding:10px;border-radius:10px;border:1px solid var(--border);background:var(--card2);font-size:13px;font-weight:700;cursor:pointer;color:var(--text2)}
.mk.ok:hover{border-color:var(--accent);color:var(--accent2)}
.mk.mid:hover{border-color:var(--warn);color:var(--warn)}
.mk.no:hover{border-color:var(--danger);color:var(--danger)}
.vnav{display:flex;justify-content:space-between;margin-top:18px;gap:10px;flex-wrap:wrap}
.opt{display:block;padding:10px 14px;border:1px solid var(--border);border-radius:10px;margin-bottom:8px;font-size:13px;color:var(--text2);cursor:pointer;line-height:1.5}
.opt:hover{border-color:var(--accent)}
.opt.right{border-color:var(--accent);background:rgba(16,185,129,.12);color:var(--accent2)}
.opt.wrong{border-color:var(--danger);background:rgba(248,113,113,.08);color:var(--danger)}
.exp{margin-top:10px;padding:12px 14px;border-radius:10px;background:var(--card2);border-left:3px solid var(--accent);font-size:12px;color:var(--text2);line-height:1.7}
.exp b{color:var(--accent2)}
.empty{text-align:center;color:var(--text3);font-size:13px;padding:26px 0}
.note{font-size:11px;color:var(--text3);margin-top:14px;text-align:center;line-height:1.8}
.srsbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.tbl{width:100%;border-collapse:collapse;font-size:12px}
.tbl th,.tbl td{padding:7px 9px;border-bottom:1px solid var(--border);text-align:left}
.tbl th{color:var(--text3);font-size:11px}
.tbl td{color:var(--text2)}
.tbl td.first{color:var(--accent2);font-weight:700}
input.q{width:100%;max-width:320px;padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:var(--card2);color:var(--text);font-size:14px;outline:none}
input.q:focus{border-color:var(--accent)}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <a class="back" href="./">← 首页</a>
    <h1><span class="grad">🇪🇸 <span id="t-title">西语 A2 学习中心</span></span></h1>
    <span class="badge" id="t-badge">Agent 合体版</span>
    <button class="langbtn" id="langBtn">ES</button>
  </div>
  <p class="sub" id="t-sub">合并词库 329 词 · 20 张透彻语法卡 · 114 动词变位速查 · SRS 遗忘曲线复习 · DELE A2 对齐</p>

  <div class="tabs" id="tabs">
    <button class="tab on" data-p="gram"><span id="t1">📖 语法精讲</span></button>
    <button class="tab" data-p="vocab"><span id="t2">🃏 词汇复习</span></button>
    <button class="tab" data-p="verbs"><span id="t3">🔤 动词变位</span></button>
    <button class="tab" data-p="sent">✍️ 句子训练</button>\n    <button class="tab" data-p="srs"><span id="t5">🔁 遗忘曲线</span><span id="srsBadge" style="display:none;margin-left:4px;font-size:11px;color:var(--warn)"></span></button>
    <button class="tab" data-p="quiz"><span id="t4">📝 综合小测</span></button>
  </div>

  <div class="panel on" id="p-gram">
    <div class="card"><h3 id="t-g0">20 张 A2 核心语法卡 · 点击展开透彻讲解</h3><div class="hint" id="t-g0d">每张卡含：核心原理 / 常见错误 / 对比辨析 / 例句。</div>
    <div class="chips" id="gramChips" style="margin-top:8px"></div></div>
    <div class="ggrid" id="gGrid"></div>
  </div>

  <div class="panel" id="p-vocab">
    <div class="stat" id="vStat"></div>
    <div class="card" style="padding:12px 16px"><div class="chips" id="vocabSrcChips"></div></div>
    <div class="vbox" id="vBox"></div>
    <div class="vnav">
      <button class="btn ghost" id="vSkip">← 跳过</button>
      <button class="btn" id="vNext">下一个 →</button>
    </div>
    <div class="note" id="t-vnote">✅ 认识 / 🟡 模糊 / ❌ 不认识 —— 弱词优先推送；标记进入遗忘曲线队列，跨设备自动同步</div>
  </div>

  <div class="panel" id="p-verbs">
    <div class="card">
      <h3>🔤 动词变位速查（114 个高频动词）</h3>
      <div class="hint" style="margin-bottom:10px">搜索动词原形或中文含义；点击动词行展开 6 人称现在时 + 简单过去时关键位。</div>
      <input class="q" id="verbSearch" placeholder="输入动词，如 hablar / ser / 吃">
      <button class="btn" id="vqStart" style="margin-left:10px">🎯 变位练习（12 题）</button>
    </div>
    <div id="verbList"></div>
    <div id="verbQuizArea" style="margin-top:14px"></div>
  </div>

  <div class="panel" id="p-sent">
    <div class="card" id="dailyBox"></div>
    <div class="card">
      <h3>✍️ 句子训练（L1-L4）</h3>
      <div class="hint" style="margin-bottom:8px">四级递进：L1 变位填空 → L2 点击组句 → L3 中译西 → L4 阅读理解。历史沿用旧版练习记录。</div>
      <div class="chips" id="sentLv"></div>
      <div id="sentArea"></div>
    </div>
    <div class="card">
      <h3>🧳 旅行场景速用</h3>
      <div class="chips" id="travelChips"></div>
      <div id="travelArea"></div>
    </div>
  </div>

  <div class="panel" id="p-srs">
    <div class="card">
      <div class="srsbar">
        <h3>🔁 遗忘曲线复习</h3>
        <span class="hint" id="srsStat"></span>
        <button class="btn danger" id="srsClear">清空队列</button>
      </div>
      <div id="srsBody"></div>
    </div>
  </div>

  <div class="panel" id="p-quiz">
    <div id="qSetup" class="card">
      <h3>📝 A2 综合小测</h3>
      <div class="hint" style="margin-bottom:12px">每次随机抽 15 题：词汇 10 题 + 语法 5 题，答错自动进入遗忘曲线队列。</div>
      <button class="btn" id="qStart">开始小测 →</button>
    </div>
    <div id="qBody" style="display:none"></div>
  </div>

  <p class="note">🤖 Agent 合体版：Agent 模块 × A2 手册词汇 × 动词变位库 · 讲解透彻 · 遗忘曲线复习 · 数据自动云同步<br>All data stored locally & in your own private GitHub repo · No tracking</p>
</div>
<script src="site-auth.js?v=3"></script>
<script>
window.ESDATA = __DATA__;
</script>
<script>
(function(){
var D = window.ESDATA;
var lang = "zh";
var T = {
zh:{t1:"📖 语法精讲",t2:"🃏 词汇复习",t3:"🔤 动词变位",t4:"📝 综合小测",t5:"🔁 遗忘曲线",next:"下一个 →",skip:"跳过",ok:"✅ 认识",mid:"🟡 模糊",no:"❌ 不认识",open:"🃏 点击展开透彻讲解"},
es:{t1:"📖 Gramática",t2:"🃏 Vocabulario",t3:"🔤 Verbos",t4:"📝 Miniprueba",t5:"🔁 Repaso",next:"Siguiente →",skip:"Saltar",ok:"✅ Lo sé",mid:"🟡 Más o menos",no:"❌ No lo sé",open:"🃏 Haz clic para ver"}
};

/* ===== 存储键（文本键，兼容迁移）===== */
var K = { mark:"agv_mark_v2", srs:"es_srs_v1", oldMark:"agv_mark" };
function load(k,d){ try{ var v=JSON.parse(localStorage.getItem(k)); return v==null?d:v }catch(e){ return d } }
function save(k,v){ localStorage.setItem(k, JSON.stringify(v)); window.__agMiscTouch && window.__agMiscTouch(); }
var VMARK = load(K.mark, null);
if(!VMARK){ // 旧索引键迁移到文本键
  VMARK = {};
  var old = load(K.oldMark, {});
  for(var i in old){ var w = D.mig[i]; if(w) VMARK[w] = old[i]; }
  save(K.mark, VMARK);
}
var SRS = load(K.srs, {});
function mLevel(w){ return VMARK[w]||0 }
function touch(w, lv){ if(lv===0) delete VMARK[w]; else VMARK[w]=lv; save(K.mark, VMARK);
  if(lv>=2){ if(!SRS[w]) SRS[w] = {due: Date.now(), streak: 0}; save(K.srs, SRS); }
  else if(SRS[w] && lv===1){ delete SRS[w]; save(K.srs, SRS); }
}

/* ===== i18n ===== */
function applyLang(){
  ["t1","t2","t3","t4","t5"].forEach(function(id){ var el=document.getElementById(id); if(el) el.textContent=T[lang][id]; });
  document.getElementById("langBtn").textContent = lang==="zh"?"ES":"中文";
  renderStat(); renderSrs();
}
document.getElementById("langBtn").onclick=function(){ lang = lang==="zh"?"es":"zh"; applyLang(); };

/* ===== Tabs ===== */
document.querySelectorAll(".tab").forEach(function(t){
  t.onclick=function(){
    document.querySelectorAll(".tab").forEach(function(x){x.classList.remove("on")});
    t.classList.add("on");
    document.querySelectorAll(".panel").forEach(function(p){p.classList.remove("on")});
    document.getElementById("p-"+t.dataset.p).classList.add("on");
    if(t.dataset.p==="vocab") showWord();
    if(t.dataset.p==="verbs") renderVerbs(document.getElementById("verbSearch").value);
    if(t.dataset.p==="srs") renderSrs();
  };
});

/* ===== 语法精讲 ===== */
var gCh = "all";
function renderGramChips(){
  var chips = '<span class="chip'+(gCh==="all"?" on":"")+'" data-v="all">全部</span>';
  chips += '<span class="chip'+(gCh==="core"?" on":"")+'" data-v="core">高频核心</span>';
  var h="";
  for(var i=0;i<D.grammar.length;i++){ h+='<span class="chip'+(gCh===(i+1)?" on":"")+'" data-v="'+(i+1)+'">'+(i+1)+'</span>'; }
  document.getElementById("gramChips").innerHTML = chips + '<span style="flex:1"></span>' + h;
  document.querySelectorAll("#gramChips .chip").forEach(function(c){
    c.onclick=function(){ gCh = c.dataset.v==="core"?"core":(c.dataset.v==="all"?"all":+c.dataset.v); renderGram(); };
  });
}
function renderGram(){
  var list = D.grammar.filter(function(g,i){ return gCh==="all"||gCh==="core"&&i<14||gCh===i+1; });
  document.getElementById("gGrid").innerHTML = list.map(function(g,i){
    var h='<div class="gcard"><div class="gt">'+g.t+'</div><div class="gs">'+T[lang].open+'</div><div class="gp">'+g.zh;
    g.ex.forEach(function(e){ h+='<div class="gex"><b>'+e[0]+'</b><br><i>'+e[1]+'</i></div>'; });
    return h+'</div></div>';
  }).join("");
  document.querySelectorAll("#gGrid .gcard").forEach(function(c){ c.onclick=function(){ c.classList.toggle("open"); }; });
}
renderGramChips(); renderGram();

/* ===== 词汇复习（弱词优先）===== */
var vIdx = null;
function stat(){
  var ok=0, mid=0, no=0;
  D.vocab.forEach(function(w){ var l=mLevel(w.es); if(l===1)ok++; else if(l===2)mid++; else if(l===3)no++; });
  return {ok:ok,mid:mid,no:no,total:D.vocab.length};
}
function renderStat(){
  var s = stat();
  document.getElementById("vStat").innerHTML =
    '<span style="color:var(--accent2)">✅ '+s.ok+'</span><span style="color:var(--warn)">🟡 '+s.mid+'</span><span style="color:var(--danger)">❌ '+s.no+'</span><span>总词库 '+s.total+'</span>';
}
function srcChips(){
  var srcs = {};
  D.vocab.forEach(function(w){ srcs[w.src] = (srcs[w.src]||0)+1; });
  var chips = '<span class="chip on" data-v="all">全部</span>';
  for(var s in srcs){ if(s!=="core") chips += '<span class="chip" data-v="'+s+'">'+s+'（'+srcs[s]+'）</span>'; }
  document.getElementById("vocabSrcChips").innerHTML = chips;
  document.querySelectorAll("#vocabSrcChips .chip").forEach(function(c){
    c.onclick=function(){ document.querySelectorAll("#vocabSrcChips .chip").forEach(function(x){x.classList.remove("on")}); c.classList.add("on"); showWord(c.dataset.v); };
  });
}
srcChips();
function showWord(srcFilter){
  var pool = D.vocab.map(function(w,i){ return {w:w, i:i}; }).filter(function(x){ return !srcFilter||srcFilter==="all"||x.w.src===srcFilter; });
  var cand = [];
  pool.forEach(function(x){
    var l = mLevel(x.w.es);
    cand.push({w:x.w, wt: l===3?0 : l===2?1 : 2});
  });
  cand.sort(function(a,b){ return a.wt-b.wt || Math.random()-.5; });
  var pick = cand[Math.floor(Math.random()*Math.min(cand.length, 10))].w;
  vIdx = pick.es;
  document.getElementById("vBox").innerHTML =
    '<div class="ves">'+pick.es+'</div><div class="vez">'+pick.zh+'</div>'
    + (pick.ex ? '<div class="vex">💬 '+pick.ex+'<i>'+pick.exz+'</i></div>' : '<div class="vex" style="color:var(--text3)">（本词暂无例句）</div>')
    + '<div class="mark3"><button class="mk ok" id="mk-ok">'+T[lang].ok+'</button><button class="mk mid" id="mk-mid">'+T[lang].mid+'</button><button class="mk no" id="mk-no">'+T[lang].no+'</button></div>';
  document.getElementById("mk-ok").onclick = function(){ touch(pick.es,1); showWord(srcFilter); };
  document.getElementById("mk-mid").onclick = function(){ touch(pick.es,2); showWord(srcFilter); };
  document.getElementById("mk-no").onclick = function(){ touch(pick.es,3); showWord(srcFilter); };
  renderStat();
}
document.getElementById("vNext").onclick = function(){ showWord(); };
document.getElementById("vSkip").onclick = function(){ if(vIdx){ touch(vIdx,0); } showWord(); };
renderStat(); showWord();

/* ===== 动词变位速查 ===== */
var PERS = ["yo","tú","él/ella","nosotros","vosotros","ellos"];
document.getElementById("verbSearch").addEventListener("input", function(){ renderVerbs(this.value); });
function renderVerbs(q){
  q = (q||"").trim().toLowerCase();
  var list = D.verbs.filter(function(v){ return !q || v.v.indexOf(q)>=0 || (v.t||"").indexOf(q)>=0; }).slice(0, 30);
  document.getElementById("verbList").innerHTML = list.map(function(v){
    var pres = v.pres ? v.pres : null;
    var h = '<div class="card" style="padding:14px 18px"><div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><b style="font-size:16px;color:var(--accent2)">'+v.v+'</b><span style="color:var(--text2);font-size:13px">'+(v.t||"")+'</span><span class="hint">'+(v.type==="irr"?"不规则":"规则")+'</span></div>';
    if(pres){
      h += '<div style="margin-top:8px"><div class="hint" style="margin-bottom:4px">现在时</div><table class="tbl">';
      PERS.forEach(function(p,i){ h += '<tr><th style="width:90px">'+p+'</th><td'+(i===0?' class="first"':'')+'>'+(pres[i]||"—")+'</td></tr>'; });
      h += '</table>';
      if(v.pretConj){ h += '<div class="hint" style="margin:8px 0 4px">简单过去时</div><table class="tbl">';
        var pc = v.pretConj;
        PERS.forEach(function(p,i){ h += '<tr><th style="width:90px">'+p+'</th><td>'+(Array.isArray(pc)?(pc[i]||"—"):(pc[p]||"—"))+'</td></tr>'; });
        h += '</table>'; }
      else if(v.pret){ h += '<div class="hint" style="margin-top:6px">简单过去时 yo：'+v.pret+'</div>'; }
    } else { h += '<div class="hint" style="margin-top:6px">（无完整变位数据）</div>'; }
    return h+'</div>';
  }).join("") || '<div class="empty">未找到匹配动词</div>';
}
renderVerbs("");

/* ===== SRS 遗忘曲线 ===== */
function srsDue(){
  var due = [];
  for(var w in SRS){ if(SRS[w] && SRS[w].due<=Date.now()){ var vw = D.vocab.filter(function(x){return x.es===w;})[0]; if(vw) due.push(vw); } }
  return due;
}
function updSrsBadge(){
  var n = srsDue().length;
  var el = document.getElementById("srsBadge");
  if(n>0){ el.style.display=""; el.textContent="（今日 "+n+"）"; } else el.style.display="none";
}
setInterval(updSrsBadge, 2000);
function renderSrs(){
  var due = srsDue();
  var total = Object.keys(SRS).length;
  var future = total - due.length;
  document.getElementById("srsStat").innerHTML = '今日到期 <b style="color:'+(due.length?"var(--warn)":"var(--ok)")+'">'+due.length+'</b> · 排期中 '+future+' · 原则：看词回忆 → 翻面自评 → 答对拉长间隔、答错明天再见';
  var body = document.getElementById("srsBody");
  document.getElementById("srsClear").onclick = function(){
    if(!confirm("清空整个复习队列？")) return;
    SRS = {}; save(K.srs, SRS); renderSrs();
  };
  if(!due.length){ body.innerHTML = '<div class="empty">今日没有到期的复习词 🎉</div>'; return; }
  var w = due[0];
  body.innerHTML =
    '<div class="vbox" style="cursor:pointer" id="srsFlip"><div class="ves">'+w.es+'</div>'
    + '<div class="vez" id="srsBack" style="display:none">'+w.zh+'</div>'
    + '<div class="vex" id="srsEx" style="display:none">'+(w.ex?'💬 '+w.ex+'<i>'+w.exz+'</i>':'')+'<i>还剩 '+due.length+' 词到期</i></div></div>'
    + '<div class="mark3"><button class="mk ok" id="srs-ok">✅ 记住了</button><button class="mk no" id="srs-no">❌ 没记住</button></div>';
  document.getElementById("srsFlip").onclick = function(){
    document.getElementById("srsBack").style.display="";
    document.getElementById("srsEx").style.display="";
  };
  document.getElementById("srs-ok").onclick = function(){
    var s = SRS[w.es]; s.streak = (s.streak||0)+1;
    s.due = Date.now() + [1,2,4,7,15,30][Math.min(s.streak-1,5)]*86400000;
    if(s.streak>=3){ delete SRS[w.es]; delete VMARK[w.es]; save(K.mark, VMARK); }
    save(K.srs, SRS); renderSrs(); renderStat();
  };
  document.getElementById("srs-no").onclick = function(){
    SRS[w.es] = {due: Date.now()+86400000, streak: 0};
    VMARK[w.es] = 3; save(K.mark, VMARK);
    save(K.srs, SRS); renderSrs(); renderStat();
  };
}

/* ===== 综合小测 ===== */
var QBS = [
["Me ___ el café.","gusta|gustan|gusto|gustas",0,"Me gusta + 单数名词。"],
["¿Las llaves? No ___ veo.","lo|las|la|les",1,"las 代替阴性复数直接宾语。"],
["Ayer ___ al cine.","voy|iba|fui|he ido",2,"一次性完结动作用简单过去时 fui。"],
["De niño, ___ al fútbol.","jugaba|jugué|juego|he jugado",0,"过去习惯动作用未完成过去时 jugaba。"],
["Si ___ tiempo, ven a mi casa.","tienes|tendrás|tengas|vas a tener",0,"si 从句用陈述式现在时。"],
["Le ___ el mapa a María.","doy|da|das|damos",0,"「我给」→ 第一人称单数 doy。"],
["Se ___ digo mañana.","lo|la|le|los",0,"与格 le + 宾格 lo → se lo。"],
["Gracias ___ todo.","para|por|a|de",1,"por 表原因。"],
["Esto es ___ ti.","por|para|con|en",1,"para 表对象。"],
["No viene ___.","nada|nadie|nunca|ninguno",1,"「没有人」= nadie。"],
["Tengo ___ trabajar.","que|de|a|por",0,"tener que + 原形表义务。"],
["Me ___ a las siete.","levanto|levantar|levantas|levanta",0,"自复动词第一人称 me levanto。"],
["¿___ es tu número?","Qué|Cuál|Cómo|Cuánto",1,"问号码/姓名用 cuál。"],
["El agua ___ fría.","es|está|son|están",1,"状态用 estar：está fría。"],
["Había mucha gente ___ la fiesta.","en|a|por|para",0,"「在派对上」en la fiesta。"]
];
document.getElementById("qStart").onclick = function(){
  var vs = [];
  var idxs = D.vocab.map(function(w,i){return i;});
  for(var i=idxs.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=idxs[i]; idxs[i]=idxs[j]; idxs[j]=t; }
  idxs.slice(0,10).forEach(function(i){
    var w = D.vocab[i];
    var wrong = D.vocab.filter(function(x){ return x.zh!==w.zh; });
    var opts = [w.zh];
    for(var k=0;k<3;k++){ opts.push(wrong[Math.floor(Math.random()*wrong.length)].zh); }
    opts.sort(function(){ return Math.random()-.5; });
    vs.push({ q:'“'+w.es+'” 的意思是？', o:opts, a:opts.indexOf(w.zh), e:w.es+' = '+w.zh+(w.ex?'。例句：'+w.ex:''), word:w });
  });
  QBS.forEach(function(r){ r.opts = r[1].split("|"); });
  var gs = QBS.slice().sort(function(){ return Math.random()-.5; }).slice(0,5);
  var items = vs.concat(gs.map(function(r){ return { q:r[0], o:r.opts, a:r[2], e:r[3], isG:true }; }));
  var qi = 0, right = 0, answered = false;
  document.getElementById("qSetup").style.display = "none";
  var qb = document.getElementById("qBody"); qb.style.display = "";
  function draw(){
    var it = items[qi];
    var h = '<div class="card"><div class="hint" style="margin-bottom:10px">第 '+(qi+1)+' / '+items.length+' 题 · 已答对 '+right+'</div>'
      + '<div style="font-size:14.5px;font-weight:700;margin-bottom:12px;line-height:1.6">'+it.q+'</div>';
    it.o.forEach(function(o,j){ h += '<div class="opt" data-j="'+j+'">'+o+'</div>'; });
    h += '<div id="qExp" style="display:none"></div></div>';
    qb.innerHTML = h;
    answered = false;
    qb.querySelectorAll(".opt").forEach(function(op){
      op.onclick = function(){
        if(answered) return; answered = true;
        var j = +op.dataset.j;
        var ok = j===it.a;
        if(ok) right++;
        else if(!it.isG && it.word){ touch(it.word.es, 3); }
        op.classList.add(ok?"right":"wrong");
        qb.querySelector('.opt[data-j="'+it.a+'"]').classList.add("right");
        var ex = document.getElementById("qExp");
        ex.style.display = "block";
        ex.innerHTML = '<b>'+(ok?"✅":"❌")+'</b> '+it.e+(ok?"":(it.word?" · 已加入遗忘曲线队列":""));
        
updSrsBadge();
        setTimeout(function(){
          qi++;
          if(qi<items.length) draw();
          else {
            qb.innerHTML = '<div class="card" style="text-align:center;padding:28px"><div style="font-size:38px;font-weight:900;color:var(--accent2)">'+right+' / '+items.length+'</div><div class="hint" style="margin-top:6px">得分率 '+Math.round(right/items.length*100)+'% · 错词已进入遗忘曲线复习</div><button class="btn" style="margin-top:14px" onclick="document.getElementById(\\'qSetup\\').style.display=\\'\\';document.getElementById(\\'qBody\\').style.display=\\'none\\'">再来一轮</button></div>';
          }
        }, 1100);
      };
    });
  }
  draw();
};

/* ===== 变位练习（历史沿用 spanish_verb_hist）===== */
var VH_KEY = "spanish_verb_hist";
function vHist(){ try{ return JSON.parse(localStorage.getItem(VH_KEY))||[] }catch(e){ return [] } }
document.getElementById("vqStart").onclick = function(){
  var bank = D.verbQuiz.slice().sort(function(){ return Math.random()-.5; }).slice(0,12);
  var qi = 0, ok = 0;
  var area = document.getElementById("verbQuizArea");
  function draw(){
    if(qi >= bank.length){
      var h = vHist(); h.push({ok:ok, total:bank.length, d:new Date().toLocaleString("zh-CN")});
      localStorage.setItem(VH_KEY, JSON.stringify(h.slice(-50)));
      window.__agMiscTouch && window.__agMiscTouch();
      area.innerHTML = '<div class="card"><b>本轮变位练习：'+ok+' / '+bank.length+'</b><div class="hint" style="margin-top:6px">已计入历史（沿用旧版练习记录）</div><button class="btn ghost" style="margin-top:8px" id="vqClose">关闭</button></div>';
      document.getElementById("vqClose").onclick = function(){ area.innerHTML = ""; };
      return;
    }
    var q = bank[qi];
    var distr = D.verbQuiz.filter(function(x){ return x.ans!==q.ans; }).sort(function(){ return Math.random()-.5; }).slice(0,3).map(function(x){ return x.ans; });
    var opts = distr.concat([q.ans]).sort(function(){ return Math.random()-.5; });
    area.innerHTML = '<div class="card"><div class="hint" style="margin-bottom:8px">第 '+(qi+1)+' / '+bank.length+' 题 · 已对 '+ok+'</div>'
      + '<div style="font-size:16px;font-weight:700">🎯 <b style="color:var(--accent2)">'+q.v+'</b> · '+q.tense+' · 主语 '+q.subj+'（'+q.person+'）</div>'
      + '<div class="hint" style="margin:4px 0 10px">'+q.hint+'</div>'
      + opts.map(function(o){ return '<div class="opt" data-a="'+o+'">'+o+'</div>'; }).join("")
      + '</div>';
    area.querySelectorAll(".opt").forEach(function(op){
      op.onclick = function(){
        var right = op.dataset.a === q.ans;
        if(right) ok++;
        op.classList.add(right?"right":"wrong");
        area.querySelectorAll(".opt").forEach(function(x){ if(x.dataset.a===q.ans) x.classList.add("right"); });
        setTimeout(function(){ qi++; draw(); }, 800);
      };
    });
  }
  draw();
};

/* ===== 每日一句（沿用 sp_daily 连续打卡）===== */
function norm(t){
  var map={'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'n','Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ü':'U','Ñ':'N','?':'?','¿':'?'};
  return String(t).toLowerCase().split("").map(function(c){ return map[c]||c; }).join("").replace(/[.,!?¡¿]/g,"").replace(/\s+/g," ").trim();
}
function drawDaily(){
  var today = new Date().toISOString().slice(0,10);
  var d;
  try{ d = JSON.parse(localStorage.getItem("sp_daily"))||{date:"",count:0}; }catch(e){ d = {date:"",count:0}; }
  if(d.date===today){ /* 已打卡 */ }
  var idx = Math.floor(new Date().getDate()*7 % D.daily.length);
  var sent = D.daily[idx];
  document.getElementById("dailyBox").innerHTML =
    '<h3>📅 每日一句 · 连续打卡 <b style="color:var(--accent2)">'+(d.count||0)+'</b> 天</h3>'
    + '<div style="font-size:17px;font-weight:800;margin:10px 0 4px">'+sent.es+'</div>'
    + '<div class="hint" style="font-size:13px;color:var(--text2)">'+sent.zh+'</div>'
    + '<button class="btn" id="dailyBtn" style="margin-top:12px" '+(d.date===today?'disabled':'')+'>'+(d.date===today?'✅ 今日已完成':'我学会了，打卡 +1')+'</button>';
  document.getElementById("dailyBtn").onclick = function(){
    var dd;
    try{ dd = JSON.parse(localStorage.getItem("sp_daily"))||{date:"",count:0}; }catch(e){ dd = {date:"",count:0}; }
    if(dd.date===today) return;
    var y = new Date(Date.now()-864e5).toISOString().slice(0,10);
    dd.count = (dd.date===y) ? (dd.count||0)+1 : 1;
    dd.date = today;
    localStorage.setItem("sp_daily", JSON.stringify(dd));
    window.__agMiscTouch && window.__agMiscTouch();
    drawDaily();
  };
}

/* ===== 句子训练 L1-L4（历史沿用 sp_history）===== */
var SPH_KEY = "sp_history";
function pushHist(type, correct, total){
  var h; try{ h = JSON.parse(localStorage.getItem(SPH_KEY))||[] }catch(e){ h = [] }
  h.push({type:type, correct:correct, total:total, d:new Date().toISOString().slice(0,16).replace('T',' ')});
  localStorage.setItem(SPH_KEY, JSON.stringify(h.slice(-100)));
  window.__agMiscTouch && window.__agMiscTouch();
}
var sentLv = 1;
function drawSentLv(){
  var lvNames = {1:"L1 变位填空", 2:"L2 点击组句", 3:"L3 中译西", 4:"L4 阅读理解"};
  var h = "";
  for(var i=1;i<=4;i++){ h += '<span class="chip'+(sentLv===i?" on":"")+'" data-l="'+i+'">'+lvNames[i]+'</span>'; }
  h += '<span class="hint" style="flex:100%;margin-top:4px">历史记录沿用旧版（sp_history），可在旧练习页看到全部数据</span>';
  document.getElementById("sentLv").innerHTML = h;
  document.querySelectorAll("#sentLv .chip").forEach(function(c){
    c.onclick = function(){ sentLv = +c.dataset.l; drawSentLv(); drawSent(); };
  });
}
function drawSent(){
  var area = document.getElementById("sentArea");
  var bank = D.sent[sentLv] || [];
  var items = bank.slice().sort(function(){ return Math.random()-.5; }).slice(0, 4);
  var h = "";
  if(sentLv === 1 || sentLv === 3){
    items.forEach(function(it, i){
      h += '<div class="card"><div class="hint" style="margin-bottom:6px">'+(sentLv===1?'填入动词的正确形式':'翻译成西班牙语')+'</div>'
        + '<div style="font-size:14.5px;font-weight:600;margin-bottom:4px">'+(sentLv===1? it.q : it.zh||it.q)+'</div>'
        + (it.hint ? '<div class="hint" style="margin-bottom:8px">💡 '+it.hint+'</div>' : '')
        + '<input class="q" id="si-'+i+'" placeholder="'+(sentLv===1?'输入动词变位':'输入西语句子')+'" style="max-width:100%">'
        + '<button class="btn" style="margin-top:8px" data-i="'+i+'">检查</button><div id="sf-'+i+'"></div></div>';
    });
  } else if(sentLv === 2){
    items.forEach(function(it, i){
      var pool = it.words.slice().sort(function(){ return Math.random()-.5; });
      h += '<div class="card"><div class="hint" style="margin-bottom:6px">点击单词组成句子</div>'
        + '<div style="font-size:14px;font-weight:600;margin-bottom:8px">'+it.zh+'</div>'
        + '<div class="chips" id="sc-'+i+'" style="margin-bottom:8px"></div>'
        + '<div class="chips" id="sp2-'+i+'"></div>'
        + '<button class="btn" style="margin-top:8px" data-i="'+i+'" data-check="1">检查</button><div id="sf-'+i+'"></div></div>';
    });
  } else {
    h = '<div class="card"><div style="font-size:14px;line-height:1.9;margin-bottom:10px">'+items[0].text+'</div>';
    items[0].qs.forEach(function(q, qi){
      h += '<div style="font-weight:700;margin:10px 0 6px">'+q.q+'</div>';
      q.opts.forEach(function(o, oi){ h += '<div class="opt" data-i="0" data-q="'+qi+'" data-o="'+oi+'">'+o+'</div>'; });
    });
    h += '<button class="btn" style="margin-top:10px" id="l4check">检查阅读题</button><div id="sf-0"></div></div>';
  }
  area.innerHTML = h;
  var answered = {};
  if(sentLv === 1 || sentLv === 3){
    area.querySelectorAll("button[data-i]").forEach(function(b){
      b.onclick = function(){
        var i = b.dataset.i, it = items[i];
        var val = document.getElementById("si-"+i).value;
        var ok = norm(val) === norm(it.ans);
        answered[i] = ok;
        document.getElementById("sf-"+i).innerHTML = '<div class="exp"><b>'+(ok?"✅":"❌")+'</b> 正确答案：'+it.ans+'</div>';
        if(Object.keys(answered).length === items.length) pushHist(sentLv===1?"L1填空":"L3翻译", Object.values(answered).filter(Boolean).length, items.length);
      };
    });
  } else if(sentLv === 2){
    var sel = {};
    items.forEach(function(it, i){
      sel[i] = [];
      var poolEl = document.getElementById("sp2-"+i), chipEl = document.getElementById("sc-"+i);
      function render2(){
        poolEl.innerHTML = it.words.map(function(w, wi){
          var used = sel[i].indexOf(wi) >= 0;
          return '<span class="chip" data-w="'+wi+'" style="'+(used?"opacity:.3":"")+'">'+w+'</span>';
        }).join("");
        chipEl.innerHTML = sel[i].map(function(wi){ return '<span class="chip on" data-back="'+wi+'">'+it.words[wi]+'</span>'; }).join("");
        poolEl.querySelectorAll(".chip:not([data-back])").forEach(function(c){
          if(c.style.opacity === "0.3") return;
          c.onclick = function(){ sel[i].push(+c.dataset.w); render2(); };
        });
        chipEl.querySelectorAll(".chip").forEach(function(c){
          c.onclick = function(){ sel[i] = sel[i].filter(function(x){ return x !== +c.dataset.back; }); render2(); };
        });
      }
      render2();
    });
    area.querySelectorAll("button[data-check]").forEach(function(b){
      b.onclick = function(){
        var i = b.dataset.i, it = items[i];
        var built = sel[i].map(function(wi){ return it.words[wi]; }).join(" ");
        var ok = norm(built) === norm(it.ans);
        answered[i] = ok;
        document.getElementById("sf-"+i).innerHTML = '<div class="exp"><b>'+(ok?"✅":"❌")+'</b> 正确答案：'+it.ans+'</div>';
        if(Object.keys(answered).length === items.length) pushHist("L2组句", Object.values(answered).filter(Boolean).length, items.length);
      };
    });
  } else if(sentLv === 4){
    var picks = {};
    area.querySelectorAll(".opt").forEach(function(o){
      o.onclick = function(){
        picks[o.dataset.q] = +o.dataset.o;
        o.parentNode.querySelectorAll(".opt").forEach(function(x){ x.classList.remove("right"); });
        o.classList.add("sel");
      };
    });
    document.getElementById("l4check").onclick = function(){
      var qs = items[0].qs, ok = 0;
      qs.forEach(function(q, qi){ if(picks[qi] === q.ans) ok++; });
      qs.forEach(function(q, qi){
        area.querySelectorAll('.opt[data-q="'+qi+'"]').forEach(function(x){ if(+x.dataset.o === q.ans) x.classList.add("right"); else if(picks[qi]===+x.dataset.o) x.classList.add("wrong"); });
      });
      document.getElementById("sf-0").innerHTML = '<div class="exp"><b>阅读得分：'+ok+' / '+qs.length+'</b></div>';
      pushHist("L4阅读", ok, qs.length);
    };
  }
}

/* ===== 旅行场景 ===== */
var travelSel = null;
function drawTravel(){
  var h = "";
  for(var name in D.travel){ h += '<span class="chip'+(travelSel===name?" on":"")+'" data-n="'+name+'">'+name+'（'+D.travel[name].length+'）</span>'; }
  document.getElementById("travelChips").innerHTML = h;
  document.querySelectorAll("#travelChips .chip").forEach(function(c){
    c.onclick = function(){ travelSel = c.dataset.n; drawTravel(); };
  });
  var area = document.getElementById("travelArea");
  if(!travelSel){ area.innerHTML = '<div class="empty">选择场景查看常用句</div>'; return; }
  var list = D.travel[travelSel];
  area.innerHTML = list.map(function(x){
    return '<div class="exp" style="margin-bottom:8px"><b>'+x.es+'</b><br><i>'+x.zh+'</i></div>';
  }).join("");
}

/* tab 切换挂载句子训练 */
(function(){
  var origTabs = document.querySelectorAll(".tab");
  origTabs.forEach(function(t){
    if(t.dataset.p === "sent"){
      t.addEventListener("click", function(){ drawDaily(); drawSentLv(); drawSent(); drawTravel(); });
    }
  });
})();

updSrsBadge();
updSrsBadge();
applyLang();
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", DATA)
open(DEST, "w", encoding="utf-8").write(HTML)
print("生成:", DEST, len(HTML), "字符")

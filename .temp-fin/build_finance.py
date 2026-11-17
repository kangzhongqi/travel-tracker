# -*- coding: utf-8 -*-
"""组装金融合体版 agent-finance.html：v2 考试引擎 + 学习中心（合并题库/54卡/错题SRS/历史/12篇深度讲解）"""
import json, re

OUT = "/Users/kangzhongqi/Desktop/travel-tracker-pages/.temp-fin"
SRC = "/Users/kangzhongqi/Library/CloudStorage/OneDrive-个人/金融知识测评-v2/金融知识在线测评.html"
DEST = "/Users/kangzhongqi/Desktop/travel-tracker-pages/agent-finance.html"

questions = json.load(open(OUT + "/merged_questions.json", encoding="utf-8"))
kps = json.load(open(OUT + "/merged_kps.json", encoding="utf-8"))
ch_names = json.load(open(OUT + "/ch_names.json", encoding="utf-8"))
deep = json.load(open(OUT + "/deep_articles.json", encoding="utf-8"))

html = open(SRC, encoding="utf-8").read()

DATA_JS = "window.LEARN = " + json.dumps({
    "questions": questions, "kps": kps, "chNames": ch_names, "deep": deep
}, ensure_ascii=False, separators=(",", ":")) + ";\n"

HUB_HTML = """
<div id="learnhub" style="max-width:960px;margin:26px auto 60px;padding:0 16px;display:none">
  <div class="lh-card" style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;box-shadow:0 1px 3px rgba(26,60,110,.06)">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px">
      <div style="width:34px;height:34px;border-radius:8px;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800">学</div>
      <div><b style="font-size:16px">学习中心</b> <span style="color:var(--sub);font-size:12px">· 合并题库 114 题 · 8 章 54 卡 · 12 篇深度讲解</span></div>
      <button id="lh-close" style="margin-left:auto;border:none;background:var(--bg);border-radius:8px;padding:6px 12px;cursor:pointer;color:var(--sub)">收起 ✕</button>
    </div>
    <div class="lh-tabs" style="display:flex;gap:8px;flex-wrap:wrap;border-bottom:2px solid var(--line);padding-bottom:10px;margin-bottom:14px">
      <button class="lh-tab on" data-t="practice" style="border:1px solid var(--navy);background:var(--navy);color:#fff;border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600">✍️ 题库练习</button>
      <button class="lh-tab" data-t="kp" style="border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600">🃏 知识点</button>
      <button class="lh-tab" data-t="wrong" style="border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600">❌ 错题复习<span id="lh-wrongbadge" style="display:none;background:var(--no);color:#fff;border-radius:10px;padding:1px 7px;margin-left:4px;font-size:11px">0</span></button>
      <button class="lh-tab" data-t="hist" style="border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600">📊 记录</button>
      <button class="lh-tab" data-t="deep" style="border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600">📖 深度讲解</button>
    </div>
    <div id="lh-body"></div>
  </div>
</div>
<style>
.lh-opt{display:block;border:1.5px solid var(--line);border-radius:10px;padding:10px 12px;margin:6px 0;cursor:pointer;font-size:13.5px;line-height:1.5}
.lh-opt:hover{border-color:var(--navy)}
.lh-opt.sel{border-color:var(--navy);background:#eef3fb}
.lh-opt.right{border-color:var(--ok);background:var(--okbg)}
.lh-opt.wrong{border-color:var(--no);background:var(--nobg)}
.lh-chip{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:5px 12px;cursor:pointer;font-size:12px;color:var(--sub);white-space:nowrap}
.lh-chip.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.lh-q{border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:12px;background:var(--card)}
.lh-meta{font-size:11px;color:var(--sub);display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.lh-exp{margin-top:10px;background:#f6f8fc;border-left:3px solid var(--navy);border-radius:8px;padding:11px 13px;font-size:12.5px;line-height:1.7}
.lh-kpc{margin-top:8px;border:1px dashed var(--gold);border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.7}
.lh-btn{background:var(--navy);color:#fff;border:none;border-radius:9px;padding:9px 18px;cursor:pointer;font-size:13px;font-weight:600}
.lh-btn:hover{filter:brightness(1.1)}
.lh-btn.ghost{background:var(--card);color:var(--sub);border:1px solid var(--line)}
.lh-article{border:1px solid var(--line);border-radius:12px;margin-bottom:10px;overflow:hidden}
.lh-article h4{background:var(--navy);color:#fff;margin:0;padding:11px 14px;font-size:14px;cursor:pointer}
.lh-article .body{display:none;padding:14px 16px;font-size:13.5px;line-height:1.9;background:var(--card)}
.lh-article.open .body{display:block}
.lh-stat{display:inline-block;border:1px solid var(--line);border-radius:10px;padding:10px 16px;margin:4px;font-size:12px;background:var(--bg)}
@media print{#learnhub,.siteauth-badge{display:none!important}}
</style>
"""

HUB_JS = r"""
<script>
(function(){
  var L = window.LEARN;
  var K = { wrong:"fin_wrongbook_v1", hist:"fin_history_v1", srs:"fin_srs_v1", examState:"fin_exam_state_v1" };
  var TYPE_NAMES = {single:"单选", multiple:"多选", judge:"判断"};
  var DIFF_NAMES = {easy:"基础", medium:"进阶", hard:"较难"};
  var LET = ["A","B","C","D","E","F"];
  function load(k,d){ try{ var v = JSON.parse(localStorage.getItem(k)); return v==null?d:v }catch(e){ return d } }
  function save(k,v){ localStorage.setItem(k, JSON.stringify(v)); window.__agMiscTouch && window.__agMiscTouch(); }
  var wrong = load(K.wrong, []);
  var hist = load(K.hist, []);
  var srs = load(K.srs, {});
  var qmap = {}; L.questions.forEach(function(q){ qmap[q.id]=q; });
  var kmap = {}; L.kps.forEach(function(p){ kmap[p.id]=p; });

  // 考试交卷后的错题并入错题本（读取考试持久状态）
  (function mergeExam(){
    try{
      var st = load(K.examState, null);
      if(st && st.results && st.results.wrongIds && st.results.wrongIds.length){
        st.results.wrongIds.forEach(function(id){
          if(wrong.indexOf(id) < 0) wrong.push(id);
          srs[id] = srs[id] || {due: Date.now(), streak: 0};
        });
        save(K.wrong, wrong); save(K.srs, srs);
      }
    }catch(e){}
  })();

  var hub = document.getElementById("learnhub");
  var body = document.getElementById("lh-body");
  // 顶部入口：intro 的按钮排
  var ia = document.getElementById("introActions");
  if(ia){
    var b = document.createElement("button");
    b.className = "btn"; b.style.cssText = "background:var(--navy)";
    b.textContent = "📚 学习中心（题库练习 · 知识点 · 错题复习）";
    b.onclick = function(){ hub.style.display="block"; hub.scrollIntoView({behavior:"smooth"}); };
    ia.appendChild(b);
  }
  document.getElementById("lh-close").onclick = function(){ hub.style.display="none"; };
  function updBadge(){
    var due = Object.keys(srs).filter(function(id){ return srs[id] && srs[id].due <= Date.now() && qmap[id]; });
    var el = document.getElementById("lh-wrongbadge");
    if(wrong.length){ el.style.display=""; el.textContent = wrong.length + (due.length ? " · 今日到期 " + due.length : ""); }
  }
  updBadge();

  document.querySelectorAll(".lh-tab").forEach(function(t){
    t.onclick = function(){
      document.querySelectorAll(".lh-tab").forEach(function(x){ x.className = "lh-tab"; x.style.cssText = "border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600"; });
      t.className = "lh-tab on"; t.style.cssText = "border:1px solid var(--navy);background:var(--navy);color:#fff;border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600";
      render(t.dataset.t);
    };
  });

  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]; }); }

  /* ---------- 题库练习 ---------- */
  var pf = { ch:"all", type:"all", dif:"all", order:"seq", list:[], idx:0, answers:{} };
  function renderPractice(){
    var chips = function(cur, key, map, allLabel){
      var h = '<span class="lh-chip'+(cur==="all"?" on":"")+'" data-k="'+key+'" data-v="all">'+allLabel+'</span>';
      for(var k in map){ h += '<span class="lh-chip'+(cur===k?" on":"")+'" data-k="'+key+'" data-v="'+k+'">'+map[k]+'</span>'; }
      return h;
    };
    body.innerHTML = '<div style="font-size:12px;color:var(--sub);margin-bottom:6px">章节</div>'
      + '<div style="margin-bottom:8px" id="pf-ch">'+chips(pf.ch,"ch",L.chNames,"全部")+'</div>'
      + '<div style="font-size:12px;color:var(--sub);margin-bottom:6px">题型 / 难度 / 顺序</div>'
      + '<div style="margin-bottom:12px">'
      + chips(pf.type,"type",TYPE_NAMES,"全部") + ' '
      + chips(pf.dif,"dif",DIFF_NAMES,"全部") + ' '
      + '<span class="lh-chip'+(pf.order==="rand"?" on":"")+'" data-k="order" data-v="rand">随机顺序</span> '
      + '<button class="lh-btn" id="pf-go" style="margin-left:8px">开始练习</button>'
      + '</div><div id="pf-area"></div>';
    body.querySelectorAll(".lh-chip").forEach(function(c){
      c.onclick = function(){ pf[c.dataset.k] = c.dataset.v; renderPractice(); };
    });
    document.getElementById("pf-go").onclick = function(){
      var pool = L.questions.filter(function(q){
        return (pf.ch==="all"||q.chapter_id===pf.ch) && (pf.type==="all"||q.type===pf.type) && (pf.dif==="all"||q.difficulty===pf.dif);
      });
      if(pf.order==="rand") pool.sort(function(){ return Math.random()-0.5; });
      pf.list = pool; pf.idx = 0; pf.answers = {};
      drawQ();
    };
    drawIntroStat();
  }
  function drawIntroStat(){
    var a = document.getElementById("pf-area");
    if(a) a.innerHTML = '<div style="color:var(--sub);font-size:12.5px;padding:6px 2px">共库 114 题（v2 考试题库 74 + 精选补充 40）· 选择条件后点「开始练习」，逐题作答即时判分并计入错题本</div>';
  }
  function drawQ(){
    var a = document.getElementById("pf-area"); if(!a) return;
    if(!pf.list.length){ drawIntroStat(); return; }
    if(pf.idx >= pf.list.length){
      var ok = 0; pf.list.forEach(function(q){ if(pf.answers[q.id] && isOk(q, pf.answers[q.id])) ok++; });
      a.innerHTML = '<div class="lh-q"><b>本轮练习完成</b><div style="margin-top:8px;font-size:13px">答对 '+ok+' / '+pf.list.length+' 题 · 答错的题已进入错题复习（遗忘曲线队列）</div><button class="lh-btn" style="margin-top:10px" onclick="location.reload()">再来一轮</button></div>';
      return;
    }
    var q = pf.list[pf.idx];
    var h = '<div class="lh-q"><div class="lh-meta"><span style="color:var(--navy);font-weight:700">'+L.chNames[q.chapter_id]+'</span><span>'+TYPE_NAMES[q.type]+'</span><span>'+DIFF_NAMES[q.difficulty]+'</span><span>第 '+(pf.idx+1)+' / '+pf.list.length+' 题</span>'+(wrong.indexOf(q.id)>=0?'<span style="color:var(--no)">曾错</span>':'')+'</div>'
      + '<div style="font-size:14.5px;font-weight:600;line-height:1.6;margin-bottom:8px">'+esc(q.stem)+'</div>';
    if(q.type==="judge"){ h += '<div class="lh-opt" data-v="正确">正确</div><div class="lh-opt" data-v="错误">错误</div>'; }
    else { q.options.forEach(function(o,i){ h += '<div class="lh-opt" data-v="'+LET[i]+'">'+LET[i]+'. '+esc(o)+'</div>'; }); }
    h += '<div id="pf-exp"></div></div>';
    a.innerHTML = h;
    var picked = [];
    a.querySelectorAll(".lh-opt").forEach(function(o){
      o.onclick = function(){
        if(a.getAttribute("data-done")) return;
        if(q.type==="multiple"){
          o.classList.toggle("sel");
          var v = o.dataset.v;
          var ix = picked.indexOf(v); if(ix>=0) picked.splice(ix,1); else picked.push(v);
        } else {
          a.querySelectorAll(".lh-opt").forEach(function(x){ x.classList.remove("sel"); });
          picked = [o.dataset.v];
          a.setAttribute("data-done","1");
          judge(q, picked, a);
        }
      };
    });
    if(q.type==="multiple"){
      var sub = document.createElement("button"); sub.className="lh-btn"; sub.textContent="提交本题"; sub.style.marginTop="8px";
      sub.onclick = function(){ if(!picked.length) return; a.setAttribute("data-done","1"); judge(q, picked, a); };
      a.appendChild(sub);
    }
  }
  function isOk(q, ua){
    var ca = Array.isArray(q.answer) ? q.answer.slice().sort() : [q.answer];
    var u = ua.slice().sort();
    return u.length===ca.length && u.every(function(x,i){ return x===ca[i]; });
  }
  function judge(q, ua, area){
    var ok = isOk(q, ua);
    var ca = Array.isArray(q.answer) ? q.answer.slice().sort().join("") : q.answer;
    area.querySelectorAll(".lh-opt").forEach(function(o){
      var v = o.dataset.v;
      if(Array.isArray(q.answer) ? q.answer.indexOf(v)>=0 : v===q.answer) o.classList.add("right");
      else if(ua.indexOf(v)>=0) o.classList.add("wrong");
    });
    // 错题入库 + SRS
    if(!ok){
      if(wrong.indexOf(q.id)<0) wrong.push(q.id);
      srs[q.id] = srs[q.id] || {due: Date.now(), streak: 0};
    } else if(srs[q.id] && srs[q.id].streak >= 0){
      // 练习答对不提前消除 SRS（按复习队列来）
    }
    save(K.wrong, wrong); save(K.srs, srs); updBadge();
    var kp = q.kp_id && kmap[q.kp_id];
    var exp = document.getElementById("pf-exp");
    exp.innerHTML = '<div class="lh-exp"><b style="color:'+(ok?"var(--ok)":"var(--no)")+'">'+(ok?"✅ 答对":"❌ 答错，已加入复习队列")+'</b> · 正确答案：<b>'+ca+'</b><br>'+esc(q.analysis||"")+'</div>'
      + (kp ? '<div class="lh-kpc"><b>📖 关联知识点：'+esc(kp.title)+'</b><br>'+esc(kp.content)+'</div>' : "");
    var nx = document.createElement("button"); nx.className="lh-btn"; nx.textContent="下一题 →"; nx.style.marginTop="10px";
    nx.onclick = function(){ pf.idx++; drawQ(); };
    area.appendChild(nx);
  }

  /* ---------- 知识点卡 ---------- */
  function renderKp(){
    var h = '<div id="kp-ch2" style="margin-bottom:10px"></div><div id="kp-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px"></div>';
    body.innerHTML = h;
    var chips = '<span class="lh-chip on" data-v="all">全部（'+L.kps.length+'）</span>';
    for(var c in L.chNames){ chips += '<span class="lh-chip" data-v="'+c+'">'+L.chNames[c]+'</span>'; }
    document.getElementById("kp-ch2").innerHTML = chips;
    document.querySelectorAll("#kp-ch2 .lh-chip").forEach(function(x){
      x.onclick = function(){
        document.querySelectorAll("#kp-ch2 .lh-chip").forEach(function(y){ y.className="lh-chip"; });
        x.className = "lh-chip on";
        drawKp(x.dataset.v);
      };
    });
    drawKp("all");
  }
  function drawKp(ch){
    var list = L.kps.filter(function(p){ return ch==="all"||p.chapter_id===ch; });
    document.getElementById("kp-grid").innerHTML = list.map(function(p){
      return '<div class="lh-q" style="margin:0"><div class="lh-meta"><span style="color:var(--navy);font-weight:700">'+L.chNames[p.chapter_id]+'</span></div><b style="font-size:14px">'+esc(p.title)+'</b><div style="font-size:12.5px;line-height:1.7;color:var(--sub);margin-top:6px">'+esc(p.content)+'</div></div>';
    }).join("") || '<div style="color:var(--sub);font-size:13px">本章暂无卡片</div>';
  }

  /* ---------- 错题复习（SRS） ---------- */
  function renderWrong(){
    var due = [];
    var future = 0;
    wrong.forEach(function(id){ if(qmap[id] && srs[id]){ if(srs[id].due<=Date.now()) due.push(id); else future++; } });
    var h = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">'
      + '<span class="lh-stat">错题本：<b>'+wrong.length+'</b> 题</span>'
      + '<span class="lh-stat">今日到期复习：<b style="color:'+(due.length?"var(--warn)":"var(--ok)")+'">'+due.length+'</b> 题</span>'
      + '<span class="lh-stat">排期中：'+future+' 题</span>'
      + '<button class="lh-btn ghost" id="wr-clear">清空错题本</button></div><div id="wr-area"></div>';
    body.innerHTML = h;
    document.getElementById("wr-clear").onclick = function(){
      if(!confirm("清空全部错题与复习队列？")) return;
      wrong = []; srs = {}; save(K.wrong, wrong); save(K.srs, srs); updBadge(); renderWrong();
    };
    var area = document.getElementById("wr-area");
    if(!due.length){
      area.innerHTML = '<div style="color:var(--sub);font-size:13px;padding:16px 0">今日没有到期的复习题 🎉</div>';
      return;
    }
    var id = due[0];
    var q = qmap[id];
    var h2 = '<div class="lh-q"><div class="lh-meta"><span style="color:var(--navy);font-weight:700">'+L.chNames[q.chapter_id]+'</span><span>'+TYPE_NAMES[q.type]+'</span><span>还剩 '+due.length+' 题到期</span></div>'
      + '<div style="font-size:14.5px;font-weight:600;line-height:1.6;margin-bottom:8px">'+esc(q.stem)+'</div>';
    if(q.type==="judge"){ h2 += '<div class="lh-opt" data-v="正确">正确</div><div class="lh-opt" data-v="错误">错误</div>'; }
    else { q.options.forEach(function(o,i){ h2 += '<div class="lh-opt" data-v="'+LET[i]+'">'+LET[i]+'. '+esc(o)+'</div>'; }); }
    h2 += '</div>';
    area.innerHTML = h2;
    area.querySelectorAll(".lh-opt").forEach(function(o){
      o.onclick = function(){
        var ok = isOk(q, [o.dataset.v]);
        area.querySelectorAll(".lh-opt").forEach(function(x){
          var v = x.dataset.v;
          if(v===q.answer) x.classList.add("right"); else if(v===o.dataset.v && !ok) x.classList.add("wrong");
        });
        // SRS 更新：对→间隔拉长，错→明天再见
        var s = srs[id] || {streak:0};
        if(ok){ s.streak = (s.streak||0)+1; s.due = Date.now() + [1,2,4,7,15,30][Math.min(s.streak-1,5)]*86400000; }
        else { s.streak = 0; s.due = Date.now() + 86400000; }
        srs[id] = s;
        // 连续答对 3 次移出错题本
        if(ok && s.streak>=3){ wrong = wrong.filter(function(x){ return x!==id; }); delete srs[id]; }
        save(K.wrong, wrong); save(K.srs, srs); updBadge();
        var kp = q.kp_id && kmap[q.kp_id];
        area.insertAdjacentHTML("beforeend", '<div class="lh-exp"><b style="color:'+(ok?"var(--ok)":"var(--no)")+'">'+(ok?"✅ 答对 · "+(s.streak>=3?"已移出错题本":"间隔已延长"):"❌ 答错 · 明天再见")+'</b> · 正确答案：<b>'+q.answer+'</b><br>'+esc(q.analysis||"")+'</div>'+(kp?'<div class="lh-kpc"><b>📖 '+esc(kp.title)+'</b><br>'+esc(kp.content)+'</div>':'')+'<button class="lh-btn" style="margin-top:10px" id="wr-next">下一题 →</button>');
        document.getElementById("wr-next").onclick = renderWrong;
      };
    });
  }

  /* ---------- 记录 ---------- */
  function renderHist(){
    var rows = hist.slice(0, 20).map(function(r){
      return '<tr><td style="padding:7px 8px;border-bottom:1px solid var(--line);font-size:12.5px">'+esc(r.d)+'</td><td style="padding:7px 8px;border-bottom:1px solid var(--line);font-size:12.5px">'+esc(r.m)+'</td><td style="padding:7px 8px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--navy);font-weight:700">'+r.s+' / '+r.t+'</td><td style="padding:7px 8px;border-bottom:1px solid var(--line);font-size:12.5px">'+r.rate+'%</td></tr>';
    }).join("");
    body.innerHTML = '<div style="display:flex;gap:8px;align-items:center;margin-bottom:10px"><b>练习与考试记录（本机保存 20 条）</b><button class="lh-btn ghost" id="hs-clear">清空</button></div>'
      + '<table style="width:100%;border-collapse:collapse"><tr><th style="padding:7px 8px;text-align:left;font-size:11px;color:var(--sub)">时间</th><th style="padding:7px 8px;text-align:left;font-size:11px;color:var(--sub)">类型</th><th style="padding:7px 8px;text-align:left;font-size:11px;color:var(--sub)">得分</th><th style="padding:7px 8px;text-align:left;font-size:11px;color:var(--sub)">正确率</th></tr>'+(rows||'<tr><td colspan="4" style="padding:16px;text-align:center;color:var(--sub)">暂无记录，去练习或考试吧</td></tr>')+'</table>';
    document.getElementById("hs-clear").onclick = function(){ if(!confirm("清空记录？"))return; hist=[]; save(K.hist,hist); renderHist(); };
  }
  // hook：考试交卷时写历史（包装原 submitExam）
  try{
    var orig = window.submitExam;
    if(orig){
      window.submitExam = function(){
        orig();
        try{
          var st = load(K.examState, null);
          if(st && st.results){
            hist.unshift({ d: new Date().toLocaleString("zh-CN"), m: "正式测评", s: st.results.total, t: st.results.full, rate: Math.round(st.results.total/st.results.full*100) });
            hist = hist.slice(0,20); save(K.hist, hist);
          }
        }catch(e){}
      };
    }
  }catch(e){}

  /* ---------- 深度讲解 ---------- */
  function renderDeep(){
    body.innerHTML = L.deep.map(function(a, i){
      return '<div class="lh-article" id="da-'+a.id+'"><h4 onclick="this.parentNode.classList.toggle(\'open\')">'+(i+1)+'. '+esc(a.title)+' <span style="float:right;font-weight:400;font-size:12px;opacity:.8">'+esc(L.chNames[a.ch]||"")+' · 点击展开</span></h4><div class="body">'+esc(a.body)+'</div></div>';
    }).join("");
  }

  function render(t){
    if(t==="practice") renderPractice();
    else if(t==="kp") renderKp();
    else if(t==="wrong") renderWrong();
    else if(t==="hist") renderHist();
    else if(t==="deep") renderDeep();
  }
  render("practice");
})();
</script>
"""

# 注入：数据 + 学习中心 DOM（放在 intro 后）+ 学习中心 JS + site-auth
html = html.replace("</body>",
    DATA_JS.replace("window.LEARN = ", "<script>window.LEARN = ").replace(";\n", ";</script>\n")
    + HUB_HTML
    + HUB_JS
    + '<script src="site-auth.js?v=3"></script>\n</body>', 1)

# 题库练习计分写入历史的练习侧（在 drawQ 完成处已写错题；补充历史）
html = html.replace("答对的题已进入错题复习（遗忘曲线队列）",
    "答对的题已计入记录，错题已进入遗忘曲线复习队列")

open(DEST, "w", encoding="utf-8").write(html)
print("生成:", DEST, len(html), "字符")
PYEOF_MARK = None

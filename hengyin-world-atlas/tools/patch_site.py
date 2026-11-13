# -*- coding: utf-8 -*-
"""
第一版网页 → 统一数据层网页的一次性结构补丁（可重复运行，已打补丁则跳过）。

只做结构改造，不写任何实体数据：实体数据全部由 tools/build_kb.py 注入的
#kb-data / #ai-pack-b64 / #beasts-json 数据岛提供。
"""
from pathlib import Path
import re, sys

P = Path(__file__).resolve().parent.parent / "衡垠世界图集.html"
s = P.read_text(encoding="utf-8")
if "/* KB-V2-PATCHED */" in s:
    print("已打过补丁，跳过。")
    sys.exit(0)


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise RuntimeError("找不到替换锚点：" + label)
    s = s.replace(old, new, count)
    print("  ✓", label)


# ---------------------------------------------------------------- CSS
CSS = r"""
/* ============ 统一数据层 · v2.0 ============ */
.r-badge{font-size:10px;letter-spacing:.04em;padding:1px 5px;border:1px solid var(--line);color:var(--ink-faint);margin-left:6px;vertical-align:1px;white-space:nowrap}
.r-badge.proposed{border-color:var(--copper-pale);color:var(--copper)}
.r-badge.uncertain{border-color:var(--river-pale);color:var(--river)}
.r-badge.revised{border-color:var(--river-2);color:var(--river)}
.kb-tag{display:inline-block;font-size:10.5px;letter-spacing:.06em;padding:2px 8px;border:1px solid var(--line);color:var(--ink-faint);margin:0 6px 6px 0;background:rgba(255,255,255,.45);white-space:nowrap}
.kb-tag.s-existing{border-color:var(--river-pale);color:var(--river)}
.kb-tag.s-proposed{border-color:var(--copper-pale);color:var(--copper);background:rgba(156,107,67,.07)}
.kb-tag.s-uncertain{border-color:var(--line);color:var(--ink-faint)}
.kb-tag.c-full{border-color:var(--river-2);color:var(--river)}
.kb-tag.c-index{background:transparent}
.kb-card{border:1px solid var(--line);background:rgba(255,255,255,.5);padding:22px 24px;margin:0 0 18px}
.kb-card h3{font-family:var(--serif);font-size:17px;margin:0 0 10px}
.kb-card p{font-size:13.5px;line-height:1.95;color:var(--ink-soft);margin:0 0 10px}
.kb-table{width:100%;font-size:13px}
.kb-table th{font-size:12px;letter-spacing:.04em}
.kb-table td{vertical-align:top}
.kb-table a{border-bottom:1px solid var(--river-pale)}
.kb-table a:hover{border-bottom-color:var(--copper)}
.kb-doc{font-size:13.5px;line-height:1.95;color:#26313d}
.kb-doc h3,.kb-doc h4,.kb-doc h5{font-family:var(--serif);margin:22px 0 8px;color:var(--ink)}
.kb-doc .kb-p{margin:0 0 12px;text-indent:0}
.kb-doc .kb-ul{margin:0 0 14px;padding-left:22px}
.kb-doc .kb-ul li{margin:3px 0}
.kb-doc hr{border:0;border-top:1px solid var(--line);margin:22px 0}
.kb-doc code{font-size:12px;background:var(--paper-2);padding:1px 4px}
.kb-doc table{margin:12px 0 18px}
.kb-details{border:1px solid var(--line);background:rgba(255,255,255,.4);margin:0 0 12px}
.kb-details summary{cursor:pointer;padding:12px 18px;font-family:var(--serif);font-size:15px;letter-spacing:.04em}
.kb-details .kb-doc{padding:4px 20px 18px;border-top:1px solid var(--line-soft)}
.kb-meta{border:1px solid var(--line);margin:22px 0;background:rgba(255,255,255,.45)}
.kb-meta .kb-row{display:grid;grid-template-columns:150px 1fr;border-bottom:1px solid var(--line-soft)}
.kb-meta .kb-row:last-child{border-bottom:0}
.kb-meta .kb-k{padding:9px 14px;font-size:12px;color:var(--ink-faint);border-right:1px solid var(--line-soft);background:rgba(255,255,255,.35)}
.kb-meta .kb-v{padding:9px 14px;font-size:13.5px;line-height:1.85}
.kb-rel{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 0}
.kb-rel a{display:inline-flex;gap:8px;align-items:baseline;border:1px solid var(--line);padding:7px 11px;font-size:12.5px;background:rgba(255,255,255,.5)}
.kb-rel a:hover{border-color:var(--copper)}
.kb-rel a span{font-size:10.5px;color:var(--ink-faint)}
.kb-btns{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 4px}
.kb-big{display:inline-flex;align-items:center;gap:10px;padding:15px 26px;font-family:var(--serif);font-size:17px;letter-spacing:.06em;border:1px solid var(--river);background:var(--river);color:#f7f4ec;cursor:pointer}
.kb-big:hover{background:#244b5c}
.kb-small{font-size:11.5px;color:var(--ink-faint);margin-top:10px;line-height:1.85}
.kb-warn{border-left:3px solid var(--copper);background:rgba(156,107,67,.07);padding:14px 18px;font-size:13px;line-height:1.9;margin:18px 0}
.kb-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:18px 0}
.kb-stat{border:1px solid var(--line);padding:16px 18px;background:rgba(255,255,255,.5)}
.kb-stat b{display:block;font-family:var(--serif);font-size:27px;line-height:1.3;color:var(--ink)}
.kb-stat span{font-size:11.5px;color:var(--ink-faint);letter-spacing:.06em}
.kb-list{font-size:12.5px;color:var(--ink-soft);line-height:1.9;margin:0;padding-left:20px}
.mp-link{display:inline-block;margin-top:10px;font-size:12px;border-bottom:1px solid var(--river-pale)}
.mp-link:hover{border-bottom-color:var(--copper)}
.kb-empty{padding:26px 0;font-size:13.5px;color:var(--ink-faint)}
@media(max-width:900px){
  .kb-grid{grid-template-columns:1fr}
  .kb-meta .kb-row{grid-template-columns:100px 1fr}
  .kb-table{font-size:12px}
  .kb-big{width:100%;justify-content:center}
}
"""
rep("</style>", CSS + "\n</style>", "CSS")

# ---------------------------------------------------------------- 导航
rep('<a href="#/status" data-nav="status">建设状态</a>',
    '<a href="#/status" data-nav="status">建设状态</a>\n      <a href="#/entities" data-nav="entities">档案</a>\n      <a href="#/export" data-nav="export">导出</a>',
    "导航新增档案/导出")

# ---------------------------------------------------------------- 关联链接修正
rep('<a href="#/yunqi">蛊坊街 <span>LOC-101-0340</span></a>',
    '<a href="#/entity/LOC-101-0340">蛊坊街 <span>LOC-101-0340</span></a>', "蛊坊街链接")
rep('<a href="#/yunqi">北城公交枢纽 <span>LOC-101-0104</span></a>',
    '<a href="#/entity/LOC-101-0104">北城公交枢纽 <span>LOC-101-0104</span></a>', "公交枢纽链接")
rep('<tr><td><a href="#/garden">第二小学</a></td>',
    '<tr><td><a href="#/entity/LOC-101-0318">第二小学</a></td>', "第二小学链接")
rep('<a href="#/beicheng">屏岭街道 <span>距城区 6 km</span></a>',
    '<a href="#/entity/LOC-101-0306">屏岭街道 <span>距城区 6 km</span></a>', "屏岭街道链接")
rep('<a href="#/garden">云栖河下游 <span>REALM-064</span></a>',
    '<a href="#/entity/REALM-064">云栖河下游 <span>REALM-064</span></a>', "云栖河水眼链接")
rep('<a href="#/realms">临江五处秘境 <span>REALM-012 · 061—064</span></a>',
    '<a href="#/entity/REALM-012">临江五处秘境 <span>REALM-012 · 061—064</span></a>', "临江秘境链接")

# ---------------------------------------------------------------- 建设状态：口径与统计
rep('共 36 条索引项（含十二种妖兽与野生仙蛊 O-G-110）。',
    '第一版为 36 条硬编码索引；本阶段已改为读取统一实体索引（<span id="statEntCount">…</span> 条，含资料状态与完整度），见下方「统一数据层」。',
    "搜索条数口径")
rep('蛊道全量 1,176 条仅接入 5 条；',
    '蛊道总目 1,176 条（C-G 684＋C-K 447＋O-G 32＋O-K 13），页面展示 5 条，其中 4 条属于总目、1 条为 O-G-110 额外登记条目，未接入 1,172 条（口径见 C-05）；',
    "蛊道数字口径")
rep('本站是本地单文件版本：双击即可打开，不依赖服务器与账号。下面如实列出已接通的内容、仍为框架的模块，以及原始资料里尚未解决的冲突。',
    '本站是本地单文件版本：双击即可打开，不依赖服务器与账号；也可用「启动网站.bat」开本地服务。下面如实列出已接通的内容、仍为框架的模块，以及原始资料里尚未解决的冲突。本阶段新增的统一数据层统计见页面末尾。',
    "状态页说明")
rep('    <p class="t" style="max-width:760px">本站的小说式文字只做“基于既有事实的呈现”，不新增历史事件、居民身份、案件或蛊师活动；凡新增空间细节，均在页面内标注。</p>\n  </section>\n</section>\n\n</main>',
    '''    <p class="t" style="max-width:760px">本站的小说式文字只做“基于既有事实的呈现”，不新增历史事件、居民身份、案件或蛊师活动；凡新增空间细节，均在页面内标注。</p>
  </section>

  <section class="block" id="kb-status-block">
    <h2 class="sec">统一数据层 <em>UNIFIED DATA · v2.0</em></h2>
    <div id="kbStatus"></div>
  </section>
</section>

<!-- ===== 视图：实体总索引 ===== -->
<section class="view" id="v-entities" hidden>
  <div class="crumb"><a href="#/">衡垠</a><i>›</i><b>实体总索引</b></div>
  <div class="hero" style="padding-top:34px">
    <div class="kicker">知识库 · ENTITIES</div>
    <h1 class="display" style="font-size:clamp(28px,4vw,44px)">一个编号，一条记录。</h1>
    <p class="lede">这里列出统一知识库的全部实体。每条都有唯一编号、类型、父级、资料状态与完整度；状态为「新增拟定」的不是既定事实，「仅索引」的不代表已有完整档案。</p>
  </div>
  <section class="block">
    <h2 class="sec">按条件筛选 <em>FILTER</em></h2>
    <div class="filters kb-filters">
      <input type="search" id="entQ" placeholder="名称 / 编号 / 关键词" aria-label="实体搜索">
      <select id="entType" aria-label="按类型筛选"></select>
      <select id="entStatus" aria-label="按状态筛选">
        <option value="">全部状态</option><option value="existing">原设定已有</option>
        <option value="proposed">新增拟定</option><option value="uncertain">尚未确认</option><option value="revised">已修订</option>
      </select>
      <select id="entCoverage" aria-label="按完整度筛选">
        <option value="">全部完整度</option><option value="full">完整档案</option>
        <option value="summary">摘录/概要</option><option value="index">仅索引</option><option value="missing">未建档</option>
      </select>
      <span class="cnt" id="entCount"></span>
    </div>
    <div id="entMount"></div>
    <div style="margin-top:18px"><button class="btn" id="entMore" type="button">再显示 60 条</button></div>
  </section>
</section>

<!-- ===== 视图：统一实体档案 ===== -->
<section class="view" id="v-entity" hidden>
  <div class="crumb" id="entityCrumb"></div>
  <div id="entityMount"></div>
</section>

<!-- ===== 视图：资料导出 ===== -->
<section class="view" id="v-export" hidden>
  <div class="crumb"><a href="#/">衡垠</a><i>›</i><b>资料导出</b></div>
  <div class="hero" style="padding-top:34px">
    <div class="kicker">AI PACK · EXPORT</div>
    <h1 class="display" style="font-size:clamp(28px,4vw,44px)">把整个世界，<br>打包交给 AI。</h1>
    <p class="lede">网页和资料包共用同一份数据源。导出得到一个 ZIP，把它上传给支持文件读取的 AI 即可；云端 AI 无法自动访问你电脑上的本地网站。</p>
  </div>
  <div id="exportMount"></div>
</section>

</main>''', "新增三个视图 + 状态页容器")

# ---------------------------------------------------------------- footer
rep('世界资料库 v1.0 ＋ 城市空间工程 R1—R2',
    '世界资料库 v1.0 ＋ 城市空间工程 R1—R2 ＋ 统一知识库 v2.0', "页脚版本")
rep('本站为本地单文件版本，双击即可打开。',
    '本站双击即可打开；「启动网站.bat」可开本地服务；「导出」页可一键生成 AI 资料包。', "页脚说明")

# ---------------------------------------------------------------- 数据层 JS：替换 ENTITIES / POIS
start = s.index('/* ===== 数据：实体索引（内联，file:// 可用） ===== */')
end = s.index('/* ===== 路由 ===== */', start)
NEW_DATA = r'''/* KB-V2-PATCHED */
/* ===== 统一数据层（由 tools/build_kb.py 从 data/ 生成，勿手工改数据） =====
   #kb-data        = data/entities/*.json 的网页投影
   #ai-pack-b64    = 由同一份 data/ 生成的 AI 资料包 ZIP（base64）
   #beasts-json    = 第一版生灵图鉴渲染数据，也由 data/entities/beasts_render.json 重建
   网页不再维护任何硬编码实体列表；搜索、地图 POI、正文引用共用同一套 ID。      */
const KB = JSON.parse(document.getElementById("kb-data").textContent);
const ENTITIES = KB.entities;
const POIS = KB.pois;
const RELS = KB.relationships;
const META = KB.manifest;
const ENT_BY_ID = Object.fromEntries(ENTITIES.map(e => [e.id, e]));
const STATUS_CN = {existing:"原设定已有", proposed:"新增拟定", uncertain:"尚未确认", revised:"已修订"};
const COVERAGE_CN = {full:"完整档案", summary:"摘录/概要", index:"仅索引", missing:"未建档"};
const REL_EDGES_BY_ID = {};
RELS.edges.forEach(r => {
  (REL_EDGES_BY_ID[r.from] = REL_EDGES_BY_ID[r.from] || []).push(r);
  if (r.to !== r.from) (REL_EDGES_BY_ID[r.to] = REL_EDGES_BY_ID[r.to] || []).push(r);
});

'''
s = s[:start] + NEW_DATA + s[end:]
print("  ✓ 替换硬编码实体/POI 为统一数据层")

# ---------------------------------------------------------------- 路由
rep('const VIEWS = ["home","world","linjiang","beicheng","yunqi","garden","gu","beasts","beast","realms","status"];',
    'const VIEWS = ["home","world","linjiang","beicheng","yunqi","garden","gu","beasts","beast","realms","status","entities","entity","export"];',
    "VIEWS 增加三视图")
rep('  if(seg[0]==="beast"&&/^\\d{3}$/.test(seg[1]||"")) return {view:"beast",param:seg[1]};',
    '  if(seg[0]==="beast"&&/^\\d{3}$/.test(seg[1]||"")) return {view:"beast",param:seg[1]};\n  if(seg[0]==="entity"&&seg[1]) return {view:"entity",param:decodeURIComponent(seg.slice(1).join("/"))};',
    "parseHash 支持 entity")
rep('  if(v==="beast") renderBeast(param);\n  if(wantMap) scrollToLifeMap();',
    '''  if(v==="beast") renderBeast(param);
  if(v==="entity") renderEntity(param);
  if(v==="entities") renderEntities();
  if(v==="export") renderExport();
  if(v==="status") renderStatus();
  if(wantMap) scrollToLifeMap();''', "render 分派新视图")
rep('  if(v==="beast")return "beasts";\n  return v;',
    '  if(v==="beast")return "beasts";\n  if(v==="entity"||v==="entities")return "entities";\n  if(v==="export")return "export";\n  return v;', "navKey")

# ---------------------------------------------------------------- 搜索
old_search = s[s.index('/* ===== 搜索 ===== */'):s.index('/* ===== 地图交互 ===== */')]
new_search = r'''/* ===== 搜索（读取统一实体索引） ===== */
function initSearch(){
  const q=document.getElementById("q"),box=document.getElementById("results");
  function show(){
    const s=q.value.trim().toLowerCase();
    if(!s){box.classList.remove("show");box.innerHTML="";return;}
    const hits=ENTITIES.filter(e=>(e.name+" "+e.id+" "+e.type_label+" "+(e.tags||[]).join(" ")+" "+(e.summary||"")).toLowerCase().includes(s)).slice(0,12);
    box.innerHTML = hits.length? hits.map(e=>
      `<button data-id="${escapeHtml(e.id)}" role="option"><div class="r-t">${escapeHtml(e.name)}<span class="r-badge ${e.status}">${STATUS_CN[e.status]||e.status}</span></div><div class="r-m">${escapeHtml(e.id)} · ${escapeHtml(e.type_label)} · ${COVERAGE_CN[e.coverage]||e.coverage}</div></button>`
    ).join("") : `<div class="empty">没有匹配的条目。可试 CITY-101、LOC-101-0312、O-B-012、REALM-012。</div>`;
    box.classList.add("show");
    box.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
      q.value="";box.classList.remove("show");location.hash="#/entity/"+encodeURIComponent(b.dataset.id);
    }));
  }
  q.addEventListener("input",show);
  q.addEventListener("focus",show);
  q.addEventListener("keydown",e=>{
    if(e.key==="Escape"){box.classList.remove("show");q.blur();}
    if(e.key==="Enter"){const f=box.querySelector("button");if(f)f.click();}
  });
  document.addEventListener("click",e=>{if(!document.getElementById("searchBox").contains(e.target))box.classList.remove("show");});
}

'''
s = s.replace(old_search, new_search, 1)
print("  ✓ 搜索改为统一索引")

# ---------------------------------------------------------------- 地图 POI 面板加档案入口
rep('    panel.innerHTML=`<div class="mp-name">${p.name}</div><div class="mp-id">${p.id}${p.idNote?" · "+p.idNote:""} · 空间示意</div><div class="mp-desc">${p.desc}</div>`;',
    '    panel.innerHTML=`<div class="mp-name">${escapeHtml(p.name)}</div><div class="mp-id">${escapeHtml(p.id)}${p.idNote?" · "+escapeHtml(p.idNote):""} · 空间示意</div><div class="mp-desc">${escapeHtml(p.desc)}</div><a class="mp-link" href="#/entity/${encodeURIComponent(p.id)}">查看实体档案 →</a>`;',
    "POI 面板直达实体档案")

# ---------------------------------------------------------------- 新功能 JS（追加到主 script 末尾）
JS = r'''
/* ============================================================
   统一数据层 · 实体档案 / 索引 / 导出 / 状态报告
   数据全部来自 #kb-data（= data/entities/*.json 的投影）
   ============================================================ */
function kbInline(s){
  return escapeHtml(s||"")
    .replace(/\*\*(.+?)\*\*/g,"<b>$1</b>")
    .replace(/`([^`]+)`/g,"<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2">$1</a>');
}
function md2html(md){
  const lines=(md||"").split(/\r?\n/); let out=[], i=0;
  while(i<lines.length){
    const L=lines[i];
    if(/^\s*\|/.test(L)){
      const blk=[]; while(i<lines.length&&/^\s*\|/.test(lines[i])){blk.push(lines[i].trim());i++;}
      const rows=blk.map(r=>r.replace(/^\||\|$/g,"").split("|").map(c=>c.trim()));
      if(!rows.length)continue;
      let t='<table class="data kb-table"><thead><tr>'+rows[0].map(c=>"<th>"+kbInline(c)+"</th>").join("")+"</tr></thead><tbody>";
      const st=(blk[1]&&/^[\s\-:|]+$/.test(blk[1]))?2:1;
      for(let r=st;r<rows.length;r++) t+="<tr>"+rows[r].map(c=>"<td>"+kbInline(c)+"</td>").join("")+"</tr>";
      out.push(t+"</tbody></table>"); continue;
    }
    if(/^\s*$/.test(L)){i++;continue;}
    if(/^---+\s*$/.test(L)){out.push("<hr>");i++;continue;}
    let m=L.match(/^(#{1,6})\s+(.*)$/);
    if(m){const n=Math.min(m[1].length+2,6);out.push("<h"+n+' class="kb-h">'+kbInline(m[2])+"</h"+n+">");i++;continue;}
    if(/^\s*>/.test(L)){
      const arr=[]; while(i<lines.length&&/^\s*>/.test(lines[i])){arr.push(lines[i].replace(/^\s*>\s?/,""));i++;}
      out.push('<p class="note">'+kbInline(arr.join(" "))+"</p>");continue;
    }
    if(/^\s*[-*]\s/.test(L)){
      const arr=[]; while(i<lines.length&&/^\s*[-*]\s/.test(lines[i])){arr.push(lines[i].replace(/^\s*[-*]\s/,""));i++;}
      out.push('<ul class="kb-ul">'+arr.map(x=>"<li>"+kbInline(x)+"</li>").join("")+"</ul>");continue;
    }
    const arr=[];
    while(i<lines.length&&!/^\s*$/.test(lines[i])&&!/^\s*\|/.test(lines[i])&&!/^#{1,6}\s/.test(lines[i])&&!/^\s*>/.test(lines[i])&&!/^\s*[-*]\s/.test(lines[i])&&!/^---+\s*$/.test(lines[i])){arr.push(lines[i]);i++;}
    if(arr.length) out.push('<p class="kb-p">'+kbInline(arr.join(" "))+"</p>");
  }
  return out.join("\n");
}
function kbTag(cls,txt){return '<span class="kb-tag '+cls+'">'+escapeHtml(txt)+"</span>";}
function kbEntityLink(id,label){
  const e=ENT_BY_ID[id];
  return '<a href="#/entity/'+encodeURIComponent(id)+'">'+escapeHtml(label||(e?e.name:id))+"</a>";
}
function kbChain(e){
  const chain=[]; let p=e.parent_id, guard=0;
  while(p&&ENT_BY_ID[p]&&guard++<12){chain.unshift(ENT_BY_ID[p]);p=ENT_BY_ID[p].parent_id;}
  return chain;
}
function kbSources(e){
  return (e.source||[]).map(x=>"<div>"+escapeHtml(x.doc||"")+(x.section?" · "+escapeHtml(x.section):"")+(x.version?" · "+escapeHtml(x.version):"")+(x.note?"<br><span style=\"font-size:11.5px;color:var(--ink-faint)\">"+escapeHtml(x.note)+"</span>":"")+"</div>").join("");
}
let entShown=60;
function renderEntities(){
  const host=document.getElementById("entMount"); if(!host)return;
  const sel=document.getElementById("entType");
  if(sel&&!sel.dataset.ready){
    const types=Array.from(new Set(ENTITIES.map(e=>e.type_label))).sort();
    sel.innerHTML='<option value="">全部类型</option>'+types.map(t=>'<option value="'+escapeHtml(t)+'">'+escapeHtml(t)+"</option>").join("");
    sel.dataset.ready="1";
    ["entQ","entType","entStatus","entCoverage"].forEach(id=>{
      const el=document.getElementById(id);
      if(el)el.addEventListener(el.tagName==="INPUT"?"input":"change",()=>{entShown=60;renderEntities();});
    });
    const more=document.getElementById("entMore");
    if(more)more.addEventListener("click",()=>{entShown+=60;renderEntities();});
  }
  const q=(document.getElementById("entQ")||{}).value||"";
  const ft=(document.getElementById("entType")||{}).value||"";
  const fs=(document.getElementById("entStatus")||{}).value||"";
  const fc=(document.getElementById("entCoverage")||{}).value||"";
  const s=q.trim().toLowerCase();
  const hits=ENTITIES.filter(e=>
    (!ft||e.type_label===ft)&&(!fs||e.status===fs)&&(!fc||e.coverage===fc)&&
    (!s||(e.name+" "+e.id+" "+e.type_label+" "+(e.tags||[]).join(" ")+" "+(e.summary||"")).toLowerCase().includes(s)));
  const cnt=document.getElementById("entCount");
  if(cnt)cnt.textContent="命中 "+hits.length+" 条 / 全库 "+ENTITIES.length+" 条";
  const rows=hits.slice(0,entShown).map(e=>
    "<tr><td><a href=\"#/entity/"+encodeURIComponent(e.id)+'">'+escapeHtml(e.id)+"</a></td>"+
    "<td><a href=\"#/entity/"+encodeURIComponent(e.id)+'">'+escapeHtml(e.name)+"</a></td>"+
    "<td>"+escapeHtml(e.type_label)+"</td>"+
    "<td>"+(e.parent_id?kbEntityLink(e.parent_id,ENT_BY_ID[e.parent_id]?ENT_BY_ID[e.parent_id].name:e.parent_id):"—")+"</td>"+
    "<td>"+kbTag("s-"+e.status,STATUS_CN[e.status]||e.status)+"</td>"+
    "<td>"+kbTag("c-"+e.coverage,COVERAGE_CN[e.coverage]||e.coverage)+"</td></tr>").join("");
  host.innerHTML=hits.length? '<table class="data kb-table"><thead><tr><th>编号</th><th>名称</th><th>类型</th><th>父级</th><th>资料状态</th><th>完整度</th></tr></thead><tbody>'+rows+"</tbody></table>" : '<div class="kb-empty">没有符合条件的实体。</div>';
  const more=document.getElementById("entMore");
  if(more)more.hidden=hits.length<=entShown;
}
function renderEntity(id){
  const mount=document.getElementById("entityMount"); if(!mount)return;
  const crumb=document.getElementById("entityCrumb");
  const e=ENT_BY_ID[id];
  if(!e){
    if(crumb)crumb.innerHTML='<a href="#/">衡垠</a><i>›</i><b>未找到</b>';
    mount.innerHTML='<div class="hero" style="padding-top:34px"><h1 class="display" style="font-size:30px">没有这个编号</h1><p class="lede">'+escapeHtml(id||"")+' 不在统一索引里。可以到<a class="ob-link" href="#/entities">实体总索引</a>查找，或检查编号是否写错。</p></div>';
    return;
  }
  const chain=kbChain(e);
  if(crumb)crumb.innerHTML='<a href="#/">衡垠</a>'+(chain.length?"<i>›</i>":"")+chain.map(x=>'<a href="#/entity/'+encodeURIComponent(x.id)+'">'+escapeHtml(x.name)+"</a>").join("<i>›</i>")+"<i>›</i><b>"+escapeHtml(e.name)+"</b>";
  const attrs=Object.entries(e.attributes||{}).filter(([k,v])=>v!==""&&v!==null&&v!==undefined);
  const attrHtml=attrs.length? '<h3 class="sub">类型专属字段</h3><table class="data kb-table"><tbody>'+attrs.map(([k,v])=>"<tr><th style=\"width:32%\">"+escapeHtml(k)+"</th><td>"+escapeHtml(typeof v==="object"?JSON.stringify(v, null, 0):String(v))+"</td></tr>").join("")+"</tbody></table>":"";
  const edges=(REL_EDGES_BY_ID[e.id]||[]).slice(0,40);
  const relHtml=edges.length? edges.map(r=>{
    const other=r.from===e.id?r.to:r.from;
    const dir=r.from===e.id?"→":"←";
    const lab=(RELS.kinds&&RELS.kinds[r.type])||r.type;
    return '<a href="#/entity/'+encodeURIComponent(other)+'"><span>'+escapeHtml(r.type)+" "+dir+"</span>"+escapeHtml(lab)+" · "+escapeHtml(ENT_BY_ID[other]?ENT_BY_ID[other].name:other)+(r.kind==="hierarchy"?" · 父级":"")+"</a>";
  }).join("") : '<span class="kb-small">该实体暂无登记关联。</span>';
  const gz=e.content_file?e.content_file.split("/").pop():null;
  const gzHtml=(gz&&KB.gazetteers&&KB.gazetteers[gz])? '<h3 class="sub">正文（来自地方志，文字未改写）</h3><div class="kb-doc">'+md2html(KB.gazetteers[gz])+"</div>":"";
  const routeBtn=e.route? '<a class="btn" href="'+escapeHtml(e.route)+'">打开网站专题页</a>':"";
  const noteHtml=e.note? '<p class="note">'+escapeHtml(e.note)+"</p>":"";
  mount.innerHTML=
    '<div class="hero" style="padding-top:34px">'+
      '<div class="kicker">实体档案 · '+escapeHtml(e.type_label)+" · "+escapeHtml(e.category)+"</div>"+
      '<h1 class="display" style="font-size:clamp(28px,4vw,46px)">'+escapeHtml(e.name)+"</h1>"+
      '<div style="margin:10px 0 4px">'+kbTag("s-"+e.status,STATUS_CN[e.status]||e.status)+kbTag("c-"+e.coverage,COVERAGE_CN[e.coverage]||e.coverage)+(e.tags||[]).slice(0,8).map(t=>kbTag("",t)).join("")+"</div>"+
      '<p class="lede" style="margin-top:14px">'+escapeHtml(e.summary||"")+"</p>"+
      '<div class="kb-btns">'+routeBtn+
        '<button class="btn" type="button" data-ex="md" data-id="'+escapeHtml(e.id)+'">导出本实体 · Markdown</button>'+
        '<button class="btn" type="button" data-ex="json" data-id="'+escapeHtml(e.id)+'">导出本实体 · JSON</button>'+
      "</div></div>"+
    '<section class="block"><div class="kb-meta">'+
      '<div class="kb-row"><div class="kb-k">唯一编号</div><div class="kb-v"><b>'+escapeHtml(e.id)+"</b></div></div>"+
      '<div class="kb-row"><div class="kb-k">类型 / 大类</div><div class="kb-v">'+escapeHtml(e.type_label)+" / "+escapeHtml(e.type)+" · "+escapeHtml(e.category)+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">父级（parent_id）</div><div class="kb-v">'+(e.parent_id?kbEntityLink(e.parent_id,e.parent_name||e.parent_id)+" <span style=\"font-size:11.5px;color:var(--ink-faint)\">"+escapeHtml(e.parent_id)+"</span>":"无（不属于地理层级）")+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">资料状态</div><div class="kb-v">'+(STATUS_CN[e.status]||e.status)+(e.status==="proposed"?" —— 新增拟定，不是既定事实":"")+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">完整度</div><div class="kb-v">'+(COVERAGE_CN[e.coverage]||e.coverage)+(e.coverage==="index"?" —— 只有编号与名称，没有正文":"")+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">正文文件</div><div class="kb-v">'+(e.content_file?escapeHtml(e.content_file):"无（尚未导入完整正文）")+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">来源</div><div class="kb-v">'+kbSources(e)+"</div></div>"+
      '<div class="kb-row"><div class="kb-k">版本</div><div class="kb-v">'+escapeHtml(String(e.version||""))+"</div></div>"+
    "</div>"+noteHtml+attrHtml+
    '<h3 class="sub">关联（'+edges.length+' 条，父级与普通关联分列）</h3><div class="kb-rel">'+relHtml+"</div>"+
    "</section>"+ (gzHtml?'<section class="block">'+gzHtml+"</section>":"");
  mount.querySelectorAll("[data-ex]").forEach(b=>b.addEventListener("click",()=>exportEntity(b.dataset.id,b.dataset.ex)));
}
function kbEntityMD(e){
  const L=["# "+e.id+" "+e.name,"",
    "> 本文件由《衡垠世界图集》统一数据层导出 ｜ 生成时间 "+new Date().toLocaleString("zh-CN"),"",
    "- 类型："+e.type_label+"（"+e.type+"）｜ 大类："+e.category,
    "- 资料状态："+(STATUS_CN[e.status]||e.status)+"（"+e.status+"）",
    "- 完整度："+(COVERAGE_CN[e.coverage]||e.coverage)+"（"+e.coverage+"）",
    "- 父级："+(e.parent_id?e.parent_id+" "+(ENT_BY_ID[e.parent_id]?ENT_BY_ID[e.parent_id].name:""):"无"),
    "- 正文文件："+(e.content_file||"无"),
    "- 网站专题页："+(e.route||"无"),"",
    "## 概要","",e.summary||"（无）","",
    "## 类型专属字段",""];
  for(const [k,v] of Object.entries(e.attributes||{})) L.push("- **"+k+"**："+(typeof v==="object"?JSON.stringify(v):String(v)));
  if(!Object.keys(e.attributes||{}).length)L.push("- （无）");
  L.push("","## 关联","");
  const edges=REL_EDGES_BY_ID[e.id]||[];
  if(!edges.length)L.push("- （无）");
  for(const r of edges){
    const other=r.from===e.id?r.to:r.from;
    L.push("- "+(r.from===e.id?"→":"←")+" `"+(r.type)+"`（"+((RELS.kinds&&RELS.kinds[r.type])||r.type)+"） "+other+" "+(ENT_BY_ID[other]?ENT_BY_ID[other].name:"")+(r.note?"；"+r.note:""));
  }
  L.push("","## 来源","");
  for(const x of (e.source||[])) L.push("- "+x.doc+(x.section?" · "+x.section:"")+(x.version?" · "+x.version:"")+(x.note?"：" +x.note:""));
  if(e.note)L.push("","## 备注","",e.note);
  L.push("","---","","状态与完整度口径见 AI_START_HERE.md；本文件不得脱离资料包单独当作完整设定使用。","");
  return L.join("\n");
}
function downloadBlob(blob,name){
  const url=URL.createObjectURL(blob),a=document.createElement("a");
  a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),4000);
}
function exportEntity(id,fmt){
  const e=ENT_BY_ID[id]; if(!e)return;
  const safe=id.replace(/[^\w\-]/g,"_");
  if(fmt==="json"){
    downloadBlob(new Blob([JSON.stringify({entity:e,relations:REL_EDGES_BY_ID[id]||[],schema:"hengyin/entity-export/1.0",generated_at:new Date().toISOString()},null,2)],{type:"application/json;charset=utf-8"}),safe+".json");
  }else{
    downloadBlob(new Blob([kbEntityMD(e)],{type:"text/markdown;charset=utf-8"}),safe+".md");
  }
}
function downloadPack(){
  const el=document.getElementById("ai-pack-b64");
  const b64=(el?el.textContent:"").trim();
  const st=document.getElementById("packState");
  if(!b64){if(st)st.textContent="资料包未生成，请运行「重新生成资料.bat」。";return;}
  try{
    const bin=atob(b64),arr=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
    const d=new Date(),ds=""+d.getFullYear()+String(d.getMonth()+1).padStart(2,"0")+String(d.getDate()).padStart(2,"0");
    downloadBlob(new Blob([arr],{type:"application/zip"}),"衡垠AI资料包_"+ds+".zip");
    if(st)st.textContent="已导出（"+(arr.length/1024).toFixed(0)+" KB）。把 ZIP 上传给支持文件读取的 AI，并让它先读 AI_START_HERE.md。";
  }catch(err){if(st)st.textContent="导出失败："+err.message;}
}
function renderExport(){
  const host=document.getElementById("exportMount"); if(!host)return;
  const c=META.counts||{};
  const files=(META.files||[]).filter(f=>/^(AI_START_HERE|AI_INTEGRATION_GUIDE|DATA_SCHEMA|README|world-index|relationships|manifest)/.test(f.path)||/^(entities|rules|gazetteers|sources|reports)\//.test(f.path));
  host.innerHTML=
  '<section class="block"><h2 class="sec">三件事，不是一件事 <em>THREE CAPABILITIES</em></h2>'+
    '<div class="kb-grid">'+
      '<div class="kb-card"><h3>① 本地网站浏览</h3><p>人用浏览器打开本项目；双击 HTML 即可，或运行「启动网站.bat」开本地服务。已实现。</p></div>'+
      '<div class="kb-card"><h3>② 资料包导出给 AI</h3><p>点下方按钮生成 ZIP，由你手动上传给支持文件读取的 AI。已实现。</p></div>'+
      '<div class="kb-card" style="opacity:.72"><h3>③ AI 实时查询接口</h3><p>未来可通过 HTTP 按编号、关键词、地域、关系查询。本阶段<b>未实现</b>，只做了兼容设计。</p></div>'+
    '</div>'+
    '<div class="kb-warn"><b>请注意：</b>云端 AI（ChatGPT、DeepSeek 等）<b>无法自动访问</b>你电脑上的本地网站或 localhost。只有你上传了 ZIP，AI 才读得到这些资料。</div>'+
  '</section>'+
  '<section class="block"><h2 class="sec">一键导出 <em>DOWNLOAD</em></h2>'+
    '<div class="kb-card"><p>资料包内容全部来自同一份 <code>data/</code>：实体总索引、分类实体记录、关联关系、地方志、规则、来源、冲突与缺失报告、AI 阅读入口。</p>'+
      '<button class="kb-big" type="button" id="btnPack">↓ 一键导出 AI 资料包（ZIP）</button>'+
      '<div class="kb-small" id="packState">也可直接使用项目目录里的「衡垠AI资料包.zip」；两者内容一致。</div>'+
    '</div>'+
    '<p class="note">单个实体资料：在<a class="ob-link" href="#/entities">实体总索引</a>或任意<a class="ob-link" href="#/entity/CITY-101">实体档案页</a>点「导出本实体」，可导出 Markdown 或 JSON。</p>'+
  '</section>'+
  '<section class="block"><h2 class="sec">资料包内容与数据完整度 <em>PACK CONTENTS</em></h2>'+
    '<div class="kb-grid">'+
      '<div class="kb-stat"><b>'+(c.entities||ENTITIES.length)+'</b><span>实体总数</span></div>'+
      '<div class="kb-stat"><b>'+(c.relations||RELS.count)+'</b><span>关联关系</span></div>'+
      '<div class="kb-stat"><b>'+(c.full_records||0)+'</b><span>有完整正文</span></div>'+
      '<div class="kb-stat"><b>'+(c.pack_files||files.length+2)+'</b><span>资料包文件</span></div>'+
      '<div class="kb-stat"><b>'+(c.conflicts||0)+'</b><span>已登记冲突</span></div>'+
      '<div class="kb-stat"><b>'+(c.invalid_routes||0)+'</b><span>无效路由</span></div>'+
    '</div>'+
    '<p class="t" style="text-indent:0;font-size:13px">按完整度：完整档案 '+(META.counts&&META.counts.by_coverage?META.counts.by_coverage.full:0)+' 条，摘录/概要 '+(META.counts&&META.counts.by_coverage?META.counts.by_coverage.summary:0)+' 条，仅索引 '+(META.counts&&META.counts.by_coverage?META.counts.by_coverage.index:0)+' 条。<b>「仅索引」不是完整档案</b>，C-K 447 条、C-B 37 条、R-B 40 条都属此类。</p>'+
    '<details class="kb-details" open><summary>资料包文件清单（'+files.length+' 项）</summary><div class="kb-doc"><ul class="kb-list">'+files.map(f=>"<li>"+escapeHtml(f.path)+"</li>").join("")+"</ul></div></details>"+
    '<details class="kb-details"><summary>编号冲突检查报告</summary><div class="kb-doc">'+md2html(KB.reports.conflicts)+"</div></details>"+
    '<details class="kb-details"><summary>资料缺失与完整度报告</summary><div class="kb-doc">'+md2html(KB.reports.completeness)+"</div></details>"+
    '<details class="kb-details"><summary>待确认清单</summary><div class="kb-doc">'+md2html(KB.reports.pending)+"</div></details>"+
  '</section>'+
  '<section class="block"><h2 class="sec">交给 AI 之后 <em>FOR AI</em></h2>'+
    '<div class="kb-card"><p>让 AI 先完整读 <code>AI_START_HERE.md</code>，再按 <code>world-index.json</code> 查编号、按 <code>relationships.json</code> 查关联。资料包内已写明：<code>status=proposed</code> 不是既定事实，<code>coverage=index</code> 不是完整档案，R-B 不是本世界物种，冲突须并列保留。</p>'+
    '<p>未来接口设计见 <code>AI_INTEGRATION_GUIDE.md</code>；字段定义见 <code>DATA_SCHEMA.md</code>。</p></div>'+
  '</section>';
  const b=document.getElementById("btnPack"); if(b)b.addEventListener("click",downloadPack);
}
function renderStatus(){
  const el=document.getElementById("statEntCount"); if(el)el.textContent=ENTITIES.length;
  const host=document.getElementById("kbStatus"); if(!host)return;
  const c=META.counts||{};
  const cv=(c.by_coverage||{}),sv=(c.by_status||{});
  host.innerHTML=
    '<p class="t" style="text-indent:0;font-size:14px">本阶段把第一版网页与原始资料抽取到 <code>data/</code> 这一份正式数据源。网页里的搜索、地图 POI、正文引用与导出的 ZIP 全部由它生成，不再各自维护一份实体列表。</p>'+
    '<div class="kb-grid">'+
      '<div class="kb-stat"><b>'+(c.entities||ENTITIES.length)+'</b><span>统一实体索引</span></div>'+
      '<div class="kb-stat"><b>'+(c.relations||RELS.count)+'</b><span>带类型关联</span></div>'+
      '<div class="kb-stat"><b>'+(cv.full||0)+'</b><span>完整档案</span></div>'+
      '<div class="kb-stat"><b>'+(cv.summary||0)+'</b><span>摘录/概要</span></div>'+
      '<div class="kb-stat"><b>'+(cv.index||0)+'</b><span>仅索引</span></div>'+
      '<div class="kb-stat"><b>'+(sv.proposed||0)+'</b><span>新增拟定（非事实）</span></div>'+
    '</div>'+
    '<p class="note">校验：重复编号 '+(c.duplicate_ids||0)+' 处，无效路由 '+(c.invalid_routes||0)+' 处，悬空关联 '+(META.checks&&META.checks.dangling_relations||0)+' 处。完整报告在「导出」页与 <code>data/reports/</code>。</p>'+
    '<div class="kb-btns"><a class="btn primary" href="#/entities">浏览实体总索引</a><a class="btn" href="#/export">导出 AI 资料包</a></div>'+
    '<details class="kb-details"><summary>本阶段新增的冲突登记（C-05—C-08）与全部冲突</summary><div class="kb-doc">'+md2html(KB.reports.conflicts)+"</div></details>"+
    '<details class="kb-details"><summary>资料缺失与完整度报告</summary><div class="kb-doc">'+md2html(KB.reports.completeness)+"</div></details>"+
    '<details class="kb-details"><summary>待用户确认清单</summary><div class="kb-doc">'+md2html(KB.reports.pending)+"</div></details>";
}
'''
idx = s.rindex("</script>")
s = s[:idx] + JS + "\n" + s[idx:]
print("  ✓ 追加统一数据层 JS")

P.write_text(s, encoding="utf-8", newline="\n")
print("补丁完成：", P)

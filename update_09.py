import io,os,sys

P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overly','test-8.html')
if not os.path.exists(P):
    print('MISSING: '+P);sys.exit(1)
s=io.open(P,encoding='utf-8').read()
orig=s
applied,skipped=[],[]

def rep(a,b,tag):
    global s
    if a in s: s=s.replace(a,b,1);applied.append(tag)
    else: skipped.append(tag)

# ── 0. backfills (in case audit_08 was missed) ──
if '\u6d3b\u8dc3' in s:
    s='\n'.join(l for l in s.split('\n') if '\u6d3b\u8dc3' not in l);applied.append('strip-cjk')
else: skipped.append('strip-cjk')
if "toggle('on',this.w.v>3)" not in s:
    rep("this.el.classList.toggle('zero',this.w.v<3)}",
        "this.el.classList.toggle('zero',this.w.v<3);this.el.classList.toggle('on',this.w.v>3)}",
        'fix-pod-on-backfill')
else: skipped.append('fix-pod-on-backfill')

# ── 1. island dock height (pods center inside 56px strap) ──
rep('--cluster-top:24px;','--cluster-top:5px;','cluster-top')

# ── 2. THE BUG: demo no longer kills itself ──
rep('push(raw){const a=normalize(raw);if(!a)return;wentReal();',
    'push(raw){const a=normalize(raw);if(!a)return;','fix-wentreal-stage')
rep('open(d){d=d||{};wentReal();','open(d){d=d||{};','fix-wentreal-trade')
rep('apply(st){\n  if(st.goal)','apply(st){wentReal();\n  if(st.goal)','fix-wentreal-state')

# ── 3. pods display-only in viewer · debug-gated clicks ──
POD_OLD="""podT.el.addEventListener('click',()=>{
 if(Stage.a)Stage.dismiss();
 else if(Trade.cur&&Trade.cur.status==='running')Trade.collapse(true)});
podP.el.addEventListener('click',()=>{
 if(Trade.cur&&Trade.cur.status==='running')Trade.collapse()});"""
POD_NEW="""const podTap=()=>document.body.classList.contains('debug');
podT.el.addEventListener('click',()=>{if(!podTap())return;
 if(Stage.a)Stage.dismiss();
 else if(Trade.cur&&Trade.cur.status==='running')Trade.collapse(true)});
podP.el.addEventListener('click',()=>{if(!podTap())return;
 if(Trade.cur&&Trade.cur.status==='running')Trade.collapse()});"""
rep(POD_OLD,POD_NEW,'pod-clicks-debug')

rep("const IS_CONTROL=params.get('control')==='1';",
    "const IS_CONTROL=params.get('control')==='1';\nconst IS_DEBUG=params.get('debug')==='1';",'isdebug-const')
rep('podP.el.classList.add('+"'on');",
    "if(IS_DEBUG)document.body.classList.add('debug');\npodP.el.classList.add('on');",'boot-debug')

# ── 4. exact brand mascot + wordmark asset ──
MASCOT_OLD="""const MASCOT=()=>'<span class="mascot"><svg class="smile" viewBox="0 0 100 100" aria-hidden="true"><circle class="face" cx="50" cy="50" r="45"/><circle class="eye" cx="35" cy="40" r="6"/><circle class="eye" cx="65" cy="40" r="6"/><path class="mouth" d="M25 55 A25 25 0 0 0 75 55"/></svg></span>';"""
MASCOT_NEW="""const MASCOT=()=>'<span class="mascot"><svg class="smile" viewBox="0 0 100 100" aria-hidden="true"><circle class="face" cx="50" cy="50" r="48"/><circle class="eye" cx="31" cy="35" r="5.5"/><circle class="eye" cx="69" cy="35" r="5.5"/><path class="mouth" d="M20 48 A30 30 0 0 0 80 48"/></svg></span>';
const WORDMARK=(h)=>'<svg viewBox="0 0 146.5 87" style="height:'+h+'px;width:auto" aria-hidden="true">'
+'<path style="fill:var(--c-fg)" d="m39 48c0.5 1.7 1.2 2.9 3.3 2.9 1.7 0.1 3-0.7 3-1.9s-0.5-1.9-2.3-2.1l-3-0.4c-4.6-0.6-7.5-2.2-7.5-6.3s3.6-6.1 9.6-6.1c4.5-0.1 7.7 1 10.1 4.9l-7.6 1c-0.3-1.3-1-2-2.4-2s-1.9 1-1.9 1.9 0.6 1.4 1.7 1.5l3.5 0.4c4.5 0.5 7.8 2.4 7.8 6.2 0 4-4.1 6.6-11.1 6.6-5.2 0-9.5-1.1-11-5.6l7.8-1z"/>'
+'<path style="fill:var(--c-fg)" d="m57.2 34.1h7.3v2.9h0.1c1.3-1.8 3.8-2.9 6.9-2.9 2.5 0 4.4 0.9 5.9 3 1.7-1.6 3.6-3 7.6-3 3.4 0 7.3 1.4 7.3 6.9v13.6h-7.9v-12.1c0-1.3-1.2-2.6-2.8-2.6s-3.2 1.7-3.2 3.2v11.5h-7.8v-12.3c0-1.1-1.2-2.4-2.5-2.4-1.5 0-3 1.3-3 3.2v11.4h-7.9v-20.4z"/>'
+'<path style="fill:var(--c-fg)" d="m97.2 34.1h7.9v20.5h-7.9v-20.5z"/>'
+'<path style="fill:var(--c-fg)" d="m97.2 26.1h7.9v5.2h-7.9v-5.2z"/>'
+'<polygon style="fill:var(--c-fg)" points="110.2 26.1 117.9 26.1 117.9 54.6 110.2 54.6"/>'
+'<path style="fill:var(--c-fg)" d="m131.4 39.2c2.4-0.8 5.6-0.2 6.4 2.7h-7.8c0.2-0.7 0.4-2 1.4-2.7m6.5 8.7c-0.9 1.5-2.3 2-4 2-2.5 0-3.9-1.5-3.9-4h15.5c0.1-6.9-2.7-11.7-11.4-11.7-8.2 0-12.1 4-12.1 10.4 0 5.6 3.4 10 12.2 10 4.7 0 8.8-1.6 11.2-5.6l-7.5-1.1z"/>'
+'<path style="fill:var(--c-accent)" d="m29.7 45.1c0 7.5-5.9 14.3-14.8 14.3-7.6 0-14.3-5.5-14.3-14.3 0-6.7 5.3-14.5 14.6-14.5 6.7-0.1 14.5 5.3 14.5 14.5z"/>'
+'<path style="fill:var(--c-on-accent)" d="m23.9 45.2c0 4.3-3.3 8.4-8.5 8.5-4.8 0-8.7-2.8-9.2-8.8l-1.6 0.1c0.3 4.6 3.1 10.5 10.8 10.5 6.3 0 10.1-5.1 10.1-10.6l-1.6 0.3z"/>'
+'<circle style="fill:var(--c-on-accent)" cx="8.7" cy="39.9" r="1.6"/>'
+'<path style="fill:var(--c-on-accent)" d="m23.2 39.9c0 0.8-0.7 1.6-1.7 1.6-0.9 0-1.8-0.6-1.8-1.6 0-0.8 0.8-1.7 1.8-1.7 0.9 0.1 1.7 0.8 1.7 1.7z"/></svg>';"""
rep(MASCOT_OLD,MASCOT_NEW,'brand-mascot-wordmark')

# ── 5. footer logo bug uses the wordmark ──
if "c.innerHTML=MASCOT()+'<span>SMILE</span>'" in s:
    rep("c.innerHTML=MASCOT()+'<span>SMILE</span>';","c.innerHTML=WORDMARK(38);",'capleft-wordmark')
elif 'Cap.refresh();\nPx.sim();Px.binance();' in s:
    rep('Cap.refresh();\nPx.sim();Px.binance();',
        "Cap.refresh();\n(function(){var c=document.getElementById('capLeft');if(c)c.innerHTML=WORDMARK(38);})();\nPx.sim();Px.binance();",'capleft-wordmark')
else: skipped.append('capleft-wordmark (anchor missing)')

# ── 6. chrome defaults + visibility + layout margins ──
rep('stage:{mode:\'widgets\',edge:\'bottom\',guests:5,autospeak:1,mic:0,host:\'You · Host\'},',
    'stage:{mode:\'widgets\',edge:\'bottom\',guests:5,autospeak:1,mic:0,host:\'You · Host\'},\nchrome:{title:\'SMILE MARKETS\',next:\'MARKET WAKE UP · 08:00\'},',
    'def-chrome')
rep('vis:{pip:1,sess:1,trades:1,ticker:1,island:1,piptag:1,market:1,glow:1},',
    'vis:{pip:1,sess:1,trades:1,ticker:1,island:1,piptag:1,market:1,glow:1,header:1},',
    'def-vis-header')
rep("b.toggle('hide-market',!v.market);b.toggle('hide-glow',!v.glow)}",
    "b.toggle('hide-market',!v.market);b.toggle('hide-glow',!v.glow);b.toggle('hide-header',!v.header)}",
    'applyvis-header')
rep('if(APP.Layout)APP.Layout.apply()}',
    'if(APP.Layout)APP.Layout.apply();\n if(APP.Chrome)APP.Chrome.render()}','applymeta-chrome')
rep('mx:44,mt:24,mb:96,','mx:44,mt:76,mb:112,','layout-margins')
rep("{k:'ticker',name:'Ticker',note:'marquee + goal cap',pos:0},",
    "{k:'header',name:'Header Strap',note:'live · clocks · up-next',pos:0},\n {k:'ticker',name:'Footer Strap',note:'wordmark · crawl · goal',pos:0},",
    'layers-chrome')

# ── 7. header strap markup ──
TOPSTRAP="""  <div id="topStrap">
    <div class="ts-mod">
      <span class="ts-live"><i></i>LIVE</span>
      <span class="ts-sep"></span>
      <span class="ts-title" id="tsTitle">SMILE MARKETS</span>
    </div>
    <div class="ts-mod">
      <span class="ts-date num" id="tsDate">— — —</span>
      <span class="ts-sep"></span>
      <span class="ts-tz num" id="tsNbo">NBO --:--</span>
      <span class="ts-tz num" id="tsNyc">NYC --:--</span>
      <span class="ts-next" id="tsNext">NEXT · <b>—</b></span>
    </div>
  </div>
"""
rep('  <div id="islandZone">',TOPSTRAP+'  <div id="islandZone">','html-topstrap')

# ── 8. chrome styles ──
CSS09="""/* ── update_09 · broadcast chrome ── */
#topStrap{position:absolute;left:0;right:0;top:0;height:56px;z-index:55;display:flex;align-items:center;justify-content:space-between;padding:0 18px;pointer-events:none;background:linear-gradient(180deg,rgba(5,5,7,.52),rgba(5,5,7,.16) 60%,transparent);transition:opacity .4s ease,transform .5s var(--ease)}
body.hide-header #topStrap,body.ticker-top #topStrap{opacity:0;transform:translateY(-100%)}
body.hide-header #islandZone{top:22px}
.ts-mod{display:flex;align-items:center;gap:11px;height:40px;padding:0 16px;border-radius:999px;background:rgba(10,10,12,.72);border:1px solid rgba(255,255,255,.09);backdrop-filter:blur(14px) saturate(150%);box-shadow:0 10px 26px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.09);white-space:nowrap}
.ts-live{display:flex;align-items:center;gap:7px;font-family:var(--f-d);font-weight:700;font-size:10px;letter-spacing:.18em;color:#FF375F}
.ts-live i{width:7px;height:7px;border-radius:50%;background:currentColor;animation:softpulse 1.6s infinite}
.ts-sep{width:1px;height:16px;background:rgba(255,255,255,.14);flex:none}
.ts-title{font-family:var(--f-d);font-weight:700;font-size:13px;letter-spacing:.22em;color:var(--c-fg);text-transform:uppercase}
.ts-date,.ts-tz{font-family:var(--f-m);font-size:10.5px;letter-spacing:.12em;color:var(--c-muted)}
.ts-tz b{color:var(--c-fg);font-weight:600}
.ts-next{font-family:var(--f-m);font-size:9.5px;letter-spacing:.14em;color:var(--c-muted);background:rgba(var(--c-accent-rgb),.08);box-shadow:inset 0 0 0 1px rgba(var(--c-accent-rgb),.28);border-radius:999px;padding:7px 12px}
.ts-next b{color:var(--c-accent);font-weight:700}
#ticker{left:0;right:0;bottom:0;height:64px;border-radius:22px 22px 0 0}
body.ticker-top #ticker{transform:translateY(calc(-100vh + 64px))}
body.hide-ticker:not(.ticker-top) #ticker{transform:translateY(120%)}
.cap.left{background:rgba(9,9,11,.9);color:var(--c-fg);border-radius:22px 0 0 0;border-right:1px solid rgba(255,255,255,.09);padding:0 24px 0 20px}
.cap.right{border-radius:0}
body.island-bottom #islandZone{bottom:86px}
.pod{cursor:default}
body.debug .pod{cursor:pointer}
"""
rep('</style>',CSS09+'</style>','css-chrome')

# ── 9. control section ──
CHROME_SEC="""  <section>
    <h2>Broadcast Chrome <span class="hint">header &amp; footer straps</span></h2>
    <div class="ctrl-row"><label>Show Title</label><input type="text" id="ctrl-title" placeholder="SMILE MARKETS" style="min-width:190px"></div>
    <div class="ctrl-row"><label>Up Next</label><input type="text" id="ctrl-next" placeholder="MARKET WAKE UP · 08:00" style="min-width:190px"></div>
    <div class="ctrl-row"><label>Header Strap</label><div class="seg" data-seg="headerVis"><button data-val="1">On</button><button data-val="0">Off</button></div></div>
    <p style="font-size:11px;color:#71717a;line-height:1.6;margin-top:4px">Header: LIVE · title · NBO/NYC clocks · up-next. Footer: wordmark bug · crawl · goal cap. The island docks center-header, iPhone status-bar style.</p>
  </section>

"""
rep('  <section>\n    <h2>Camera</h2>',CHROME_SEC+'  <section>\n    <h2>Camera</h2>','ctrl-chrome-section')

# ── 10. chrome runtime ──
CHROME_JS="""/* ═════════ BROADCAST CHROME — header strap ═════════ */
Tw.chrome=Tw.chrome||{title:'SMILE MARKETS',next:'MARKET WAKE UP · 08:00'};
const Chrome={
 fmt(tz){try{return new Intl.DateTimeFormat('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:tz}).format(new Date())}catch(e){return'--:--'}},
 render(){const q=function(id){return document.getElementById(id)};if(!q('tsTitle'))return;
  const d=new Date();
  const day=d.toLocaleDateString('en-US',{weekday:'short'}).toUpperCase();
  const dm=d.toLocaleDateString('en-US',{day:'2-digit',month:'short'}).toUpperCase();
  if(q('tsDate'))q('tsDate').textContent=day+' '+dm;
  if(q('tsNbo'))q('tsNbo').innerHTML='<b>NBO</b> '+this.fmt('Africa/Nairobi');
  if(q('tsNyc'))q('tsNyc').innerHTML='<b>NYC</b> '+this.fmt('America/New_York');
  if(q('tsTitle'))q('tsTitle').textContent=Tw.chrome.title||'';
  if(q('tsNext'))q('tsNext').innerHTML='NEXT · <b>'+esc(Tw.chrome.next||'')+'</b>'}};
Chrome.render();
setInterval(function(){if(!IS_CONTROL)Chrome.render()},15000);
APP.Chrome=Chrome;
(function(){var a=document.getElementById('ctrl-title'),b=document.getElementById('ctrl-next');
 if(a)a.value=Tw.chrome.title||'';if(b)b.value=Tw.chrome.next||''})();
 $('#ctrl-title').oninput=function(e){Tw.chrome.title=e.target.value;saveTw();bcastTweaks();Chrome.render()};
 $('#ctrl-next').oninput=function(e){Tw.chrome.next=e.target.value;saveTw();bcastTweaks();Chrome.render()};
wireSeg('headerVis',function(){return Tw.vis.header},function(v){Tw.vis.header=+v});

"""
rep('/* ═════════ HOTKEYS',CHROME_JS+'/* ═════════ HOTKEYS','js-chrome')

if s!=orig:
    io.open(P,'w',encoding='utf-8').write(s)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

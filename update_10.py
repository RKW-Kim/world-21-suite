import io,os,sys
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overly','test-8.html')
if not os.path.exists(P): print('MISSING: '+P);sys.exit(1)
s=io.open(P,encoding='utf-8').read(); orig=s
applied,skipped=[],[]
def rep(a,b,tag):
    global s
    if a in s: s=s.replace(a,b,1);applied.append(tag)
    else: skipped.append(tag+' (anchor)')
def rng(a,b,new,tag):
    global s
    i=s.find(a)
    if i<0: skipped.append(tag+' (start)');return
    j=s.find(b,i)
    if j<0: skipped.append(tag+' (end)');return
    s=s[:i]+new+s[j+len(b):];applied.append(tag)

# 0 · stray CJK line (idempotent)
if '\u6d3b\u8dc3' in s:
    s='\n'.join(l for l in s.split('\n') if '\u6d3b\u8dc3' not in l);applied.append('strip-cjk')
else: skipped.append('strip-cjk (clean)')

# 1 · STORAGE v10 — isolate from test-7 poison + ?safe=1 nuke
rep("""(function(){try{Tw=merge(JSON.parse(JSON.stringify(DEF)),JSON.parse(localStorage.getItem('smile-suite-v9')||'{}'))}catch(e){}})();
const saveTw=()=>{try{localStorage.setItem('smile-suite-v9',JSON.stringify(Tw))}catch(e){}};""",
"""(function(){try{var raw=localStorage.getItem('smile-suite-v10');if(raw){Tw=merge(JSON.parse(JSON.stringify(DEF)),JSON.parse(raw))}}catch(e){}})();
const saveTw=()=>{try{localStorage.setItem('smile-suite-v10',JSON.stringify(Tw))}catch(e){}};
if(params.get('safe')==='1'){try{['smile-suite-v10','smile-suite-v9','smile-suite-cmd','smile-goal'].forEach(function(k){localStorage.removeItem(k)})}catch(e){}Tw=JSON.parse(JSON.stringify(DEF))}""",
'storage-v10')

# 2 · command versioning — old test-7 broadcasts ignored
rep("const cmd=m=>{m._id=Math.random().toString(36).slice(2,9);",
    "const cmd=m=>{m.v=10;m._id=Math.random().toString(36).slice(2,9);",'cmd-version')
rep("if(!m||m._id===lastId)return;lastId=m._id;wentReal();",
    "if(!m||m.v!==10||m._id===lastId)return;lastId=m._id;wentReal();",'oncmd-guard')
rep("  case 'chat':Drawer.show(m.data);break;",
    "  case 'chat':Drawer.show(m.data);if(APP.ChatCol)APP.ChatCol.add(m.data);break;",'cmd-chat-col')
rep("  case 'goal':Goal.set(m.data||{});break;",
    "  case 'goal':Goal.set(m.data||{});break;\n  case 'news':if(APP.News)APP.News.push(m.data||{});break;",'cmd-news')
rep(" dismiss:()=>{wentReal();if(APP.Stage)APP.Stage.dismiss()}};",
    " dismiss:()=>{wentReal();if(APP.Stage)APP.Stage.dismiss()},\n news:t=>{wentReal();if(APP.News)APP.News.push(t)}};",'api-news')

# 3 · defaults: chat visibility + camera preview flag + frame label
rep("vis:{pip:1,sess:1,trades:1,ticker:1,island:1,piptag:1,market:1,glow:1,header:1},",
    "vis:{pip:1,sess:1,trades:1,ticker:1,island:1,piptag:1,market:1,glow:1,header:1,chat:1},",'def-vis-chat')
rep("cam:{mirror:0,fit:'cover',ratio:'16/9',size:376,dev:''}};",
    "cam:{mirror:0,fit:'cover',ratio:'16/9',size:376,dev:'',preview:0,label:'YOU'}};",'def-cam')
rep("b.toggle('hide-market',!v.market);b.toggle('hide-glow',!v.glow);b.toggle('hide-header',!v.header)}",
    "b.toggle('hide-market',!v.market);b.toggle('hide-glow',!v.glow);b.toggle('hide-header',!v.header);b.toggle('hide-chat',!v.chat)}",
    'applyvis-chat')
rep("full:{mode:'full',vis:{pip:0}},","full:{mode:'full',vis:{pip:1}},",'scene-full-frame')
rep("if(!IS_CONTROL)Cam.init();","if(!IS_CONTROL&&(Tw.cam.preview||!APP.CLEAN))Cam.init();",'cam-preview-gate')

# 4 · layout: clear of the tall logo block · pinned items skipped by anchor engine
rep("mx:44,mt:76,mb:112,","mx:44,mt:96,mb:120,",'layout-margins')
rep("for(const k in this.items){const it=this.items[k];if(!it)continue;",
    "for(const k in this.items){const it=this.items[k];if(!it||it.dataset.pinned)continue;",'layout-pinned')

# 5 · MEET removed — stub keeps old call sites alive
rng("/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 MEET STAGE \u2014 auto-speaker \u00b7 pin \u00b7 hands \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */",
    "else if(Tw.stage.autospeak)Meet.rotate()},5000);",
"""/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 MEET \u2014 removed v10 \u00b7 OBS owns video sources \u00b7 stub keeps old calls safe \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
const Meet={people:[{name:'YOU',color:'var(--c-accent)',ini:'YO',host:true,speaking:false}],main:0,analyser:null,_micAsk:false,
 rebuild(){},render(){},speak(){},rotate(){},useMic(){},micLevel(){return -1}};
APP.Meet=Meet;""",'meet-stub')
rep("  <div id=\"meetStage\"><div class=\"meet-main\" id=\"meetMain\"></div><div class=\"meet-strip\" id=\"meetStrip\"></div></div>\n",'','meet-html')

# 6 · meet scene buttons dropped
lines=s.split('\n'); n0=len(lines)
lines=[l for l in lines if 'data-scene="meet' not in l]
if len(lines)!=n0: applied.append('meet-scenes (%d)'%(n0-len(lines))); s='\n'.join(lines)
else: skipped.append('meet-scenes (none)')
rep("$('#ctrl-host').oninput=e=>{Tw.stage.host=e.target.value||'You \u00b7 Host';saveTw();bcastTweaks()};",
    "var _hostEl=$('#ctrl-host');if(_hostEl)_hostEl.oninput=e=>{Tw.stage.host=e.target.value||'You \u00b7 Host';saveTw();bcastTweaks()};",'host-guard')

# 7 · HEADER — angular redesign + goal moved up + news rail
rng("  <div id=\"topStrap\">","  </div>\n  <div id=\"islandZone\">",
"""  <div id="topStrap">
    <div class="ts-logo">
      <span class="ts-mark"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" style="fill:var(--c-accent)"/><circle cx="31" cy="35" r="5.5" style="fill:var(--c-on-accent)"/><circle cx="69" cy="35" r="5.5" style="fill:var(--c-on-accent)"/><path d="M 20 48 A 30 30 0 0 0 80 48" fill="none" style="stroke:var(--c-on-accent)" stroke-width="7.5" stroke-linecap="round"/></svg></span>
      <span class="ts-livettl"><b id="tsTitle">SMILE MARKETS</b><small>SMILE.CO.KE</small></span>
    </div>
    <div class="ts-cluster">
      <span class="ts-date num" id="tsDate">\u2014 \u2014 \u2014</span>
      <i class="ts-slash"></i>
      <span class="ts-tz num" id="tsNbo"><b>NBO</b> --:--</span>
      <span class="ts-tz num" id="tsNyc"><b>NYC</b> --:--</span>
    </div>
    <div class="ts-goal" id="tsGoal"></div>
    <div class="ts-next" id="tsNext">NEXT \u00b7 <b>\u2014</b></div>
  </div>
  <div id="newsRail"><span class="nr-tag" id="newsTag">NEWS</span><span class="nr-txt" id="newsTxt"></span><span class="nr-time num" id="newsTime"></span></div>
  <div id="islandZone">""",'header-html')

rng("/* \u2500\u2500 update_09 \u00b7 broadcast chrome \u2500\u2500 */",".ts-next b{color:var(--c-accent);font-weight:700}",
"""/* \u2500\u2500 v10 \u00b7 broadcast chrome \u2014 angular header \u2500\u2500 */
#topStrap{position:absolute;left:0;right:0;top:0;height:58px;z-index:55;display:flex;align-items:center;gap:14px;padding:0 18px 0 0;pointer-events:none;background:linear-gradient(180deg,rgba(5,5,7,.62),rgba(5,5,7,.24) 62%,transparent);transition:opacity .4s ease,transform .5s var(--ease)}
body.hide-header #topStrap,body.ticker-top #topStrap{opacity:0;transform:translateY(-100%)}
body.hide-header #islandZone{top:22px}
.ts-logo{display:flex;align-items:center;gap:12px;height:74px;margin:8px 16px 0 0;padding:0 30px 0 18px;background:linear-gradient(160deg,#FFD84E,#FFC107 55%,#EDA400);clip-path:polygon(0 0,100% 0,calc(100% - 16px) 100%,0 100%);box-shadow:0 16px 32px -12px rgba(255,193,7,.4)}
.ts-mark svg{width:38px;height:38px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.28))}
.ts-livettl{display:flex;flex-direction:column;gap:4px;padding-right:12px}
.ts-livettl b{font-family:var(--f-d);font-weight:700;font-size:15px;letter-spacing:.14em;color:var(--c-on-accent);line-height:1;text-transform:uppercase}
.ts-livettl small{font-family:var(--f-m);font-size:8px;letter-spacing:.32em;color:rgba(10,10,10,.6)}
.ts-cluster{display:flex;align-items:center;gap:12px;height:40px;padding:0 16px;border-radius:10px;background:rgba(10,10,12,.72);border:1px solid rgba(255,255,255,.09);backdrop-filter:blur(14px) saturate(150%);box-shadow:inset 0 1px 0 rgba(255,255,255,.09);white-space:nowrap}
.ts-slash{width:2px;height:20px;background:rgba(var(--c-accent-rgb),.38);transform:skewX(-20deg);border-radius:1px;flex:none}
.ts-date,.ts-tz{font-family:var(--f-m);font-size:10.5px;letter-spacing:.12em;color:var(--c-muted)}
.ts-tz b{color:var(--c-fg);font-weight:600}
.ts-goal{display:flex;align-items:center;gap:11px;height:40px;padding:0 16px;border-radius:10px 10px 10px 0;background:rgba(10,10,12,.72);border:1px solid rgba(255,255,255,.09);border-left:2px solid var(--c-accent);backdrop-filter:blur(14px);white-space:nowrap}
.ts-goal .cb-lbl{color:var(--c-accent);font-weight:700;font-family:var(--f-d);font-size:9px;letter-spacing:.2em;flex:none}
.ts-goal .cb-bar{width:120px;height:10px;flex:none}
.ts-goal .cb-val{color:var(--c-fg);font-weight:600;font-size:11.5px}
.ts-next{margin-left:auto;font-family:var(--f-m);font-size:9.5px;letter-spacing:.14em;color:var(--c-muted);background:rgba(var(--c-accent-rgb),.08);box-shadow:inset 0 0 0 1px rgba(var(--c-accent-rgb),.28);border-radius:999px;padding:9px 14px;white-space:nowrap}
.ts-next b{color:var(--c-accent);font-weight:700}""",'header-css')

# 8 · footer crawl / news rail / chat column / video frame / clean mode CSS
rep("</style>",
"""/* \u2500\u2500 v10 \u00b7 footer crawl \u00b7 news \u00b7 chat column \u00b7 video frame \u2500\u2500 */
#ticker{height:56px;border-radius:0;background:rgba(8,8,10,.9);border:0;border-top:1px solid rgba(255,255,255,.08);backdrop-filter:blur(18px) saturate(160%);box-shadow:0 -12px 34px rgba(0,0,0,.4)}
body.ticker-top #ticker{transform:translateY(calc(-100vh + 56px))}
.cap.left{background:transparent;border-right:1px solid rgba(255,255,255,.08);border-radius:0;padding:0 18px 0 16px;color:var(--c-fg)}
.cap.left svg{height:30px}
.cap.right{width:250px;background:rgba(255,255,255,.03)}
.item{gap:12px;margin-right:56px}
.item::before{width:5px;height:5px;transform:rotate(45deg);box-shadow:none}
#newsRail{position:absolute;left:0;right:0;bottom:56px;height:46px;z-index:39;display:flex;align-items:center;gap:14px;padding:0 18px;background:rgba(10,10,13,.93);border-top:1px solid rgba(255,255,255,.09);backdrop-filter:blur(18px);transform:translateX(-104%);opacity:0;transition:transform .6s var(--isl-spring),opacity .3s ease;pointer-events:none;overflow:hidden}
#newsRail.on{transform:none;opacity:1}
#newsRail.breaking{border-top-color:rgba(246,70,93,.5)}
.nr-tag{flex:none;font-family:var(--f-d);font-weight:700;font-size:10px;letter-spacing:.22em;padding:6px 13px;color:var(--c-on-accent);background:var(--c-accent);clip-path:polygon(0 0,100% 0,calc(100% - 8px) 100%,0 100%)}
#newsRail.breaking .nr-tag{background:var(--c-down);color:#fff;animation:softpulse 1.2s infinite}
.nr-txt{font-family:var(--f-d);font-weight:600;font-size:14px;letter-spacing:.04em;color:var(--c-fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#newsRail.breaking .nr-txt{color:#FFD7DC}
.nr-time{margin-left:auto;flex:none;font-family:var(--f-m);font-size:9.5px;letter-spacing:.16em;color:var(--c-faint)}
body.hide-ticker #newsRail{bottom:0}
#chatCol{position:absolute;right:20px;top:70px;bottom:80px;width:384px;z-index:16;display:none;flex-direction:column;gap:8px;justify-content:flex-end;overflow:hidden;pointer-events:none}
body[data-scene="soloChat"] #chatCol{display:flex}
body.hide-chat #chatCol{display:none!important}
.cRow{display:flex;gap:10px;align-items:flex-start;background:rgba(14,14,17,.72);border:1px solid rgba(255,255,255,.08);border-left:2px solid var(--c-accent);border-radius:12px;padding:10px 12px;backdrop-filter:blur(14px);animation:chIn .5s var(--ease) both}
.cRow .drw-plat{width:28px;height:28px}
.cRow .drw-plat svg{width:14px;height:14px}
.cRow .drw-user{font-size:11.5px}
.cRow .drw-txt{font-size:12px;margin-top:2px;-webkit-line-clamp:4}
.pip-card::before{content:"";position:absolute;left:10px;top:10px;width:20px;height:20px;border-left:2px solid rgba(var(--c-accent-rgb),.85);border-top:2px solid rgba(var(--c-accent-rgb),.85);border-radius:6px 0 0 0;pointer-events:none;z-index:2}
.pip-card::after{content:"";position:absolute;right:10px;bottom:10px;width:20px;height:20px;border-right:2px solid rgba(var(--c-accent-rgb),.85);border-bottom:2px solid rgba(var(--c-accent-rgb),.85);border-radius:0 0 6px 0;pointer-events:none;z-index:2}
#frameLabel{position:absolute;left:12px;bottom:12px;z-index:2;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:5px 10px;font-family:var(--f-d);font-weight:700;font-size:10.5px;letter-spacing:.14em;color:#fff;backdrop-filter:blur(8px)}
#frameLabel i{width:6px;height:6px;border-radius:50%;background:var(--c-down);animation:softpulse 1.4s infinite}
.rsz{position:absolute;right:5px;bottom:5px;z-index:4;width:22px;height:22px;cursor:nwse-resize;opacity:0;transition:.25s;display:grid;place-items:center;color:rgba(255,255,255,.65)}
.pip-card:hover .rsz{opacity:1}
.rsz svg{width:12px;height:12px;stroke:currentColor;stroke-width:2;fill:none;stroke-linecap:round}
body.clean #viewerApp{background:transparent}
body.clean .bg-grad,body.clean .market-bg{opacity:0;transition:opacity .4s ease}
body.clean.mode-full #stageCam{display:none}
body.clean.mode-full #pip{display:block!important}
</style>""",'css-v10')

# 9 · frame label element
rep("      <span class=\"pip-hint\">CAMERA \u00b7 AUTO-PLACE</span>",
    "      <span class=\"pip-hint\">CAMERA \u00b7 AUTO-PLACE</span>\n      <span id=\"frameLabel\"><i></i>YOU</span>",'frame-label-html')

# 10 · participants section -> News Flash section
rng("  <section>\n    <h2>Stage &amp; Participants <span class=\"hint\">meet engine</span></h2>",
    "    <div id=\"pList\"></div>\n  </section>",
"""  <section>
    <h2>News Flash <span class="hint">headline strap above the crawl</span></h2>
    <div class="ctl-inline" style="margin-bottom:12px">
      <input type="text" id="news-text" placeholder="FED HOLDS RATES \u00b7 MARKETS REACT" style="flex:1;min-width:200px">
      <div class="seg" data-seg="newsLevel"><button data-val="info">News</button><button data-val="breaking">Breaking</button></div>
      <button class="mini-btn" id="news-push" data-ico="mega">Push</button>
    </div>
    <div class="isl-tests">
      <button class="mini-btn" id="news-test-1" data-ico="zap">Test Breaking</button>
      <button class="mini-btn" id="news-test-2" data-ico="clock">Test News</button>
    </div>
    <p style="font-size:11px;color:#71717a;line-height:1.6;margin-top:10px">Also fires from state.json: {"news":"FED CUTS 25BPS"} or {"news":{"text":"\u2026","level":"breaking"}}. Breaking pre-empts News.</p>
  </section>""",'news-section')

# 11 · camera section -> Video Frame & Camera
rep("    <h2>Camera</h2>",
"""    <h2>Video Frame &amp; Camera</h2>
    <p style="font-size:11px;color:#a1a1aa;line-height:1.6;margin:0 0 14px">OBS owns the video: put your camera source UNDER this overlay, then drag &amp; resize the yellow-cornered frame to match it. Browser preview is optional (grant via Interact).</p>
    <div class="ctrl-row"><label>Frame Label</label><input type="text" id="ctrl-framelabel" placeholder="YOU" style="min-width:150px"></div>
    <div class="ctrl-row"><label>Browser Cam Preview</label><label class="switch"><input type="checkbox" id="ctrl-cam-prev"><span class="sl"></span></label></div>""",'frame-section')

# 12 · goal controls in chrome section
rep("    <div class=\"ctrl-row\"><label>Up Next</label><input type=\"text\" id=\"ctrl-next\" placeholder=\"MARKET WAKE UP \u00b7 08:00\" style=\"min-width:190px\"></div>",
"""    <div class="ctrl-row"><label>Up Next</label><input type="text" id="ctrl-next" placeholder="MARKET WAKE UP \u00b7 08:00" style="min-width:190px"></div>
    <div class="ctrl-row"><label>Goal Label</label><input type="text" id="goal-label" style="min-width:150px"></div>
    <div class="ctrl-row"><label>Goal Current</label><input type="number" id="goal-cur" style="min-width:110px"><button class="mini-btn" id="goal-set" data-ico="check">Set</button></div>
    <div class="ctrl-row"><label>Goal Target</label><input type="number" id="goal-tgt" style="min-width:110px"></div>""",'goal-controls')

# 13 · layers: chat column
rep(" {k:'trades',name:'Signals',note:'tracker',pos:1},",
    " {k:'trades',name:'Signals',note:'tracker',pos:1},\n {k:'chat',name:'Chat Column',note:'solo scenes',pos:0},",'layers-chat')

# 14 · Chrome.render renders the goal too
rng(" render(){const q=function(id){return document.getElementById(id)};if(!q('tsTitle'))return;",
    "esc(Tw.chrome.next||'')+'</b>'}};",
""" render(){const q=function(id){return document.getElementById(id)};if(!q('tsTitle'))return;
  const d=new Date();
  const day=d.toLocaleDateString('en-US',{weekday:'short'}).toUpperCase();
  const dm=d.toLocaleDateString('en-US',{day:'2-digit',month:'short'}).toUpperCase();
  if(q('tsDate'))q('tsDate').textContent=day+' '+dm;
  if(q('tsNbo'))q('tsNbo').innerHTML='<b>NBO</b> '+this.fmt('Africa/Nairobi');
  if(q('tsNyc'))q('tsNyc').innerHTML='<b>NYC</b> '+this.fmt('America/New_York');
  if(q('tsTitle'))q('tsTitle').textContent=Tw.chrome.title||'';
  if(q('tsNext'))q('tsNext').innerHTML='NEXT \u00b7 <b>'+esc(Tw.chrome.next||'')+'</b>';
  if(q('tsGoal')){const g=Goal.d,pct=clamp(g.cur/Math.max(1,g.tgt)*100,0,100);
   q('tsGoal').innerHTML='<span class="cb-lbl">'+esc(g.label)+'</span><span class="cb-bar"><i style="width:'+pct.toFixed(1)+'%"><svg viewBox="0 0 120 8" preserveAspectRatio="none"><path d="M0 4 Q7.5 1 15 4 T30 4 T45 4 T60 4 Q67.5 1 75 4 T90 4 T105 4 T120 4 V8 H0 Z"/></svg></i></span><b class="cb-val num">'+fmtN(g.cur)+'<em>/'+fmtN(g.tgt)+'</em></b>'}};""",'chrome-goal')

# 15 · Goal.set refreshes header · Cap loses the goal · smaller wordmark
rep(""" set(d){merge(this.d,d);try{localStorage.setItem('smile-goal',JSON.stringify(this.d))}catch(e){}
  Cap.refresh();Cap.i=0;if(APP.Panel)APP.Panel.syncGoal&&APP.Panel.syncGoal()}};""",
""" set(d){merge(this.d,d);try{localStorage.setItem('smile-goal',JSON.stringify(this.d))}catch(e){}
  Cap.refresh();Cap.i=0;if(APP.Chrome)APP.Chrome.render();if(APP.Panel)APP.Panel.syncGoal&&APP.Panel.syncGoal()}};""",'goal-header')
rng(" items(){const g=Goal.d;","PLAN THE ENTRY</span>']},",
""" items(){const n=nextSession();
  return [
   '<span class="cb-slide">JOIN THE FAMILY \u00b7 <b>smile.co.ke</b></span>',
   '<span class="cb-slide">'+n.k+' OPENS IN <b class="num">'+n.txt+'</b></span>',
   '<span class="cb-slide">RISK <b>1%</b> PER TRADE \u00b7 PLAN THE ENTRY</span>',
   '<span class="cb-slide">LIVE MARKETS \u00b7 <b>SMILE.CO.KE</b></span>']},""",'cap-items')
if "WORDMARK(38)" in s: rep("WORDMARK(38);","WORDMARK(30);",'capleft-size')
elif "MASCOT()+'<span>SMILE</span>'" in s: rep("MASCOT()+'<span>SMILE</span>'","WORDMARK(30);",'capleft-size')
else: skipped.append('capleft-size (anchor)')

# 16 · state.json news
rep("   this.lastEv=st.island.lastEvent.id;Stage.push(st.island.lastEvent)}",
    """   this.lastEv=st.island.lastEvent.id;Stage.push(st.island.lastEvent)}
  if(st.news){const n=(typeof st.news==='string')?{text:st.news}:st.news;
   if(n.text&&n.text!==this.lastNews){this.lastNews=n.text;if(APP.News)APP.News.push(n)}}""",'state-news')

# 17 · demo includes news flashes
rep("  this.schedule(1400,()=>Stage.push({type:'follow',name:'Maya'}));",
"""  this.schedule(1400,()=>Stage.push({type:'follow',name:'Maya'}));
  this.schedule(6400,()=>News.push({text:'FED HOLDS RATES \u00b7 EQUITIES RIP HIGHER',level:'breaking'}));
  this.schedule(30500,()=>News.push({text:'S&P 500 PRINTS FRESH RECORD HIGH'}));""",'demo-news')

# 18 · Scenes.apply drives ScenePin
rep("  if(Tw.stage.mode==='meet')Meet.rebuild();\n  applyVis()}",
    "  applyVis();if(window.ScenePin)ScenePin.apply(this.current)}",'scenes-pin')

# 19 · BOOT — island first, guarded steps, error surface
rng("/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 BOOT \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */",
    "if(!IS_CONTROL&&!APP.CLEAN)Demo.start();",
"""/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 BOOT v10 \u2014 island first, every step guarded \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
addEventListener('error',function(e){console.error('[smile]',e.message);if(IS_DEBUG)toast('JS error \u2014 open console')});
function bootstep(n,fn){try{fn()}catch(e){console.error('[smile boot:'+n+']',e)}}
if(APP.CLEAN){Tw.vis.market=0;Tw.vis.glow=0}
bootstep('shell',function(){if(APP.CLEAN)document.body.classList.add('clean');
 $('#viewerApp').classList.toggle('active',!IS_CONTROL);
 $('#controlPanel').classList.toggle('active',IS_CONTROL)});
bootstep('theme',applyAll);
bootstep('island',function(){if(IS_DEBUG)document.body.classList.add('debug');
 podP.el.classList.add('on');sync();Eng.wake();podP.paint();
 if(podP.w.t<140)podP.w.to(380,300,26)});
bootstep('chrome',function(){Scenes.apply();Chrome.render()});
bootstep('ticker',function(){Cap.refresh();Px.sim();Px.binance();Marquee.measure();
 setTimeout(function(){Marquee.measure();fitP()},650)});
bootstep('state',function(){StatePoll.start()});
bootstep('demo',function(){if(!IS_CONTROL&&!APP.CLEAN)Demo.start()});""",'boot-v10')

# 20 · v10 runtime — News \u00b7 ChatCol \u00b7 ScenePin \u00b7 frame resize/label \u00b7 wiring
rep("/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 HOTKEYS",
"""/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 NEWS FLASH \u2014 headline strap above the crawl \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
const News={q:[],cur:null,t:0,
 push(o){if(typeof o==='string')o={text:o};if(!o||!o.text)return;
  o.level=(o.level==='breaking')?'breaking':'info';
  o.dwell=o.dwell||(o.level==='breaking'?11000:7000);
  if(this.cur&&this.cur.level==='breaking'&&o.level==='info'){this.q.push(o);if(this.q.length>4)this.q.shift();return}
  if(!this.cur){this.play(o);return}
  this.q.push(o);if(this.q.length>4)this.q.shift()},
 play(o){this.cur=o;const r=document.getElementById('newsRail');if(!r)return;
  r.className='on '+o.level;
  document.getElementById('newsTag').textContent=o.level==='breaking'?'BREAKING':'NEWS';
  const tx=document.getElementById('newsTxt');tx.textContent=o.text;tx.title=o.text;
  document.getElementById('newsTime').textContent=new Date().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});
  clearTimeout(this.t);this.t=setTimeout(()=>this.end(),o.dwell)},
 end(){const r=document.getElementById('newsRail');if(r)r.className='';this.cur=null;
  setTimeout(()=>{if(this.q.length)this.play(this.q.shift())},650)}};
APP.News=News;

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 CHAT COLUMN \u2014 persistent feed for solo scenes \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
const ChatCol={add(d){const col=document.getElementById('chatCol');if(!col||!d)return;
  const plat=PLATS[d.plat||'yt'];
  const row=document.createElement('div');row.className='cRow';
  row.innerHTML='<div class="drw-plat" style="color:'+plat.c+'">'+plat.svg+'</div>'
   +'<div style="min-width:0;flex:1"><div class="drw-user">'+esc(d.name||'Viewer')+'<em>@'+esc(d.handle||'smile')+'</em></div>'
   +'<p class="drw-txt">'+esc(d.msg||'')+'</p></div>';
  col.appendChild(row);
  while(col.children.length>7)col.removeChild(col.firstChild);
  setTimeout(()=>{row.style.transition='opacity .6s ease';row.style.opacity='0';
   setTimeout(()=>{if(row.parentNode)row.parentNode.removeChild(row)},650)},60000)}};
APP.ChatCol=ChatCol;

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 SCENE PIN \u2014 layouts that FILL the frame \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
const ScenePin={
 map:{
  full:{pip:{left:0,top:0,width:'100vw',height:'100vh'},sess:{hide:1},trades:{hide:1}},
  soloChat:{pip:{left:20,top:70,width:'calc(100vw - 432px)',height:'calc(100vh - 150px)'},sess:{hide:1},trades:{hide:1}},
  soloTrades:{pip:{left:20,top:70,width:'calc(100vw - 436px)',height:'calc(100vh - 150px)'},sess:{hide:1}},
  desk:{pip:{left:'50%',top:96,ml:-300,width:600,height:'calc(100vh - 250px)'},sess:{left:20,top:88},trades:{right:20,top:88}},
  minimal:{pip:{left:'50%',bottom:84,ml:-170,width:340,height:191},sess:{hide:1},trades:{hide:1}},
  webp:{}},
 el(k){return k==='pip'?document.getElementById('pip'):k==='sess'?document.getElementById('slotSess'):k==='trades'?document.getElementById('slotTrades'):document.getElementById('chatCol')},
 apply(name){document.body.dataset.scene=name||'';
  ['pip','sess','trades','chat'].forEach(k=>{const it=this.el(k);if(!it)return;
   const cfg=(name&&this.map[name]&&this.map[name][k])||null;
   if(cfg&&cfg.hide){it.dataset.pinned='1';it.style.opacity='0';it.style.pointerEvents='none';return}
   if(!cfg){delete it.dataset.pinned;it.style.opacity='';it.style.pointerEvents='';
    ['left','top','right','bottom','width','height','marginLeft'].forEach(p=>it.style[p]='');
    const pc=it.querySelector('.pip-card');if(pc){pc.style.aspectRatio='';pc.style.height=''}
    Layout.apply();return}
   it.dataset.pinned='1';it.style.opacity='';it.style.pointerEvents='';
   ['left','top','right','bottom','width','height','marginLeft'].forEach(p=>it.style[p]='');
   if(cfg.ml!=null)it.style.marginLeft=cfg.ml+'px';
   if(cfg.left!=null)it.style.left=cfg.left;
   if(cfg.top!=null)it.style.top=cfg.top;
   if(cfg.right!=null)it.style.right=cfg.right;
   if(cfg.bottom!=null)it.style.bottom=cfg.bottom;
   if(cfg.width!=null)it.style.width=cfg.width;
   if(cfg.height!=null)it.style.height=cfg.height;
   if(k==='pip'){const pc=it.querySelector('.pip-card');
    if(pc&&cfg.height!=null){pc.style.aspectRatio='auto';pc.style.height='100%'}}});
  Layout.apply()}};
window.ScenePin=ScenePin;

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 VIDEO FRAME \u2014 label \u00b7 resize \u00b7 preview \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
(function(){
 var fl=document.getElementById('frameLabel');
 if(fl)fl.innerHTML='<i></i>'+esc(Tw.cam.label||'YOU');
 var fi=document.getElementById('ctrl-framelabel');
 if(fi){fi.value=Tw.cam.label||'YOU';
  fi.oninput=function(e){Tw.cam.label=e.target.value||'YOU';saveTw();bcastTweaks();
   if(fl)fl.innerHTML='<i></i>'+esc(Tw.cam.label)}}
 wireSwitch('ctrl-cam-prev',function(){return Tw.cam.preview},function(v){Tw.cam.preview=v;if(v)Cam.init()});
 var pc=document.querySelector('.pip-card'),pip=document.getElementById('pip');
 if(pc&&pip){var rz=document.createElement('span');rz.className='rsz';
  rz.innerHTML='<svg viewBox="0 0 24 24"><line x1="22" y1="14" x2="14" y2="22"/><line x1="22" y1="8" x2="8" y2="22"/></svg>';
  pc.appendChild(rz);
  rz.addEventListener('pointerdown',function(ev){ev.preventDefault();ev.stopPropagation();
   pip.classList.add('dragging');pip.dataset.pinned='1';
   var sx=ev.clientX,sy=ev.clientY,ow=pip.offsetWidth,oh=pc.offsetHeight;
   var mv=function(e2){pip.style.width=clamp(ow+e2.clientX-sx,220,1400)+'px';
    pc.style.aspectRatio='auto';pc.style.height=clamp(oh+e2.clientY-sy,120,innerHeight-140)+'px'};
   var up=function(){removeEventListener('pointermove',mv);removeEventListener('pointerup',up);pip.classList.remove('dragging')};
   addEventListener('pointermove',mv);addEventListener('pointerup',up)})}})();

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 NEWS + GOAL wiring \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
(function(){var newsLevel='info';
 wireSeg('newsLevel',function(){return newsLevel},function(v){newsLevel=v});
 var np=document.getElementById('news-push');
 if(np)np.onclick=function(){var t=document.getElementById('news-text').value.trim();if(!t)return toast('Type a headline');
  var d={text:t,level:newsLevel};News.push(d);cmd({cmd:'news',data:d})};
 var t1=document.getElementById('news-test-1');
 if(t1)t1.onclick=function(){var d={text:'BREAKING \u00b7 EMERGENCY FED DECISION IN 30 MIN',level:'breaking'};News.push(d);cmd({cmd:'news',data:d})};
 var t2=document.getElementById('news-test-2');
 if(t2)t2.onclick=function(){var d={text:'ETHEREUM ETF INFLOWS HIT RECORD $1.2B WEEKLY',level:'info'};News.push(d);cmd({cmd:'news',data:d})};
 var gl=document.getElementById('goal-label'),gc=document.getElementById('goal-cur'),gt=document.getElementById('goal-tgt');
 if(gl)gl.value=Goal.d.label;if(gc)gc.value=Goal.d.cur;if(gt)gt.value=Goal.d.tgt;
 var gs=document.getElementById('goal-set');
 if(gs)gs.onclick=function(){var d={label:(gl.value||'').trim()||'SUB GOAL',cur:+gc.value||0,tgt:+gt.value||1};
  Goal.set(d);cmd({cmd:'goal',data:d});toast('Goal updated')}})();

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 HOTKEYS""",'js-v10')

if s!=orig: io.open(P,'w',encoding='utf-8').write(s)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

import io,os,sys
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P) or os.path.getsize(P)==0:
    print('💥 overlay/live.html missing or empty — say "rebuild" to me');sys.exit(1)
s=io.open(P,encoding='utf-8').read();orig=s
applied,skipped=[],[]
def rep(a,b,tag):
    global s
    if a in s:s=s.replace(a,b,1);applied.append(tag)
    else:skipped.append(tag)
def rng(a,b,new,tag):
    global s
    i=s.find(a)
    if i<0:skipped.append(tag+' (start)');return
    j=s.find(b,i)
    if j<0:skipped.append(tag+' (end)');return
    s=s[:i]+new+s[j+len(b):];applied.append(tag)

# 1 · kill the 560px ambient glow behind the island
rng('#islw{position:absolute;top:11px;left:50%;transform:translateX(-50%);z-index:60;display:flex;align-items:flex-start;pointer-events:none}',
'@keyframes islglow{0%,100%{opacity:.45}50%{opacity:1}}',
'#islw{position:absolute;top:11px;left:50%;transform:translateX(-50%);z-index:60;pointer-events:none}','css-kill-glow')

# 2 · THE bug — restore display:flex (identity + stage side by side)
rep('#isl{position:relative;overflow:hidden;border-radius:999px;',
    '#isl{position:relative;display:flex;align-items:center;padding-left:9px;overflow:hidden;border-radius:999px;','css-isl-flex')

# 3 · punch-hole mascot socket
rng('#idb{position:relative;height:100%;flex:none;z-index:2}',
'#isl.tall #imicro{opacity:1;transform:none}',
'''#punch{flex:none;width:38px;height:38px;border-radius:50%;background:#000;box-shadow:inset 0 0 0 1px rgba(255,255,255,.07);display:grid;place-items:center;position:relative;z-index:2}
#punch .smk{width:30px;height:30px}''','css-punch')

# 4 · stage = single content region
rng('#stg{position:relative;height:100%;flex:1 1 auto;min-width:0;z-index:2}',
'#isl.liquid #stg::before{background:rgba(0,0,0,.25)}',
'#stg{position:relative;flex:1 1 auto;min-width:0;height:100%;z-index:2;margin-left:10px}','css-stg')

# 5 · dead mini CSS
rng('.miniwrap{display:flex;align-items:center;gap:9px}',
'.mini{font-size:12.5px;font-weight:700}','','css-mini-dead')

# 6 · liquid overrides — socket tints, smile stays brand yellow
rng('#isl.liquid #ifull,#isl.liquid #imicro{color:var(--on)}',
'#isl.liquid .smk .fc{fill:var(--on)}#isl.liquid .smk .fe{fill:var(--acc)}#isl.liquid .smk .fm{stroke:var(--acc)}',
'''#isl.liquid .lv{color:var(--on)}
#isl.liquid .upt,#isl.liquid .psym,#isl.liquid .ppc,#isl.liquid .sdt{color:rgba(10,10,10,.6)}
#isl.liquid .ppx{color:var(--on)}
#isl.liquid .ihair{background:rgba(0,0,0,.2)}
#isl.liquid #punch{background:rgba(0,0,0,.16);box-shadow:none}''','css-liquid-punch')

# 7 · idle view + horizontal tick animation
rep('.view.as{gap:13px;padding:0 20px}',
'.view.as{gap:13px;padding:0 20px}\n.view.idle{justify-content:space-between;padding:0 18px 0 2px}\n.idleg{display:flex;align-items:center;gap:10px}','css-view-idle')
rng('.roll{animation:roll .5s var(--ease)}',
'@keyframes roll{0%{transform:translateY(55%);opacity:0;filter:blur(3px)}100%{transform:none;opacity:1;filter:none}}',
'''.roll{animation:tickUp .32s var(--ease)}
.roll.dn{animation-name:tickDown}
@keyframes tickUp{0%{opacity:0;transform:translateX(12px);color:var(--up)}100%{opacity:1;transform:none;color:var(--fg)}}
@keyframes tickDown{0%{opacity:0;transform:translateX(12px);color:var(--down)}100%{opacity:1;transform:none;color:var(--fg)}}''','css-tick')

# 8 · equal header pills, masthead gone
rep('.pill{display:flex;align-items:center;height:44px;padding:0 8px;',
    '.pill{display:flex;align-items:center;height:44px;padding:0 8px;flex:1 1 0;min-width:0;max-width:560px;','css-pill-flex')
rng('.mst{display:flex;align-items:center;gap:10px;height:100%;padding:0 12px 0 16px}',
'.murl{font-family:var(--fm);font-size:9px;letter-spacing:.22em;color:var(--fnt)}',
'''#pillL{justify-content:flex-start}
#pillR{margin-left:auto;justify-content:flex-end}''','css-pill-align')
rep('@media (max-width:1080px){#goalSeg{display:none}}',
'@media (max-width:1080px){#goalSeg{display:none}}\n@media (max-width:1080px){#pillL{display:none}}\n@media (max-width:1500px){.pill{max-width:470px}}','css-pill-mq')
rng('<header id="hdr">','</header>',
'''<header id="hdr">
  <div class="pill" id="pillL">
    <span class="sgt" id="goalChip"><span class="glabel" id="goalLabel">SUB GOAL</span><span class="gbar"><i id="goalFill" style="width:0%"><svg viewBox="0 0 120 8" preserveAspectRatio="none"><path d="M0 4 Q7.5 1 15 4 T30 4 T45 4 T60 4 Q67.5 1 75 4 T90 4 T105 4 T120 4 V8 H0 Z"/></svg></i></span><b class="mono" id="goalVal">\u2014</b></span>
  </div>
  <div class="pill" id="pillR">
    <span class="sgt"><span id="clkDate">\u2014 \u2014 \u2014</span><i class="cdot"></i><span class="clktz mono" id="clkNbo"><b>NBO</b> --:--</span><span class="clktz mono" id="clkNyc"><b>NYC</b> --:--</span></span>
    <span class="sgt" id="nextSeg"><i class="cdot"></i><span class="nlab">NEXT</span><b id="nextTxt">MARKET WAKE UP \u00b7 08:00 EAT</b></span>
  </div>
</header>''','html-header')

# 9 · island HTML — punch + single stage
rng('<div id="islw"><div id="isl">','<div id="stg"></div>\n</div></div>',
'''<div id="islw"><div id="isl">
  <div class="bubs"><i style="left:12%;width:5px;height:5px;animation-delay:0s"></i><i style="left:32%;width:8px;height:8px;animation-delay:1.3s"></i><i style="left:50%;width:4px;height:4px;animation-delay:2.2s"></i><i style="left:68%;width:7px;height:7px;animation-delay:.7s"></i><i style="left:86%;width:5px;height:5px;animation-delay:1.8s"></i></div>
  <div id="punch"><svg class="smk" viewBox="0 0 100 100" width="30" height="30" aria-hidden="true"><circle class="fc" cx="50" cy="50" r="48"/><circle class="fe" cx="31" cy="35" r="5.5"/><circle class="fe" cx="69" cy="35" r="5.5"/><path class="fm" d="M 20 48 A 30 30 0 0 0 80 48"/></svg></div>
  <div id="stg"></div>
</div></div>''','html-island')

# 10 · geometry: bigger footer logo, lanes unstacked
rep('.flogo svg{height:26px;width:auto}','.flogo svg{height:39px;width:auto}','css-flogo-big')
rep('#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:48px;','#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:54px;','css-ftr-h')
rep('#news{position:absolute;left:50%;bottom:88px;','#news{position:absolute;left:50%;bottom:94px;','css-news-up')
rep('#drawer{position:absolute;right:16px;bottom:66px;','#drawer{position:absolute;right:16px;bottom:72px;','css-drawer-up')
rep('#csl{position:absolute;left:50%;bottom:64px;','#csl{position:absolute;left:50%;bottom:152px;','css-csl-up')
rep('#hint{position:absolute;left:50%;bottom:70px;','#hint{position:absolute;left:50%;bottom:170px;','css-hint-up')

# 11 · frame CSS -> web stage
rng('/* video frame */','#frame.drag{opacity:.85}',
'''/* web stage (?web=1|URL) \u2014 interactive site under the chrome */
#webStage{position:absolute;inset:0;width:100%;height:100%;border:0;z-index:1;background:#0d0d10}
body.mode-web #stage{display:none!important}''','css-webstage')

# 12 · frame HTML removed
rng('<div id="frame">','<span id="frameRsz"><svg viewBox="0 0 24 24"><line x1="22" y1="14" x2="14" y2="22"/><line x1="22" y1="8" x2="8" y2="22"/></svg></span>\n</div>','','html-frame-gone')

# 13 · panel: drop frame/label, add web
rep('<button class="cbtn on" data-layer="frame">Frame</button>','','panel-frame-btn')
rep('<div class="crow"><label>Label</label><input type="text" id="ctlLabel" maxlength="18"></div>\n','','panel-label-row')
rep('<button class="cbtn" id="ctlSlow">1/4x</button>','<button class="cbtn" id="ctlSlow">1/4x</button><button class="cbtn" id="ctlWeb">Web Stage</button>','panel-web-btn')

# 14 · JS params
rep('?hide=header,footer,news,frame,goal,next \u00b7 ?label=YOU \u00b7 ?next=TEXT \u00b7 ?cur=$ \u00b7 ?speed=52',
    '?hide=header,footer,news,goal,next \u00b7 ?next=TEXT \u00b7 ?cur=$ \u00b7 ?speed=52 \u00b7 ?web=1|URL (site as backdrop)','comment-params')
rep("var LBL=String(P.get('label')||'YOU').slice(0,18);\n",'','js-lbl-gone')
rep(" case 'label':LBL=String(d||'YOU').slice(0,18);Frame.apply();break;\n",'','js-route-label')
rep("if(P.get('console')==='1'||DEMO)document.body.classList.add('console');",
    "if(P.get('console')==='1')document.body.classList.add('console');",'js-demo-no-console')

# 15 · horizontal directional price ticks
rep("set:function(sym,p,ch){var m=this.M[sym];if(!m||!isFinite(p)||p<=0)return;m.p=p;m.ch=ch||0;",
    "set:function(sym,p,ch){var m=this.M[sym];if(!m||!isFinite(p)||p<=0)return;var dn=(m.prev!=null&&p<m.prev);m.prev=p;m.p=p;m.ch=ch||0;","js-px-prev")
rep("if(pe){var t=fmtP(p);if(pe.textContent!==t){pe.textContent=t;pe.classList.remove('roll');void pe.offsetWidth;pe.classList.add('roll')}}",
    "if(pe){var t=fmtP(p);if(pe.textContent!==t){pe.textContent=t;pe.classList.remove('roll','dn');void pe.offsetWidth;pe.classList.add('roll');if(dn)pe.classList.add('dn')}}","js-px-tick")
rep("if(sym==='BTC'){var g=Isl.idrefs||{};\n   if(g.px){g.px.textContent=fmtP(p);g.px.classList.remove('roll');void g.px.offsetWidth;g.px.classList.add('roll')}",
    "if(sym==='BTC'&&Isl.view==='idle'){var g=Isl.idrefs||{};\n   if(g.px){g.px.textContent=fmtP(p);g.px.classList.remove('roll','dn');void g.px.offsetWidth;g.px.classList.add('roll');if(dn)g.px.classList.add('dn')}}","js-px-isl-tick")

# 16 · island engine — GEO + idle view + punch architecture
rng("var GEO={as:{w:640,h:64,r:999},al:{w:700,h:150,r:38},trade:{w:720,h:236,r:40},res:{w:600,h:112,r:32}};",
"if(!self.view)self.stg.innerHTML=''},430)}};",
'''var GEO={idle:{w:612,h:46,r:999},as:{w:660,h:64,r:999},al:{w:700,h:150,r:40},trade:{w:720,h:236,r:40},res:{w:620,h:112,r:36}};
function vwIdle(){var m=Px.M.BTC;
 return '<div class="idleg"><span class="lv"><i></i>LIVE</span><span class="upt mono" data-r="upt">'+dur(Date.now()-Boot.since)+'</span></div>'
 +'<span class="pairwrap"><span class="psym mono">BTC</span><b class="ppx mono" data-r="px">'+fmtP(m.p)+'</b><span class="ppc mono '+(m.ch>=0?'up':'down')+'" data-r="pc">'+(m.ch>=0?'+':'')+m.ch.toFixed(1)+'%</span></span>'
 +'<span class="sess">'+sessDots()+'</span>'}
var Isl={el:$('#isl'),stg:$('#stg'),idMark:$('#punch .smk'),
 iw:new Spr(0),ih:new Spr(46),ir:new Spr(999),
 view:null,refs:{},idrefs:{},
 paint:function(){var st=this.el.style;
  st.width=Math.max(0,this.iw.v).toFixed(2)+'px';
  st.height=Math.max(0,this.ih.v).toFixed(2)+'px';
  st.borderRadius=Math.max(0,this.ir.v).toFixed(1)+'px'},
 bump:function(){if(!MOTION)return;this.el.classList.remove('bump');void this.el.offsetWidth;this.el.classList.add('bump')},
 setView:function(kind,html,g){
  var old=this.stg.querySelector('.view.on');
  var v=el('div','view on in '+kind,html);
  this.stg.appendChild(v);
  if(old){old.classList.remove('on','in');old.classList.add('out');setTimeout(function(){if(old.parentNode)old.parentNode.removeChild(old)},180)}
  var refs={};v.querySelectorAll('[data-r]').forEach(function(n){refs[n.dataset.r]=n});
  this.refs=refs;this.idrefs=refs;this.view=kind;
  var closing=g.h<this.ih.v;
  this.iw.to(g.w,closing?420:300,closing?34:24);
  this.ih.to(g.h,closing?420:300,closing?34:24);
  this.ir.to(g.r,closing?420:340,closing?34:30);
  Eng.wake()},
 setIdle:function(){this.setView('idle',vwIdle(),GEO.idle)}};''','js-island-arch')

# 17 · sync — idle is a state
rng("var curStage=null,curTrade=false;","else Isl.show('al',vwAl(a),GEO.al)}",
'''var curStage=null;
function sync(){
 var a=Stage.cur,tr=Trade.cur;
 var kind=a?('a'+a.size):(tr?(tr.status==='run'?'trade':'res'):'idle');
 if(kind===curStage)return;
 curStage=kind;
 if(kind==='idle'){Isl.setIdle();return}
 if(kind==='trade')Isl.setView('trade',vwTrade(tr),GEO.trade);
 else if(kind==='res')Isl.setView('res',vwRes(tr),GEO.res);
 else if(kind==='as')Isl.setView('as',vwAs(a),GEO.as);
 else Isl.setView('al',vwAl(a),GEO.al)}''','js-sync-idle')

# 18 · trade engine cleanups
rep('Isl.buildId(true);sync();Isl.bump();Mood.look();return this.cur','sync();Isl.bump();Mood.look();return this.cur','js-trade-open')
rep('self.cur=null;Isl.buildId(false);sync()},3200)','self.cur=null;sync()},3200)','js-trade-res')
rep("  if(Isl.idrefs&&Isl.idrefs.mini){var m=Isl.idrefs.mini;m.textContent=money(t.pnl);m.className='mini mono '+(t.pnl>=0?'up':'down')}\n",'','js-trade-mini')
rep("return SMK(26)+'<div class=\"rcol\">","return '<div class=\"rcol\">",'js-res-smk')

# 19 · boot + routes
rep("boot('island',function(){Isl.buildId(false);\n Isl.imc.innerHTML=SMK(24)+'<span class=\"lv s\"><i></i>LIVE</span>';\n Isl.el.classList.add('on');sync();Mood.blinkLoop()});",
    "boot('island',function(){Isl.setIdle();Isl.el.classList.add('on');Eng.wake();Mood.blinkLoop()});",'js-boot-island')
rep("if(!Isl.view)Isl.buildId(false)})});","if(curStage==='idle'||!curStage)Isl.setIdle()})});",'js-boot-fonts')
rep(" case 'cur':CUR=sanCur(d);if(Trade.cur){Isl.buildId(Trade.cur.status==='run');sync()}break;",
    " case 'cur':CUR=sanCur(d);curStage=null;sync();break;",'js-route-cur')
rep("if(Trade.cur){Isl.buildId(Trade.cur.status==='run');sync()}}});","curStage=null;sync()}}});",'js-panel-cur')

# 20 · Frame -> webToggle
rng("var Frame={g:LS.get('smile-live-frame')||{x:.60,y:.12,w:.32},",
"addEventListener('pointermove',mv);addEventListener('pointerup',up)})}};",
'''function webToggle(){var f=document.getElementById('webStage');
 if(f){f.parentNode.removeChild(f);document.body.classList.remove('mode-web');return}
 var w=P.get('web'),u=(w&&w!=='1')?w:'https://smile.co.ke';
 f=el('iframe');f.id='webStage';f.src=u;f.setAttribute('allow','autoplay; fullscreen');
 document.body.insertBefore(f,document.getElementById('stage'));
 document.body.classList.add('mode-web')}''','js-webtoggle')
rep("boot('frame',function(){Frame.init();addEventListener('resize',function(){Frame.apply()})});",
    "boot('web',function(){if(P.get('web'))webToggle()});",'js-boot-web')
rep("q('#ctlLabel').value=LBL;","",'js-panel-label-init')
rep("q('#ctlLabel').oninput=function(){LBL=this.value.slice(0,18)||'YOU';Frame.apply();bsend('label',LBL)};\n",'','js-panel-label')
rep("q('#ctlSlow').onclick=function(){Eng.speed=(Eng.speed===1)?.25:1;this.classList.toggle('on',Eng.speed!==1)};",
    "q('#ctlSlow').onclick=function(){Eng.speed=(Eng.speed===1)?.25:1;this.classList.toggle('on',Eng.speed!==1)};\n q('#ctlWeb').onclick=function(){webToggle()};",'js-panel-web')
rep("['Demo',function(){Demo.stop();Demo.start()}],","['Demo',function(){Demo.stop();Demo.start()}],\n ['Web',function(){webToggle()}],",'js-csl-web')

# 21 · demo retimed (proper emoji escape this time — python, not javascript)
rng("[1200,function(){Stage.push({type:'follow',name:'Maya'})}],",
"[34000,function(){Goal.set({cur:Goal.d.tgt})}]];",
'''[1200,function(){Stage.push({type:'follow',name:'Maya'})}],
 [4200,function(){News.push({text:'FED HOLDS RATES \u00b7 EQUITIES RIP HIGHER',level:'breaking'})}],
 [6500,function(){Stage.push({type:'chat',name:'Kofi_A',amount:25,message:'first time catching the stream live \u2014 that BTC breakout call was clean \U0001F525'})}],
 [8600,function(){Drawer.show({plat:'yt',name:'Zawadi',handle:'zawadi_fx',msg:'NBO open soon \u2014 watching EURUSD closely'})}],
 [13800,function(){Stage.push({type:'sub',name:'jules.eth'})}],
 [15100,function(){Stage.push({type:'sub',name:'Riya'})}],
 [16800,function(){Trade.open({market:'BTC/USDT',side:'long',tp:+(Px.val('BTC')*1.002).toFixed(1)})}],
 [19800,function(){News.push({text:'S&P 500 PRINTS FRESH RECORD HIGH'})}],
 [22800,function(){Trade.close('win')}],
 [26800,function(){Stage.push({type:'raid',name:'TraderTV_Fans',count:214})}],
 [30500,function(){Stage.push({type:'announce',name:'SMILE',sub:'FRIDAY \u00b7 8PM EAT',message:'Merch restock + live portfolio review this Friday. Set a reminder.'})}],
 [34000,function(){Goal.set({cur:Goal.d.tgt})}]];''','js-demo-retimed')

# ═══ ATOMIC WRITE — validate BEFORE touching your file, then swap ═══
if s!=orig:
    try:
        data=s.encode('utf-8')
    except UnicodeEncodeError as e:
        print('\U0001F4A5 ENCODE FAIL \u2014 your file was NOT touched: '+str(e));sys.exit(1)
    tmp=P+'.tmp'
    with io.open(tmp,'wb') as f:f.write(data)
    os.replace(tmp,P)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

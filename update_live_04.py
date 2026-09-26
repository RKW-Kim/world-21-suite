import io,os,sys
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P):print('❌ overlay/live.html not found');sys.exit(1)
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

# ═══ 1 · ISLAND CSS — fixed state geometry, sheen, glow ═══
NEW_ISL="""/* island \u2014 fixed state geometry (states have designed sizes, never measured mid-morph) */
#islw{position:absolute;top:11px;left:50%;transform:translateX(-50%);z-index:60;display:flex;align-items:flex-start;pointer-events:none}
#islw::after{content:"";position:absolute;left:50%;top:40px;width:560px;height:230px;transform:translateX(-50%);z-index:-1;background:radial-gradient(closest-side,rgba(var(--acc-rgb),.09),transparent 72%);filter:blur(6px);pointer-events:none;animation:islglow 7s ease-in-out infinite}
@keyframes islglow{0%,100%{opacity:.45}50%{opacity:1}}
#isl{position:relative;overflow:hidden;border-radius:999px;opacity:0;transform:translateY(-8px);background:linear-gradient(165deg,#16161B 0%,#060608 55%,#000 100%);box-shadow:0 24px 50px -16px rgba(0,0,0,.75),0 4px 16px rgba(0,0,0,.35);transition:opacity .5s ease,transform .6s var(--spring)}
#isl.on{opacity:1;transform:none}
body.debug #isl{pointer-events:auto;cursor:pointer}
#isl::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;z-index:4;pointer-events:none;background:linear-gradient(180deg,rgba(255,255,255,.30),rgba(255,255,255,.07) 30%,rgba(255,255,255,.015) 55%,rgba(255,255,255,.10));-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);mask-composite:exclude}
#isl::after{content:"";position:absolute;top:0;left:-70%;width:42%;height:100%;z-index:3;pointer-events:none;background:linear-gradient(105deg,transparent,rgba(255,255,255,.055),transparent);transform:skewX(-18deg);animation:sheen 9s ease-in-out infinite}
@keyframes sheen{0%,60%{left:-70%}85%,100%{left:135%}}
#isl.bump{animation:bump .34s var(--spring)}
@keyframes bump{0%{transform:scale(1)}35%{transform:scale(1.02)}100%{transform:scale(1)}}
#isl.liquid{background:linear-gradient(168deg,#FFD84E 0%,#FFC107 48%,#EDA400 100%)}
#isl.liquid::before{background:linear-gradient(180deg,rgba(255,255,255,.75),rgba(255,255,255,.25) 30%,rgba(255,255,255,.08) 60%,rgba(255,255,255,.4))}
#isl.liquid::after{display:none}
.bubs{position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden;border-radius:inherit;opacity:0;transition:opacity .6s ease}
#isl.bub .bubs{opacity:1}
.bubs i{position:absolute;bottom:-12px;border-radius:50%;background:rgba(255,255,255,.10);animation:bub 4.8s ease-in infinite}
#isl.liquid .bubs i{background:rgba(255,255,255,.38)}
@keyframes bub{0%{transform:translateY(0) scale(.5);opacity:0}12%{opacity:.55}100%{transform:translateY(-150px) scale(1.15);opacity:0}}
#idb{position:relative;height:100%;flex:none;z-index:2}
#ifull,#imicro{position:absolute;left:0;top:0;bottom:0;display:flex;align-items:center;width:max-content;transition:opacity .3s ease,transform .3s ease}
#ifull{gap:12px;padding:0 20px;height:46px}
#imicro{flex-direction:column;justify-content:center;gap:5px;padding:0 12px;opacity:0;transform:scale(.9)}
#isl.tall #ifull{opacity:0;transform:scale(.9)}
#isl.tall #imicro{opacity:1;transform:none}
.lv{display:flex;align-items:center;gap:7px;font-family:var(--fd);font-weight:700;font-size:10.5px;letter-spacing:.18em;color:var(--live)}
.lv i{width:7px;height:7px;border-radius:50%;background:currentColor;animation:softpulse 1.6s infinite}
.lv.s{font-size:8.5px;gap:4px}
.lv.s i{width:5px;height:5px}
@keyframes softpulse{0%,100%{opacity:1}50%{opacity:.3}}
.upt{font-size:12px;color:rgba(255,255,255,.75)}
.ihair{width:1px;height:14px;background:rgba(255,255,255,.14);flex:none}
.pairwrap{display:flex;align-items:baseline;gap:8px}
.psym{font-size:10.5px;color:rgba(255,255,255,.4);letter-spacing:.12em}
.ppx{font-size:13px;font-weight:700;color:#fff}
.roll{animation:roll .5s var(--ease)}
@keyframes roll{0%{transform:translateY(55%);opacity:0;filter:blur(3px)}100%{transform:none;opacity:1;filter:none}}
.ppc{font-size:11px;font-weight:700}
.sess{display:flex;gap:8px;align-items:center}
.sdt{display:flex;gap:4px;align-items:center;font-family:var(--fm);font-size:9.5px;letter-spacing:.14em;color:rgba(255,255,255,.4)}
.sdt i{width:5px;height:5px;border-radius:50%;background:rgba(255,255,255,.18)}
.sdt.open{color:rgba(255,255,255,.9)}
.sdt.open i{background:var(--up);box-shadow:0 0 6px var(--up)}
.miniwrap{display:flex;align-items:center;gap:9px}
.miniwrap .mk2{font-family:var(--fd);font-weight:700;font-size:12px;color:#fff}
.side{font-size:8.5px;font-weight:800;letter-spacing:.14em;padding:3px 8px;border-radius:999px;flex:none}
.side.long{color:var(--up);background:rgba(14,203,129,.13);box-shadow:inset 0 0 0 1px rgba(14,203,129,.4)}
.side.short{color:var(--down);background:rgba(246,70,93,.13);box-shadow:inset 0 0 0 1px rgba(246,70,93,.4)}
.mini{font-size:12.5px;font-weight:700}
#isl.liquid #ifull,#isl.liquid #imicro{color:var(--on)}
#isl.liquid .lv{color:var(--on)}
#isl.liquid .upt,#isl.liquid .psym,#isl.liquid .ppc,#isl.liquid .sdt{color:rgba(10,10,10,.6)}
#isl.liquid .ppx,#isl.liquid .mk2,#isl.liquid .mini{color:var(--on)}
#isl.liquid .ihair{background:rgba(0,0,0,.2)}
#isl.liquid .smk .fc{fill:var(--on)}#isl.liquid .smk .fe{fill:var(--acc)}#isl.liquid .smk .fm{stroke:var(--acc)}
#stg{position:relative;height:100%;flex:1 1 auto;min-width:0;z-index:2}
#stg::before{content:"";position:absolute;left:-6px;top:26%;bottom:26%;width:1px;background:rgba(255,255,255,.10);opacity:0;transition:opacity .4s ease}
#stg.open::before{opacity:.6}
#isl.liquid #stg::before{background:rgba(0,0,0,.25)}
.view{position:absolute;left:0;top:0;bottom:0;width:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;opacity:0;pointer-events:none}
.view.on{opacity:1}
.view.in{animation:vIn .45s var(--ease) both}
.view.in>*{animation:chIn .5s var(--ease) both;animation-delay:.1s}
.view.in>*:nth-child(2){animation-delay:.15s}
.view.in>*:nth-child(3){animation-delay:.2s}
.view.in>*:nth-child(4){animation-delay:.25s}
.view.out{animation:vOut .14s ease forwards}
@keyframes vIn{0%{opacity:0;transform:scale(.94) translateY(5px);filter:blur(8px)}100%{opacity:1;transform:none;filter:blur(0)}}
@keyframes vOut{to{opacity:0;transform:scale(.965);filter:blur(6px)}}
@keyframes chIn{0%{opacity:0;transform:translateY(7px)}100%{opacity:1;transform:none}}
.view.as{gap:13px;padding:0 20px}
.aico{width:42px;height:42px;flex:none;border-radius:14px;display:grid;place-items:center;color:var(--acc);background:rgba(var(--acc-rgb),.13);box-shadow:inset 0 0 0 1px rgba(var(--acc-rgb),.35),inset 0 1px 0 rgba(255,255,255,.12);animation:pop .5s var(--spring)}
@keyframes pop{0%{transform:scale(.4);opacity:0}60%{transform:scale(1.1)}100%{transform:scale(1)}}
.atx{display:flex;flex-direction:column;gap:3px;min-width:0}
.atx b{font-family:var(--fd);font-weight:700;font-size:16px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px}
.atx span{font-size:12.5px;color:rgba(255,255,255,.6);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.aamt{flex:none;font-family:var(--fd);font-weight:700;font-size:14px;color:var(--acc);background:rgba(var(--acc-rgb),.12);box-shadow:inset 0 0 0 1px rgba(var(--acc-rgb),.38);border-radius:999px;padding:7px 14px}
#isl.liquid .aamt{color:var(--on);background:rgba(0,0,0,.14);box-shadow:inset 0 0 0 1px rgba(0,0,0,.22)}
.view.al{flex-direction:column;justify-content:center;gap:10px;padding:12px 22px}
.ahead{display:flex;align-items:center;gap:13px;min-width:0;width:100%}
.amsg{font-size:13.5px;line-height:1.5;color:rgba(255,255,255,.78);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;width:100%}
#isl.liquid .atx b{color:var(--on)}
#isl.liquid .atx span,#isl.liquid .amsg{color:rgba(10,10,10,.66)}
.view.trade{flex-direction:column;justify-content:center;gap:13px;padding:14px 24px}
.trow1{display:flex;align-items:center;gap:10px;width:100%}
.tdot{width:8px;height:8px;border-radius:50%;background:var(--acc);box-shadow:0 0 8px rgba(255,193,7,.7);animation:softpulse 1.8s infinite;flex:none}
.tmkt{font-family:var(--fd);font-weight:700;font-size:17px;color:#fff}
.tside{font-size:9px;font-weight:800;letter-spacing:.16em;padding:4px 10px;border-radius:999px;flex:none}
.tside.long{color:var(--up);background:rgba(14,203,129,.15);box-shadow:inset 0 0 0 1px rgba(14,203,129,.4)}
.tside.short{color:var(--down);background:rgba(246,70,93,.15);box-shadow:inset 0 0 0 1px rgba(246,70,93,.4)}
.ttime{margin-left:auto;font-size:11px;color:rgba(255,255,255,.4);letter-spacing:.08em}
.trow2{display:flex;align-items:center;gap:22px;min-height:56px;width:100%}
.tpnl{font-family:var(--fm);font-weight:700;font-size:30px;letter-spacing:-.02em;line-height:1}
.tsub{display:flex;align-items:center;gap:8px;font-size:11px;color:rgba(255,255,255,.55);margin-top:7px}
.tsub b{color:rgba(255,255,255,.8);font-weight:600}
.tstats{margin-left:auto;display:flex}
.tcell{display:flex;flex-direction:column;gap:4px;padding:2px 16px;text-align:right}
.tcell + .tcell{border-left:1px solid rgba(255,255,255,.05)}
.tcell label{font-size:8.5px;font-weight:700;letter-spacing:.22em;color:rgba(255,255,255,.42)}
.tcell b{font-size:13.5px;font-weight:600;color:#fff}
.tlad{display:flex;align-items:center;gap:12px;width:100%}
.tlab{font-size:9px;font-weight:600;letter-spacing:.14em;color:rgba(255,255,255,.45);line-height:1.3}
.tlab b{display:block;font-size:11px;color:rgba(255,255,255,.75);letter-spacing:0}
.lbar{position:relative;flex:1;height:5px;border-radius:999px;background:linear-gradient(90deg,rgba(246,70,93,.45),rgba(255,255,255,.1) 50%,rgba(14,203,129,.45))}
.ldot{position:absolute;top:50%;left:50%;width:11px;height:11px;border-radius:50%;background:#fff;transform:translate(-50%,-50%);box-shadow:0 0 0 3px rgba(0,0,0,.55),0 0 12px rgba(255,255,255,.65);transition:left .7s var(--ease)}
.lbear,.lbull{position:absolute;top:50%;transform:translateY(-50%);display:flex}
.lbear{left:-2px;color:var(--down)}
.lbull{right:-2px;color:var(--up)}
.lbear svg,.lbull svg{width:13px;height:13px}
#isl.liquid .tmkt,#isl.liquid .tpnl,#isl.liquid .tcell b,#isl.liquid .tlab b{color:var(--on)}
#isl.liquid .tsub,#isl.liquid .tlab,#isl.liquid .ttime,#isl.liquid .tcell label{color:rgba(10,10,10,.6)}
.view.res{gap:16px;padding:0 24px}
.rcol{display:flex;flex-direction:column;gap:4px}
.rt{font-family:var(--fd);font-weight:700;font-size:11px;letter-spacing:.26em;color:rgba(255,255,255,.55)}
.rv{font-family:var(--fm);font-weight:700;font-size:28px;letter-spacing:-.02em;color:#fff}
.rbtn{font-family:var(--fm);font-size:12px;font-weight:600;color:rgba(255,255,255,.7);border-radius:999px;padding:6px 13px;background:rgba(0,0,0,.14);box-shadow:inset 0 0 0 1px rgba(0,0,0,.18)}
.view.res.loss .rt,.view.res.loss .rv{color:var(--down)}
#isl.liquid .rt,#isl.liquid .rv{color:var(--on)}
#isl.liquid .rbtn{color:var(--on);background:rgba(255,255,255,.28);box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}
@media (max-width:820px){#islw{transform:translateX(-50%) scale(.72);transform-origin:top center}}
"""
rng('/* island */','/* mascot */',NEW_ISL,'css-island-fixed')

# ═══ 2 · NEWS — floating banner, own silhouette ═══
NEW_NEWS="""/* news \u2014 floating banner (its own silhouette, never a stacked bar) */
#news{position:absolute;left:50%;bottom:88px;transform:translateX(-50%) translateY(20px) scale(.96);max-width:min(880px,86vw);height:54px;z-index:41;display:flex;align-items:center;gap:14px;padding:0 15px 0 11px;border-radius:999px;background:rgba(9,9,11,.93);backdrop-filter:blur(18px) saturate(1.5);box-shadow:0 18px 44px rgba(0,0,0,.5),0 2px 8px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.09);opacity:0;transition:transform .55s var(--spring),opacity .3s ease;pointer-events:none;overflow:hidden}
#news.on{opacity:1;transform:translateX(-50%)}
#news.breaking{background:rgba(34,10,15,.94);box-shadow:0 18px 44px rgba(0,0,0,.55),0 0 46px rgba(246,70,93,.30),inset 0 1px 0 rgba(255,255,255,.09)}
.ntag{flex:none;font-family:var(--fd);font-weight:700;font-size:10px;letter-spacing:.22em;padding:8px 15px;color:var(--on);background:var(--acc);border-radius:999px}
#news.breaking .ntag{background:var(--down);color:#fff;animation:softpulse 1.2s infinite}
#newsTxt{font-family:var(--fd);font-weight:600;font-size:15.5px;letter-spacing:.03em;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#news.breaking #newsTxt{color:#FFD7DC}
#newsTime{margin-left:auto;flex:none;font-size:10px;letter-spacing:.16em;color:var(--fnt)}
body.hide-news #news{display:none}
body.hide-footer #news{bottom:16px}
/* footer \u2014 pill bar */"""
rng('/* news rail','/* footer \u2014 pill bar */',NEW_NEWS,'css-news-banner')

# ═══ 3 · TYPE SCALE — broadcast legibility ═══
rep('.mst b{font-family:var(--fd);font-weight:700;font-size:13px;','.mst b{font-family:var(--fd);font-weight:700;font-size:14px;','type-mast')
rep('#clkDate{font-family:var(--fm);font-size:10px;','#clkDate{font-family:var(--fm);font-size:11px;','type-date')
rep('.clktz{font-size:10.5px;','.clktz{font-size:11.5px;','type-clk')
rep('#goalVal{font-family:var(--fm);font-size:11.5px;','#goalVal{font-family:var(--fm);font-size:12.5px;','type-goalval')
rep('.glabel{font-family:var(--fd);font-weight:700;font-size:9px;','.glabel{font-family:var(--fd);font-weight:700;font-size:9.5px;','type-glabel')
rep('#nextTxt{font-family:var(--fm);font-size:10px;','#nextTxt{font-family:var(--fm);font-size:11px;','type-next')
rep('.nlab{font-family:var(--fm);font-size:9px;','.nlab{font-family:var(--fm);font-size:10px;','type-nlab')
rep('.murl{font-family:var(--fm);font-size:8.5px;','.murl{font-family:var(--fm);font-size:9px;','type-murl')
rep('.q b{font-family:var(--fd);font-weight:700;font-size:11.5px;','.q b{font-family:var(--fd);font-weight:700;font-size:12.5px;','type-qsym')
rep('.qp{font-size:11.5px;','.qp{font-size:12.5px;','type-qpx')
rep('.qc{font-size:10.5px;','.qc{font-size:11.5px;','type-qc')
rep('.flogo svg{height:24px;','.flogo svg{height:26px;','type-flogo')
rep('.duser{font-family:var(--fd);font-weight:700;font-size:12px;','.duser{font-family:var(--fd);font-weight:700;font-size:13px;','type-duser')
rep('.dmsg{font-size:12.5px;','.dmsg{font-size:13.5px;','type-dmsg')
rep('font-size:10.5px;letter-spacing:.14em','font-size:11.5px;letter-spacing:.12em','type-framelabel')

# ═══ 4 · JS — engine registry fix (array, not target-keyed) ═══
rng('var Eng={S:{},on:false,last:0,speed:1,','paint:function(){Isl.paint()}};',
"""var Eng={A:[],on:false,last:0,speed:1,
 add:function(s){if(Eng.A.indexOf(s)<0)Eng.A.push(s);Eng.wake()},
 wake:function(){if(Eng.on)return;Eng.on=true;Eng.last=performance.now();requestAnimationFrame(function(t){Eng.loop(t)})},
 loop:function(now){var dt=clamp((now-Eng.last)/1000,.001,.05)*Eng.speed;Eng.last=now;var any=false;
  for(var i=Eng.A.length-1;i>=0;i--){if(Eng.A[i].step(dt))any=true;else Eng.A.splice(i,1)}
  Isl.paint();
  if(Stage.cur){Stage.age+=dt*1000;if(Stage.age>=Stage.cur.dwell)Stage.end()}
  if(any||Stage.cur)Eng.wake();else Eng.on=false}};""",'js-eng-array')
rep('this.vel=0;Eng.paint();return}','this.vel=0;Isl.paint();return}','js-spr-paint')

# ═══ 5 · JS — island: fixed geometry table, measurement only at rest ═══
rng('var Isl={el:$(\'#isl\'),',"if(!self.view)self.stg.innerHTML=''},430)}};",
"""var GEO={as:{w:640,h:64,r:999},al:{w:700,h:150,r:38},trade:{w:720,h:236,r:40},res:{w:600,h:112,r:32}};
var IDW=150;
var Isl={el:$('#isl'),idb:$('#idb'),ifl:$('#ifull'),imc:$('#imicro'),stg:$('#stg'),
 iw:new Spr(0),ih:new Spr(46),ir:new Spr(999),
 view:null,refs:{},idrefs:{},idMark:null,closeT:0,
 paint:function(){var st=this.el.style;
  st.width=Math.max(0,this.iw.v).toFixed(2)+'px';
  st.height=Math.max(0,this.ih.v).toFixed(2)+'px';
  st.borderRadius=Math.max(0,this.ir.v).toFixed(1)+'px';
  this.el.classList.toggle('tall',this.ih.v>60);
  this.stg.classList.toggle('open',this.ih.v>60)},
 bump:function(){if(!MOTION)return;this.el.classList.remove('bump');void this.el.offsetWidth;this.el.classList.add('bump')},
 buildId:function(tradeLive){
  this.ifl.innerHTML=SMK(22)
   +'<span class="lv"><i></i>LIVE</span>'
   +'<span class="upt mono" data-r="upt">'+dur(Date.now()-Boot.since)+'</span>'
   +'<span class="ihair"></span>'
   +(tradeLive
     ?'<span class="miniwrap"><b class="mk2">'+esc(Trade.cur.market)+'</b><span class="side '+Trade.cur.side+'">'+Trade.cur.side.toUpperCase()+'</span><b class="mini mono '+(Trade.cur.pnl>=0?'up':'down')+'" data-r="mini">'+money(Trade.cur.pnl)+'</b></span>'
     :'<span class="pairwrap"><span class="psym mono">BTC</span><b class="ppx mono" data-r="px">'+fmtP(Px.M.BTC.p)+'</b><span class="ppc mono '+(Px.M.BTC.ch>=0?'up':'down')+'" data-r="pc">'+(Px.M.BTC.ch>=0?'+':'')+Px.M.BTC.ch.toFixed(1)+'%</span></span>')
   +'<span class="ihair"></span>'
   +'<span class="sess">'+sessDots()+'</span>';
  var refs={};this.ifl.querySelectorAll('[data-r]').forEach(function(n){refs[n.dataset.r]=n});
  this.idrefs=refs;this.idMark=this.ifl.querySelector('.smk');
  if(!this.view){var w=this.ifl.offsetWidth;
   this.idb.style.width=w+'px';
   this.iw.to(w,300,26);this.ih.to(46,300,27);this.ir.to(999,340,30)}},
 show:function(kind,html,g){
  clearTimeout(this.closeT);
  var old=this.stg.querySelector('.view.on');
  var v=el('div','view on in '+kind,html);
  this.stg.appendChild(v);
  if(old){old.classList.remove('on','in');old.classList.add('out');setTimeout(function(){if(old.parentNode)old.parentNode.removeChild(old)},180)}
  var refs={};v.querySelectorAll('[data-r]').forEach(function(n){refs[n.dataset.r]=n});
  this.refs=refs;this.view=kind;
  this.idb.style.width=IDW+'px';
  var closing=g.h<this.ih.v;
  this.iw.to(g.w,closing?420:300,closing?34:24);
  this.ih.to(g.h,closing?420:300,closing?34:24);
  this.ir.to(g.r,closing?420:340,closing?34:30);
  Eng.wake()},
 close:function(){this.view=null;this.refs={};
  var w=this.ifl.offsetWidth;
  this.idb.style.width=w+'px';
  this.iw.to(w,420,34);this.ih.to(46,420,34);this.ir.to(999,420,34);
  var self=this;this.closeT=setTimeout(function(){if(!self.view)self.stg.innerHTML=''},430)}};""",'js-island-fixed')

# ═══ 6 · JS — sync passes the geometry table ═══
rng('var curStage=null,curTrade=false;',"else Isl.show('al',vwAl(a),{h:96,r:40})}",
"""var curStage=null,curTrade=false;
function sync(){
 var a=Stage.cur,tr=Trade.cur;
 var tradeLive=!!(tr&&tr.status==='run');
 if(tradeLive!==curTrade){curTrade=tradeLive;Isl.buildId(tradeLive)}
 var kind=!a?(tr?(tr.status==='run'?'trade':'res'):null):('a'+a.size);
 if(kind===curStage)return;
 curStage=kind;
 if(!kind){Isl.close();return}
 if(kind==='trade')Isl.show('trade',vwTrade(tr),GEO.trade);
 else if(kind==='res')Isl.show('res',vwRes(tr),GEO.res);
 else if(kind==='as')Isl.show('as',vwAs(a),GEO.as);
 else Isl.show('al',vwAl(a),GEO.al)}""",'js-sync-geo')

# ═══ 7 · boot blocks — renamed springs ═══
rng("boot('island',function(){Isl.buildId(false);","Mood.blinkLoop()});",
"""boot('island',function(){Isl.buildId(false);
 Isl.imc.innerHTML=SMK(24)+'<span class="lv s"><i></i>LIVE</span>';
 Isl.el.classList.add('on');sync();Mood.blinkLoop()});""",'js-boot-island')
rng("boot('fonts',function(){","Isl.ifl.offsetWidth,300,26)})});",
"""boot('fonts',function(){if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){
 if(!Isl.view)Isl.buildId(false)})});""",'js-boot-fonts')

# ═══ 8 · global scale param (?scale=1.15) ═══
rep("if(P.get('debug')==='1')document.body.classList.add('debug');",
"if(P.get('debug')==='1')document.body.classList.add('debug');\n"
"var Z=clamp(parseFloat(P.get('scale'))||1,.8,1.4);if(Z!==1)document.body.style.zoom=Z;",'param-scale')

if s!=orig:io.open(P,'w',encoding='utf-8').write(s)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

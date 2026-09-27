import io,os,sys
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P):print('❌ overlay/live.html not found');sys.exit(1)
s=io.open(P,encoding='utf-8').read();orig=s
applied,skipped=[],[]
def rep(a,b,tag):
    global s
    if a in s:s=s.replace(a,b,1);applied.append(tag)
    else:skipped.append(tag)

# 1 · state vars (sanitized currency + label/next/speed/control)
rep("var CUR=P.get('cur')||'$';",
"var sanCur=function(s){return String(s==null?'':s).replace(/[^A-Za-z0-9 £€$¥]/g,'').slice(0,5)||'$'};\n"
"var CUR=sanCur(P.get('cur')||'$');\n"
"var LBL=String(P.get('label')||'YOU').slice(0,18);\n"
"var NXT=String(P.get('next')||'MARKET WAKE UP · 08:00 EAT').slice(0,64);\n"
"var SPD=clamp(parseFloat(P.get('speed'))||52,10,200);\n"
"var CTL=P.get('control')==='1';",'state-vars')

# 2 · control body class
rep("if(P.get('console')==='1'||DEMO)document.body.classList.add('console');",
"if(P.get('console')==='1'||DEMO)document.body.classList.add('console');\n"
"if(CTL){document.body.classList.add('control');if(P.get('clean')!=='1')document.body.classList.add('stage')}",'ctl-class')

# 3 · swap param reads for live vars
rep("var l=$('#frameLabel');if(l)l.innerHTML='<i></i>'+esc(P.get('label')||'YOU')}",
    "var l=$('#frameLabel');if(l)l.innerHTML='<i></i>'+esc(LBL)}",'frame-label-var')
rep("$('#nextTxt').textContent=P.get('next')||'MARKET WAKE UP · 08:00 EAT';",
    "$('#nextTxt').textContent=NXT;",'next-var')
rep("Crawl.x-=(parseFloat(P.get('speed'))||52)*dt;",
    "Crawl.x-=SPD*dt;",'speed-var')

# 4 · transport routes for panel commands
rep(" case 'dismiss':API.dismiss();break}}",
" case 'dismiss':API.dismiss();break;\n"
" case 'ui':if(d&&d.cls)document.body.classList.toggle(d.cls,!d.on);break;\n"
" case 'cur':CUR=sanCur(d);if(Trade.cur){Isl.buildId(Trade.cur.status==='run');sync()}break;\n"
" case 'label':LBL=String(d||'YOU').slice(0,18);Frame.apply();break;\n"
" case 'next':NXT=String(d||'').slice(0,64);var nx=$('#nextTxt');if(nx)nx.textContent=NXT;break;\n"
" case 'speed':SPD=clamp(parseFloat(d)||52,10,200);break}}",'routes-panel')

# 5 · panel CSS
rep("/* motion safety */",
"/* control panel */\n"
"#ctl{position:fixed;right:14px;top:14px;bottom:14px;width:332px;z-index:400;display:none;flex-direction:column;gap:10px;overflow-y:auto;overflow-x:hidden;padding-right:2px}\n"
"body.control #ctl{display:flex}\n"
"body.control #csl{display:none!important}\n"
"body.hide-isl #islw{opacity:0;pointer-events:none}\n"
"#ctl::-webkit-scrollbar{width:8px}\n"
"#ctl::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:99px}\n"
".ccard{background:rgba(14,14,17,.94);border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:13px 14px;backdrop-filter:blur(18px);flex:none}\n"
".ccard h5{font-family:var(--fm);font-size:9px;letter-spacing:.24em;color:var(--fnt);text-transform:uppercase;margin-bottom:10px}\n"
".crow{display:flex;align-items:center;gap:8px;margin-bottom:8px}\n"
".crow:last-child{margin-bottom:0}\n"
".crow label{font-size:11px;color:var(--mut);font-weight:600;min-width:52px;flex:none}\n"
".crow input[type=text],.crow input[type=number]{flex:1;min-width:0;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:var(--fg);padding:7px 9px;font-size:12px;outline:none}\n"
".crow input:focus{border-color:rgba(255,193,7,.5)}\n"
".cbtn{height:29px;padding:0 11px;border-radius:8px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.06);color:rgba(255,255,255,.85);font-family:var(--fm);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;cursor:pointer;flex:none}\n"
".cbtn:hover{border-color:rgba(255,193,7,.55);color:var(--acc)}\n"
".cbtn.on{background:var(--acc);color:var(--on);border-color:var(--acc)}\n"
".cbtns{display:flex;flex-wrap:wrap;gap:6px}\n"
"/* motion safety */",'css-panel')

# 6 · panel HTML
rep('<div id="csl"></div>',
'<aside id="ctl">\n'
'  <div class="ccard"><h5>SMILE · Control</h5>\n'
'    <div class="cbtns"><button class="cbtn" id="ctlCopy">Copy OBS URL</button><button class="cbtn" id="ctlDemo">Run Demo</button><button class="cbtn" id="ctlSlow">1/4x</button></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>Layers</h5>\n'
'    <div class="cbtns"><button class="cbtn on" data-layer="header">Header</button><button class="cbtn on" data-layer="isl">Island</button><button class="cbtn on" data-layer="footer">Footer</button><button class="cbtn on" data-layer="news">News</button><button class="cbtn on" data-layer="frame">Frame</button></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>Show</h5>\n'
'    <div class="crow"><label>Label</label><input type="text" id="ctlLabel" maxlength="18"></div>\n'
'    <div class="crow"><label>Up Next</label><input type="text" id="ctlNext" maxlength="64"></div>\n'
'    <div class="crow"><label>Money</label><div class="cbtns" id="ctlCur"><button class="cbtn on">$</button><button class="cbtn">£</button><button class="cbtn">€</button><button class="cbtn">KSh</button></div></div>\n'
'    <div class="crow"><label>Crawl</label><input type="range" id="ctlSpeed" min="20" max="120" value="52" style="flex:1;accent-color:var(--acc)"><span class="mono" id="ctlSpeedV" style="font-size:10px;color:var(--mut);min-width:22px;text-align:right">52</span></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>Goal</h5>\n'
'    <div class="crow"><label>Title</label><input type="text" id="ctlGL" maxlength="18"></div>\n'
'    <div class="crow"><label>Cur</label><input type="number" id="ctlGC"><label>Target</label><input type="number" id="ctlGT"></div>\n'
'    <div class="cbtns" style="margin-top:8px"><button class="cbtn" id="ctlGSet">Set Goal</button><button class="cbtn" id="ctlGHit">Hit 100%</button></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>Fire · Alerts</h5>\n'
'    <div class="cbtns"><button class="cbtn" data-ev="follow">Follow</button><button class="cbtn" data-ev="sub">Sub</button><button class="cbtn" data-ev="thanks">Thanks</button><button class="cbtn" data-ev="chat">Super Chat</button><button class="cbtn" data-ev="raid">Raid</button><button class="cbtn" data-ev="announce">Announce</button></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>Fire · Trade</h5>\n'
'    <div class="cbtns"><button class="cbtn" data-t="open">Open</button><button class="cbtn" data-t="win">Hit TP</button><button class="cbtn" data-t="loss">Hit SL</button><button class="cbtn" data-t="flat">Flatten</button></div>\n'
'  </div>\n'
'  <div class="ccard"><h5>News Rail</h5>\n'
'    <div class="crow"><input type="text" id="ctlNews" maxlength="90" placeholder="HEADLINE TEXT" style="width:100%"></div>\n'
'    <div class="cbtns" style="margin-top:8px"><button class="cbtn" id="ctlNewsGo">Push News</button><button class="cbtn" id="ctlNewsBrk">Push Breaking</button></div>\n'
'  </div>\n'
'</aside>\n'
'<div id="csl"></div>','html-panel')

# 7 · panel wiring
rep("boot('transport',function(){StatePoll.start()});",
"boot('panel',function(){if(!CTL)return;\n"
" var q=function(s){return $(s)};\n"
" q('#ctlGL').value=Goal.d.label;q('#ctlGC').value=Goal.d.cur;q('#ctlGT').value=Goal.d.tgt;\n"
" q('#ctlLabel').value=LBL;q('#ctlNext').value=NXT;\n"
" q('#ctlCopy').onclick=function(){var u=location.origin+location.pathname+'?clean=1';\n"
"  var b=this;if(navigator.clipboard)navigator.clipboard.writeText(u);\n"
"  b.textContent='COPIED';setTimeout(function(){b.textContent='Copy OBS URL'},1200)};\n"
" q('#ctlDemo').onclick=function(){Demo.stop();Demo.start()};\n"
" q('#ctlSlow').onclick=function(){Eng.speed=(Eng.speed===1)?.25:1;this.classList.toggle('on',Eng.speed!==1)};\n"
" document.querySelectorAll('#ctl [data-layer]').forEach(function(b){\n"
"  b.onclick=function(){var ly=b.dataset.layer,vis=!b.classList.contains('on');\n"
"   b.classList.toggle('on',vis);\n"
"   document.body.classList.toggle('hide-'+ly,!vis);\n"
"   bsend('ui',{cls:'hide-'+ly,on:vis})}});\n"
" q('#ctlLabel').oninput=function(){LBL=this.value.slice(0,18)||'YOU';Frame.apply();bsend('label',LBL)};\n"
" q('#ctlNext').oninput=function(){NXT=this.value.slice(0,64);var n=$('#nextTxt');if(n)n.textContent=NXT;bsend('next',NXT)};\n"
" document.querySelectorAll('#ctlCur .cbtn').forEach(function(b){\n"
"  b.onclick=function(){document.querySelectorAll('#ctlCur .cbtn').forEach(function(x){x.classList.remove('on')});\n"
"   b.classList.add('on');CUR=sanCur(b.textContent);bsend('cur',CUR);\n"
"   if(Trade.cur){Isl.buildId(Trade.cur.status==='run');sync()}}});\n"
" q('#ctlSpeed').oninput=function(){SPD=clamp(parseFloat(this.value)||52,10,200);q('#ctlSpeedV').textContent=SPD;bsend('speed',SPD)};\n"
" q('#ctlGSet').onclick=function(){var g={label:q('#ctlGL').value.slice(0,18)||'SUB GOAL',cur:+q('#ctlGC').value||0,tgt:+q('#ctlGT').value||1};\n"
"  Goal.set(g);bsend('goal',g)};\n"
" q('#ctlGHit').onclick=function(){var g={cur:Goal.d.tgt};Goal.set(g);bsend('goal',g)};\n"
" var EV={follow:{type:'follow',name:'Maya'},sub:{type:'sub',name:'jules.eth'},\n"
"  thanks:{type:'thanks',name:'Kofi_A',amount:5},\n"
"  chat:{type:'chat',name:'Riya',amount:25,message:'that breakout call was clean'},\n"
"  raid:{type:'raid',name:'TTV_Fans',count:214},\n"
"  announce:{type:'announce',name:'SMILE',sub:'NOTICE',message:'Test announcement from control.'}};\n"
" document.querySelectorAll('#ctl [data-ev]').forEach(function(b){\n"
"  b.onclick=function(){var e=EV[b.dataset.ev];API.alert(e);bsend('alert',e)}});\n"
" document.querySelectorAll('#ctl [data-t]').forEach(function(b){\n"
"  b.onclick=function(){var a=b.dataset.t;\n"
"   if(a==='open'){var d={market:'BTC/USDT',side:'long'};API.trade(d);bsend('trade',d)}\n"
"   else if(a==='flat'){API.flatten();bsend('flatten')}\n"
"   else{API.close(a);bsend('close',a)}}});\n"
" q('#ctlNewsGo').onclick=function(){var t=q('#ctlNews').value.trim();if(!t)return;\n"
"  var o={text:t};API.news(o);bsend('news',o)};\n"
" q('#ctlNewsBrk').onclick=function(){var t=q('#ctlNews').value.trim()||'BREAKING DEVELOPMENT';\n"
"  var o={text:t,level:'breaking'};API.news(o);bsend('news',o)}});\n"
"boot('transport',function(){StatePoll.start()});",'js-panel')

if s!=orig:io.open(P,'w',encoding='utf-8').write(s)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

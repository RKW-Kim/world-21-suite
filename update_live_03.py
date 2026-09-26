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

# ── 1 · header CSS: chips → pill system ──
NEW_HDR = """/* header — pill system */
#scrim{position:absolute;left:0;right:0;top:0;height:150px;z-index:30;pointer-events:none;background:linear-gradient(180deg,rgba(5,5,7,.55),rgba(5,5,7,.16) 55%,transparent)}
#hdr{position:absolute;left:0;right:0;top:12px;z-index:40;display:flex;align-items:center;gap:10px;padding:0 14px;pointer-events:none;transition:opacity .4s ease,transform .5s var(--ease)}
body.hide-header #hdr{opacity:0;transform:translateY(-100%)}
.pill{display:flex;align-items:center;height:44px;padding:0 8px;border-radius:999px;background:var(--glass);backdrop-filter:blur(16px) saturate(1.6);box-shadow:0 12px 32px rgba(0,0,0,.42),0 2px 8px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.09);white-space:nowrap}
.sgt{display:flex;align-items:center;gap:9px;height:100%;padding:0 11px}
.cdot{width:3px;height:3px;border-radius:50%;background:rgba(var(--acc-rgb),.45);flex:none}
.mst{display:flex;align-items:center;gap:10px;height:100%;padding:0 12px 0 16px}
.mst b{font-family:var(--fd);font-weight:700;font-size:13px;letter-spacing:.18em;color:var(--fg)}
.mlive{display:flex;align-items:center;gap:6px;font-family:var(--fd);font-weight:700;font-size:9px;letter-spacing:.24em;color:var(--live)}
.mlive i{width:6px;height:6px;border-radius:50%;background:currentColor;animation:softpulse 1.6s infinite}
.murl{font-family:var(--fm);font-size:8.5px;letter-spacing:.22em;color:var(--fnt)}
#goalSeg .glabel{font-family:var(--fd);font-weight:700;font-size:9px;letter-spacing:.2em;color:var(--acc)}
.gbar{width:104px;height:9px;border-radius:999px;background:rgba(127,127,127,.24);overflow:hidden;position:relative;flex:none}
.gbar i{position:absolute;top:0;bottom:0;left:0;border-radius:999px;background:linear-gradient(90deg,rgba(var(--acc-rgb),.6),var(--acc));overflow:hidden;transition:width .9s var(--ease)}
.gbar i svg{position:absolute;top:0;left:0;height:100%;width:200%;animation:wave 2.8s linear infinite}
.gbar i svg path{fill:rgba(255,255,255,.32)}
@keyframes wave{to{transform:translateX(-50%)}}
#goalVal{font-family:var(--fm);font-size:11.5px;font-weight:600;color:var(--fg)}
#goalVal em{font-style:normal;color:var(--fnt);font-size:10px}
#goalChip.hit{animation:hit 2.4s var(--ease)}
@keyframes hit{0%,100%{filter:none}18%{filter:brightness(1.9)}}
#clkDate{font-family:var(--fm);font-size:10px;letter-spacing:.12em;color:var(--mut)}
.clktz{font-size:10.5px;letter-spacing:.1em;color:var(--mut)}
.clktz b{color:var(--fg);font-weight:600}
.nlab{font-family:var(--fm);font-size:9px;letter-spacing:.18em;color:var(--acc)}
#nextTxt{font-family:var(--fm);font-size:10px;letter-spacing:.06em;color:var(--fg);max-width:230px;overflow:hidden;text-overflow:ellipsis}
@media (max-width:1760px){#nextSeg{display:none}}
@media (max-width:1560px){#clkNyc{display:none}}
@media (max-width:1340px){#clkDate{display:none}}
@media (max-width:1240px){#goalSeg .gbar{display:none}}
@media (max-width:1080px){#goalSeg{display:none}}
/* island */"""
rng('/* header */','/* island */',NEW_HDR,'css-header-pills')

# ── 2 · header HTML ──
NEW_HDR_HTML = """<header id="hdr">
  <div class="pill">
    <span class="mst"><b>SMILE</b><span class="mlive"><i></i>LIVE</span><span class="murl">SMILE.CO.KE</span></span>
    <span class="sgt" id="goalChip"><i class="cdot"></i><span class="glabel" id="goalLabel">SUB GOAL</span><span class="gbar"><i id="goalFill" style="width:0%"><svg viewBox="0 0 120 8" preserveAspectRatio="none"><path d="M0 4 Q7.5 1 15 4 T30 4 T45 4 T60 4 Q67.5 1 75 4 T90 4 T105 4 T120 4 V8 H0 Z"/></svg></i></span><b class="mono" id="goalVal">\u2014</b></span>
  </div>
  <div class="pill" style="margin-left:auto">
    <span class="sgt"><span id="clkDate">\u2014 \u2014 \u2014</span><i class="cdot"></i><span class="clktz mono" id="clkNbo"><b>NBO</b> --:--</span><span class="clktz mono" id="clkNyc"><b>NYC</b> --:--</span></span>
    <span class="sgt" id="nextSeg"><i class="cdot"></i><span class="nlab">NEXT</span><b id="nextTxt">MARKET WAKE UP \u00b7 08:00 EAT</b></span>
  </div>
</header>"""
rng('<header id="hdr">','</header>',NEW_HDR_HTML,'html-header-pills')

# ── 3 · scrim element ──
rep('<div id="stage"></div>','<div id="stage"></div>\n<div id="scrim"></div>','scrim-html')

# ── 4 · news / footer / drawer / frame CSS region rewrite ──
NEW_CHROME = """/* news rail \u2014 pill ribbon */
#news{position:absolute;left:12px;right:12px;bottom:66px;height:44px;z-index:39;display:flex;align-items:center;gap:13px;padding:0 12px 0 9px;border-radius:999px;background:rgba(9,9,11,.93);backdrop-filter:blur(16px) saturate(1.5);box-shadow:0 14px 36px rgba(0,0,0,.45),0 2px 8px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.08);transform:translateX(-104%);opacity:0;transition:transform .6s var(--spring),opacity .3s ease;pointer-events:none;overflow:hidden}
#news.on{transform:none;opacity:1}
.ntag{flex:none;font-family:var(--fd);font-weight:700;font-size:9.5px;letter-spacing:.22em;padding:7px 14px;color:var(--on);background:var(--acc);border-radius:999px}
#news.breaking .ntag{background:var(--down);color:#fff;animation:softpulse 1.2s infinite}
#newsTxt{font-family:var(--fd);font-weight:600;font-size:14px;letter-spacing:.04em;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#news.breaking #newsTxt{color:#FFD7DC}
#newsTime{margin-left:auto;flex:none;font-size:9.5px;letter-spacing:.16em;color:var(--fnt)}
body.hide-news #news{display:none}
body.hide-footer #news{bottom:10px}
/* footer \u2014 pill bar */
#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:48px;z-index:40;display:flex;align-items:center;gap:14px;padding:0 10px 0 16px;border-radius:999px;background:rgba(8,8,10,.9);backdrop-filter:blur(16px) saturate(1.5);box-shadow:0 14px 36px rgba(0,0,0,.45),0 2px 8px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.08);transition:transform .55s var(--spring),opacity .35s ease}
body.hide-footer #ftr{opacity:0;transform:translateY(130%);pointer-events:none}
.flogo{display:flex;align-items:center;flex:none}
.flogo svg{height:24px;width:auto}
.fmask{flex:1;overflow:hidden;display:flex;align-items:center;min-width:0}
#crawl{display:flex;align-items:center;width:max-content;will-change:transform}
.q{display:flex;align-items:baseline;gap:10px;margin-right:46px;position:relative;white-space:nowrap}
.q::after{content:"";position:absolute;right:-25px;top:50%;width:4px;height:4px;background:rgba(var(--acc-rgb),.45);transform:translateY(-50%) rotate(45deg)}
.q b{font-family:var(--fd);font-weight:700;font-size:11.5px;letter-spacing:.08em;color:var(--fg)}
.qp{font-size:11.5px;font-weight:600;color:var(--fg)}
.qc{font-size:10.5px;font-weight:600}
/* chat drawer */
#drawer{position:absolute;right:16px;bottom:66px;width:440px;max-width:72vw;z-index:45;border-radius:20px;padding:14px;display:flex;gap:11px;align-items:flex-start;background:rgba(14,14,17,.94);backdrop-filter:blur(20px) saturate(1.5);box-shadow:0 22px 48px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.12);opacity:0;transform:translateY(12px) scale(.97);transform-origin:bottom right;transition:opacity .28s ease,transform .45s var(--spring);pointer-events:none}
#drawer.open{opacity:1;transform:none;pointer-events:auto}
.pico{width:30px;height:30px;border-radius:999px;background:rgba(255,255,255,.08);display:grid;place-items:center;flex:none}
.pico svg{width:15px;height:15px}
.duser{font-family:var(--fd);font-weight:700;font-size:12px;color:var(--fg)}
.duser em{font-style:normal;color:var(--fnt);font-weight:500;font-size:10.5px;margin-left:5px}
.dmsg{font-size:12.5px;color:var(--mut);line-height:1.45;margin-top:3px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical}
.dact{margin-left:auto;display:flex;flex-direction:column;gap:6px;flex:none}
.dbtn{width:25px;height:25px;border-radius:999px;display:grid;place-items:center;color:var(--fnt);cursor:pointer}
.dbtn:hover{color:var(--fg);background:rgba(255,255,255,.08)}
.dbtn.on{color:var(--acc);background:rgba(var(--acc-rgb),.12)}
/* video frame */
#frame{position:absolute;z-index:5;aspect-ratio:16/9;pointer-events:none;transition:opacity .3s ease}
body.hide-frame #frame{display:none}
.fcn{position:absolute;width:22px;height:22px;border-color:rgba(var(--acc-rgb),.8);border-style:solid;border-width:0;pointer-events:none;filter:drop-shadow(0 0 6px rgba(var(--acc-rgb),.25))}
.fcn.c1{left:0;top:0;border-left-width:2px;border-top-width:2px;border-radius:12px 0 0 0}
.fcn.c2{right:0;top:0;border-right-width:2px;border-top-width:2px;border-radius:0 12px 0 0}
.fcn.c3{left:0;bottom:0;border-left-width:2px;border-bottom-width:2px;border-radius:0 0 0 12px}
.fcn.c4{right:0;bottom:0;border-right-width:2px;border-bottom-width:2px;border-radius:0 0 12px 0}
#frameLabel{position:absolute;left:12px;bottom:12px;display:inline-flex;align-items:center;background:rgba(0,0,0,.58);border-radius:999px;padding:5px 13px;font-family:var(--fd);font-weight:700;font-size:10.5px;letter-spacing:.14em;color:#fff;backdrop-filter:blur(8px);box-shadow:inset 0 1px 0 rgba(255,255,255,.09)}
#frameGrip,#frameRsz{position:absolute;width:24px;height:24px;display:grid;place-items:center;color:rgba(255,255,255,.65);background:rgba(0,0,0,.5);border-radius:999px;opacity:0;transition:opacity .25s;pointer-events:auto;cursor:grab}
#frameGrip{top:8px;right:8px}
#frameRsz{bottom:8px;right:8px;cursor:nwse-resize}
#frame:hover #frameGrip,#frame:hover #frameRsz{opacity:1}
#frameGrip svg,#frameRsz svg{width:12px;height:12px;stroke:currentColor;stroke-width:2;fill:none;stroke-linecap:round}
#frame.drag{opacity:.85}"""
rng('/* news rail */','#frame.drag{opacity:.85}',NEW_CHROME,'css-chrome-pills')

# ── 5 · footer HTML: wordmark + crawl only ──
NEW_FTR = """<footer id="ftr">
  <span class="flogo"><svg viewBox="0 0 146.5 87" style="fill:#FAFAFA"><path d="m39 48c0.5 1.7 1.2 2.9 3.3 2.9 1.7 0.1 3-0.7 3-1.9s-0.5-1.9-2.3-2.1l-3-0.4c-4.6-0.6-7.5-2.2-7.5-6.3s3.6-6.1 9.6-6.1c4.5-0.1 7.7 1 10.1 4.9l-7.6 1c-0.3-1.3-1-2-2.4-2s-1.9 1-1.9 1.9 0.6 1.4 1.7 1.5l3.5 0.4c4.5 0.5 7.8 2.4 7.8 6.2 0 4-4.1 6.6-11.1 6.6-5.2 0-9.5-1.1-11-5.6l7.8-1z"/><path d="m57.2 34.1h7.3v2.9h0.1c1.3-1.8 3.8-2.9 6.9-2.9 2.5 0 4.4 0.9 5.9 3 1.7-1.6 3.6-3 7.6-3 3.4 0 7.3 1.4 7.3 6.9v13.6h-7.9v-12.1c0-1.3-1.2-2.6-2.8-2.6s-3.2 1.7-3.2 3.2v11.5h-7.8v-12.3c0-1.1-1.2-2.4-2.5-2.4-1.5 0-3 1.3-3 3.2v11.4h-7.9v-20.4z"/><path d="m97.2 34.1h7.9v20.5h-7.9v-20.5z"/><path d="m97.2 26.1h7.9v5.2h-7.9v-5.2z"/><polygon points="110.2 26.1 117.9 26.1 117.9 54.6 110.2 54.6"/><path d="m131.4 39.2c2.4-0.8 5.6-0.2 6.4 2.7h-7.8c0.2-0.7 0.4-2 1.4-2.7m6.5 8.7c-0.9 1.5-2.3 2-4 2-2.5 0-3.9-1.5-3.9-4h15.5c0.1-6.9-2.7-11.7-11.4-11.7-8.2 0-12.1 4-12.1 10.4 0 5.6 3.4 10 12.2 10 4.7 0 8.8-1.6 11.2-5.6l-7.5-1.1z"/><path fill="#FFC107" d="m29.7 45.1c0 7.5-5.9 14.3-14.8 14.3-7.6 0-14.3-5.5-14.3-14.3 0-6.7 5.3-14.5 14.6-14.5 6.7-0.1 14.5 5.3 14.5 14.5z"/><path fill="#0A0A0A" d="m23.9 45.2c0 4.3-3.3 8.4-8.5 8.5-4.8 0-8.7-2.8-9.2-8.8l-1.6 0.1c0.3 4.6 3.1 10.5 10.8 10.5 6.3 0 10.1-5.1 10.1-10.6l-1.6 0.3z"/><circle fill="#0A0A0A" cx="8.7" cy="39.9" r="1.6"/><path fill="#0A0A0A" d="m23.2 39.9c0 0.8-0.7 1.6-1.7 1.6-0.9 0-1.8-0.6-1.8-1.6 0-0.8 0.8-1.7 1.8-1.7 0.9 0.1 1.7 0.8 1.7 1.7z"/></svg></span>
  <i class="cdot"></i>
  <div class="fmask"><div id="crawl"></div></div>
</footer>"""
rng('<footer id="ftr">','</footer>',NEW_FTR,'html-footer-pill')

# ── 6 · frame label: no dot, text-only ──
rep('<span id="frameLabel"><i></i>YOU</span>','<span id="frameLabel">YOU</span>','html-framelabel')
rep("var l=$('#frameLabel');if(l)l.innerHTML='<i></i>'+esc(LBL)}","var l=$('#frameLabel');if(l)l.textContent=LBL}",'js-framelabel-2b')
rep("var l=$('#frameLabel');if(l)l.innerHTML='<i></i>'+esc(P.get('label')||'YOU')}","var l=$('#frameLabel');if(l)l.textContent=P.get('label')||'YOU'}",'js-framelabel-base')

# ── 7 · dead code: Cap + nextSess ──
rng('\u2500\u2500 footer cap rotation \u2500','\u2500\u2500 video frame \u2500','\u2500\u2500 video frame \u2500','js-cap-remove')
rng('function nextSess(){var d=new Date()',"pad(m%60)+'H '+pad(m%60)+'M':m+'M'}}",'','js-nextsess-remove')
rep("boot('footer',function(){Px.build();Crawl.start();Cap.refresh();\n setInterval(function(){Cap.tick()},9000)});",
    "boot('footer',function(){Px.build();Crawl.start()});",'js-bootfooter')

# ── 8 · island joins the top band + softenings ──
rep('#islw{position:absolute;top:26px;left:50%;','#islw{position:absolute;top:11px;left:50%;','css-islw-band')
rep('.tcell + .tcell{border-left:1px solid rgba(255,255,255,.08)}','.tcell + .tcell{border-left:1px solid rgba(255,255,255,.05)}','css-tcell-soft')
rep('background:rgba(255,255,255,.16);opacity:0','background:rgba(255,255,255,.11);opacity:0','css-seam-soft')

if s!=orig:io.open(P,'w',encoding='utf-8').write(s)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

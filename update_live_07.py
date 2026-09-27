import io,os,sys,re,subprocess,shutil,tempfile
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P) or os.path.getsize(P)==0:
    print('\U0001F4A5 overlay/live.html missing/empty');sys.exit(1)
s=io.open(P,encoding='utf-8').read();orig=s
applied,skipped=[],[]
DECLARED={'geo-corridor':(1,1),'js-setidle':(1,1),'js-resize':(2,2)}  # deliberate balanced additions
def rep(a,b,tag):
    global s
    if a not in s:skipped.append(tag);return
    d=(b.count('{')-a.count('{'),b.count('}')-a.count('}'))
    if d!=DECLARED.get(tag,(0,0)):
        print('\U0001F4A5 %s: undeclared brace delta %s \u2014 refusing to write'%(tag,d));sys.exit(1)
    s=s.replace(a,b,1);applied.append(tag)

# 1 · hard clamp \u2014 past-screen becomes geometrically impossible
rep('#isl{position:relative;display:flex;align-items:center;padding-left:9px;overflow:hidden;border-radius:999px;',
    '#isl{position:relative;display:flex;align-items:center;padding-left:9px;overflow:hidden;border-radius:999px;max-width:calc(100vw - 40px);min-width:0;','css-isl-clamp')

# 2 · price tick: color pulse only \u2014 no motion, no axis conflict
rep(""".roll{animation:tickUp .32s var(--ease)}
.roll.dn{animation-name:tickDown}
@keyframes tickUp{0%{opacity:0;transform:translateX(12px);color:var(--up)}100%{opacity:1;transform:none;color:var(--fg)}}
@keyframes tickDown{0%{opacity:0;transform:translateX(12px);color:var(--down)}100%{opacity:1;transform:none;color:var(--fg)}}""",
""".roll{animation:tickUp .7s ease-out}
.roll.dn{animation-name:tickDown}
@keyframes tickUp{0%{color:var(--up)}100%{color:var(--fg)}}
@keyframes tickDown{0%{color:var(--down)}100%{color:var(--fg)}}""",'css-tick-pulse')

# 3 · logo +50% (39\u219258) \u00b7 footer 54\u219270 \u00b7 lanes shift up
rep('.flogo svg{height:39px;width:auto}','.flogo svg{height:58px;width:auto}','css-flogo-58')
rep('#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:54px;','#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:70px;','css-ftr-70')
rep('#news{position:absolute;left:50%;bottom:94px;','#news{position:absolute;left:50%;bottom:110px;','css-news-110')
rep('#drawer{position:absolute;right:16px;bottom:72px;','#drawer{position:absolute;right:16px;bottom:88px;','css-drawer-88')
rep('#csl{position:absolute;left:50%;bottom:152px;','#csl{position:absolute;left:50%;bottom:168px;','css-csl-168')
rep('#hint{position:absolute;left:50%;bottom:170px;','#hint{position:absolute;left:50%;bottom:186px;','css-hint-186')

# 4 · corridor() \u2014 idle island sizes itself to the space between the pills
rep("var GEO={idle:{w:612,h:46,r:999},as:{w:660,h:64,r:999},al:{w:700,h:150,r:40},trade:{w:720,h:236,r:40},res:{w:620,h:112,r:36}};",
"""var GEO={idle:{w:612,h:46,r:999},as:{w:660,h:64,r:999},al:{w:700,h:150,r:40},trade:{w:720,h:236,r:40},res:{w:620,h:112,r:36}};
function corridor(){if(document.body.classList.contains('hide-header'))return Math.max(320,innerWidth-48);
 var l=document.getElementById('pillL'),r=document.getElementById('pillR');
 return Math.max(320,innerWidth-((l?l.offsetWidth:0)+(r?r.offsetWidth:0)+76))}""",'geo-corridor')

# 5 · idle view adapts to the corridor it's given
rep("""function vwIdle(){var m=Px.M.BTC;
 return '<div class="idleg"><span class="lv"><i></i>LIVE</span><span class="upt mono" data-r="upt">'+dur(Date.now()-Boot.since)+'</span></div>'
 +'<span class="pairwrap"><span class="psym mono">BTC</span><b class="ppx mono" data-r="px">'+fmtP(m.p)+'</b><span class="ppc mono '+(m.ch>=0?'up':'down')+'" data-r="pc">'+(m.ch>=0?'+':'')+m.ch.toFixed(1)+'%</span></span>'
 +'<span class="sess">'+sessDots()+'</span>'}""",
"""function vwIdle(w){var m=Px.M.BTC;
 var h='<div class="idleg"><span class="lv"><i></i>LIVE</span>';
 if(w>=500)h+='<span class="upt mono" data-r="upt">'+dur(Date.now()-Boot.since)+'</span>';
 h+='</div>'
 +'<span class="pairwrap"><span class="psym mono">BTC</span><b class="ppx mono" data-r="px">'+fmtP(m.p)+'</b><span class="ppc mono '+(m.ch>=0?'up':'down')+'" data-r="pc">'+(m.ch>=0?'+':'')+m.ch.toFixed(1)+'%</span></span>';
 if(w>=640)h+='<span class="sess">'+sessDots()+'</span>';
 return h}""",'js-vwidle-w')

# 6 · momentary views clamp to viewport \u00b7 idle clamps to corridor
rep("""  var closing=g.h<this.ih.v;
  this.iw.to(g.w,closing?420:300,closing?34:24);""",
"""  var closing=g.h<this.ih.v;
  var w=Math.min(g.w,innerWidth-40);
  this.iw.to(w,closing?420:300,closing?34:24);""",'js-setview-clamp')
rep("setIdle:function(){this.setView('idle',vwIdle(),GEO.idle)}};",
    "setIdle:function(){var w=Math.min(GEO.idle.w,corridor());this.setView('idle',vwIdle(w),{w:w,h:GEO.idle.h,r:GEO.idle.r})}};",'js-setidle')

# 7 · resize re-fits the island (debounced, at rest)
rep("boot('web',function(){if(P.get('web'))webToggle()});",
"""boot('web',function(){if(P.get('web'))webToggle()});
var rzT;addEventListener('resize',function(){clearTimeout(rzT);rzT=setTimeout(function(){curStage=null;sync()},150)});""",'js-resize')

# 8 · reduced-motion: snap instead of a marginally-stiff spring
rep("if(!MOTION){this.k=1400;this.d=90}","if(!MOTION){this.v=t;this.t=t;this.vel=0;Isl.paint();return}",'js-spr-snap')

# 9 · telemetry \u2014 console status shows live island dimensions
rep("s.textContent=(REAL?'LIVE INPUT':'DEMO/IDLE')+' \u00b7 island:'+ (Isl.view||'idle') +' \u00b7 queue:'+Stage.q.length+' \u00b7 '+(Eng.speed===1?'1x':'1/4x')",
    "s.textContent=(REAL?'LIVE INPUT':'DEMO/IDLE')+' \u00b7 isl '+Math.round(Isl.iw.v)+'x'+Math.round(Isl.ih.v)+' '+(Isl.view||'idle')+' \u00b7 q:'+Stage.q.length+' \u00b7 '+(Eng.speed===1?'1x':'1/4x')",'js-stat-isl')

# \u2550\u2550 GUARD: verify balance + real parse BEFORE touching the file \u2550\u2550
if s!=orig:
    blocks=re.findall(r'<script>(.*?)</script>',s,re.S);ok=True
    for i,b in enumerate(blocks):
        if b.count('{')!=b.count('}'):
            print('\u274c script %d imbalance (%d/%d) \u2014 NOT writing'%(i,b.count('{'),b.count('}')));ok=False
    node=shutil.which('node')
    if ok and node:
        for i,b in enumerate(blocks):
            tf=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8');tf.write(b);tf.close()
            r=subprocess.run([node,'--check',tf.name],capture_output=True,text=True);os.unlink(tf.name)
            if r.returncode!=0:
                print('\u274c node: '+' | '.join((r.stderr or '').splitlines()[:2])+' \u2014 NOT writing');ok=False
    if not ok:sys.exit(1)
    try:data=s.encode('utf-8')
    except UnicodeEncodeError as e:
        print('\U0001F4A5 encode fail \u2014 file untouched: '+str(e));sys.exit(1)
    tmp=P+'.tmp'
    with io.open(tmp,'wb') as f:f.write(data)
    os.replace(tmp,P)
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('lines %d -> %d'%(orig.count('\n'),s.count('\n')))

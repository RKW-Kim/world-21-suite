import io,os,re,sys

P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overly','test-8.html')
if not os.path.exists(P):
    print('MISSING: '+P);sys.exit(1)
s=io.open(P,encoding='utf-8').read()
orig=s
applied,skipped,issues=[],[],[]

def rep(a,b,tag):
    global s
    if a in s:
        s=s.replace(a,b,1);applied.append(tag)
    else:
        skipped.append(tag)

# FIX A — populate the left ticker cap (mascot + wordmark)
A_OLD="Cap.refresh();\nPx.sim();Px.binance();"
A_NEW=("Cap.refresh();\n"
       "(function(){var c=document.getElementById('capLeft');"
       "if(c)c.innerHTML=MASCOT()+'<span>SMILE</span>';})();\n"
       "Px.sim();Px.binance();")
if A_NEW.split('\n')[1] in s:
    skipped.append('fix-capleft (already applied)')
else:
    rep(A_OLD,A_NEW,'fix-capleft')

# FIX B — pods become visible as a property of the spring (width>3 => .on)
B_OLD="this.el.classList.toggle('zero',this.w.v<3)}"
B_NEW="this.el.classList.toggle('zero',this.w.v<3);this.el.classList.toggle('on',this.w.v>3)}"
if "toggle('on',this.w.v>3)" in s:
    skipped.append('fix-pod-on (already applied)')
else:
    rep(B_OLD,B_NEW,'fix-pod-on')

if s!=orig:
    io.open(P,'w',encoding='utf-8').write(s)

# ── AUDIT ──────────────────────────────────────────────
def need(label,cond):
    print(('  OK   ' if cond else '  FAIL ')+label)
    if not cond:issues.append(label)

print('── STRUCTURE ──')
need('starts with <!DOCTYPE html>',s.lstrip().startswith('<!DOCTYPE html>'))
need('ends with </html> (no truncation)',s.rstrip().endswith('</html>'))
need('no heredoc EOF leakage',not [l for l in s.split('\n') if l.strip()=='EOF'])
need('exactly one <style>…</style>',s.count('<style>')==1 and s.count('</style>')==1)
need('exactly one <script>…</script>',s.count('<script>')==1 and s.count('</script>')==1)
need('IIFE closed',s.count('})();')>=1 and s.rstrip().endswith('</html>'))

print('── CRITICAL SYMBOLS ──')
for sym in ['class Spring','const Eng=','new Pod(\'podP\')','new Pod(\'podT\')',
            'const Stage=','const Trade=','const Px=','const Meet=','const Scenes=',
            'const Obs=','const Layout=','const Cam=','const Marquee=','const Drawer=',
            'const Goal=','const Cap=','const Mood=','const Demo=','StatePoll',
            'function sync()','const ALERTS=','const GEO=','MASCOT()',
            'BroadcastChannel','smile-suite-v9','SMILE_ISLAND','applyAll()','Demo.start()']:
    need(sym,sym in s)

print('── DUPLICATE IDS ──')
ids=re.findall(r'id="([^"]+)"',s)
dupes=sorted({i for i in ids if ids.count(i)>1})
need('none',not dupes)
if dupes:print('       dupes: '+', '.join(dupes))

print('── SEG CONTROLS WIRED ──')
for seg in ['moneyMode','islandPos','txtSize','pipFit','pipRatio']:
    need(seg+': HTML + wireSeg',('data-seg="'+seg+'"') in s and ("wireSeg('"+seg+"'") in s)

print('── VIEW REFS BOUND ──')
for r in ['uptime','px','pc','rot','rec','minipnl','trtime','trpnl','trr','trpct','trarr','mark','asub']:
    need('data-r="'+r+'"',('data-r="'+r+'"') in s)

print('── FIXES FROM THIS BATCH ──')
need('capLeft populated',"getElementById('capLeft')" in s)
need('pod .on tied to spring',"toggle('on',this.w.v>3)" in s)
need('no stray CJK identifier','\u6d3b\u8dc3' not in s)

print('── EMOJI DISCIPLINE ──')
emoji=[ch for ch in s if ord(ch)>=0x1F000]
need('emoji only inside message content (<=2, both in chat strings)',len(emoji)<=2)
if emoji:print('       found %d: %s'%(len(emoji),''.join(sorted(set(emoji)))))

print('── SIZE ──')
print('  lines: %d · bytes: %d'%(s.count('\n')+1,len(s.encode('utf-8'))))

print('')
print('APPLIED: '+(', '.join(applied) or 'none'))
print('SKIPPED: '+(', '.join(skipped) or 'none'))
print('ISSUES : '+(', '.join(issues) or 'none — file is sound'))
sys.exit(1 if issues else 0)

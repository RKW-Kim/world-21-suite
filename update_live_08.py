import io,os,sys,re,subprocess,shutil,tempfile
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P) or os.path.getsize(P)==0:
    print('\U0001F4A5 overlay/live.html missing/empty');sys.exit(1)
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

# 1 · punch: no black disc — the smiley is hardware by permanence, not by a socket
rep('#punch{flex:none;width:38px;height:38px;border-radius:50%;background:#000;box-shadow:inset 0 0 0 1px rgba(255,255,255,.07);display:grid;place-items:center;position:relative;z-index:2}\n#punch .smk{width:30px;height:30px}',
    '#punch{flex:none;display:grid;place-items:center;position:relative;z-index:2}\n#punch .smk{width:28px;height:28px}','css-punch-clean')

# 2 · liquid: smiley inverts on yellow (05 accidentally dropped this — yellow-on-yellow = invisible smiley at TP)
rep('#isl.liquid #punch{background:rgba(0,0,0,.16);box-shadow:none}',
    '#isl.liquid .smk .fc{fill:var(--on)}#isl.liquid .smk .fe{fill:var(--acc)}#isl.liquid .smk .fm{stroke:var(--acc)}','css-liquid-smk')

# 3 · footer: Market Sunrise — sun disc + word + fade mask
rng('.flogo{display:flex;align-items:center;flex:none}',
'.flogo svg{height:58px;width:auto}',
'''#fsun{position:absolute;left:8px;top:-14px;width:76px;height:76px;border-radius:50%;background:var(--acc);box-shadow:0 12px 28px rgba(0,0,0,.5),inset 0 2px 3px rgba(255,255,255,.35),inset 0 -3px 6px rgba(0,0,0,.12);display:grid;place-items:center;z-index:2}
#fsun svg{width:60px;height:60px}
#fword{display:flex;flex-direction:column;justify-content:center;gap:3px;flex:none;padding-right:16px;margin-right:4px;border-right:1px solid rgba(255,255,255,.08)}
#fword b{font-family:var(--fd);font-weight:700;font-size:19px;line-height:1;color:var(--fg)}
#fword small{font-family:var(--fm);font-size:7px;letter-spacing:.3em;color:var(--fnt)}
.fmask{flex:1;overflow:hidden;display:flex;align-items:center;min-width:0;-webkit-mask-image:linear-gradient(90deg,transparent,#000 30px,#000 calc(100% - 18px),transparent);mask-image:linear-gradient(90deg,transparent,#000 30px,#000 calc(100% - 18px),transparent)}''','css-sunrise')
rep('#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:70px;z-index:40;display:flex;align-items:center;gap:14px;padding:0 10px 0 16px;',
    '#ftr{position:absolute;left:12px;right:12px;bottom:10px;height:70px;z-index:40;display:flex;align-items:center;gap:14px;padding:0 14px 0 96px;','css-ftr-pad')

# 4 · footer HTML: sun rises, word inside, crawl fades in from its light
rng('<footer id="ftr">','</footer>',
'''<footer id="ftr">
  <div id="fsun"><svg viewBox="0 0 100 100"><circle cx="31" cy="35" r="5.5" fill="#0A0A0A"/><circle cx="69" cy="35" r="5.5" fill="#0A0A0A"/><path d="M 20 48 A 30 30 0 0 0 80 48" fill="none" stroke="#0A0A0A" stroke-width="7.5" stroke-linecap="round"/></svg></div>
  <div id="fword"><b>smile</b><small>SMILE.CO.KE</small></div>
  <div class="fmask"><div id="crawl"></div></div>
</footer>''','html-sunrise')

# ═══ GUARD: balance + node parse BEFORE touching the file ═══
if s!=orig:
    blocks=re.findall(r'<script>(.*?)</script>',s,re.S);ok=True
    for i,b in enumerate(blocks):
        if b.count('{')!=b.count('}'):
            print('\u274c script %d imbalance \u2014 NOT writing'%i);ok=False
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

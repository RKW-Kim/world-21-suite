import io,os,sys,re,subprocess,shutil,tempfile
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P) or os.path.getsize(P)==0:
    print('💥 overlay/live.html missing/empty');sys.exit(1)
s=io.open(P,encoding='utf-8').read();orig=s

BAD="if(dn)g.px.classList.add('dn')}}"
GOOD="if(dn)g.px.classList.add('dn')}"

# balance guard — this fix deliberately changes the count (that's its job),
# so the anchor shape is asserted instead:
assert BAD.count('{')==GOOD.count('{') and BAD.count('}')==GOOD.count('}')+1,'anchor shape drifted'

if BAD in s:
    s=s.replace(BAD,GOOD,1);print('✅ FIXED: extra "}" removed — BTC price-tick block in Px.set')
elif GOOD in s and "g.px.classList.remove('roll','dn')" in s:
    print('⚠️ already fixed')
else:
    print('❌ anchor not found — paste me the lines around Px.set');sys.exit(1)

# self-verify BEFORE writing: whole-file balance + real node parse
blocks=re.findall(r'<script>(.*?)</script>',s,re.S);ok=True
for i,b in enumerate(blocks):
    if b.count('{')!=b.count('}'):
        print('❌ script %d still imbalanced (%d opens / %d closes)'%(i,b.count('{'),b.count('}')));ok=False
node=shutil.which('node')
if ok and node:
    for i,b in enumerate(blocks):
        tf=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8');tf.write(b);tf.close()
        r=subprocess.run([node,'--check',tf.name],capture_output=True,text=True);os.unlink(tf.name)
        if r.returncode!=0:
            print('❌ node: '+' | '.join((r.stderr or '').splitlines()[:2]));ok=False
if not ok:
    print('💥 NOT WRITING — file untouched');sys.exit(1)
if s!=orig:
    try:data=s.encode('utf-8')
    except UnicodeEncodeError as e:
        print('💥 encode fail — file untouched: '+str(e));sys.exit(1)
    tmp=P+'.tmp'
    with io.open(tmp,'wb') as f:f.write(data)
    os.replace(tmp,P)
    print('💾 written atomically · balance verified' + (' · node --check passed' if node else ''))

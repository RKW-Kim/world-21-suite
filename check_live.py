import io,os,re,sys,subprocess,shutil,tempfile
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P):print('❌ overlay/live.html not found');sys.exit(1)
s=io.open(P,encoding='utf-8').read();probs=[]
js='\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S))
css=s[:s.find('</style>')]
defined=set(re.findall(r'id="([^"]+)"',s))|set(re.findall(r"\.id\s*=\s*'([^']+)'",js))
used=set(re.findall(r"\$\('#([A-Za-z0-9_-]+)'\)",js))|set(re.findall(r"getElementById\('([^']+)'\)",js))
for m in sorted(used-defined):probs.append('phantom id: '+m)
ids=re.findall(r'id="([^"]+)"',s)
for d in sorted({i for i in ids if ids.count(i)>1}):probs.append('duplicate id: '+d)
for c in sorted(set(re.findall(r"classList\.(?:add|toggle|remove)\('([A-Za-z0-9_-]+)'",js))):
    if c.endswith('-'):
        if not re.search(re.escape(c)+r'[A-Za-z0-9_]',css):probs.append('prefix "'+c+'" matches no CSS rule')
    elif not re.search(r'[.\#][A-Za-z0-9_-]*'+re.escape(c)+r'[\s{,:.\[]',css):
        probs.append('phantom class: '+c)
node=shutil.which('node')
for i,b in enumerate(re.findall(r'<script>(.*?)</script>',s,re.S)):
    o,c=b.count('{'),b.count('}')
    if o!=c:probs.append('script %d: brace imbalance (opens %d · closes %d · delta %+d)'%(i,o,c,o-c))
    if node:
        tf=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8');tf.write(b);tf.close()
        try:
            r=subprocess.run([node,'--check',tf.name],capture_output=True,text=True)
            if r.returncode!=0:
                probs.append('script %d: NODE SYNTAX ERROR — %s'%(i,' | '.join((r.stderr or '').strip().splitlines()[:3])))
        finally:os.unlink(tf.name)
for t in ['</html>','</body>','</style>']:
    if s.count(t)!=1:probs.append('markup: expected one '+t)
if probs:
    print('💥 CHECK FAILED — do not ship:');[print('   ❌ '+p) for p in probs];sys.exit(1)
print('✅ CLEAN · ids · classes · braces · %s · %d lines'%('node --check passed' if node else 'install node for a real syntax gate',s.count('\n')+1))

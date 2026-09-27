import io,os,sys,re,shutil,subprocess,tempfile

P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overly','test-8.html')
if not os.path.exists(P):
    print('❌ FILE NOT FOUND: '+P);sys.exit(1)
s=io.open(P,encoding='utf-8').read(); orig=s
applied,skipped=[],[]

print('──────────────────────────────────')
print('  🛠  SMILE PATCH 11 · RESCUE + RADAR')
print('──────────────────────────────────')

def rep(a,b,tag):
    global s
    if a in s: s=s.replace(a,b,1);applied.append(tag)
    else: skipped.append(tag)

# 💥 THE BLANK-PAGE KILLER — Chrome object was never closed (missing })
rep("+fmtN(g.tgt)+'</em></b>'}};", "+fmtN(g.tgt)+'</em></b>'}}};", 'chrome-brace — fixes the total blank')

# Goal.set refreshes the header goal (safe anchor)
if "APP.Chrome)APP.Chrome.render();if(APP.Panel)" in s:
    skipped.append('goal-refresh (already ok)')
else:
    rep("Cap.refresh();Cap.i=0;if(APP.Panel)",
        "Cap.refresh();Cap.i=0;if(APP.Chrome)APP.Chrome.render();if(APP.Panel)",
        'goal-refresh — header goal updates live')

# The chat column element existed in CSS+JS but never in the HTML — inject it
if 'id="chatCol"' in s:
    skipped.append('chatcol-element (already ok)')
else:
    rep('  <div id="ticker">','  <div id="chatCol"></div>\n  <div id="ticker">',
        'chatcol-element — solo chat column now actually exists')

# Every chat that hits the drawer also feeds the column
rep("show(d){const e=$('#capDrawer');if(!e)return;",
    "show(d){if(APP.ChatCol)APP.ChatCol.add(d);const e=$('#capDrawer');if(!e)return;",
    'drawer-feeds-column')

# Demo narrative gets one chat so the column shows life
rep("  this.schedule(11000,()=>Trade.open({market:'BTC/USDT',side:'long'}));",
    "  this.schedule(8200,()=>Drawer.show({plat:'yt',name:'Zawadi',handle:'zawadi_fx',msg:'NBO open soon — watching EURUSD closely'}));\n  this.schedule(11000,()=>Trade.open({market:'BTC/USDT',side:'long'}));",
    'demo-chat')

# ⚡ boot splash + 💥 failure banner (registered BEFORE the main script so it catches even syntax errors)
if 'bootSplash' in s:
    skipped.append('splash+guard (already ok)')
else:
    SPLASH=('<div id="bootSplash" style="position:fixed;left:50%;bottom:26px;transform:translateX(-50%);'
     'z-index:99999;display:flex;align-items:center;gap:9px;padding:10px 18px;border-radius:999px;'
     'background:#0a0a0c;border:1px solid rgba(255,193,7,.45);font-family:ui-monospace,Menlo,monospace;'
     'font-size:11px;letter-spacing:.22em;color:#FFC107">\u26a1 SMILE BOOTING\u2026</div>\n')
    GUARD=('<script>\n'
     '(function(){\n'
     'window.addEventListener("error",function(e){\n'
     ' var d=document.getElementById("bootSplash");if(!d)return;\n'
     ' d.setAttribute("style","position:fixed;inset:0;z-index:99999;display:grid;place-items:center;background:rgba(9,9,11,.97);padding:24px");\n'
     ' d.innerHTML=\'<div style="max-width:680px;border:2px solid #F6465D;border-radius:18px;padding:26px 30px;background:rgba(246,70,93,.07);font-family:ui-monospace,Menlo,monospace;text-align:center">\'\n'
     '  +\'<div style="font-size:40px">\U0001F4A5</div>\'\n'
     '  +\'<div style="color:#fff;font-weight:700;font-size:15px;letter-spacing:.2em;margin:12px 0 10px">SMILE FAILED TO BOOT</div>\'\n'
     '  +\'<div id="bootErrMsg" style="color:#FFD7DC;font-size:12.5px;line-height:1.65;word-break:break-word"></div>\'\n'
     '  +\'<div style="color:#a1a1aa;font-size:11px;margin-top:12px">line \'+(e.lineno||"?")+\' \u00b7 copy this red box and paste it back</div>\'\n'
     '  +\'</div>\';\n'
     ' var m=document.getElementById("bootErrMsg");if(m)m.textContent=String((e&&e.message)||e||"unknown error");\n'
     '});\n'
     '})();\n'
     '</script>\n')
    rep('<body>\n','<body>\n'+SPLASH+GUARD,'splash+guard — failures are now VISIBLE')

# Remove splash on successful boot (works for both boot variants)
if '__sp' in s:
    skipped.append('splash-removal (already ok)')
else:
    RM="\nvar __sp=document.getElementById('bootSplash');if(__sp)__sp.remove();"
    if "bootstep('demo',function(){if(!IS_CONTROL&&!APP.CLEAN)Demo.start()});" in s:
        s=s.replace("bootstep('demo',function(){if(!IS_CONTROL&&!APP.CLEAN)Demo.start()});",
                    "bootstep('demo',function(){if(!IS_CONTROL&&!APP.CLEAN)Demo.start()});"+RM,1)
        applied.append('splash-removal')
    elif "if(!IS_CONTROL&&!APP.CLEAN)Demo.start();" in s:
        s=s.replace("if(!IS_CONTROL&&!APP.CLEAN)Demo.start();",
                    "if(!IS_CONTROL&&!APP.CLEAN)Demo.start();"+RM,1)
        applied.append('splash-removal (legacy boot)')
    else:
        skipped.append('splash-removal (no anchor — splash will linger, tell me)')

# ═══ 🔍 SYNTAX RADAR — check BEFORE writing, refuse to ship broken files ═══
print('')
print('🔍 syntax check · nothing gets written until this passes…')

def check_js(src):
    src=src.replace('/[&<>"\']/g','/X/g')  # neutralize the one regex containing quotes
    problems=[];stack=[];state='code';line=1;i=0;n=len(src)
    pairs={')':'(',']':'[','}':'{'}
    while i<n:
        c=src[i];nxt=src[i+1] if i+1<n else ''
        if c=='\n':line+=1
        if state=='code':
            if c=='/' and nxt=='/':state='line';i+=2;continue
            if c=='/' and nxt=='*':state='block';i+=2;continue
            if c=="'":state='sq';i+=1;continue
            if c=='"':state='dq';i+=1;continue
            if c in '([{':stack.append((c,line))
            elif c in ')]}':
                if not stack:problems.append('line %d: "%s" closes nothing'%(line,c))
                else:
                    op,ol=stack.pop()
                    if op!=pairs[c]:problems.append('line %d: "%s" does not match "%s" opened on line %d'%(line,c,op,ol))
        elif state=='line':
            if c=='\n':state='code'
        elif state=='block':
            if c=='*' and nxt=='/':state='code';i+=2;continue
        else:
            if c=='\\':i+=2;continue
            if (state=='sq' and c=="'") or (state=='dq' and c=='"'):state='code'
        i+=1
    for op,ol in stack:problems.append('line %d: "%s" was never closed'%(ol,op))
    if state not in ('code','line'):problems.append('ends inside an open string')
    return problems

blocks=re.findall(r'<script>(.*?)</script>',s,re.S)
bal=[]
for bi,b in enumerate(blocks):
    for p in check_js(b):bal.append('[script %d] %s'%(bi+1,p))

node_bin=shutil.which('node'); node_bad=[]
if node_bin:
    for bi,b in enumerate(blocks):
        tf=tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8')
        tf.write(b);tf.close()
        try:
            r=subprocess.run([node_bin,'--check',tf.name],capture_output=True,text=True)
            if r.returncode!=0:
                node_bad.append('[script %d] %s'%(bi+1,' | '.join((r.stderr or '').strip().splitlines()[:3])))
        finally:
            os.unlink(tf.name)

fatal=node_bad or (bal and not node_bin)
if node_bad:
    print('🔴 NODE FOUND REAL ERRORS:'); [print('   ❌ '+p) for p in node_bad]
elif bal and node_bin:
    print('🟡 balancer grumbles, but node (real parser) says the file is fine — trusting node')
    [print('   ⚠️  '+p) for p in bal[:4]]
elif bal:
    print('🔴 BALANCE CHECK FAILED (install node for a real parser check):')
    [print('   ❌ '+p) for p in bal[:10]]
else:
    print('🟢 all %d script blocks balanced%s'%(len(blocks),' · node --check passed' if node_bin else ''))

if fatal:
    print('')
    print('💥💥💥  FILE NOT WRITTEN — shipping this would give you a blank page  💥💥💥')
    print('👉 paste this whole terminal output back to me — one round trip, fixed')
    sys.exit(1)

io.open(P,'w',encoding='utf-8').write(s)
print('')
print('✅ PATCHED:')
[print('   ✅ '+a) for a in applied]
if skipped:
    print('⚠️  SKIPPED (harmless — anchor already applied or absent):')
    [print('   ⚠️  '+k) for k in skipped]
print('')
print('💾 written → overly/test-8.html  (%d → %d lines)'%(orig.count('\n'),s.count('\n')))
print('')
print('➡️  NOW OPEN:  overly/test-8.html?safe=1')
print('    ⚡ pill flashes <1s on load · 💥 red banner = paste it to me')

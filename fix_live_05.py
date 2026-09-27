import io,os,sys
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'overlay','live.html')
if not os.path.exists(P) or os.path.getsize(P)==0:
    print('💥 overlay/live.html missing/empty');sys.exit(1)
s=io.open(P,encoding='utf-8').read();orig=s
BAD="curStage=null;sync()}}});"   # orphan brace: if-opener removed, closer kept
GOOD="curStage=null;sync()}});"
if BAD in s:
    s=s.replace(BAD,GOOD,1);print('✅ FIXED: orphan brace removed (money-button handler)')
elif GOOD in s:
    print('⚠️ already fixed')
else:
    print('❌ anchor not found — paste me the file around ctlCur');sys.exit(1)
if s!=orig:
    try:data=s.encode('utf-8')
    except UnicodeEncodeError as e:
        print('💥 encode fail — file untouched: '+str(e));sys.exit(1)
    tmp=P+'.tmp'
    with io.open(tmp,'wb') as f:f.write(data)
    os.replace(tmp,P)
    print('💾 written atomically')

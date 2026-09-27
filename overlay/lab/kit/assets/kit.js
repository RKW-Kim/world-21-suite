/* ═══════════════════════════════════════════════════════════════
   SMILE KIT — SPINE ENGINE · v1
   URL contract (every scene page):
     ?v=a|b|c|d|e|f    style lane (a=obsidian glass · b=apple ·
                       c=tradify · d=broadcast · e=editorial · f=kinetic)
     ?t=obsidian|frost|chameleon   material override (lane a)
     ?cd=300           countdown seconds (mm:ss / hh:mm:ss string ok)
     ?title=…&sub=…    override the scene headline / subline
     ?ep=12            episode tag for the show badge
     ?bg=bright|dark|chart|wash   preview backdrop behind the scene
     ?g=1              judge mode — HUD off
     ?obs=1            OBS: transparent page, HUD off, no chrome
     ?wm=0|tl|tr|bl|br watermark off / position (default tl)
   Keys:  V next lane · 1-6 direct lane · G judge
   ═══════════════════════════════════════════════════════════════ */
(function(){
'use strict';
var Q=new URLSearchParams(location.search);
var LANES=['a','b','c','d','e','f'];
var MATS=['obsidian','frost','chameleon'];
var WMS=['0','off','tl','tr','bl','br'];

/* ── state ── */
var S={
  v: (LANES.indexOf(Q.get('v'))>=0?Q.get('v'):'a'),
  g: Q.get('g')==='1',
  obs: Q.get('obs')==='1',
  wm: (WMS.indexOf(Q.get('wm'))>=0?Q.get('wm'):'tl'),
  cd: Q.get('cd')||null
};
window.KIT=S;

/* ── body flags ── */
function applyV(){document.body.dataset.v=S.v}
applyV();
if(S.g)document.body.classList.add('g');
if(S.obs){document.body.classList.add('obs');document.body.classList.add('g')}

/* ── unit scale: 1080 design height → viewport, clamped ── */
function unit(){
  var h=Math.min(innerHeight,innerWidth*9/16);
  document.documentElement.style.setProperty('--u',(h/1080)+'px');
}
addEventListener('resize',unit,{passive:true});unit();

/* ── HUD ── */
var hud=document.createElement('div');hud.className='kit-hud';
hud.innerHTML='<span class="hud-v">'+S.v+'</span>'+
  '<span class="hud-hint">V lane · 1-6 direct · G judge</span>';
if(!S.g)document.body.appendChild(hud);

/* ── keyboard ── */
addEventListener('keydown',function(e){
  var k=e.key.toLowerCase();
  if(k==='v'){S.v=LANES[(LANES.indexOf(S.v)+1)%LANES.length];applyV();
    var m=hud.querySelector('.hud-v');if(m)m.textContent=S.v;
    document.dispatchEvent(new CustomEvent('kit:lane',{detail:S.v}));}
  else if('123456'.indexOf(k)>=0){S.v=LANES[+k-1];applyV();
    var m2=hud.querySelector('.hud-v');if(m2)m2.textContent=S.v;
    document.dispatchEvent(new CustomEvent('kit:lane',{detail:S.v}));}
  else if(k==='g'){S.g=!S.g;document.body.classList.toggle('g',S.g);}
});

/* ── watermark positioning (kit.css renders tl/tr/bl/br) ── */
onReady(function(){
  if(document.querySelector('.kit-ticker'))document.body.classList.add('has-ticker');
  var wms=document.querySelectorAll('.kit-wm');
  wms.forEach(function(w){
    if(S.wm==='0'||S.wm==='off'){w.style.display='none';return}
    w.dataset.pos=S.wm;
  });
  /* headline overrides — data-t / data-sub hooks */
  var ti=Q.get('title'),su=Q.get('sub'),ep=Q.get('ep');
  if(ti)document.querySelectorAll('[data-t]').forEach(function(n){n.textContent=ti});
  if(su)document.querySelectorAll('[data-sub]').forEach(function(n){n.textContent=su});
  if(ep)document.querySelectorAll('[data-ep]').forEach(function(n){
    n.textContent='EP '+ep.replace(/^ep/i,'');});
});

/* ── countdown engine — monotonic, tab-safe, no drift ── */
var CD_MAX=359999; /* 99:59:59 — nothing longer is a countdown */
function parseCD(v){
  if(v===null||v==='')return null;
  if(/^\d+$/.test(v))return Math.min(+v,CD_MAX);
  if(!/^\d{1,3}(:\d{1,2}){0,2}$/.test(v))return null; /* rejects '5:' '1:2:3:4' */
  var p=v.split(':').map(Number);if(p.some(isNaN))return null;
  var s=p.length===3?p[0]*3600+p[1]*60+p[2]:p[0]*60+p[1];
  return Math.min(s,CD_MAX);
}
function onReady(fn){
  if(document.readyState==='loading')addEventListener('DOMContentLoaded',fn);
  else fn();
}
function fmt(t){
  var h=Math.floor(t/3600),m=Math.floor(t%3600/60),s=t%60,pp=function(n){return (n<10?'0':'')+n};
  return h>0? h+':'+pp(m)+':'+pp(s) : m+':'+pp(s);
}
var total=parseCD(S.cd);
onReady(function(){
  document.querySelectorAll('.cd').forEach(function(el){
    var base=total!==null?total:parseCD(el.dataset.cd||el.textContent.trim())||0;
    var t0=performance.now(),last=-1;
    function tick(now){
      var left=Math.max(0,Math.ceil(base-(now-t0)/1000));
      if(left!==last){last=left;
        el.innerHTML=fmt(left).replace(/:/g,'<span class="sep">:</span>');
        el.dataset.done=left===0?'1':'0';
        if(left===0){el.dispatchEvent(new CustomEvent('cd:done',{bubbles:true}));return}
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});

/* ── ticker filler — [logo, prices, socials] merged-ticker law ── */
window.kitTicker=function(root,items){
  var tr=root.querySelector('.tk-track');
  if(!tr)return;
  var html=items.map(function(it){
    if(it.logo)return '<img src="'+it.logo+'" alt="">';
    if(it.gap)return '<span class="tk-item"><span class="k">'+it.gap+'</span></span>';
    return '<span class="tk-item '+(it.dir||'')+'"><span class="k">'+it.k+
      '</span><span class="v">'+it.v+'</span></span>';
  }).join('');
  tr.innerHTML=html+html; /* double track → seamless -50% loop */
};

/* ── material override for lane A glass — spine-level, all pages ── */
onReady(function(){
  var t=Q.get('t');
  if(t&&MATS.indexOf(t)>=0&&document.querySelector('.lg')){ /* unknown t → keep authored default */
    document.querySelectorAll('.lg').forEach(function(el){
      el.classList.remove('lg--obsidian','lg--frost','lg--chameleon');
      el.classList.add('lg--'+t);
    });
  }
});
})();

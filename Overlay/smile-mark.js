(function(){
  const EYES  = '<circle class="eye-l" cx="31" cy="35" r="5.5"/><circle class="eye-r" cx="69" cy="35" r="5.5"/>';
  const MOUTH = '<path class="mouth" d="M 20 48 A 30 30 0 0 0 80 48"/>';
  const INNER = '<circle cx="50" cy="50" r="48" fill="#FFC800"/><g class="eyes">' + EYES + '</g>' + MOUTH;
  const FACE  = '<g class="eyes">' + EYES + '</g>' + MOUTH;
  const css = `
  .smile-anim .eye-l,.smile-anim .eye-r{transform-box:fill-box;transform-origin:center;transition:transform .12s ease;fill:#000000}
  .smile-anim .mouth{transform-box:fill-box;transform-origin:50% 60%;transition:transform .18s ease;fill:none;stroke:#000000;stroke-width:7.5 !important;stroke-linecap:round;stroke-linejoin:round}
  .face-svg .mouth{transform:none !important}
  .face>svg.face-svg{position:absolute;inset:0;width:100%;height:100%}
  .smile-anim.is-blink .eye-l,.smile-anim.is-blink .eye-r{transform:scaleY(.08)}
  .smile-anim.wink .eye-r{transform:scaleY(.08)}
  .smile-anim.smirk .eye-r{transform:scaleY(.55) translateY(10%)} .smile-anim.smirk .mouth{transform:rotate(-7deg) translateX(6%)} .smile-anim.smirk .eye-l{transform:translateY(-6%)}
  .smile-anim.look .eye-l,.smile-anim.look .eye-r{transform:translateX(22%)}
  .smile-anim.nod{animation:sm-nod .8s ease} .smile-anim.spin{animation:sm-spin 1s cubic-bezier(.6,.05,.3,1)}
  .smile-anim.bounce{animation:sm-bounce 1s cubic-bezier(.3,1.5,.5,1)} .smile-anim.celebrate{animation:sm-cel .9s ease} .smile-anim.shake{animation:sm-shake .5s ease}
  @keyframes sm-nod{0%,100%{transform:translateY(0)}30%{transform:translateY(7%)}60%{transform:translateY(2%)}}
  @keyframes sm-spin{to{transform:rotate(360deg)}}
  @keyframes sm-bounce{0%,100%{transform:translateY(0)}25%{transform:translateY(-16%) scaleY(1.06)}55%{transform:translateY(0) scaleY(.94)}75%{transform:translateY(-6%)}}
  @keyframes sm-cel{0%,100%{transform:rotate(0) scale(1)}20%{transform:rotate(-9deg) scale(1.12)}45%{transform:rotate(8deg) scale(1.12)}70%{transform:rotate(-4deg)}}
  @keyframes sm-shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-6%)}40%{transform:translateX(6%)}60%{transform:translateX(-4%)}80%{transform:translateX(4%)}}`;

  const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
  const reg=[];
  const moodOf=el=>el.getAttribute('data-mood')||(el.closest&&el.closest('[data-mood]')&&el.closest('[data-mood]').getAttribute('data-mood'))||'';

  function upgrade(el){
    if(!el||!el.isConnected)return;let a;
    if(el.matches('.face')){el.innerHTML='<svg class="face-svg smile-anim" viewBox="0 0 100 100">'+FACE+'</svg>';a=el.querySelector('svg');}
    else if(el.matches('svg.disc')){const ex=(el.getAttribute('class')||'').replace(/\bdisc\b/,'').replace('smile-anim','').trim();el.setAttribute('class','disc smile-anim '+ex);el.innerHTML=INNER;a=el;}
    else{el.innerHTML='<svg class="disc smile-anim" viewBox="0 0 100 100">'+INNER+'</svg>';a=el.querySelector('svg');}
    if(!a)return;const m=moodOf(el)||moodOf(a);if(m){a.classList.add(m);a.dataset.locked='1';}reg.push(a);
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.brand .dw, svg.disc, .face').forEach(upgrade);
  });
  if(document.readyState !== 'loading') document.querySelectorAll('.brand .dw, svg.disc, .face').forEach(upgrade);

  function idle(){
    const free=reg.filter(a=>!a.dataset.locked&&!a.classList.contains('is-blink'));
    if(free.length){
      const a=free[Math.floor(Math.random()*free.length)];
      a.classList.add('is-blink');
      setTimeout(()=>a.classList.remove('is-blink'),150);
      if(Math.random()<.22)setTimeout(()=>{a.classList.add('look');setTimeout(()=>a.classList.remove('look'),480);},220);
    }
    setTimeout(idle,2600+Math.random()*3200);
  }
  setTimeout(idle,1500);

  window.smileMood=function(mood,ms,target){
    ms=ms||900;
    reg.forEach(a=>{if(a.dataset.locked||(target&&a!==target))return;a.classList.add(mood);setTimeout(()=>a.classList.remove(mood),ms);});
  };

  function applyBrand(b){
    if(!b)return;
    if(b.tokens){const r=document.documentElement.style;for(const k in b.tokens)r.setProperty(k,b.tokens[k]);}
    if(b.wordmark)document.querySelectorAll('.brand b').forEach(el=>{if(!el.dataset.brandLocked)el.textContent=b.wordmark;});
  }

  (function loadBrand(){
    if(window.BRAND){applyBrand(window.BRAND);return;}
    fetch('brand.json').then(r=>r.ok?r.json():null).then(applyBrand).catch(()=>{});
  })();
})();
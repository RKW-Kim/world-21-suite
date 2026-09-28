/* SMILE · shared runtime — include in every source (after smile-mark.js where used) */
window.SMILE = (function(){
  var q = new URLSearchParams(location.search);

  function setU(){
    var u = Math.min(window.innerWidth/1920, window.innerHeight/1080) || 1;
    document.documentElement.style.setProperty('--u', u + 'px');
  }
  var resizeTimer;
  window.addEventListener('resize', function(){
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(setU, 100);
  });
  setU();

  function param(k, def){ var v = q.get(k); return (v === null || v === '') ? def : v; }
  function cssVar(k, def){
    var v = getComputedStyle(document.documentElement).getPropertyValue(k).trim();
    return v || def;
  }
  /* priority: URL param > OBS Custom CSS variable > default */
  function opt(name, def){
    var p = param(name, null);
    return p !== null ? p : cssVar('--' + name, def);
  }

  /* FIXED: mount sets vars on element, not on :root */
  function mount(el, o){
    o = o || {};
    var corner = opt('corner', o.corner || 'tl');
    var mx = parseFloat(opt('mx', o.mx != null ? o.mx : 44));
    var my = parseFloat(opt('my', o.my != null ? o.my : 30));
    var sc = parseFloat(opt('scale', o.scale != null ? o.scale : 1));
    if(isNaN(mx)) mx = 44;
    if(isNaN(my)) my = 30;
    if(isNaN(sc)) sc = 1;
    el.style.setProperty('--mx', mx);
    el.style.setProperty('--my', my);
    el.style.setProperty('--scale', sc);
    el.classList.remove('pos-tl','pos-tr','pos-bl','pos-br');
    el.classList.add('anchor', 'pos-' + corner);
  }

  /* polls state.json — edit ONE file, every source updates live */
  function watchState(cb, ms){
    var last = '';
    function pull(){
      fetch('state.json?t=' + Date.now(), {cache:'no-store'})
        .then(function(r){ return r.ok ? r.text() : null; })
        .then(function(txt){
          if (txt && txt !== last){
            last = txt;
            try{ cb(JSON.parse(txt)); }catch(e){ console.warn('state.json parse error', e); }
          }
        }).catch(function(){});
    }
    pull();
    setInterval(pull, ms || 3000);
  }

  function esc(s){ return String(s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

  return { param:param, cssVar:cssVar, opt:opt, mount:mount, watchState:watchState, esc:esc, setU:setU };
})();

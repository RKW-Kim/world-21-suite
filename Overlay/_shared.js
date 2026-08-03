/* SMILE · shared runtime — include in every source (after smile-mark.js where used) */
window.SMILE = (function(){
  var q = new URLSearchParams(location.search);

  function setU(){
    var u = Math.min(innerWidth/1920, innerHeight/1080);
    document.documentElement.style.setProperty('--u', u + 'px');
  }
  addEventListener('resize', setU); setU();

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

  /* mount(el, {corner,mx,my,scale}) — positions any .anchor */
  function mount(el, o){
    var corner = opt('corner', o.corner);
    var mx = parseFloat(opt('mx', o.mx));
    var my = parseFloat(opt('my', o.my));
    var sc = parseFloat(opt('scale', o.scale));
    var r = document.documentElement.style;
    r.setProperty('--mx', mx); r.setProperty('--my', my); r.setProperty('--scale', sc);
    el.classList.add('anchor', 'pos-' + corner);
  }

  /* polls state.json — edit ONE file, every source updates live */
  function watchState(cb, ms){
    var last = '';
    function pull(){
      fetch('state.json?t=' + Date.now())
        .then(function(r){ return r.ok ? r.text() : null; })
        .then(function(txt){
          if (txt && txt !== last){ last = txt; try{ cb(JSON.parse(txt)); }catch(e){} }
        }).catch(function(){});
    }
    pull(); setInterval(pull, ms || 3000);
  }

  function esc(s){ return String(s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

  return { param:param, cssVar:cssVar, opt:opt, mount:mount, watchState:watchState, esc:esc };
})();

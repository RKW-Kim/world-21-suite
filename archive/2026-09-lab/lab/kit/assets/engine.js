/* ============================================================
   SMILE KIT — engine.js · shared scene runtime
   URL contract: ?v=a..d · ?t=<sec|datetime> · ?ep= · ?title= ·
   ?sub= · ?g=1 (hide help) · ?obs=1 (hide chrome)
   Keys: V cycles takes · 1-4 direct · H toggles help
   Helpers: kitDigits(el, str) rolling split-flap digits ·
            kitRing(circleEl, frac) SVG progress ring
   ============================================================ */
(function () {
  var q = new URLSearchParams(location.search);

  /* ---- take gate ---- */
  var v = (q.get('v') || 'a').toLowerCase();
  if ('abcd'.indexOf(v) < 0) v = 'a';
  document.body.setAttribute('data-v', v);
  window.kitTake = v;

  /* ---- chrome flags ---- */
  if (q.get('g') === '1') document.documentElement.classList.add('kit-noguide');
  if (q.get('obs') === '1') { document.documentElement.classList.add('kit-obs'); document.body && document.body.classList.add('kit-obs'); }

  /* ---- text overrides ---- */
  var eps = q.get('ep') || '128';
  function applyOverrides() {
    document.querySelectorAll('[data-ep]').forEach(function (e) { e.textContent = eps; });
    var tt = q.get('title');
    if (tt) document.querySelectorAll('[data-title]').forEach(function (e) { e.textContent = tt; });
    var sb = q.get('sub');
    if (sb) document.querySelectorAll('[data-sub]').forEach(function (e) { e.textContent = sb; });
  }
  if (document.readyState !== 'loading') applyOverrides();
  else document.addEventListener('DOMContentLoaded', applyOverrides);

  /* ---- countdown target ---- */
  function P(n) { return String(n).padStart(2, '0'); }
  var tp = q.get('t'), target = null;
  if (tp) {
    if (/^\d+$/.test(tp)) target = Date.now() + parseInt(tp, 10) * 1000;
    else { var d = new Date(tp); if (!isNaN(d.getTime())) target = d.getTime(); }
  }
  if (target === null) target = Date.now() + 600000;
  var total = Math.max(1000, target - Date.now());
  window.kitCountdown = function () { return Math.max(0, Math.round((target - Date.now()) / 1000)); };
  window.kitFrac = function () { return Math.max(0, Math.min(1, (target - Date.now()) / total)); };
  window.kitFmt = function () {
    var s = window.kitCountdown();
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    return (h > 0 ? P(h) + ':' : '') + P(m) + ':' + P(x);
  };
  window.kitDone = function () { return window.kitCountdown() <= 0; };

  /* ---- rolling digits: rebuild cells on length change, roll the GLYPH inside the cell ---- */
  window.kitDigits = function (root, str) {
    if (!root) return;
    if (root.dataset.n !== String(str.length)) {
      root.dataset.n = String(str.length);
      root.innerHTML = '';
      for (var i = 0; i < str.length; i++) {
        var c = document.createElement('span');
        var ch = str[i];
        if (ch === ':' || ch === ' ') { c.className = 'dgt sep'; }
        else { c.className = 'dgt'; }
        var g = document.createElement('i');
        g.textContent = ch;
        c.appendChild(g);
        root.appendChild(c);
      }
      return;
    }
    var cells = root.querySelectorAll('.dgt');
    for (var j = 0; j < str.length; j++) {
      var el = cells[j];
      if (!el) continue;
      var g2 = el.firstChild;
      if (g2 && g2.textContent === str[j]) continue;
      if (g2) g2.textContent = str[j];
      el.classList.remove('roll');
      void el.offsetWidth;
      el.classList.add('roll');
    }
  };

  /* ---- svg progress ring ---- */
  window.kitRing = function (circle, frac) {
    if (!circle) return;
    var r = circle.r.baseVal.value;
    var C = 2 * Math.PI * r;
    circle.style.strokeDasharray = C;
    circle.style.strokeDashoffset = C * (1 - frac);
  };

  /* ---- EAT clock ---- */
  function tickClock() {
    var t = new Date().toLocaleTimeString('en-KE', { timeZone: 'Africa/Nairobi', hour: '2-digit', minute: '2-digit', hour12: false });
    document.querySelectorAll('[data-clock]').forEach(function (e) { e.textContent = t; });
  }
  if (document.readyState !== 'loading') tickClock();
  else document.addEventListener('DOMContentLoaded', tickClock);
  setInterval(tickClock, 10000);

  /* ---- countdown master tick: default wiring for [data-cd] ---- */
  var celebrated = false;
  function tick() {
    var str = window.kitFmt();
    document.querySelectorAll('[data-cd]').forEach(function (e) {
      if (e.dataset.digits !== undefined) window.kitDigits(e, str);
      else e.textContent = str;
    });
    document.querySelectorAll('[data-ring]').forEach(function (c) { window.kitRing(c, window.kitFrac()); });
    if (window.kitDone()) {
      document.querySelectorAll('[data-when-live]').forEach(function (e) { e.removeAttribute('hidden'); });
      document.querySelectorAll('[data-cd-wrap]').forEach(function (e) { e.setAttribute('data-done', '1'); });
      if (!celebrated && window.smileMood) { window.smileMood('celebrate', 1200); celebrated = true; }
    }
  }
  if (document.readyState !== 'loading') tick();
  else document.addEventListener('DOMContentLoaded', tick);
  setInterval(tick, 250);

  /* ---- keys + help ---- */
  function withTake(nv) {
    var p = new URLSearchParams(location.search);
    p.set('v', nv);
    return '?' + p.toString();
  }
  var takes = ['a', 'b', 'c', 'd'];
  document.addEventListener('keydown', function (ev) {
    var k = ev.key.toLowerCase();
    if (k === 'v') {
      var i = takes.indexOf(document.body.getAttribute('data-v'));
      location.search = withTake(takes[(i + 1) % takes.length]);
    } else if ('1234'.indexOf(k) >= 0) {
      location.search = withTake(takes[parseInt(k, 10) - 1]);
    } else if (k === 'h') {
      document.documentElement.classList.toggle('kit-noguide');
    }
  });
})();

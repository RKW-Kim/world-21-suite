/* ============================================================
   SMILE KIT — logo.js  ·  the REAL smile logo, no placeholder
   Face paths are BYTE-VERBATIM from assets/smile-icon.svg
   (verbatim crop of the official Smile-Logo.svg, zero redraw).
   Only change: paths are wrapped in <g class="eyes"> / mouth
   class hooks so the mood system can animate them with CSS
   transforms. The drawing itself is never altered.
   ============================================================ */
(function () {
  /* --- verbatim geometry from smile-icon.svg / smile-face.svg --- */
  var P_FACE  = 'm16.8 11c-5.8 0-11.4 4.5-11.2 11.7 0.1 6.2 4.5 11.5 11.4 11.6 6.4 0 12-4.7 12.1-11.5-0.2-6.6-5.2-11.8-12.3-11.8z';
  var P_EYE_L = 'm12.3 17.2c-0.7 0-1.3 0.6-1.3 1.3s0.6 1.3 1.3 1.3 1.3-0.6 1.3-1.3c0.1-0.6-0.5-1.3-1.3-1.3z';
  var P_EYE_R = 'm22.3 17.2c-0.7 0-1.4 0.6-1.4 1.4 0 0.7 0.7 1.3 1.4 1.3s1.3-0.6 1.3-1.3c0-0.8-0.6-1.4-1.3-1.4z';
  var P_MOUTH = 'm24.5 22.4c-0.4 0-0.6 0.5-0.6 1-0.3 3.5-3 6.1-6.7 6.1s-6.5-2.5-6.8-6.2c-0.1-0.4-0.4-0.8-0.7-0.8s-0.9 0.3-0.8 1c0.5 3.8 3.2 7.5 8.3 7.5 5.2-0.1 8-3.8 8.3-7.8 0.1-0.6-0.4-1-1-0.8z';
  var FILL_FACE = '#ffd100', FILL_INK = '#0A0900';
  var VB = '5 10.8 23.8 23.8';

  /* icon-only face; fills overridable via CSS vars --sm-face / --sm-ink */
  function faceSVG(cls) {
    return '<svg class="sm-face' + (cls ? ' ' + cls : '') + '" viewBox="' + VB + '" aria-hidden="true">' +
      '<path class="sm-head" d="' + P_FACE + '" fill="var(--sm-face,' + FILL_FACE + ')"/>' +
      '<g class="sm-eyes">' +
        '<path class="sm-eye sm-eye-l" d="' + P_EYE_L + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
        '<path class="sm-eye sm-eye-r" d="' + P_EYE_R + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
      '</g>' +
      '<path class="sm-mouth" d="' + P_MOUTH + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
    '</svg>';
  }

  /* full lockup: ALL paths byte-verbatim from smile-logo.svg, native coords */
  var P_WORD1 = 'm46.9 18-6 0.7c-0.3-0.7-0.4-1.7-1.7-1.7-0.9 0-1.4 0.6-1.4 1.5s0.4 1.1 2.2 1.2c3.9 0.2 7.9 1.3 7.9 5.3 0 3.7-3.9 5.3-8.8 5.3-4.8 0-8.2-1.3-8.6-4.6l6.1-0.8c0.3 0.9 0.7 2.4 2.5 2.4 1.3 0 2.3-0.4 2.3-1.5 0-1.2-0.7-1.6-2.6-1.8-3.8-0.4-7.8-1.1-7.8-5.1 0-3.7 4.1-5 8.1-5 3.9 0 6.9 0.7 7.9 4';
  var P_WORD2 = 'm70.7 14.6c0.9-0.4 1.9-0.6 3.1-0.6 3.2 0 5.5 1.5 5.5 5.6v10.7h-6.4v-10.4c-0.5-0.7-1-1.3-1.9-1.3-1.3 0-2.4 0.8-2.7 2.6v9.1h-6.3v-10.4c-0.4-0.6-1-1.2-1.9-1.3-1.3 0-2.4 0.7-2.7 2.6v9.1h-6.5v-16.3h5.9v2.2h0.2c1.4-1.4 3.2-2.2 5.7-2.3 1.9-0.1 3.9 0.7 4.9 2.3h0.4c0.9-0.7 1.7-1.3 2.7-1.6';
  var P_WORD3 = 'm83.5 13.9h6.2v16.4h-6.2v-16.4zm0-6.4h6.2v4.1h-6.3l0.1-4.1z';
  var P_WORD4 = 'm112.1 17.7c-1.7-0.1-2.9 1-3 2.5h6.2c-0.2-1.6-1.3-2.4-3.2-2.5m3.3 7.1 6.7 0.9c-1.3 2.5-3.7 4.6-9 4.6-4.8 0-9.5-1.7-9.5-8.1 0-3.2 1.8-8.3 9.2-8.2 7.8 0 9.3 4.4 9.3 9.1h-12.7c0 1.8 1.4 3.4 3.2 3.3 1.4 0 2.5-0.6 2.8-1.6';
  function wordSVG(cls) {
    return '<svg class="sm-word' + (cls ? ' ' + cls : '') + '" viewBox="5 7.4 118 28" aria-label="smile">' +
      '<g fill="var(--sm-word,#E6E6E6)">' +
        '<path d="' + P_WORD1 + '"/><path d="' + P_WORD2 + '"/><path d="' + P_WORD3 + '"/>' +
        /* the "l" — verbatim <polygon> from smile-logo.svg */
        '<polygon points="93.8 7.5 100.4 7.5 100.4 30.3 93.8 30.3"/>' +
        '<path d="' + P_WORD4 + '"/>' +
      '</g>' +
      '<path d="' + P_FACE + '" fill="var(--sm-face,' + FILL_FACE + ')"/>' +
      '<g class="sm-eyes">' +
        '<path d="' + P_EYE_L + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
        '<path d="' + P_EYE_R + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
      '</g>' +
      '<path d="' + P_MOUTH + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
    '</svg>';
  }

  var css = ''
    /* geometry & mood plumbing */
    + '.sm-face{display:block;width:100%;height:100%;overflow:visible}'
    + '.sm-face .sm-eyes,.sm-face .sm-eye,.sm-face .sm-mouth{transform-box:fill-box;transform-origin:center;transition:transform .14s ease}'
    /* moods (transform-only, never redraw) */
    + '.sm-mood-blink .sm-eyes{transform:scaleY(.08)}'
    + '.sm-mood-wink .sm-eye-r{transform:scaleY(.08)}'
    + '.sm-mood-look .sm-eyes{transform:translateX(18%)}'
    + '.sm-mood-look-l .sm-eyes{transform:translateX(-18%)}'
    + '.sm-mood-nod{animation:sm-nod .8s ease}'
    + '.sm-mood-bounce{animation:sm-bounce 1s cubic-bezier(.3,1.5,.5,1)}'
    + '.sm-mood-celebrate{animation:sm-cel .9s ease}'
    + '.sm-mood-shake{animation:sm-shake .5s ease}'
    + '.sm-mood-tilt .sm-face{transform:rotate(-6deg)}'
    + '@keyframes sm-nod{0%,100%{transform:translateY(0)}30%{transform:translateY(7%)}60%{transform:translateY(2%)}}'
    + '@keyframes sm-bounce{0%,100%{transform:translateY(0)}25%{transform:translateY(-16%) scaleY(1.06)}55%{transform:translateY(0) scaleY(.94)}75%{transform:translateY(-6%)}}'
    + '@keyframes sm-cel{0%,100%{transform:rotate(0) scale(1)}20%{transform:rotate(-8deg) scale(1.1)}45%{transform:rotate(7deg) scale(1.1)}70%{transform:rotate(-3deg)}}'
    + '@keyframes sm-shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-6%)}40%{transform:translateX(6%)}60%{transform:translateX(-4%)}80%{transform:translateX(4%)}}'
    + '@media (prefers-reduced-motion:reduce){.sm-mood-nod,.sm-mood-bounce,.sm-mood-celebrate,.sm-mood-shake{animation:none}}';

  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var reg = [];

  function upgrade(el) {
    if (!el || !el.isConnected) return;
    var svg;
    if (el.classList.contains('sm-slot') || el.classList.contains('face')) {
      el.innerHTML = faceSVG('sm-live');
      svg = el.querySelector('svg');
      if (el.classList.contains('face') && !el.getAttribute('data-keep-size')) {
        /* .face containers keep their own box; svg fills it */
      }
    } else if (el.tagName === 'svg' && el.classList.contains('disc')) {
      var ex = (el.getAttribute('class') || '').replace(/\bdisc\b/, '').trim();
      el.setAttribute('class', ('disc ' + ex).trim());
      el.setAttribute('viewBox', VB);
      el.innerHTML = '<path class="sm-head" d="' + P_FACE + '" fill="var(--sm-face,' + FILL_FACE + ')"/>' +
        '<g class="sm-eyes">' +
          '<path class="sm-eye sm-eye-l" d="' + P_EYE_L + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
          '<path class="sm-eye sm-eye-r" d="' + P_EYE_R + '" fill="var(--sm-ink,' + FILL_INK + ')"/>' +
        '</g>' +
        '<path class="sm-mouth" d="' + P_MOUTH + '" fill="var(--sm-ink,' + FILL_INK + ')"/>';
      svg = el;
    } else if (el.classList.contains('logo-full')) {
      el.innerHTML = wordSVG('');
      return; /* wordmark lockups don't join the mood registry */
    } else { return; }
    if (!svg) return;
    var m = el.getAttribute('data-mood') || '';
    if (m) { svg.classList.add('sm-mood-' + m); svg.dataset.locked = '1'; }
    reg.push(svg);
  }

  function boot() {
    document.querySelectorAll('.face, svg.disc, .sm-slot, .logo-full:not([data-ready])').forEach(function (el) {
      if (el.classList.contains('logo-full')) { if (el.getAttribute('data-ready')) return; el.setAttribute('data-ready', '1'); }
      upgrade(el);
    });
  }
  document.addEventListener('DOMContentLoaded', boot);
  if (document.readyState !== 'loading') boot();

  /* idle life: blinks + occasional glances — the character stays alive */
  function idle() {
    var free = reg.filter(function (s) { return !s.dataset.locked && !s.classList.contains('sm-mood-blink'); });
    if (free.length) {
      var s = free[Math.floor(Math.random() * free.length)];
      s.classList.add('sm-mood-blink');
      setTimeout(function () { s.classList.remove('sm-mood-blink'); }, 150);
      if (Math.random() < .22) setTimeout(function () {
        var look = Math.random() < .5 ? 'sm-mood-look' : 'sm-mood-look-l';
        s.classList.add(look); setTimeout(function () { s.classList.remove(look); }, 480);
      }, 220);
    }
    setTimeout(idle, 2600 + Math.random() * 3200);
  }
  setTimeout(idle, 1500);

  /* public: smileMood('wink'|'nod'|'bounce'|'celebrate'|'shake'|'look'|'look-l', ms, targetEl) */
  window.smileMood = function (mood, ms, target) {
    ms = ms || 900;
    reg.forEach(function (s) {
      if (s.dataset.locked || (target && s !== target)) return;
      s.classList.add('sm-mood-' + mood);
      setTimeout(function () { s.classList.remove('sm-mood-' + mood); }, ms);
    });
  };
  /* public: smileMoodAt(el, mood, ms) — fire at one instance */
  window.smileMoodAt = function (el, mood, ms) {
    var s = el && (el.tagName === 'svg' ? el : el.querySelector('svg.sm-face'));
    if (!s) return; s.classList.add('sm-mood-' + mood);
    setTimeout(function () { s.classList.remove('sm-mood-' + mood); }, ms || 900);
  };
})();

/* ============================================================
   LIQUID GLASS CORE JS — world-21-suite stingers
   Port of nikdelvin/liquid-glass displacement technique:
   neutral-grey map, edge-only gradients, triple feDisplacementMap
   with chromatic aberration, applied via backdrop-filter url().
   API:
     LG.glass(el, opts) -> {refresh}
       opts: radius, depth(12), strength(72), ca(1.6), blur(1.5),
             theme('clear'|'obsidian'), saturate(1.7), brightness(1.08)
     LG.filter(o) -> dataURI svg filter (advanced use)
   ============================================================ */
var LG = (function () {

  function displacementMap(o) {
    var w = o.width, h = o.height, r = o.radius, d = o.depth;
    var yIn = Math.ceil((r / Math.max(h, 1)) * 15);
    var xIn = Math.ceil((r / Math.max(w, 1)) * 15);
    var svg =
      '<svg height="' + h + '" width="' + w + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">' +
      '<style>.mix{mix-blend-mode:screen;}</style>' +
      '<defs>' +
      '<linearGradient id="Y" x1="0" x2="0" y1="' + yIn + '%" y2="' + Math.floor(100 - yIn) + '%">' +
      '<stop offset="0%" stop-color="#0F0"/><stop offset="100%" stop-color="#000"/></linearGradient>' +
      '<linearGradient id="X" x1="' + xIn + '%" x2="' + Math.floor(100 - xIn) + '%" y1="0" y2="0">' +
      '<stop offset="0%" stop-color="#F00"/><stop offset="100%" stop-color="#000"/></linearGradient>' +
      '</defs>' +
      '<rect width="' + w + '" height="' + h + '" fill="#808080"/>' +
      '<g filter="blur(2px)">' +
      '<rect width="' + w + '" height="' + h + '" fill="#000080"/>' +
      '<rect width="' + w + '" height="' + h + '" fill="url(#Y)" class="mix"/>' +
      '<rect width="' + w + '" height="' + h + '" fill="url(#X)" class="mix"/>' +
      '<rect x="' + d + '" y="' + d + '" width="' + (w - 2 * d) + '" height="' + (h - 2 * d) +
      '" fill="#808080" rx="' + r + '" ry="' + r + '" filter="blur(' + d + 'px)"/>' +
      '</g></svg>';
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
  }

  function filter(o) {
    var w = o.width, h = o.height, s = o.strength, ca = o.ca || 0;
    var href = displacementMap(o);
    var svg =
      '<svg height="' + h + '" width="' + w + '" viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">' +
      '<defs><filter id="displace" color-interpolation-filters="sRGB" x="0" y="0" width="100%" height="100%">' +
      '<feImage x="0" y="0" width="' + w + '" height="' + h + '" href="' + href + '" result="map"/>' +
      /* blue channel branch (base strength) */
      '<feDisplacementMap in="SourceGraphic" in2="map" scale="' + s + '" xChannelSelector="R" yChannelSelector="G"/>' +
      '<feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="dB"/>' +
      /* green branch (strength + ca) */
      '<feDisplacementMap in="SourceGraphic" in2="map" scale="' + (s + ca) + '" xChannelSelector="R" yChannelSelector="G"/>' +
      '<feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="dG"/>' +
      /* red branch (strength + ca*2) */
      '<feDisplacementMap in="SourceGraphic" in2="map" scale="' + (s + ca * 2) + '" xChannelSelector="R" yChannelSelector="G"/>' +
      '<feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="dR"/>' +
      /* recombine */
      '<feComposite in="dR" in2="dG" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="dRG"/>' +
      '<feComposite in="dRG" in2="dB" operator="arithmetic" k1="0" k2="1" k3="1" k4="0"/>' +
      '</filter></defs></svg>';
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
  }

  var supportsUrl = (function () {
    var t = document.createElement('div');
    t.style.cssText = 'backdrop-filter: url(#test)';
    return t.style.backdropFilter === 'url(#test)' || t.style.backdropFilter === 'url("#test")';
  })();

  /**
   * LG.glass(el, opts) — turns el into a liquid-glass shell.
   * El must have position (css .lg class does that) and its content
   * should live in a child (or children) — they are lifted into .lg-content.
   */
  function glass(el, opts) {
    opts = opts || {};
    var o = {
      depth: opts.depth != null ? opts.depth : 12,
      strength: opts.strength != null ? opts.strength : 72,
      ca: opts.ca != null ? opts.ca : 1.6,
      blur: opts.blur != null ? opts.blur : 1.5,
      theme: opts.theme || 'clear',
      saturate: opts.saturate != null ? opts.saturate : 1.7,
      brightness: opts.brightness != null ? opts.brightness : 1.08
    };
    var theme = o.theme === 'obsidian' ? 'lg--obsidian' : 'lg--clear';

    if (!el.classList.contains('lg')) el.classList.add('lg');
    el.classList.add(theme);

    /* wrap existing children into .lg-content */
    var content = el.querySelector(':scope > .lg-content');
    if (!content) {
      content = document.createElement('div');
      content.className = 'lg-content';
      while (el.firstChild) content.appendChild(el.firstChild);
      el.appendChild(content);
    }

    var bd = document.createElement('div'); bd.className = 'lg-backdrop';
    var tint = document.createElement('div'); tint.className = 'lg-tint';
    var rim = document.createElement('div'); rim.className = 'lg-rim';
    var spec = document.createElement('div'); spec.className = 'lg-spec';
    el.insertBefore(bd, content);
    el.insertBefore(tint, content);
    el.insertBefore(rim, content);
    el.insertBefore(spec, content);

    function apply() {
      var r = el.getBoundingClientRect();
      var w = Math.max(2, Math.round(r.width)), h = Math.max(2, Math.round(r.height));
      var radius = opts.radius != null ? opts.radius
        : (parseFloat(getComputedStyle(el).borderTopLeftRadius) || h / 2);
      if (radius > Math.min(w, h) / 2) radius = Math.min(w, h) / 2;
      var mapO = { width: w, height: h, radius: radius, depth: o.depth, strength: o.strength, ca: o.ca };
      if (supportsUrl) {
        bd.style.backdropFilter =
          'blur(' + (o.blur / 2) + 'px) url("' + LG.filter(mapO) + '")' +
          ' blur(' + o.blur + 'px) brightness(' + o.brightness + ') saturate(' + o.saturate + ')';
        el.classList.remove('nodisp');
      } else {
        el.classList.add('nodisp');
      }
    }
    apply();
    if (window.ResizeObserver) new ResizeObserver(apply).observe(el);
    return { refresh: apply };
  }

  /* round spark factory — 3D money moments
     opts: {color:'#FFCE00', delay:ms, z:index, arc:0..1 (weight vs drift)} */
  function spark(parent, x, y, size, life, opts) {
    opts = opts || {};
    var s = document.createElement('i');
    s.className = 'lg-spark';
    var c = opts.color || '';
    s.style.cssText = 'left:' + x + 'px;top:' + y + 'px;width:' + size + 'px;height:' + size + 'px;' +
      (c ? 'background:radial-gradient(circle at 35% 30%,#FFFFFF,' + c + ' 60%);box-shadow:0 0 10px ' + c + '88;' : '') +
      (opts.z != null ? 'z-index:' + opts.z + ';' : '') +
      (opts.delay ? 'animation-delay:-' + opts.delay + 'ms;' : '');
    parent.appendChild(s);
    var arc = opts.arc != null ? opts.arc : 1;
    var dx = (Math.random() - .5) * (90 - arc * 40), dy = -(20 + arc * 30 + Math.random() * 60);
    var anim = s.animate([
      { transform: 'translate(0,0) scale(.4)', opacity: 0 },
      { transform: 'translate(' + dx * .3 + 'px,' + dy * .55 + 'px) scale(1)', opacity: 1, offset: .3 },
      { transform: 'translate(' + dx + 'px,' + (dy - 20) + 'px) scale(.2)', opacity: 0 }
    ], { duration: life || 950, delay: opts.delay || 0, easing: 'cubic-bezier(.22,.68,.4,1)', fill: 'both' });
    anim.onfinish = function () { s.remove(); };
    return s;
  }

  return { glass: glass, filter: filter, displacementMap: displacementMap, spark: spark, supportsUrl: supportsUrl };
})();

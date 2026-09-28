/* ============================================================
   LIQUID GLASS CORE JS — world-21-suite stingers
   Port of nikdelvin/liquid-glass displacement technique:
   neutral-grey map, edge-only gradients, triple feDisplacementMap
   with chromatic aberration, applied via backdrop-filter url().
   API:
     LG.glass(el, opts) -> {refresh}
       opts: radius, depth(12), strength(72), ca(1.6), blur(1.5),
             theme('frost'|'obsidian'|'chameleon'|'clear'),
             saturate(1.7), brightness(1.08)
     LG.chameleon(el, opts) -> {sample, stop}   (round 7 matte core)
       opts: source (canvas|video el), stage (el mapping 1:1 to source
             px space), interval(420ms), hue, sat — samples the region
             behind the card, drives --ch-h/--ch-s/--ch-e on it.
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
    var THEME_CLASS = {
      clear: 'lg--clear', frost: 'lg--frost', obsidian: 'lg--obsidian', chameleon: 'lg--chameleon'
    };
    var theme = THEME_CLASS[o.theme] || 'lg--clear';
    var matte = (o.theme === 'frost' || o.theme === 'obsidian' || o.theme === 'chameleon');

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
    if (matte) {                    /* matte family: mineral grain over the tint */
      var grain = document.createElement('div'); grain.className = 'lg-grain';
      el.insertBefore(grain, content);
    }

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

  /* ----------------------------------------------------------------
     LG.chameleon(el, opts) — the smart material (round 7).
     Samples the region of `opts.source` (canvas/video element) that
     sits BEHIND `el`, extracts the weighted dominant hue + chroma and
     a motion-energy score, then drives CSS custom properties:
       --ch-h (0-360)  --ch-s (0-100)  --ch-e (0-1)
     The .lg--chameleon theme maps those onto tint/rim/breath, so the
     glass colour and life respond to what's happening behind it.
     opts.source  canvas or <video> element (same-origin pixels)
     opts.stage   element whose client rect maps 1:1 onto source px
                  space (defaults to viewport)
     opts.interval sampling cadence ms (default 420)
     opts.hue/opts.sat  initial/fallback values
     Returns { sample, stop }.
     NOTE: in OBS the browser source cannot see the video behind it —
     ship ?tint=h,s pages there; in-lab this runs for real.
     ---------------------------------------------------------------- */
  function chameleon(el, opts) {
    opts = opts || {};
    var src = opts.source;
    var stage = opts.stage || null;
    var SW = opts.sourceWidth || 1920, SH = opts.sourceHeight || 1080;
    var box = document.createElement('canvas');
    box.width = 32; box.height = 18;
    var bctx = box.getContext('2d', { willReadFrequently: true });
    var prev = null;
    var cur = { h: opts.hue != null ? opts.hue : 224, s: opts.sat != null ? opts.sat : 22, e: 0 };
    var tgt = { h: cur.h, s: cur.s, e: 0 };
    var running = true, lastErr = 0;

    function sampleRegion() {
      if (!src || !running) return;
      var r = el.getBoundingClientRect();
      var stageW = stage ? stage.clientWidth : (window.innerWidth || SW);
      var stageH = stage ? stage.clientHeight : (window.innerHeight || SH);
      var sx = SW / Math.max(stageW, 1), sy = SH / Math.max(stageH, 1);
      var x = r.left * sx, y = r.top * sy;
      var w = Math.max(6, r.width * sx), h = Math.max(6, r.height * sy);
      try { bctx.drawImage(src, x, y, w, h, 0, 0, 32, 18); }
      catch (e) { if (++lastErr < 4) console.warn('chameleon drawImage:', e.message); return; }
      var px;
      try { px = bctx.getImageData(0, 0, 32, 18).data; }
      catch (e) { if (++lastErr < 4) console.warn('chameleon getImageData:', e.message); return; }
      var n = 32 * 18, i;
      var sumX = 0, sumY = 0, sumW = 0, sumL = 0;
      for (i = 0; i < n; i++) {
        var R = px[i*4] / 255, G = px[i*4+1] / 255, B = px[i*4+2] / 255;
        var mx = Math.max(R, G, B), mn = Math.min(R, G, B), c = mx - mn;
        var L = mx, S = mx ? c / mx : 0, H = 0;
        if (c > 0.004) {
          if (mx === R) H = 60 * (((G - B) / c) % 6);
          else if (mx === G) H = 60 * ((B - R) / c + 2);
          else H = 60 * ((R - G) / c + 4);
          if (H < 0) H += 360;
        } else S = 0;
        var wgt = S * S + 0.02;          /* grey pixels barely vote */
        sumX += Math.cos(H * Math.PI / 180) * wgt;
        sumY += Math.sin(H * Math.PI / 180) * wgt;
        sumW += wgt; sumL += L;
      }
      var H2 = sumW ? Math.atan2(sumY, sumX) * 180 / Math.PI : tgt.h;
      if (H2 < 0) H2 += 360;
      var S2 = sumW ? Math.min(100, (sumW / n) * 165) : tgt.s;
      tgt.h = H2;
      tgt.s = Math.max(9, S2);
      if (prev) {                        /* scene energy: mean abs delta */
        var dsum = 0;
        for (i = 0; i < n * 4; i += 4)
          dsum += Math.abs(px[i] - prev[i]) + Math.abs(px[i+1] - prev[i+1]) + Math.abs(px[i+2] - prev[i+2]);
        tgt.e = Math.min(1, Math.pow((dsum / (n * 3)) / 255 * 6.5, 0.75));
      }
      prev = new Uint8ClampedArray(px);  /* copy — getImageData reuses */
    }

    function tick() {
      var k = 0.14, dh = tgt.h - cur.h;
      if (dh > 180) dh -= 360; else if (dh < -180) dh += 360;
      cur.h = (cur.h + dh * k + 360) % 360;
      cur.s += (tgt.s - cur.s) * k;
      cur.e += (tgt.e - cur.e) * 0.10;
      el.style.setProperty('--ch-h', cur.h.toFixed(1));
      el.style.setProperty('--ch-s', cur.s.toFixed(1));
      el.style.setProperty('--ch-e', cur.e.toFixed(3));
    }

    sampleRegion();
    var sampler = setInterval(sampleRegion, opts.interval || 420);
    (function loop() { if (!running) return; tick(); requestAnimationFrame(loop); })();
    return {
      sample: sampleRegion,
      stop: function () { running = false; clearInterval(sampler); }
    };
  }

  return { glass: glass, filter: filter, displacementMap: displacementMap, spark: spark, chameleon: chameleon, supportsUrl: supportsUrl };
})();

/* SMILE KIT — core.js · brand token + wordmark loader.
   The face/mood system lives in logo.js (real logo, verbatim paths). */
(function () {
  function applyBrand(b) {
    if (!b) return;
    if (b.tokens) {
      var r = document.documentElement.style;
      for (var k in b.tokens) r.setProperty(k, b.tokens[k]);
    }
    if (b.wordmark) document.querySelectorAll('.brand b').forEach(function (el) {
      if (!el.dataset.brandLocked) el.textContent = b.wordmark;
    });
  }
  if (window.BRAND) { applyBrand(window.BRAND); return; }
  fetch('brand.json').then(function (r) { return r.ok ? r.json() : null; }).then(applyBrand).catch(function () {});
})();

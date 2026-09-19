/* ============================================================
   SMILE LAB · ALERT ENGINE v2  — honest toast stack
   ------------------------------------------------------------
   What changed from v1 (user feedback):
   · NO ×N merge counters — "ain't no way someone may spam the
     same message over and over". A repeat from the same user
     within 9s is silently DROPPED, like a real moderation rule.
   · Toasts now stack like NORMAL toasts: newest enters at the
     bottom of the zone (closest to the ticker), older ones sit
     above it. The ZONE has a MAX HEIGHT — when the stack grows
     past it, the OLDEST toast leaves first. Nothing can ever
     cover the content.
   · Pill toast redesign: quiet dark glass, rounded-20, gold
     type chip + hairline progress. No loud color bars.
   · New types: lesson / trade / news (next lesson · close trade
     · market flash) with up/down trade colouring.
   · setZone('left'|'center'|'right') + scene key Z cycles the
     zone so you can A/B what reads better above the ticker.
   ------------------------------------------------------------
   Usage:
     const alerts = SmileAlerts.mount('#alerts');
     alerts.push({user:'njeri', type:'tip', amount:'500 KES',
                  msg:'karibu!', platform:'youtube'});
   URL params:
     ?amax=3    max toasts visible   (default 3, hard cap 5)
     ?adur=8    seconds per toast    (default 7)
     ?amaxh=42  zone max height in % of 1080 canvas (default 42)
     ?ademo=1   auto demo loop
   Scene keys: A one alert · ⇧A stress (6 distinct) · X clear
   ============================================================ */
(function () {
  'use strict';

  /* ---------- injected base CSS (scenes may theme via vars) --- */
  var CSS =
  '.alzone{display:flex;flex-direction:column;justify-content:flex-end;gap:10px;pointer-events:none;' +
    'max-height:var(--al-maxh,454px);overflow:hidden}' +
  '.alzone.zleft{align-items:flex-start}.alzone.zright{align-items:flex-end}.alzone.zcenter{align-items:center}' +
  '.al{position:relative;width:var(--al-w,380px);max-width:var(--al-w,380px);box-sizing:border-box;' +
    'padding:11px 15px 13px;border-radius:20px;' +
    'background:var(--al-bg,rgba(13,16,24,.9));' +
    '-webkit-backdrop-filter:blur(18px) saturate(1.3);backdrop-filter:blur(18px) saturate(1.3);' +
    'box-shadow:inset 0 0 0 1px rgba(255,255,255,.1),inset 0 1px 0 rgba(255,255,255,.07),' +
      '0 5px 14px rgba(0,0,0,.34),0 22px 48px rgba(0,0,0,.48);' +
    'display:flex;flex-direction:column;gap:6px;' +
    'opacity:0;transform:translateY(18px) scale(.96);' +
    'animation:al-in .55s cubic-bezier(.16,1,.3,1) forwards}' +
  '.al.out{animation:al-out .32s ease forwards}' +
  '@keyframes al-in{to{opacity:1;transform:none}}' +
  '@keyframes al-out{to{opacity:0;transform:translateY(-10px) scale(.95)}}' +
  '.al .r1{display:flex;align-items:center;gap:8px;min-width:0}' +
  '.al .tag{flex:none;display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;' +
    'font-family:"IBM Plex Mono",monospace;font-size:8.5px;font-weight:700;letter-spacing:.16em;' +
    'color:var(--al-accent,#FFCE00);background:color-mix(in srgb,var(--al-accent,#FFCE00) 13%,transparent);' +
    'box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--al-accent,#FFCE00) 34%,transparent)}' +
  '.al .who{font-weight:800;font-size:14.5px;letter-spacing:-.01em;color:var(--al-fg,#F2F5FC);' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
  '.al .amt{flex:none;margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:700;' +
    'color:var(--al-accent,#FFCE00);white-space:nowrap}' +
  '.al .r2{display:flex;align-items:center;gap:8px;min-width:0}' +
  '.al .msg{flex:1;font-size:12.5px;line-height:1.45;color:#C9D2E4;display:-webkit-box;' +
    '-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}' +
  '.al .msg b{color:var(--al-accent,#FFCE00);font-weight:700}' +
  '.al .plat{flex:none;display:inline-flex;align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;' +
    'font-size:8px;font-weight:600;letter-spacing:.13em;color:#9AA4BC}' +
  '.al .plat i{width:6px;height:6px;border-radius:50%;background:var(--pc,#8A94AC)}' +
  '.al .prog{position:absolute;left:20px;right:20px;bottom:6px;height:2px;border-radius:2px;' +
    'transform-origin:left;background:var(--al-accent,#FFCE00);opacity:.55;' +
    'animation:al-prog linear forwards;animation-duration:inherit}' +
  '@keyframes al-prog{from{transform:scaleX(1)}to{transform:scaleX(0)}}' +
  '@media (prefers-reduced-motion:reduce){.al{animation-duration:.01s}}';

  /* ---------- helpers ---------- */
  function el(t, c, h) { var e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; }
  function getPlat(p) {
    return { youtube: ['#FF4E45', 'YOUTUBE'], twitch: ['#9146FF', 'TWITCH'], tiktok: ['#3AE4E7', 'TIKTOK'],
             x: ['#E7E9EA', 'X'], kick: ['#53FC18', 'KICK'], facebook: ['#4267FF', 'FACEBOOK'],
             insta: ['#FF5C8A', 'INSTAGRAM'] }[p] || ['#8A94AC', p ? String(p).toUpperCase() : 'SMILE'];
  }
  var TYPES = {
    tip:    { accent: '#FFCE00', tag: 'TIP' },
    member: { accent: '#6E9BFF', tag: 'MEMBER' },
    sub:    { accent: '#6E9BFF', tag: 'SUB' },
    follow: { accent: '#9AA4BC', tag: 'FOLLOW' },
    raid:   { accent: '#34D399', tag: 'RAID' },
    q:      { accent: '#E8EDF7', tag: 'QUESTION' },
    lesson: { accent: '#FFCE00', tag: 'NEXT LESSON' },
    trade:  { accent: '#34D399', tag: 'CLOSE TRADE' },
    tradedn:{ accent: '#F6465D', tag: 'CLOSE TRADE' },
    news:   { accent: '#FFCE00', tag: 'MARKET FLASH' }
  };
  /* priority: trade/lesson/news always play first; tips & raids next; follows last */
  var PRIO = { follow: 0, q: 1, sub: 1, member: 1, raid: 2, tip: 2, lesson: 3, trade: 3, tradedn: 3, news: 3 };

  function Engine(host, opts) {
    this.host = (typeof host === 'string') ? document.querySelector(host) : host;
    if (!this.host) return;
    var q = function (k, d) { var v = parseFloat(new URLSearchParams(location.search).get(k)); return isNaN(v) ? d : v; };
    this.max  = Math.min(5, Math.max(1, q('amax', (opts && opts.max) || 3)));
    this.dur  = q('adur', (opts && opts.dur) || 7) * 1000;
    this.qcap = q('aq', (opts && opts.queue) || 10);
    this.maxh = Math.round(1080 * q('amaxh', (opts && opts.maxh) || 42) / 100);
    this.queue = []; this.live = []; this.seen = {};
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    this.host.classList.add('alzone');
    this.host.style.setProperty('--al-maxh', this.maxh + 'px');
    var self = this;
    if (q('ademo', 0) || (opts && opts.demo)) this._demo = setInterval(function () { self.push(self.fake()); }, 9000);
  }

  /* ---------- zone (scene key Z) ---------- */
  Engine.prototype.setZone = function (z) {
    if (!this.host) return;
    this.host.classList.remove('zleft', 'zcenter', 'zright');
    this.host.classList.add('z' + (z || 'right'));
  };

  /* ---------- public ---------- */
  Engine.prototype.push = function (ev) {
    if (!this.host) return;
    ev = ev || {};
    var key = (ev.user || '?') + '|' + (ev.type || 'tip');
    var now = Date.now(), prev = this.seen[key];
    if (prev && (now - prev.t) < 9000) {           /* repeat inside 9s → dropped, not merged */
      this.seen[key].t = now;
      return 'dropped';
    }
    this.seen[key] = { t: now };
    var item = { user: ev.user || 'smile.co.ke', type: ev.type || 'tip', amount: ev.amount || '',
                 msg: ev.msg || '', platform: ev.platform || 'youtube', id: key + ':' + now };
    if (this.queue.length >= this.qcap) {           /* queue full → drop lowest-priority oldest */
      var drop = -1;
      for (var i = 0; i < this.queue.length; i++) if (PRIO[this.queue[i].type] === 0) { drop = i; break; }
      if (drop < 0) for (var j = 0; j < this.queue.length; j++) if (PRIO[this.queue[j].type] <= 1) { drop = j; break; }
      this.queue.splice(drop < 0 ? 0 : drop, 1);
    }
    var p = PRIO[item.type] || 1;
    if (p >= 2) { var k = this.queue.length; while (k > 0 && (PRIO[this.queue[k - 1].type] || 1) < p) k--; this.queue.splice(k, 0, item); }
    else this.queue.push(item);
    this._pump();
    return item.id;
  };

  Engine.prototype.clear = function () {
    this.queue = [];
    this.live.slice().forEach(function (c) { c._kill(true); });
  };
  Engine.prototype.counts = function () { return { live: this.live.length, queued: this.queue.length }; };

  Engine.prototype.storm = function (n) {           /* stress test — distinct users, like a real raid */
    n = n || 6;
    var names = ['njeri.w', 'ke_trader', 'mumbi', 'otienoJ', 'githinji', 'awuor.d', 'kamau254', 'zendesk_fan'];
    var plats = ['youtube', 'twitch', 'tiktok', 'x', 'kick', 'youtube', 'tiktok', 'twitch'];
    for (var i = 0; i < n; i++) {
      var self = this;
      setTimeout(function (k) {
        var r = k % 4;
        self.push({ user: names[k % names.length],
          type: r === 0 ? 'tip' : (r === 1 ? 'follow' : (r === 2 ? 'q' : 'sub')),
          amount: r === 0 ? (50 + k * 25) + ' KES' : '',
          msg: r === 1 ? 'just followed — karibu sana!' : (r === 0 ? 'keep it up!' : (r === 2 ? 'do a USD/KES deep-dive?' : 'joined the after-hours tier')),
          platform: plats[k % plats.length] });
      }.bind(null, i), i * 420);
    }
  };

  Engine.prototype.fake = function () {
    var pool = [
      { user: 'njeri.w', type: 'tip', amount: '500 KES', msg: 'ndio hii chai — leak the NSE watchlist!', platform: 'youtube' },
      { user: 'ke_trader', type: 'q', amount: '', msg: 'can you cover the Safaricom dividend dates?', platform: 'twitch' },
      { user: 'mumbi', type: 'follow', amount: '', msg: 'just followed — karibu sana!', platform: 'tiktok' },
      { user: 'otienoJ', type: 'member', amount: '', msg: 'joined the after-hours tier', platform: 'youtube' },
      { user: 'awuor.d', type: 'raid', amount: '', msg: 'raided with 42 fam — hujambo!', platform: 'twitch' },
      { user: 'smile.co.ke', type: 'lesson', amount: '', msg: 'CHART SCHOOL 07 — Reading Order Flow · 2:00 PM EAT', platform: 'youtube' },
      { user: 'desk bot', type: 'trade', amount: '+6.2%', msg: 'CLOSE · SCOM long hit target — 28.75 → 30.55', platform: 'smile' },
      { user: 'desk bot', type: 'tradedn', amount: '-1.1%', msg: 'CLOSE · BTC swing stopped out at 96,100', platform: 'smile' },
      { user: 'smile.co.ke', type: 'news', amount: '', msg: 'CBK holds rate at 13.00% — shilling steadies', platform: 'smile' },
      { user: 'kamau254', type: 'tip', amount: '1,000 KES', msg: 'for the USD/KES converter segment', platform: 'x' }
    ];
    return pool[Math.floor(Math.random() * pool.length)];
  };

  /* ---------- internals ---------- */
  Engine.prototype._pump = function () {
    while (this.live.length < this.max && this.queue.length) this._show(this.queue.shift());
    this._trim();
  };

  /* the honesty check: zone never grows past max-height — oldest leaves first */
  Engine.prototype._trim = function () {
    var host = this.host, maxh = this.maxh;
    while (this.live.length > 1 &&
           (this.live.length > this.max || host.scrollHeight > maxh + 2)) {
      this._kill(this.live[0], true);
    }
  };

  Engine.prototype._show = function (it) {
    var self = this, T = TYPES[it.type] || TYPES.tip, pc = getPlat(it.platform);
    var card = el('div', 'al');
    card.style.setProperty('--al-accent', T.accent);
    card.innerHTML =
      '<div class="r1">' +
      '<span class="tag">' + T.tag + '</span>' +
      '<span class="who"></span>' +
      (it.amount ? '<span class="amt">' + it.amount + '</span>' : '') +
      '</div>' +
      '<div class="r2">' +
      (it.msg ? '<div class="msg"></div>' : '') +
      '<span class="plat"><i style="--pc:' + pc[0] + '"></i>' + pc[1] + '</span>' +
      '</div>' +
      '<div class="prog"></div>';
    card.querySelector('.who').textContent = it.user;
    if (it.msg) card.querySelector('.msg').textContent = it.msg;
    card.querySelector('.prog').style.animationDuration = this.dur + 'ms';
    var handle = { el: card, key: it.id };
    this.live.push(handle);
    this.host.appendChild(card);                    /* newest at the BOTTOM — classic toast stack */
    var t = setTimeout(function () { self._kill(handle); }, this.dur);
    handle._kill = function (fast) {
      clearTimeout(t);
      var ix = self.live.indexOf(handle); if (ix >= 0) self.live.splice(ix, 1);
      if (fast) { card.remove(); } else { card.classList.add('out'); setTimeout(function () { card.remove(); }, 330); }
      self._pump();
    };
    /* measure after layout so overflow trimming is exact */
    requestAnimationFrame(function () { self._trim(); });
  };

  window.SmileAlerts = { mount: function (h, o) { return new Engine(h, o); }, types: TYPES };
})();

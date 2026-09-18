/* ============================================================
   SMILE LAB · ALERT ENGINE v1  (shared by all lab scenes)
   ------------------------------------------------------------
   Fixes the "infinite stack" problem:
   · max N cards on screen (default 2) — the rest WAIT in a queue
   · queue is capped (default 12). When full, lowest-priority
     oldest item is dropped (follows die first, tips survive)
   · same user + same type within 9s MERGES into one card with a
     ×N counter instead of stacking a new card
   · every card auto-dismisses with a visible progress bar
   · multiplatform: youtube / twitch / tiktok / x / kick badges
   ------------------------------------------------------------
   Usage:
     const alerts = SmileAlerts.mount('#alerts');
     alerts.push({user:'njeri', type:'tip', amount:'500 KES',
                  msg:'karibu!', platform:'youtube'});
   URL params:
     ?amax=3     max cards on screen      (default 2, hard cap 4)
     ?adur=9     seconds per card         (default 7)
     ?aq=16      queue capacity           (default 12)
     ?ademo=1    auto demo loop (fires a realistic event every ~9s)
   Keys handled by the SCENE, not the engine:
     A = one random alert · Shift+A = spam storm (6 fast) · X = clear
   ============================================================ */
(function () {
  'use strict';

  /* ---------- injected base CSS (scene themes can override) --- */
  var CSS =
  '.alzone{display:flex;flex-direction:column;gap:10px;align-items:flex-end;pointer-events:none}' +
  '.alzone.alleft{align-items:flex-start}' +
  '.al{position:relative;width:var(--al-w,400px);max-width:var(--al-w,400px);display:flex;align-items:stretch;overflow:hidden;' +
    'border-radius:var(--al-r,18px);background:var(--al-bg,rgba(14,16,24,.9));' +
    '-webkit-backdrop-filter:blur(18px) saturate(1.3);backdrop-filter:blur(18px) saturate(1.3);' +
    'box-shadow:inset 0 0 0 1px rgba(255,255,255,.09),0 4px 10px rgba(0,0,0,.35),0 22px 48px rgba(0,0,0,.5);' +
    'opacity:0;transform:translateX(calc(var(--al-dir,1) * 46px)) scale(.96);' +
    'animation:al-in .62s cubic-bezier(.16,1,.3,1) forwards}' +
  '.alzone.alleft .al{--al-dir:-1}' +
  '.al.out{animation:al-out .4s cubic-bezier(.5,0,.75,.4) forwards}' +
  '@keyframes al-in{to{opacity:1;transform:none}}' +
  '@keyframes al-out{to{opacity:0;transform:translateY(14px) scale(.94)}}' +
  '.al .bar{flex:none;width:5px;background:var(--al-accent,#FFCE00)}' +
  '.al .bd{flex:1;min-width:0;padding:12px 16px 13px 14px;display:flex;flex-direction:column;gap:5px}' +
  '.al .r1{display:flex;align-items:center;gap:8px;min-width:0}' +
  '.al .who{font-weight:800;font-size:15px;letter-spacing:-.01em;color:var(--al-fg,#F2F5FC);' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
  '.al .n{flex:none;font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;color:#1F1702;' +
    'background:var(--al-accent,#FFCE00);border-radius:999px;padding:2px 7px;transform-origin:center;' +
    'animation:al-pop .45s cubic-bezier(.34,1.56,.64,1)}' +
  '@keyframes al-pop{0%{transform:scale(1)}45%{transform:scale(1.45)}100%{transform:scale(1)}}' +
  '.al .plat{flex:none;display:inline-flex;align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;' +
    'font-size:8.5px;font-weight:600;letter-spacing:.14em;color:#96A0B8;border:1px solid rgba(255,255,255,.13);' +
    'border-radius:999px;padding:2.5px 8px}' +
  '.al .plat i{width:6px;height:6px;border-radius:50%;background:var(--pc,#888)}' +
  '.al .msg{font-size:12.5px;line-height:1.45;color:#C6CEDF;display:-webkit-box;-webkit-line-clamp:2;' +
    '-webkit-box-orient:vertical;overflow:hidden}' +
  '.al .msg b{color:var(--al-accent,#FFCE00);font-weight:700}' +
  '.al .prog{position:absolute;left:0;bottom:0;height:3px;width:100%;transform-origin:left;' +
    'background:var(--al-accent,#FFCE00);opacity:.85;animation:al-prog linear forwards;animation-duration:inherit}' +
  '@keyframes al-prog{from{transform:scaleX(1)}to{transform:scaleX(0)}}' +
  '.al .amt{flex:none;display:flex;align-items:center;padding:0 16px 0 0;font-family:"IBM Plex Mono",monospace;' +
    'font-size:13px;font-weight:600;color:var(--al-accent,#FFCE00);white-space:nowrap}' +
  '.al .tag{font-family:"IBM Plex Mono",monospace;font-size:8.5px;font-weight:600;letter-spacing:.18em;' +
    'color:var(--al-accent,#FFCE00);text-transform:uppercase}';

  /* ---------- helpers ---------- */
  function el(t, c, h) { var e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; }
  function getPlat(p) {
    return { youtube: ['#FF4E45', 'YOUTUBE'], twitch: ['#9146FF', 'TWITCH'], tiktok: ['#3AE4E7', 'TIKTOK'],
             x: ['#E7E9EA', 'X'], kick: ['#53FC18', 'KICK'] }[p] || ['#8A94AC', p ? String(p).toUpperCase() : 'SMILE'];
  }
  var TYPES = {
    tip:    { accent: '#FFCE00', tag: 'TIP' },
    member: { accent: '#3E6EFF', tag: 'MEMBER' },
    sub:    { accent: '#3E6EFF', tag: 'SUB' },
    follow: { accent: '#8A94AC', tag: 'FOLLOW' },
    raid:   { accent: '#10B981', tag: 'RAID' },
    q:      { accent: '#F2F5FC', tag: 'QUESTION' }
  };

  function Engine(host, opts) {
    this.host = (typeof host === 'string') ? document.querySelector(host) : host;
    if (!this.host) return;
    var q = function (k, d) { var v = parseInt(new URLSearchParams(location.search).get(k), 10); return isNaN(v) ? d : v; };
    this.max  = Math.min(4, Math.max(1, q('amax', (opts && opts.max) || 2)));
    this.dur  = q('adur', (opts && opts.dur) || 7) * 1000;
    this.qcap = q('aq', (opts && opts.queue) || 12);
    this.queue = []; this.live = []; this.seen = {};
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    this.host.classList.add('alzone');
    var self = this;
    if (q('ademo', 0) || (opts && opts.demo)) this._demo = setInterval(function () { self.push(self.fake()); }, 9000);
  }

  /* ---------- public ---------- */
  Engine.prototype.push = function (ev) {
    if (!this.host) return;
    ev = ev || {};
    var key = (ev.user || '?') + '|' + (ev.type || 'tip');
    var now = Date.now(), prev = this.seen[key];
    if (prev && (now - prev.t) < 9000) {           /* anti-spam merge */
      prev.n++; prev.t = now;
      this._bump(key, prev.n);
      return 'merged';
    }
    this.seen[key] = { t: now, n: 1, id: null };
    var item = { user: ev.user || 'smile.co.ke', type: ev.type || 'tip', amount: ev.amount || '',
                 msg: ev.msg || '', platform: ev.platform || 'youtube', n: 1, id: key };
    if (this.queue.length >= this.qcap) {           /* queue cap: drop lowest-priority oldest */
      var PRIO = { follow: 0, q: 1, sub: 1, member: 1, raid: 2, tip: 2 };
      var drop = -1;
      for (var i = 0; i < this.queue.length; i++) if (PRIO[this.queue[i].type] === 0) { drop = i; break; }
      if (drop < 0) for (var j = 0; j < this.queue.length; j++) if (PRIO[this.queue[j].type] <= 1) { drop = j; break; }
      this.queue.splice(drop < 0 ? 0 : drop, 1);
    }
    /* tips & raids jump ahead of follows, otherwise FIFO */
    if (PRIO_[item.type] >= 2) { var k = this.queue.length; while (k > 0 && PRIO_[this.queue[k - 1].type] < 2) k--; this.queue.splice(k, 0, item); }
    else this.queue.push(item);
    this._pump();
    return item.id;
  };
  var PRIO_ = { follow: 0, q: 1, sub: 1, member: 1, raid: 2, tip: 2 };

  Engine.prototype.clear = function () {
    this.queue = [];
    this.live.slice().forEach(function (c) { c._kill(true); });
  };
  Engine.prototype.counts = function () { return { live: this.live.length, queued: this.queue.length }; };

  Engine.prototype.storm = function (n) {           /* spam test */
    n = n || 6;
    var names = ['njeri.w', 'ke_trader', 'mumbi', 'otienoJ', 'zendesk_fan', 'githinji', 'awuor.d', 'kamau254'];
    var plats = ['youtube', 'twitch', 'tiktok', 'x', 'kick'];
    for (var i = 0; i < n; i++) {
      var self = this;
      setTimeout(function (k) {
        self.push({ user: names[k % names.length] + (k > 4 ? '2' : ''), type: k % 3 === 0 ? 'tip' : (k % 3 === 1 ? 'follow' : 'q'),
                    amount: k % 3 === 0 ? (50 + k * 25) + ' KES' : '',
                    msg: k % 3 === 1 ? 'just followed — karibu sana!' : (k % 3 === 0 ? 'keep it up!' : 'do a USD/KES deep-dive?'),
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
      { user: 'kamau254', type: 'tip', amount: '1,000 KES', msg: 'for the USD/KES converter segment', platform: 'x' }
    ];
    return pool[Math.floor(Math.random() * pool.length)];
  };

  /* ---------- internals ---------- */
  Engine.prototype._pump = function () {
    while (this.live.length < this.max && this.queue.length) this._show(this.queue.shift());
  };

  Engine.prototype._show = function (it) {
    var self = this, T = TYPES[it.type] || TYPES.tip, pc = getPlat(it.platform);
    var card = el('div', 'al');
    card.style.setProperty('--al-accent', T.accent);
    var extra = it.amount ? '<span class="amt">' + it.amount + '</span>' : '';
    card.innerHTML =
      '<div class="bar"></div><div class="bd"><div class="r1">' +
      '<span class="tag">' + T.tag + '</span>' +
      '<span class="who"></span>' +
      (it.n > 1 ? '<span class="n">×' + it.n + '</span>' : '') +
      '<span class="plat"><i style="--pc:' + pc[0] + '"></i>' + pc[1] + '</span></div>' +
      (it.msg ? '<div class="msg"></div>' : '') +
      '</div>' + extra + '<div class="prog"></div>';
    card.querySelector('.who').textContent = it.user;
    if (it.msg) card.querySelector('.msg').textContent = it.msg;
    card.querySelector('.prog').style.animationDuration = this.dur + 'ms';
    var handle = { el: card, key: it.id, n: it.n };
    this.live.push(handle);
    this.host.appendChild(card);
    /* cap DOM: if cards somehow exceed max (merge race), kill oldest */
    while (this.live.length > this.max) this._kill(this.live[0], true);

    var t = setTimeout(function () { self._kill(handle); }, this.dur);
    handle._kill = function (fast) {
      clearTimeout(t);
      var ix = self.live.indexOf(handle); if (ix >= 0) self.live.splice(ix, 1);
      if (fast) { card.remove(); } else { card.classList.add('out'); setTimeout(function () { card.remove(); }, 400); }
      self._pump();
    };
  };

  Engine.prototype._bump = function (key, n) {
    /* update a live card if present, else the queued one */
    for (var i = 0; i < this.live.length; i++) {
      var h = this.live[i];
      if (h.key === key) {
        h.n = n;
        var badge = h.el.querySelector('.n');
        if (!badge) {
          badge = el('span', 'n'); h.el.querySelector('.r1').insertBefore(badge, h.el.querySelector('.plat'));
        }
        badge.textContent = '×' + n;
        badge.style.animation = 'none'; void badge.offsetWidth; badge.style.animation = '';
        return;
      }
    }
    for (var j = 0; j < this.queue.length; j++) {
      if (this.queue[j].id === key) { this.queue[j].n = n; return; }
    }
  };

  window.SmileAlerts = { mount: function (h, o) { return new Engine(h, o); }, types: TYPES };
})();

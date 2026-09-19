/* ============================================================
   SMILE LAB · CHROME KIT v1 (Round 4 shared top chrome)
   ------------------------------------------------------------
   The user's Round-4 chrome spec, one shared implementation:
   · TOP-CENTER pill  = the smile FACE mark only (no writing)
   · TOP-LEFT pill    = the full smile logo (with the writing)
   · TOP-RIGHT pill   = rotating social chips (Instagram,
     Facebook, X, TikTok, YouTube, WhatsApp — real brand marks)
     + the EAT clock / session line (slightly taller pill)
   · BOTTOM           = the scene's own ticker pill
   Ticker content rule (sponsor confusion fix):
     SmileChrome.tickerItems('market')  → pure market data
     SmileChrome.tickerItems('offair')  → + sponsor slots + socials
   ============================================================ */
(function () {
  'use strict';

  var ICONS = {
    insta: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="18" height="18" rx="5.2"/><circle cx="12" cy="12" r="4.1"/><circle cx="17.4" cy="6.6" r="1.15" fill="currentColor" stroke="none"/></svg>',
    facebook: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.42 20.6v-6.9h2.32l.35-2.7h-2.67V9.25c0-.78.22-1.32 1.34-1.32h1.43V5.52c-.25-.03-1.1-.11-2.08-.11-2.06 0-3.47 1.26-3.47 3.57V11H8.32v2.7h2.32v6.9z"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    tiktok: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>',
    youtube: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23 12s0-3.85-.49-5.7a3 3 0 0 0-2.1-2.1C18.56 3.7 12 3.7 12 3.7s-6.56 0-8.4.5a3 3 0 0 0-2.11 2.1C1 8.15 1 12 1 12s0 3.85.49 5.7a3 3 0 0 0 2.1 2.1c1.85.5 8.41.5 8.41.5s6.56 0 8.4-.5a3 3 0 0 0 2.11-2.1C23 15.85 23 12 23 12zM9.75 15.02V8.98L15.5 12z"/></svg>',
    whatsapp: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.64.07-.3-.15-1.26-.46-2.39-1.47-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.13-.14.3-.35.44-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.5 0 1.47 1.07 2.9 1.22 3.1.15.2 2.11 3.22 5.1 4.51.71.31 1.27.49 1.7.63.72.23 1.37.2 1.88.12.57-.09 1.76-.72 2-1.42.25-.7.25-1.3.18-1.42-.08-.13-.28-.2-.57-.35zM12.05 21.79h-.01a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 1 1 8.38 4.63zM12.05 2A10 10 0 0 0 3.4 17.2L2 22l4.9-1.28A10 10 0 1 0 12.05 2z"/></svg>'
  };

  var SOCIALS = [
    { icon: 'insta',    brand: '#FF5C8A', handle: '@smile.co.ke',  net: 'INSTAGRAM' },
    { icon: 'facebook', brand: '#6E9BFF', handle: 'smile.co.ke',   net: 'FACEBOOK' },
    { icon: 'x',        brand: '#E7E9EA', handle: '@smilecoke',    net: 'X' },
    { icon: 'tiktok',   brand: '#3AE4E7', handle: '@smile.co.ke',  net: 'TIKTOK' },
    { icon: 'youtube',  brand: '#FF4E45', handle: 'Smile TV KE',   net: 'YOUTUBE' },
    { icon: 'whatsapp', brand: '#34D399', handle: 'smile.co.ke',   net: 'WHATSAPP' },
    { icon: 'insta',    brand: '#FFCE00', handle: '#TradeSmile',   net: 'HASHTAG' }
  ];

  var CSS =
  /* ---- shared pill chrome ---- */
  '.spill{position:absolute;top:20px;height:64px;display:flex;align-items:center;z-index:48;' +
    'border-radius:999px;background:rgba(12,15,23,.88);-webkit-backdrop-filter:blur(20px) saturate(1.3);' +
    'backdrop-filter:blur(20px) saturate(1.3);' +
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 0 0 1px rgba(0,0,0,.4),0 14px 34px rgba(0,0,0,.45),0 0 0 1.5px rgba(255,206,0,.2)}' +
  '#brandL{left:24px;padding:0 20px 0 16px;gap:14px}' +
  '#brandL img.lg{height:26px;display:block}' +
  '#brandL .lv{display:flex;align-items:center;gap:7px;padding:7px 14px;border-radius:999px;background:#FFCE00;' +
    'color:#1F1702;font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:700;letter-spacing:.16em;' +
    'box-shadow:0 6px 16px rgba(255,206,0,.3)}' +
  '#brandL .lv i{width:6.5px;height:6.5px;border-radius:50%;background:#1F1702;animation:sp-pulse 1.7s infinite}' +
  '#brandC{left:0;right:0;margin:auto;width:fit-content;padding:0 18px;height:56px;top:24px}' +
  '#brandC img{height:32px;display:block;filter:drop-shadow(0 4px 12px rgba(255,206,0,.25));animation:sp-breathe 3.4s ease-in-out infinite}' +
  '#brandR{right:24px;height:76px;top:14px;flex-direction:column;align-items:stretch;justify-content:center;gap:4px;padding:8px 18px;min-width:236px}' +
  '#brandR .soc{position:relative;display:flex;align-items:center;gap:9px;height:26px;overflow:hidden}' +
  '#brandR .soc .ic{width:16px;height:16px;flex:none;color:var(--soc-brand,#FFCE00);transition:transform .5s cubic-bezier(.16,1,.3,1),opacity .5s}' +
  '#brandR .soc .ic svg{width:100%;height:100%;display:block}' +
  '#brandR .soc .hd{font-weight:700;font-size:13px;letter-spacing:-.01em;color:#F2F5FC;white-space:nowrap}' +
  '#brandR .soc .nt{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:7.5px;font-weight:600;' +
    'letter-spacing:.16em;color:#8A94AC}' +
  '#brandR .soc .sw{position:absolute;inset:0;display:flex;align-items:center;gap:9px;opacity:0;' +
    'transform:translateY(10px)}' +
  '#brandR .soc .sw.on{opacity:1;transform:none;transition:all .55s cubic-bezier(.16,1,.3,1)}' +
  '#brandR .soc .sw.off{opacity:0;transform:translateY(-10px);transition:all .55s cubic-bezier(.16,1,.3,1)}' +
  '#brandR .tmline{display:flex;align-items:center;gap:9px;border-top:1px solid rgba(255,255,255,.07);padding-top:4px}' +
  '#brandR .clk{font-family:"IBM Plex Mono",monospace;font-weight:700;font-size:12.5px;color:#F2F5FC;font-variant-numeric:tabular-nums}' +
  '#brandR .sess{margin-left:auto;display:inline-flex;align-items:center;gap:6px;font-family:"IBM Plex Mono",monospace;' +
    'font-size:8px;font-weight:600;letter-spacing:.16em;color:#9AA4BC}' +
  '#brandR .sess b{color:#FFCE00;font-weight:600;width:5px;height:5px;border-radius:50%;background:#FFCE00;display:inline-block}' +
  '@keyframes sp-pulse{0%,100%{opacity:1}50%{opacity:.3}}' +
  '@keyframes sp-breathe{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-2px) scale(1.03)}}';

  function mount(opts) {
    opts = opts || {};
    var fit = document.querySelector(opts.fit || '#fit');
    if (!fit) return null;
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);

    if (opts.logo !== false) {
      var L = document.createElement('div'); L.id = 'brandL'; L.className = 'spill';
      L.innerHTML = '<img class="lg" src="assets/smile-logo.svg" alt="smile.co.ke">' +
        (opts.live === false ? '' : '<span class="lv"><i></i>LIVE</span>');
      fit.appendChild(L);
    }
    if (opts.face !== false) {
      var C = document.createElement('div'); C.id = 'brandC'; C.className = 'spill';
      C.innerHTML = '<img src="assets/smile-face.svg" alt="smile">';
      fit.appendChild(C);
    }
    var R = null;
    if (opts.social !== false) {
      R = document.createElement('div'); R.id = 'brandR'; R.className = 'spill';
      R.innerHTML = '<div class="soc" id="socRot"></div>' +
        '<div class="tmline"><span class="clk" id="rcClk">--:--:--</span>' +
        '<span class="sess"><b></b><span id="rcSess">—</span>· EAT</span></div>';
      fit.appendChild(R);
      /* social rotation: one platform at a time, slide-swap every 4.2s */
      var rot = R.querySelector('#socRot'), ix = 0;
      function chipHTML(s) {
        return '<span class="ic" style="--soc-brand:' + s.brand + ';color:' + s.brand + '">' + ICONS[s.icon] + '</span>' +
               '<span class="hd">' + s.handle + '</span><span class="nt">' + s.net + '</span>';
      }
      function show(i, dir) {
        var cur = rot.querySelector('.sw.on'), nxt = document.createElement('div');
        nxt.className = 'sw'; nxt.innerHTML = chipHTML(SOCIALS[i % SOCIALS.length]);
        rot.appendChild(nxt);
        requestAnimationFrame(function () {
          nxt.classList.add('on');
          if (cur) { cur.classList.remove('on'); cur.classList.add('off'); setTimeout(function () { cur.remove(); }, 600); }
        });
      }
      show(0);
      setInterval(function () { ix++; show(ix); }, 4200);
    }

    /* EAT clock + session truth */
    var SESSIONS = [['ASIA', 3, 9], ['NAIROBI', 9, 15], ['LONDON', 10, 19], ['NEW YORK', 16.5, 23]];
    function eatParts() {
      var f = new Intl.DateTimeFormat('en-GB', { timeZone: 'Africa/Nairobi', hour12: false, hourCycle: 'h23',
        hour: '2-digit', minute: '2-digit', second: '2-digit' }), p = {};
      f.formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
      return p;
    }
    function tick() {
      var p = eatParts();
      var clk = document.getElementById('rcClk');
      if (clk) clk.textContent = p.hour + ':' + p.minute + ':' + p.second;
      var h = parseInt(p.hour, 10) + parseInt(p.minute, 10) / 60;
      var act = SESSIONS.filter(function (s) { return h >= s[1] && h < s[2]; });
      var se = document.getElementById('rcSess');
      if (se) se.textContent = act.length ? act[act.length - 1][0] + ' OPEN' : 'AFTER HRS';
    }
    setInterval(tick, 1000); tick();

    return { socials: SOCIALS, icons: ICONS, eatParts: eatParts, sessions: SESSIONS };
  }

  /* ---------- ticker content rules ---------- */
  var MKT = [
    ['USD/KES', '129.42', '+0.31%', 1], ['NSE 20', '82.41', '+0.9%', 1], ['SCOM', '28.75 KES', '+4.2%', 1],
    ['BTC', '97,240', '-1.2%', 0], ['XAU', '2,412', '+0.6%', 1], ['EQTY', '52.10 KES', '+2.8%', 1],
    ['KCB', '44.60 KES', '+2.1%', 1], ['EABL', '224.00 KES', '-1.4%', 0], ['EUR/KES', '140.85', '-0.18%', 0]
  ];
  var OFFAIR = [
    ['SP', 'AD · SMILE QUANTUM — INVEST FROM 100 KES', '', 2],
    ['SP', 'AD · TREASURY BOND AUCTION MAR 26 — 16.8% YTM', '', 2],
    ['SOC', '#TradeSmile — tag your setups', '', 3],
    ['SOC', '@smile.co.ke — the desk, everywhere', '', 3]
  ];
  function tickerItems(mode) {
    var list = (mode === 'offair') ? MKT.concat(OFFAIR) : MKT;
    return list.map(function (t) {
      if (t[3] === 2) return '<span class="it sponsor"><span class="s">AD</span>' + t[1] + '</span>';
      if (t[3] === 3) return '<span class="it social"><span class="s">' + t[0] + '</span>' + t[1] + '</span>';
      return '<span class="it"><span class="s">' + t[0] + '</span><span class="num">' + t[1] + '</span>' +
             '<span class="num ' + (t[2][0] === '+' ? 'up' : 'dn') + '">' + t[2] + '</span></span>';
    }).join('');
  }
  /* shared pill-ticker CSS (island-R3 look, per user spec for fixed bottom tickers) */
  var TICKER_CSS =
  '.tkWrap{position:absolute;left:0;right:0;bottom:24px;display:flex;justify-content:center;z-index:35;pointer-events:none}' +
  '.tkPill{max-width:1420px;width:fit-content;height:54px;display:flex;align-items:stretch;overflow:hidden;border-radius:999px;' +
    'background:rgba(12,15,23,.9);-webkit-backdrop-filter:blur(20px) saturate(1.3);backdrop-filter:blur(20px) saturate(1.3);' +
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 0 0 1px rgba(0,0,0,.4),0 14px 34px rgba(0,0,0,.45),0 0 0 1.5px rgba(255,206,0,.2)}' +
  '.tkPill .cap{flex:none;display:flex;align-items:center;gap:9px;padding:0 22px 0 18px;background:#FFCE00;color:#1F1702;' +
    'clip-path:polygon(0 0,100% 0,calc(100% - 20px) 100%,0 100%)}' +
  '.tkPill .cap i{width:7px;height:7px;border-radius:50%;background:#1F1702;animation:sp-pulse 1.7s infinite}' +
  '.tkPill .cap .t{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:700;letter-spacing:.18em}' +
  '.tkPill .clip{flex:1;display:flex;align-items:center;overflow:hidden;position:relative;' +
    '-webkit-mask:linear-gradient(90deg,transparent,#000 26px calc(100% - 26px),transparent);' +
    'mask:linear-gradient(90deg,transparent,#000 26px calc(100% - 26px),transparent)}' +
  '.tkPill .tk{display:flex;align-items:center;gap:34px;padding:0 17px;white-space:nowrap;will-change:transform;animation:sp-tk 38s linear infinite}' +
  '.tkPill .it{display:flex;align-items:center;gap:8px;font-family:"IBM Plex Mono",monospace;font-size:12.5px;font-weight:600;color:#F2F5FC}' +
  '.tkPill .it .s{color:#9AA4BC;letter-spacing:.06em}' +
  '.tkPill .it.sponsor{background:rgba(255,206,0,.12);box-shadow:inset 0 0 0 1px rgba(255,206,0,.35);border-radius:999px;padding:7px 16px;color:#FFCE00}' +
  '.tkPill .it.sponsor .s{color:rgba(255,206,0,.75)}' +
  '.tkPill .it.social{color:#F2F5FC}.tkPill .it.social .s{color:#FFCE00}' +
  '@keyframes sp-tk{from{transform:translateX(0)}to{transform:translateX(-50%)}}';

  function tickerCSS() {
    var st = document.createElement('style'); st.textContent = TICKER_CSS; document.head.appendChild(st);
  }

  window.SmileChrome = { mount: mount, tickerItems: tickerItems, tickerCSS: tickerCSS, icons: ICONS, socials: SOCIALS };
})();

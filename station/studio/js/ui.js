/* ============================================================
   OBS Studio — Web Replication · UI Framework
   Qt-style popup menus, draggable dialog windows, tooltips,
   message boxes — pixel-matched to OBS/Qt on Windows.
   ============================================================ */
import { h, $, clamp } from './util.js';
import { I } from './icons.js';

let zTop = 6000;
const openWindows = [];

/* ---------------- popup menus ---------------- */
export function openMenu(items, x, y, opts = {}) {
  closeMenus();
  const menu = buildMenu(items, opts);
  menu.classList.add('qmenu');
  // LOCAL-PATCH (station): menus join the same z-ladder as dialogs
  // (dialogs increment zTop on every open/focus, so a fixed menu z would
  // eventually sink under them in long sessions).
  menu.style.zIndex = ++zTop;
  document.body.appendChild(menu);
  positionMenu(menu, x, y);
  const closer = (e) => {
    if (!menu.contains(e.target) && !e.target.closest('.qmenu')) { closeMenus(); }
  };
  const esc = (e) => { if (e.key === 'Escape') closeMenus(); };
  setTimeout(() => {
    document.addEventListener('mousedown', closer, true);
    document.addEventListener('keydown', esc, true);
    document.addEventListener('contextmenu', closer, true);
  });
  menu._cleanup = () => {
    document.removeEventListener('mousedown', closer, true);
    document.removeEventListener('keydown', esc, true);
    document.removeEventListener('contextmenu', closer, true);
  };
  activeMenus.push(menu);
  return menu;
}

export function closeMenus() {
  while (activeMenus.length) {
    const m = activeMenus.pop();
    m._cleanup?.();
    m.remove();
  }
}
const activeMenus = [];

function positionMenu(menu, x, y) {
  const r = menu.getBoundingClientRect();
  const vw = innerWidth, vh = innerHeight;
  if (x + r.width > vw - 4) x = Math.max(4, (x - r.width) || 4);
  if (y + r.height > vh - 4) y = Math.max(4, vh - r.height - 4);
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
}

function buildMenu(items, opts) {
  const menu = h('div', { class: 'qmenu' });
  let openSub = null;
  const closeSub = () => { if (openSub) { openSub.el._cleanup?.(); openSub.el.remove(); const ix = activeMenus.indexOf(openSub.el); if (ix >= 0) activeMenus.splice(ix, 1); openSub.row.classList.remove('open'); openSub = null; } };

  for (const it of items) {
    if (!it) continue;
    if (it.sep) { menu.append(h('div', { class: 'qm-sep' })); continue; }
    if (it.title) { menu.append(h('div', { class: 'qm-title', text: it.label })); continue; }
    const row = h('div', {
      class: 'qm-item' + (it.enabled === false ? ' disabled' : '') + (it.checked ? ' has-check' : ''),
    });
    if (it.checked) row.append(h('span', { class: 'qm-check', html: I('check') }));
    if (it.icon) row.append(h('span', { class: 'qm-icon', html: typeof it.icon === 'string' ? I(it.icon) : it.icon }));
    row.append(h('span', { class: 'qm-label', text: it.label }));
    if (it.shortcut) row.append(h('span', { class: 'qm-shortcut', text: it.shortcut }));
    if (it.sub) {
      row.append(h('span', { class: 'qm-arrow', html: I('chev-r') }));
      row.addEventListener('mouseenter', () => {
        closeSub();
        const el = buildMenu(it.sub, opts);
        el.classList.add('qmenu');
        document.body.appendChild(el);
        const r = row.getBoundingClientRect();
        const sr = el.getBoundingClientRect();
        let sx = r.right - 2, sy = r.top - 3;
        if (sx + sr.width > innerWidth - 4) sx = Math.max(4, r.left - sr.width + 2);
        if (sy + sr.height > innerHeight - 4) sy = Math.max(4, innerHeight - sr.height - 4);
        el.style.left = `${sx}px`; el.style.top = `${sy}px`;
        const closer = (e) => { if (!el.contains(e.target) && e.target !== row && !row.contains(e.target)) { el._cleanup?.(); el.remove(); } };
        setTimeout(() => {
          const c1 = (e) => { if (!el.contains(e.target) && !row.contains(e.target)) { el._cleanup?.(); el.remove(); } };
          document.addEventListener('mousedown', c1, true);
          el._cleanup = () => document.removeEventListener('mousedown', c1, true);
        });
        row.classList.add('open');
        openSub = { el, row };
        activeMenus.push(el);
      });
    } else {
      row.addEventListener('mouseenter', () => closeSub());
      row.addEventListener('click', () => {
        if (it.enabled === false) return;
        closeMenus();
        it.action?.();
      });
    }
    menu.append(row);
  }
  return menu;
}

/* ---------------- dialog windows ---------------- */
export function openDialog({
  title, w = 420, h: height, x, y, resizable = false, maximizable = false,
  content, buttons, onclose, winClass = '', onClose, center = true, noFooter = false,
}) {
  const win = h('div', { class: `qwin ${winClass}` });
  win.style.width = typeof w === 'number' ? w + 'px' : w;
  if (height) win.style.height = typeof height === 'number' ? height + 'px' : height;

  const tbar = h('div', { class: 'qwin-titlebar' },
    h('div', { class: 'qwin-title', text: title }),
    maximizable && h('div', { class: 'qwin-tbtn', html: I('fullscreen'), onclick: () => { /* toggle maximize */ } }),
    h('div', {
      class: 'qwin-tbtn close', html: I('close'),
      onclick: () => api.close(),
    }),
  );
  const body = h('div', { class: 'qwin-body' });
  win.append(tbar, body);

  if (resizable) {
    for (const dir of ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw']) {
      const rz = h('div', { class: `qwin-resize ${dir}` });
      rz.addEventListener('mousedown', (e) => startResize(e, win, dir));
      win.append(rz);
    }
  }

  const footer = buttons && buttons.length ? h('div', { class: 'qwin-footer' }) : null;
  if (footer) {
    for (const b of buttons) {
      if (!b) continue;
      if (b.grow) { footer.append(h('div', { class: 'grow' })); continue; }
      footer.append(h('button', {
        class: 'qpush' + (b.def ? ' default' : '') + (b.danger ? ' danger' : '') + (b.checked ? ' checked' : ''),
        text: b.label,
        onclick: () => b.action ? b.action(api) : api.close(),
      }));
    }
    body.append(content, footer);
  } else if (!noFooter) {
    body.append(content);
  } else {
    body.append(content);
  }

  document.body.appendChild(win);
  win.style.zIndex = ++zTop;

  // position
  const r = win.getBoundingClientRect();
  if (x == null) x = Math.max(8, (innerWidth - r.width) / 2);
  if (y == null) y = Math.max(8, (innerHeight - r.height) / 2.4);
  win.style.left = `${clamp(x, 0, innerWidth - 60)}px`;
  win.style.top = `${clamp(y, 0, Math.max(0, innerHeight - 60))}px`;

  tbar.addEventListener('mousedown', (e) => {
    if (e.target.closest('.qwin-tbtn')) return;
    bringToFront(win);
    const ox = e.clientX - win.offsetLeft, oy = e.clientY - win.offsetTop;
    const mv = (ev) => {
      win.style.left = `${clamp(ev.clientX - ox, -r.width + 80, innerWidth - 80)}px`;
      win.style.top = `${clamp(ev.clientY - oy, 0, innerHeight - 40)}px`;
    };
    const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
    addEventListener('mousemove', mv); addEventListener('mouseup', up);
    e.preventDefault();
  });
  win.addEventListener('mousedown', () => bringToFront(win));

  function bringToFront(w) { w.style.zIndex = ++zTop; }
  function startResize(e, w, dir) {
    e.preventDefault(); e.stopPropagation();
    const sw = w.offsetWidth, sh = w.offsetHeight, sx = e.clientX, sy = e.clientY;
    const sl = w.offsetLeft, st = w.offsetTop;
    const mv = (ev) => {
      const dx = ev.clientX - sx, dy = ev.clientY - sy;
      if (dir.includes('e')) w.style.width = Math.max(240, sw + dx) + 'px';
      if (dir.includes('s')) w.style.height = Math.max(120, sh + dy) + 'px';
      if (dir.includes('w')) { const nw = Math.max(240, sw - dx); w.style.width = nw + 'px'; w.style.left = sl + (sw - nw) + 'px'; }
      if (dir.includes('n')) { const nh = Math.max(120, sh - dy); w.style.height = nh + 'px'; w.style.top = st + (sh - nh) + 'px'; }
    };
    const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
    addEventListener('mousemove', mv); addEventListener('mouseup', up);
  }

  const api = {
    el: win, body, footer,
    close() {
      const idx = openWindows.indexOf(api); if (idx >= 0) openWindows.splice(idx, 1);
      const keep = (onclose || onClose)?.(api) === false;
      if (keep) return;
      win.remove();
    },
    setTitle(t) { tbar.querySelector('.qwin-title').textContent = t; },
    bringFront: () => bringToFront(win),
  };
  openWindows.push(api);
  return api;
}

export function closeAllDialogs() { while (openWindows.length) openWindows[openWindows.length - 1].close(); }

/* ---------------- message box ---------------- */
export function msgBox({ title = '', text = '', icon = 'info', buttons = [{ label: 'OK', def: true }], w = 380 }) {
  const body = h('div', { class: 'qmsg-body' },
    h('div', { class: 'qmsg-icon', html: I(icon === 'warning' ? 'warn' : icon === 'question' ? 'question' : 'info') }),
    h('div', { class: 'qmsg-text', text }));
  const dlg = openDialog({
    title, w, content: body, resizable: false,
    buttons: buttons.map(b => ({ ...b, action: () => { dlg.close(); b.action?.(); } })),
  });
  return dlg;
}

export function promptDlg(title, label, value, cb) {
  const input = h('input', { class: 'qinput', value: value || '', style: { width: '260px' } });
  const body = h('div', { style: { padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' } },
    h('label', { text: label }), input);
  const dlg = openDialog({
    title, w: 320, content: body, resizable: false,
    buttons: [
      { label: 'OK', def: true, action: () => { const v = input.value.trim(); if (v) { dlg.close(); cb(v); } } },
      { label: 'Cancel', action: () => dlg.close() },
    ],
  });
  setTimeout(() => { input.focus(); input.select(); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { const v = input.value.trim(); if (v) { dlg.close(); cb(v); } }
  });
  return dlg;
}

/* ---------------- tooltip ---------------- */
let tipEl = null, tipTimer = null;
document.addEventListener('mouseover', (e) => {
  const t = e.target.closest('[data-tip]');
  if (tipTimer) { clearTimeout(tipTimer); tipTimer = null; }
  if (!t) { hideTip(); return; }
  tipTimer = setTimeout(() => showTip(t.dataset.tip, t), 550);
});
document.addEventListener('mousedown', hideTip);
document.addEventListener('scroll', hideTip, true);
function showTip(text, target) {
  hideTip();
  tipEl = h('div', { id: 'qtooltip', text });
  document.body.appendChild(tipEl);
  const r = target.getBoundingClientRect(), tr = tipEl.getBoundingClientRect();
  let x = r.left + r.width / 2 - tr.width / 2;
  let y = r.bottom + 6;
  if (y + tr.height > innerHeight - 4) y = r.top - tr.height - 6;
  tipEl.style.left = `${clamp(x, 4, innerWidth - tr.width - 4)}px`;
  tipEl.style.top = `${y}px`;
}
function hideTip() { tipEl?.remove(); tipEl = null; }

/* ---------------- toast (web-only notices) ---------------- */
export function toast(msg, ms = 2600) {
  let wrap = $('#toast-wrap');
  if (!wrap) { wrap = h('div', { id: 'toast-wrap' }); document.body.appendChild(wrap); }
  const t = h('div', { class: 'toast', text: msg });
  wrap.append(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 320); }, ms);
}

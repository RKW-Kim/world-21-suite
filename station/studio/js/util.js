/* ============================================================
   OBS Studio — Web Replication · Utilities & DOM helpers
   ============================================================ */

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function h(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null) continue;
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k === 'text') e.textContent = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'dataset') Object.assign(e.dataset, v);
    else e.setAttribute(k, v);
  }
  for (const c of children.flat(9)) {
    if (c == null || c === false) continue;
    e.append(c.nodeType ? c : document.createTextNode(c));
  }
  return e;
}

let _uid = 1;
export const uid = (p = 'id') => `${p}-${(_uid++).toString(36)}-${Math.random().toString(36).slice(2, 7)}`;

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

export function fmtTime(sec) {
  sec = Math.max(0, Math.floor(sec));
  const hh = String(Math.floor(sec / 3600)).padStart(2, '0');
  const mm = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
  const ss = String(sec % 60).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

export const dbToMul = db => Math.pow(10, db / 20);
export const mulToDb = m => (m <= 0.00001 ? -Infinity : 20 * Math.log10(m));
export function fmtDb(db) {
  if (!isFinite(db) || db <= -100) return '-inf dB';
  return `${db >= 0 ? '' : '-'}${Math.abs(db).toFixed(1)} dB`;
}

/* WebCrypto SHA-256 → base64 (obs-websocket auth) */
export async function sha256B64(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  let bin = '';
  const bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

/* Keyboard shortcut string, OBS-style ("Ctrl+Alt+S") */
export function keyStr(e) {
  const parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  if (e.metaKey) parts.push('Super');
  let k = e.key;
  if (k === ' ') k = 'Space';
  else if (k.length === 1) k = k.toUpperCase();
  if (!['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) parts.push(k);
  return parts.join('+');
}

/* window-title-friendly resolution helpers */
export const parseRes = s => { const [w, hh] = s.split('x').map(Number); return { w, h: hh }; };

export function download(filename, url) {
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}

export function deepClone(o) { return JSON.parse(JSON.stringify(o)); }

export function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/* Simple emitter */
export class Emitter {
  constructor() { this._l = new Map(); }
  on(ev, fn) {
    if (!this._l.has(ev)) this._l.set(ev, new Set());
    this._l.get(ev).add(fn);
    return () => this.off(ev, fn);
  }
  off(ev, fn) { this._l.get(ev)?.delete(fn); }
  emit(ev, ...args) { this._l.get(ev)?.forEach(fn => { try { fn(...args); } catch (err) { console.error(err); } }); }
}

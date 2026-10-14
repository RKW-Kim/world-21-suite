/* ============================================================
   OBS Studio — Web Replication · Preview & Studio Mode
   Canvas compositor with drag/scale/crop/marquee, snapping
   guides, selection handles, fade transitions — mirrors OBS.
   ============================================================ */
import { h, $, $$, clamp } from './util.js';
import { I } from './icons.js';
import { obs } from './engine.js';
import { openMenu } from './ui.js';
import { ctx as dockCtx } from './docks.js';

const KIND_COLORS = {
  display_capture: ['#274a68', '#3f8cff'], window_capture: ['#3d4450', '#9a9ca2'],
  game_capture: ['#3a3f6e', '#7a8cff'], image: ['#1d4a2a', '#2ebd4e'],
  image_slideshow: ['#1d4a2a', '#2ebd4e'], color_source: ['#33383f', '#c9c9cc'],
  text: ['#3a3a3e', '#e8e8ec'], media_source: ['#3b2d63', '#a88cff'],
  vlc_source: ['#5a3a14', '#e08a2e'], browser_source: ['#163a5e', '#4aa3ff'],
  audio_input_capture: ['#4a2038', '#e0559a'], audio_output_capture: ['#16355a', '#3f8cff'],
  application_audio_capture: ['#1d4030', '#2ebd4e'], group: ['#3d2a4e', '#b06fd4'],
  scene: ['#4a3a10', '#e0b400'],
};

let remoteFrames = new Map(); // sceneId -> {img, t}

export function buildPreviewArea(root) {
  const area = h('div', { class: 'preview-area', id: 'preview-area' });
  root.append(area);

  let studioControls = null;
  let paneP = null, paneProg = null, labelP = null, labelProg = null;

  /* ---------- pane factory ---------- */
  function makePane(withCanvas) {
    const canvas = h('canvas', { class: 'obs-preview', tabindex: 0 });
    const wrap = h('div', { class: 'preview-canvas-wrap' }, canvas);
    const pane = h('div', { class: 'preview-pane' }, wrap);
    area.append(pane);
    return { pane, wrap, canvas };
  }

  function layout() {
    area.innerHTML = '';
    if (obs.S.studioMode) {
      paneP = makePane(); paneProg = makePane();
      labelP = h('div', { class: 'preview-label', html: `<b>Preview</b> — <span></span>` });
      labelProg = h('div', { class: 'preview-label', html: `<b>Program</b> — <span></span>` });
      paneP.pane.append(labelP); paneProg.pane.append(labelProg);
      studioControls = buildStudioControls();
      // OBS layout: Program on the LEFT, Preview on the RIGHT, transition controls between
      area.append(paneProg.pane, studioControls, paneP.pane);
    } else {
      paneProg = makePane();
      paneP = null; studioControls = null;
    }
    bindInteractions();
    resizeCanvases();
    updateLabels();
  }

  function buildStudioControls() {
    const btn = h('button', { class: 'studio-transition-btn' },
      h('span', { html: I('transition') }),
      h('span', { text: 'Transition' }));
    btn.addEventListener('click', () => obs.triggerTransition());
    const transSel = h('select', { class: 'qcombo', style: { width: '100%' } });
    const durInput = h('input', { class: 'qinput', type: 'number', min: 50, max: 20000, step: 50, value: obs.S.transitionDur, style: { width: '70px' } });
    const refreshSel = () => {
      transSel.innerHTML = '';
      for (const t of ['Cut', 'Fade', 'Fade to black', 'Stinger', 'Slide', 'Swipe', 'Zoom']) {
        transSel.append(h('option', { value: t, text: t, selected: t === obs.S.transition ? '' : null }));
      }
      durInput.disabled = obs.S.transition === 'Cut';
    };
    transSel.addEventListener('change', () => obs.setTransition(transSel.value));
    durInput.addEventListener('change', () => obs.setTransitionDur(parseInt(durInput.value) || 300));
    refreshSel();
    obs.on('transition', refreshSel);

    const editBtn = h('button', { class: 'qpush studio-edit-btn', text: 'Edit Scene', onclick: () => {
      // quick transform on first selected item
      const selItem = obs.selection[0];
      if (selItem) import('./dialogs.js').then(m => m.openTransform(selItem.id));
    } });
    return h('div', { class: 'studio-controls' }, btn, transSel,
      h('div', { class: 'row', style: { gap: '4px' } }, durInput, h('span', { class: 'hint', text: 'ms', style: { color: 'var(--text-dim)' } })), editBtn);
  }

  function updateLabels() {
    if (labelP) labelP.querySelector('span').textContent = obs.preview?.name || '';
    if (labelProg) labelProg.querySelector('span').textContent = obs.program?.name || '';
  }

  /* ---------- rendering ---------- */
  const scaleInfo = new Map(); // canvas -> {scale, ox, oy}
  let dpr = Math.min(devicePixelRatio || 1, 2);

  function resizeCanvases() {
    const canvases = $$('.obs-preview', area);
    for (const c of canvases) {
      const wrap = c.parentElement;
      const r = wrap.getBoundingClientRect();
      const aspect = obs.canvas.w / obs.canvas.h;
      let w = r.width - 2, hh = r.height - 2;
      if (w / hh > aspect) w = hh * aspect; else hh = w / aspect;
      w = Math.max(40, Math.floor(w)); hh = Math.max(30, Math.floor(hh));
      c.style.width = `${w}px`; c.style.height = `${hh}px`;
      c.width = Math.floor(w * dpr); c.height = Math.floor(hh * dpr);
      const scale = w / obs.canvas.w;
      scaleInfo.set(c, { scale, ox: 0, oy: 0 });
    }
  }
  new ResizeObserver(resizeCanvases).observe(area);

  function drawScene(c, scene, alphaOverride) {
    const g = c.getContext('2d');
    const si = scaleInfo.get(c) || { scale: 1 };
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, c.width, c.height);
    g.fillStyle = '#000';
    g.fillRect(0, 0, c.width, c.height);
    if (!scene) return;

    // remote frame (real OBS screenshot)
    const rf = remoteFrames.get(scene.id);
    if (rf && rf.img && rf.img.complete && rf.img.naturalWidth) {
      g.globalAlpha = alphaOverride ?? 1;
      g.drawImage(rf.img, 0, 0, c.width, c.height);
      g.globalAlpha = 1;
      return;
    }

    const s = si.scale;
    g.save();
    g.globalAlpha = alphaOverride ?? 1;
    const items = obs.itemsOf(scene.id);
    for (const it of items) {
      if (!it.visible) continue;
      const src = obs.sourceById(it.sourceId);
      if (!src) continue;
      drawItem(g, it, src, s);
    }
    g.restore();

    // selection overlay only on the interactive (preview) pane
    if (scene.id === obs.S.previewId && c === interactiveCanvas) {
      drawSelection(g, s);
      drawMarquee(g, s);
      drawSnapGuides(g, s);
    }
  }

  function drawItem(g, it, src, s) {
    const [fill, border] = KIND_COLORS[src.kind] || ['#33363c', '#8b8d92'];
    const x = it.x * s, y = it.y * s, w = it.w * s, hh = it.h * s;
    const cx = x + w / 2, cy = y + hh / 2;
    g.save();
    g.translate(cx, cy);
    g.rotate((it.rot || 0) * Math.PI / 180);
    g.translate(-cx, -cy);

    if (src.kind === 'color_source' && src.settings?.color) {
      g.fillStyle = normalizeColor(src.settings.color);
    } else {
      g.fillStyle = fill;
    }
    g.globalAlpha = 0.92;
    g.fillRect(x, y, w, hh);
    g.globalAlpha = 1;
    g.strokeStyle = border;
    g.lineWidth = 2;
    g.strokeRect(x + 1, y + 1, w - 2, hh - 2);

    // label
    const fs = Math.max(11, Math.min(16, 14 * s * 3));
    g.font = `${fs}px "Segoe UI", sans-serif`;
    g.fillStyle = '#ffffff';
    g.textAlign = 'center';
    g.textBaseline = 'middle';

    // text sources render their actual text content
    if (src.kind === 'text' && src.settings?.text) {
      const tset = src.settings;
      const lines = String(tset.text).split('\n');
      const tfs = clamp((tset.font?.size || 256) * s * 0.35, fs, Math.min(hh / Math.max(1, lines.length) * 0.72, w / 8));
      g.font = `${tset.font?.italic ? 'italic ' : ''}${tset.font?.bold ? '700 ' : '400 '}${tfs}px "${tset.font?.face || 'Arial'}", sans-serif`;
      g.fillStyle = normalizeColor(tset.color || '#ffffffff');
      g.textAlign = tset.align === 'right' ? 'right' : tset.align === 'center' ? 'center' : 'left';
      const tx = tset.align === 'right' ? x + w - 8 : tset.align === 'center' ? cx : x + 8;
      lines.forEach((ln, i) => {
        g.fillText(ln, tx, y + (hh / (lines.length + 1)) * (i + 1));
      });
      g.restore();
      return;
    }

    const label = src.name;
    const tw = g.measureText(label).width;
    const lx = cx, ly = cy;
    if (w > tw + 12 && hh > fs + 8) {
      g.fillStyle = 'rgba(0,0,0,.55)';
      g.fillRect(lx - tw / 2 - 6, ly - fs / 2 - 4, tw + 12, fs + 8);
      g.fillStyle = '#fff';
      g.fillText(label, lx, ly + 1);
    }
    // crop overlay
    if (it.crop && (it.crop.l || it.crop.t || it.crop.r || it.crop.b)) {
      g.strokeStyle = 'rgba(0,255,0,.85)';
      g.setLineDash([5, 4]);
      g.lineWidth = 1;
      g.strokeRect(x + it.crop.l * s, y + it.crop.t * s, Math.max(2, w - (it.crop.l + it.crop.r) * s), Math.max(2, hh - (it.crop.t + it.crop.b) * s));
      g.setLineDash([]);
    }
    g.restore();
  }

  function normalizeColor(c) {
    if (!c) return '#444';
    let s = c.replace('#', '');
    if (s.length === 8) s = s.slice(2);
    if (s.length === 6) return '#' + s;
    return '#' + (s.padEnd(6, '0').slice(0, 6));
  }

  let interactiveCanvas = null;
  function drawSelection(g, s) {
    const items = obs.selection;
    if (!items.length) return;
    g.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--sel-handle').trim() || '#29c8ff';
    g.fillStyle = g.strokeStyle;
    for (const it of items) {
      const bb = itemBBox(it, s);
      g.lineWidth = 1;
      g.strokeRect(bb.x, bb.y, bb.w, bb.h);
      if (it.locked) continue;
      for (const hd of handlePositions(bb)) {
        g.fillRect(hd.x - 3, hd.y - 3, 6, 6);
        g.save();
        g.strokeStyle = 'rgba(0,0,0,.6)';
        g.strokeRect(hd.x - 3, hd.y - 3, 6, 6);
        g.restore();
      }
    }
  }
  function itemBBox(it, s) {
    const pts = [
      [it.x, it.y], [it.x + it.w, it.y], [it.x + it.w, it.y + it.h], [it.x, it.y + it.h],
    ].map(([px, py]) => rotP(px, py, it));
    const xs = pts.map(p => p[0] * s), ys = pts.map(p => p[1] * s);
    return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  }
  function rotP(px, py, it) {
    if (!it.rot) return [px, py];
    const cx = it.x + it.w / 2, cy = it.y + it.h / 2;
    const a = it.rot * Math.PI / 180;
    const dx = px - cx, dy = py - cy;
    return [cx + dx * Math.cos(a) - dy * Math.sin(a), cy + dx * Math.sin(a) + dy * Math.cos(a)];
  }
  function handlePositions(bb) {
    const { x, y, w, h: hh } = bb;
    return [
      { x, y, dir: 'nw' }, { x: x + w / 2, y, dir: 'n' }, { x: x + w, y, dir: 'ne' },
      { x, y: y + hh / 2, dir: 'w' }, { x: x + w, y: y + hh / 2, dir: 'e' },
      { x, y: y + hh, dir: 'sw' }, { x: x + w / 2, y: y + hh, dir: 's' }, { x: x + w, y: y + hh, dir: 'se' },
    ];
  }

  /* marquee */
  const marquee = { active: false, x0: 0, y0: 0, x1: 0, y1: 0 };
  function drawMarquee(g, s) {
    if (!marquee.active) return;
    g.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--sel-handle').trim() || '#29c8ff';
    g.setLineDash([4, 3]);
    g.strokeRect(Math.min(marquee.x0, marquee.x1), Math.min(marquee.y0, marquee.y1), Math.abs(marquee.x1 - marquee.x0), Math.abs(marquee.y1 - marquee.y0));
    g.setLineDash([]);
  }

  /* snap guides */
  const snapGuides = { lines: [] };
  function drawSnapGuides(g, s) {
    for (const l of snapGuides.lines) {
      g.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--snap-guide').trim() || '#f0f';
      g.setLineDash([4, 3]);
      g.beginPath();
      if (l.v) { g.moveTo(l.pos * s, 0); g.lineTo(l.pos * s, obs.canvas.h * s); }
      else { g.moveTo(0, l.pos * s); g.lineTo(obs.canvas.w * s, l.pos * s); }
      g.stroke();
      g.setLineDash([]);
    }
  }

  /* ---------- interactions ---------- */
  function toWorld(c, e) {
    const r = c.getBoundingClientRect();
    const si = scaleInfo.get(c);
    return { x: (e.clientX - r.left) / si.scale, y: (e.clientY - r.top) / si.scale };
  }
  function hitItem(c, e) {
    const scene = obs.preview; if (!scene) return null;
    const w = toWorld(c, e);
    const items = obs.itemsOf(scene.id);
    for (let i = items.length - 1; i >= 0; i--) {
      const it = items[i];
      if (!it.visible) continue;
      // inverse-rotate point into item space
      let [px, py] = [w.x, w.y];
      if (it.rot) {
        const cx = it.x + it.w / 2, cy = it.y + it.h / 2;
        const a = -it.rot * Math.PI / 180;
        const dx = px - cx, dy = py - cy;
        px = cx + dx * Math.cos(a) - dy * Math.sin(a);
        py = cy + dx * Math.sin(a) + dy * Math.cos(a);
      }
      if (px >= it.x && px <= it.x + it.w && py >= it.y && py <= it.y + it.h) return it;
    }
    return null;
  }
  function hitHandle(c, e) {
    const selItems = obs.selection.filter(it => !it.locked);
    if (selItems.length !== 1) return null;
    const it = selItems[0];
    const r = c.getBoundingClientRect();
    const si = scaleInfo.get(c);
    const bb = itemBBox(it, si.scale);
    for (const hd of handlePositions(bb)) {
      if (Math.abs(e.clientX - r.left - hd.x) <= 5 && Math.abs(e.clientY - r.top - hd.y) <= 5) return { it, dir: hd.dir };
    }
    return null;
  }

  function bindInteractions() {
    const c = (paneP || paneProg).canvas;
    interactiveCanvas = c;

    c.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      const scene = obs.preview;
      const it = hitItem(c, e);
      if (it) {
        const src = obs.sourceById(it.sourceId);
        if (!it.sel) obs.select(it.id, e.ctrlKey);
        dockCtx.sourceItemMenu?.(it, src, e);
      } else {
        openMenu([
          { label: 'Enable Preview', checked: true, action: () => {} },
          { sep: 1 },
          { label: 'Screenshot (Preview)', action: () => obs.screenshotScene(scene.id, url => import('./util.js').then(u => u.download(`${scene.name}-preview.png`, url))) },
          { sep: 1 },
          { label: 'Scale to Window', action: () => resizeCanvases() },
          { label: 'Fullscreen', action: () => area.requestFullscreen?.() },
        ], e.clientX, e.clientY);
      }
    });

    c.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      c.focus();
      const scene = obs.preview; if (!scene) return;
      const handle = hitHandle(c, e);
      const it = hitItem(c, e);
      if (handle) {
        beginScale(handle.it, handle.dir, e, c);
        e.preventDefault();
      } else if (it) {
        if (!it.sel) obs.select(it.id, e.ctrlKey || e.shiftKey);
        else if (e.ctrlKey || e.shiftKey) { obs.select(it.id, true); }
        if (it.locked) return;
        beginMove(e, c);
      } else {
        obs.clearSelection();
        beginMarquee(e, c);
      }
    });

    c.addEventListener('mousemove', (e) => {
      const h = hitHandle(c, e);
      const it = hitItem(c, e);
      c.style.cursor = h ? ({ n: 'ns-resize', s: 'ns-resize', e: 'ew-resize', w: 'ew-resize', ne: 'nesw-resize', sw: 'nesw-resize', nw: 'nwse-resize', se: 'nwse-resize' })[h.dir]
        : (it ? 'move' : 'default');
    });
  }

  let drag = null;
  function beginMove(e, c) {
    const scene = obs.preview;
    const items = obs.selection.filter(it => !it.locked);
    if (!items.length) return;
    const start = toWorld(c, e);
    const starts = items.map(it => ({ it, x: it.x, y: it.y }));
    const gset = obs.settings.general;
    drag = {
      type: 'move',
      mv: (ev) => {
        const w = toWorld(c, ev);
        let dx = w.x - start.x, dy = w.y - start.y;
        if (ev.shiftKey) { if (Math.abs(dx) > Math.abs(dy)) dy = 0; else dx = 0; }
        snapGuides.lines = [];
        if (gset.snapEnabled && !ev.ctrlKey && items.length === 1) {
          const it = items[0];
          const nx = starts[0].x + dx, ny = starts[0].y + dy;
          const d = gset.snapDistance || 10;
          const cxT = (obs.canvas.w - it.w) / 2, cyT = (obs.canvas.h - it.h) / 2;
          const targetsX = [[0, 'l'], [obs.canvas.w - it.w, 'r'], [cxT, 'c']];
          const targetsY = [[0, 't'], [obs.canvas.h - it.h, 'b'], [cyT, 'c']];
          for (const [tx, tag] of targetsX) {
            if (gset.snapScreen && (tag === 'l' || tag === 'r')) { if (Math.abs(nx - tx) < d) { dx = tx - starts[0].x; snapGuides.lines.push({ v: true, pos: tx === 0 ? 0 : obs.canvas.w }); break; } }
            if (gset.snapCenter && tag === 'c') { if (Math.abs(nx - tx) < d) { dx = tx - starts[0].x; snapGuides.lines.push({ v: true, pos: obs.canvas.w / 2 }); break; } }
          }
          for (const [ty, tag] of targetsY) {
            if (gset.snapScreen && (tag === 't' || tag === 'b')) { if (Math.abs(ny - ty) < d) { dy = ty - starts[0].y; snapGuides.lines.push({ v: false, pos: ty === 0 ? 0 : obs.canvas.h }); break; } }
            if (gset.snapCenter && tag === 'c') { if (Math.abs(ny - ty) < d) { dy = ty - starts[0].y; snapGuides.lines.push({ v: false, pos: obs.canvas.h / 2 }); break; } }
          }
        }
        for (const st of starts) {
          st.it.x = Math.round(st.x + dx);
          st.it.y = Math.round(st.y + dy);
        }
        obs.emit('item-transform', items[0].id);
      },
      up: () => { snapGuides.lines = []; obs.persist(); },
    };
    attachDrag(e);
  }

  function beginScale(it, dir, e, c) {
    const start = toWorld(c, e);
    const s0 = { x: it.x, y: it.y, w: it.w, h: it.h, crop: { ...it.crop } };
    const gset = obs.settings.general;
    drag = {
      type: 'scale',
      mv: (ev) => {
        const w = toWorld(c, ev);
        let dx = w.x - start.x, dy = w.y - start.y;
        if (ev.altKey && dir.length === 1) {
          // crop mode
          const crop = { ...s0.crop };
          if (dir === 'e') crop.r = clamp(s0.crop.r + dx, 0, s0.w - 16);
          if (dir === 'w') crop.l = clamp(s0.crop.l - dx, 0, s0.w - 16);
          if (dir === 's') crop.b = clamp(s0.crop.b + dy, 0, s0.h - 16);
          if (dir === 'n') crop.t = clamp(s0.crop.t - dy, 0, s0.h - 16);
          it.crop = crop;
        } else {
          let nx = s0.x, ny = s0.y, nw = s0.w, nh = s0.h;
          if (dir.includes('e')) nw = Math.max(16, s0.w + dx);
          if (dir.includes('w')) { nw = Math.max(16, s0.w - dx); nx = s0.x + (s0.w - nw); }
          if (dir.includes('s')) nh = Math.max(16, s0.h + dy);
          if (dir.includes('n')) { nh = Math.max(16, s0.h - dy); ny = s0.y + (s0.h - nh); }
          if (ev.shiftKey && dir.length === 2) {
            const ar = s0.w / s0.h;
            if (dir.includes('e') || dir.includes('w')) nh = nw / ar; else nw = nh * ar;
            if (dir.includes('n')) ny = s0.y + (s0.h - nh);
            if (dir.includes('w')) nx = s0.x + (s0.w - nw);
          }
          it.x = Math.round(nx); it.y = Math.round(ny); it.w = Math.round(nw); it.h = Math.round(nh);
        }
        obs.emit('item-transform', it.id);
      },
      up: () => obs.persist(),
    };
    attachDrag(e);
  }

  function beginMarquee(e, c) {
    const start = toWorld(c, e);
    marquee.active = true;
    const si = scaleInfo.get(c);
    marquee.x0 = start.x * si.scale; marquee.y0 = start.y * si.scale;
    drag = {
      type: 'marquee',
      mv: (ev) => {
        const w = toWorld(c, ev);
        marquee.x1 = w.x * si.scale; marquee.y1 = w.y * si.scale;
        // live-select items intersecting
        const x0 = Math.min(marquee.x0, marquee.x1), x1 = Math.max(marquee.x0, marquee.x1);
        const y0 = Math.min(marquee.y0, marquee.y1), y1 = Math.max(marquee.y0, marquee.y1);
        const scene = obs.preview;
        for (const iid of scene.items) {
          const it = obs.S.items[iid]; if (!it) continue;
          const bb = itemBBox(it, si.scale);
          const hit = bb.x < x1 && bb.x + bb.w > x0 && bb.y < y1 && bb.y + bb.h > y0;
          it.sel = hit;
        }
        obs.emit('selection');
      },
      up: () => { marquee.active = false; },
    };
    attachDrag(e);
  }

  function attachDrag(e) {
    const mv = (ev) => drag?.mv?.(ev);
    const up = () => {
      drag?.up?.();
      drag = null;
      removeEventListener('mousemove', mv);
      removeEventListener('mouseup', up);
    };
    addEventListener('mousemove', mv);
    addEventListener('mouseup', up);
    e.preventDefault();
  }

  /* ---------- transitions ---------- */
  let transAnim = null;
  obs.on('transition-start', ({ from, to, type, dur }) => {
    if (!paneProg) return;
    const c = paneProg.canvas;
    if (type === 'Cut' || dur === 0) { return; }
    // capture "from" frame
    const snap = document.createElement('canvas');
    snap.width = c.width; snap.height = c.height;
    const g = snap.getContext('2d');
    g.drawImage(c, 0, 0);
    const start = performance.now();
    transAnim = { snap, start, dur: Math.max(120, dur), type };
  });

  /* ---------- main render loop ---------- */
  function frame() {
    const sceneP = obs.preview, sceneProg = obs.program;
    if (paneP) drawScene(paneP.canvas, sceneP);
    if (paneProg) {
      if (transAnim) {
        const t = clamp((performance.now() - transAnim.start) / transAnim.dur, 0, 1);
        drawScene(paneProg.canvas, sceneProg, 1);
        const g = paneProg.canvas.getContext('2d');
        if (transAnim.type === 'Fade') {
          g.globalAlpha = 1 - t;
          g.drawImage(transAnim.snap, 0, 0);
          g.globalAlpha = 1;
        } else if (transAnim.type === 'Fade to black') {
          g.fillStyle = `rgba(0,0,0,${Math.sin(t * Math.PI)})`;
          g.fillRect(0, 0, paneProg.canvas.width, paneProg.canvas.height);
        } else {
          // slide/zoom/swipe/stinger approximated by fade
          g.globalAlpha = 1 - t;
          g.drawImage(transAnim.snap, 0, 0);
          g.globalAlpha = 1;
        }
        if (t >= 1) transAnim = null;
      } else {
        drawScene(paneProg.canvas, sceneProg);
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  obs.on('studio', layout);
  obs.on('preview', updateLabels);
  obs.on('program', updateLabels);
  obs.on('scenes', updateLabels);
  obs.on('request-screenshot', ({ sceneId, cb }) => {
    const off = document.createElement('canvas');
    off.width = obs.canvas.w; off.height = obs.canvas.h;
    const g = off.getContext('2d');
    g.fillStyle = '#000'; g.fillRect(0, 0, off.width, off.height);
    const scene = obs.sceneById(sceneId);
    if (scene) for (const it of obs.itemsOf(sceneId)) {
      if (!it.visible) continue;
      const src = obs.sourceById(it.sourceId); if (!src) continue;
      drawItem(g, it, src, 1);
    }
    cb(off.toDataURL('image/png'));
  });

  layout();
  return { area, layout };
}

export function setRemoteFrame(sceneId, dataUrl) {
  let entry = remoteFrames.get(sceneId);
  if (!entry) { entry = { img: new Image() }; remoteFrames.set(sceneId, entry); }
  entry.img.src = dataUrl;
  entry.t = Date.now();
}

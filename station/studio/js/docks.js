/* ============================================================
   OBS Studio — Web Replication · Docks & Status Bar
   Scenes · Sources · Audio Mixer · Scene Transitions ·
   Controls · Stats — with full context menus and interactions.
   ============================================================ */
import { h, $, fmtTime, fmtDb, dbToMul, clamp } from './util.js';
import { I, SOURCE_ICON } from './icons.js';
import { obs, AUDIO_KINDS, TRANSITIONS } from './engine.js';
import { openMenu, openDialog, msgBox, promptDlg } from './ui.js';

export const sel = { sceneId: null }; // selected scene row
export const ctx = {};                // context-menu registry (shared with preview)

/* ============================ Scenes dock ============================ */
export function buildScenesDock(root) {
  const list = h('div', { class: 'qlist', tabindex: 0 });
  const dock = h('div', { class: 'dock', id: 'dock-scenes' },
    h('div', { class: 'dock-header', text: 'Scenes' }),
    h('div', { class: 'dock-body' },
      list,
      h('div', { class: 'dock-toolbar bottom' },
        tbBtn('plus', 'Add Scene', () => promptDlg('Add Scene', 'Please enter the name of the scene', nextSceneName(), v => { obs.createScene(v); obs.setProgram(obs.S.scenes[obs.S.scenes.length - 1].id); })),
        tbBtn('minus', 'Remove Scene', () => { const sc = obs.program; if (!sc) return; removeSceneDlg(sc); }),
        tbBtn('up', 'Move Up', () => moveScene(-1)),
        tbBtn('down', 'Move Down', () => moveScene(1)),
      )));
  root.append(dock);

  function nextSceneName() {
    const taken = new Set(obs.S.scenes.map(s => s.name));
    let i = obs.S.scenes.length + 1;
    while (taken.has(`Scene ${i}`)) i++;
    return obs.S.scenes.length ? `Scene ${i}` : 'Scene';
  }
  function moveScene(dir) {
    const sc = obs.program; if (!sc) return;
    const i = obs.S.scenes.indexOf(sc);
    obs.reorderScene(sc.id, i + dir);
  }
  function removeSceneDlg(sc) {
    msgBox({
      title: 'Confirm Remove', icon: 'question',
      text: `Are you sure you wish to remove '${sc.name}'?`,
      buttons: [
        { label: 'Yes', def: true, action: () => obs.removeScene(sc.id) },
        { label: 'No', action: () => {} },
      ],
    });
  }

  function render() {
    list.innerHTML = '';
    for (const sc of obs.S.scenes) {
      const active = sc.id === obs.S.programId;
      const row = h('div', {
        class: 'qlist-row' + (active ? ' selected' : ''),
        draggable: 'true',
        onmousedown: (e) => {
          if (e.button !== 0) return;
          if (obs.S.studioMode) obs.setPreview(sc.id); else obs.setProgram(sc.id);
          list.focus();
        },
        ondblclick: () => promptDlg('Rename Scene', `Please enter a new name for the scene below:`, sc.name, v => obs.renameScene(sc.id, v)),
        oncontextmenu: (e) => { e.preventDefault(); e.stopPropagation(); if (!active) { obs.S.studioMode ? obs.setPreview(sc.id) : obs.setProgram(sc.id); } sceneMenu(sc, e); },
      },
        h('span', { class: 'row-icon', html: I('scene') }),
        h('span', { class: 'row-label', text: sc.name }),
      );
      row.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/scene-id', sc.id); e.dataTransfer.effectAllowed = 'move'; });
      row.addEventListener('dragover', (e) => { e.preventDefault(); row.classList.add('drop-above'); });
      row.addEventListener('dragleave', () => row.classList.remove('drop-above'));
      row.addEventListener('drop', (e) => {
        e.preventDefault(); row.classList.remove('drop-above');
        const id = e.dataTransfer.getData('text/scene-id');
        if (id && id !== sc.id) obs.reorderScene(id, obs.S.scenes.findIndex(s => s.id === sc.id));
      });
      list.append(row);
    }
  }

  function sceneMenu(sc, e) {
    const i = obs.S.scenes.indexOf(sc);
    openMenu([
      { label: 'Add Scene', icon: 'plus', action: () => promptDlg('Add Scene', 'Please enter the name of the scene', nextSceneName(), v => obs.createScene(v)) },
      { label: 'Duplicate Scene', action: () => obs.duplicateScene(sc.id) },
      { sep: 1 },
      { label: 'Order', sub: [
        { label: 'Move Up', action: () => obs.reorderScene(sc.id, i - 1) },
        { label: 'Move Down', action: () => obs.reorderScene(sc.id, i + 1) },
        { label: 'Move to Beginning', action: () => obs.reorderScene(sc.id, 0) },
        { label: 'Move to End', action: () => obs.reorderScene(sc.id, obs.S.scenes.length - 1) },
      ]},
      { sep: 1 },
      { label: 'Rename', action: () => promptDlg('Rename Scene', `Please enter a new name for the scene below:`, sc.name, v => obs.renameScene(sc.id, v)) },
      { label: 'Remove', icon: 'trash', action: () => removeSceneDlg(sc) },
      { sep: 1 },
      { label: 'Filters', action: () => import('./dialogs.js').then(m => m.openFiltersForScene(sc)) },
      { label: 'Per-scene Transition Override', sub: [
        { label: 'Default (Global)', checked: !sc.transitionOverride, action: () => { delete sc.transitionOverride; obs.emitc('scenes', { action: 'override' }); } },
        ...(['Cut', 'Fade', 'Fade to black', 'Slide'].map(t => ({ label: t, checked: sc.transitionOverride === t, action: () => { sc.transitionOverride = t; obs.emitc('scenes', { action: 'override' }); } }))),
      ]},
      { sep: 1 },
      { label: 'Multiview (Scene)', action: () => import('./tools.js').then(m => m.openMultiview(sc.id)) },
      { label: 'Screenshot (Scene)', action: () => obs.screenshotScene(sc.id, url => import('./util.js').then(u => u.download(`${sc.name}.png`, url))) },
      { label: 'Projector (Scene)', action: () => import('./tools.js').then(m => m.openProjector(sc.id, sc.name)) },
    ], e.clientX, e.clientY);
  }

  obs.on('scenes', render);
  obs.on('program', render);
  obs.on('preview', render);
  obs.on('studio', render);
  obs.on('collection', render);
  render();
  return dock;
}

function tbBtn(icon, tip, action) {
  return h('div', { class: 'dock-btn', html: I(icon), 'data-tip': tip, onclick: action });
}

/* ============================ Sources dock ============================ */
export function buildSourcesDock(root) {
  const list = h('div', { class: 'qlist', tabindex: 0 });
  const dock = h('div', { class: 'dock', id: 'dock-sources' },
    h('div', { class: 'dock-header', text: 'Sources' }),
    h('div', { class: 'dock-body' },
      list,
      h('div', { class: 'dock-toolbar bottom' },
        tbBtn('plus', 'Add Source', (e, btn) => addSourceMenu(e.clientX ?? 60, e.clientY ?? 40)),
        tbBtn('minus', 'Remove Selected Source(s)', removeSelected),
        tbBtn('props', 'Properties', openPropsSelected),
        tbBtn('filter', 'Filters', openFiltersSelected),
      )));
  root.append(dock);

  const toolbarBtns = dock.querySelectorAll('.dock-btn');

  function curScene() { return obs.preview; }

  function render() {
    const sc = curScene();
    list.innerHTML = '';
    if (!sc) return;
    // OBS shows the Sources list in reverse stacking order: front-most source at the top
    const items = obs.itemsOf(sc.id).slice().reverse();
    for (const it of items) {
      const src = obs.sourceById(it.sourceId);
      if (!src) continue;
      const row = h('div', {
        class: 'qlist-row' + (it.sel ? ' selected' : ''),
        draggable: 'true',
        onmousedown: (e) => { if (e.button === 0) obs.select(it.id, e.ctrlKey || e.shiftKey); list.focus(); },
        ondblclick: () => import('./dialogs.js').then(m => m.openProperties(src)),
        oncontextmenu: (e) => { e.preventDefault(); e.stopPropagation(); if (!it.sel) obs.select(it.id, e.ctrlKey); sourceItemMenu(it, src, e); },
      },
        h('span', {
          class: 'row-vis' + (it.visible ? '' : ' hidden-src'), html: I(it.visible ? 'eye' : 'eye-off'),
          'data-tip': it.visible ? 'Hide source' : 'Show source',
          onclick: (e) => { e.stopPropagation(); obs.setItemVisible(it.id, !it.visible); },
        }),
        h('span', { class: 'row-icon', html: I(SOURCE_ICON[src.kind] || 'scene') }),
        h('span', { class: 'row-label' + (it.visible ? '' : ' row-ghost'), text: src.name }),
        h('span', {
          class: 'row-lock dim' + (it.locked ? ' locked' : ''), html: I(it.locked ? 'lock' : 'unlock'),
          'data-tip': it.locked ? 'Unlock source' : 'Lock source',
          onclick: (e) => { e.stopPropagation(); obs.setItemLocked(it.id, !it.locked); },
        }),
      );
      row.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/item-id', it.id); e.dataTransfer.effectAllowed = 'move'; });
      row.addEventListener('dragover', (e) => {
        e.preventDefault();
        const r = row.getBoundingClientRect();
        const above = e.clientY < r.top + r.height / 2;
        row.classList.toggle('drop-above', above); row.classList.toggle('drop-below', !above);
      });
      row.addEventListener('dragleave', () => row.classList.remove('drop-above', 'drop-below'));
      row.addEventListener('drop', (e) => {
        e.preventDefault();
        const above = row.classList.contains('drop-above');
        row.classList.remove('drop-above', 'drop-below');
        const id = e.dataTransfer.getData('text/item-id');
        if (!id || id === it.id) return;
        // list renders in reverse stacking order: visual "above" = higher array index
        const i = sc.items.indexOf(it.id);
        obs.reorderItem(sc.id, id, above ? i + 1 : i);
      });
      list.append(row);
    }
    // toolbar enable state
    const hasSel = obs.selection.length > 0;
    toolbarBtns[1].classList.toggle('disabled', !hasSel);
    toolbarBtns[2].classList.toggle('disabled', !hasSel);
    toolbarBtns[3].classList.toggle('disabled', !hasSel);
  }

  function removeSelected() {
    const items = obs.selection;
    if (!items.length) return;
    const sc = curScene();
    for (const it of items) obs.removeItem(sc.id, it.id);
  }
  function openPropsSelected() {
    const it = obs.selection[0]; if (!it) return;
    import('./dialogs.js').then(m => m.openProperties(obs.sourceById(it.sourceId)));
  }
  function openFiltersSelected() {
    const it = obs.selection[0]; if (!it) return;
    import('./dialogs.js').then(m => m.openFilters(obs.sourceById(it.sourceId)));
  }

  function sourceItemMenu(it, src, e) {
    const sc = curScene();
    const multi = obs.selection.length > 1;
    const label = multi ? `${obs.selection.length} sources` : src.name;
    openMenu([
      { label: 'Add Source', icon: 'plus', sub: sourceTypesSubmenu() },
      { sep: 1 },
      { label: `Lock ${label}`, checked: it.locked, action: () => obs.setItemLocked(it.id, !it.locked) },
      { sep: 1 },
      { label: 'Order', sub: [
        { label: 'Move Up', action: () => obs.itemOrder(sc.id, it.id, 'up') },
        { label: 'Move Down', action: () => obs.itemOrder(sc.id, it.id, 'down') },
        { sep: 1 },
        { label: 'Move to Top', action: () => obs.itemOrder(sc.id, it.id, 'top') },
        { label: 'Move to Bottom', action: () => obs.itemOrder(sc.id, it.id, 'bottom') },
      ]},
      { label: 'Transform', sub: transformSubmenu(it, sc) },
      { label: 'Scale Filtering', sub: ['Disable', 'Point', 'Bilinear', 'Bicubic', 'Lanczos', 'Area'].map(f => ({
          label: f, checked: (it.scaleFilter || 'Disable') === f, action: () => { it.scaleFilter = f; obs.emitc('item-transform', it.id); },
        })) },
      { label: 'Blend Mode', sub: ['Normal', 'Additive', 'Subtract', 'Multiply', 'Screen', 'Lighten', 'Darken'].map(b => ({
          label: b, checked: (it.blendMode || 'Normal') === b, action: () => { it.blendMode = b; obs.emitc('item-transform', it.id); },
        })) },
      { sep: 1 },
      { label: 'Projector (Source)', action: () => import('./tools.js').then(m => m.openProjector(null, src.name)) },
      { label: 'Screenshot (Source)', action: () => obs.log('info', `Saved screenshot of '${src.name}'`) },
      { sep: 1 },
      { label: `Rename${multi ? ' (first)' : ''}`, action: () => promptDlg('Rename Source', `Please enter a new name for the source below:`, src.name, v => obs.renameSource(src.id, v)) },
      { label: `Remove ${label}`, icon: 'trash', action: removeSelected },
      { sep: 1 },
      { label: multi ? 'Group Selected Sources' : 'Group', action: () => groupSelected() },
      { sep: 1 },
      { label: 'Properties', icon: 'props', action: openPropsSelected },
      { label: 'Filters', icon: 'filter', action: openFiltersSelected },
    ], e.clientX, e.clientY);
  }

  function transformSubmenu(it, sc) {
    const openT = () => import('./dialogs.js').then(m => m.openTransform(it.id));
    return [
      { label: 'Edit Transform', action: openT },
      { sep: 1 },
      { label: 'Reset Transform', action: () => obs.resetItemTransform(it.id) },
      { sep: 1 },
      { label: 'Fit to Screen', action: () => obs.fitItemToScreen(it.id, false) },
      { label: 'Stretch to Screen', action: () => obs.fitItemToScreen(it.id, true) },
      { label: 'Center to Screen', action: () => obs.centerItem(it.id) },
      { label: 'Center Horizontally', action: () => obs.centerItem(it.id, 'h') },
      { label: 'Center Vertically', action: () => obs.centerItem(it.id, 'v') },
      { sep: 1 },
      { label: 'Flip Vertical', action: () => obs.setItemTransform(it.id, { scaleY: -(it.scaleY || 1) }) },
      { label: 'Flip Horizontal', action: () => obs.setItemTransform(it.id, { scaleX: -(it.scaleX || 1) }) },
      { label: 'Rotate 90 degrees CW', action: () => obs.setItemTransform(it.id, { rot: ((it.rot || 0) + 90) % 360 }) },
      { label: 'Rotate 90 degrees CCW', action: () => obs.setItemTransform(it.id, { rot: ((it.rot || 0) + 270) % 360 }) },
      { label: 'Rotate 180 degrees', action: () => obs.setItemTransform(it.id, { rot: ((it.rot || 0) + 180) % 360 }) },
    ];
  }

  function groupSelected() {
    const selItems = obs.selection;
    if (selItems.length < 2) { toastMin('Select at least two sources to group'); return; }
    const sc = curScene();
    promptDlg('Add Group', 'Please enter the name of the group', 'Group', (name) => {
      const g = obs.createSource('group', name, {}, { noScene: true });
      const gi = obs.addItem(sc.id, g.id);
      for (const it of selItems) obs.removeItem(sc.id, it.id, true);
      // group children: store on item
      gi.children = selItems.map(x => x.id);
      gi.w = obs.canvas.w; gi.h = obs.canvas.h; gi.x = 0; gi.y = 0;
      obs.emitc('items', { action: 'grouped' });
    });
  }

  function sourceTypesSubmenu() {
    return obs.S.sources
      .filter(s => !s.global)
      .slice(0, 0)
      .concat([{ __types: true }]) && SOURCE_TYPES.map(t => ({
        label: t.name, icon: SOURCE_ICON[t.kind] || 'scene',
        action: () => import('./dialogs.js').then(m => m.createSourceFlow(t)),
      }));
  }

  obs.on('items', render);
  obs.on('selection', render);
  obs.on('program', render);
  obs.on('preview', render);
  obs.on('sources', render);
  obs.on('studio', render);
  obs.on('collection', render);
  obs.on('item-transform', render);
  ctx.sourceItemMenu = sourceItemMenu;
  ctx.transformSubmenu = transformSubmenu;
  ctx.removeSelected = removeSelected;
  render();
  return dock;
}

function toastMin(msg) { import('./ui.js').then(m => m.toast(msg)); }

export function addSourceMenu(x, y) {
  import('./dialogs.js').then(m => {
    openMenu(SOURCE_TYPES.map(t => ({
      label: t.name, icon: SOURCE_ICON[t.kind] || 'scene',
      action: () => m.createSourceFlow(t),
    })), x, y);
  });
}

/* ============================ Audio Mixer dock ============================ */
export function buildMixerDock(root) {
  const mixer = h('div', { class: 'mixer' });
  // LOCAL-PATCH (station): LIVE/SIM badge — answers "is the mixer showing
  // the plane or a simulation?" at a glance. Never guess again.
  const liveBadge = h('span', { class: 'mx-live off', text: 'SIM', title: 'SIM: simulated levels (not connected, or no meter data yet). LIVE: real peaks from the render plane.' });
  const dock = h('div', { class: 'dock', id: 'dock-mixer' },
    h('div', { class: 'dock-header' }, h('span', { text: 'Audio Mixer' }), liveBadge),
    h('div', { class: 'dock-body' }, mixer));
  root.append(dock);

  mixer.addEventListener('contextmenu', (e) => {
    if (e.target.closest('.mixer-channel')) return;
    e.preventDefault();
    openMenu([
      { label: 'Vertical Layout', checked: obs.settings.ui.mixerLayout === 'vertical', action: () => { obs.settings.ui.mixerLayout = 'vertical'; obs.emit('mixer-layout'); obs.persist(); } },
      { label: 'Horizontal Layout', checked: obs.settings.ui.mixerLayout === 'horizontal', action: () => { obs.settings.ui.mixerLayout = 'horizontal'; obs.emit('mixer-layout'); obs.persist(); } },
    ], e.clientX, e.clientY);
  });

  let dragDb = null;
  const channelEls = new Map();

  function channelMenu(s, e) {
    openMenu([
      { label: 'Lock Volume', checked: !!s.volLocked, action: () => { s.volLocked = !s.volLocked; obs.emit('mixer', { id: s.id }); } },
      { sep: 1 },
      { label: 'Hide', action: () => toastMin('Audio sources cannot be hidden in the mixer (OBS parity)') },
      { label: 'Copy Volume to', sub: [
        { label: 'All', action: () => { for (const x of obs.mixerSources()) obs.setVolumeDb(x.id, s.volumeDb); } },
        ...obs.mixerSources().filter(x => x.id !== s.id).map(x => ({ label: x.name, action: () => obs.setVolumeDb(x.id, s.volumeDb) })),
      ]},
      { sep: 1 },
      { label: 'Deactivate', action: () => obs.log('info', `Deactivated '${s.name}'`) },
      { label: 'Activate', action: () => obs.log('info', `Activated '${s.name}'`) },
      { sep: 1 },
      { label: 'Vertical Layout', checked: obs.settings.ui.mixerLayout === 'vertical', action: () => { obs.settings.ui.mixerLayout = 'vertical'; obs.emit('mixer-layout'); obs.persist(); } },
      { label: 'Horizontal Layout', checked: obs.settings.ui.mixerLayout === 'horizontal', action: () => { obs.settings.ui.mixerLayout = 'horizontal'; obs.emit('mixer-layout'); obs.persist(); } },
      { sep: 1 },
      { label: 'Filters', action: () => import('./dialogs.js').then(m => m.openFilters(s)) },
      { label: 'Properties', action: () => import('./dialogs.js').then(m => m.openProperties(s)) },
      { sep: 1 },
      { label: 'Advanced Audio Properties', action: () => import('./dialogs.js').then(m => m.openAdvAudio()) },
    ], e.clientX, e.clientY);
  }

  function render() {
    mixer.innerHTML = '';
    channelEls.clear();
    mixer.classList.toggle('vertical', obs.settings.ui.mixerLayout === 'vertical');
    for (const s of obs.mixerSources()) {
      const slider = h('input', {
        class: 'obs-range', type: 'range', min: -60, max: 0, step: 0.1,
        value: clamp(s.volumeDb, -60, 0),
        oninput: (e) => { obs.setVolumeDb(s.id, parseFloat(e.target.value)); ch.classList.add('dragging-vol'); },
        onchange: () => ch.classList.remove('dragging-vol'),
      });
      const meterFill = h('div', { class: 'fill' });
      const meterPeak = h('div', { class: 'peak' });
      const meter = h('div', { class: 'mx-meter' }, meterFill, meterPeak);
      const ch = h('div', {
        class: 'mixer-channel' + (s.selected ? ' selected' : ''),
        oncontextmenu: (e) => { e.preventDefault(); e.stopPropagation(); channelMenu(s, e); },
      },
        h('div', {
          class: 'mx-speaker' + (s.muted ? ' muted' : ''),
          html: I(s.muted ? 'vol-mute' : 'vol'),
          'data-tip': s.muted ? 'Unmute' : 'Mute',
          onclick: () => obs.toggleMute(s.id),
        }),
        h('div', { class: 'mx-main' },
          h('div', { class: 'mx-name', text: s.name }),
          h('div', { class: 'mx-sliderrow' }, h('div', { class: 'mx-slider' }, slider)),
        ),
        h('div', { class: 'mx-meter-wrap' }, meter),
        h('div', { class: 'mx-db', text: fmtDb(s.volumeDb) }),
      );
      channelEls.set(s.id, { meterFill, meterPeak, ch });
      mixer.append(ch);
    }
  }

  /* meter animation */
  let raf;
  let lastBadge = '';
  const tick = () => {
    const live = obs.metersLive();
    const badge = live ? 'LIVE' : 'SIM';
    if (badge !== lastBadge) {
      lastBadge = badge;
      liveBadge.textContent = badge;
      liveBadge.classList.toggle('on', live);
      liveBadge.classList.toggle('off', !live);
    }
    for (const [id, els] of channelEls) {
      const { level } = obs.getLevel(id);
      const pct = clamp(Math.pow(level, 0.6) * 100, 0, 100);
      els.meterFill.style.height = pct.toFixed(1) + '%';
      const prevPeak = els._peak && performance.now() - els._peakT < 900 ? els._peak : pct;
      if (pct >= (els._peak ?? 0)) { els._peak = pct; els._peakT = performance.now(); }
      els.meterPeak.style.bottom = `calc(${clamp(els._peak ?? 0, 0, 100).toFixed(1)}% - 1px)`;
      els.meterPeak.style.display = els._peak > 2 ? 'block' : 'none';
    }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);

  obs.on('mixer-structure', render);
  obs.on('mixer', render);
  obs.on('mixer-layout', render);
  obs.on('program', render);
  obs.on('sources', render);
  obs.on('collection', render);
  render();
  return dock;
}

/* ============================ Transitions dock ============================ */
export function buildTransitionsDock(root) {
  const list = h('div', { class: 'qlist transitions-list' });
  const durInput = h('input', { class: 'qinput', type: 'number', min: 50, max: 20000, step: 50, value: obs.S.transitionDur, style: { width: '74px' } });
  const dock = h('div', { class: 'dock', id: 'dock-transitions' },
    h('div', { class: 'dock-header', text: 'Scene Transitions' }),
    h('div', { class: 'dock-body' },
      h('div', { class: 'dock-toolbar' },
        tbBtn('plus', 'Add custom transitions (web)', () => toastMin('Custom transitions require OBS theme files (web replica)')),
        tbBtn('minus', 'Remove transition', () => toastMin('Built-in transitions cannot be removed (OBS parity)')),
        tbBtn('props', 'Transition Properties', () => toastMin('The selected transition has no properties')),
      ),
      list,
      h('div', { class: 'transition-duration' },
        h('label', { text: 'Duration' }), durInput, h('span', { class: 'hint', text: 'ms', style: { color: 'var(--text-dim)' } }))));
  root.append(dock);

  const custom = [];
  function render() {
    list.innerHTML = '';
    const names = [...TRANSITIONS, ...custom];
    for (const n of names) {
      const row = h('div', {
        class: 'qlist-row' + (n === obs.S.transition ? ' selected' : ''),
        onclick: () => obs.setTransition(n),
        oncontextmenu: (e) => { e.preventDefault(); if (!['Cut', 'Fade'].includes(n)) openMenu([
          { label: 'Remove', action: () => { custom.splice(custom.indexOf(n), 1); render(); } },
        ], e.clientX, e.clientY); },
      }, h('span', { class: 'row-icon', html: I('transition') }), h('span', { class: 'row-label', text: n }));
      list.append(row);
    }
    durInput.disabled = obs.S.transition === 'Cut';
  }
  durInput.addEventListener('change', () => obs.setTransitionDur(parseInt(durInput.value) || 300));
  obs.on('transition', render);
  render();
  return dock;
}

/* ============================ Controls dock ============================ */
export function buildControlsDock(root) {
  const box = h('div', { class: 'controls' });
  const dock = h('div', { class: 'dock', id: 'dock-controls' },
    h('div', { class: 'dock-header', text: 'Controls' }),
    h('div', { class: 'dock-body' }, box));
  root.append(dock);

  let btnStream, btnRecord, btnVcam, btnReplay, btnSettings, btnExit, btnStudio;

  function render() {
    const o = obs.S.outputs;
    box.innerHTML = '';
    // LOCAL-PATCH (station): Studio Mode toggle lives in Controls (OBS
    // parity — it was hotkey-only). Mirrors via the existing setStudioMode.
    btnStudio = h('button', {
      class: 'ctrl-btn' + (obs.S.studioMode ? ' checked' : ''),
      text: obs.S.studioMode ? 'Exit Studio Mode' : 'Studio Mode',
      onclick: () => obs.setStudioMode(!obs.S.studioMode),
    });
    btnStream = h('button', { class: 'ctrl-btn' + (o.streaming ? ' live' : ''), text: o.streaming ? 'Stop Streaming' : 'Start Streaming', onclick: () => o.streaming ? obs.stopStream() : obs.startStream() });
    btnRecord = h('button', { class: 'ctrl-btn' + (o.recording ? ' live' : ''), text: o.recording ? 'Stop Recording' : 'Start Recording', onclick: () => o.recording ? obs.stopRecord() : obs.startRecord() });
    btnVcam = h('button', { class: 'ctrl-btn', text: o.vcam ? 'Stop Virtual Camera' : 'Start Virtual Camera', onclick: () => obs.toggleVCam() });
    btnReplay = h('button', { class: 'ctrl-btn' + (o.replay ? ' checked' : ''), text: o.replay ? 'Stop Replay Buffer' : 'Start Replay Buffer', onclick: () => obs.toggleReplay() });
    btnSettings = h('button', { class: 'ctrl-btn', text: 'Settings', onclick: () => import('./settings.js').then(m => m.openSettings()) });
    btnExit = h('button', { class: 'ctrl-btn', text: 'Exit', onclick: exitApp });
    box.append(
      btnStudio, btnStream, btnRecord, btnVcam, btnReplay,
      h('div', { class: 'controls-row' }, btnSettings, btnExit));
  }
  obs.on('outputs', render);
  obs.on('studio', render);
  obs.on('transition', render);
  render();
  return dock;
}

function exitApp() {
  msgBox({
    title: 'Exit', icon: 'question',
    text: 'You have active outputs that will stop when you exit.\nAre you sure you want to exit OBS?',
    buttons: [
      { label: 'Exit', def: true, action: () => obs.log('info', 'Exit requested (web replica stays open)') },
      { label: 'Cancel', action: () => {} },
    ],
  });
}

/* ============================ Stats dock ============================ */
export function buildStatsDock(root) {
  const grid = h('div', { class: 'stats-grid', style: { padding: '8px 10px' } });
  const dock = h('div', { class: 'dock', id: 'dock-stats' },
    h('div', { class: 'dock-header', text: 'Stats' }),
    h('div', { class: 'dock-body' }, grid));
  root.append(dock);

  function render() {
    const st = obs._sim, o = obs.S.outputs;
    grid.innerHTML = '';
    const add = (k, v) => { grid.append(h('div', { class: 'k', text: k }), h('div', { class: 'v', text: v })); };
    grid.append(h('div', { class: 'stats-sep' }));
    add('Live time', o.streaming ? fmtTime(o.streamTime) : 'Inactive');
    add('Data rate', o.streaming ? `${Math.round(obs._sim.kbps || 0)} kb/s` : '-');
    grid.append(h('div', { class: 'stats-sep' }));
    add('Recording time', o.recording ? fmtTime(o.recTime) : 'Inactive');
    grid.append(h('div', { class: 'stats-sep' }));
    add('Dropped frames', o.streaming ? `${obs._sim.dropped || 0}` : '-');
    add('CPU usage', `${(st.cpu || 0).toFixed(1)}%`);
    add('Memory usage', `${Math.round(st.mem || 0)} MB`);
    add('FPS', `${(st.fps || 60).toFixed(1)}`);
    add('Average time to render frame', `${(st.renderMs || 0).toFixed(1)} ms`);
  }
  obs.on('stats-tick', render);
  obs.on('outputs-tick', render);
  render();
  return dock;
}

/* ============================ Status bar ============================ */
export function buildStatusBar(root) {
  const bar = h('div', { id: 'statusbar' });
  root.append(bar);

  function render() {
    const o = obs.S.outputs, st = obs._sim;
    bar.innerHTML = '';
    const seg = (children, cls) => h('div', { class: 'sb-seg ' + (cls || '') }, ...[].concat(children));

    if (obs.S.studioMode) bar.append(seg([h('span', { text: 'Studio Mode' })]));
    if (o.streaming) {
      bar.append(seg([I('broadcast'), h('span', { class: 'sb-timer', text: fmtTime(o.streamTime) })], 'live-active'));
      bar.append(seg([I('up'), h('span', { text: `${Math.round(obs._sim.kbps || 0).toLocaleString()} kb/s` })]));
      bar.append(seg([h('span', { text: `Dropped Frames: ${obs._sim.dropped || 0}` })]));
    }
    if (o.recording) {
      bar.append(seg([I('record'), h('span', { class: 'sb-timer', text: fmtTime(o.recTime) })], 'rec-active'));
      if (o.paused) bar.append(seg([h('span', { text: 'PAUSED' })], 'rec-active'));
    }
    if (o.replay) bar.append(seg([I('replay'), h('span', { text: 'Replay' })]));
    if (o.vcam) bar.append(seg([I('camera'), h('span', { text: 'Virtual Camera active' })]));

    bar.append(h('div', { class: 'sb-seg sb-spacer' }));

    if (!obs.wsMode) {
      bar.append(seg([h('span', { text: `CPU ${(st.cpu || 0).toFixed(1)}%, ${(st.fps || 60).toFixed(1)} fps, ${Math.round(st.mem || 0)} MB` })]));
    }
    bar.append(seg([h('span', { text: `${obs.canvas.w}x${obs.canvas.h}` })]));
    const wsBadge = seg([
      h('span', { text: obs.wsMode ? 'WebSocket: Connected' : 'WebSocket: Off' }),
    ], obs.wsMode ? 'live-active' : '');
    wsBadge.setAttribute('data-tip', obs.wsMode ? 'Connected to a real OBS via obs-websocket v5' : 'Not connected — simulated core active');
    bar.append(wsBadge);
  }
  obs.on('outputs', render);
  obs.on('outputs-tick', render);
  obs.on('stats-tick', render);
  obs.on('ws-status', render);
  obs.on('studio', render);
  render();
  return bar;
}

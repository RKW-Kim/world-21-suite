/* ============================================================
   OBS Studio — Web Replication · Main / Bootstrap
   Title bar · Menu bar · Toolbar · Workspace assembly ·
   Global hotkeys · Theme engine · Docks wiring
   ============================================================ */
import { h, $, fmtTime, keyStr } from './util.js';
import { I, ObsLogo } from './icons.js';
import { obs, SOURCE_TYPES } from './engine.js';
import { openMenu, openDialog, msgBox, promptDlg, toast } from './ui.js';
import { buildScenesDock, buildSourcesDock, buildMixerDock, buildTransitionsDock, buildControlsDock, buildStatsDock, buildStatusBar, addSourceMenu } from './docks.js';
import { buildPreviewArea } from './preview.js';
import { openSettings } from './settings.js';
import * as tools from './tools.js';
import { wsApi, openConnect } from './ws.js';

const app = {};

/* ---------------- theme ---------------- */
function applyTheme() {
  const t = obs.settings.general.theme;
  let theme = t;
  if (t === 'System Theme') theme = matchMedia('(prefers-color-scheme: light)').matches ? 'Light' : 'Dark';
  document.documentElement.dataset.theme = theme;
}
matchMedia('(prefers-color-scheme: light)').addEventListener?.('change', applyTheme);
obs.on('theme', applyTheme);

/* ---------------- title bar ---------------- */
function buildTitlebar(root) {
  const tb = h('div', { id: 'titlebar' },
    h('div', { class: 'tb-icon', html: ObsLogo(16) }),
    h('div', { class: 'tb-title', id: 'win-title' }),
    h('div', { class: 'tb-spacer' }),
    h('div', { class: 'tb-btn', html: I('minus'), 'data-tip': 'Minimize', onclick: () => toast('Minimize is native-window behavior (web replica)') }),
    h('div', { class: 'tb-btn', html: I('fullscreen'), 'data-tip': 'Maximize', onclick: () => document.documentElement.requestFullscreen?.() }),
    h('div', { class: 'tb-btn close', html: I('close'), 'data-tip': 'Close', onclick: () => tools.openWizard === null ? null : confirmExit() }),
  );
  root.append(tb);

  function renderTitle() {
    $('#win-title').textContent = `OBS 30.2.3 - Profile: ${obs.S.activeProfile} - Scenes: ${obs.S.activeCollection}`;
  }
  obs.on('profile', renderTitle);
  obs.on('collection', renderTitle);
  renderTitle();
}
function confirmExit() {
  msgBox({
    title: 'Exit', icon: 'question',
    text: 'Are you sure you want to quit OBS?',
    buttons: [
      { label: 'Exit', def: true, action: () => toast('This is a web replica — the tab stays open') },
      { label: 'Cancel', action: () => {} },
    ],
  });
}

/* ---------------- menu bar ---------------- */
function buildMenubar(root) {
  const bar = h('div', { id: 'menubar' });
  root.append(bar);
  let openBtn = null;

  const menus = {
    File: () => [
      { label: 'Show Recordings', action: () => toast(`Recording folder: ${obs.settings.output.simple.recPath}`) },
      { label: 'Remux Recordings', action: () => tools.openRemux() },
      { sep: 1 },
      { label: 'Settings', shortcut: 'Ctrl+,', action: () => openSettings() },
      { label: 'Show Settings Folder', action: () => toast('Settings folder is localStorage in the web replica') },
      { sep: 1 },
      { label: 'Exit', action: confirmExit },
    ],
    Edit: () => [
      { label: 'Undo', shortcut: 'Ctrl+Z', enabled: !!obs.undoStack?.length, action: () => obs.undo?.() },
      { label: 'Redo', shortcut: 'Ctrl+Y', enabled: !!obs.redoStack?.length, action: () => obs.redo?.() },
      { sep: 1 },
      { label: 'Copy', shortcut: 'Ctrl+C', enabled: obs.selection.length > 0, action: () => copySelection() },
      { label: 'Paste', shortcut: 'Ctrl+V', enabled: !!obs._cb?.items?.length, action: () => pasteClipboard(false) },
      { label: 'Paste Reference', shortcut: 'Ctrl+Shift+V', enabled: !!obs._cb?.items?.length, action: () => pasteClipboard(true) },
      { sep: 1 },
      { label: 'Copy Filters', enabled: obs.selection.length > 0, action: () => copyFilters() },
      { label: 'Paste Filters', enabled: !!obs._cbFilters && obs.selection.length > 0, action: () => pasteFilters() },
    ],
    View: () => [
      { label: 'Always On Top', checked: !!app.alwaysOnTop, action: () => { app.alwaysOnTop = !app.alwaysOnTop; toast('Always On Top is native-window behavior (web replica)'); } },
      { sep: 1 },
      { label: 'Windowed Projector (Preview)', action: () => tools.openProjector(obs.S.previewId, obs.preview?.name || 'Preview') },
      { label: 'Windowed Projector (Program)', action: () => tools.openProjector(null, obs.program?.name || 'Program') },
      { label: 'Windowed Projector (Source)', action: () => tools.openSourceProjector() },
      { label: 'Windowed Projector (Scene)', action: () => tools.openSceneProjector() },
      { label: 'Fullscreen Projector (Preview)', action: () => tools.openProjector(obs.S.previewId, obs.preview?.name || 'Preview', true) },
      { label: 'Fullscreen Projector (Program)', action: () => tools.openProjector(null, obs.program?.name || 'Program', true) },
      { sep: 1 },
      { label: 'Multiview (Windowed)', action: () => tools.openMultiview() },
      { label: 'Multiview (Fullscreen)', action: () => tools.openMultiview(null, true) },
      { sep: 1 },
      { label: 'Studio Mode', checked: !!obs.S.studioMode, action: () => obs.setStudioMode(!obs.S.studioMode) },
      { label: 'Show Status Bar', checked: !!app.statusBarVisible, action: () => { app.statusBarVisible = !app.statusBarVisible; $('#statusbar')?.classList.toggle('hidden', !app.statusBarVisible); } },
      { sep: 1 },
      { label: 'Reset UI', action: () => { obs.resetUI(); toast('UI layout reset'); } },
    ],
    Docks: () => [
      dockItem('Scenes', 'scenes'), dockItem('Sources', 'sources'), dockItem('Audio Mixer', 'mixer'),
      dockItem('Scene Transitions', 'transitions'), dockItem('Controls', 'controls'), dockItem('Stats', 'stats'),
      { sep: 1 },
      { label: 'Custom Browser Docks…', action: () => tools.openCustomDocks() },
      { sep: 1 },
      { label: 'Lock UI', checked: !!app.lockUI, action: () => { app.lockUI = !app.lockUI; toast(app.lockUI ? 'UI locked' : 'UI unlocked'); } },
      { label: 'Reset UI', action: () => { obs.resetUI(); toast('UI layout reset'); } },
    ],
    Profile: () => [
      { label: 'New', action: () => promptDlg('Add Profile', 'Please enter the name of the profile', 'Profile 2', v => obs.createProfile(v, false)) },
      { label: 'Duplicate', action: () => promptDlg('Duplicate Profile', `Please enter the name of the profile`, `${obs.S.activeProfile} Copy`, v => obs.createProfile(v, true)) },
      { label: 'Rename', action: () => promptDlg('Rename Profile', 'Please enter a new name for the profile', obs.S.activeProfile, v => obs.renameProfile(obs.S.activeProfile, v)) },
      { label: 'Remove', action: () => obs.removeProfile(obs.S.activeProfile) },
      { sep: 1 },
      ...obs.S.profiles.map(p => ({ label: p, checked: p === obs.S.activeProfile, action: () => obs.switchProfile(p) })),
    ],
    'Scene Collection': () => [
      { label: 'New', action: () => promptDlg('Add Scene Collection', 'Please enter the name of the scene collection', 'Collection 2', v => obs.createCollection(v, false)) },
      { label: 'Duplicate', action: () => promptDlg('Duplicate Scene Collection', 'Please enter the name of the scene collection', `${obs.S.activeCollection} Copy`, v => obs.createCollection(v, true)) },
      { label: 'Rename', action: () => promptDlg('Rename Scene Collection', 'Please enter a new name for the scene collection', obs.S.activeCollection, v => obs.renameCollection(obs.S.activeCollection, v)) },
      { label: 'Remove', action: () => obs.removeCollection(obs.S.activeCollection) },
      { sep: 1 },
      ...obs.S.collections.map(c => ({ label: c, checked: c === obs.S.activeCollection, action: () => obs.switchCollection(c) })),
      { sep: 1 },
      { label: 'Import', action: () => toast('Scene collection import reads OBS JSON files (browser sandbox limits local disk access)') },
      { label: 'Export', action: () => exportCollection() },
    ],
    Tools: () => [
      { label: 'Auto-Configuration Wizard', action: () => tools.openWizard() },
      { label: 'Output Timer', action: () => tools.openOutputTimer() },
      { label: 'Scripts', action: () => tools.openScripts() },
      { sep: 1 },
      { label: 'WebSocket Server Settings', action: () => tools.openWsSettings(wsApi) },
      { label: 'Connect to OBS…', action: () => openConnect() },
      { sep: 1 },
      { label: 'Plugins', action: () => tools.openPlugins() },
    ],
    Help: () => [
      { label: 'Check For Updates', action: () => msgBox({ title: 'Update Available?', text: 'OBS 30.2.3 is up to date. (Simulated)', icon: 'info' }) },
      { sep: 1 },
      { label: 'Log Viewer', action: () => tools.openLogViewer() },
      { label: 'Crash Reports', action: () => toast('No crash reports on a web replica') },
      { sep: 1 },
      { label: 'Help Portal', action: () => window.open('https://obsproject.com/help', '_blank') },
      { label: 'Website', action: () => window.open('https://obsproject.com', '_blank') },
      { sep: 1 },
      { label: 'About', action: () => tools.openAbout() },
    ],
  };

  function dockItem(label, key) {
    return { label, checked: !!obs.settings.ui.docks[key], action: () => {
      obs.settings.ui.docks[key] = !obs.settings.ui.docks[key];
      obs.emit('dock-visibility'); obs.persist();
    } };
  }
  function lockAll(v) {
    for (const it of Object.values(obs.S.items)) if (it) it.locked = v;
    obs.emitc('items', { action: 'locked-all' });
  }
  function toggleFullscreen() { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }

  for (const name of Object.keys(menus)) {
    const btn = h('div', { class: 'mb-item', text: name });
    const open = () => {
      closeAllMenus();
      const r = btn.getBoundingClientRect();
      openMenu(menus[name](), r.left, r.bottom);
      btn.classList.add('open');
      openBtn = btn;
      const closer = () => { btn.classList.remove('open'); openBtn = null; document.removeEventListener('qmenu-close', closer); };
      document.addEventListener('qmenu-close', closer);
    };
    btn.addEventListener('click', (e) => { e.stopPropagation(); if (openBtn === btn) { closeAllMenus(); } else open(); });
    btn.addEventListener('mouseenter', () => { if (openBtn && openBtn !== btn) open(); });
    bar.append(btn);
  }
  app.lockUI = false;
}

/* dispatch qmenu-close whenever menus close */
const _origCloseMenus = () => {};
document.addEventListener('click', () => document.dispatchEvent(new Event('qmenu-close')), true);

function closeAllMenus() { document.dispatchEvent(new Event('qmenu-close')); }

/* ---------------- undo / redo (snapshot-based, like OBS Edit menu) ---------------- */
function installUndo() {
  obs.undoStack = []; obs.redoStack = [];
  const snap = () => JSON.stringify({
    scenes: obs.S.scenes, sources: obs.S.sources, items: obs.S.items,
    programId: obs.S.programId, previewId: obs.S.previewId,
  });
  const structural = ['createScene', 'removeScene', 'renameScene', 'reorderScene', 'duplicateScene',
    'createSource', 'removeSource', 'renameSource', 'addItem', 'removeItem', 'reorderItem'];
  for (const m of structural) {
    const orig = obs[m].bind(obs);
    obs[m] = (...args) => {
      const before = snap();
      const r = orig(...args);
      const after = snap();
      if (after !== before) {
        obs.undoStack.push({ before, after });
        if (obs.undoStack.length > 200) obs.undoStack.shift();
        obs.redoStack.length = 0;
      }
      return r;
    };
  }
  const apply = (s) => {
    const d = JSON.parse(s);
    obs.state.scenes = d.scenes; obs.state.sources = d.sources; obs.state.items = d.items;
    obs.state.programId = d.programId; obs.state.previewId = d.previewId;
    obs.emit('scenes'); obs.emit('sources'); obs.emit('items');
    obs.emit('program', d.programId); obs.emit('preview', d.previewId);
    obs.emit('mixer-structure'); obs.persist();
  };
  obs.undo = () => {
    const u = obs.undoStack.pop();
    if (!u) { toast('Nothing to undo'); return; }
    obs.redoStack.push(u); apply(u.before);
  };
  obs.redo = () => {
    const r = obs.redoStack.pop();
    if (!r) { toast('Nothing to redo'); return; }
    obs.undoStack.push(r); apply(r.after);
  };
}

/* ---------------- clipboard (Copy / Paste / Paste Reference / Filters) ---------------- */
function copySelection() {
  const items = obs.selection;
  if (!items.length) return;
  obs._cb = {
    items: items.map(it => JSON.parse(JSON.stringify(it))),
    sources: items.map(it => JSON.parse(JSON.stringify(obs.sourceById(it.sourceId) || {}))),
  };
  obs.log('info', `Copied ${items.length} source(s) to the clipboard`);
}
function pasteClipboard(reference) {
  const cb = obs._cb;
  const scene = obs.preview;
  if (!cb?.items?.length || !scene) return;
  for (let i = 0; i < cb.items.length; i++) {
    const srcData = cb.sources[i];
    let sourceId;
    if (reference && obs.sourceByName?.(srcData.name)) {
      sourceId = obs.sourceByName(srcData.name).id;
    } else {
      const clone = JSON.parse(JSON.stringify(srcData));
      const created = obs.createSource(clone.kind, clone.name, clone.settings, { noScene: true });
      created.volumeDb = clone.volumeDb; created.muted = clone.muted;
      sourceId = created.id;
    }
    const c = JSON.parse(JSON.stringify(cb.items[i]));
    const it = obs.addItem(scene.id, sourceId);
    if (it) { it.x = c.x + 20; it.y = c.y + 20; it.w = c.w; it.h = c.h; it.rot = c.rot || 0; it.crop = c.crop; obs.emitc('item-transform', it.id); }
  }
}
function copyFilters() {
  const it = obs.selection[0];
  if (!it) return;
  obs._cbFilters = JSON.parse(JSON.stringify(it.filters || []));
  toast(`Copied ${obs._cbFilters.length} filter(s)`);
}
function pasteFilters() {
  const it = obs.selection[0];
  if (!it || !obs._cbFilters) return;
  it.filters = JSON.parse(JSON.stringify(obs._cbFilters));
  obs.emitc('items', { action: 'filters-pasted', itemId: it.id });
  toast('Filters pasted');
}
function exportCollection() {
  const data = JSON.stringify({
    name: obs.S.activeCollection,
    scenes: obs.S.scenes, sources: obs.S.sources, items: obs.S.items,
    programId: obs.S.programId, previewId: obs.S.previewId,
  }, null, 2);
  const url = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
  import('./util.js').then(u => u.download(`${obs.S.activeCollection}.json`, url));
  toast('Scene collection exported (OBS-compatible JSON)');
}

/* ---------------- workspace ---------------- */
function buildWorkspace(root) {
  const ws = h('div', { id: 'workspace' });
  const left = h('div', { class: 'ws-col left' });
  const center = h('div', { class: 'ws-col center' });
  const right = h('div', { class: 'ws-col right' });
  ws.append(left, center, right);
  root.append(ws);

  buildScenesDock(left);
  buildSourcesDock(left);
  buildPreviewArea(center);
  buildMixerDock(right);
  buildTransitionsDock(right);
  buildControlsDock(right);
  buildStatsDock(right);

  const applyDockVis = () => {
    const d = obs.settings.ui.docks;
    $('#dock-scenes')?.classList.toggle('hidden', !d.scenes);
    $('#dock-sources')?.classList.toggle('hidden', !d.sources);
    $('#dock-mixer')?.classList.toggle('hidden', !d.mixer);
    $('#dock-transitions')?.classList.toggle('hidden', !d.transitions);
    $('#dock-controls')?.classList.toggle('hidden', !d.controls);
    $('#dock-stats')?.classList.toggle('hidden', !d.stats);
  };
  obs.on('dock-visibility', applyDockVis);
  obs.on('ui-reset', applyDockVis);
  applyDockVis();

  // left column split: scenes auto, sources flex
  const sceneDock = $('#dock-scenes'), srcDock = $('#dock-sources');
  sceneDock.style.flex = '0 1 auto';
  sceneDock.querySelector('.qlist').style.maxHeight = '30vh';
  srcDock.style.flex = '1 1 0';
  right.style.width = '340px';
  return ws;
}

/* ---------------- global hotkeys ---------------- */
function bindHotkeys() {
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || document.activeElement?.isContentEditable;
    if (typing) return;

    // built-in OBS-style behaviors
    if (/^F11$/.test(e.key)) { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); e.preventDefault(); return; }
    if (e.ctrlKey && !e.altKey && !e.shiftKey && /^[1-9]$/.test(e.key)) {
      const sc = obs.S.scenes[parseInt(e.key) - 1];
      if (sc) { obs.S.studioMode ? obs.setPreview(sc.id) : obs.setProgram(sc.id); e.preventDefault(); }
      return;
    }
    if (obs.S.studioMode && e.code === 'Space') { obs.triggerTransition(); e.preventDefault(); return; }
    if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'z') { obs.undo?.(); e.preventDefault(); return; }
    if (e.ctrlKey && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) { obs.redo?.(); e.preventDefault(); return; }
    if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'c') { copySelection(); e.preventDefault(); return; }
    if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'v') { pasteClipboard(false); e.preventDefault(); return; }
    if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'v') { pasteClipboard(true); e.preventDefault(); return; }
    if (e.ctrlKey && e.key === ',') { openSettings(); e.preventDefault(); return; }

    // configured hotkeys
    const combo = keyStr(e);
    const H = obs.settings.hotkeys;
    for (const [action, binds] of Object.entries(H)) {
      if (!binds || !binds.length) continue;
      if (binds.includes(combo)) {
        e.preventDefault();
        switch (action) {
          case 'Start Streaming': if (!obs.S.outputs.streaming) obs.startStream(); break;
          case 'Stop Streaming': if (obs.S.outputs.streaming) obs.stopStream(); break;
          case 'Start Recording': if (!obs.S.outputs.recording) obs.startRecord(); break;
          case 'Stop Recording': if (obs.S.outputs.recording) obs.stopRecord(); break;
          case 'Enable Studio Mode': if (!obs.S.studioMode) obs.setStudioMode(true); break;
          case 'Disable Studio Mode': if (obs.S.studioMode) obs.setStudioMode(false); break;
          case 'Transition (Studio Mode)': obs.triggerTransition(); break;
          case 'Take Screenshot': obs.screenshotScene(obs.S.programId, url => import('./util.js').then(u => u.download(`screenshot.png`, url))); break;
          case 'Enable Virtual Camera': if (!obs.S.outputs.vcam) obs.toggleVCam(); break;
          case 'Disable Virtual Camera': if (obs.S.outputs.vcam) obs.toggleVCam(); break;
          default:
            if (action.startsWith('Scene: ')) {
              const sc = obs.sceneByName(action.slice(7));
              if (sc) obs.S.studioMode ? obs.setPreview(sc.id) : obs.setProgram(sc.id);
            }
        }
        return;
      }
    }
  });
}

/* ---------------- logs feed into sim ---------------- */
function wireLogs() {
  obs.on('log', l => { obs._sim.logs = obs._sim.logs || []; obs._sim.logs.push(l); if (obs._sim.logs.length > 500) obs._sim.logs.shift(); });
  obs.log('info', 'OBS Studio (web replica) started');
  obs.log('info', 'Audio: 48000 Hz, stereo');
  obs.log('info', 'Video: 1920x1080 @ 60 fps, NV12, Rec. 709');
}

/* ---------------- boot ---------------- */
function boot() {
  const root = document.getElementById('obs-root');
  if (!root) return;
  applyTheme();
  buildTitlebar(root);
  buildMenubar(root);
  buildWorkspace(root);
  buildStatusBar(root);
  bindHotkeys();
  wireLogs();
  installUndo();

  // OBS-like output resolution from settings
  const base = obs.settings.video?.baseRes;
  if (base) { const p = base.split('x'); obs.canvas = { w: parseInt(p[0]) || 1920, h: parseInt(p[1]) || 1080 }; }

  window.__obs = obs;         // debugging handle
  window.__ws = wsApi;
  // LOCAL-PATCH (station): zero-config connect — gateway defaults already
  // point at this server and the relay bridges authentication.
  setTimeout(() => { try { wsApi.connect(); } catch {} }, 800);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();

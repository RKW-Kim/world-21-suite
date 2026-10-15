/* ============================================================
   OBS Studio — Web Replication · Source & Property Dialogs
   Create/Select Source flow, per-type Properties, Filters
   window, Edit Transform, Advanced Audio Properties.
   ============================================================ */
import { h, $, clamp } from './util.js';
import { I, SOURCE_ICON, ObsLogo } from './icons.js';
import { obs, SOURCE_TYPES, FILTER_TYPES, AUDIO_KINDS, defaultSettingsFor } from './engine.js';
import { openDialog, openMenu, msgBox, promptDlg, toast } from './ui.js';

/* ================= Create / Select Source flow ================= */
export function createSourceFlow(type) {
  const isScene = type.kind === 'scene';
  const radioCreate = h('input', { type: 'radio', name: 'cs', checked: obs.S.sources.some(s => s.kind === type.kind) ? '' : null });
  const radioExisting = h('input', { type: 'radio', name: 'cs' });
  const nameInput = h('input', { class: 'qinput', value: defaultNameFor(type), style: { width: '240px' } });
  const existingSel = h('select', { class: 'qcombo', style: { width: '240px' }, disabled: '' });

  const refreshExisting = () => {
    existingSel.innerHTML = '';
    for (const s of obs.S.sources.filter(s => s.kind === type.kind)) {
      existingSel.append(h('option', { value: s.id, text: s.name }));
    }
  };
  refreshExisting();

  const body = h('div', { style: { padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px' } },
    h('label', { class: 'qradio' }, radioCreate, h('span', { class: 'dot' }), h('span', { text: 'Create new' })),
    h('div', { class: 'row' }, h('label', { style: { width: '90px' }, text: 'Name' }), nameInput),
    h('label', { class: 'qradio' }, radioExisting, h('span', { class: 'dot' }), h('span', { text: 'Add existing' })),
    existingSel,
  );
  radioCreate.addEventListener('change', sync);
  radioExisting.addEventListener('change', sync);
  function sync() {
    nameInput.disabled = radioExisting.checked;
    existingSel.disabled = radioCreate.checked;
  }

  const sceneTarget = obs.preview;
  const d = openDialog({
    title: `Create or Select Source — ${type.name}`, w: 430, resizable: false,
    content: body,
    buttons: [
      { label: isScene ? 'Add Scene' : 'OK', def: true, action: () => {
          if (radioExisting.checked && existingSel.value) {
            obs.addItem(sceneTarget.id, existingSel.value);
          } else if (isScene) {
            const sc = obs.createScene(nameInput.value);
            obs.setProgram(sc.id);
          } else {
            const src = obs.createSource(type.kind, nameInput.value, null, { sceneId: sceneTarget.id });
            d.close();
            if (obs.settings.general.openProps === 'always' && !['group', 'scene'].includes(src.kind)) {
              openProperties(src, true);
            }
            return;
          }
          d.close();
        } },
      { label: 'Cancel', action: () => d.close() },
    ],
  });
  setTimeout(() => nameInput.focus());
}

function defaultNameFor(type) {
  const taken = new Set(obs.S.sources.map(s => s.name));
  const base = type.name.replace(/\s*\(.*\)$/, '');
  if (!taken.has(base)) return base;
  let i = 2;
  while (taken.has(`${base} ${i}`)) i++;
  return `${base} ${i}`;
}

/* ================= Properties dialog ================= */
export function openProperties(src, isNew) {
  const previewBox = h('div', { class: 'props-preview' }, h('div', { style: { color: '#666' }, text: 'Preview unavailable (simulated source)' }));
  const grid = h('div', { class: 'props-grid' });
  const body = h('div', { class: 'props-body' },
    !AUDIO_KINDS.has(src.kind) ? previewBox : null,
    grid);

  const ctrl = {};
  const row = (label, ...els) => { grid.append(h('label', { text: label }), h('div', { class: 'row', style: { flexWrap: 'wrap' } }, ...els)); };
  const full = (...els) => grid.append(h('div', { class: 'full row', style: { flexWrap: 'wrap' } }, ...els));
  const combo = (opts, get, set) => {
    const s = h('select', { class: 'qcombo' });
    for (const o of opts) s.append(h('option', { value: o, text: o, selected: String(o) === String(get()) ? '' : null }));
    s.addEventListener('change', () => { set(s.value); apply(); });
    return s;
  };
  const check = (label, get, set) => {
    const input = h('input', { type: 'checkbox' });
    input.checked = !!get();
    input.addEventListener('change', () => { set(input.checked); apply(); });
    return h('label', { class: 'qcheck' }, input, h('span', { class: 'box' }), h('span', { text: label }));
  };
  const num = (get, set, min, max, w = '90px') => {
    const inp = h('input', { class: 'qinput', type: 'number', value: get(), min, max });
    inp.style.width = w;
    inp.addEventListener('change', () => { set(parseFloat(inp.value) || 0); apply(); });
    return inp;
  };
  const txt = (get, set, w = '240px') => {
    const inp = h('input', { class: 'qinput', value: get() });
    inp.style.width = w;
    inp.addEventListener('change', () => { set(inp.value); apply(); });
    return inp;
  };
  const apply = () => obs.setSourceSettings(src.id, src.settings);

  const s = src.settings;
  switch (src.kind) {
    case 'display_capture':
      row('Method', combo(['Windows 10 (1903 and up)', 'DXGI Desktop Duplication'], () => s.method, v => s.method = v));
      row('Display', combo(['Display 1 (1920x1080)', 'Display 2 (2560x1440)'], () => `Display ${s.display + 1} (1920x1080)`, v => s.display = v.startsWith('Display 2') ? 1 : 0));
      grid.append(h('div'), check('Capture Cursor', () => s.cursor, v => s.cursor = v));
      break;
    case 'window_capture':
      row('Method', combo(['Windows 10 (1903 and up)', 'BitBlt (Windows 7 and up)'], () => s.method, v => s.method = v));
      row('Window', combo(['OBS Studio — Web Replication', 'Mozilla Firefox', 'Visual Studio Code'], () => s.window, v => s.window = v));
      row('Window Match Priority', combo(['Window title must match', 'Match title, otherwise find window of same executable', 'Match title or executable'], () => s.priority, v => s.priority = v));
      grid.append(h('div'), check('Capture Cursor', () => s.cursor, v => s.cursor = v));
      break;
    case 'game_capture':
      row('Mode', combo(['Capture any fullscreen application', 'Capture specific window', 'Capture foreground window with hotkey'], () => s.mode, v => s.mode = v));
      row('Window', combo(['[any window]', 'game.exe'], () => s.window, v => s.window = v));
      grid.append(h('div'), check('Use anti-cheat compatibility hook', () => s.antiCheat, v => s.antiCheat = v));
      break;
    case 'browser_source':
      row('URL', txt(() => s.url, v => s.url = v, '360px'));
      row('Width', num(() => s.width, v => s.width = v, 1, 8192));
      row('Height', num(() => s.height, v => s.height = v, 1, 8192));
      row('FPS', combo(['30', '60', 'Use custom'], () => String(s.fps), v => s.fps = parseInt(v)));
      full(h('label', { text: 'Custom CSS' }));
      full(txt(() => s.css, v => s.css = v, '420px'));
      grid.append(h('div'), check('Shutdown source when not visible', () => s.shutdown, v => s.shutdown = v));
      grid.append(h('div'), check('Refresh browser when scene becomes active', () => s.refresh, v => s.refresh = v));
      full(h('button', { class: 'qpush', text: 'Refresh Cache of Current Page', onclick: () => toast('Browser cache refreshed (simulated)') }));
      break;
    case 'color_source':
      row('Width', num(() => s.width, v => s.width = v, 1, 8192));
      row('Height', num(() => s.height, v => s.height = v, 1, 8192));
      row('Color', colorSwatch(() => s.color, v => { s.color = v; apply(); }));
      break;
    case 'image':
      row('Image File', txt(() => s.file, v => s.file = v, '300px'), h('button', { class: 'qpush', text: 'Browse…', onclick: () => toast('File dialogs are OS-native; paste a path (web replica)') }));
      grid.append(h('div'), check('Unload image when not shown', () => s.unload, v => s.unload = v));
      break;
    case 'image_slideshow':
      row('Slide Time', num(() => s.slideTime, v => s.slideTime = v, 50, 3600000), 'ms');
      row('Transition', combo(['Cut', 'Fade', 'Swipe', 'Slide'], () => s.transition, v => s.transition = v));
      row('Transition Time', num(() => s.transitionTime, v => s.transitionTime = v, 50, 20000), 'ms');
      grid.append(h('div'), check('Randomize', () => s.randomize, v => s.randomize = v));
      grid.append(h('div'), check('Loop', () => s.loop, v => s.loop = v));
      break;
    case 'media_source':
      grid.append(h('div'), check('Local File', () => s.local, v => s.local = v));
      row('Input', txt(() => s.input, v => s.input = v, '300px'));
      row('Input Format', txt(() => s.inputFormat, v => s.inputFormat = v));
      row('Buffering (MB)', num(() => s.buffering, v => s.buffering = v, 0, 16));
      grid.append(h('div'), check('Restart playback when source becomes active', () => s.restartOnActivate, v => s.restartOnActivate = v));
      grid.append(h('div'), check('Looping', () => s.loop, v => s.loop = v));
      row('Speed (%)', num(() => s.speed, v => s.speed = v, 1, 400));
      break;
    case 'text':
      full(h('button', { class: 'qpush', text: 'Choose Font', onclick: () => toast('Font dialog is OS-native (web replica)') }));
      full(h('div', { class: 'row' }, h('span', { text: 'Font: Arial' }), h('span', { text: 'Size: 256' })));
      row('Color', colorSwatch(() => s.color, v => { s.color = v; apply(); }));
      full(txt(() => s.text, v => { s.text = v; apply(); }, '420px'));
      grid.append(h('div'), check('Outline', () => s.outline, v => s.outline = v));
      grid.append(h('div'), check('Drop Shadow', () => s.shadow, v => s.shadow = v));
      break;
    case 'audio_input_capture':
      row('Device', combo(['Default', 'Microphone (Realtek Audio)', 'Microphone (USB)'], () => s.device, v => s.device = v));
      grid.append(h('div'), check('Disable Windows ducking', () => s.disableDucking, v => s.disableDucking = v));
      break;
    case 'audio_output_capture':
      row('Device', combo(['Default', 'Speakers (Realtek Audio)', 'Headphones (USB)'], () => s.device, v => s.device = v));
      break;
    case 'application_audio_capture':
      row('Window', combo(['[Match any application]', 'firefox.exe'], () => s.window, v => s.window = v));
      break;
    case 'vlc_source':
      full(h('div', { class: 'hint', text: 'Playlist (simulated): add files via VLC in real OBS.' }));
      grid.append(h('div'), check('Loop playlist', () => s.loop, v => s.loop = v));
      grid.append(h('div'), check('Shuffle playlist', () => s.shuffle, v => s.shuffle = v));
      break;
    case 'group':
    case 'scene':
      full(h('div', { class: 'hint', text: src.kind === 'group' ? 'Groups have no properties.' : 'Scenes have no properties.' }));
      break;
    default:
      full(h('div', { class: 'hint', text: `Properties for "${src.kind}" are not simulated.` }));
  }

  const d = openDialog({
    title: `Properties for '${src.name}'`, w: 760, h: 600, resizable: true,
    content: body,
    buttons: [
      { label: isNew ? 'OK' : 'OK', def: true, action: () => d.close() },
      { label: 'Cancel', action: () => { if (isNew) obs.removeSource(src.id); d.close(); } },
    ],
  });
  function colorSwatch(get, set) {
    const inp = h('input', { type: 'color', value: normalize(get()), style: { width: '46px', height: '22px', border: 'none', background: 'none', padding: 0 } });
    const hex = h('span', { class: 'hint', text: get() });
    inp.addEventListener('input', () => { set(rgbaFromHex(inp.value)); hex.textContent = inp.value; });
    return h('div', { class: 'row' }, inp, hex);
  }
  function normalize(c) {
    let s = (c || '#808080ff').replace('#', '');
    if (s.length === 8) s = s.slice(2);
    return '#' + s.slice(0, 6);
  }
  function rgbaFromHex(hexv) {
    return '#ff' + hexv.replace('#', '');
  }
}

/* ================= Filters window ================= */
export function openFilters(src) {
  const nameRow = h('div', { class: 'filters-name' },
    h('span', { class: 'fname', text: src.name }),
    h('span', { class: 'ftype', text: src.kind.replace(/_/g, ' ') }));
  const list = h('div', { class: 'qlist', style: { flex: 1 } });
  const right = h('div', { class: 'filters-right' });
  const canvasBox = h('div', { class: 'filters-canvas' });

  const left = h('div', { class: 'filters-left' },
    h('div', { class: 'dock-header', style: { fontWeight: 600 } }, nameRow),
    h('div', { class: 'dock-toolbar' },
      ...['plus', 'minus', 'up', 'down'].map(ic => h('div', { class: 'dock-btn', html: I(ic), onclick: (e) => listBtn(ic, e) })),
    ),
    list);
  const center = h('div', { class: 'filters-center' },
    h('div', { style: { color: 'var(--text-dim)' }, text: 'Effect Filters preview' }),
    canvasBox);
  const body = h('div', { style: { display: 'flex', flex: 1, minHeight: 0 } }, left, center, right);

  const d = openDialog({
    title: `Filters for '${src.name}'`, w: 900, h: 620, resizable: true, winClass: 'filters-win',
    content: body,
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });

  let current = null;

  function render() {
    list.innerHTML = '';
    for (const f of src.filters || []) {
      list.append(h('div', {
        class: 'qlist-row' + (f === current ? ' selected' : ''),
        onclick: () => { current = f; render(); },
        oncontextmenu: (e) => { e.preventDefault(); openMenu([
          // LOCAL-PATCH (station): audio removals mirror to OBS.
          { label: 'Remove', action: () => { if (f.audio) obs.removeSourceFilter(src.id, f); else src.filters = src.filters.filter(x => x !== f); current = null; render(); } },
        ], e.clientX, e.clientY); },
      },
        h('span', { class: 'row-icon', html: I(f.audio ? 'audioLine' : 'filter') }),
        h('span', { class: 'row-label', text: f.name })));
    }
    right.innerHTML = '';
    if (current) {
      right.append(h('h3', { style: { margin: '0 0 10px' }, text: current.name }));
      buildFilterProps(right, current);
    } else {
      right.append(h('div', { class: 'hint', text: 'No filter selected. Add a filter with the + button.' }));
    }
  }

  function listBtn(ic, e) {
    if (ic === 'plus') {
      openMenu([
        { title: 'Effect Filters', label: 'Effect Filters' },
        ...FILTER_TYPES.effect.map(t => ({ label: t.name, action: () => addFilter(t, false) })),
        { sep: 1 },
        { title: 'Audio Filters', label: 'Audio Filters' },
        ...FILTER_TYPES.audio.map(t => ({ label: t.name, action: () => addFilter(t, true) })),
      ], e.clientX + 4, e.clientY + 4);
    } else if (ic === 'minus' && current) {
      if (current.audio) obs.removeSourceFilter(src.id, current);
      else src.filters = src.filters.filter(x => x !== current);
      current = null; render();
    } else if (current) {
      const i = src.filters.indexOf(current);
      const to = ic === 'up' ? clamp(i + 1, 0, src.filters.length - 1) : clamp(i - 1, 0, src.filters.length - 1);
      src.filters.splice(to, 0, src.filters.splice(i, 1)[0]);
      render();
    }
  }
  function addFilter(t, audio) {
    // LOCAL-PATCH (station): audio filters are real (mirrored to OBS via
    // the engine); effect filters stay local-only sim.
    if (audio) { current = obs.addSourceFilter(src.id, t.id, t.name); render(); return; }
    const f = { id: t.id, name: t.name, audio, settings: {} };
    (src.filters = src.filters || []).unshift(f);
    current = f; render();
  }

  render();
}

function buildFilterProps(root, f) {
  const grid = h('div', { class: 'props-grid' });
  root.append(grid);
  const row = (label, ...els) => grid.append(h('label', { text: label }), h('div', { class: 'row' }, ...els));
  const slider = (label, get, set, min = -100, max = 100) => {
    const inp = h('input', { class: 'obs-range', type: 'range', min, max, value: get(), style: { width: '170px' } });
    const val = h('span', { class: 'hint', text: String(get()), style: { width: '36px' } });
    inp.addEventListener('input', () => { set(parseFloat(inp.value)); val.textContent = inp.value; });
    row(label, inp, val);
  };
  const combo = (label, opts, get, set) => {
    const s = h('select', { class: 'qcombo' });
    for (const o of opts) s.append(h('option', { value: o, text: o, selected: o === get() ? '' : null }));
    s.addEventListener('change', () => set(s.value));
    row(label, s);
  };
  const num = (label, get, set, min, max) => {
    const inp = h('input', { class: 'qinput', type: 'number', value: get(), min, max, style: { width: '90px' } });
    inp.addEventListener('change', () => set(parseFloat(inp.value) || 0));
    row(label, inp);
  };
  const s = f.settings;
  switch (f.id) {
    case 'color_corr':
      slider('Brightness', () => s.brightness ?? 0, v => s.brightness = v);
      slider('Contrast', () => s.contrast ?? 0, v => s.contrast = v);
      slider('Saturation', () => s.saturation ?? 0, v => s.saturation = v);
      slider('Gamma', () => s.gamma ?? 0, v => s.gamma = v);
      slider('Opacity', () => s.opacity ?? 100, v => s.opacity = v, 0, 100);
      combo('Blend Type', ['Normal', 'Additive', 'Subtract', 'Multiply', 'Screen', 'Lighten', 'Darken'], () => s.blend || 'Normal', v => s.blend = v);
      break;
    case 'chroma_key':
      slider('Similarity (1-1000)', () => s.similarity ?? 400, v => s.similarity = v, 1, 1000);
      slider('Smoothness (1-1000)', () => s.smoothness ?? 80, v => s.smoothness = v, 1, 1000);
      combo('Key Color Type', ['Green', 'Blue', 'Magenta', 'Custom'], () => s.type || 'Green', v => s.type = v);
      slider('Opacity', () => s.opacity ?? 100, v => s.opacity = v, 0, 100);
      slider('Contrast', () => s.contrast ?? 0, v => s.contrast = v);
      break;
    case 'color_key':
      row('Key Color', h('input', { type: 'color', value: s.color || '#00ff00' }));
      slider('Similarity', () => s.similarity ?? 400, v => s.similarity = v, 1, 1000);
      slider('Smoothness', () => s.smoothness ?? 80, v => s.smoothness = v, 1, 1000);
      break;
    case 'crop_pad':
      num('Left', () => s.l ?? 0, v => s.l = v, 0, 4096);
      num('Right', () => s.r ?? 0, v => s.r = v, 0, 4096);
      num('Top', () => s.t ?? 0, v => s.t = v, 0, 4096);
      num('Bottom', () => s.b ?? 0, v => s.b = v, 0, 4096);
      break;
    case 'sharpness':
      slider('Sharpness', () => s.sharpness ?? 0, v => s.sharpness = v, 0, 100);
      break;
    case 'scaling':
      combo('Resolution', ['1280x720', '1920x1080', '2560x1440'], () => s.res || '1920x1080', v => s.res = v);
      combo('Downscale Filter', ['Bilinear', 'Bicubic', 'Lanczos', 'Area'], () => s.filter || 'Lanczos', v => s.filter = v);
      break;
    case 'scroll':
      slider('Horizontal Speed', () => s.h ?? 0, v => s.h = v, -100, 100);
      slider('Vertical Speed', () => s.v ?? 0, v => s.v = v, -100, 100);
      break;
    case 'render_delay':
      num('Delay (ms)', () => s.delay ?? 0, v => s.delay = v, 0, 10000);
      break;
    case 'lut':
      row('Path', h('input', { class: 'qinput', value: s.path || '', style: { width: '240px' } }), h('button', { class: 'qpush', text: 'Browse…', onclick: () => toast('File dialogs are OS-native (web replica)') }));
      slider('Amount', () => s.amount ?? 100, v => s.amount = v, 0, 100);
      break;
    case 'mask':
      combo('Type', ['Alpha Mask (Alpha Channel)', 'Alpha Mask (Color Value)', 'Blend (Multiplication)', 'Blend (Addition)', 'Blend (Subtraction)'], () => s.type || 'Alpha Mask (Alpha Channel)', v => s.type = v);
      slider('Opacity', () => s.opacity ?? 100, v => s.opacity = v, 0, 100);
      break;
    case 'compressor':
      slider('Ratio (X:1)', () => s.ratio ?? 10, v => obs.setFilterProp(src.id, f, 'ratio', v), 1, 20);
      slider('Threshold', () => s.threshold ?? -18, v => obs.setFilterProp(src.id, f, 'threshold', v), -60, 0);
      slider('Attack (ms)', () => s.attack ?? 6, v => obs.setFilterProp(src.id, f, 'attack', v), 0.1, 100);
      slider('Release (ms)', () => s.release ?? 60, v => obs.setFilterProp(src.id, f, 'release', v), 1, 1000);
      slider('Output Gain (dB)', () => s.outputGain ?? 0, v => obs.setFilterProp(src.id, f, 'outputGain', v), -32, 32);
      break;
    case 'limiter':
      slider('Threshold', () => s.threshold ?? -6, v => obs.setFilterProp(src.id, f, 'threshold', v), -60, 0);
      slider('Release (ms)', () => s.release ?? 60, v => obs.setFilterProp(src.id, f, 'release', v), 1, 1000);
      break;
    case 'gain':
      slider('Gain (dB)', () => s.gain ?? 0, v => obs.setFilterProp(src.id, f, 'gain', v), -30, 30);
      break;
    case 'invert':
      row('', h('label', { class: 'qcheck' }, h('input', { type: 'checkbox', checked: '' }), h('span', { class: 'box' }), h('span', { text: 'Invert Polarity' })));
      break;
    case 'expander':
      slider('Ratio (X:1)', () => s.ratio ?? 2, v => obs.setFilterProp(src.id, f, 'ratio', v), 1, 20);
      slider('Threshold', () => s.threshold ?? -40, v => obs.setFilterProp(src.id, f, 'threshold', v), -60, 0);
      slider('Attack (ms)', () => s.attack ?? 10, v => obs.setFilterProp(src.id, f, 'attack', v), 0.1, 100);
      slider('Release (ms)', () => s.release ?? 100, v => obs.setFilterProp(src.id, f, 'release', v), 1, 1000);
      slider('Output Gain (dB)', () => s.outputGain ?? 0, v => obs.setFilterProp(src.id, f, 'outputGain', v), -32, 32);
      break;
    case 'noise_gate':
      slider('Close Threshold', () => s.close ?? -60, v => obs.setFilterProp(src.id, f, 'close', v), -60, 0);
      slider('Open Threshold', () => s.open ?? -45, v => obs.setFilterProp(src.id, f, 'open', v), -60, 0);
      slider('Attack Time (ms)', () => s.attack ?? 5, v => obs.setFilterProp(src.id, f, 'attack', v), 0, 500);
      slider('Hold Time (ms)', () => s.hold ?? 200, v => obs.setFilterProp(src.id, f, 'hold', v), 0, 2000);
      slider('Release Time (ms)', () => s.release ?? 150, v => obs.setFilterProp(src.id, f, 'release', v), 0, 2000);
      break;
    case 'noise_supp':
      combo('Method', ['RNNoise', 'Speex'], () => s.method || 'RNNoise', v => obs.setFilterProp(src.id, f, 'method', v));
      slider('Suppression Level', () => s.level ?? -30, v => obs.setFilterProp(src.id, f, 'level', v), -60, 0);
      break;
    case 'upward_comp':
      slider('Ratio (X:1)', () => s.ratio ?? 2, v => obs.setFilterProp(src.id, f, 'ratio', v), 1, 20);
      slider('Threshold', () => s.threshold ?? -40, v => obs.setFilterProp(src.id, f, 'threshold', v), -60, 0);
      break;
    case 'vst':
      row('Plugin Path', h('input', { class: 'qinput', value: s.path || '', style: { width: '240px' } }), h('button', { class: 'qpush', text: 'Browse…', onclick: () => toast('VST plugins load in real OBS (web replica)') }));
      row('', h('button', { class: 'qpush', text: 'Open Plug-In Interface', onclick: () => toast('VST UI unavailable in web replica') }));
      break;
    default:
      grid.append(h('div', { class: 'hint', text: 'No configurable properties.' }));
  }
}

export function openFiltersForScene(scene) {
  const pseudo = { name: scene.name, kind: 'scene', filters: scene.filters || [] };
  const d = openFilters(pseudo);
  return d;
}

/* ================= Edit Transform ================= */
export function openTransform(itemId) {
  const it = obs.S.items[itemId];
  if (!it) return;
  // LOCAL-PATCH (station): same lock as the canvas — transform edits are
  // committed JSON while attached, not live dialog tweaks.
  if (obs.wsMode) { toast('Layout locked while attached — scenes come from committed JSON, not the canvas'); return; }
  const grid = h('div', { class: 'form-grid', style: { padding: '14px 16px', gap: '8px 12px' } });
  const d = openDialog({
    title: 'Edit Transform', w: 480, resizable: false,
    content: grid,
    buttons: [
      { label: 'Reset Transform', action: () => { obs.resetItemTransform(itemId); sync(); } },
      { label: 'Close', def: true, action: () => d.close() },
    ],
  });

  const inputs = {};
  function field(label, key, min, max, step = 1) {
    const inp = h('input', { class: 'qinput', type: 'number', step, min, max, style: { width: '100px' } });
    inp.addEventListener('change', () => {
      const v = parseFloat(inp.value) || 0;
      obs.setItemTransform(itemId, { [key]: v });
    });
    grid.append(h('label', { text: label }), inp);
    inputs[key] = inp;
    return inp;
  }

  field('Position X', 'x', -8192, 8192);
  field('Position Y', 'y', -8192, 8192);
  grid.append(h('label', { text: 'Alignment' }), alignGrid());
  field('Size Width', 'w', 1, 8192);
  field('Size Height', 'h', 1, 8192);
  field('Rotation', 'rot', -360, 360);

  // bounds
  const boundsSel = h('select', { class: 'qcombo' },
    ...['No bounds', 'Scale to Inner Bounds', 'Scale to Outer Bounds', 'Stretch to Bounds', 'Scale to Width', 'Scale to Height'].map(o => h('option', { value: o, text: o, selected: (it.boundsType === 'none' ? 'No bounds' : it.boundsType) === o ? '' : null })));
  boundsSel.addEventListener('change', () => obs.setItemTransform(itemId, { boundsType: boundsSel.value === 'No bounds' ? 'none' : boundsSel.value }));
  grid.append(h('label', { text: 'Bounds Type' }), boundsSel);

  // crop
  const crop = {};
  grid.append(h('div', { class: 'stats-sep', style: { gridColumn: '1 / -1' } }));
  grid.append(h('label', { text: 'Crop' }), h('span', { class: 'hint', text: 'Use Alt+drag on preview handles, or enter pixel values:' }));
  for (const side of ['l', 'r', 't', 'b']) {
    const inp = h('input', { class: 'qinput', type: 'number', min: 0, style: { width: '80px' } });
    inp.addEventListener('change', () => obs.setItemTransform(itemId, { crop: { [side]: Math.max(0, parseInt(inp.value) || 0) } }));
    crop[side] = inp;
    grid.append(h('label', { text: { l: 'Left', r: 'Right', t: 'Top', b: 'Bottom' }[side] }), inp);
  }

  function alignGrid() {
    const g = h('div', { class: 'align-grid' });
    for (let i = 0; i < 9; i++) {
      g.append(h('button', {
        class: (it.align === i) ? 'active' : '',
        onclick: () => { obs.setItemTransform(itemId, { align: i }); sync(); },
      }, h('span', { html: I('dot') })));
    }
    return g;
  }

  function sync() {
    const it = obs.S.items[itemId]; if (!it) { d.close(); return; }
    for (const [k, inp] of Object.entries(inputs)) inp.value = Math.round(it[k] ?? 0);
    for (const side of ['l', 'r', 't', 'b']) crop[side].value = it.crop[side] || 0;
    grid.querySelectorAll('.align-grid button').forEach((b, i) => b.classList.toggle('active', it.align === i));
  }
  obs.on('item-transform', sync);
  sync();
}

/* ================= Advanced Audio Properties ================= */
export function openAdvAudio() {
  const table = h('table', { class: 'qtable' });
  const wrap = h('div', { style: { overflow: 'auto', flex: 1, padding: '10px 12px' } }, table);
  const d = openDialog({
    title: 'Advanced Audio Properties', w: 760, h: 420, resizable: true,
    content: wrap,
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });

  function render() {
    table.innerHTML = '';
    const thead = h('thead', {}, h('tr', {},
      h('th', { text: 'Volume (%)' }), h('th', { text: 'Volume (dB)' }), h('th', { text: 'Balance' }),
      h('th', { text: 'Sync Offset (ms)' }), h('th', { text: 'Audio Monitoring' }), h('th', { text: 'Tracks' })));
    const tbody = h('tbody');
    const groups = [
      ['Global Audio Devices', obs.mixerSources().filter(s => s.global)],
      ['Sources', obs.mixerSources().filter(s => !s.global)],
    ];
    for (const [title, srcs] of groups) {
      if (!srcs.length) continue;
      tbody.append(h('tr', { class: 'group' }, h('td', { colSpan: 6, text: title })));
      for (const s of srcs) {
        const pct = Math.round(Math.pow(10, s.volumeDb / 20) * 100);
        const volRange = h('input', { class: 'obs-range', type: 'range', min: 0, max: 2000, value: pct });
        volRange.addEventListener('input', () => { obs.setVolumeMul(s.id, parseFloat(volRange.value) / 100); dbInp.value = fmtDb(s.volumeDb); renderTracks(); });
        const dbInp = h('input', { class: 'qinput', type: 'text', value: fmtDb(s.volumeDb), style: { width: '80px' } });
        dbInp.addEventListener('change', () => {
          const v = parseFloat(dbInp.value);
          if (!isNaN(v)) obs.setVolumeDb(s.id, v);
          dbInp.value = fmtDb(s.volumeDb);
        });
        const balRange = h('input', { class: 'obs-range', type: 'range', min: 0, max: 100, value: s.balance * 100 });
        balRange.addEventListener('input', () => { s.balance = parseFloat(balRange.value) / 100; obs.persist(); });
        const syncInp = h('input', { class: 'qinput', type: 'number', value: s.syncOffset, style: { width: '70px' } });
        syncInp.addEventListener('change', () => { s.syncOffset = parseInt(syncInp.value) || 0; obs.persist(); });
        const monSel = h('select', { class: 'qcombo' },
          ...['Monitor Off', 'Monitor Only (mute output)', 'Monitor and Output'].map(o => h('option', { value: o, text: o, selected: o === s.monitoring ? '' : null })));
        monSel.addEventListener('change', () => { s.monitoring = monSel.value; obs.persist(); });
        const tracks = h('div', { class: 'tracks' });
        for (let i = 0; i < 6; i++) {
          const cb = h('input', { type: 'checkbox' });
          cb.checked = !!s.tracks[i];
          cb.addEventListener('change', () => { s.tracks[i] = cb.checked; obs.persist(); });
          tracks.append(h('label', {}, cb, h('span', { text: String(i + 1) })));
        }
        function renderTracks() {}
        tbody.append(h('tr', {},
          h('td', {}, volRange),
          h('td', {}, dbInp),
          h('td', {}, balRange),
          h('td', {}, syncInp),
          h('td', {}, monSel),
          h('td', {}, tracks),
        ));
      }
    }
    table.append(thead, tbody);
  }
  render();
}

/* ============================================================
   OBS Studio — Web Replication · Simulated OBS Core Engine
   Mirrors obs-studio core state: scenes, sources, scene items,
   audio mixer, outputs, transitions, studio mode, profiles,
   scene collections, settings — persisted to localStorage.
   When a real OBS is attached over obs-websocket v5, most
   operations are proxied to it instead (see ws.js).
   ============================================================ */
import { Emitter, uid, deepClone, debounce, clamp, dbToMul, mulToDb } from './util.js';

export const AUDIO_KINDS = new Set([
  'audio_input_capture', 'audio_output_capture', 'application_audio_capture',
  'media_source', 'vlc_source', 'browser_source', 'wasapi_process_output_capture',
]);

export const SOURCE_TYPES = [
  { kind: 'audio_input_capture',       name: 'Audio Input Capture' },
  { kind: 'audio_output_capture',      name: 'Audio Output Capture' },
  { kind: 'application_audio_capture', name: 'Application Audio Capture' },
  { kind: 'browser_source',            name: 'Browser' },
  { kind: 'color_source',              name: 'Color Source' },
  { kind: 'display_capture',           name: 'Display Capture' },
  { kind: 'game_capture',              name: 'Game Capture' },
  { kind: 'image',                     name: 'Image' },
  { kind: 'image_slideshow',           name: 'Image Slide Show' },
  { kind: 'media_source',              name: 'Media Source' },
  { kind: 'text',                      name: 'Text (FreeType 2)' },
  { kind: 'vlc_source',                name: 'VLC Video Source' },
  { kind: 'window_capture',            name: 'Window Capture' },
  { kind: 'group',                     name: 'Group' },
  { kind: 'scene',                     name: 'Scene' },
];

export const FILTER_TYPES = {
  effect: [
    { id: 'lut',          name: 'Apply LUT' },
    { id: 'chroma_key',   name: 'Chroma Key' },
    { id: 'color_key',    name: 'Color Key' },
    { id: 'color_corr',   name: 'Color Correction' },
    { id: 'crop_pad',     name: 'Crop/Pad' },
    { id: 'mask',         name: 'Mask (Alpha Mask, Image Mask/Blend)' },
    { id: 'render_delay', name: 'Render Delay' },
    { id: 'scaling',      name: 'Scaling/Aspect Ratio' },
    { id: 'scroll',       name: 'Scroll' },
    { id: 'sharpness',    name: 'Sharpness' },
  ],
  audio: [
    { id: 'compressor',    name: 'Compressor' },
    { id: 'expander',      name: 'Expander' },
    { id: 'gain',          name: 'Gain' },
    { id: 'invert',        name: 'Invert Polarity' },
    { id: 'limiter',       name: 'Limiter' },
    { id: 'noise_gate',    name: 'Noise Gate' },
    { id: 'noise_supp',    name: 'Noise Suppression' },
    { id: 'upward_comp',   name: 'Upward Compressor' },
    { id: 'vst',           name: 'VST 2.x Plugin' },
  ],
};

export const TRANSITIONS = ['Cut', 'Fade', 'Fade to black', 'Stinger', 'Slide', 'Swipe', 'Zoom'];

const LS_KEY = 'obs-web-state-v1';
const LS_COLLECTION = name => `obs-web-collection-${name}`;
const LS_PROFILE = name => `obs-web-profile-${name}`;

const DEFAULTS = () => ({
  version: '30.2.3 (web)',
  general: {
    language: 'English', theme: 'Dark',
    saveProjectors: true,
    trayEnabled: false, trayMinimize: false, trayAlways: false, trayHide: false, trayNotify: true,
    previewFocusOnClick: true, previewDrawSafeAreas: false, previewHoverSources: true, previewClickEmpty: false,
    snapEnabled: true, snapScreen: true, snapCenter: true, snapSources: false, snapDistance: 10,
    studioReturnPreview: false, studioSceneSel: true,
    autoCheckUpdates: true, autoCheckBeta: false,
    openStatsOnLive: false, confirmOnStop: false,
    hideFromCapture: false, autoOpenProps: true, openProps: 'always',
  },
  stream: {
    service: 'Twitch', server: 'Auto (Recommended)', key: '',
    bandwidthTest: false, auth: false, twitchAuth: false, kickAuth: false,
  },
  output: {
    mode: 'Simple',
    simple: {
      streamVBitrate: 2500, streamVEncoder: 'Software (x264)', streamABitrate: 160,
      enforceBitrate: true,
      recPath: 'C:\\Users\\You\\Videos', recFormat: 'mkv', recVEncoder: 'Software (x264)', recAEncoder: 'AAC',
      replay: false, replayMaxTime: 20, replayMaxSize: 512,
      advEnc: false, customEnc: '',
      tracks: [160, 160, 160, 160, 160, 160],
      muxCustom: '', rescale: false, rescaleRes: '1280x720',
    },
    adv: {
      stream: {
        encoder: 'Software (x264)', enforce: true, rescale: false, rescaleRes: '1280x720',
        rateControl: 'CBR', bitrate: 2500, keyframe: 2, preset: 'veryfast', tuning: 'default',
        multipass: 'Single (low latency)', profile: 'high', lookahead: false, psycho: true,
        gpu: 0, maxBframes: 2, custom: '',
      },
      rec: {
        type: 'Standard', path: 'C:\\Users\\You\\Videos', format: 'mkv',
        encoder: 'Software (x264)', rescale: false, rescaleRes: '1280x720',
        rateControl: 'CRF', bitrate: 2500, keyframe: 0, crf: 23, preset: 'veryfast', custom: '',
      },
      audio: [160, 160, 160, 160, 160, 160],
      replay: { enabled: false, maxTime: 20, maxSize: 512 },
    },
    filenameFmt: '%CCYY-%MM-%DD %hh-%mm-%ss',
    overwriteIfExists: false,
    simpleNoSpace: false, replayWhileStream: false, autoRemux: 'Never',
  },
  audio: {
    sampleRate: 48000, channels: 'Stereo',
    desktopDevice: 'Default', micDevice: 'Default',
    ptt: false, ptm: false, pttDelay: 0, ptmDelay: 0,
    monitorDevice: 'Default',
    meterDecay: 'Medium (Fast)', peakType: 'Sample Peak',
  },
  video: {
    baseRes: '1920x1080', outRes: '1920x1080', downscale: 'Lanczos',
    fpsType: 'Common FPS Values', fps: 60, fpsInt: 60, fpsNum: 30, fpsDen: 1,
  },
  hotkeys: {
    'Start Streaming': [], 'Stop Streaming': [], 'Start Recording': [], 'Stop Recording': [],
    'Enable Studio Mode': [], 'Disable Studio Mode': [], 'Transition (Studio Mode)': [],
    'Take Screenshot': [], 'Enable Virtual Camera': [], 'Disable Virtual Camera': [],
  },
  advanced: {
    processPriority: 'High', renderer: 'Direct3D 11',
    colorFormat: 'NV12', colorSpace: 'Rec. 709', colorRange: 'Partial', sdrWhite: 300,
    streamDelay: false, streamDelaySec: 20, preserveDelay: true,
    reconnect: true, retryDelay: 2, maxRetries: 25,
    browserAccel: true, mediaRewind: false, mediaPause: false,
    autoRemux: 'Never',
  },
  ui: {
    docks: { scenes: true, sources: true, mixer: true, transitions: true, controls: true, stats: false, replay: false },
    mixerLayout: 'horizontal',
    scaling: 'canvas',
  },
});

/* ------------------------- engine ------------------------- */
class ObsEngine extends Emitter {
  constructor() {
    super();
    this.canvas = { w: 1920, h: 1080 };
    this.remote = null;            // obs-websocket client when attached
    this.wsMode = false;
    this._load();
    this._sim = { levels: new Map(), peak: new Map(), phase: Math.random() * 100 };
    this._liveLevels = new Map();  // LOCAL-PATCH (station): real-name -> peak, fed by InputVolumeMeters.
    this._startTimers();
  }

  /* ---------- persistence ---------- */
  _load() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(LS_KEY) || 'null'); } catch {}
    if (s) {
      this.state = s;
      // merge missing defaults (forward-compat)
      const d = DEFAULTS();
      for (const k of Object.keys(d)) if (this.state[k] === undefined) this.state[k] = d[k];
      for (const k of Object.keys(d)) if (k !== 'ui' && typeof d[k] === 'object' && !Array.isArray(d[k]))
        for (const kk of Object.keys(d[k])) if (this.state[k]?.[kk] === undefined) this.state[k][kk] = d[k][kk];
    } else {
      this.state = this._freshState();
      this.persist(true);
    }
    this.canvas = { w: 1920, h: 1080 };
  }

  _freshState() {
    const st = {
      settings: DEFAULTS(),
      collections: ['Untitled'], activeCollection: 'Untitled',
      profiles: ['Untitled'], activeProfile: 'Untitled',
      scenes: [], sources: [], items: {},
      programId: null, previewId: null,
      transition: 'Fade', transitionDur: 300,
      studioMode: false,
      outputs: { streaming: false, recording: false, paused: false, vcam: false, replay: false, streamTime: 0, recTime: 0 },
      ui: DEFAULTS().ui,
    };
    const scene = { id: uid('scene'), name: 'Scene', items: [] };
    st.scenes.push(scene);
    st.programId = scene.id; st.previewId = scene.id;
    // global audio devices (always present, like OBS)
    const taken = new Set();
    st.sources.push(this._mkSource('audio_output_capture', 'Desktop Audio', { global: true }, taken));
    st.sources.push(this._mkSource('audio_input_capture', 'Mic/Aux', { global: true, volumeDb: 0 }, taken));
    return st;
  }

  get S() { return this.state; }
  get settings() { return this.state.settings; }

  persist = debounce((immediate) => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(this.state));
      localStorage.setItem(LS_COLLECTION(this.state.activeCollection), JSON.stringify({
        scenes: this.state.scenes, sources: this.state.sources, items: this.state.items,
        programId: this.state.programId, previewId: this.state.previewId,
      }));
    } catch (e) { console.warn('persist failed', e); }
  }, 400);

  emitc(ev, ...a) { this.emit(ev, ...a); this.persist(); }

  /* ---------- scenes ---------- */
  sceneById(id) { return this.state.scenes.find(s => s.id === id); }
  sceneByName(n) { return this.state.scenes.find(s => s.name === n); }
  get program() { return this.sceneById(this.state.programId); }
  get preview() { return this.state.studioMode ? this.sceneById(this.state.previewId) : this.program; }

  uniqueName(base, taken) {
    if (!taken.has(base)) return base;
    let i = 2;
    while (taken.has(`${base} ${i}`)) i++;
    return `${base} ${i}`;
  }

  createScene(name, silent) {
    const taken = new Set(this.state.scenes.map(s => s.name));
    const sc = { id: uid('scene'), name: this.uniqueName(name || 'Scene', taken), items: [] };
    this.state.scenes.push(sc);
    if (!silent) this.emitc('scenes', { action: 'created', scene: sc });
    return sc;
  }
  removeScene(id) {
    const st = this.state;
    const sc = this.sceneById(id); if (!sc) return;
    for (const iid of [...sc.items]) this.removeItem(sc.id, iid, true);
    // sources of kind scene referencing? keep simple: none
    st.scenes = st.scenes.filter(s => s.id !== id);
    if (st.programId === id) st.programId = st.scenes[0]?.id ?? null;
    if (st.previewId === id) st.previewId = st.programId;
    this.emitc('scenes', { action: 'removed', id });
  }
  renameScene(id, name) {
    const sc = this.sceneById(id); if (!sc) return;
    const taken = new Set(this.state.scenes.filter(s => s.id !== id).map(s => s.name));
    sc.name = this.uniqueName(name.trim() || sc.name, taken);
    this.emitc('scenes', { action: 'renamed', id, name: sc.name });
  }
  reorderScene(id, to) {
    const st = this.state;
    const from = st.scenes.findIndex(s => s.id === id);
    if (from < 0) return;
    const [sc] = st.scenes.splice(from, 1);
    st.scenes.splice(clamp(to, 0, st.scenes.length), 0, sc);
    this.emitc('scenes', { action: 'reordered' });
  }
  duplicateScene(id) {
    const sc = this.sceneById(id); if (!sc) return;
    const taken = new Set(this.state.scenes.map(s => s.name));
    const copy = { id: uid('scene'), name: this.uniqueName(sc.name, taken), items: [] };
    for (const iid of sc.items) {
      const it = this.state.items[iid];
      const nid = uid('item');
      this.state.items[nid] = { ...deepClone(it), id: nid, sceneId: copy.id };
      copy.items.push(nid);
    }
    this.state.scenes.splice(this.state.scenes.indexOf(sc) + 1, 0, copy);
    this.emitc('scenes', { action: 'created', scene: copy });
    return copy;
  }

  setProgram(id, silent) {
    if (this.state.programId === id) return;
    // OBS behavior: when not in studio mode, preview == program
    this.state.programId = id;
    if (!this.state.studioMode) this.state.previewId = id;
    this.emitc(silent ? 'program' : 'program', id);
    this.emit('mixer-structure');
  }
  setPreview(id) {
    if (!this.state.studioMode || this.state.previewId === id) return;
    this.state.previewId = id;
    this.emitc('preview', id);
  }

  /* ---------- sources ---------- */
  _mkSource(kind, name, opt = {}, takenNames) {
    const taken = takenNames || new Set((this.state?.sources || []).map(s => s.name));
    return {
      id: uid('src'), kind, name: this.uniqueName(name, taken),
      settings: defaultSettingsFor(kind),
      muted: false, volumeDb: 0, monitoring: 'none', syncOffset: 0,
      balance: 0.5, tracks: [true, false, false, false, false, false],
      global: !!opt.global, audio: AUDIO_KINDS.has(kind),
      created: Date.now(),
    };
  }

  sourceById(id) { return this.state.sources.find(s => s.id === id); }
  sourceByName(name) { return this.state.sources.find(s => s.name === name); }

  createSource(kind, name, settings, opts = {}) {
    const src = this._mkSource(kind, name);
    if (settings) src.settings = { ...src.settings, ...settings };
    this.state.sources.push(src);
    if (!opts.noScene) this.addItem(opts.sceneId || this.state.previewId, src.id, opts);
    this.emitc('sources', { action: 'created', source: src });
    return src;
  }

  removeSource(id) {
    const st = this.state;
    const src = this.sourceById(id); if (!src) return;
    for (const sc of st.scenes) for (const iid of [...sc.items]) {
      if (st.items[iid]?.sourceId === id) this.removeItem(sc.id, iid, true);
    }
    st.sources = st.sources.filter(s => s.id !== id);
    this.emitc('sources', { action: 'removed', id });
    this.emit('mixer-structure');
  }
  renameSource(id, name) {
    const src = this.sourceById(id); if (!src) return;
    const taken = new Set(this.state.sources.filter(s => s.id !== id).map(s => s.name));
    src.name = this.uniqueName(name.trim() || src.name, taken);
    this.emitc('sources', { action: 'renamed', id, name: src.name });
  }
  setSourceSettings(id, settings) {
    const src = this.sourceById(id); if (!src) return;
    src.settings = { ...src.settings, ...settings };
    this.emitc('sources', { action: 'settings', id });
  }

  /* ---------- scene items ---------- */
  itemsOf(sceneId) {
    const sc = this.sceneById(sceneId);
    return sc ? sc.items.map(iid => this.state.items[iid]).filter(Boolean) : [];
  }
  sourcesOfScene(sceneId) {
    return this.itemsOf(sceneId).map(it => this.sourceById(it.sourceId)).filter(Boolean);
  }

  addItem(sceneId, sourceId, opts = {}) {
    const sc = this.sceneById(sceneId); if (!sc) return null;
    const iid = uid('item');
    const size = opts.w ?? 960, h = opts.h ?? 540;
    const x = opts.x ?? Math.round((this.canvas.w - size) / 2);
    const y = opts.y ?? Math.round((this.canvas.h - h) / 2);
    this.state.items[iid] = {
      id: iid, sceneId, sourceId,
      x, y, w: size, h, rot: 0,
      crop: { l: 0, t: 0, r: 0, b: 0 },
      visible: true, locked: false,
      boundsType: 'none', boundsW: this.canvas.w, boundsH: this.canvas.h, align: 5,
      scaleX: 1, scaleY: 1,
      filters: [],
      sel: false,
    };
    sc.items.push(iid);
    this.emitc('items', { action: 'added', sceneId, itemId: iid });
    if (AUDIO_KINDS.has(this.sourceById(sourceId)?.kind)) this.emit('mixer-structure');
    return this.state.items[iid];
  }
  removeItem(sceneId, itemId, silent) {
    const sc = this.sceneById(sceneId); if (!sc) return;
    const it = this.state.items[itemId]; if (!it) return;
    sc.items = sc.items.filter(i => i !== itemId);
    delete this.state.items[itemId];
    if (AUDIO_KINDS.has(this.sourceById(it.sourceId)?.kind)) this.emit('mixer-structure');
    if (!silent) this.emitc('items', { action: 'removed', sceneId, itemId });
  }
  reorderItem(sceneId, itemId, to) {
    const sc = this.sceneById(sceneId); if (!sc) return;
    const from = sc.items.indexOf(itemId);
    if (from < 0) return;
    sc.items.splice(from, 1);
    const idx = to > from ? to - 1 : to;
    sc.items.splice(clamp(idx, 0, sc.items.length), 0, itemId);
    this.emitc('items', { action: 'reordered', sceneId });
  }
  itemOrder(sceneId, itemId, where) {
    const sc = this.sceneById(sceneId); if (!sc) return;
    const n = sc.items.length;
    const i = sc.items.indexOf(itemId);
    if (where === 'top') this.reorderItem(sceneId, itemId, n - 1);
    else if (where === 'bottom') this.reorderItem(sceneId, itemId, 0);
    else if (where === 'up') this.reorderItem(sceneId, itemId, Math.min(n - 1, i + 1));
    else if (where === 'down') this.reorderItem(sceneId, itemId, Math.max(0, i - 1));
  }
  setItemTransform(itemId, patch) {
    const it = this.state.items[itemId]; if (!it) return;
    Object.assign(it, patch);
    if (patch.crop) it.crop = { ...it.crop, ...patch.crop };
    this.emitc('item-transform', itemId);
  }
  setItemVisible(itemId, v) { const it = this.state.items[itemId]; if (!it) return; it.visible = v; this.emitc('items', { action: 'visible', itemId }); }
  setItemLocked(itemId, v) { const it = this.state.items[itemId]; if (!it) return; it.locked = v; this.emitc('items', { action: 'locked', itemId }); }
  resetItemTransform(itemId) {
    const it = this.state.items[itemId]; if (!it) return;
    Object.assign(it, { x: 0, y: 0, w: this.canvas.w, h: this.canvas.h, rot: 0, crop: { l: 0, t: 0, r: 0, b: 0 }, boundsType: 'none', scaleX: 1, scaleY: 1 });
    this.emitc('item-transform', itemId);
  }
  fitItemToScreen(itemId, stretch) {
    const it = this.state.items[itemId]; if (!it) return;
    if (stretch) Object.assign(it, { x: 0, y: 0, w: this.canvas.w, h: this.canvas.h });
    else {
      const ar = it.w / it.h, car = this.canvas.w / this.canvas.h;
      let w = this.canvas.w, hh = this.canvas.h;
      if (ar > car) hh = Math.round(this.canvas.w / ar); else w = Math.round(this.canvas.h * ar);
      Object.assign(it, { w, h: hh, x: Math.round((this.canvas.w - w) / 2), y: Math.round((this.canvas.h - hh) / 2) });
    }
    this.emitc('item-transform', itemId);
  }
  centerItem(itemId, axis) {
    const it = this.state.items[itemId]; if (!it) return;
    if (axis === 'h' || !axis) it.x = Math.round((this.canvas.w - it.w) / 2);
    if (axis === 'v' || !axis) it.y = Math.round((this.canvas.h - it.h) / 2);
    this.emitc('item-transform', itemId);
  }

  /* selection */
  get selection() {
    const scene = this.preview;
    return scene ? scene.items.map(iid => this.state.items[iid]).filter(it => it?.sel) : [];
  }
  clearSelection() {
    for (const it of Object.values(this.state.items)) if (it.sel) { it.sel = false; }
    this.emit('selection');
  }
  select(itemId, additive) {
    const scene = this.preview;
    if (!additive && scene) for (const iid of scene.items) if (this.state.items[iid]) this.state.items[iid].sel = false;
    const it = this.state.items[itemId];
    if (it) it.sel = additive ? !it.sel : true;
    this.emitc('selection');
  }

  /* ---------- audio ---------- */
  mixerSources() {
    const st = this.state;
    const out = st.sources.filter(s => s.global);
    const prog = this.program;
    if (prog) for (const it of this.itemsOf(prog.id)) {
      const src = this.sourceById(it.sourceId);
      if (src && src.audio && !src.global && !out.includes(src)) out.push(src);
    }
    return out;
  }
  setVolumeDb(id, db) {
    const s = this.sourceById(id); if (!s) return;
    s.volumeDb = clamp(db, -100, 26);
    this.emit('mixer', { id, volumeDb: s.volumeDb });
    this.persist();
  }
  setVolumeMul(id, mul) { this.setVolumeDb(id, mulToDb(mul)); }
  toggleMute(id) { const s = this.sourceById(id); if (s) this.setMute(id, !s.muted); }
  setMute(id, m) {
    const s = this.sourceById(id); if (!s) return;
    s.muted = m;
    this.emit('mixer', { id, muted: m });
    this.persist();
  }

  /* simulated instantaneous level 0..1 (per source) */
  getLevel(id) {
    const s = this.sourceById(id);
    if (!s || s.muted) return { level: 0, peak: 0 };
    // LOCAL-PATCH (station): attached mode reads the live peak pushed by
    // the websocket layer; anything else (or a silent input) simulates.
    if (this.wsMode) {
      const live = this._liveLevels.get(s.name);
      if (live != null) return { level: live, peak: live };
    }
    const now = performance.now() / 1000;
    const seed = this._sim.phase + hashStr(id);
    let base;
    if (s.global && s.kind === 'audio_input_capture') base = micEnv(now + seed);      // mic
    else base = musicEnv(now * 0.7 + seed);                                            // desktop/media
    const mul = dbToMul(s.volumeDb);
    return { level: clamp(base * mul, 0, 1.0), peak: clamp(base * mul, 0, 1) };
  }

  /* LOCAL-PATCH (station): live peak sink for the websocket layer. */
  setLiveLevel(name, peak) {
    this._liveLevels.set(name, Math.max(0, Math.min(1, +peak || 0)));
  }
  clearLiveLevels() {
    this._liveLevels.clear();
  }

  /* ---------- outputs ---------- */
  startStream() {
    if (this.state.outputs.streaming || this.wsMode) return false;
    this.state.outputs.streaming = true;
    this.state.outputs.streamStart = Date.now();
    this._sim.dropped = 0; this._sim.kbps = this.settings.output.simple.streamVBitrate;
    this.emitc('outputs');
    return true;
  }
  stopStream() {
    if (!this.state.outputs.streaming) return false;
    this.state.outputs.streaming = false;
    this.emitc('outputs');
    return true;
  }
  startRecord() {
    if (this.state.outputs.recording || this.wsMode) return false;
    this.state.outputs.recording = true; this.state.outputs.paused = false;
    this.state.outputs.recStart = Date.now();
    this.emitc('outputs');
    return true;
  }
  stopRecord() {
    if (!this.state.outputs.recording) return false;
    this.state.outputs.recording = false; this.state.outputs.paused = false;
    this.emitc('outputs');
    return true;
  }
  pauseRecord() {
    const o = this.state.outputs;
    if (!o.recording) return false;
    o.paused = !o.paused;
    this.emitc('outputs');
    return true;
  }
  toggleVCam() {
    this.state.outputs.vcam = !this.state.outputs.vcam;
    this.emitc('outputs');
    return true;
  }
  toggleReplay() {
    this.state.outputs.replay = !this.state.outputs.replay;
    this.emitc('outputs');
    return true;
  }
  saveReplay() { this.log('info', `Saved replay buffer to "${this.settings.output.simple.recPath}"`); }

  /* ---------- transitions / studio ---------- */
  setTransition(name) { this.state.transition = name; this.emitc('transition'); }
  setTransitionDur(ms) { this.state.transitionDur = clamp(ms | 0, 50, 20000); this.emitc('transition'); }
  setStudioMode(on) {
    const st = this.state;
    if (st.studioMode === on) return;
    st.studioMode = on;
    if (on) { st.previewId = st.programId; }
    else { st.previewId = st.programId; this.clearSelection(); }
    this.emitc('studio', on);
  }
  triggerTransition() {
    const st = this.state;
    if (!st.studioMode || st.previewId === st.programId) return;
    const from = st.programId, to = st.previewId;
    st.programId = to;
    this.emit('program', to);
    this.emit('transition-start', { from, to, type: st.transition, dur: st.transition === 'Cut' ? 0 : st.transitionDur });
    this.emit('mixer-structure');
    this.persist();
  }

  /* ---------- screenshots ---------- */
  screenshotScene(sceneId, cb) {
    this.emit('request-screenshot', { sceneId, cb });
  }

  /* ---------- profiles & collections ---------- */
  switchProfile(name) {
    if (!this.state.profiles.includes(name)) return;
    this.state.activeProfile = name;
    this.emitc('profile', name);
    this.emit('log', { level: 'info', msg: `Profile '${name}' activated` });
  }
  createProfile(name, dup) {
    name = name.trim(); if (!name) return;
    if (dup && this.state.profiles.includes(this.state.activeProfile)) {
      const srcState = localStorage.getItem(LS_PROFILE(this.state.activeProfile));
      if (srcState) localStorage.setItem(LS_PROFILE(name), srcState);
    }
    if (!this.state.profiles.includes(name)) this.state.profiles.push(name);
    this.switchProfile(name);
  }
  renameProfile(oldN, newN) {
    const i = this.state.profiles.indexOf(oldN);
    if (i < 0 || !newN.trim()) return;
    this.state.profiles[i] = newN.trim();
    if (this.state.activeProfile === oldN) this.state.activeProfile = newN.trim();
    this.emitc('profile');
  }
  removeProfile(name) {
    if (this.state.profiles.length <= 1) return;
    this.state.profiles = this.state.profiles.filter(p => p !== name);
    if (this.state.activeProfile === name) this.switchProfile(this.state.profiles[0]);
    this.emitc('profile');
  }

  switchCollection(name) {
    if (!this.state.collections.includes(name)) return;
    this.persist();
    const saved = localStorage.getItem(LS_COLLECTION(name));
    this.state.activeCollection = name;
    if (saved) {
      try {
        const d = JSON.parse(saved);
        Object.assign(this.state, {
          scenes: d.scenes || [], sources: d.sources || [], items: d.items || {},
          programId: d.programId, previewId: d.previewId,
        });
        if (!this.sceneById(this.state.programId) && this.state.scenes[0]) {
          this.state.programId = this.state.previewId = this.state.scenes[0].id;
        }
      } catch {}
    } else {
      const fresh = this._freshState();
      Object.assign(this.state, {
        scenes: fresh.scenes, sources: fresh.sources, items: fresh.items,
        programId: fresh.programId, previewId: fresh.previewId,
      });
    }
    this.emitc('collection', name);
    this.emit('mixer-structure');
  }
  createCollection(name, dup) {
    name = name.trim(); if (!name || this.state.collections.includes(name)) return;
    this.state.collections.push(name);
    if (dup) {
      const cur = localStorage.getItem(LS_COLLECTION(this.state.activeCollection));
      if (cur) localStorage.setItem(LS_COLLECTION(name), cur);
    }
    this.switchCollection(name);
  }
  renameCollection(oldN, newN) {
    const i = this.state.collections.indexOf(oldN);
    if (i < 0 || !newN.trim() || this.state.collections.includes(newN.trim())) return;
    const saved = localStorage.getItem(LS_COLLECTION(oldN));
    localStorage.removeItem(LS_COLLECTION(oldN));
    if (saved) localStorage.setItem(LS_COLLECTION(newN.trim()), saved);
    this.state.collections[i] = newN.trim();
    if (this.state.activeCollection === oldN) this.state.activeCollection = newN.trim();
    this.emitc('collection');
  }
  removeCollection(name) {
    if (this.state.collections.length <= 1) return;
    localStorage.removeItem(LS_COLLECTION(name));
    const wasActive = this.state.activeCollection === name;
    this.state.collections = this.state.collections.filter(c => c !== name);
    if (wasActive) this.switchCollection(this.state.collections[0]);
    this.emitc('collection');
  }

  resetUI() {
    this.state.ui = DEFAULTS().ui;
    this.emitc('ui-reset');
  }

  setTheme(t) {
    this.settings.general.theme = t;
    this.emit('theme', t);
    this.persist();
  }

  log(level, msg) { this.emit('log', { level, msg, t: Date.now() }); }

  /* ---------- sim timers ---------- */
  _startTimers() {
    setInterval(() => {
      const o = this.state.outputs;
      if (o.streaming) {
        o.streamTime += 0.5;
        if (!this.wsMode) {
          const target = this.settings.output.simple.streamVBitrate;
          this._sim.kbps = Math.max(0, (this._sim.kbps ?? target) + (Math.random() - 0.48) * 60);
          const dropP = this._sim.kbps < target * 0.8 ? 0.004 : 0.0004;
          if (Math.random() < dropP) this._sim.dropped = (this._sim.dropped || 0) + 1;
        }
      }
      if (o.recording && !o.paused) o.recTime += 0.5;
      this.emit('outputs-tick');
    }, 500);

    setInterval(() => {
      if (this.wsMode) return; // stats come from real OBS
      const s = this._sim;
      s.cpu = clamp((s.cpu ?? 3) + (Math.random() - 0.5) * 1.6, 0.6, 22);
      s.mem = clamp((s.mem ?? 312) + (Math.random() - 0.5) * 6, 240, 640);
      s.fps = Math.random() < 0.02 ? 59.9 : 60;
      s.renderMs = clamp((s.renderMs ?? 2.1) + (Math.random() - 0.5) * 0.5, 0.8, 8);
      s.skipped = (s.skipped || 0) + (Math.random() < 0.01 ? 1 : 0);
      this.emit('stats-tick');
    }, 1000);
  }
}

/* pseudo audio envelopes */
function hashStr(str) { let h = 0; for (let i = 0; i < str.length; i++) { h = (h * 31 + str.charCodeAt(i)) | 0; } return (h >>> 0) % 1000 / 100; }
function musicEnv(t) {
  const beat = Math.abs(Math.sin(t * Math.PI * 2 * 1.7));
  const bar = 0.45 + 0.35 * Math.sin(t * 0.35);
  return clamp(beat * bar * (0.75 + 0.25 * Math.sin(t * 5.1)), 0, 1) * 0.85;
}
function micEnv(t) {
  const talk = (Math.sin(t * 0.9) > 0.1) ? 1 : 0.04;
  const wobble = 0.55 + 0.45 * Math.sin(t * 11.3) * Math.sin(t * 3.7);
  return clamp(talk * wobble, 0, 1) * 0.8;
}

export function defaultSettingsFor(kind) {
  switch (kind) {
    case 'display_capture': return { method: 'Windows 10 (1903 and up)', display: 0, cursor: true };
    case 'window_capture': return { method: 'Windows 10 (1903 and up)', window: 'OBS Studio — Web Replication', priority: 1, cursor: true };
    case 'game_capture': return { mode: 'Capture any fullscreen application', window: '', antiCheat: true, hookRate: 'Fast' };
    case 'browser_source': return { url: 'https://obsproject.com', width: 1280, height: 720, fps: 30, css: 'body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }', restart: false, shutdown: false, refresh: false, local: false };
    case 'color_source': return { color: '#ff404040', width: 1920, height: 1080 };
    case 'image': return { file: '', unload: false, linearAlpha: true };
    case 'image_slideshow': return { files: [], slideTime: 8000, transition: 'Fade', transitionTime: 300, randomize: false, loop: true, hide: false };
    case 'media_source': return { local: true, file: '', input: '', inputFormat: '', buffering: 2, closeInactive: false, restartOnActivate: true, hwDecode: false, loop: false, speed: 100 };
    case 'text': return { text: 'Your Text Here', font: { face: 'Arial', size: 256, bold: false, italic: false }, color: '#ffffffff', outline: false, outlineColor: '#ff000000', outlineSize: 2, shadow: false, align: 'left', valign: 'top', width: 0, height: 0, antialias: true };
    case 'audio_input_capture': return { device: 'Default', disableDucking: false };
    case 'audio_output_capture': return { device: 'Default' };
    case 'application_audio_capture': return { window: '', priority: 1 };
    case 'vlc_source': return { playlist: [], loop: true, shuffle: false, fullscreen: true };
    case 'group': return {};
    case 'scene': return {};
    default: return {};
  }
}

export const obs = new ObsEngine();

/* ============================================================
   OBS Studio — Web Replication · obs-websocket v5 Client
   Implements the obs-websocket 5.x JSON protocol (official opcodes):
     Hello(0) → Identify(1) → Identified(2) → Reidentify(3)
     Event(4) · Request(5) · RequestResponse(6)
     RequestBatch(7) · RequestBatchResponse(8)
   Attaches the web GUI to a REAL OBS Studio instance: mirrors
   UI actions as RPC requests, reconciles state from events,
   and renders the real program/preview via GetSourceScreenshot.
   ============================================================ */
import { h, sha256B64, deepClone } from './util.js';
import { obs, AUDIO_KINDS } from './engine.js';
import { openDialog, msgBox, toast } from './ui.js';
import { setRemoteFrame } from './preview.js';
import { openWsSettings } from './tools.js';

const KIND_MAP = {
  wasapi_input_capture: 'audio_input_capture',
  wasapi_process_output_capture: 'application_audio_capture',
  wasapi_output_capture: 'audio_output_capture',
  pulse_input_capture: 'audio_input_capture',
  pulse_output_capture: 'audio_output_capture',
  coreaudio_input_capture: 'audio_input_capture',
  coreaudio_output_capture: 'audio_output_capture',
  dshow_input: 'media_source',
  avfoundation_input: 'media_source',
  browser_source: 'browser_source',
  ffmpeg_source: 'media_source',
  text_ft2_source: 'text',
  text_gdiplus: 'text',
  game_capture: 'game_capture',
  window_capture: 'window_capture',
  screen_capture: 'display_capture',
  monitor_capture: 'display_capture',
  display_capture: 'display_capture',
  color_source: 'color_source',
  image_source: 'image',
  slideshow: 'image_slideshow',
  vlc_source: 'vlc_source',
  scene: 'scene',
  group: 'group',
};

const state = {
  ws: null,
  status: 'offline', // offline | connecting | connected | error
  config: { enabled: false, port: 4455, auth: true, password: '', host: 'localhost', refresh: 1000, gateway: true },
  url: '',
  reqId: 1,
  pending: new Map(),
  pendingBatch: new Map(),
  patches: [],
  busy: false,
  obsVersion: '',
  itemSourceSize: new Map(), // itemId -> {w,h} native source size
  timers: [],
};

export const wsApi = {
  get status() { return state.status; },
  get config() { return state.config; },
  connect,
  disconnect,
  request,
  requestBatch,
  openConnect,
  openSettings: () => openWsSettings(wsApi),
};

obs.on('log', l => obs._logFeed?.(l));

/* ---------------- connect dialog ---------------- */
export function openConnect() {
  const cfg = state.config;
  const hostInp = h('input', { class: 'qinput', value: cfg.host || 'localhost', style: { width: '160px' } });
  const portInp = h('input', { class: 'qinput', type: 'number', value: cfg.port, style: { width: '90px' } });
  const pwdInp = h('input', { class: 'qinput', type: 'password', value: cfg.password || '', style: { width: '160px' } });
  const refreshInp = h('input', { class: 'qinput', type: 'number', value: cfg.refresh, style: { width: '90px' } });
  const gwChk = h('input', { type: 'checkbox' });
  gwChk.checked = cfg.gateway !== false;
  const statusLine = h('div', { class: 'hint', html: statusHtml() });

  const body = h('div', { style: { padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' } },
    h('div', { class: 'form-grid' },
      h('label', { text: 'Host' }), hostInp,
      h('label', { text: 'Port' }), portInp,
      h('label', { text: 'Password' }), pwdInp,
      h('label', { text: 'Preview refresh (ms)' }), refreshInp,
      h('label', { text: 'Route via page gateway' }), h('label', { class: 'qcheck', 'data-tip': 'Uses the same origin as this page (XTransformPort) — avoids mixed-content blocks. Uncheck to connect directly to ws://host:port.' }, gwChk, h('span', { class: 'box' })),
    ),
    statusLine,
    h('div', { class: 'hint', html:
      'Connects this page to a real OBS Studio running <b>obs-websocket v5</b> (Tools ▸ WebSocket Server Settings in your OBS).<br>' +
      '⚠ If you opened this page over <b>https</b>, browsers block plain <b>ws://</b> to localhost (mixed content). ' +
      'Keep gateway routing enabled, run this page locally over http, or use a wss:// tunnel to OBS.' }),
  );

  const d = openDialog({
    title: 'Connect to OBS (obs-websocket v5)', w: 480, resizable: false,
    content: body,
    buttons: [
      { label: 'Connect', def: true, action: () => {
          cfg.host = hostInp.value.trim() || 'localhost';
          cfg.port = parseInt(portInp.value) || 4455;
          cfg.password = pwdInp.value;
          cfg.refresh = Math.max(250, parseInt(refreshInp.value) || 1000);
          cfg.gateway = gwChk.checked;
          d.close();
          connect();
        } },
      state.status === 'connected' ? { label: 'Disconnect', danger: true, action: () => { disconnect(); d.close(); } } : null,
      { label: 'Cancel', action: () => d.close() },
    ],
  });
  const off = obs.on('ws-status', () => { statusLine.innerHTML = statusHtml(); });
  d.body._off = off;
}
function statusHtml() {
  const s = state.status;
  const cls = s === 'connected' ? 'on' : '';
  return `<span class="ws-badge ${cls}"><span class="dot"></span>${s}${state.obsVersion ? ' — OBS ' + state.obsVersion : ''}</span>`;
}

/* ---------------- core client ---------------- */
function setStatus(s, extra) {
  state.status = s;
  obs.emit('ws-status', s);
  obs.log('info', `WebSocket: ${s}${extra ? ' — ' + extra : ''}`);
}

function connect() {
  disconnect(true);
  const { host, port } = state.config;
  state.url = buildWsUrl();
  setStatus('connecting', state.url);
  let ws;
  try { ws = new WebSocket(state.url); }
  catch (e) { setStatus('error', e.message); return; }
  state.ws = ws;

  ws.onopen = () => { /* wait for Hello */ };
  ws.onmessage = (ev) => {
    let msg; try { msg = JSON.parse(ev.data); } catch { return; }
    handle(msg);
  };
  ws.onerror = () => { setStatus('error', 'connection failed (is OBS + obs-websocket running? mixed content?)'); };
  ws.onclose = () => {
    if (state.status !== 'offline') {
      unpatchEngine();
      setStatus('offline');
      msgBox({ title: 'WebSocket', text: 'Disconnected from OBS.', icon: 'info' });
    }
  };
}

function disconnect(silent) {
  for (const t of state.timers) clearInterval(t);
  state.timers = [];
  if (state.ws) { try { state.ws.onclose = null; state.ws.close(); } catch {} state.ws = null; }
  unpatchEngine();
  obs.wsMode = false;
  obs.clearLiveLevels();  // LOCAL-PATCH (station): no frozen meters after a drop.
  if (!silent) setStatus('offline');
}

async function handle(msg) {
  const { op } = msg;
  if (op === 0) { // Hello
    const hello = msg.d || {};
    state.obsVersion = (hello.obsWebSocketVersion || '').replace(/^(\d+\.\d+\.\d+).*$/, '$1');
    // EventSubscriptions: Config|Scenes|Inputs|Transitions|Filters|Outputs|MediaInputs|Vendors|Ui = bits 0..8
    // LOCAL-PATCH (station): + Meters bit 16 — without it live mixer levels never arrive.
    const identify = { op: 1, d: { rpcVersion: 1, eventSubscriptions: 0x1FF | 0x10000 } };
    if (hello.authentication) {
      const { challenge, salt } = hello.authentication;
      const secret = await sha256B64(state.config.password + salt);
      identify.d.authentication = await sha256B64(secret + challenge);
    }
    send(identify);
  } else if (op === 2) { // Identified
    setStatus('connected', state.url);
    obs.wsMode = true;
    patchEngine();
    await initialSync();
    startPolling();
    toast(`Connected to OBS ${state.obsVersion || ''}`.trim());
  } else if (op === 4) { // Event
    handleEvent(msg.d || {});
  } else if (op === 6) { // RequestResponse
    const d = msg.d || {};
    const p = state.pending.get(d.requestId);
    if (p) {
      state.pending.delete(d.requestId);
      if (d.requestStatus?.result) p.resolve(d.responseData || {});
      else p.reject(new Error(`${d.responseType || 'Request'} failed: ${codeName(d.requestStatus?.code)}`));
    }
  } else if (op === 8) { // RequestBatchResponse
    const d = msg.d || {};
    const p = state.pendingBatch.get(d.requestId);
    if (p) {
      state.pendingBatch.delete(d.requestId);
      p.resolve(d.results || []);
    }
  }
}

function send(obj) { if (state.ws?.readyState === 1) state.ws.send(JSON.stringify(obj)); }

/* URL builder — gateway mode (default) routes through the same origin the page was
 * served from using the XTransformPort query (works from the preview URL and avoids
 * mixed-content when the page is https). Direct mode speaks ws://host:port verbatim. */
export function buildWsUrl() {
  const { host, port } = state.config;
  if (state.config.gateway !== false) {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${location.host}/?XTransformPort=${port}`;
  }
  return `ws://${host}:${port}`;
}

export function request(requestType, requestData = {}) {
  return new Promise((resolve, reject) => {
    if (state.status !== 'connected') { reject(new Error('not connected')); return; }
    const requestId = `r${state.reqId++}`;
    state.pending.set(requestId, { resolve, reject });
    send({ op: 5, d: { requestType, requestId, requestData } });
    setTimeout(() => {
      if (state.pending.has(requestId)) { state.pending.delete(requestId); reject(new Error(`${requestType} timed out`)); }
    }, 5000);
  });
}

/* obs-websocket v5 RequestBatch (op 7 → op 8) */
export function requestBatch(requests, { haltOnFailure = false } = {}) {
  return new Promise((resolve, reject) => {
    if (state.status !== 'connected') { reject(new Error('not connected')); return; }
    const requestId = `b${state.reqId++}`;
    state.pendingBatch.set(requestId, { resolve, reject });
    send({ op: 7, d: { requestId, haltOnFailure, requests: requests.map(r => ({ requestType: r.requestType || r[0], requestId: `r${state.reqId++}`, requestData: r.requestData || r[1] || {} })) } });
    setTimeout(() => {
      if (state.pendingBatch.has(requestId)) { state.pendingBatch.delete(requestId); reject(new Error('RequestBatch timed out')); }
    }, 8000);
  });
}

function codeName(code) {
  return ({
    0: 'Unknown', 100: 'Success', 200: 'MissingRequestField', 203: 'UnknownRequestType',
    300: 'Unsupported', 500: 'NotConnected', 600: 'ResourceNotFound', 700: 'InvalidResourceType',
  })[code] || `code ${code}`;
}

/* ---------------- engine patching (mirror UI actions → RPC) ---------------- */
function patchEngine() {
  if (state.patches.length) return;
  const wrap = (obj, method, rpc) => {
    const orig = obj[method].bind(obj);
    state.patches.push([obj, method, orig]);
    obj[method] = (...args) => {
      const r = orig(...args);
      if (!state.busy && state.status === 'connected') {
        Promise.resolve().then(() => { try { rpc(args, r); } catch (e) { obs.log('warn', `WS mirror ${method}: ${e.message}`); } });
      }
      return r;
    };
  };
  const sceneName = id => obs.sceneById(id)?.name;
  const E = obs;

  wrap(E, 'createScene', ([name]) => request('CreateScene', { sceneName: name }).catch(() => {}));
  wrap(E, 'removeScene', ([id]) => request('RemoveScene', { sceneName: sceneName(id) }).catch(() => {}));
  wrap(E, 'renameScene', ([id, name]) => request('SetSceneName', { sceneName: sceneName(id), newSceneName: name }).catch(() => {}));
  // LOCAL-PATCH (station): no scene-reorder exists in obs-websocket v5;
  // the old call failed silently. Local order only, said out loud.
  wrap(E, 'reorderScene', () => { obs.log('warn', 'Server scene order is fixed; reorder applies locally only.'); });
  wrap(E, 'setProgram', ([id]) => request('SetCurrentProgramScene', { sceneName: sceneName(id) }).catch(() => {}));
  wrap(E, 'setPreview', ([id]) => request('SetCurrentPreviewScene', { sceneName: sceneName(id) }).catch(() => {}));
  wrap(E, 'createSource', ([kind, name, settings, opts], r) => {
    if (kind === 'scene' || kind === 'group') return;
    const scName = sceneName(opts?.sceneId || obs.S.previewId);
    request('CreateInput', { sceneName: scName, inputName: r?.name || name, inputKind: reverseKind(kind), inputSettings: settings || {} }).catch(() => {});
  });
  wrap(E, 'removeSource', ([id]) => request('RemoveInput', { inputName: obs.sourceById(id)?.name }).catch(() => {}));
  wrap(E, 'renameSource', ([id, name]) => request('SetInputName', { inputName: obs.sourceById(id)?.name, newInputName: name }).catch(() => {}));
  wrap(E, 'setSourceSettings', ([id, settings]) => request('SetInputSettings', { inputName: obs.sourceById(id)?.name, inputSettings: settings }).catch(() => {}));
  wrap(E, 'addItem', ([sceneId, sourceId], r) => {
    const src = obs.sourceById(sourceId);
    if (src && (src.kind === 'scene' || src.kind === 'group' || src.global)) return;
    request('CreateSceneItem', { sceneName: sceneName(sceneId), sourceName: src?.name }).catch(() => {});
  });
  wrap(E, 'removeItem', ([sceneId, itemId]) => {
    const it = obs.S.items[itemId]; if (!it) return;
    const src = obs.sourceById(it.sourceId);
    if (src && (src.kind === 'scene' || src.kind === 'group' || src.global)) return;
    request('RemoveSceneItem', { sceneName: sceneName(sceneId), sceneItemId: obsItemToObsId(itemId) }).catch(() => {});
  });
  wrap(E, 'reorderItem', ([sceneId, itemId, to]) => {
    request('SetSceneItemIndex', { sceneName: sceneName(sceneId), sceneItemId: obsItemToObsId(itemId), sceneItemIndex: to }).catch(() => {});
  });
  wrap(E, 'setItemTransform', ([itemId, patch], r) => mirrorTransform(itemId, r));
  wrap(E, 'setItemVisible', ([itemId, v]) => request('SetSceneItemEnabled', { sceneName: sceneName(obs.S.items[itemId]?.sceneId), sceneItemId: obsItemToObsId(itemId), sceneItemEnabled: !!v }).catch(() => {}));
  wrap(E, 'setItemLocked', ([itemId, v]) => request('SetSceneItemLocked', { sceneName: sceneName(obs.S.items[itemId]?.sceneId), sceneItemId: obsItemToObsId(itemId), sceneItemLocked: !!v }).catch(() => {}));
  wrap(E, 'resetItemTransform', ([itemId]) => mirrorTransform(itemId, { reset: true }));
  wrap(E, 'setVolumeDb', ([id, db]) => request('SetInputVolume', { inputName: obs.sourceById(id)?.name, inputVolumeDb: db }).catch(() => {}));
  wrap(E, 'setMute', ([id, m]) => request('SetInputMute', { inputName: obs.sourceById(id)?.name, inputMuted: !!m }).catch(() => {}));
  wrap(E, 'startStream', () => request('StartStream').catch(e => obs.log('warn', e.message)));
  wrap(E, 'stopStream', () => request('StopStream').catch(e => obs.log('warn', e.message)));
  wrap(E, 'startRecord', () => request('StartRecord').catch(e => obs.log('warn', e.message)));
  wrap(E, 'stopRecord', () => request('StopRecord').catch(e => obs.log('warn', e.message)));
  wrap(E, 'pauseRecord', () => request('ToggleRecordPause').catch(() => {}));
  wrap(E, 'toggleVCam', () => request('ToggleVirtualCam').catch(() => {}));
  wrap(E, 'toggleReplay', () => request('ToggleReplayBuffer').catch(() => {}));
  wrap(E, 'saveReplay', () => request('SaveReplayBuffer').catch(() => {}));
  // LOCAL-PATCH (station): real v5 field is transitionName, not sceneTransitionName.
  wrap(E, 'setTransition', ([name]) => request('SetCurrentSceneTransition', { transitionName: name }).catch(() => {}));
  wrap(E, 'setTransitionDur', ([ms]) => request('SetCurrentSceneTransitionDuration', { sceneTransitionDuration: ms }).catch(() => {}));
  wrap(E, 'triggerTransition', () => request('TriggerStudioModeTransition').catch(() => {}));
  wrap(E, 'setStudioMode', ([on]) => request('SetStudioModeEnabled', { studioModeEnabled: !!on }).catch(() => {}));
}

function unpatchEngine() {
  for (const [obj, method, orig] of state.patches) obj[method] = orig;
  state.patches = [];
}

function reverseKind(kind) {
  for (const [obsKind, ourKind] of Object.entries(KIND_MAP)) if (ourKind === kind) return obsKind;
  return 'ffmpeg_source';
}

/* local item id → OBS numeric sceneItemId (learned during sync) */
const itemIdMap = new Map(); // obsWebItemId -> obs numeric id
const obsIdMap = new Map();  // obs numeric id -> obsWebItemId
function obsItemToObsId(localId) { return itemIdMap.get(localId); }

async function mirrorTransform(itemId, patch) {
  const it = obs.S.items[itemId]; if (!it) return;
  let native = state.itemSourceSize.get(itemId);
  if (!native) {
    try {
      const r = await request('GetSceneItemTransform', { sceneName: obs.sceneById(it.sceneId)?.name, sceneItemId: itemIdMap.get(itemId) });
      native = { w: r.sourceWidth || 1920, h: r.sourceHeight || 1080 };
    } catch { native = { w: 1920, h: 1080 }; }
    state.itemSourceSize.set(itemId, native);
  }
  const transform = {
    positionX: Math.round(it.x), positionY: Math.round(it.y),
    rotation: it.rot || 0,
    scaleX: it.w / native.w, scaleY: it.h / native.h,
    cropLeft: it.crop.l | 0, cropTop: it.crop.t | 0, cropRight: it.crop.r | 0, cropBottom: it.crop.b | 0,
  };
  request('SetSceneItemTransform', { sceneName: obs.sceneById(it.sceneId)?.name, sceneItemId: itemIdMap.get(itemId), sceneTransform: transform }).catch(() => {});
}

/* ---------------- initial sync ---------------- */
async function initialSync() {
  state.busy = true;
  try {
    const ver = await request('GetVersion');
    obs.log('info', `OBS ${ver.obsVersion} · obs-websocket ${ver.obsWebSocketVersion} · RPC ${ver.rpcVersion}`);

    const sceneList = await request('GetSceneList');
    const localScenes = [];
    itemIdMap.clear(); obsIdMap.clear();
    const itemsToBuild = [];
    for (const sc of sceneList.scenes) {
      const local = obs.sceneByName(sc.sceneName) || { id: `scene-${sc.sceneIndex}-${sc.sceneName}`, name: sc.sceneName, items: [] };
      if (!obs.sceneByName(sc.sceneName)) obs.S.scenes.push(local);
      localScenes.push(local);
      try {
        const sil = await request('GetSceneItemList', { sceneName: sc.sceneName });
        for (const it of sil.sceneItems) {
          itemsToBuild.push({ scene: local, obs: it });
        }
      } catch {}
    }
    obs.S.scenes = localScenes;

    // inputs
    const inputList = await request('GetInputList');
    for (const inp of inputList.inputs) {
      let src = obs.sourceByName?.(inp.inputName);
      if (!src) {
        const kind = KIND_MAP[inp.inputKind] || 'media_source';
        src = {
          id: `src-${inp.inputName}`, kind, name: inp.inputName,
          settings: {}, muted: false, volumeDb: 0, monitoring: 'none',
          syncOffset: 0, balance: 0.5, tracks: [true, false, false, false, false, false],
          global: false, audio: AUDIO_KINDS.has(kind), remote: true, inputKind: inp.inputKind,
        };
        obs.S.sources.push(src);
        if (src.audio) {
          try {
            const vol = await request('GetInputVolume', { inputName: inp.inputName });
            src.volumeDb = vol.inputVolumeDb ?? 0;
          } catch {}
          try {
            const mute = await request('GetInputMute', { inputName: inp.inputName });
            src.muted = !!mute.inputMuted;
          } catch {}
        }
      }
    }

    // scene items with transforms
    for (const { scene, obs: oit } of itemsToBuild) {
      const src = obs.S.sources.find(s => s.name === oit.sourceName);
      if (!src) continue;
      const t = oit.sceneItemTransform || {};
      const native = { w: oit.sourceWidth || 1920, h: oit.sourceHeight || 1080 };
      const scaleX = t.scaleX ?? 1, scaleY = t.scaleY ?? 1;
      const w = Math.round(native.w * Math.abs(scaleX)) || 960;
      const h = Math.round(native.h * Math.abs(scaleY)) || 540;
      const localId = `item-${oit.sceneItemId}`;
      const item = {
        id: localId, sceneId: scene.id, sourceId: src.id,
        x: Math.round(t.positionX ?? 0), y: Math.round(t.positionY ?? 0),
        w, h, rot: t.rotation || 0,
        crop: { l: t.cropLeft | 0, t: t.cropTop | 0, r: t.cropRight | 0, b: t.cropBottom | 0 },
        visible: oit.sceneItemEnabled !== false, locked: !!oit.sceneItemLocked,
        boundsType: 'none', align: 5, scaleX, scaleY, filters: [], sel: false,
      };
      obs.S.items[localId] = item;
      scene.items.push(localId);
      itemIdMap.set(localId, oit.sceneItemId);
      obsIdMap.set(oit.sceneItemId, localId);
      state.itemSourceSize.set(localId, native);
    }

    // program/preview
    obs.S.programId = obs.sceneByName(sceneList.currentProgramSceneName)?.id || obs.S.scenes[0]?.id;
    if (sceneList.currentPreviewSceneName) obs.S.previewId = obs.sceneByName(sceneList.currentPreviewSceneName)?.id;
    else obs.S.previewId = obs.S.programId;

    // studio mode
    try {
      const sm = await request('GetStudioModeEnabled');
      obs.S.studioMode = !!sm.studioModeEnabled;
    } catch {}
    // transition
    try {
      const tr = await request('GetCurrentSceneTransition');
      if (tr?.transitionName) { obs.S.transition = tr.transitionName; obs.S.transitionDur = tr.transitionDuration || 300; }
    } catch {}
    // outputs
    try {
      const os = await request('GetStreamStatus').catch(() => null);
      if (os) {
        obs.S.outputs.streaming = !!os.outputActive;
      }
    } catch {}
    try {
      const rs = await request('GetRecordStatus');
      obs.S.outputs.recording = !!rs.outputActive;
      obs.S.outputs.paused = !!rs.outputPaused;
    } catch {}

    obs.emit('scenes'); obs.emit('sources'); obs.emit('items');
    obs.emit('program', obs.S.programId); obs.emit('preview', obs.S.previewId);
    obs.emit('studio', obs.S.studioMode); obs.emit('outputs'); obs.emit('transition');
    obs.emit('mixer-structure');
    obs.persist();
  } catch (e) {
    obs.log('warn', `Initial sync: ${e.message}`);
  } finally {
    state.busy = false;
  }
}

/* ---------------- polling (stats + live screenshots) ---------------- */
function startPolling() {
  const stats = setInterval(async () => {
    if (state.status !== 'connected') return;
    try {
      const st = await request('GetStats');
      obs._sim.cpu = st.cpuUsage ?? 0;
      obs._sim.mem = st.memoryUsage ?? 0;
      obs._sim.fps = st.activeFps ?? st.renderedFrames ?? 60;
      obs._sim.kbps = obs.S.outputs.streaming ? (st.bitrate ?? 0) : 0;
      obs._sim.dropped = obs.S.outputs.streaming ? (st.numDroppedFrames ?? 0) : 0;
      obs.emit('stats-tick');
    } catch {}
  }, 1000);
  state.timers.push(stats);

  let progName = null, prevName = null;
  const shot = setInterval(async () => {
    if (state.status !== 'connected') return;
    try {
      const scenes = await request('GetSceneList');
      progName = scenes.currentProgramSceneName; prevName = scenes.currentPreviewSceneName;
      const prog = obs.sceneByName(progName);
      if (prog) {
        const r = await request('GetSourceScreenshot', { sourceName: progName, imageFormat: 'png', imageWidth: 960 });
        if (r.imageData) setRemoteFrame(prog.id, r.imageData);
      }
      if (obs.S.studioMode && prevName) {
        const prev = obs.sceneByName(prevName);
        if (prev) {
          const r = await request('GetSourceScreenshot', { sourceName: prevName, imageFormat: 'png', imageWidth: 960 });
          if (r.imageData) setRemoteFrame(prev.id, r.imageData);
        }
      }
    } catch {}
  }, Math.max(250, state.config.refresh || 1000));
  state.timers.push(shot);
}

/* ---------------- events ---------------- */
function handleEvent(d) {
  state.busy = true;
  const done = () => { state.busy = false; };
  try {
    switch (d.eventType) {
      case 'CurrentProgramSceneChanged': {
        const sc = obs.sceneByName(d.eventData.sceneName);
        if (sc) { obs.S.programId = sc.id; obs.emit('program', sc.id); obs.emit('mixer-structure'); }
        break;
      }
      case 'CurrentPreviewSceneChanged': {
        const sc = obs.sceneByName(d.eventData.sceneName);
        if (sc) { obs.S.previewId = sc.id; obs.emit('preview', sc.id); }
        break;
      }
      case 'SceneCreated': obs.createScene(d.eventData.sceneName, true); obs.emit('scenes'); break;
      case 'SceneRemoved': {
        const sc = obs.sceneByName(d.eventData.sceneName);
        if (sc) { obs.S.scenes = obs.S.scenes.filter(s => s.id !== sc.id); obs.emit('scenes'); }
        break;
      }
      case 'SceneNameChanged': {
        const sc = obs.sceneByName(d.eventData.oldSceneName);
        if (sc) { sc.name = d.eventData.sceneName; obs.emit('scenes'); }
        break;
      }
      case 'SceneListChanged': refreshSceneList(d.eventData.scenes).then(done); return;
      case 'SceneItemCreated': addRemoteItem(d.eventData).then(done); return;
      case 'SceneItemRemoved': {
        const localId = obsIdMap.get(d.eventData.sceneItemId);
        if (localId) { obs.removeItem(obs.S.items[localId]?.sceneId, localId, true); obs.emit('items'); }
        break;
      }
      case 'SceneItemEnableStateChanged': {
        const localId = obsIdMap.get(d.eventData.sceneItemId);
        const it = obs.S.items[localId];
        if (it) { it.visible = d.eventData.sceneItemEnabled; obs.emit('items'); }
        break;
      }
      case 'SceneItemLockStateChanged': {
        const localId = obsIdMap.get(d.eventData.sceneItemId);
        const it = obs.S.items[localId];
        if (it) { it.locked = d.eventData.sceneItemLocked; obs.emit('items'); }
        break;
      }
      case 'SceneItemSelected': {
        const localId = obsIdMap.get(d.eventData.sceneItemId);
        if (localId) { obs.clearSelection(); obs.select(localId); }
        break;
      }
      case 'SceneItemTransformChanged': {
        const localId = obsIdMap.get(d.eventData.sceneItemId);
        const it = obs.S.items[localId];
        const t = d.eventData.sceneItemTransform || {};
        if (it) {
          it.x = Math.round(t.positionX ?? it.x); it.y = Math.round(t.positionY ?? it.y);
          it.rot = t.rotation ?? it.rot;
          const native = state.itemSourceSize.get(localId) || { w: it.w, h: it.h };
          it.w = Math.round(native.w * Math.abs(t.scaleX ?? 1)) || it.w;
          it.h = Math.round(native.h * Math.abs(t.scaleY ?? 1)) || it.h;
          it.crop = { l: t.cropLeft | 0, t: t.cropTop | 0, r: t.cropRight | 0, b: t.cropBottom | 0 };
          obs.emit('item-transform', localId);
        }
        break;
      }
      case 'InputActiveStateChanged': {
        const src = obs.S.sources.find(s => s.name === d.eventData.inputName);
        if (src) { src.active = !!d.eventData.videoActive ?? d.eventData.videoShowing; obs.emit('mixer', { id: src.id }); }
        break;
      }
      case 'InputCreated': case 'InputRemoved': case 'InputNameChanged':
        obs.emit('sources'); break;
      case 'InputMuteStateChanged': {
        const src = obs.S.sources.find(s => s.name === d.eventData.inputName);
        if (src) { src.muted = !!d.eventData.inputMuted; obs.emit('mixer', { id: src.id, muted: src.muted }); }
        break;
      }
      case 'InputVolumeChanged': {
        const src = obs.S.sources.find(s => s.name === d.eventData.inputName);
        if (src) { src.volumeDb = d.eventData.inputVolumeDb; obs.emit('mixer', { id: src.id }); }
        break;
      }
      // LOCAL-PATCH (station): feed live meter peaks into the engine; the
      // mixer animation reads them via getLevel() when attached.
      case 'InputVolumeMeters': {
        for (const i of d.eventData.inputs || []) {
          const lv = (i.inputLevelsMul && i.inputLevelsMul[0]) || [0];
          obs.setLiveLevel(i.inputName, lv[1] != null ? lv[1] : lv[0]);
        }
        break;
      }
      case 'InputSettingsChanged': {
        const src = obs.S.sources.find(s => s.name === d.eventData.inputName);
        if (src) { src.settings = { ...src.settings, ...d.eventData.inputSettings }; obs.emit('sources', { action: 'settings', id: src.id }); }
        break;
      }
      case 'StreamStateChanged': {
        obs.S.outputs.streaming = d.eventData.outputActive;
        if (d.eventData.outputActive) obs.S.outputs.streamStart = Date.now();
        obs.emit('outputs');
        break;
      }
      case 'RecordStateChanged': {
        obs.S.outputs.recording = d.eventData.outputActive;
        if (d.eventData.outputActive) obs.S.outputs.recStart = Date.now();
        obs.S.outputs.paused = d.eventData.outputPaused || false;
        obs.emit('outputs');
        break;
      }
      case 'ReplayBufferStateChanged':
        obs.S.outputs.replay = d.eventData.outputActive; obs.emit('outputs'); break;
      case 'VirtualcamStateChanged':
        obs.S.outputs.vcam = d.eventData.outputActive; obs.emit('outputs'); break;
      case 'StudioModeStateChanged': {
        obs.S.studioMode = !!d.eventData.studioModeEnabled;
        obs.emit('studio', obs.S.studioMode);
        break;
      }
      case 'CurrentSceneTransitionChanged': {
        obs.S.transition = d.eventData.transitionName || obs.S.transition;
        obs.emit('transition');
        break;
      }
      case 'CurrentSceneTransitionDurationChanged':
        obs.S.transitionDur = d.eventData.transitionDuration; obs.emit('transition'); break;
      case 'ExitStarted':
        obs.log('warn', 'OBS is exiting — connection will drop');
        break;
      default:
        obs.log('info', `WS event: ${d.eventType}`);
    }
  } catch (e) {
    obs.log('warn', `event ${d.eventType}: ${e.message}`);
  }
  done();
}

async function refreshSceneList(scenes) {
  const localScenes = [];
  for (const sc of scenes) {
    let local = obs.sceneByName(sc.sceneName);
    if (!local) { local = { id: `scene-${sc.sceneName}`, name: sc.sceneName, items: [] }; obs.S.scenes.push(local); }
    localScenes.push(local);
  }
  obs.S.scenes = localScenes;
  obs.emit('scenes');
}

async function addRemoteItem(d) {
  const scene = obs.sceneByName(d.sceneName);
  const src = obs.S.sources.find(s => s.name === d.sourceName);
  if (!scene || !src) return;
  const localId = `item-${d.sceneItemId}`;
  const t = d.sceneItemTransform || {};
  obs.S.items[localId] = {
    id: localId, sceneId: scene.id, sourceId: src.id,
    x: Math.round(t.positionX ?? 0), y: Math.round(t.positionY ?? 0),
    w: 960, h: 540, rot: t.rotation || 0,
    crop: { l: 0, t: 0, r: 0, b: 0 },
    visible: d.sceneItemEnabled !== false, locked: !!d.sceneItemLocked,
    boundsType: 'none', align: 5, filters: [], sel: false,
  };
  scene.items.push(localId);
  itemIdMap.set(localId, d.sceneItemId);
  obsIdMap.set(d.sceneItemId, localId);
  obs.emit('items');
  obs.emit('mixer-structure');
}

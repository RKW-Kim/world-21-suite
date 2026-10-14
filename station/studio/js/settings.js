/* ============================================================
   OBS Studio — Web Replication · Settings Dialog
   General · Stream · Output · Audio · Video · Hotkeys ·
   Accessibility · Advanced — applies live, persisted.
   ============================================================ */
import { h, $, fmtTime } from './util.js';
import { I } from './icons.js';
import { obs } from './engine.js';
import { openDialog } from './ui.js';

const THEMES = ['System Theme', 'Dark', 'Light', 'Grey', 'Rachni'];
const RESOLUTIONS = ['1920x1080', '2560x1440', '1366x768', '1280x720', '1600x900', '3840x2160', '2560x1080', '1920x1200'];
const SERVICES = ['Twitch', 'YouTube - RTMPS', 'Kick', 'Facebook Live', 'Restream.io', 'Trovo', 'Custom...'];

let dlg = null;

export function openSettings(page = 'General') {
  if (dlg) { dlg.close(); }
  const S = obs.settings;

  const pages = {};
  const nav = h('div', { class: 'settings-nav' });
  const pagesWrap = h('div', { class: 'settings-pages' });

  const body = h('div', { style: { display: 'flex', flex: 1, minHeight: 0 } }, nav, pagesWrap);

  dlg = openDialog({
    title: 'Settings', w: 920, h: 640, resizable: true,
    content: body,
    buttons: [
      { label: 'OK', def: true, action: () => { obs.persist(); dlg.close(); } },
      { label: 'Cancel', action: () => dlg.close() },
      { label: 'Apply', action: () => { obs.persist(); } },
    ],
  });
  dlg.el.classList.add('settings-win');

  function page(id, icon, label, build) {
    const pane = h('div', { class: 'settings-page', style: { display: 'none' } });
    build(pane);
    pages[id] = pane;
    pagesWrap.append(pane);
    const item = h('div', {
      class: 'sn-item', dataset: { page: id },
      onclick: () => show(id),
    }, h('span', { html: I(icon) }), h('span', { text: label }));
    nav.append(item);
  }

  function show(id) {
    for (const [k, pane] of Object.entries(pages)) pane.style.display = k === id ? '' : 'none';
    nav.querySelectorAll('.sn-item').forEach(el => el.classList.toggle('active', el.dataset.page === id));
  }

  /* ---------------- helpers ---------------- */
  const row = (label, ctrl, hint) => {
    const r = h('div', { class: 'srow' });
    if (label) r.append(h('label', { text: label }));
    r.append(ctrl);
    if (hint) r.append(h('span', { class: 'hint', text: hint, style: { margin: '0' } }));
    return r;
  };
  const check = (label, get, set) => {
    const input = h('input', { type: 'checkbox' });
    input.checked = !!get();
    input.addEventListener('change', () => { set(input.checked); obs.persist(); });
    return h('label', { class: 'qcheck' }, input, h('span', { class: 'box' }), h('span', { text: label }));
  };
  const combo = (options, get, set, w) => {
    const sel = h('select', { class: 'qcombo' });
    if (w) sel.style.width = w;
    for (const o of options) sel.append(h('option', { value: o, text: o, selected: o === get() ? '' : null }));
    sel.addEventListener('change', () => { set(sel.value); obs.persist(); });
    return sel;
  };
  const num = (get, set, min, max, step = 1, w = '90px') => {
    const inp = h('input', { class: 'qinput', type: 'number', min, max, step, value: get() });
    inp.style.width = w;
    inp.addEventListener('change', () => { set(parseFloat(inp.value) || 0); obs.persist(); });
    return inp;
  };
  const text = (get, set, w = '220px', placeholder) => {
    const inp = h('input', { class: 'qinput', value: get(), placeholder: placeholder || '' });
    inp.style.width = w;
    inp.addEventListener('change', () => { set(inp.value); obs.persist(); });
    return inp;
  };
  const sect = (title) => h('h3', { class: 'section', text: title });
  const fieldset = (title, ...kids) => h('fieldset', {}, h('legend', { text: title }), ...kids);

  /* ================= General ================= */
  page('General', 'gear', 'General', (p) => {
    p.append(
      fieldset('General',
        row('Language', combo(['English', 'Deutsch', 'Français', 'Español', '日本語', '简体中文'], () => S.general.language, v => S.general.language = v)),
        row('Theme', combo(THEMES, () => S.general.theme, v => { S.general.theme = v; obs.setTheme(v === 'System Theme' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'Light' : 'Dark') : v); })),
      ),
      fieldset('Projectors',
        check('Save projectors on exit', () => S.general.saveProjectors, v => S.general.saveProjectors = v),
      ),
      fieldset('System Tray',
        check('Enable', () => S.general.trayEnabled, v => S.general.trayEnabled = v),
        check('Show (web: keeps tab running in background)', () => S.general.trayMinimize, v => S.general.trayMinimize = v),
        check('Always show', () => S.general.trayAlways, v => S.general.trayAlways = v),
      ),
      fieldset('Preview',
        check('Focus preview on click', () => S.general.previewFocusOnClick, v => S.general.previewFocusOnClick = v),
        check('Draw safe areas on preview', () => S.general.previewDrawSafeAreas, v => S.general.previewDrawSafeAreas = v),
        check('Hover sources in preview panel', () => S.general.previewHoverSources, v => S.general.previewHoverSources = v),
      ),
      fieldset('Source Align Snapping',
        check('Enable', () => S.general.snapEnabled, v => S.general.snapEnabled = v),
        check('Snap to screen edges', () => S.general.snapScreen, v => S.general.snapScreen = v),
        check('Snap to center', () => S.general.snapCenter, v => S.general.snapCenter = v),
        row('Snap Sensitivity', num(() => S.general.snapDistance, v => S.general.snapDistance = v, 1, 100)),
      ),
      fieldset('Studio Mode',
        check('Return preview to the previous scene when leaving Studio Mode', () => S.general.studioReturnPreview, v => S.general.studioReturnPreview = v),
        check('Double-click scene to assign to preview', () => S.general.studioSceneSel, v => S.general.studioSceneSel = v),
      ),
      fieldset('Source Properties',
        row('Select when the properties window opens', combo(['Always open', 'Never open'], () => S.general.openProps, v => S.general.openProps = v)),
      ),
      fieldset('Updates',
        check('Automatically check for updates on startup', () => S.general.autoCheckUpdates, v => S.general.autoCheckUpdates = v),
        check('Automatically check for beta versions', () => S.general.autoCheckBeta, v => S.general.autoCheckBeta = v),
      ),
      sect('Notifications'),
      check('Open the stats dialog when starting streaming', () => S.general.openStatsOnLive, v => S.general.openStatsOnLive = v),
      check('Show confirmation dialog when stopping streams', () => S.general.confirmOnStop, v => S.general.confirmOnStop = v),
      check('Hide OBS window from screen capture', () => S.general.hideFromCapture, v => S.general.hideFromCapture = v),
    );
  });

  /* ================= Stream ================= */
  page('Stream', 'broadcast', 'Stream', (p) => {
    const st = S.stream;
    p.append(
      fieldset('Stream Information',
        row('Service', combo(SERVICES, () => st.service, v => { st.service = v; })),
        row('Server', combo(['Auto (Recommended)', 'Custom...'], () => st.server, v => st.server = v)),
        row('Stream Key', text(() => st.key, v => st.key = v, '240px', 'rtmp://…')),
      ),
      h('div', { class: 'row', style: { marginTop: '10px' } },
        h('button', { class: 'qpush', text: 'Get Stream Key', onclick: () => import('./ui.js').then(m => m.toast('Opens the service dashboard in real OBS (web replica)')) })),
      fieldset('Connection',
        check('Enable bandwidth test mode', () => st.bandwidthTest, v => st.bandwidthTest = v),
        check('Use authentication', () => st.auth, v => st.auth = v),
      ),
      h('div', { class: 'hint', style: { marginTop: '12px' } },
        'Streaming from the web replica uses the simulated output engine. Connect a real OBS via Tools → WebSocket Server Settings to drive actual streams.'),
    );
  });

  /* ================= Output ================= */
  page('Output', 'video', 'Output', (p) => {
    const O = S.output;
    const content = h('div');
    p.append(
      row('Output Mode', combo(['Simple', 'Advanced'], () => O.mode, v => { O.mode = v; renderOut(); })),
      content,
    );

    function renderOut() {
      content.innerHTML = '';
      if (O.mode === 'Simple') {
        const s = O.simple;
        content.append(
          fieldset('Streaming',
            row('Video Bitrate', num(() => s.streamVBitrate, v => s.streamVBitrate = v, 200, 40000, 50)),
            row('Encoder', combo(['Software (x264)', 'Hardware (NVENC)', 'Hardware (QSV)', 'Hardware (AMF)'], () => s.streamVEncoder, v => s.streamVEncoder = v)),
            row('Audio Bitrate', num(() => s.streamABitrate, v => s.streamABitrate = v, 32, 320, 32)),
            check('Enforce streaming service bitrate limits', () => s.enforceBitrate, v => s.enforceBitrate = v),
          ),
          fieldset('Recording',
            row('Recording Path', text(() => s.recPath, v => s.recPath = v, '280px')),
            row('Recording Format', combo(['mkv', 'mp4', 'mov', 'flv', 'ts'], () => s.recFormat, v => s.recFormat = v)),
            row('Video Encoder', combo(['Software (x264)', 'Hardware (NVENC)'], () => s.recVEncoder, v => s.recVEncoder = v)),
            row('Audio Encoder', combo(['AAC', 'Opus'], () => s.recAEncoder, v => s.recAEncoder = v)),
            check('Enable Replay Buffer', () => s.replay, v => s.replay = v),
            row('Maximum Replay Time', num(() => s.replayMaxTime, v => s.replayMaxTime = v, 5, 600)),
          ),
          fieldset('Audio — Track Bitrates',
            ...s.tracks.map((t, i) => row(`Track ${i + 1}`, num(() => s.tracks[i], v => s.tracks[i] = v, 32, 320, 32))),
          ),
          fieldset('Advanced Encoder Settings',
            check('Enable Advanced Encoder Settings', () => s.advEnc, v => s.advEnc = v),
            row('Custom Encoder Options', text(() => s.customEnc, v => s.customEnc = v, '260px')),
          ),
        );
      } else {
        const a = O.adv;
        content.append(
          h('h3', { class: 'section', text: 'Streaming' }),
          row('Encoder', combo(['Software (x264)', 'Hardware (NVENC, H.264)', 'Hardware (QSV, H.264)'], () => a.stream.encoder, v => a.stream.encoder = v)),
          check('Enforce streaming service encoder settings', () => a.stream.enforce, v => a.stream.enforce = v),
          check('Rescale Output', () => a.stream.rescale, v => a.stream.rescale = v),
          row('Rate Control', combo(['CBR', 'VBR', 'CRF', 'ABR'], () => a.stream.rateControl, v => a.stream.rateControl = v)),
          row('Bitrate', num(() => a.stream.bitrate, v => a.stream.bitrate = v, 200, 40000, 50)),
          row('Keyframe Interval', num(() => a.stream.keyframe, v => a.stream.keyframe = v, 0, 10, 1)),
          row('CPU Usage Preset', combo(['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow'], () => a.stream.preset, v => a.stream.preset = v)),
          row('Tune', combo(['default', 'film', 'animation', 'zerolatency'], () => a.stream.tuning, v => a.stream.tuning = v)),
          row('Profile', combo(['high', 'main', 'baseline'], () => a.stream.profile, v => a.stream.profile = v)),
          row('Look-ahead', combo(['Disabled', 'Enabled'], () => a.stream.lookahead ? 'Enabled' : 'Disabled', v => a.stream.lookahead = v === 'Enabled')),
          row('Psycho Visual Tuning', combo(['Enabled', 'Disabled'], () => a.stream.psycho ? 'Enabled' : 'Disabled', v => a.stream.psycho = v === 'Enabled')),
          h('h3', { class: 'section', text: 'Recording' }),
          row('Type', combo(['Standard', 'Custom Output (FFmpeg)'], () => a.rec.type, v => a.rec.type = v)),
          row('Recording Path', text(() => a.rec.path, v => a.rec.path = v, '280px')),
          row('Recording Format', combo(['mkv', 'mp4', 'mov', 'flv', 'ts'], () => a.rec.format, v => a.rec.format = v)),
          row('Video Encoder', combo(['Software (x264)', 'Hardware (NVENC)'], () => a.rec.encoder, v => a.rec.encoder = v)),
          row('Rate Control', combo(['CRF', 'CBR', 'VBR'], () => a.rec.rateControl, v => a.rec.rateControl = v)),
          row('CRF Value', num(() => a.rec.crf, v => a.rec.crf = v, 0, 51)),
          h('h3', { class: 'section', text: 'Audio — Track Bitrates' }),
          ...a.audio.map((t, i) => row(`Track ${i + 1}`, num(() => a.audio[i], v => a.audio[i] = v, 32, 320, 32))),
          h('h3', { class: 'section', text: 'Replay Buffer' }),
          check('Enable Replay Buffer', () => a.replay.enabled, v => a.replay.enabled = v),
          row('Maximum Replay Time', num(() => a.replay.maxTime, v => a.replay.maxTime = v, 5, 600)),
        );
      }
    }
    renderOut();
  });

  /* ================= Audio ================= */
  page('Audio', 'audio', 'Audio', (p) => {
    const A = S.audio;
    p.append(
      fieldset('General',
        row('Sample Rate', combo(['48000 Hz', '44100 Hz'], () => `${A.sampleRate} Hz`, v => A.sampleRate = parseInt(v))),
        row('Channels', combo(['Stereo', 'Mono'], () => A.channels, v => A.channels = v)),
      ),
      fieldset('Global Audio Devices',
        row('Desktop Audio', combo(['Default', 'Disabled'], () => A.desktopDevice, v => A.desktopDevice = v)),
        row('Mic/Auxiliary Audio', combo(['Default', 'Disabled'], () => A.micDevice, v => A.micDevice = v)),
      ),
      fieldset('Hotkeys',
        check('Push-to-talk', () => A.ptt, v => A.ptt = v),
        row('Push-to-talk delay', num(() => A.pttDelay, v => A.pttDelay = v, 0, 20000)),
        check('Push-to-mute', () => A.ptm, v => A.ptm = v),
        row('Push-to-mute delay', num(() => A.ptmDelay, v => A.ptmDelay = v, 0, 20000)),
      ),
      fieldset('Monitoring Device',
        row('Device', combo(['Default', 'Disabled'], () => A.monitorDevice, v => A.monitorDevice = v)),
      ),
      fieldset('Meter Style',
        row('Meter Decay', combo(['Medium (Fast)', 'Medium (Slow)', 'Slow', 'Fast'], () => A.meterDecay, v => A.meterDecay = v)),
        row('Peak Meter Type', combo(['Sample Peak', 'True Peak'], () => A.peakType, v => A.peakType = v)),
      ),
    );
  });

  /* ================= Video ================= */
  page('Video', 'monitor', 'Video', (p) => {
    const V = S.video;
    p.append(
      fieldset('Base (Canvas) Resolution',
        row('', combo(RESOLUTIONS, () => V.baseRes, v => { V.baseRes = v; const p = v.split('x'); obs.canvas = { w: parseInt(p[0]) || 1920, h: parseInt(p[1]) || 1080 }; obs.emit('outputs-tick'); })),
        h('div', { class: 'hint', text: 'The video source is rendered at this resolution before being scaled to the output.' }),
      ),
      fieldset('Output (Scaled) Resolution',
        row('', combo(RESOLUTIONS, () => V.outRes, v => V.outRes = v)),
        row('Downscale Filter', combo(['Bilinear (Fastest, but blurry if scaling)', 'Area (Weighted area average)', 'Bicubic (Sharpened scaling, 16 samples)', 'Lanczos (Sharpened scaling, 36 samples)'], () => V.downscale, v => V.downscale = v)),
      ),
      fieldset('FPS',
        row('', combo(['Common FPS Values', 'Integer FPS Value', 'Fractional FPS Value'], () => V.fpsType, v => V.fpsType = v)),
        row('Common FPS Values', combo(['10', '20', '24 NTSC', '29.97 NTSC', '30', '48', '50 PAL', '59.94 NTSC', '60'], () => String(V.fps), v => V.fps = parseFloat(v) || 60)),
      ),
      h('div', { class: 'hint', style: { marginTop: '12px' } },
        'Changing video settings restarts the compositor in real OBS. The web replica applies them instantly.'),
    );
  });

  /* ================= Hotkeys ================= */
  page('Hotkeys', 'keyboard', 'Hotkeys', (p) => {
    const list = h('div', { style: { maxHeight: '460px', overflowY: 'auto' } });
    p.append(h('div', { class: 'hint', style: { marginBottom: '10px' } }, 'Click a binding, then press the key combination. These hotkeys work while the OBS replica tab is focused.'), list);
    const H = S.hotkeys;

    function hotkeyWidget(action, idx) {
      const label = h('span', { text: H[action][idx] || 'Press to bind' });
      const el = h('div', {
        class: 'hotkey-widget', tabindex: 0,
        onclick: () => {
          el.classList.add('capturing');
          label.textContent = 'Press keys…';
          const handler = (ev) => {
            ev.preventDefault(); ev.stopPropagation();
            if (ev.key === 'Escape') { end(); return; }
            import('./util.js').then(u => {
              const ks = u.keyStr(ev);
              H[action][idx] = ks;
              label.textContent = ks;
              obs.persist();
              end();
            });
          };
          addEventListener('keydown', handler, true);
          function end() { removeEventListener('keydown', handler, true); el.classList.remove('capturing'); label.textContent = H[action][idx] || 'Press to bind'; }
        },
      }, label);
      const clear = h('span', {
        class: 'hk-clear', html: I('close'), 'data-tip': 'Clear binding',
        onclick: (e) => { e.stopPropagation(); H[action][idx] = null; label.textContent = 'Press to bind'; obs.persist(); },
      });
      el.append(clear);
      return el;
    }

    function render() {
      list.innerHTML = '';
      for (const [action, binds] of Object.entries(H)) {
        const row = h('div', { class: 'hotkey-row' },
          h('div', { class: 'hk-name', text: action }),
          h('div', { class: 'hk-bind' },
            hotkeyWidget(action, 0),
            hotkeyWidget(action, 1),
          ));
        list.append(row);
      }
      // per-scene hotkeys
      for (const sc of obs.S.scenes) {
        H[`Scene: ${sc.name}`] = H[`Scene: ${sc.name}`] || [];
        list.append(h('div', { class: 'hotkey-row' },
          h('div', { class: 'hk-name sub', text: `Scene: ${sc.name}` }),
          h('div', { class: 'hk-bind' }, hotkeyWidget(`Scene: ${sc.name}`, 0)),
        ));
      }
    }
    render();
  });

  /* ================= Accessibility ================= */
  page('Accessibility', 'person', 'Accessibility', (p) => {
    p.append(
      fieldset('Interface Scaling Overrides',
        row('List selectors', num(() => 2, () => {}, 1, 5)),
        row('Spinbox selectors', num(() => 2, () => {}, 1, 5)),
        row('Scrollbar selectors', num(() => 3, () => {}, 1, 5)),
        row('Checkbox selectors', num(() => 2, () => {}, 1, 5)),
        row('Group selectors', num(() => 2, () => {}, 1, 5)),
      ),
      h('div', { class: 'hint' }, 'Overrides control which interface element is targeted for accessibility navigation in real OBS.'),
    );
  });

  /* ================= Advanced ================= */
  page('Advanced', 'sliders', 'Advanced', (p) => {
    const A = S.advanced;
    p.append(
      fieldset('General',
        row('Process Priority', combo(['High', 'Above Normal', 'Normal', 'Below Normal', 'Idle'], () => A.processPriority, v => A.processPriority = v)),
        row('Renderer', combo(['Direct3D 11', 'OpenGL'], () => A.renderer, v => A.renderer = v)),
      ),
      fieldset('Video',
        row('Color Format', combo(['NV12', 'I420', 'I444', 'P010', 'RGB'], () => A.colorFormat, v => A.colorFormat = v)),
        row('Color Space', combo(['Rec. 709', 'Rec. 601', 'Rec. 2100 (PQ)', 'Rec. 2100 (HLG)'], () => A.colorSpace, v => A.colorSpace = v)),
        row('Color Range', combo(['Partial', 'Full'], () => A.colorRange, v => A.colorRange = v)),
        row('SDR White Level', num(() => A.sdrWhite, v => A.sdrWhite = v, 80, 480)),
      ),
      fieldset('Stream Delay',
        check('Enable', () => A.streamDelay, v => A.streamDelay = v),
        row('Duration', num(() => A.streamDelaySec, v => A.streamDelaySec = v, 0, 3600), 'sec'),
        check('Preserve cut point when restarting the stream', () => A.preserveDelay, v => A.preserveDelay = v),
      ),
      fieldset('Automatically Reconnect',
        check('Enable', () => A.reconnect, v => A.reconnect = v),
        row('Retry delay', num(() => A.retryDelay, v => A.retryDelay = v, 1, 60), 's'),
        row('Maximum retries', num(() => A.maxRetries, v => A.maxRetries = v, 1, 10000)),
      ),
      fieldset('Sources',
        check('Enable browser source hardware acceleration', () => A.browserAccel, v => A.browserAccel = v),
        check('Rewind media when it loses focus', () => A.mediaRewind, v => A.mediaRewind = v),
        check('Automatically pause media when it is not visible', () => A.mediaPause, v => A.mediaPause = v),
      ),
      fieldset('Recording',
        row('Filename Formatting', text(() => S.output.filenameFmt, v => S.output.filenameFmt = v, '240px')),
        check('Overwrite if file exists', () => S.output.overwriteIfExists, v => S.output.overwriteIfExists = v),
        row('Automatically remux to', combo(['Never', 'mp4', 'mov', 'mkv'], () => A.autoRemux, v => A.autoRemux = v)),
      ),
    );
  });

  nav.dataset.ready = '1';
  show(pages[page] ? page : 'General');
  return dlg;
}

/* ============================================================
   OBS Studio — Web Replication · Tools & Misc Dialogs
   Auto-Configuration Wizard · Scripts · Plugins ·
   WebSocket Server Settings · Stats · About · Log Viewer ·
   Remux · Multiview · Projector · Custom Browser Docks
   ============================================================ */
import { h, $, fmtTime } from './util.js';
import { I, ObsLogo } from './icons.js';
import { obs } from './engine.js';
import { openDialog, openMenu, msgBox, promptDlg, toast } from './ui.js';

/* ================= Auto-Configuration Wizard ================= */
export function openWizard() {
  let step = 0;
  const bodyEl = h('div', { class: 'wizard-body' });
  const d = openDialog({
    title: 'Auto-Configuration Wizard', w: 560, resizable: false,
    content: bodyEl,
    buttons: [
      { label: 'Back', action: () => { if (step > 0) { step--; render(); } } },
      { label: 'Next', def: true, action: () => { if (step < 2) { step++; render(); } else { apply(); d.close(); } } },
      { label: 'Cancel', action: () => d.close() },
    ],
  });

  const usage = { streaming: true, recording: false };
  function render() {
    const btns = d.footer.querySelectorAll('.qpush');
    btns[0].style.visibility = step > 0 ? 'visible' : 'hidden';
    btns[1].textContent = step === 2 ? 'Apply Settings' : 'Next';
    bodyEl.innerHTML = '';
    if (step === 0) {
      bodyEl.append(
        h('div', { class: 'wizard-title', text: 'Usage Information' }),
        h('div', { class: 'hint', text: 'This wizard will automatically configure your video settings based on your available hardware and connection.' }),
        h('label', { class: 'qradio', style: { marginTop: '10px' } },
          radio('usage', usage.streaming === true), h('span', { class: 'dot' }), h('span', { text: 'Optimize for streaming, recording is secondary' })),
        h('label', { class: 'qradio' },
          radio('usage', usage.streaming === false), h('span', { class: 'dot' }), h('span', { text: 'Optimize just for recording, I will not be streaming' })),
      );
    } else if (step === 1) {
      bodyEl.append(
        h('div', { class: 'wizard-title', text: 'Video Settings' }),
        h('div', { class: 'srow' }, h('label', { text: 'Base (Canvas) Resolution' }), combo(['1920x1080', '2560x1440'], '1920x1080')),
        h('div', { class: 'srow' }, h('label', { text: 'Output (Scaled) Resolution' }), combo(['1280x720', '1920x1080'], '1280x720')),
        h('div', { class: 'srow' }, h('label', { text: 'FPS' }), combo(['30', '60'], '60')),
      );
    } else {
      bodyEl.append(
        h('div', { class: 'wizard-title', text: 'Final Results' }),
        h('div', { class: 'hint', text: 'The estimated settings below balance quality with performance. In real OBS this step runs a bandwidth test against your connection.' }),
        h('div', { class: 'wsconnect-info', html:
          `<b>Encoder:</b> Software (x264)<br><b>Stream bitrate:</b> 2500 kbps<br><b>Output resolution:</b> 1280x720 @ 30/60 fps` }),
      );
    }
  }
  function radio(name, on) {
    const i = h('input', { type: 'radio', name });
    if (on) i.setAttribute('checked', '');
    i.addEventListener('change', () => { usage.streaming = name === 'usage' ? true : false; });
    return i;
  }
  function combo(opts, def) {
    const s = h('select', { class: 'qcombo' });
    for (const o of opts) s.append(h('option', { value: o, text: o, selected: o === def ? '' : null }));
    return s;
  }
  function apply() {
    obs.S.video.outRes = '1280x720';
    obs.persist();
    toast('Auto-configuration applied');
  }
  render();
}

/* ================= Scripts window ================= */
export function openScripts() {
  const list = h('div', { class: 'qlist' });
  const right = h('div', { class: 'scripts-right' });
  const d = openDialog({
    title: 'Scripts', w: 780, h: 520, resizable: true, winClass: 'scripts-win',
    content: h('div', { style: { display: 'flex', flex: 1, minHeight: 0 } },
      h('div', { class: 'scripts-left' },
        h('div', { class: 'dock-toolbar' },
          ...[['plus', 'Add Scripts (Python/Lua)'], ['minus', 'Remove Scripts'], ['refresh', 'Reload Scripts']].map(([ic, tip]) =>
            h('div', { class: 'dock-btn', html: I(ic), 'data-tip': tip, onclick: () => {
              if (ic === 'plus') addScript(); else toast(ic === 'minus' ? 'Select a script to remove' : 'Scripts reloaded');
            } }))),
        list),
      right),
    buttons: [
      { label: 'Python Settings', action: () => toast('Python 3.6+ install path (OS-native in real OBS)') },
      { label: 'Close', def: true, action: () => d.close() },
    ],
  });

  const scripts = [
    { name: 'clock.lua', loaded: true },
    { name: 'countdown.py', loaded: true },
  ];
  function render() {
    list.innerHTML = '';
    for (const sc of scripts) {
      list.append(h('div', {
        class: 'qlist-row',
        onclick: () => showScript(sc),
        oncontextmenu: (e) => openMenu([{ label: 'Remove', action: () => { scripts.splice(scripts.indexOf(sc), 1); render(); } }], e.clientX, e.clientY),
      }, h('span', { class: 'row-icon', html: I('script') }), h('span', { class: 'row-label', text: sc.name })));
    }
  }
  function showScript(sc) {
    right.innerHTML = '';
    right.append(
      h('div', { class: 'script-desc', text: `Script: ${sc.name}\nLoaded: ${sc.loaded ? 'Yes' : 'No'}` }),
      h('div', { class: 'hint', text: 'Script properties appear here in real OBS (defined by the script author).' }));
  }
  function addScript() {
    promptDlg('Add Script', 'Script path', 'my-script.lua', (v) => {
      scripts.push({ name: v, loaded: true });
      render();
      obs.log('info', `Loaded script '${v}'`);
    });
  }
  render();
}

/* ================= Plugins manager ================= */
const PLUGINS = [
  { name: 'obs-websocket', ver: '5.5.5', desc: 'Remote-control OBS Studio via WebSocket (RPC protocol v5). Bundled with OBS 28+.', bundled: true },
  { name: 'obs-ffmpeg', ver: 'bundled', desc: 'FFmpeg output — recording, remuxing, media sources and encoders.', bundled: true },
  { name: 'obs-x264', ver: 'bundled', desc: 'Software x264 video encoder.', bundled: true },
  { name: 'obs-nvenc', ver: 'bundled', desc: 'NVIDIA hardware encoder (NVENC).', bundled: true },
  { name: 'obs-qsv11', ver: 'bundled', desc: 'Intel QuickSync video encoder.', bundled: true },
  { name: 'obs-text', ver: 'bundled', desc: 'FreeType2 text source rendering.', bundled: true },
  { name: 'frontend-tools', ver: 'bundled', desc: 'Auto-scene switcher, capture board, output timers, scripting.', bundled: true },
  { name: 'rtmp-services', ver: 'bundled', desc: 'Streaming services list (Twitch, YouTube, Kick, …).', bundled: true },
  { name: 'decklink-capturer', ver: 'bundled', desc: 'Blackmagic DeckLink capture source.', bundled: true },
  { name: 'vlc-video', ver: 'bundled', desc: 'VLC playlist video source.', bundled: true },
  { name: 'win-capture', ver: 'bundled', desc: 'Game/Window/Display capture plugins for Windows.', bundled: true },
  { name: 'win-dshow', ver: 'bundled', desc: 'DirectShow audio/video device capture.', bundled: true },
];

export function openPlugins() {
  const list = h('div', { class: 'qlist', style: { flex: 1 } });
  const right = h('div', { class: 'scripts-right' });
  const d = openDialog({
    title: 'Plugins', w: 780, h: 520, resizable: true, winClass: 'scripts-win',
    content: h('div', { style: { display: 'flex', flex: 1, minHeight: 0 } }, list, right),
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });
  function render() {
    list.innerHTML = '';
    for (const p of PLUGINS) {
      list.append(h('div', {
        class: 'qlist-row',
        onclick: () => show(p),
      },
        h('span', { class: 'row-icon', html: I('plug') }),
        h('span', { class: 'row-label', text: p.name })));
    }
  }
  function show(p) {
    right.innerHTML = '';
    right.append(
      h('div', { class: 'filters-name' }, h('span', { class: 'fname', text: p.name }), h('span', { class: 'ws-badge on', html: `<span class="dot"></span>Loaded` })),
      h('div', { class: 'hint', style: { margin: '10px 0' }, text: `Version: ${p.ver}` }),
      h('div', { class: 'script-desc', text: p.desc }),
      h('div', { class: 'hint', text: 'Third-party plugins are loaded from the OBS plugin directory in the desktop application. The web replica ships the bundled set above with obs-websocket protocol v5 fully functional.' }));
  }
  render();
}

/* ================= WebSocket Server Settings ================= */
export function openWsSettings(wsApi) {
  const cfg = wsApi?.config || { enabled: false, port: 4455, auth: true, password: '' };
  const portInp = h('input', { class: 'qinput', type: 'number', value: cfg.port, style: { width: '110px' } });
  const pwdInp = h('input', { class: 'qinput', type: 'password', value: cfg.password || '', style: { width: '180px' } });
  const authChk = h('input', { type: 'checkbox' });
  authChk.checked = cfg.auth !== false;
  const enableChk = h('input', { type: 'checkbox' });
  enableChk.checked = !!cfg.enabled;

  const info = h('div', { class: 'wsconnect-info', html: '' });
  const clientsBox = h('div', { class: 'wsclients' }, h('div', { class: 'row', text: 'No clients connected' }));

  const body = h('div', { style: { padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' } },
    h('label', { class: 'qcheck' }, enableChk, h('span', { class: 'box' }), h('span', { text: 'Enable WebSocket server' })),
    h('div', { class: 'form-grid' },
      h('label', { text: 'Server Port' }), portInp,
      h('label', { text: 'Enable Authentication' }), h('label', { class: 'qcheck' }, authChk, h('span', { class: 'box' })),
      h('label', { text: 'Password' }), pwdInp,
    ),
    h('div', { class: 'row' }, h('button', { class: 'qpush', text: 'Show Connect Info', onclick: () => {
      info.innerHTML = `<b>Server URL:</b> ws://localhost:${portInp.value}<br><b>Password:</b> ${authChk.checked ? '••••••••' : '(no auth)'}`;
    } })),
    info,
    h('h3', { style: { margin: '4px 0 0' }, text: 'Connected WebSocket Clients' }),
    clientsBox,
    h('div', { class: 'hint', html:
      'In the desktop app this dialog configures OBS\'s <i>own</i> server. In the web replica, this same dialog drives the <b>client connector</b> below — letting this page attach to a real OBS running obs-websocket v5.' }),
    h('div', { class: 'row', style: { gap: '8px' } },
      h('button', { class: 'qpush default', text: 'Connect to OBS…', onclick: () => { d.close(); wsApi.openConnect(); } }),
      wsApi && wsApi.status === 'connected' ? h('button', { class: 'qpush danger', text: 'Disconnect', onclick: () => { wsApi.disconnect(false, true); d.close(); } }) : null,
    ),
  );

  const d = openDialog({
    title: 'WebSocket Server Settings', w: 520, resizable: false,
    content: body,
    buttons: [
      { label: 'OK', def: true, action: () => { cfg.port = parseInt(portInp.value) || 4455; cfg.auth = authChk.checked; cfg.password = pwdInp.value; cfg.enabled = enableChk.checked; obs.persist(); d.close(); } },
      { label: 'Cancel', action: () => d.close() },
    ],
  });
  refreshClients();
  function refreshClients() {
    if (wsApi?.status === 'connected') {
      clientsBox.innerHTML = '';
      clientsBox.append(h('div', { class: 'row' }, h('span', { text: 'This page (browser client) — connected' })));
    }
  }
}

/* ================= Stats dialog ================= */
export function openStats() {
  const grid = h('div', { class: 'stats-grid', style: { padding: '14px 18px' } });
  const d = openDialog({
    title: 'Stats', w: 460, resizable: true,
    content: grid,
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });
  function render() {
    const st = obs._sim, o = obs.S.outputs;
    grid.innerHTML = '';
    const add = (k, v) => grid.append(h('div', { class: 'k', text: k }), h('div', { class: 'v', text: v }));
    add('Live time', o.streaming ? fmtTime(o.streamTime) : 'Inactive');
    add('Data rate', o.streaming ? `${Math.round(obs._sim.kbps || 0)} kb/s` : '-');
    grid.append(h('div', { class: 'stats-sep' }));
    add('Recording time', o.recording ? fmtTime(o.recTime) : 'Inactive');
    grid.append(h('div', { class: 'stats-sep' }));
    add('Total frames rendered', `${Math.round((st.fps || 60) * (o.recTime || 0) + 1200)}`);
    add('Frames rendered late', `${st.skipped || 0} (0.0%)`);
    add('Frames rendered missed', `0 (0.0%)`);
    grid.append(h('div', { class: 'stats-sep' }));
    add('CPU usage', `${(st.cpu || 0).toFixed(1)}%`);
    add('Memory usage', `${Math.round(st.mem || 0)} MB`);
    add('Render time per frame', `${(st.renderMs || 0).toFixed(1)} ms`);
    add('Average time to render frame (last 2000 frames)', `${(st.renderMs || 0).toFixed(1)} ms`);
    add('FPS', `${(st.fps || 60).toFixed(1)}`);
    grid.append(h('div', { class: 'stats-sep' }));
    add('Output resolution', obs.settings.video.outRes);
    add('Base resolution', obs.settings.video.baseRes);
  }
  render();
  const iv = setInterval(() => { if (!document.body.contains(grid)) { clearInterval(iv); return; } render(); }, 1000);
}

/* ================= About ================= */
export function openAbout() {
  const d = openDialog({
    title: 'About', w: 560, resizable: false,
    content: h('div', { class: 'about-body' },
      h('div', { class: 'about-logo', html: ObsLogo(96) }),
      h('div', { class: 'about-title', text: 'OBS Studio' }),
      h('div', { class: 'about-ver', text: 'Version: 30.2.3 (Web Replication) — 64-bit' }),
      h('div', { class: 'about-text', text: 'Free and open source software for video capturing, recording, and live streaming. This build is a 1:1 web replication of the OBS Studio interface with a simulated core and obs-websocket v5 client.' }),
      h('div', { class: 'about-text hint', text: 'Copyright (C) 2012+ Hugh Bailey (OBS Studio contributors)\nThis program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License v2.0.' }),
      h('div', { class: 'about-links' },
        h('button', { class: 'qpush', text: 'Donate', onclick: () => toast('https://obsproject.com/donate') }),
        h('button', { class: 'qpush', text: 'Contribute', onclick: () => toast('https://github.com/obsproject/obs-studio') }),
        h('button', { class: 'qpush', text: 'Troubleshooter', onclick: () => toast('https://obsproject.com/help') })),
    ),
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });
}

/* ================= Log Viewer ================= */
export function openLogViewer() {
  const view = h('div', { class: 'logview' });
  const d = openDialog({
    title: 'Log Viewer', w: 760, h: 480, resizable: true,
    content: view,
    buttons: [{ label: 'Clear', action: () => { view.innerHTML = ''; } }, { label: 'Close', def: true, action: () => d.close() }],
  });
  const addLine = ({ level, msg, t }) => {
    const time = new Date(t || Date.now()).toLocaleTimeString();
    view.append(h('div', { class: `lg-${level}` , text: `${time} [${level}] ${msg}` }));
    view.scrollTop = view.scrollHeight;
  };
  obs.log('info', 'Log viewer attached');
  obs.on('log', addLine);
  obs._sim.logs?.forEach(addLine);
  obs._logFeed = l => addLine(l);
}

/* ================= Remux Recordings ================= */
export function openRemux() {
  const mkRow = (label) => h('div', { class: 'remux-row' },
    h('label', { style: { width: '90px' }, text: label }),
    h('input', { class: 'qinput', style: { flex: 1 }, placeholder: 'No file selected', disabled: '' }),
    h('button', { class: 'qpush', text: '…', onclick: () => toast('File dialogs are OS-native (web replica)') }));
  const prog = h('div', { class: 'row', style: { marginTop: '10px' } },
    h('div', { style: { flex: 1, height: '8px', background: 'var(--input-bg)', border: '1px solid var(--input-border)', borderRadius: '4px', overflow: 'hidden' } },
      h('div', { id: 'remux-prog', style: { width: '0%', height: '100%', background: 'var(--accent)' } })),
    h('span', { id: 'remux-status', class: 'hint', text: 'Ready' }));
  const d = openDialog({
    title: 'Remux Recordings', w: 560, resizable: false,
    content: h('div', { style: { padding: '14px 16px' } },
      mkRow('OBS Recording'),
      mkRow('Target File'),
      prog),
    buttons: [
      { label: 'Remux', def: true, action: () => {
          const bar = d.body.querySelector('#remux-prog'), st = d.body.querySelector('#remux-status');
          st.textContent = 'Remuxing…';
          let p = 0;
          const iv = setInterval(() => {
            p += 12; bar.style.width = Math.min(100, p) + '%';
            if (p >= 100) { clearInterval(iv); st.textContent = 'Done'; obs.log('info', 'Remux finished'); }
          }, 160);
        } },
      { label: 'Close', action: () => d.close() },
    ],
  });
}

/* ================= Multiview ================= */
export function openMultiview(programId) {
  const grid = h('div', { class: 'multiview-grid' });
  const d = openDialog({
    title: 'Multiview (Windowed)', w: 720, resizable: false,
    content: h('div', { style: { padding: '12px' } }, grid),
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });
  function render() {
    grid.innerHTML = '';
    const prog = obs.program, prev = obs.preview;
    const mk = (sc, cls) => h('div', { class: 'multiview-cell ' + cls, text: sc ? sc.name : '' });
    grid.append(mk(prog, 'program main'), mk(prev, 'preview'));
    obs.S.scenes.filter(s => s.id !== prog.id && s.id !== prev.id).slice(0, 6).forEach(sc => grid.append(mk(sc, '')));
    while (grid.children.length < 9) grid.append(h('div', { class: 'multiview-cell' }));
  }
  render();
  obs.on('program', render);
  obs.on('preview', render);
  obs.on('scenes', render);
}

/* ================= Projector ================= */
export function openProjector(sceneId, name) {
  const c = h('canvas', { width: 640, height: 360, style: { width: '100%', background: '#000' } });
  const d = openDialog({
    title: `Windowed Projector (Scene) — ${name}`, w: 660, resizable: true,
    content: h('div', { style: { padding: '8px' } }, c),
    buttons: [{ label: 'Close', def: true, action: () => { clearInterval(iv); d.close(); } }],
  });
  const g = c.getContext('2d');
  const iv = setInterval(() => {
    g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
    const scene = sceneId ? obs.sceneById(sceneId) : obs.program;
    if (!scene) return;
    let i = 0;
    for (const it of obs.itemsOf(scene.id)) {
      if (!it.visible) continue;
      const src = obs.sourceById(it.sourceId); if (!src) continue;
      g.fillStyle = 'rgba(70,90,120,.9)';
      g.fillRect(it.x / 3, it.y / 3, it.w / 3, it.h / 3);
      g.strokeStyle = '#5a7ea6'; g.strokeRect(it.x / 3, it.y / 3, it.w / 3, it.h / 3);
      i++;
    }
  }, 200);
}

/* ================= Custom Browser Docks ================= */
export function openCustomDocks() {
  const urlInp = h('input', { class: 'qinput', style: { flex: 1 }, placeholder: 'https://example.com/panel' });
  const nameInp = h('input', { class: 'qinput', style: { width: '160px' }, placeholder: 'Dock name' });
  const list = h('div', { class: 'hint' });
  const d = openDialog({
    title: 'Custom Browser Docks', w: 520, resizable: false,
    content: h('div', { style: { padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' } },
      h('div', { class: 'row' }, nameInp, urlInp, h('button', { class: 'qpush', text: 'Add', onclick: () => {
        if (urlInp.value && nameInp.value) {
          obs.emit('add-browser-dock', { name: nameInp.value, url: urlInp.value });
          obs.log('info', `Added custom browser dock '${nameInp.value}'`);
          toast('Browser dock added (panel opens as a window)');
          window.open(urlInp.value, '_blank', 'width=420,height=560');
        }
      } })),
      list),
    buttons: [{ label: 'Close', def: true, action: () => d.close() }],
  });
}

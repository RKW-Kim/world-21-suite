# OBS Studio — Web Replica

A 1:1 replication of the OBS Studio desktop GUI in pure HTML/CSS/JS — no frameworks, no build
step, no dependencies. Connects to a **real OBS** instance over **obs-websocket v5** and drives
it live (scenes, sources, mixer, transitions, outputs, studio mode), or runs fully offline
against a built-in simulated core / the included demo backend.

```
┌────────────────────────────────────────────────────────────────────┐
│ OBS logo   OBS 30.2.3 - Profile: … - Scenes: …          –  □  ✕    │
│ File  Edit  View  Docks  Profile  Scene Collection  Tools  Help    │
├──────────────┬──────────────────────────────────┬──────────────────┤
│ Scenes       │                                  │ Audio Mixer      │
│ Sources      │          Preview                 │ Transitions      │
│              │      (drag / resize sources)     │ Controls         │
├──────────────┴──────────────────────────────────┴──────────────────┤
│ ● LIVE 00:00:12 · 4500 kb/s   ● REC 00:05:40      CPU 3.2% 60 fps  │
└────────────────────────────────────────────────────────────────────┘
```

## Quick start

ES modules need HTTP, so serve this folder with any static server:

**Option A — Node (zero dependencies):**
```bash
node server.mjs            # → http://localhost:8787
```

**Option B — Python:**
```bash
python3 -m http.server 8787
```

**Option C — double-click a launcher:**
- macOS / Linux: `./start-mac-linux.sh`
- Windows: `start-windows.bat`

Then open **http://localhost:8787**. That's it — the whole app runs client-side.

## Connecting to a real OBS (live control)

1. On your desktop OBS ≥ 28: **Tools ▸ WebSocket Server Settings** → enable it,
   note the port (default `4455`) and set a password (or uncheck auth).
2. In the replica: **Tools ▸ Connect to OBS…**
3. Tick **Direct ws:// connection**, enter `localhost:4455` (or your OBS host IP) + password → Connect.
4. The status bar shows `WS ● Connected`. Everything below now drives the real OBS:

| Replica action | obs-websocket v5 calls |
|---|---|
| Click scene (program / preview) | `SetCurrentProgramScene` / `SetCurrentPreviewScene` |
| Create / rename / remove scene | `CreateScene`, `SetSceneName`, `RemoveScene` |
| Add / remove source | `CreateInput`, `RemoveInput` |
| Eye / lock toggles | `SetSceneItemEnabled` |
| Drag & resize in preview | `SetSceneItemTransform` |
| Mixer faders / mute | `SetInputVolume`, `SetInputMute` (+ live meters via `InputVolumeMeters` events) |
| Stream / Record / Virtual Cam buttons | `StartStream`, `StopStream`, `StartRecord`, `StopRecord`, `StartVirtualCam`, `StopVirtualCam` |
| Transitions dock / studio mode | `SetCurrentSceneTransition(Duration)`, `TriggerStudioModeTransition`, `SetTBarPosition`, `Enable/DisableStudioMode` |
| Filters / properties | `SetSourceFilterSettings`, `SetSourceFilterEnabled`, `SetInputSettings` |
| Status bar CPU/FPS/RAM | `GetStats` polling |
| Live scene/output changes made in desktop OBS | Events: `CurrentProgramSceneChanged`, `SceneItemEnableStateChanged`, `StreamStateChanged`, … |

### No OBS installed? Try the demo backend

```bash
node demo-obs-server.mjs            # ws://localhost:4455, password "test123"
```

This is a zero-dependency, protocol-faithful obs-websocket v5 server (Hello → Identify auth →
Identified, Requests, Events, Batch). It pushes `InputVolumeMeters` at 250 ms so the mixer
dances with real protocol data, and flips program to *Demo Scene B* after 8 s to prove
event handling. Point the replica's **Tools ▸ Connect to OBS…** at it.

Offline mode (no connection) works too — the app ships with a built-in simulated core that
implements the same request/event surface internally.

## What's replicated

- **Main window**: title bar, 8 canonical menus (File, Edit, View, Docks, Profile,
  Scene Collection, Tools, Help) with working actions, dockable Scenes / Sources / Audio
  Mixer / Transitions / Controls / Stats docks, status bar.
- **Audio Mixer**: dB-accurate faders, dual VU meters with peak hold, mute / monitor options,
  advanced audio properties.
- **Preview**: real scene compositor — add sources (browser, image, text, color, display via
  `getDisplayMedia`, media…), drag, resize, crop, rotate, Edit Transform, right-click
  context menus, snap guides.
- **Studio Mode**: Program/Program pane, Cut/Fade, draggable T-bar, `Space` to transition.
- **Settings**: General / Stream / Output / Audio / Video / Hotkeys / Accessibility /
  Advanced — including the **theme engine** (Dark/Yami, Light/Acri, Grey/Rachni, System) and
  custom theme color import (paste any OBS `.qss`/`.obt` — its `qproperty-*` palette is parsed
  and applied live).
- **Tools**: Auto-config wizard, Plugins, Scripts, Output timer, projectors, multiview,
  remux, log viewer, WebSocket settings.
- **Edit**: undo/redo (Ctrl+Z/Y), copy/paste/paste-reference, copy/paste filters.
- **Hotkeys**: Ctrl+1…9 scenes, Space (studio transition), F11, Ctrl+, settings, plus
  user-bindable hotkeys in Settings ▸ Hotkeys.

## What obs-websocket can't do (named, per request)

These OBS features are replicated in the **UI** but cannot be driven through obs-websocket v5 —
the protocol simply has no request/event for them:

1. **Video frames of OBS's actual output** — no raw-frame request exists; the replica renders
   its own compositor (only `GetSourceScreenshot` stills per source).
2. **Screen / window / game capture acquisition** — capturing OS windows and games happens in
   OBS's process; a browser page can only `getDisplayMedia` what the user picks.
3. **Encoder control (x264 / NVENC / AMF detail settings)** — encoding runs inside OBS.
4. **Desktop audio capture** — browsers cannot tap system audio without screen-share.
5. **Native plugin execution (.dll/.so, Lua/Python scripts)** — plugins run in OBS's process.
6. **Virtual camera output itself** — the camera device is created by OBS; we only start/stop it.
7. **Hotkey capture while the page is unfocused** — browsers don't allow global key hooks.
8. **Remuxing recordings, writing to OBS's log/config folders** — filesystem sandbox.
9. **Tray icon, native notifications, always-on-top window behavior** — OS integration.
10. **Multi-adapter / renderer selection, performance windows** — hardware paths in OBS.

## Layout

```
obs-web-studio/
├── index.html            ← entry point (standalone)
├── server.mjs            ← zero-dep static server
├── demo-obs-server.mjs   ← zero-dep obs-websocket v5 demo backend
├── start-mac-linux.sh / start-windows.bat
├── css/  themes.css · obs.css · dialogs.css
├── js/   main.js · engine.js · ui.js · docks.js · preview.js ·
│         settings.js · dialogs.js · tools.js · ws.js · icons.js · util.js
└── docs/ architecture.html (interactive, generated with archify)
          architecture-quick-reference.png
```

## Architecture (short version)

**Pure vanilla ES modules, zero runtime dependencies.** `main.js` boots the app into
`#obs-root`; `engine.js` is the state store + simulated OBS core (event bus, undo, persistence
to localStorage); every UI module (docks, preview, mixer, dialogs) renders from engine state
and mutates it through engine methods; `ws.js` is an obs-websocket v5 client that mirrors those
engine mutations over the wire, so connected and offline behavior share one code path.
The full interactive diagram is in `docs/architecture.html`.

See the hosted/development report for the complete architecture decision record.

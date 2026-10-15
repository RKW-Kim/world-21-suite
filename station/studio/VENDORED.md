# Vendored: OBS Studio Web Replica (`station/studio/`)

- **Origin:** user-supplied `OBS-Studio-Web-Replica.zip` (received 2026-10-14),
  commissioned work owned by the operator. Vendored with permission.
- **Kept:** `index.html`, `css/`, `js/`, `README.md` — unmodified.
- **Excluded:** `server.mjs` (our overlay server serves the tree),
  `demo-obs-server.mjs` (mock OBS on :4455 — NEVER run on the render-plane
  host, it would shadow the real socket), `start-*` launchers, `docs/`
  (kept in Downloads, not shipped).
- **Pristine-tree policy:** six marked `LOCAL-PATCH` lines exist (see below);
  everything else byte-identical to the drop. Updates: re-copy the tree,
  re-apply the listed patches, commit.
- **LOCAL-PATCH list (all verified live against OBS 32.2.2 / ws 5.7.4):**
  1. `js/ws.js` Identify: `+ Meters bit (0x10000)` — without it no live
     levels ever arrive; mixer dB was sim-only.
  2. `js/ws.js` event switch: `InputVolumeMeters` case feeding
     `obs.setLiveLevel()` — the consumer never existed.
  3. `js/engine.js`: `_liveLevels` map + `setLiveLevel/clearLiveLevels` +
     `getLevel()` prefers live peaks when attached (sim otherwise).
  4. `js/ws.js` disconnect: clears live levels (no frozen meters).
  5. `js/ws.js` mirror `setTransition`: real field is `transitionName`
     (was `sceneTransitionName` — failed silently on every transitions
     change).
  6. `js/ws.js` mirror `reorderScene`: no such protocol call exists —
     replaced with a spoken warning, local order only.
  7. `js/ws.js` opcode table: Request is op 6 (was 5), responses op 7
     (was 6), batch op 8 (was 7), batch-responses op 9 (was 8). The whole
     client spoke a shifted dialect that only its own mock understood;
     real OBS closed every session with "Unknown OpCode: 5".
  8. `js/ws.js` request(): 12s window + one retry + visible warnings
     (was 5s-then-silent), plus 15s flap grace before first send.
  9. `js/ws.js` mirror wrap: no `busy` gate (it is held by unrelated async
     event handling, e.g. the daemon's own deck advances, and silently
     dropped user actions fired mid-flight; every mirrored call sets
     absolute state so echo is harmless).
  10. `js/main.js` boot: auto-connect after paint + 5s watchdog with
     stuck-handshake redial (never stamps on a handshake younger than 15s).
  7. `js/main.js` boot: auto-connect after first paint (gateway defaults
     already target this server; the relay bridges authentication, so no
     password is needed anywhere on the operator side).
- **Integration:** served at `/studio` (MIME-correct, no-cache exempt —
  browsers may cache; hard-reload after updates). OBS traffic goes through
  the overlay server's raw relay: the replica's gateway mode
  (`?XTransformPort=<obs-port>`) is spliced TCP-to-TCP to the render plane,
  auth end-to-end via its own connect dialog. See `_ws_relay`.
- **Known notes (theirs to fix upstream, not forked here):**
  - Add-source offers platform-specific captures absent on Linux
    (game/dshow/vlc/AVFoundation); those creates fail at runtime.
  - README's `Enable/DisableStudioMode` row is docs-only; the code
    correctly uses `SetStudioModeEnabled`.
  - Deploy script only mirrors `overlay/` to gh-pages, so this tree is
    never published publicly. Keep it that way: it is a control surface.

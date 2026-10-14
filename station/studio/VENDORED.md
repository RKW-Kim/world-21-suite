# Vendored: OBS Studio Web Replica (`station/studio/`)

- **Origin:** user-supplied `OBS-Studio-Web-Replica.zip` (received 2026-10-14),
  commissioned work owned by the operator. Vendored with permission.
- **Kept:** `index.html`, `css/`, `js/`, `README.md` — unmodified.
- **Excluded:** `server.mjs` (our overlay server serves the tree),
  `demo-obs-server.mjs` (mock OBS on :4455 — NEVER run on the render-plane
  host, it would shadow the real socket), `start-*` launchers, `docs/`
  (kept in Downloads, not shipped).
- **Pristine-tree policy:** never edit files under `studio/`. Updates arrive
  as a fresh zip from the author: delete the tree, re-copy, commit. Any
  local deviation (none so far) must be listed here with its reason.
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

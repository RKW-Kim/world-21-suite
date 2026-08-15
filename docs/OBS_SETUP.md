# OBS Setup Guide

> How to point OBS at the GitHub Pages URL and verify the overlay is working.
> 5-minute setup. No build step, no server, no bridge to keep alive.

---

## Step 1: Enable GitHub Pages (one-time)

1. Open <https://github.com/RKW-Kim/world-21-suite/settings/pages>
2. Under "Build and deployment", set **Source: GitHub Actions**.
3. Done. The next push to `main` triggers the [`deploy-pages`](../.github/workflows/deploy-pages.yml) workflow.

You'll get a green checkmark on the workflow run when it succeeds. The site URL will be:
```
https://rkw-kim.github.io/world-21-suite/
```

> Pages deploys only from `main`. If you're on `prototype`, merge to `main` first.

---

## Step 2: Pick your overlay file

Each file in `overlay/` (top-level only — `archive/` files are reference-only) is a complete OBS browser source:

| File | What it is | Recommended? |
|---|---|---|
| [`overlay/smile-v9.html`](../overlay/smile-v9.html) | Current good baseline (V7 strap + V9 surgical fixes) | ✅ **Yes — start here** |
| [`overlay/test-7.html`](../overlay/test-7.html) | V7 — the APPROVED baseline (strap choreography is sacred) | For reference / V7 regression testing |
| [`overlay/smile-v8.html`](../overlay/smile-v8.html) | V8 — the failed precision rebuild | ❌ Don't use — kept for history |
| [`overlay/test.html`](../overlay/test.html) | Revolut Obsidian Batch 01 (parallel design exploration) | If you want the blue/banking aesthetic |
| [`overlay/revolut-overlay-v03.html`](../overlay/revolut-overlay-v03.html) | Revolut Obsidian v0.3 | Same — Revolut direction |

The live URL pattern is:
```
https://rkw-kim.github.io/world-21-suite/<filename>
```

So:
- `https://rkw-kim.github.io/world-21-suite/smile-v9.html` (the recommended one)
- `https://rkw-kim.github.io/world-21-suite/test-7.html`
- etc.

---

## Step 3: Add the Browser Source in OBS

1. Open OBS Studio.
2. In the **Sources** panel (bottom), click **+** → **Browser**.
3. Name it (e.g., `SMILE Overlay`) → OK.
4. Properties dialog:
   - **URL**: `https://rkw-kim.github.io/world-21-suite/smile-v9.html`
   - **Width**: `1920`
   - **Height**: `1080`
   - **FPS**: `30` (or `60` if your stream is 60fps)
   - ✅ **Shutdown source when not visible** (saves CPU)
   - ✅ **Refresh browser when scene becomes active** (optional but recommended — picks up file updates)
5. Click **OK**.

The overlay should appear in your preview window.

---

## Step 4: Test the keys

Press these keys **while the OBS preview has focus** (or click on the browser source in the preview first):

| Key | What it does | What you should see |
|---|---|---|
| `1` | Hide overlay | Overlay fades out (1.4s soft fade) |
| `2` | Lesson strap | Kicker + headline + amber rule slide up with staggered mask reveal |
| `3` | TP (take-profit) strap | Green strap, smile → grin + celebrate, ladder at 88%, `+32.0 pips` count |
| `4` | SL (stop-loss) strap | Red strap, smile → frown + shake, ladder at 6%, `-18.0 pips` |
| `5` | Poll strap | Poll question + options strap |
| `6` | Host/name strap | Host introduction strap |
| `7` | Goal strap | Goal progress strap, smile's goal ring fills |
| `8` | Wire card | DESK/NOTICE/LESSON notice card slides in |
| `9` | Force wire swap | Manually rotate to next wire instrument |
| `V` | Cycle backgrounds | 5 test scenes: 0 dark, 1 bright chart, 2 talking-head, 3 city-night, 4 light |
| `T` | Clock mode | Cycles: LIVE (green dot, seconds) → TAPE (amber, date + "REC · DEMO") → STEALTH (black-on-black) |
| `L` | Light theme toggle | Switches dark ↔ light palette |
| `B` | Market background | Toggles the faint amber market-line SVG |
| `H` | Hide help | Hides the keyboard help overlay |

For the full keymap + visual description: see [`docs/archive/SMILE-ARCHIVE.md`](./archive/SMILE-ARCHIVE.md) §10 ("V9 FILE ANATOMY") and §12 ("Continuity test").

---

## Step 5: (Optional) Wire live trade state

The overlay can display **live** trades (instead of the demo simulator) if a bot writes [`overlay/state.json`](../overlay/state.json) every few seconds. The overlay polls it every 3s and switches automatically.

### state.json schema (see [`SIGNALS.md`](../SIGNALS.md) for the full doc)

```json
{
  "pair": "EUR/USD",
  "goal": { "count": 850, "target": 2000 },
  "trades": [
    { "pair": "EUR/USD", "side": "long",  "pnl": "▲ +34 pips" },
    { "pair": "XAU/USD", "side": "long",  "pnl": "▲ +$126" },
    { "pair": "BTC/USD", "side": "short", "pnl": "▼ −0.8%" }
  ],
  "ticker": [
    { "symbol": "EUR/USD", "price": "1.0842", "change": "+0.12%" }
  ],
  "live": true
}
```

### Integration path (per `SIGNALS.md`)

- **A. FILE (works today):** bot/EA writes `overlay/state.json` directly. Gitignored if you want to keep it local-only; or commit to a separate `live-state` branch and let Pages deploy it.
- **B. BRIDGE (future):** a small HTTP service exposes `POST /state`; overlay swaps polling for `EventSource`. One-line change.
- **C. NATIVE (ask smile backend):** smile backend emits a webhook on position open/update/close → webhook writer → `state.json`.

---

## Troubleshooting

### Overlay is blank / shows old version
- **Right-click** the Browser Source in OBS → **Refresh**.
- Or toggle **Shutdown source when not visible** off, then on again.
- GitHub Pages caches aggressively; force-refresh with `Ctrl+F5` in a regular browser tab pointed at the URL.

### Overlay is too small / blurry
- Confirm Width **1920** and Height **1080** in the Browser Source properties.
- Confirm your OBS canvas is also 1920×1080 (Settings → Video → Base Canvas Resolution).

### Keys don't seem to work
- Click the OBS preview window once to give it focus. (Browser sources only receive keyboard input when OBS is focused.)
- If running in a regular browser tab (not OBS), click the page first.

### Ticker cells flash like a strobe
- This was the V8 bug (archive §6 finale). Make sure you're on `smile-v9.html`, not `smile-v8.html`.
- If you see strobe on v9: file a bug with the `.github/ISSUE_TEMPLATE/bug.md` template — this is a regression of landmine #1 (archive §8).

### Strap lies on top of the ticker
- V8 bug. Use `smile-v9.html`. If you see this on v9: regression of landmine #3 — file a bug.

### Grin looks off-center
- V8 bug. Use `smile-v9.html`. If you see this on v9: regression of landmine #4 — file a bug.

---

## Going live

When you're happy with `smile-v9.html` on `main`:

1. Confirm the deploy-pages workflow ran (green checkmark at <https://github.com/RKW-Kim/world-21-suite/actions/workflows/deploy-pages.yml>).
2. Open the URL in a regular browser tab first to verify: <https://rkw-kim.github.io/world-21-suite/smile-v9.html>
3. Add the Browser Source in OBS per Step 3 above.
4. Press `H` to hide the keyboard help overlay.
5. Press `T` until the clock pill shows **LIVE** (green dot, seconds).
6. You're live.

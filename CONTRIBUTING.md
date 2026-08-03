# Contributing

## The one rule
Operators never hand-edit deployed files. Every change is either a **core** change (edit `core/`, commit, redeploy) or a **brand** change (edit `brands/<x>/brand.json`). No opening a live file mid-week.

## Repo map
- `core/` brand-agnostic engine, served over localhost by `bridge.py`. `smile.css` = components + Smile default tokens. `smile-mark.js` = 1:1 mark + moods + runtime brand layer. `live-feed.js` = data. `*.html` = the screens (kept flat with the css/js so file:// also works).
- `brands/<name>/` one folder per look, data only. `core/brand.json` = the active skin the bridge serves.
- `obs/` portable scene collection (localhost URLs). `docs/` manual. `scripts/` + `.github/` CI/build/push.

## Add an instrument
1. `core/live-feed.js` -> push to `FEED`. 2. `core/bridge.py` -> push same row to `SYMBOLS`. 3. pick `prov`: binance|metals|fx|td(budget-gated)|smile(dev feed). 4. `python scripts/validate.py`.

## Add a layout
Edit the `T={...}` table in `core/03-live.html`, then add the scene + browser source (`?layout=<key>`) to `obs/Smile-Trading-Kit.json`.

## Add a brand
Copy `brands/template/` -> `brands/<name>/`, edit `brand.json`. To make it active, copy it to `core/brand.json` (or set `BRAND_FILE`). No code.

## Change the mark shape
A `core/smile-mark.js` constant change (`EYES`/`MOUTH`), in a PR, kept 1:1 to the official asset. See `docs/design.md`.

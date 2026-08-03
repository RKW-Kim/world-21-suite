# Theming & multi-channel

## How a brand is applied (no page edits)
Each page loads `core/smile-mark.js`, which asks the bridge for `http://localhost:8787/brand.json` and: sets CSS variables (`tokens`), rewrites every logo wordmark (`wordmark`), and runs find->replace over on-screen text (`handles`, including late-rendered text via a short MutationObserver). Bridge off -> built-in Smile defaults apply, so Smile needs no brand file.

## brand.json schema
- `name` label only.
- `wordmark` text in the logo lockup.
- `tokens` CSS vars to override: `--yellow --yellow-hot --ink --panel --panel-2 --line --muted --paper --up --down --up-soft --down-soft --sky --live`.
- `handles` `{ "old text": "new text" }` applied to any text node on any page.

## New channel
1. Copy `brands/template/` -> `brands/<channel>/`. 2. Edit `brand.json`. 3. Copy it to `core/brand.json` (or `set BRAND_FILE=...`), run bridge, refresh OBS.

## What brand.json can't change
The mark shape is shared core geometry; a different logo shape is a `core/smile-mark.js` PR.

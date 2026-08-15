# Contributing

## The one rule

**Full files only.** No diffs, no "edit line 40," no scripts that patch. If you're changing an overlay HTML file, you ship the complete file. (This rule was forged in the original chat after batched heredoc delivery kept truncating files mid-tag — see `docs/archive/SMILE-ARCHIVE.md` §8 landmine #10.)

## Repo map

```
world-21-suite/
├── overlay/                       ← THE FOLDER (singular, NOT 'overly/')
│   ├── smile-v9.html              ← current good baseline (sacred)
│   ├── smile-v8.html              ← V8 (failed precision rebuild, kept for ref)
│   ├── test-7.html                ← V7 (APPROVED baseline — strap choreography is SACRED)
│   ├── _shared.css, _shared.js    ← shared design system
│   ├── smile.css, smile-mark.js   ← smile brand CSS + mascot animation engine
│   ├── smile-mark.svg             ← canonical smile SVG (100-viewBox, FIXED)
│   ├── state.json                 ← live trade state (file-based bot integration)
│   └── archive/                   ← earlier iterations (test-2..6.html)
│
├── docs/
│   ├── OBS_SETUP.md               ← how to point OBS at the GitHub Pages URL
│   ├── archive/SMILE-ARCHIVE.md   ← complete project history + taste profile + landmines
│   └── development/
│       ├── VERSIONING.md          ← versioning rules
│       └── BRANCHING.md           ← branch model + commit conventions
│
├── SIGNALS.md                     ← live trade state integration (file-based / bridge / native)
├── CHANGELOG.md                   ← what's new in each version
├── brand.json                     ← smile brand tokens (colors, handles, wordmark)
└── .github/workflows/             ← CI (validate) + deploy (Pages)
```

## Add a new strap state to `smile-v9.html`

1. Read `docs/archive/SMILE-ARCHIVE.md` §7 (taste profile) and §8 (landmines catalog).
2. Read §10 (V9 file anatomy) to understand where strap states are defined.
3. **Copy `smile-v9.html` to `smile-v10.html`** if the change is destructive or experimental. Otherwise edit v9 in place.
4. Add the new state to the strap state map (kicker + headline + amber rule + sub-line + optional ladder/number block).
5. Bind a key (use the next free number — see §10 KEYS list).
6. Test in OBS (see `docs/OBS_SETUP.md`).
7. Update `CHANGELOG.md` with the new state under `[Unreleased]`.
8. Open a PR: `feat/strap-<state>` → `prototype`. CI runs `html-validate`. Merge after human review.

## Add a new ticker cell type

1. Same ritual: read archive §7-8 first.
2. Ticker cells live in `smile-v9.html` (or `smile-v10.html` if destructive).
3. The 6th cell is THE WIRE — the rotating news/instrument slot. Other cells are pinned (EUR/USD, GBP/USD, USD/JPY, XAU/USD, BTC/USD). See §10.
4. Match the existing cell structure: mono symbol (9.5px, faint) + % change pill (green/red, caret triangle) + 20px tabular-nums price.
5. Landmine warnings (archive §8):
   - **#1**: entrance animation must play EXACTLY ONCE (`.done` class on `animationend`). Flash is a separate animation that only runs on `.done` cells. Strobe = entrance replaying.
   - **#6**: wire cell counter badge was deleted (collided with change pill). Don't re-add.
   - **#7**: progress bar goes on cell BOTTOM EDGE, never under the price (reads as underline).

## Add a new background scene (V key cycle)

1. Read §10 BACKGROUNDS section in archive.
2. V cycles 5 scenes today: 0 dark, 1 bright chart, 2 talking-head warmth, 3 city-night, 4 light (auto-toggles light theme).
3. Add scene 5+ by extending the cycle array in `smile-v9.html`.
4. Verify the scene doesn't fight the strap or ticker (light scene must auto-toggle light palette).

## Change the mascot (the smile)

**Stop. Read `docs/archive/SMILE-ARCHIVE.md` §8 landmine #4 first.**

- The canonical smile SVG is **FIXED**: 100-viewBox, face circle r=48 at (50,50), eyes r=5.5 at (31,35) and (69,35).
- Mouth paths MUST be authored in the 100-viewBox coordinate space, chord-centered at x=50:
  - neutral: `M 20 48 A 30 30 0 0 0 80 48`
  - grin:    `M 15 44 A 35 35 0 0 0 85 44`
  - frown:   `M 30 64 A 22 22 0 0 1 70 64`
- Wrong-viewBox paths = off-center grin. This was the V8 bug.
- Layered contact shadow only (no glow): `drop-shadow(0 1px 1px rgba(0,0,0,.35)) drop-shadow(0 3px 6px rgba(0,0,0,.4))`.

## Tournament method (when exploring new designs)

Per archive §7 rule #8: when exploring, present 2–3 **named variants** sharing ONE LOCKED SPEC. User picks a winner; winner becomes the new baseline.

1. Define the locked spec (e.g., "strap choreography stays V7; only the ticker layout varies").
2. Build 2–3 variants as separate HTML files in `overlay/` (e.g., `exploration-a.html`, `exploration-b.html`, `exploration-c.html`).
3. Push to `prototype`, deploy via Pages, give the user the 2–3 URLs to compare in OBS.
4. User picks. Rename the winner to `smile-v10.html` (or whatever next number). Delete the losers, or move to `overlay/archive/`.

## Branch + commit conventions

See [`docs/development/BRANCHING.md`](./docs/development/BRANCHING.md). TL;DR:

- Work on `prototype` (or a `feat/*` branch off `prototype`).
- Commit format: `<type>(<scope>): <description> [Task ID: <id>]`
- Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`
- Scopes: `overlay`, `ticker`, `strap`, `mascot`, `bg`, `ci`, `docs`, `infra`

## CI

- `html-validate` runs on every PR (`.github/workflows/validate.yml`).
- Config: `.github/html-validate.json` (tuned for OBS browser-source HTML — relaxed on script/style/heading rules).
- Archive files (`overlay/archive/*.html`) get a **warning-only** smoke check, not a hard fail.

## Deploy

- Push to `main` → `deploy-pages.yml` runs → `overlay/` deploys to GitHub Pages.
- Live URL: `https://rkw-kim.github.io/world-21-suite/<filename>.html`
- See [`docs/OBS_SETUP.md`](./docs/OBS_SETUP.md) for the full setup guide.

## Communication style (archive §7 rule #9)

- **"Next"** = keep shipping. Don't stop to ask permission.
- **"Great stuff"** = pleased.
- **Hard grilling** = quality dropped. Convert to a numbered fix list and ship the fix. Don't defend. Don't take personally.
- **"We're going backwards"** = always right. Diff against the last approved version, restore what was lost FIRST, then add new things.

## The rules (read these once)

1. Full files only. No diffs, no patches.
2. No jargon without inline definition. ("Wire" = newsroom slang for the Reuters/AP feed.)
3. No metaphors unflagged. ("Volume up" was once taken literally.)
4. Judge by screenshots. Describe what to press, what the eyes should report.
5. Momentum matters. Ship first, explain second.
6. V7 strap choreography + V9 surgical fixes are SACRED. Canonical smile SVG is FIXED. Extend, never regress.
7. Folder is `overlay/` (singular). Never `overly/`.

# World-21 Suite

> **One HTML file = one OBS browser source.**
> A finance/trading education livestream overlay system for Nairobi-based retail-trading-curious viewers.
> Self-contained HTML files — no frameworks, no build step, no external assets except Google Fonts.

[![CI](https://github.com/RKW-Kim/world-21-suite/actions/workflows/validate.yml/badge.svg?branch=prototype)](https://github.com/RKW-Kim/world-21-suite/actions/workflows/validate.yml)
[![Deploy](https://github.com/RKW-Kim/world-21-suite/actions/workflows/deploy-pages.yml/badge.svg?branch=main)](https://rkw-kim.github.io/world-21-suite/)

---

## What this is

A **single-file overlay system** for OBS. Each `*.html` file in `overlay/` is a complete broadcast graphics layer — ticker, lower-third strap, mascot, backgrounds, live trade state — that you point OBS at as a Browser Source. That's the whole architecture. No Next.js, no Python bridge, no Prisma, no server to keep alive. Just HTML files served from GitHub Pages.

The current good baseline is [`overlay/smile-v9.html`](./overlay/smile-v9.html). It is **sacred** — V7's strap choreography + V9's surgical fixes (see [`docs/archive/SMILE-ARCHIVE.md`](./docs/archive/SMILE-ARCHIVE.md) §7–8). New work extends it; never regresses it.

## Live URLs (once GitHub Pages is enabled — see [Setup](#setup))

| File | OBS Browser Source URL |
|---|---|
| `overlay/smile-v9.html` (current) | `https://rkw-kim.github.io/world-21-suite/smile-v9.html` |
| `overlay/test-7.html` (V7 baseline) | `https://rkw-kim.github.io/world-21-suite/test-7.html` |
| Index (clickable list) | `https://rkw-kim.github.io/world-21-suite/` |

**Setup**: 1 minute. See [`docs/OBS_SETUP.md`](./docs/OBS_SETUP.md).

## Folder structure

```
world-21-suite/
├── overlay/                       ← THE FOLDER (singular, NOT 'overly/')
│   ├── smile-v9.html              ← current good baseline (sacred)
│   ├── smile-v8.html              ← V8 (the failed precision rebuild, kept for ref)
│   ├── test-7.html                ← V7 (the APPROVED baseline — strap choreography is SACRED)
│   ├── test.html                  ← Revolut Obsidian Batch 01 (parallel design exploration)
│   ├── revolut-overlay-v03.html   ← Revolut Obsidian v0.3 (parallel design exploration)
│   ├── _shared.css, _shared.js    ← shared design system (used by some explorations)
│   ├── smile.css                  ← smile brand CSS (used by v1-style files)
│   ├── smile-mark.js              ← canonical smile mascot animation engine
│   ├── smile-mark.svg             ← the canonical smile SVG (100-viewBox, sacred)
│   ├── state.json                 ← live trade state (file-based bot integration, see SIGNALS.md)
│   └── archive/                   ← earlier iterations (test-2..6.html), reference-only
│
├── docs/
│   ├── OBS_SETUP.md               ← how to point OBS at the GitHub Pages URL
│   ├── archive/
│   │   └── SMILE-ARCHIVE.md       ← complete project history, taste profile, landmines catalog
│   └── development/
│       ├── VERSIONING.md          ← single source of truth for versioning rules
│       └── BRANCHING.md           ← branch model + commit conventions
│
├── SIGNALS.md                     ← live trade state integration (file-based / bridge / native)
├── CHANGELOG.md                   ← what's new in each version
├── brand.json                     ← smile brand tokens (colors, handles, wordmark)
├── .github/workflows/
│   ├── validate.yml               ← HTML-validate CI on PRs
│   └── deploy-pages.yml           ← deploy overlay/ to GitHub Pages on push to main
└── .github/html-validate.json     ← CI config
```

## Project identity (the 30-second pitch)

- **Project**: SMILE TV — finance/trading education livestream overlay.
- **Base**: Nairobi, Kenya. Audience: Kenyan / East African retail-trading-curious viewers.
- **Host placeholder**: Mwangi. Site placeholder: `smile.co.ke`.
- **Format**: Live trading education on a DEMO account — an ethical stance, not a limitation.
  - Framing: *"education only, never financial advice; trading involves risk."*
  - Some content pre-recorded (clock has a tape mode — never fake-live), some genuinely live.
- **North star reference**: TraderTV Live — but classroom-paced, warm and alive, not trading-floor frantic.
- **Brand voice** (real phrases used in the overlay copy):
  - "4G smiles"
  - "losses are tuition — we show ours so you pay less of yours"
  - "one question in, one skill out"
  - "the mango test" (teaching metaphor for support/resistance)
  - "Chart School" (4-part lesson series), live lessons Mondays 9PM EAT

→ Full identity, history, taste profile, and landmines catalog: [`docs/archive/SMILE-ARCHIVE.md`](./docs/archive/SMILE-ARCHIVE.md).

## Setup

### 1. Enable GitHub Pages (one-time, 1 minute)

1. Go to **repo → Settings → Pages**.
2. Under "Build and deployment", set **Source: GitHub Actions**.
3. Done. The next push to `main` triggers the [`deploy-pages`](./.github/workflows/deploy-pages.yml) workflow, which deploys `overlay/` to `https://rkw-kim.github.io/world-21-suite/`.

> Note: Pages won't deploy from `prototype` — only from `main`. Merge `prototype` → `main` to publish.

### 2. Point OBS at the URL

Open OBS → add a **Browser** source → set URL to one of:

- `https://rkw-kim.github.io/world-21-suite/smile-v9.html` (the current good baseline)
- `https://rkw-kim.github.io/world-21-suite/test-7.html` (V7 baseline, the approved one)

Width **1920**, Height **1080**. See [`docs/OBS_SETUP.md`](./docs/OBS_SETUP.md) for the full guide.

### 3. (Optional) Wire live trade state

To feed live trades into the overlay (instead of the demo simulator), have your bot/EA write [`overlay/state.json`](./overlay/state.json) every few seconds. The overlay polls it every 3s and switches from simulator to LIVE feed automatically. See [`SIGNALS.md`](./SIGNALS.md) for the schema and integration paths.

## Development workflow

```bash
git checkout prototype && git pull
git checkout -b feat/<scope>-<description>      # e.g. feat/strap-poll-state
# edit overlay/smile-v9.html (or copy to smile-v10.html for a new iteration)
git commit -m "feat(overlay): add poll strap state [Task ID: STRAP-POLL-1]"
git push -u origin feat/<scope>-<description>
# open PR: feat/* → prototype
# CI runs html-validate; merge after review
# when stable: PR prototype → main, tag v0.X.0
```

- **`prototype`** = active dev branch (GitFlow `develop`).
- **`main`** = production, deploys to Pages.
- **Tag** = semver release marker (`v0.4.0`, `v0.5.0`, ...).
- See [`docs/development/BRANCHING.md`](./docs/development/BRANCHING.md) for full rules.
- See [`docs/development/VERSIONING.md`](./docs/development/VERSIONING.md) for the version scheme.

## The rules (read these once)

1. **Full files only.** No diffs, no "edit line 40," no scripts that patch.
2. **No jargon without inline definition.** ("Wire" = newsroom slang for the Reuters/AP feed.)
3. **No metaphors unflagged.** ("Volume up" was once taken literally.)
4. **Judge by screenshots.** Every delivery must say: what to press, what the eyes should report.
5. **Momentum matters.** Ship first, explain second.
6. **"We're going backwards" = always right.** Diff against the last approved version, restore what was lost BEFORE adding anything new.
7. **V7 strap choreography is SACRED.** V9 surgical fixes are SACRED. Canonical smile SVG (100-viewBox, chord-centered at x=50) is FIXED. Extend, never regress.
8. **Folder is `overlay/` (singular).** Never `overly/`. If you see `overly/`, rename immediately.

Full rules + verbatim grilling quotes: [`docs/archive/SMILE-ARCHIVE.md`](./docs/archive/SMILE-ARCHIVE.md) §2 + §7.

## License

MIT — see [`LICENSE`](./LICENSE).

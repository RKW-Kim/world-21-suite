# Changelog

All notable changes to **World-21 Suite** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version tags follow the overlay-file-lineage scheme (see [`docs/development/VERSIONING.md`](./docs/development/VERSIONING.md)).

---

## [Unreleased] — on `prototype` branch

_Work in progress on the `prototype` integration branch. Will become `v9` (or `v10` if a new file supersedes v9) when merged to `main`._

### Added
- **`prototype` branch is now the active dev branch** (GitFlow `develop` equivalent).
- **`gh-pages` branch** — orphan branch containing a flat copy of `overlay/` at its root. GitHub Pages reads from it in "Deploy from a branch" mode. Bypasses Actions entirely (which has been failing to allocate runners on this repo).
- **`scripts/deploy-pages-branch.sh`** — one-command script that regenerates `gh-pages` from `prototype/overlay/`, adds `.nojekyll`, commits, force-pushes. Idempotent. Auto-stashes uncommitted changes.
- **`docs/development/VERSIONING.md`** — single source of truth for versioning rules in an HTML-only repo (no package.json, no semver — the filename IS the version).
- **`docs/development/BRANCHING.md`** — branch model + commit conventions adapted for static-HTML dev.
- **`docs/archive/SMILE-ARCHIVE.md`** — complete project history offload (every turn, every quote, every rule, every landmine). The AI context bridge.
- **`README.md`** — first README on `prototype` (was previously on `main` only, describing the Python bridge).
- **`docs/OBS_SETUP.md`** — how to point OBS at the GitHub Pages URL, with troubleshooting.
- **`.github/workflows/validate.yml`** — HTML-validate CI on PRs (replaces broken Python `validate.py`). Note: Actions runners can't be allocated on this repo currently, so this CI is dormant — kept in case the issue is resolved later.
- **`.github/html-validate.json`** — config tuned for OBS browser-source HTML.
- **`CHANGELOG.md`** (this file).

### Changed
- **Renamed `overly/` → `overlay/`** (the typo fix — `overly` was a typo from the beginning).
- **Moved `smile-v9.html`** from `smile-suite/` into `overlay/` (canonical location).
- **Archived `test-2.html` through `test-6.html`** into `overlay/archive/` (earlier iterations preserved for history, out of the active folder).
- **Updated `SIGNALS.md`** to reference `overlay/` (was `overly/`) in 2 places.
- **Updated `.github/PULL_REQUEST_TEMPLATE.md`** — replaced `python scripts/validate.py passes` with `html-validate CI check passes` + OBS visual-verification block.
- **Updated `.github/ISSUE_TEMPLATE/bug.md` and `feature.md`** — overlay-file-aware triage checklists.
- **Updated `docs/OBS_SETUP.md`** — rewrote Step 1 to use Pages "Deploy from a branch" mode (was "GitHub Actions" mode). Added Step 6 documenting the deploy script.
- **Updated `README.md`** — Setup section now describes the branch-based deploy, not Actions.
- **Cleaned `.gitignore`** — removed Python bridge cruft, added `_site/` (Pages build output).

### Removed
- **Deleted `smile-suite/`** directory entirely (canonical copies now in `overlay/`).
- **Deleted duplicates:** `overlay/test-7 copy.html`, `overlay/test-7 island.html`, `overlay/test-7.html.bak`.
- **Deleted orphans:** root `test.html`, `countdown/test.html`, `starting-soon/test.html`, and the empty `countdown/` + `starting-soon/` directories.
- **Deleted `.env.example`** (was Python bridge config; not needed for static HTML repo).
- **Deleted `.github/workflows/deploy-pages.yml`** — we no longer use Actions to deploy Pages; `scripts/deploy-pages-branch.sh` does it instead.
- **Deleted `scripts/generate-index.py`** — was only used by the now-deleted deploy-pages.yml workflow.
- **Did NOT delete `smile-v8.html`** (kept for reference — it's the failed precision rebuild, per archive §6).

---

## [v9] — current good baseline (tagged retroactively on merge to main)

_This is the file `overlay/smile-v9.html`. Tag will be applied when `prototype` is merged to `main`._

### What's in v9 (per archive §10)
- V7's strap choreography restored (sacred): type-only mask reveals, staggered (kicker .08s, headline .16s, rule .30s, sub .34s, expo ease `cubic-bezier(.16,1,.3,1)`).
- Surgical fixes from V8 grilling:
  - **Flashes**: soft 1.4s fades, significance-gated, max 1 per 3s per cell. Entrance animation plays EXACTLY ONCE (`.done` class on `animationend`).
  - **Wire cell**: counter badge DELETED (was colliding with change pill); progress bar moved to cell's BOTTOM EDGE; masked slide swap for symbol changes.
  - **Strap**: FIXED `bottom:104px` (never JS-calculated); number block back IN THE FLEX ROW.
  - **Smile**: canonical 100-box mouths (`M 20 48 A 30 30 0 0 0 80 48` etc.); layered CONTACT SHADOW (no glow).
  - **Goal ring**: track alpha `.12` (invisible until progress fills).
  - **Desk-time pill**: live / tape / stealth modes.
- Keys: `1` hide · `2` lesson · `3` TP · `4` SL · `5` poll · `6` host · `7` goal · `8` wire card · `9` force wire swap · `V` scenes · `T` clock mode · `L` light · `B` market bg · `H` hide help.

### Why v9 (per archive §6 — the grilling era)
V8 was a "precision rebuild" that failed all four of its changes (clip-path wipe, absolute-positioned number block, JS-injected ticker cells, JS-calculated strap position). User verdict on V8: *"Broski, we're going backwards."* V9 = V7's exact motion system restored, with ONLY surgical fixes to the V8 bugs. Approved as the current good baseline.

---

## [v7] — the APPROVED baseline (strap choreography is SACRED)

_The file `overlay/test-7.html`. Already in the repo from earlier prototype work._

### What's in v7
- "Studio" style strap: type-only mask reveals (no box sliding), staggered entrance, expo ease.
- Refined ticker, new visual hierarchy.
- All later versions build on V7's motion system. Per archive §7 rule #1: *"Never offer minimalism as a virtue. Density with intent is the house style."*

### User verdict (verbatim)
> *"Talk me more into it. Lower-third pop out card thingie design not too big on them honestly."* — approved.

---

## [v8] — the failed precision rebuild (kept for reference)

_The file `overlay/smile-v8.html`. Kept in `overlay/` but NOT recommended — see archive §6._

### What went wrong
Four changes attempted, all failed:
1. clip-path wipe for the strap number block — detached, overlapped ticker.
2. absolute-positioned number block — detached, overlapped ticker.
3. JS-injected ticker cells — flashed like strobes (entrance animation replaying on every flash).
4. JS-calculated strap position — strap lay on top of ticker cells.
Plus: grin rendered off-center (wrong viewBox paths), wire slot's counter badge collided with change pill, progress bar read as a random underline, goal ring track read as an ugly outline.

### User verdict (verbatim)
> *"Broski, we're going backwards."*

### Lesson (archive §6 meta-lessons #1)
> When the user says "we're going backwards," they are ALWAYS right. Diff mentally against the last approved version; restore what was lost BEFORE adding anything new.

---

## Earlier history (before this repo was reorganized)

For the complete annotated chat log — every turn, every quote, every rule, every landmine — see [`docs/archive/SMILE-ARCHIVE.md`](./docs/archive/SMILE-ARCHIVE.md). That file is the canonical context bridge for any AI agent picking up the project.

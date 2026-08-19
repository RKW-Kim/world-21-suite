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

---

## Worklog

### APPLY-R3-FIXES — GLM 5V R3 safe fixes (broadcast polish pass)

Source critique: `glm-frames/r3-response.txt` (GLM 5V Round 3 audit, scorecard 7.5/10 → ship-block on safe-area, tabular nums, spring damping). Applied the 3 safe fixes only; left the 2 sign-off-blocked items (gold `#FFB020` color shift, `backdrop-filter` on progress bar) untouched per user direction.

**Fix 1 (P0) — Ticker anchored to broadcast safe area** (`overlay/smile-v11.html` `.ticker`)
- `bottom: 24px` → `bottom: 0` (no more 8px "floating island" gap)
- `left/right: 24px` → `left/right: 48px` (broadcast safe area per Apple/Bloomberg convention)
- `border-radius: 14px` → `0` and `border: 1px solid rgba(255,255,255,.045)` → `0` (flush to screen edges now that it's anchored)
- Replaced the multi-layer inset/outset shadow with a 3-layer drop shadow: `0 -12px 40px rgba(0,0,0,.6)` (ambient occlusion) + `0 -4px 12px rgba(0,0,0,.4)` (contact shadow) + `inset 0 1px 0 rgba(255,255,255,.06)` (top edge highlight). Verified via computed-style probe: `rectBottom=0, rectLeft=48, rectRight=48`.

**Fix 2 (P1) — Tabular nums on data columns**
- Verified `.cval` (ticker prices, line ~100) already has `font-variant-numeric: tabular-nums` + `font-feature-settings: 'tnum' 1, 'zero' 1`. ✓
- Verified `.num` (popup card numbers, line ~242) already has both. ✓
- **Added** both properties to `.cchg` (change percentages, line ~95) — was the lone holdout. Verified via computed-style probe: `fontVariantNumeric="tabular-nums"`, `fontFeatureSettings='"tnum", "zero"'`.

**Fix 3 (P2) — Critically damped spring**
- `--spring` variable (line ~12): `cubic-bezier(.34,1.56,.64,1)` → `cubic-bezier(.22,1,.36,1)` (no overshoot, broadcast "News fast" feel)
- Island `width/height` transition (line ~164): `0.4s var(--spring)` → `0.32s cubic-bezier(.22,1,.36,1)` — explicit, <350ms settling per R3 §5 spec. Verified via computed-style probe: `transition = width 0.32s cubic-bezier(0.22,1,0.36,1), height 0.32s cubic-bezier(0.22,1,0.36,1), ...`.

**Skipped (user sign-off required):**
- R3 #3 "broadcast gold" palette shift (`#FFB020` → `#E6B84F`) — gold color is sacred per archive, needs explicit user approval.
- R3 #4 progress-bar `backdrop-filter: inherit` — unifying glass across progress bar + ticker risks performance regression on OBS browser source.

**Verification:**
- `agent-browser` loaded `file://.../smile-v11.html`, pressed `3` (TP state), 0 console errors, screenshot saved (`/tmp/r3-tp-state.png`).
- Computed-style probe confirms all 3 fixes landed in the cascade (ticker rect, cchg font features, spring var + transition string all match spec).
- Commit: `feat(overlay): GLM 5V R3 fixes — broadcast safe area, tabular nums, critically damped spring [Task ID: APPLY-R3-FIXES]`

---

### REVERT-R3-HARSH — undo R3 broadcast harshness; restore soft floating ticker + original bevel direction

User feedback: "everything looks horrible" after the R3 commit (`41309e4`) landed. The broadcast-safe-area pass made the ticker flush to the screen edges with no rounding and a heavy ambient-occlusion drop shadow — that industrial/News-fast aesthetic is what looked wrong, not the gold or the smile. Reverted surgically (3 CSS rule blocks + 1 variable + 1 transition string); kept every other R3/R2 improvement that wasn't the problem.

**Reverted — Ticker (`.ticker` rule, lines ~56-62):**
- `bottom: 0` → `bottom: 24px` (soft 24px float above screen edge, was the original floating-island feel)
- `left/right: 48px` → `left/right: 24px` (closer to edges, more intimate — broadcast safe area was over-correcting)
- `border-radius: 0` → `border-radius: 14px` (soft rounded corners)
- `border: 0` → `border: 1px solid rgba(255,255,255,.045)` (subtle edge definition)
- Drop shadow `0 -12px 40px rgba(0,0,0,.6), 0 -4px 12px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.06)` → original soft floating `inset 0 1px 0 rgba(255,255,255,.03), 0 0 0 1px rgba(0,0,0,.4), 0 1px 3px rgba(0,0,0,.25), 0 8px 24px rgba(0,0,0,.4)`. The heavy ambient-occlusion drop shadow was the single biggest "harsh" contributor.
- ALSO dropped the R2 glassmorphic-separation layer (`border-top: 1px solid rgba(255,255,255,.06)` + `inset 0 -1px 0 rgba(0,0,0,.3)`). It was stacking weight on top of weight. Original was cleaner.

**Reverted — cap.left bevel (`.cap.left` rule, lines ~74-78):**
- R2 inverted bevel `inset 0 -1px 0 rgba(255,255,255,.15), inset 0 1px 0 rgba(0,0,0,.4), inset -1px 0 0 rgba(0,0,0,.3)` → original A4 convex bevel `inset 0 1px 0 rgba(255,255,255,.28), inset 0 -1px 0 rgba(0,0,0,.22), inset -1px 0 0 rgba(0,0,0,.08)`. The R2 inversion made the cap look "stamped into" the strap (concave/recessed); the original highlight-on-top makes it look like it "sits on" the strap (convex/raised). That's the right read for a primary action surface.

**Reverted — Spring (used discretion per task):**
- Task offered the choice between KEEP (critically damped `cubic-bezier(.22,1,.36,1)`) and REVERT-TO-`--expo` (luxurious `cubic-bezier(.16,1,.3,1)`). User said "everything looks horrible" → erred toward the more luxurious feel.
- `--spring` variable: `cubic-bezier(.22,1,.36,1)` → `cubic-bezier(.16,1,.3,1)` (= `--expo` value, slow ease-out, no snap).
- Island `width/height` transition: `0.32s cubic-bezier(.22,1,.36,1)` → `0.4s var(--spring)` (back to R2-style .4s duration using the now-luxurious spring var; hardcoded curve removed so the variable is the single source of truth again).

**Kept (not the problem, per task):**
- Smile face stays GOLD (`#FFB020`) — sacred.
- `.cchg` tabular-nums + `font-feature-settings:'tnum' 1,'zero' 1` — R3 fix #2, helps alignment, no harm. Verified live: `fontVariantNumeric="tabular-nums"`.
- Reactive eye micro-expressions, blink timing, look-around.
- Progress bar depletion direction (1→0), R2 progress track alpha `.18`, 6/12px typography rhythm, 64px cap.left padding collapse on strap-active. All preserved.

**Verification:**
- `agent-browser` loaded `file://.../smile-v11.html`, viewport 1600×900, waited 3.5s for entry animation. 0 console errors. Screenshot saved (`/tmp/revert-r3-tp-state.png`).
- Computed-style probe on `.ticker`: `bottom=24px, left=24px, right=24px, borderRadius=14px, border=1px solid rgba(255,255,255,0.043), boxShadow="rgba(255,255,255,0.03) 0px 1px 0px 0px inset, rgba(0,0,0,0.4) 0px 0px 0px 1px, rgba(0,0,0,0.25) 0px 1px 3px 0px, rgba(0,0,0,0.4) 0px 8px 24px 0px"` — all soft-floating values confirmed in cascade.
- Computed-style probe on `.cap.left`: `boxShadow="rgba(255,255,255,0.28) 0px 1px 0px 0px inset, rgba(0,0,0,0.22) 0px -1px 0px 0px inset, rgba(0,0,0,0.08) -1px 0px 0px 0px inset"` — highlight on top, A4 convex bevel restored.
- Computed-style probe on `:root`: `--spring="cubic-bezier(.16,1,.3,1)"` (= `--expo`); on `.island`: `transition="width 0.4s cubic-bezier(0.16, 1, 0.3, 1), height 0.4s cubic-bezier(0.16, 1, 0.3, 1), ..."` — luxurious .4s spring confirmed.
- Live URL verified post-deploy: `curl -sI https://rkw-kim.github.io/world-21-suite/smile-v11.html` → HTTP/2 200, `last-modified: Wed, 19 Aug 2026 01:13:45 GMT`. Body grep confirms all reverted rules are live (soft ticker rect, soft shadow, convex bevel, `--spring` = `--expo`, island `width .4s var(--spring)`).
- Remote URL restored to clean non-PAT form after push (PAT was injected only for the duration of `git push` + deploy script).
- Commit: `revert(overlay): undo R3 harsh broadcast changes — restore soft floating ticker, original bevel direction [Task ID: REVERT-R3-HARSH]` (hash `5a260ec`, on `prototype`, pushed; `gh-pages` regenerated to `a90e5c7`).

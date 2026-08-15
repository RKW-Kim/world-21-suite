# Versioning Policy

> Single source of truth for how this repo versions things.
> Read this before touching git tags or branch names.

---

## One version stream: overlay file lineage

This repo is **HTML-only** (the Python bridge and Next.js console were removed; see `main` history if you need them). There is no `package.json` to bump. There is no app-semver stream. There is only one version stream:

- **The `smile-vN.html` filename** — `v9` is the current good baseline, `v10` will be the next iteration when shipped.
- Format: `smile-v<int>.html` (e.g., `smile-v9.html`, `smile-v10.html`).
- Bump cadence: only when a new standalone overlay iteration **supersedes** the previous one (i.e., the new file becomes the recommended OBS target, replacing the old one).
- Source of truth: the file itself + git history + `CHANGELOG.md`.

### Companion files (no version in filename)

- `_shared.css`, `_shared.js` — shared design system. Unversioned; they evolve continuously.
- `smile-mark.svg`, `smile-mark.js` — the canonical smile mascot. **FIXED** — see archive §8 landmine #4.
- `state.json` — live trade state. Unversioned; runtime data, not source.
- `test.html`, `revolut-overlay-v03.html` — parallel design explorations (Revolut Obsidian direction). Versioned by their own filename (`revolut-overlay-v03.html` means "third iteration of the Revolut Obsidian direction").

### Why no semver?

Semver (`0.4.0`, `1.0.0`) implies a library or app with an API. This repo serves static HTML files — there is no API to break. The filename IS the version. It's simpler, it's honest, and it matches how OBS users actually consume the file (they paste the URL with the version baked in).

If we ever add a build step (e.g. asset bundling, SCSS compilation) or a non-overlay deliverable (e.g. a bot that writes `state.json`), we'll introduce `package.json` and app-semver at that point. Not before.

---

## Git tags

Tags live on `main` only. `prototype` and feature branches do not get version tags.

| Tag | What it marks |
|---|---|
| `v9` | The commit on `main` where `overlay/smile-v9.html` became the recommended baseline. |
| `v10` | The commit on `main` where `overlay/smile-v10.html` superseded v9 (future). |

- Format: `v<int>` (lowercase `v`, single integer — matches the filename).
- Annotated tags (`git tag -a v9 -m "..."`).
- Each tag corresponds to a `CHANGELOG.md` entry.

```bash
# Example: tagging v9 (current good baseline) on main
git checkout main && git pull
git tag -a v9 -m "v9 — V7 strap choreography + V9 surgical fixes. The current good baseline."
git push origin main --tags
```

---

## Branch → version mapping

| Branch | What it represents | Tagged? |
|---|---|---|
| `main` | The currently-recommended `smile-vN.html`, deployed to GitHub Pages | ✅ `v<N>` |
| `prototype` | Active dev — work on the next iteration here | ❌ |
| `feat/*`, `fix/*` | Inherits from base | ❌ |
| `legacy/v1-python-static` (if/when created) | Frozen v1 Python bridge era | ❌ (frozen) |

---

## Bump rules

| Change type | Bump | Example |
|---|---|---|
| Bug fix that doesn't change behavior visually | Edit the file in place, no version bump | Fix a typo in a comment |
| Surgical fix to the current baseline that preserves V7 choreography | Edit `smile-v9.html` in place, no version bump | V8→V9 fixes (per archive §6) |
| New strap/card state, new ticker cell, new mascot mood | Edit `smile-v9.html` in place, no version bump | Adding a "poll" strap state |
| New design direction (different aesthetic, parallel exploration) | New file with its own lineage | `revolut-overlay-v03.html` |
| Iteration that supersedes the previous baseline | **New file**: `smile-v10.html` | V9 → V10 |
| Architecture change (e.g., adding a build step, removing `_shared.js`) | **New file**: `smile-v10.html` + a `CHANGELOG` entry explaining the architecture shift | |

---

## Anti-patterns (don't do these)

1. **Editing `smile-v9.html` destructively without keeping V7 choreography.** V7 strap + V9 fixes are SACRED. See archive §7-8. If you must change choreography, ship a new file (`smile-v10.html`) and explain in `CHANGELOG.md`.
2. **Version numbers in branch names.** Don't use `feat/v10-foo` or `fix/v11-bar`. Use semantic scopes: `feat/strap-poll-state`, `fix/wire-progress-bar`.
3. **Tagging non-`main` branches.** Only `main` gets release tags.
4. **Creating `overly/`.** It's a typo for `overlay/`. Never use it. If you see it, rename immediately.
5. **Adding a `package.json` "just because".** Only introduce app-semver when there's a real app/library to version (build step, bot, etc.). HTML files don't need it.

---

## When in doubt

- The `smile-vN.html` filename is the version.
- Bump only when a new iteration supersedes the previous one.
- Surgical fixes to the current baseline stay in the current file (no bump).
- New design directions get their own filename lineage.
- See `docs/archive/SMILE-ARCHIVE.md` §10 for the V9 file anatomy (what's in the file, what's sacred, what's editable).

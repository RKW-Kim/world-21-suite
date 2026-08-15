# Branching Strategy

## Branch Model

- **`main`** — production-ready, deploys to GitHub Pages via the `deploy-pages` workflow. Receives version tags (`v9`, `v10`, ...). Protected: PRs only.
- **`prototype`** — active development integration branch (GitFlow `develop` equivalent). Feature branches PR into `prototype`; `prototype` PRs into `main` when stable.
- **`feat/<scope>-<description>`** — feature branches, from `prototype` (preferred) or `main`.
- **`fix/<scope>-<description>`** — bugfix branches.
- **`docs/<topic>`** — documentation-only.
- **`hotfix/<description>`** — emergency fixes, from `main`, merge to main.

> **Note**: do NOT put version numbers in branch names (`feat/v10-foo`, `fix/v11-bar`). Use semantic scopes instead (`feat/strap-poll-state`, `fix/wire-progress-bar`).

## Workflow

```bash
# Sync with prototype
git checkout prototype && git pull

# Start a feature branch
git checkout -b feat/strap-poll-state

# Implement, commit small units
git commit -m "feat(overlay): add poll strap state [Task ID: STRAP-POLL-1]"

# Push and open PR
git push -u origin feat/strap-poll-state
# Open PR: feat/strap-poll-state → prototype
# CI runs html-validate; merge after human review

# When prototype is stable, ship to main:
git checkout main && git pull
git merge prototype
git tag -a v10 -m "v10 — poll strap state, wire-card rotation refinement"
git push origin main --tags
# GitHub Pages auto-deploys
```

## Commit Format

```
<type>(<scope>): <description> [Task ID: <id>]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`

**Scopes:** `overlay`, `ticker`, `strap`, `mascot`, `bg`, `ci`, `docs`, `infra`

Examples:
```
feat(strap): add poll state with staggered mask reveal [Task ID: STRAP-POLL-1]
fix(ticker): wire cell progress bar position [Task ID: FIX-WIRE-3]
docs(archive): add V10 design rationale [Task ID: DOCS-2]
refactor(overlay): extract ticker engine into _shared.js [Task ID: REFACT-2]
ci(validate): tighten html-validate config [Task ID: CI-2]
chore(infra): force overlay/ folder name in CI [Task ID: CHORE-FOLDER-1]
```

## Release Flow

```bash
git checkout main && git pull
# (prototype has already been merged in via PR)
git tag -a v10 -m "v10 — <one-line summary>"
git push origin main --tags
# GitHub Pages auto-deploys via deploy-pages.yml workflow
```

Tags mark milestone iterations of the overlay file lineage. Each tag corresponds to a `CHANGELOG.md` entry. See [`VERSIONING.md`](./VERSIONING.md) for the full versioning policy.

## Multi-AI Coordination

- Each AI works on its own branch.
- Coordinate via the worklog — append the Task ID + branch name BEFORE starting work (so the next AI knows the branch is in flight).
- PRs are the merge point.
- Conflicts resolved on the feature branch (rebase onto latest `prototype` before merging).

## Branch Protection (set on GitHub → Settings → Branches)

### `main`:
- Require PR before merging: ✅
- Require approvals: 1 (the human)
- Require status checks: `html-validate` (the CI workflow)
- Require branches to be up to date: ✅
- Do not allow bypassing: ✅
- Restrict who can push: ✅ (only the human)
- Require linear history (squash + merge): ✅
- No force pushes, no deletions: ✅

### `prototype`:
- Require PR before merging from `feat/*` / `fix/*`: ✅ (keeps history clean).
- Direct pushes by the human (or the AI agent on the human's behalf) are allowed for fast-iteration work — but every push should be a coherent commit.
- No force pushes from `prototype` → `main` direction; rebase + PR only.
- Auto-sync with `main` after `main` updates (rebase `prototype` onto `main`).

### `feat/*`, `fix/*`, `docs/*`:
- No protection — force-push is allowed (so the AI can rewrite history to fix commit authors, squash, or rebase).
- Auto-delete on merge (GitHub setting → "Automatically delete head branches").

## Folder name convention (FORCED)

- ✅ `overlay/` — standalone HTML overlay files (the `smile-vN.html` lineage). Singular.
- ❌ `overly/` — typo. Never create this. If you see it, rename to `overlay/` immediately.
- ✅ `overlay/archive/` — earlier iterations, kept for reference (not deployed to Pages root, but accessible at `/archive/test-2.html` etc.).
- ❌ `overlays/` (plural) — not used in this repo. (In the parallel `smile-live-kit` repo it denoted Next.js React routes; doesn't apply here.)

See [`VERSIONING.md`](./VERSIONING.md) for the full versioning + folder policy.

## The Commit-Author-Email Rule (CRITICAL)

Every commit must be authored by `RKW-Kim <rkw.kim22@gmail.com>`. (Vercel Hobby previews silently 404 for commits authored by unverified emails — and even though we're on GitHub Pages now, keeping the same author keeps `git log` readable.)

```bash
git config user.name "RKW-Kim"
git config user.email "rkw.kim22@gmail.com"
```

Verify before committing:
```bash
git config user.email   # must print: rkw.kim22@gmail.com
```

## The GitHub Token

The git remote URL is configured to use a fine-grained PAT (`github_pat_` prefix), scoped to this repo only (Contents:RW + Pull requests:RW + Issues:RW). Stored in `~/.git-credentials` (chmod 600), never echoed in commands or commit messages.

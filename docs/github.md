# Repository & workflow

## Organisation
`core/` engine (served over localhost), `brands/` looks, `obs/` portable scene collection, `docs/`, `scripts/` + `.github/` CI/build/push. One engine, many channels.

## Branching
`main` = stable core + Smile brand. New work on `feat/`/`fix/` -> PR -> validator must pass. Tag releases (`v1.2.0`). Per-channel experiments on `channel/<name>` touching only a brand pack.

## CI
`.github/workflows/validate.yml` runs `scripts/validate.py` on every push/PR.

## Push (no terminal)
Double-click `push.bat` (runs `scripts/push.py`; a GitHub login window may pop once). Or GitHub Desktop: *File -> Add Local Repository* -> the `smile-live-kit` folder -> Publish.

## Build from scratch
Drop `make-kit.py` + `make-kit.bat` into your existing screens folder and double-click `make-kit.bat` - it assembles the whole structured repo + zip.

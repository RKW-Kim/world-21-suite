#!/usr/bin/env bash
# station/setup.sh — provision one broadcast root (lab laptop or VPS).
#
#   BROADCAST_ROOT=./broadcast bash station/setup.sh     # lab (default)
#   BROADCAST_ROOT=/var/broadcast sudo bash station/setup.sh   # VPS
#
# Creates dirs, a chmod-600 secrets template (never committed), and records the
# Flatpak OBS pin so Arch and Ubuntu run the identical render-plane build.
# Idempotent: safe to re-run. Does NOT start anything.

set -euo pipefail
ROOT="${BROADCAST_ROOT:-./broadcast}"

for bin in ffmpeg ffprobe python3; do
  command -v "$bin" >/dev/null || { echo "::error::$bin missing. Install ffmpeg + python3 first."; exit 1; }
done

mkdir -p "$ROOT"/{media,assets/idents,overlays,backups,recordings} station/manifest
[ -f "$ROOT/media/playlist.json" ] || cp station/playlist.json "$ROOT/media/playlist.json"

if [ ! -f "$ROOT/secrets.env" ]; then
  cat > "$ROOT/secrets.env" <<'EOF'
# Stream key lives HERE ONLY. Never commit. Never show presenters.
YOUTUBE_STREAM_KEY=paste-once-then-chmod-600
OBS_PASS=change-me
TG_TOKEN=
TG_CHAT=
EOF
  chmod 600 "$ROOT/secrets.env"
  echo "wrote $ROOT/secrets.env (mode 600) — fill in YOUTUBE_STREAM_KEY"
fi

# Pin the render-plane build: Arch and Ubuntu must run the same OBS.
if command -v flatpak >/dev/null && flatpak info com.obsproject.Studio >/dev/null 2>&1; then
  {
    echo "{"
    echo "  \"app\": \"com.obsproject.Studio\","
    echo "  \"commit\": \"$(flatpak info --show-commit com.obsproject.Studio)\","
    echo "  \"runtime\": \"$(flatpak info --show-runtime com.obsproject.Studio)\","
    echo "  \"pinned_on\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
  } > station/manifest/flatpak.lock.json
  echo "pinned Flatpak OBS -> station/manifest/flatpak.lock.json"
else
  echo "::warning::Flatpak OBS not found — install com.obsproject.Studio, then re-run to pin it."
fi

echo "OK: broadcast root at $ROOT"
ls -la "$ROOT"

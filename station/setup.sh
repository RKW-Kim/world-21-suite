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

[ -d overlay ] || { echo "::error::run from the repo root (no overlay/ found)."; exit 1; }

for bin in ffmpeg ffprobe python3 curl; do
  command -v "$bin" >/dev/null || { echo "::error::$bin missing. Install ffmpeg + python3 + curl first."; exit 1; }
done

mkdir -p "$ROOT"/{media,assets/idents,overlays,backups,recordings} station/manifest
[ -f "$ROOT/media/playlist.json" ] || cp station/playlist.json "$ROOT/media/playlist.json"

# Firewall: open exactly the SRT ingest ports, nothing else.
# (Lab lesson 2026-10-12: ufw default-DROP silently killed laptop-to-laptop
# SRT while loopback passed and ping lied. Only a two-machine run reveals it.)
if command -v ufw >/dev/null; then
  if sudo ufw allow 9000:9001/udp comment 'station SRT ingest' 2>/dev/null; then
    echo "ufw: opened 9000:9001/udp for SRT ingest"
  else
    echo "::warning::could not open SRT ports via ufw; do it by hand."
  fi
fi

if [ ! -f "$ROOT/secrets.env" ]; then
  cat > "$ROOT/secrets.env" <<'EOF'
# Stream key lives HERE ONLY. Never commit. Never show presenters.
YOUTUBE_STREAM_KEY=paste-once-then-chmod-600
OBS_PASS=change-me
# Discord channel webhook URL for alerts (Server Settings > Integrations > Webhooks).
# No bot to host, no token to rotate. WhatsApp later if ever (needs Twilio/CallMeBot).
DISCORD_WEBHOOK=
EOF
  chmod 600 "$ROOT/secrets.env"
  echo "wrote $ROOT/secrets.env (mode 600) — fill in YOUTUBE_STREAM_KEY"
fi

# Render-plane deps (VPS + headless lab): a virtual display for OBS plus the
# pinned Flatpak build. setup.sh never installs system packages itself — OS
# choices stay visible. Arch: sudo pacman -S xorg-server-xvfb.
command -v Xvfb >/dev/null || echo "::warning::Xvfb missing — headless OBS needs xorg-server-xvfb."

# MediaMTX (ingest bus): pinned static binary, no root needed, never committed.
MTX_VER="v1.21.2"
if [ ! -x station/third_party/mediamtx ]; then
  case "$(uname -s).$(uname -m)" in
    Linux.x86_64)  MTX_OS="linux_amd64" ;;
    Darwin.arm64)  MTX_OS="darwin_arm64" ;;
    Darwin.*)      MTX_OS="darwin_amd64" ;;  # Intel Macs, including the 2013 Air
    *) echo "::error::no MediaMTX asset mapped for $(uname -s)/$(uname -m). Fetch by hand."; exit 1 ;;
  esac
  echo "fetching MediaMTX $MTX_VER ($MTX_OS) ..."
  curl -fSL -o /tmp/mtx.tar.gz \
    "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VER/mediamtx_${MTX_VER#v}_$MTX_OS.tar.gz"
  mkdir -p station/third_party
  tar xzf /tmp/mtx.tar.gz -C station/third_party/ mediamtx
  rm -f /tmp/mtx.tar.gz
fi
echo "mediamtx: $(station/third_party/mediamtx --version 2>/dev/null || echo MISSING)"
echo "run it: ./station/third_party/mediamtx station/mediamtx.yml  (SRT :9000, API loopback :9997)"
# Pin the render-plane build: Arch and Ubuntu must run the same OBS.
if command -v flatpak >/dev/null && flatpak info com.obsproject.Studio >/dev/null 2>&1; then
  NEW_COMMIT="$(flatpak info --show-commit com.obsproject.Studio)"
  OLD_COMMIT="$(python3 -c "import json;print(json.load(open('station/manifest/flatpak.lock.json')).get('commit',''))" 2>/dev/null)"
  if [ "$NEW_COMMIT" != "$OLD_COMMIT" ]; then
    {
    echo "{"
    echo "  \"app\": \"com.obsproject.Studio\","
    echo "  \"commit\": \"$NEW_COMMIT\","
    echo "  \"runtime\": \"$(flatpak info --show-runtime com.obsproject.Studio)\","
    echo "  \"pinned_on\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
    } > station/manifest/flatpak.lock.json
    echo "pinned Flatpak OBS -> station/manifest/flatpak.lock.json"
  else
    echo "Flatpak pin unchanged ($NEW_COMMIT)"
  fi
else
  echo "::warning::Flatpak OBS not found — install com.obsproject.Studio, then re-run to pin it."
fi

echo "OK: broadcast root at $ROOT"
ls -la "$ROOT"

# Scene collection from template (env-driven paths, fresh UUIDs, validated).
# LAB_LIGHT=1 renders SMILE-Lab without browser sources for weak lab boxes.
if [ -n "${LAB_LIGHT:-}" ]; then
  python3 station/render_scenes.py --root "$ROOT" --light --name SMILE-Lab
else
  python3 station/render_scenes.py --root "$ROOT"
fi

# System services: the station autostarts or it isn't a station. Installs the
# units (rewritten to THIS checkout's path, so a VPS clone anywhere works),
# enables autostart, reloads. Does NOT start obs/daemon: the operator starts
# those deliberately after verifying secrets + media (see docs/VPS.md).
# (Lab lesson: an unsupervised reboot with manual-only processes is a total
# silent outage. This block exists because of one.)
UNIT_SRC="station/systemd"
if [ "$(id -u)" = "0" ]; then
  UNIT_DST="/etc/systemd/system"; SYS="systemctl"
else
  UNIT_DST="$HOME/.config/systemd/user"; SYS="systemctl --user"
fi
mkdir -p "$UNIT_DST"
for u in "$UNIT_SRC"/station-*.service; do
  sed "s|%h/Documents/GitHub/world-21-suite|$PWD|g" "$u" > "$UNIT_DST/$(basename "$u")"
done
$SYS daemon-reload
# shellcheck disable=SC2046
$SYS enable $(cd "$UNIT_SRC" && ls station-*.service) 2>&1 | tail -n 2
if [ "$(id -u)" != "0" ]; then
  if [ "$(loginctl show-user "$USER" 2>/dev/null | grep -c Linger=yes)" = "0" ]; then
    echo "::warning::linger is OFF — user units die at logout and autostart can't work."
    echo "  Run once with sudo: sudo loginctl enable-linger $USER"
  fi
fi

cat <<'EOF'

OBS profile checklist (set once in the GUI; profiles can't be safely templated):
  Output 1920x1080, 30fps | x264 superfast CBR 6000k | keyframe 2s | AAC 128k
  websocket server on 127.0.0.1:4455 with password (= OBS_PASS in secrets.env)
  Load scene collection: broadcast/scenes/SMILE-Station.json
EOF

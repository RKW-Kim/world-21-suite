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

for bin in ffmpeg ffprobe python3 curl yt-dlp; do
  command -v "$bin" >/dev/null || { echo "::error::$bin missing. Install ffmpeg + python3 + curl first."; exit 1; }
done

mkdir -p "$ROOT"/{media,assets/idents,overlays,backups,recordings} station/manifest
# Absolute, so the unit can point at the same file wherever BROADCAST_ROOT
# lives (the VPS install uses /var/broadcast).
ROOT="$(cd "$ROOT" && pwd)"
[ -f "$ROOT/media/playlist.json" ] || cp station/playlist.json "$ROOT/media/playlist.json"

# Firewall: default-deny incoming; SSH always; contribution-seat ports
# ONLY for the seat networks the operator names. (Lab lesson 2026-10-12:
# ufw default-DROP silently killed laptop-to-laptop SRT while loopback
# passed and ping lied. Only a two-machine run reveals it.)
#
#   bash station/setup.sh --seat 192.168.1.0/24 --seat 203.0.113.7/32
#
# Before 2026-10-21 this opened 9000:9001/udp to the WHOLE internet -- with
# no mediamtx auth, anyone could publish slot-cam and inject on air. Auth
# now lives in mediamtx.yml (authInternalUsers, passes in secrets.env), so
# the firewall adds SOURCE RESTRICTION on top: a seat network is opened
# deliberately, per protocol, or not at all.
SEAT_NETS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --seat) SEAT_NETS="$SEAT_NETS ${2:-}"; shift; [ $# -gt 0 ] && shift || true ;;
    *) shift ;;
  esac
done
if command -v ufw >/dev/null; then
  # mediamtx.yml states the model: "UFW allows only 22/tcp". Allowing a
  # port is not a policy: without default-deny incoming, everything else
  # (the overlay control plane on 7070) stays reachable.
  sudo ufw default deny incoming 2>/dev/null || true
  sudo ufw allow 22/tcp comment 'ssh' 2>/dev/null || true
  for net in $SEAT_NETS; do
    sudo ufw allow from "$net" to any port 9000 proto udp comment 'station SRT ingest (seat)' 2>/dev/null || true
    sudo ufw allow from "$net" to any port 8889 proto tcp comment 'station WHIP (seat)' 2>/dev/null || true
    sudo ufw allow from "$net" to any port 8189 proto udp comment 'station WebRTC ICE mux (seat)' 2>/dev/null || true
    echo "ufw: seat network $net -> SRT 9000/udp, WHIP 8889/tcp, ICE 8189/udp"
  done
  if [ -z "$SEAT_NETS" ]; then
    echo "ufw: no --seat networks given: seats stay OFF the WAN (loopback + tunnels only)."
  fi
  sudo ufw --force enable 2>/dev/null || true
  sudo ufw status numbered 2>/dev/null | sed -n '1,12p'
else
  [ -n "$SEAT_NETS" ] && echo "::warning::ufw not present; open seat ports by hand for:$SEAT_NETS"
fi

if [ ! -f "$ROOT/secrets.env" ]; then
  cat > "$ROOT/secrets.env" <<'EOF'
# Stream key lives HERE ONLY. Never commit. Never show presenters.
YOUTUBE_STREAM_KEY=paste-once-then-chmod-600
OBS_PASS=change-me
# Discord channel webhook URL for alerts (Server Settings > Integrations > Webhooks).
# No bot to host, no token to rotate. WhatsApp later if ever (needs Twilio/CallMeBot).
DISCORD_WEBHOOK=
# Contribution-seat credentials (mediamtx authInternalUsers). One seat per
# path; publish-only. SRT streamid: publish:<path>:<user>:<pass>
EOF
  for s in CAM SCREEN AUDIO AD; do
    P="$(openssl rand -hex 16 2>/dev/null || head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    echo "SEAT_${s}_PASS=$P" >> "$ROOT/secrets.env"
  done
  echo "wrote $ROOT/secrets.env (seat passes generated) — fill in YOUTUBE_STREAM_KEY"
else
  # Idempotent upgrade: an older secrets.env predates the seat passes.
  # mediamtx.yml expands ${SEAT_*_PASS}; an unset var becomes an EMPTY
  # password, which would accept an empty credential -- so every missing
  # seat pass is generated once, here.
  for s in CAM SCREEN AUDIO AD; do
    if ! grep -q "^SEAT_${s}_PASS=" "$ROOT/secrets.env"; then
      P="$(openssl rand -hex 16 2>/dev/null || head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
      echo "SEAT_${s}_PASS=$P" >> "$ROOT/secrets.env"
      echo "generated SEAT_${s}_PASS (was missing)"
    fi
  done
fi
# Always, not only on creation: a hand-made or restored secrets file kept
# mode 644 and the stream key stayed world-readable.
chmod 600 "$ROOT/secrets.env" 2>/dev/null || true

# Render the mediamtx config with the real seat passes. The repo file is a
# template: mediamtx does NOT expand environment variables inside the YAML
# (proved 2026-10-21 — the literal "${SEAT_CAM_PASS}" became the password),
# so the passes are substituted HERE, at provision time, into a 600-mode
# file the mediamtx unit runs. This is also the plugin's one good lifecycle
# habit adopted wholesale: the config is regenerated on every setup run, so
# a drifted or hand-edited render self-heals on the next provision.
set -a; . "$ROOT/secrets.env"; set +a
sed -e "s|\${SEAT_CAM_PASS}|${SEAT_CAM_PASS:-}|g" \
    -e "s|\${SEAT_SCREEN_PASS}|${SEAT_SCREEN_PASS:-}|g" \
    -e "s|\${SEAT_AUDIO_PASS}|${SEAT_AUDIO_PASS:-}|g" \
    -e "s|\${SEAT_AD_PASS}|${SEAT_AD_PASS:-}|g" \
    station/mediamtx.yml > "$ROOT/mediamtx.yml"
if grep -q '\${SEAT_' "$ROOT/mediamtx.yml"; then
  echo "::error::rendered mediamtx.yml still has placeholder passes — secrets.env is missing entries." >&2
  exit 1
fi
chmod 600 "$ROOT/mediamtx.yml"
echo "rendered mediamtx config -> $ROOT/mediamtx.yml (600)"

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
  # Release assets carry the v in the filename (mediamtx_v1.21.2_linux_amd64);
  # the stripped form 404s (seen 2026-10-21 against the v1.21.2 release).
  curl -fSL -o /tmp/mtx.tar.gz \
    "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VER/mediamtx_${MTX_VER}_$MTX_OS.tar.gz"
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

# Headless render-plane config (root-caused 2026-10-15, lab outage 05:52-09:20):
# BrowserHWAccel MUST be false. With it true, CEF's GPU process dies under
# Xvfb/software-GL ("FATAL: GPU process isn't usable. Goodbye.") and takes the
# whole main OBS process down ~30s after boot, every boot. Software CEF
# renders all 7 overlay pages fine and costs one sed.
# The old guard only touched files that ALREADY existed — which skipped
# exactly the boot that needs it: a fresh box has no global.ini until OBS's
# first run, so its first boot ran with hardware CEF and died on schedule.
# Now the minimal file is created; OBS merges its own keys around it.
for g in "$HOME/.var/app/com.obsproject.Studio/config/obs-studio/global.ini" \
         "$HOME/.config/obs-studio/global.ini"; do
  if [ ! -f "$g" ]; then
    mkdir -p "$(dirname "$g")"
    printf '[General]\nBrowserHWAccel=false\n' > "$g"
    echo "BrowserHWAccel=false written (new file) in $g"
  elif grep -q '^BrowserHWAccel=' "$g"; then
    sed -i 's/^BrowserHWAccel=.*/BrowserHWAccel=false/' "$g"
    echo "BrowserHWAccel=false enforced in $g"
  else
    printf '\nBrowserHWAccel=false\n' >> "$g"
    echo "BrowserHWAccel=false appended in $g"
  fi
done

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
# Box shape, decided BEFORE the install loop: it decides which units belong
# on this box at all (see the render block below for the display/GL render).
PLANE_GPU=no;     ls /dev/dri/renderD* >/dev/null 2>&1 && PLANE_GPU=yes
PLANE_SESSION=no; ls /tmp/.X11-unix/X* >/dev/null 2>&1 && PLANE_SESSION=yes
# wayvnc mirrors the user's Wayland session; on a headless box there is none
# and the unit would crash-loop forever (the monitor-av class of debt: 11k
# restarts doing nothing). Skip it there; the headless TD-desk recipe is
# x11vnc on the Xvfb display (docs/VPS.md §6).
SKIP_VNC=no; [ "$PLANE_SESSION" = no ] && SKIP_VNC=yes
for u in "$UNIT_SRC"/station-*.service; do
  case "$u" in
    *monitor-av*) continue ;;   # dead path (mediamtx dropped it 2026-10-18)
    *station-vnc*) [ "$SKIP_VNC" = yes ] && { echo "station-vnc: skipped (headless box, no Wayland session to mirror)"; continue; } ;;
  esac
  # The unit has to point at THIS install: the repo path, the secrets
  # file and the media root all move together (the VPS install lives in
  # /var/broadcast, not in the repo).
  sed -e "s|%h/Documents/GitHub/world-21-suite|$PWD|g" \
      -e "s|/home/rkw/Documents/GitHub/world-21-suite|$PWD|g" \
      -e "s|EnvironmentFile=.*|EnvironmentFile=$ROOT/secrets.env|" \
      "$u" > "$UNIT_DST/$(basename "$u")"
  # Every unit gets the media root, not just the daemon: panel, overlay
  # and watchdog honor BROADCAST_ROOT too. One unit left on the repo tree
  # meant a /var/broadcast daemon playing state the others couldn't see.
  grep -q "^Environment=BROADCAST_ROOT=" "$UNIT_DST/$(basename "$u")" || \
    sed -i "s|^Environment=|Environment=BROADCAST_ROOT=$ROOT\nEnvironment=|" \
      "$UNIT_DST/$(basename "$u")"
done
# Render the OBS unit for THIS box. The unit in git is the lab shape: a real
# X session on :0 with hardware GL. A GPU-less headless box (the VPS) boots a
# different plane: Xvfb :99 + llvmpipe. Rendered at provision time like the
# mediamtx config above, so a re-run self-heals a drifted or hand-edited unit.
# (Box shape was detected before the install loop; every setup.sh run starts
# the unit from the pristine git copy, so the render never compounds.)
#   session := any X socket exists (XWayland on the lab desktop creates X0)
#   gpu     := a DRM render node exists (/dev/dri/renderD*)
# A :1-only session (no X0) reads as headless -> safe-but-slower Xvfb plane;
# re-run setup.sh inside the session to re-render. Detection runs at install
# time on purpose: a VPS will never grow a GPU, and a desktop install runs
# setup.sh logged into the session it will air from.
OBS_UNIT="$UNIT_DST/station-obs.service"
if [ "$PLANE_SESSION" = yes ] && [ "$PLANE_GPU" = yes ]; then
  echo "render plane: real session :0, hardware GL (as shipped)"
else
  # LIBGL_ALWAYS_SOFTWARE: 2026-10-20 it was stripped because on the lab iGPU
  # it chained the plane to llvmpipe and burned 2x realtime CPU. On a box
  # with no GPU driver that trade does not exist — without the flag OBS may
  # fail to create a GLX context at all. Xvfb cannot host hardware GLX
  # anyway, so headless means software GL, full stop.
  # (Guarded insert: the flag must never compound if a future flow renders
  # without the install-loop reset ahead of it.)
  if ! grep -q -- '--env=LIBGL_ALWAYS_SOFTWARE=1' "$OBS_UNIT"; then
    sed -i 's| com.obsproject.Studio --verbose| --env=LIBGL_ALWAYS_SOFTWARE=1 com.obsproject.Studio --verbose|' "$OBS_UNIT"
  fi
  if [ "$PLANE_SESSION" = yes ]; then
    echo "render plane: session :0 but NO GPU driver -> LIBGL_ALWAYS_SOFTWARE=1"
  else
    sed -i -e 's|--env=DISPLAY=:0|--env=DISPLAY=:99|' \
           -e 's|--env=PLANE_DISPLAY=:0|--env=PLANE_DISPLAY=:99|' \
           -e 's|^Environment=DISPLAY=:0|Environment=DISPLAY=:99|' \
           -e 's|^Environment=PLANE_DISPLAY=:0|Environment=PLANE_DISPLAY=:99|' \
           "$OBS_UNIT"
    echo "render plane: headless -> Xvfb :99 + LIBGL_ALWAYS_SOFTWARE=1"
  fi
  # The render edits exact strings from the unit file. A future unit edit
  # that renames one of them must fail LOUD here — not silently boot a :0
  # plane on a box with no :0, which is the wedge this render exists to
  # prevent (and the failure mode a quiet sed would produce).
  grep -q -- '--env=LIBGL_ALWAYS_SOFTWARE=1' "$OBS_UNIT" || {
    echo "::error::station-obs.service render failed: LIBGL flag not planted — the unit text no longer matches the sed." >&2; exit 1
  }
  if [ "$PLANE_SESSION" = no ] && ! grep -q -- '--env=DISPLAY=:99' "$OBS_UNIT"; then
    echo "::error::station-obs.service render failed: display not moved to :99 — the unit text no longer matches the sed." >&2; exit 1
  fi
fi

$SYS daemon-reload
# The publish leg is NOT enabled here: it goes live on YouTube the moment
# a real stream key lands in secrets.env, so arming it in setup.sh turned
# provisioning into an accidental broadcast (docs/OPERATIONS.md). Enable
# it deliberately once the key is real.
# shellcheck disable=SC2046
$SYS enable $(cd "$UNIT_SRC" && ls station-*.service | grep -v -e monitor-av -e station-publish \
              $([ "$SKIP_VNC" = yes ] && echo -e station-vnc)) \
            station-watchdog.timer 2>&1 | tail -n 2
if [ "$(id -u)" != "0" ]; then
  if [ "$(loginctl show-user "$USER" 2>/dev/null | grep -c Linger=yes)" = "0" ]; then
    echo "::warning::linger is OFF — user units die at logout and autostart can't work."
    echo "  Run once with sudo: sudo loginctl enable-linger $USER"
  fi
fi

cat <<'EOF'

OBS profile checklist (set once in the GUI; profiles can't be safely templated):
EOF
# The checklist numbers are READ from the config tree, not restated here:
# two places that can disagree is how "1080p/6000k" and "540p/2500k" both
# ended up written down as the truth. The config tree is the source.
python3 - <<'PYEOF'
import json, os
try:
    v = json.load(open("station/config/video.json"))
    e = json.load(open("station/config/encoder.json")).get("streamEncoder.json", {})
    out = "%dx%d @%sfps" % (v.get("outputWidth", "?"), v.get("outputHeight", "?"),
                            v.get("fpsNumerator", "?"))
    enc = "x264 %s CBR %sk, keyint %ss" % (e.get("preset", "?"),
                                           e.get("bitrate", "?"), e.get("keyint_sec", "?"))
    print("  Output %s | %s" % (out, enc))
    print("  (canvas %dx%d; change station/config/video.json + encoder.json to move)" %
          (v.get("baseWidth", "?"), v.get("baseHeight", "?")))
except Exception as ex:
    print("  (config unreadable: %s — set Output/encoder by hand, then sync.py capture)" % ex)
PYEOF
cat <<'EOF'
  websocket server on 127.0.0.1:4455 with password (= OBS_PASS in secrets.env)
  Load scene collection: broadcast/scenes/SMILE-Station.json
EOF

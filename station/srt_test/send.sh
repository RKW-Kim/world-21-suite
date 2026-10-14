#!/usr/bin/env bash
# station/srt_test/send.sh — emit raw contribution feeds over SRT.
# The laptop is a sensor array, not a studio: no scenes, no overlays, no key.
#
#   station/srt_test/send.sh --test RECEIVER            # synthetic bars+tone, no hardware
#   station/srt_test/send.sh --cam RECEIVER             # /dev/video0 + mic, muxed (keeps lip-sync)
#   station/srt_test/send.sh --cam --screen RECEIVER    # + screen as a second feed (X11 only)
#
# RECEIVER = bus host (VPS, or this box proving it). One SRT port (:9000);
# --latency MS  retransmit budget (default 800; raise on bad wifi, costs delay)
# --record DIR  also save a local tape alongside the push (brownout insurance)
#
# Works on Linux and macOS (avfoundation). NOTE: the macOS branch is written
# against ffmpeg/avfoundation docs, untested on this Linux box — first MBA run
# is the test. Env knobs for weak machines
# (e.g. a 2013 laptop): SIZE=640x480 PRESET=ultrafast VBITRATE=1000k
#
# On the other laptop, run: station/srt_test/receive.sh [--sample 15]

set -euo pipefail
OS="$(uname -s)"
SIZE="${SIZE:-1280x720}"
if [ -z "${PRESET:-}" ]; then
  if [ "$OS" = "Darwin" ]; then PRESET="ultrafast"; else PRESET="veryfast"; fi
fi
VBITRATE="${VBITRATE:-1500k}"

set -euo pipefail
MODE=""; SCREEN=0; HOST=""; LATENCY=800000; RECORD=""

while [ $# -gt 0 ]; do
  case "$1" in
    --test|--cam) MODE="$1"; shift ;;
    --screen) SCREEN=1; shift ;;
    --latency) LATENCY="$2"; shift 2 ;;
    --record) RECORD="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) HOST="$1"; shift ;;
  esac
done
[ -n "$MODE" ] && [ -n "$HOST" ] || { echo "usage: $0 [--test|--cam] [--screen] [--latency MS] [--record DIR] RECEIVER"; exit 1; }
ffmpeg -hide_banner -protocols 2>/dev/null | grep -qw srt \
  || { echo "::error::this ffmpeg build has no SRT support (no libsrt)."; echo "  macOS brew: check 'brew info ffmpeg'; or send via OBS instead (see WORKLOG)."; exit 1; }

tee_out() { # $1 = srt url. tee always needs an explicit format (no extension to guess from).
  if [ -n "$RECORD" ]; then
    mkdir -p "$RECORD"
    echo "[f=mpegts]$1|[f=mp4]$RECORD/tape_$(date +%Y%m%d_%H%M%S).mp4"
  else
    echo "[f=mpegts]$1"
  fi
}

AV_URL="srt://$HOST:9000?streamid=publish:slot-cam&latency=$LATENCY"
echo "== pushing cam+mic to $AV_URL (latency budget $((LATENCY/1000))ms) =="

if [ "$MODE" = "--test" ]; then
  # Synthetic proof: needs no camera, no mic, no screen. If this arrives,
  # the network path works and the VPS will work — same protocol, same ports.
  # NOTE: ffmpeg 9's tee muxer needs explicit -map (auto-map doesn't propagate).
  ffmpeg -hide_banner -loglevel warning \
    -f lavfi -i "testsrc2=size=${SIZE}:rate=30" \
    -f lavfi -i "sine=frequency=440:sample_rate=48000" \
    -map 0:v -map 1:a \
    -c:v libx264 -preset "$PRESET" -tune zerolatency -b:v "$VBITRATE" \
    -c:a aac -b:a 128k -f tee "$(tee_out "$AV_URL")"
elif [ "$OS" = "Darwin" ]; then
  # macOS: camera+mic via avfoundation (one device each, muxed for lip-sync).
  # List devices first: ffmpeg -f avfoundation -list_devices true -i ""
  # Env: CAM=0 MIC=0 (device indices).
  CAM="${CAM:-0}"; MIC="${MIC:-0}"
  ffmpeg -hide_banner -loglevel warning \
    -f avfoundation -framerate 30 -video_size "$SIZE" -i "${CAM}:${MIC}" \
    -map 0:v -map 0:a \
    -c:v libx264 -preset "$PRESET" -tune zerolatency -b:v "$VBITRATE" \
    -c:a aac -b:a 96k -f tee "$(tee_out "$AV_URL")"
else
  [ -e /dev/video0 ] || { echo "::error::no /dev/video0. Use --test, or plug in a camera."; exit 1; }
  MIC="-f alsa -i default"
  ffmpeg -hide_banner -loglevel warning -f pulse -i default 2>/dev/null \
    && MIC="-f pulse -i default" || true
  ffmpeg -hide_banner -loglevel warning \
    -f v4l2 -framerate 30 -video_size "$SIZE" -i /dev/video0 \
    $MIC \
    -map 0:v -map 1:a \
    -c:v libx264 -preset "$PRESET" -tune zerolatency -b:v 2500k \
    -c:a aac -b:a 128k -f tee "$(tee_out "$AV_URL")"
fi &

if [ "$SCREEN" = "1" ]; then
  if [ "$OS" = "Darwin" ]; then
    # macOS screen = an avfoundation video device ("Capture screen 0").
    # Env: SCR=<screen-device-index> (see -list_devices). Audio: none (silent
    # slides) or mux system audio by pointing MIC at a loopback and merging —
    # out of scope for the proof run; see debrief edge case 2.
    SCR="${SCR:-1}"
    echo "== pushing screen to bus slot-screen (separate feed, no sync tie to face) =="
    ffmpeg -hide_banner -loglevel warning \
      -f avfoundation -framerate 30 -i "$SCR" \
      -map 0:v -vf "scale=1280:-2" \
      -c:v libx264 -preset "$PRESET" -tune zerolatency -b:v "$VBITRATE" \
      -f mpegts "srt://$HOST:9000?streamid=publish:slot-screen&latency=$LATENCY" &
  elif [ "${XDG_SESSION_TYPE:-}" != "x11" ] && [ -z "${DISPLAY:-}" ]; then
    echo "::warning::screen capture needs X11 (this box is ${XDG_SESSION_TYPE:-unknown})."
    echo "  On Wayland: share the screen from OBS on this laptop, or skip --screen."
    echo "  Cam+mic feed above is unaffected."
  else
    sleep 1
    echo "== pushing screen to bus slot-screen (separate feed, no sync tie to face) =="
    ffmpeg -hide_banner -loglevel warning \
      -f x11grab -framerate 30 -video_size 1920x1080 -i "${DISPLAY:-:0}.0+0,0" \
      -c:v libx264 -preset veryfast -tune zerolatency -b:v 3000k \
      -f mpegts "srt://$HOST:9000?streamid=publish:slot-screen&latency=$LATENCY" &
  fi
fi
wait

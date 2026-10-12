#!/usr/bin/env bash
# station/srt_test/receive.sh — catch SRT feeds on the "VPS" side.
# For the laptop-to-laptop proof, THIS side stands in for the VPS:
# if cam+mic arrive here intact, they will arrive on the VPS identically.
#
#   station/srt_test/receive.sh                 # watch both feeds (ffplay windows)
#   station/srt_test/receive.sh --sample 15     # record 15s, verify A+V, print PASS/FAIL
#
# --latency MS  must be >= the sender's budget; the effective window is the
# maximum of both ends, so a sender-side raise alone changes nothing.
#
# Listens: :9000 = host_av (cam+mic), :9001 = host_screen.

set -euo pipefail
SAMPLE=0; LATENCY=800000
while [ $# -gt 0 ]; do
  case "$1" in
    --sample) SAMPLE="${2:-15}"; shift 2 ;;
    --latency) LATENCY="$2"; shift 2 ;;
    *) shift ;;
  esac
done

listen() { # $1 port, $2 label
  echo "== listening :$1 ($2) =="
  if [ "$SAMPLE" -gt 0 ]; then
    OUT="/tmp/srt_sample_$1.mp4"
    # Sample mode: ONE listener only — two processes cannot bind one port.
    # Records, then verifies streams. This is the VPS-will-work proof.
    timeout "$((SAMPLE+2))" ffmpeg -hide_banner -loglevel error -y \
      -i "srt://:$1?mode=listener&latency=$LATENCY" -t "$SAMPLE" -c copy "$OUT"
    if [ -f "$OUT" ]; then
      echo "--- $2: $(ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$OUT")"
      ffprobe -v error -show_entries stream=codec_type,codec_name,width,height \
        -of csv=p=0 "$OUT" | sed 's/^/    stream: /'
    else
      echo "--- $2: NO DATA (sender not pushing? firewall?)"
    fi
  else
    ffplay -hide_banner -loglevel error -window_title "SRT $2 (:$1)" \
      "srt://:$1?mode=listener&latency=$LATENCY"
  fi
}

if [ "$SAMPLE" -gt 0 ]; then
  echo "TIP: start the sender first, then run this within a few seconds."
  listen 9000 "host_av cam+mic"
else
  listen 9000 "host_av cam+mic" &
  listen 9001 "host_screen" &
  wait
fi

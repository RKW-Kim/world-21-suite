#!/bin/bash
# Push a fresh YouTube cookies.txt from an operator device to the station.
# The daemon reads the cookie FILE on every resolve, so replacing the file
# updates playout immediately — no daemon restart, no OBS restart.
#
# Where: run this on the machine you're signed into YouTube on (your MBA,
# where Meet already has you logged in). Export cookies once per expires:
# a "Get cookies.txt LOCALLY"-style browser extension writes the file; keep
# it somewhere predictable like ~/Documents/yt-cookies.txt.
#
# Usage:
#  CookiesPushUrl defaults come from station/secrets.env on the station if
#   you don't want them in shell history:
#     ./cookies_push.sh [[user@]host] [cookies_path]
#   STATION=<host> COOKIES=<path> ./cookies_push.sh
#
# What it does: scp the file up as .new, resolve-probe THROUGH the daemon
# host (yt-dlp is installed there), then swap atomically. Old file becomes
# cookies.txt.bak (one deep, self-healing).
set -euo pipefail
STATION="${1:-${STATION:-}}"
COOKIES="${2:-${COOKIES:-$HOME/Documents/yt-cookies.txt}}"
[ -n "$STATION" ] || { echo "usage: $0 [user@]stationHost [cookies.txt]" >&2; exit 2; }
[ -r "$COOKIES" ] || { echo "no cookies file at $COOKIES — export one first" >&2; exit 2; }
head -2 "$COOKIES" | grep -q "# Netscape" || { echo "not a Netscape cookies export" >&2; exit 2; }

REMOTE_DIR=~/broadcast   # matches the service deployment layout
scp -q "$COOKIES" "$STATION:$REMOTE_DIR/.cookies.new"
ssh "$STATION" bash -s <<'EOF'
set -e
cd ~/broadcast
test -s .cookies.new || { echo "upload empty" >&2; exit 1; }
# probe: resolve a short public video using ONLY the new cookies
env YTDLP_COOKIES="$PWD/.cookies.new" \
  yt-dlp --skip-download --print "%(title)s" --no-warnings \
  "https://www.youtube.com/watch?v=aqz-KE-bpKQ" >/dev/null 2>&1 \
  || { echo "probe: YouTube still rejects us — check the file" >&2; exit 1; }
[ -f cookies.txt ] && mv -f cookies.txt cookies.txt.bak
mv -f .cookies.new cookies.txt
chmod 600 cookies.txt cookies.txt.bak 2>/dev/null || true
echo "cookies swapped. no restart needed."
EOF
echo "done: $COOKIES -> $STATION is live."
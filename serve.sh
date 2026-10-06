#!/bin/sh
# Serve the overlay over http so YouTube embeds work.
#
# WHY THIS EXISTS. A page opened as file:// cannot embed a YouTube player. There
# is no referrer to send, so the player refuses to start and answers "Error
# 153". Firefox and LibreWolf enforce this; desktop Chromium happens to tolerate
# it, which makes the problem look browser-specific when it is not — it is the
# protocol. Serving the folder gives the page a real http origin and the embed
# works.
#
#   ./serve.sh          port 8017
#   ./serve.sh 9000     a different port
#
# Then open the address it prints. Nothing is installed; this is python3's
# built-in server, serving one directory read-only.

set -e
DIR="$(cd "$(dirname "$0")/overlay" && pwd)"
PORT="${1:-8017}"

cat <<TXT
  Smile overlay → http://127.0.0.1:$PORT/

  open that address instead of the file path. It has to be http for YouTube
  embeds to run; everything else in the kit works either way.

  ctrl-c to stop.
TXT

cd "$DIR"
exec python3 -m http.server "$PORT" --bind 127.0.0.1

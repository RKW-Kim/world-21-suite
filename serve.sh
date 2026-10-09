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
#
# WHY IT IS NOT JUST python3 -m http.server. That server sends Last-Modified and
# answers a conditional request with 304 Not Modified, so a scene you just fixed
# keeps running the copy the browser decided to keep. It looks like the edit did
# not take -- you change the markup, reload, and the old roll is still there.
# The handler below keeps the same directory listing and the same read-only
# serving, and adds headers that say the answer may not be reused.

set -e
DIR="$(cd "$(dirname "$0")/overlay" && pwd)"
PORT="${1:-8017}"

cat <<TXT
  Smile overlay → http://127.0.0.1:$PORT/

  open that address instead of the file path. It has to be http for YouTube
  embeds to run; everything else in the kit works either way.

  served no-cache: reload and you get the file as it is on disk right now.

  ctrl-c to stop.
TXT

cd "$DIR"

# The cache headers are per-response, and http.server has no flag for them, so
# this subclasses the handler rather than replacing the server.
exec python3 - "$PORT" <<'PY'
import sys, functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class NoCache(SimpleHTTPRequestHandler):
    """A static file server that refuses to let anything be reused.

    no-store and no-cache together are the pair browsers actually honour:
    no-store says do not keep it at all, no-cache says if you do, check first.
    max-age=0 plus must-revalidate closes the door on the fresh-copy heuristic,
    and the two legacy headers are there for the older engines that ignore
    Cache-Control entirely.
    """

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # The scene files are edited in place, so a byte-range or a stale ETag
        # reopening an old window is the same bug wearing a different hat.
        self.send_header("Clear-Site-Data", '"cache"')
        super().end_headers()

    def send_head(self):
        # This is the half that actually matters. SimpleHTTPRequestHandler answers
        # If-Modified-Since with 304 before it ever emits a header, so dropping
        # Last-Modified on its own changes nothing -- the browser still gets told
        # "your copy is current" and no body comes back. Taking the validators off
        # the request first means the handler takes the 200 path and always sends
        # the file it just read.
        for hdr in ("If-Modified-Since", "If-None-Match", "If-Range"):
            del self.headers[hdr]
        return super().send_head()

    def log_message(self, fmt, *args):
        # The one line that matters is a reload of a scene; the rest is noise.
        if "GET" in (fmt % args):
            print("  %s" % (fmt % args))

port = int(sys.argv[1])
handler = functools.partial(NoCache, directory=".")
print("  serving %s on 127.0.0.1:%d — no-cache" % (".", port), flush=True)
try:
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
except KeyboardInterrupt:
    print("\n  stopped.")
PY

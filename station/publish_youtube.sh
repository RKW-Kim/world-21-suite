#!/usr/bin/env bash
# Publish the finished programme to YouTube.
#
# Chain: OBS (programme out) -> rtmp://127.0.0.1:1935/monitor -> here ->
# YouTube's RTMP endpoint. The key comes from broadcast/secrets.env
# (YOUTUBE_STREAM_KEY). If the key is still the placeholder, this exits
# instead of publishing: the station must never go live by accident.
#
# OFF by default. Enable the unit only when the key is real and you want
# the station to publish:
#     sudo systemctl enable --now station-publish.service
set -euo pipefail

ROOT="${BROADCAST_ROOT:-$(cd "$(dirname "$0")/.." && pwd)/broadcast}"
SECRETS="$ROOT/secrets.env"
SRC="${PUBLISH_SRC:-rtmp://127.0.0.1:1935/monitor}"
# The destination is overridable so the leg can be proven against a local
# sink instead of YouTube. The key guard below still applies to the real
# YouTube endpoint: the station must never go live by accident.
DEST="${PUBLISH_DEST:-rtmp://a.rtmp.youtube.com/live2}"

[ -f "$SECRETS" ] || { echo "no $SECRETS — nothing to publish with"; exit 1; }
# shellcheck disable=SC1090
KEY="$(grep -E '^YOUTUBE_STREAM_KEY=' "$SECRETS" | head -1 | cut -d= -f2- | tr -d '"'"'"' \r\n')"
case "$KEY" in
  ""|paste-once-then-chmod-600|change-me)
    case "$DEST" in
      rtmp://a.rtmp.youtube.com/*)
        echo "YOUTUBE_STREAM_KEY is still the placeholder — not publishing."; exit 1 ;;
      *)
        # A destination the operator chose (a test sink): no key needed.
        : ;;
    esac
    ;;
esac

echo "publishing $SRC -> $DEST (key …${KEY: -4})"
# -c copy: the programme is already encoded; re-encoding would only lose
# quality. -f flv: what YouTube's RTMP endpoint speaks.
exec ffmpeg -hide_banner -loglevel warning -nostdin \
  -i "$SRC" -c copy -f flv "${DEST}/${KEY}"

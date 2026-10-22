#!/usr/bin/env bash
# station/selftest.sh — the whole stdlib suite, one command.
#
#   bash station/selftest.sh
#
# Every proof-bearing change runs this. The list IS the suite: a new test
# file must be added here in the same commit that adds it, or it does not
# exist as far as the next agent is concerned (that is how
# test_control_consume and test_overlay_auth went missing from the
# verify lists — each doc listed a subset, and the subsets drifted).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
fails=0
for t in test_spool test_fallback test_playlist_edges test_stream_respawn \
         test_control_consume test_overlay_auth test_plane_guard \
         test_unit_render test_sync_guard test_intake_sweep \
         test_resolve_hold test_playlist_robustness; do
  if python3 "$HERE/$t.py" > "/tmp/station-$t.log" 2>&1; then
    echo "PASS $t"
  else
    echo "FAIL $t (tail below)"
    tail -8 "/tmp/station-$t.log"
    fails=$((fails + 1))
  fi
done
if python3 "$HERE/daemon.py" selftest > /tmp/station-selftest.log 2>&1; then
  echo "PASS daemon selftest"
else
  echo "FAIL daemon selftest (tail below)"
  tail -8 /tmp/station-selftest.log
  fails=$((fails + 1))
fi
if [ "$fails" -gt 0 ]; then
  echo "SUITE: $fails file(s) failing"
  exit 1
fi
echo "SUITE: all green"

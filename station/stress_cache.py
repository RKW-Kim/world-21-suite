#!/usr/bin/env python3
"""Cache stress battery: every eviction edge, scaled down, proven live.

Proportional scaling is honest here because the policy only ever compares
bytes and mtimes — a 5 MB file against 4.9 MB of room exercises the exact
same branch as 50 GB vs 49.9 GB. What does NOT scale (wall-clock transcode
time, real network loss) is covered by the SRT drills, not this file.

  python3 station/stress_cache.py   # exit 0 = all PASS, scratch in /tmp

Cases: rotation order, pin survival (operator + playing/next window),
LRU-by-mtime, big-file-small-room accept, all-pinned refusal without
downloading a byte, failure litter, _pinned_files wiring.
"""
import os
import json
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["INTAKE_MIN_FREE_BYTES"] = "1024"

TMP = tempfile.mkdtemp(prefix="cacheStress")
os.environ["BROADCAST_ROOT"] = TMP
MEDIA = os.path.join(TMP, "media")
os.makedirs(MEDIA)

import daemon
from daemon import evict_cache
import intake

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, extra))


def clip(name, seconds=6, size="320x180"):
    p = os.path.join(TMP, name + ".src.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=%s:rate=10" % size,
                    "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast",
                    "-an", p], check=True)
    return p


def fsize(name):
    return os.path.getsize(os.path.join(MEDIA, name))


def intake_as(src, name, title="T"):
    intake.intake(src, title=title, target=name)
    return name


# -- 1. rotation: oldest unpinned goes first --------------------------------
a = intake_as(clip("a"), "rot_a.mp4")
time.sleep(1.1)
b = intake_as(clip("b"), "rot_b.mp4")
cap = fsize(a) + fsize(b) + 100  # room for two, not three
c = intake_as(clip("c"), "rot_c.mp4")
freed = evict_cache(cap=cap)
check("rotation-evicts-oldest", not os.path.exists(os.path.join(MEDIA, a))
      and os.path.exists(os.path.join(MEDIA, b))
      and os.path.exists(os.path.join(MEDIA, c)),
      "freed=%d" % freed)

# -- 2. pin survival: pinned oldest outlives pressure ------------------------
d = intake_as(clip("d"), "pin_d.mp4")
time.sleep(1.1)
e = intake_as(clip("e"), "pin_e.mp4")
# Present: b (pinned, oldest), c, d, e. Cap fits three: the unpinned oldest
# must go, the pinned oldest must stay.
evict_cache(cap=fsize(b) + fsize(d) + fsize(e) + 100, pinned=frozenset({b}))
check("pin-survives", os.path.exists(os.path.join(MEDIA, b))
      and not os.path.exists(os.path.join(MEDIA, c)))

# -- 3. big-file-small-room: evictable filler makes room ---------------------
# The 50MB-vs-49.9MB edge, scaled: cap is dynamic (call-time), so shrink the
# world instead of the files.
for f in os.listdir(MEDIA):
    os.remove(os.path.join(MEDIA, f))
big_src = clip("big", seconds=12, size="640x360")
big_size = os.path.getsize(big_src)
fill1 = intake_as(clip("f1"), "fill1.mp4")
fill2 = intake_as(clip("f2"), "fill2.mp4")
daemon.CACHE_CAP = intake.CACHE_CAP = fsize(fill1) + fsize(fill2) + big_size - 100000
got = intake_as(big_src, "bigfile.mp4")
check("fit-after-evict", os.path.exists(os.path.join(MEDIA, got)),
      "5MB-class file landed with ~100k short")

# -- 4. all-pinned refusal: clean no, zero bytes moved -----------------------
for f in os.listdir(MEDIA):
    os.remove(os.path.join(MEDIA, f))
p1 = intake_as(clip("p1"), "keep1.mp4")
p2 = intake_as(clip("p2"), "keep2.mp4")
json_pl = {"shuffle_on_complete": True, "items": [
    {"file": p1, "title": "K1", "pinned": True},
    {"file": p2, "title": "K2", "pinned": True}]}
open(os.path.join(MEDIA, "playlist.json"), "w").write(json.dumps(json_pl))
open(os.path.join(TMP, "state.json"), "w").write(json.dumps({"index": 0}))
# NOTE: intake reads playlist/state from ITS module globals (real broadcast
# root), so point them at the scratch dir for this test only.
intake.PLAYLIST = os.path.join(MEDIA, "playlist.json")
_pin_backup = intake.ROOT
intake.ROOT = TMP
daemon.CACHE_CAP = intake.CACHE_CAP = fsize(p1) + fsize(p2) + 100
check("pinned-wiring", intake._pinned_files() == frozenset({p1, p2}))
big2 = clip("big2", seconds=12, size="640x360")
before = set(os.listdir(MEDIA))
refused, clean = False, False
try:
    intake_as(big2, "bigfile2.mp4")
except RuntimeError as e:
    refused = "pin" in str(e).lower() or "cache cannot fit" in str(e)
    clean = before == set(os.listdir(MEDIA))
check("all-pinned-refuses", refused and clean,
      "refused=%s no-partial=%s" % (refused, clean))
daemon.CACHE_CAP = intake.CACHE_CAP = 50 * 1024**3  # restore: test 4 shrank the world

# -- 5. failure litter: rejected intake leaves nothing -----------------------
before = set(os.listdir(MEDIA))
try:
    intake.intake(clip("short", seconds=2), title="Short")
    litter = False
except Exception:
    litter = True
after = set(os.listdir(MEDIA))
check("failure-no-litter", litter and before == after)

# -- 6. LRU: touched middle file survives, oldest goes ------------------------
for f in os.listdir(MEDIA):
    os.remove(os.path.join(MEDIA, f))
o1 = intake_as(clip("o1"), "lru1.mp4")
time.sleep(1.1)
o2 = intake_as(clip("o2"), "lru2.mp4")
time.sleep(1.1)
o3 = intake_as(clip("o3"), "lru3.mp4")
os.utime(os.path.join(MEDIA, o2), None)  # o2 watched recently: newest by mtime
cap = fsize(o1) + fsize(o2) + fsize(o3) + 100
o4 = intake_as(clip("o4"), "lru4.mp4")
evict_cache(cap=cap)
check("lru-order", not os.path.exists(os.path.join(MEDIA, o1))
      and os.path.exists(os.path.join(MEDIA, o2)),
      "oldest evicted, touched survives")

print("----\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)

# Machine sync: one config, every machine 1:1

`station/config/` is the station's committed truth: scenes + items
(transforms, visibility, locks), inputs (settings, volumes, mutes,
filters), video canvas/output/fps, stream service, transition, encoder
file. `station/sync.py` moves it both ways:

- `capture` — OBS → repo files (redacted, tokenized, leak-checked).
- `diff` — repo vs live drift report (volatile runtime excluded:
  program/preview cuts, A/B deck eyes).
- `apply [--restart]` — repo → machine: live RPCs for everything the
  protocol supports, profile files for the rest; `--restart` bounces
  obs for geometry/encoder changes (daemon is parked and resumed by
  the command itself, loop survives).

## The loops that matter

New device (or fresh VPS) matches the fleet:

```
git clone <repo> && cd <repo>
./station/setup.sh                      # dirs, units, deps, collection render,
                                        # + writes broadcast/secrets.env template (600)
# fill broadcast/secrets.env: OBS_PASS, YOUTUBE_STREAM_KEY only
python3 station/sync.py apply --restart # materialize config, boot clean
```

Daily change flow (MBA designs, VPS airs):

```
# on the design machine (any collection state, even offline sim):
#   ... make changes ...
python3 station/sync.py capture   # or hand-edit station/config/*.json
git add station/config && git commit -m "..." && git push
# on the VPS:
git pull && python3 station/sync.py apply --restart
# verify: sync.py diff (clean), loop advancing, monitor live
```

`diff` is the audit: run it any time to prove a machine matches the repo,
or to see exactly what drifted (an MBA eye-toggle shows up as one line).

## What does NOT sync (on purpose)

- Playlist queue, playout position, caches, media bytes: live runtime.
  A fresh box starts from the seed `station/playlist.json`; media arrives
  via intake/scp. Migrating queue position mid-show would be wrong.
- Secrets: `broadcast/secrets.env` is per-machine, chmod 600, gitignored.
  Capture writes `{"$secret": "NAME"}` placeholders and then scans its own
  output for every known secret value — a leak aborts the capture. Apply
  refuses to proceed with unfilled names (loud list).
- Machine paths: absolute media paths become `media:<rel>`, overlay URLs
  become `overlay:/...`, resolved locally on apply. If the bytes aren't
  there, apply says which file is missing (loud, explicit gap).

## Known edges (not hidden)

- SetSceneItemTransform is broken server-side (correct payloads rejected;
  matches upstream issue #1299): geometry travels by collection file +
  restart, never RPC. Verified round-trip in lab.
- OBS trusts stale `*_rel` caches over fresh absolute pos on load: the
  merge deletes `pos_rel/scale_rel/bounds_rel` rows it touches (the
  template ships without them; OBS regenerates).
- A running OBS autosaves its in-memory collection over the file: the
  merge runs only while obs is fully dead (apply kills, verifies, merges,
  starts). Never hand-edit the live collection file under a running OBS.
- A/B deck eyes and program/preview are daemon/loop runtime: apply never
  writes them, diff never flags them.
- Encoder/profile files apply at boot only. Video/service/transition
  apply live (skipped when already matching, so apply never bounces a
  running output). Collection-file geometry always needs the restart.
- The monitor stream (lab → MediaMTX) does NOT autostart: Start Streaming
  after any obs restart (lab routes locally). VPS differs by design (main
  output goes to YouTube; second output TBD, do not improvise on air day).

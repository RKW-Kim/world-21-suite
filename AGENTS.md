# AGENTS.md — the contract for working on this station

This file is the first thing any engineer — human or agent — reads. It is
written for someone with **no access to the machine this was built on**: it
must contain everything you need to avoid breaking a live broadcast.

The station runs 24/7. It is not a toy, and it is not a dev box: a change
that lands wrong airs silence, a dead frame, or the wrong video.

---

## 1. The rules that are not negotiable

1. **Never commit or delete live state.** `broadcast/`, `spool/`, `auto.crt`,
   `auto.key`, `station/third_party/` are gitignored for a reason. See §5.
2. **Every write to `playlist.json` or `state.json` takes the station lock**
   (`daemon.pl_lock()`). The daemon, the panel and the overlay server share
   those files; an unlocked read-modify-write loses an update. This is not
   theoretical: an unlocked panel write ate the daemon's index update.
3. **`merge_save_state()` deletes the keys its caller omits.** It is a merge
   over a fixed key list, not a patch. If you call it, pass the *whole*
   state you want to keep. A two-key fragment once wiped `index`, `deck`,
   `stream` and `fallback_air` and restarted the show at item #1.
4. **Never restart the render plane, the daemon, or a unit without saying so
   first.** A plane restart cuts the programme. If a fix needs one, say what
   you are about to do, then do it.
5. **Do not change the ad configuration while testing.** `ad_every`,
   `ad_files`, `ad_links` and `ad_plan` drive what goes on air.
6. **Secrets stay secret.** `broadcast/secrets.env` holds the YouTube stream
   key, the OBS password and the Telegram token. Never paste a value into a
   commit, a log, a PR body or a chat message.
7. **The station is the product.** A clean abstraction that is slower, less
   observable or less operable than what it replaced is a regression, even
   if the tests pass.

## 2. Speak up before a debug spiral

Before (or the moment) the work turns into a fix/restart/retry cycle that
may not converge — plane restarts, hangs, watchdog wedges, flaky anything —
**stop and report**: what went wrong in one sentence, what you are about to
try and roughly how many steps, and whether it blocks the operator's current
goal. Then let them say "go". Silent churn is not acceptable; neither is
waiting for permission to read a log.

If it is clearly not converging after 2–3 attempts, report the state and
propose handing it back rather than grinding.

## 3. The invariants (break these and the station misbehaves)

- **`state.index` is 1-based and points at the NEXT item.** The item on air
  is `items[index - 1]`. `index == 0` means "start at the top".
- **`status: "dormant"` means parked: never selected, skipped silently.**
  Dormant items are skipped by the daemon; the dock's NEXT marker must skip
  them too.
- **Exactly one deck input is visible in PROGRAM.** Every cut hides both
  other decks of both kinds, then re-reads the scene and forces the truth
  (the "reconcile" step in `advance()`). `PLAYOUT_C` is the fail-safe and
  must be hidden outside a failover.
- **The 6-second post-cut refractory is anchored to the input we just cut
  to.** It exists because a fresh RESTART can flicker `ENDED` and cause a
  cut cascade. It is not a general "do not advance" lock.
- **`PLAYOUT_C` is the fail-safe**: it holds `loop_a.mp4`/`loop_b.mp4` and
  rolls to the next one on its END. After the fallback files run out the
  station holds the Tech Diffs card — never black.
- **The music bed belongs to the waiting-room scenes only** (Starting, Off
  Air, End Credits, Tech Diffs). `ensure_bed_isolation()` keeps it out of
  Program, Ad Break and Q&A, where it would fight the programme audio.
- **The fail-safe card is the last line of defence**, not a first resort.
  Fix the deck, not the card.
- **The dock stages edits; Apply is the only thing that changes the
  station.** See `docs/DECISIONS.md` §1.

## 4. The workflow

```
read (docs + code)  →  change (small, one idea)  →  verify (tests + the live station)
                    →  commit (one message, what and why)  →  PR (if the repo is remote)
```

**Verify means all three:**

1. `python3 station/test_spool.py`, `test_fallback.py`,
   `test_playlist_edges.py`, `python3 station/daemon.py selftest` — all pass.
2. The change was seen in the **running** station (a dock screenshot, the
   activity log, the obs-websocket state) — not just in a unit test.
3. Nothing else regressed: the station is still playing, the heartbeat is
   fresh, no new CRIT rows in the activity log.

**Commits** carry a subject that says what changed and a body that says why
(the "why" is the part a future reader cannot reconstruct). One idea per
commit. Never commit live state.

**PRs** (the repo may be worked on remotely): open a branch, push, and
describe (a) what was broken, (b) what you changed, (c) how you verified
it, (d) what you did *not* fix. A PR that says "no context" is not
finished: the reviewer has no access to your session.

## 5. Never touch these

| Path | Why |
|---|---|
| `broadcast/secrets.env`, `broadcast/cookies.txt` | Live secrets (stream key, OBS password, cookies). |
| `broadcast/state.json` | The live cursor, deck, fault history, mixer value. Deleting it restarts the show. |
| `broadcast/media/playlist.json` | The live playlist — the play order itself. |
| `broadcast/media/playlists/` | The operator's saved profiles. |
| `broadcast/activity.db` | The operator's evidence trail. (Tests must not write to it.) |
| `broadcast/daemon.lock`, `broadcast/.station.lock` | Live mutexes. Deleting `daemon.lock` while the loop runs allows a second driver. |
| `spool/` | The download cache. Deleting mid-download loses the resume. |
| `station/third_party/mediamtx` | The pinned MediaMTX binary (re-fetching needs network). |
| `station/manifest/flatpak.lock.json` | The pinned OBS Flatpak build. |
| `~/.config/systemd/user/station-*.service` | The *installed* units (distinct from `station/systemd/*.service`). |
| `auto.crt`, `auto.key` | MediaMTX's self-signed TLS material. |

## 6. Layout of the code

| File | Responsibility |
|---|---|
| `station/daemon.py` | The brain: playout loop, `advance()`/`on_ended()`, watchdog, fail-safe, ad breaks, spool kick, title watcher, the loudness chain, the on-air progress publisher. |
| `station/panel.py` | The operator's HTTP surface: the dock, `/api/state`, `/api/ping`, `/api/save`, `/api/control`, `/api/playlists`, `/api/ytpl`. |
| `station/dock.html` | The dock UI. One file, no build step, no dependencies, no framework. |
| `station/overlay_server.py` | Overlay pages, SSE state push, thumbnails, media serving, the control plane on :7070. |
| `station/spool.py` | The YouTube cache: download, loudness pass, titles, eviction. |
| `station/stream.py` | Live YouTube feeds: resolve, spawn ffmpeg, publish to MediaMTX. |
| `station/station_watchdog.py` | Revives a dead station. Run by `station-watchdog.timer`. |
| `station/sync.py` | OBS configuration in and out of git. |
| `station/shuffler.py` | The shuffle seam rule (never repeat the last item of a cycle). |

Full lookup tables: `docs/REFERENCE.md`. How it fits together:
`docs/ARCHITECTURE.md`. Why it is like this: `docs/DECISIONS.md`.

## 7. Debugging recipes (the ones that cost real time)

- **"The daemon is not responding."** It is probably BUSY, not dead. The
  heartbeat is written by its own thread and carries `pass_ms` and `busy`.
  Check `broadcast/heartbeat.json`. A slow pass says so in the dock's status
  line instead of raising the alarm overlay.
- **The plane is "wedged".** Do not probe obs-websocket from outside:
  fresh handshakes hang for minutes, and the plane usually answers the
  daemon's long-lived connection. Read `broadcast/activity.db` and the
  journal instead. One plane restart usually heals it; do not loop restarts.
- **`kill -USR1 <pid>`** on the daemon dumps a stack trace (faulthandler).
  There is no ptrace/gdb on this box.
- **The obs-websocket is alive?** `curl -sI http://127.0.0.1:4455` returns
  `426` (upgrade required) — that is the cheapest proof of life.
- **What is on air right now?** `python3 station/daemon.py status`, or read
  `state.json`'s `onair` block, or look at the dock's strip.
- **The dock shows stale UI.** OBS browser docks cache the page. The dock
  reloads itself when `dock.html` changes; if it did not, the panel's
  `/api/ping` returns a different `dock_version` — or the OBS dock needs a
  manual refresh.
- **A test run polluted the operator's log?** It should not: the tests
  point `daemon.DB` at a temp file. If you add a test, do the same.

## 8. Working on the dock

The dock is a single 1,300-line HTML file with vanilla JS. It is an
operator console: dense, dark, keyboard-operable, and read at a glance
during a live show. Before changing it, read `docs/DECISIONS.md` §1–§4 (the
staged-edit model, the icon set, the dot semantics, the accessibility
rules). Non-negotiables: the queue is a `listbox` with a roving tab stop,
every control has an accessible name, state is never carried by colour
alone, and the poll must not rebuild the list unless the content changed
(a rebuild kills focus, drags and the operator's cursor).

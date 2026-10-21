# world-21-suite — a 24/7 live station

A small broadcast stack that plays a curated roll of videos on a loop, with
live YouTube streams, ad breaks, a fail-safe, overlay graphics, an operator
dock, and a watchdog that keeps it alive without a human.

This repository is **self-describing**: everything an engineer (human or
agent) needs to run, debug, change and verify the station is in `docs/`.
Read the two entry points below and you are oriented.

---

## The 60-second orientation

| Question | Answer |
|---|---|
| What is the station? | A headless-ish OBS ("the render plane") + a Python playout daemon ("the brain") + a local operator dock. |
| What plays? | A JSON playlist of items (local files and YouTube links), in order, with ad breaks every N items. |
| Who drives it? | `station/daemon.py` — the playout loop, the watchdog, the spooler, the title watcher. |
| Who does the operator talk to? | The **dock**: `http://127.0.0.1:8220/dock`, opened as an OBS Custom Browser Dock. |
| Where does state live? | `broadcast/` — playlist, cursor, knobs, activity log, heartbeat. All gitignored; it is live state. |
| What happens if OBS dies? | The daemon restarts the render plane; the station watchdog restarts the daemon, panel and overlay server. |
| What happens if a video fails? | The fail-safe deck (`PLAYOUT_C`) takes the air; after that, the Tech Diffs card. Never black. |

---

## The documentation map

Read in this order if you are new; skip to the one you need if you are not.

| Document | What it answers |
|---|---|
| **[AGENTS.md](AGENTS.md)** | The contract for working on this repo: rules, invariants, the workflow, what must never be touched. **Read this first.** |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | How the pieces fit: components, data flow, the playout state machine, the OBS model, the file formats. |
| **[docs/OPERATIONS.md](docs/OPERATIONS.md)** | Running it, health checks, the failures you will actually hit and their fixes. |
| **[docs/REFERENCE.md](docs/REFERENCE.md)** | The lookup tables: environment variables, HTTP endpoints, knobs, units, ports, on-disk formats. |
| **[docs/DECISIONS.md](docs/DECISIONS.md)** | Why things are the way they are. The decisions that were argued about, so you do not relitigate them. |
| **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)** | What is still broken, what is deliberately unfixed, what is stale. |
| **[docs/AUDIT-LOOP.md](docs/AUDIT-LOOP.md)** | The autonomous improve-the-codebase loop: how to audit, verify and land a change without a human in the room. |
| **[docs/VPS.md](docs/VPS.md)** | Moving the station to a headless VPS: the spec sheet, the platforms, the security posture, what must change in the code. |
| [docs/e2e-test.md](docs/e2e-test.md) | The compressed-time proof that the loop actually works. |
| [docs/machine-sync.md](docs/machine-sync.md) | One committed OBS config, every machine 1:1. |
| [docs/scene-portability.md](docs/scene-portability.md) | Designing scenes on one machine, airing on another. |
| [PRODUCT.md](PRODUCT.md) / [DESIGN.md](DESIGN.md) / [SCENES.md](SCENES.md) | The product intent, the interface design, the scene inventory. |
| [WORKLOG.md](WORKLOG.md) / [CHANGELOG.md](CHANGELOG.md) | The narrative history and the release notes. |

---

## Running it

```bash
# One-time install (on the target box)
sudo bash station/setup.sh          # units, secrets, mediamtx, deps

# The station is a set of systemd user units
systemctl --user start station-obs station-mediamtx station-overlay station-panel station-daemon
systemctl --user enable --now station-watchdog.timer

# Health
python3 station/station_watchdog.py --check     # all four pieces, one line each
sqlite3 broadcast/activity.db "SELECT ts,level,msg FROM activity_log ORDER BY rowid DESC LIMIT 20;"

# The operator dock
#   http://127.0.0.1:8220/dock     (OBS Custom Browser Dock, or any browser)
```

Tests (stdlib only, no pytest, no network):

```bash
python3 station/test_spool.py
python3 station/test_fallback.py
python3 station/test_playlist_edges.py
python3 station/daemon.py selftest
python3 station/stress_cache.py
```

---

## Repository layout

```
station/            the station itself
  daemon.py           playout loop, watchdog, spooler, title watcher, fail-safe
  panel.py            the operator's HTTP surface (dock + control verbs) on :8220
  dock.html           the dock UI (single file, no build step, no dependencies)
  overlay_server.py   overlay pages, SSE state push, control plane on :7070
  spool.py            YouTube download cache, loudness pass, eviction
  stream.py           live YouTube feeds (yt-dlp -> ffmpeg -> MediaMTX)
  shuffler.py         the shuffle seam rule
  preflight.py        boot-time sanity checks
  sync.py             OBS config in/out (one committed truth, many machines)
  station_watchdog.py revives a dead station (run by a systemd timer)
  publish_youtube.sh  the publish leg: OBS -> MediaMTX -> YouTube (off by default)
  systemd/            the unit files (copied into ~/.config/systemd/user by setup.sh)
broadcast/          LIVE STATE (gitignored): playlist, cursor, knobs, logs, media
spool/              the YouTube download cache (gitignored)
overlay/            the overlay pages OBS renders as browser sources
docs/               this documentation
```

---

## Working on this repo

Read [AGENTS.md](AGENTS.md). The short version: the station is live, changes
are staged and applied deliberately, every writer of the live files takes the
station lock, and a change is not done until it has been verified in the
running station and the tests are green.

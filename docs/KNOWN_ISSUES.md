# Known issues

What is still broken, what is deliberately not done, and what is stale.
Ordered by how much it matters.

---

## Open defects

### The "monitor" path was missing from MediaMTX (fixed 2026-10-21, but read this)

OBS's stream service targets `rtmp://127.0.0.1:1935/monitor`. The path
was removed from `station/mediamtx.yml` on 2026-10-18 as a "lab-era
leftover", so OBS's output went inactive and the daemon logged
`Stream output not active!` on every pass. The path is restored and the
alert is now gated on a real stream key being present. **The publish leg
itself is still off by default** — see `docs/DECISIONS.md` §13.

### The station has never published to YouTube

There was no publish leg at all: the stream key in `secrets.env` is a
convention placeholder and nothing consumed it. `station/publish_youtube.sh`
+ `station-publish.service` now exist, disabled, and refuse to run with
the placeholder. To go live: put a real key in `broadcast/secrets.env`,
`systemctl --user enable --now station-publish.service`.

### The OBS stream service in `station/config/` is not what the live plane has

`station/config/collection.json` is a **capture** and it is stale: it names
the scene `SMILE | Meet`, while the live plane has `SMILE | Program` (a
rename that cost a day of ghost re-kicks). `sync.py apply` pushes the
config; it also stops the daemon and the plane first. Do not run it
casually on a live station: it overwrites the live collection.

### `station-monitor-av.service` is a dead path

It republishes `rtsp://127.0.0.1:1935/monitor` as `monitor-av`; neither
path exists any more, and the unit crash-looped 11k+ times doing nothing.
`setup.sh` no longer installs it, but the file is still in
`station/systemd/`. Delete it when nobody is looking at the history.

### The Xvfb display `:99` is vestigial

OBS moved to the real session (`:0`) for hardware GL. `station-xvfb.service`
still runs `Xvfb :99` and `station-obs.service` still `Requires=` it. It
costs a little RAM and nothing else. Removing it means also fixing
`obs_click.py`'s default display.

### The title watcher only checks a few items per cycle

`_title_watch_pass()` resolves at most 3 fresh URLs and flags at most 2
renames per cycle (every `TITLE_WATCH_SECS`, default 300 s). A 200-item
playlist therefore takes many cycles to be fully checked. The operator
asked for a **daily** full metadata sweep; that is not implemented yet
(see "Not done" below).

### The Music Bed input has no bed file by default

`broadcast/media/music/` is empty, so the waiting-room scenes have a bed
input pointing at nothing. It is harmless (no audio) but it is not the
finished thing.

---

## Deliberately not done

| Item | Why |
|---|---|
| **Recording the programme** | The operator will record live segments manually (Google Meet, choosing the source by hand). Recording the whole programme would double the disk and the CPU for a feature nobody asked for. |
| **A Go rewrite of the daemon** | Measured: a pass is 20–190 ms, the daemon is idle ~99 % of the time, and the felt stalls were a misreported heartbeat, an unbounded handshake and a 40 ms DOM rebuild inside OBS. A rewrite would change none of them. |
| **Per-item loudness in the row menu** | Replaced by the station-wide switch (operator's decision). The file-level EBU pass still runs at intake. |
| **Re-loudnorming all 200 spooled links** | It would re-download every YouTube item for hours and hammer the disk. The station-wide dynamics chain covers the "fully on" intent. |
| **The browser context menu inside text fields** | Suppressed everywhere except inputs, where paste has to work. |
| **Auto-apply of low-risk edits** | The operator chose staged-only, with a loud prompt instead. |

---

## Not done yet (asked for, not built)

- **Per-item preview panel** (operator's Q5): clicking a row should show
  its thumbnail, description and other metadata, with a manual refresh and
  a daily metadata check. The pieces exist — `/thumbs/<file>` on the
  overlay server, and the title watcher as a metadata prober — but the
  panel in the dock does not exist.
- **Scheduled profiles** (day/night running orders switching on a clock).
- **A queue timeline / playhead** (the Studio Player pattern): a visual
  running order with a draggable playhead.
- **Bulk review of amber rows** (approve all / discard all) — the operator
  asked for the bulk action alongside the per-row one.
- **The daily metadata sweep** described above.

---

## Deliberate sharp edges

Things that look like bugs but are the design:

- **Parked decks are muted, not paused.** They keep decoding silently so a
  cut is instant. The daemon's comment says so; do not "fix" it.
- **The 6-second post-cut refractory** looks like a stuck advance. It
  guards against `ENDED` flicker right after a cut. It is anchored to the
  input that was just cut to, so the fail-safe can still roll.
- **`merge_save_state()` deletes absent keys.** By design: the daemon
  clears `fallback_air` by omitting it. Callers must pass the whole state.
- **The station is quiet when it is fine.** The activity log is trimmed to
  5,000 rows and INFO rows are only interesting when you go looking.

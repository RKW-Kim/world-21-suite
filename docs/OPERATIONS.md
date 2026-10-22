# Operations

The runbook: how to run it, how to tell whether it is healthy, and what to
do when it is not.

---

## 1. Install (a fresh box)

```bash
sudo bash station/setup.sh
```

What it does: creates the broadcast tree, writes `broadcast/secrets.env`
(mode 600) if absent, installs the systemd units into
`~/.config/systemd/user/` (or `/etc/systemd/system/` as root), fetches the
pinned MediaMTX binary, and warns about missing system packages. It is
idempotent; re-running it is safe.

Then:

```bash
systemctl --user enable --now station-obs station-mediamtx station-overlay \
    station-panel station-daemon station-watchdog.timer
```

`station/setup.sh` already enables the units; the command above is the
"right now" version.

**Never enable `station-publish.service` until `YOUTUBE_STREAM_KEY` in
`broadcast/secrets.env` is a real key.** The publish script refuses to run
with the placeholder, but the unit should not be armed either.

## 2. Health

One command tells you whether the station is alive:

```bash
python3 station/station_watchdog.py --check
```

```json
{ "daemon_age": 0.87, "daemon": true, "panel": true, "overlay": true, "plane": true }
```

Anything `false` means: run the watchdog (without `--check`) and it will
restart that piece and tell you whether it came back.

More detail:

```bash
# what is on air, and how far through it
python3 -c "import json;print(json.load(open('broadcast/state.json')).get('onair'))"

# the last 30 things that happened
sqlite3 broadcast/activity.db "SELECT ts,level,msg FROM activity_log ORDER BY rowid DESC LIMIT 30;"

# only the bad things today
sqlite3 broadcast/activity.db "SELECT ts,level,msg FROM activity_log WHERE level<>'INFO' AND ts>date('now') ORDER BY rowid DESC;"

# unit states
systemctl --user --no-pager status station-daemon station-obs station-panel station-overlay

# the dock
curl -s http://127.0.0.1:8220/api/ping | python3 -m json.tool
```

Healthy means: heartbeat age under ~2 s, `pass_ms` in the tens, no CRIT
rows in the last hour, and the programme scene showing exactly one deck
plus the ticker and the watermark.

## 3. The log is the evidence trail

`broadcast/activity.db` (SQLite, capped at 5,000 rows) is the operator's
record. It is written by the daemon, the panel and the overlay server.
Levels: `INFO` (normal life), `WARN` (something degraded), `CRIT` (the
station is impaired).

**Tests must not write to it.** The test scripts point `daemon.DB` at a
temp file; keep it that way, or the trail fills with fiction.

## 4. Failures you will actually hit

### "The daemon is not responding"

Almost always **busy**, not dead. The heartbeat is written by its own
thread and carries how long the last pass took and what it was doing:

```bash
cat broadcast/heartbeat.json
# {"t": 1792543148.8, "pass_ms": 45, "busy": "media status"}
```

The dock says *"daemon busy (media status) — last pass took 11.4s"* rather
than raising the alarm. A real stall (no heartbeat for 45 s) is what the
watchdog revives.

### "The plane is wedged"

Symptom: the dock stops updating, the daemon logs `advance deferred`, and
the programme freezes on the last frame.

- **Do not probe obs-websocket from outside.** Fresh handshakes hang for
  minutes on this build, and the server frequently does not greet a second
  client. You will conclude the plane is dead when it is fine.
- Read the journal and the activity log instead:
  `journalctl --user -u station-daemon -n 50`.
- One restart usually heals it: `systemctl --user restart station-obs`.
  **Say that you are doing it** — it cuts the programme.
- If the daemon is wedged rather than the plane:
  `kill -USR1 $(cat broadcast/daemon.pid)` dumps a stack trace.

### "The dock is stale / shows old UI"

OBS browser docks cache the page. The dock compares the `dock_version` in
`/api/ping` with the one it loaded and reloads itself. If it did not:

```bash
curl -s http://127.0.0.1:8220/api/ping | grep -o '"dock_version":"[^"]*"'
```

The panel stamps the served bytes with `mtime-size`; if they differ from
what the dock reports, the dock is on an old build → refresh the OBS dock
panel (or restart the OBS window).

### "The programme is black"

It should never be. If it is:

1. Which scene is on air? `python3 station/daemon.py status` or read
   `state.json`'s `deck`.
2. `SMILE | Tech Diffs` means the fail-safe ran out of files: the decks
   are broken. Check the media dir for the item that was supposed to play.
3. `SMILE | Off Air` means the fault limit was hit: the station stopped on
   purpose and wants a human.
4. Program with no visible deck means a visibility reconcile failed. The
   daemon re-reads the scene on every cut; check
   `GetSceneItemList` for `SMILE | Program`.

### "The stream is not going out"

- The publish leg is **off by default**. `systemctl --user status
  station-publish` — if it is not active, nothing is publishing, by design.
- The publish script refuses to run with the placeholder key.
- OBS must have an RTMP output: the daemon creates it at boot **only** when
  a real key is present (`ensure_stream_output()`).
- The chain is OBS → `rtmp://127.0.0.1:1935/monitor` → `publish_youtube.sh`
  → YouTube. If MediaMTX has no `monitor` path, OBS's output goes inactive
  and the daemon logs `Stream output not active!`.

### "YouTube says 'Sign in to confirm you're not a bot'"

`yt-dlp` is being rate-limited on this IP. The fix is cookies:
`YTDLP_COOKIES=browser:chromium` (or a `cookies.txt` path) in
`broadcast/secrets.env`.

### "The spool is not downloading"

```bash
python3 -c "import spool;print(spool.state('https://youtu.be/<id>'))"
```

`miss` means it never started (check the daemon log for `Spooling next in
background`), `fetching` means it is running, `ready` means the local copy
exists. A `.noaudio` marker beside the key means that selector produced a
silent file and will never be retried (by design).

### "The knobs do nothing"

`broadcast/knobs.json` is read by the daemon every pass. Only the keys in
`KNOB_HELP` are accepted, and only numeric values. The daemon's key list is
`KNOB_KEYS`; the three spool knobs are read directly by the spooler.

## 5. Routine operations

| Task | How |
|---|---|
| Change the running order | The dock: drag rows, then **Apply**. The change lands at the next cut. |
| Undo a staged change | Ctrl+Z in the dock, or the undo button in the staged bar. Step by step back to the last applied state. |
| Save a running order as a profile | The dock: type a name, press the save icon. Profiles live in `broadcast/media/playlists/`. |
| Load a profile | The dock: select it, press the folder icon. It **stages**; press Apply to put it on air. |
| Swap the order automatically at a set time | Edit `broadcast/schedule.json`: `{"switches": [{"at": "06:00", "profile": "morning"}]}`. The dock shows the next switch. The switch applies at the next cut after the clock passes `at`. |
| Import a YouTube playlist | Paste a link with `list=` in the dock's top field. It becomes a parked group. |
| Change the loudness | The wave icon in the strip: on = compress+limit everywhere, off = removed. |
| Restart the daemon | The dock's down overlay → Restart daemon (two presses), or `systemctl --user restart station-daemon`. |
| Restart the plane | `systemctl --user restart station-obs` — it cuts the programme. Say so first. |

### Scheduled profile switches

`broadcast/schedule.json` holds the switches:

```json
{"switches": [{"at": "06:00", "profile": "morning"}]}
```

`at` is a local `HH:MM`; `profile` is the name of a saved profile in
`broadcast/media/playlists/`. The daemon applies it when the clock
passes `at` — within five minutes, so a late restart still catches it —
and the change lands at the next cut like any other order change.

What the station refuses to do:

- apply a profile that does not exist (it logs a warning and waits),
- apply an **empty** profile (that would blank the station),
- fire the same switch twice in a day.

What it does for you: the order the switch replaced is saved as the
`before-switch` profile, so you can load it back from the dock if the
swap was not what you wanted.

The dock's toolbar shows the next switch (`next switch 06:00 ·
morning`) so a swap is never a surprise. The log line is
`Scheduled switch: the running order is now the 'morning' profile`.

## 6. Switching the render plane off (and on again)

The operator can keep the OBS window off their desktop while the rest of
the station runs.

**Do not just close the OBS window.** Closing it makes OBS *quit*, and the
unit's `Restart=always` brings it straight back — the window reappears
every 20 seconds. That loop is the "something keeps starting OBS" symptom.

**The right way: mask the unit.** A masked unit cannot be started by
anything — not systemd at boot, not a dependency, not the watchdog, not
`Restart=always`:

```bash
# 1. stop it, keep it from starting at boot, and forbid any start
systemctl --user stop station-obs.service
systemctl --user disable station-obs.service
#    (mask needs the file moved aside: a real file cannot be masked in place)
mv ~/.config/systemd/user/station-obs.service{,.disabled}
ln -s /dev/null ~/.config/systemd/user/station-obs.service
systemctl --user daemon-reload
systemctl --user is-enabled station-obs.service    # -> masked

# 2. tell the daemon not to try either (the live unit carries this)
#    Environment=PLANE_AUTORESTART=0
systemctl --user restart station-daemon

# 3. the watchdog leaves a masked unit alone
python3 station/station_watchdog.py --check    # "intentionally_off": ["plane"]

# 4. clear the flatpak leftovers (they hold a GPU context)
pkill -x obs-browser-page; pkill -x obs; pkill -x bwrap
```

**The daemon unit must not `Wants=` the plane.** It used to, and every
daemon restart pulled the OBS window back up. The plane is an independent
unit now: it has its own enable, and the daemon waits for it.

**While the plane is off, the queue HOLDS.** `advance()` refuses to
consume items when the renderer is not answering — otherwise every item
would be skipped as "unplayable" and the playlist would be empty by
morning. The daemon keeps running, keeps the state, and logs
`Render plane is down: holding the queue`.

**To turn it back on:**

```bash
rm ~/.config/systemd/user/station-obs.service        # remove the mask
cp ~/.config/systemd/user/station-obs.service.disabled \
   ~/.config/systemd/user/station-obs.service
systemctl --user enable --now station-obs.service
# and remove the override from the live daemon unit:
#   Environment=PLANE_AUTORESTART=0   ->  delete the line
systemctl --user daemon-reload && systemctl --user restart station-daemon
pkill -x obs-browser-page   # clear the flatpak leftovers, if any
```

## 7. Change verification

```bash
bash station/selftest.sh   # the whole stdlib suite, one command
```

Then watch the live station for a couple of passes:

```bash
sqlite3 broadcast/activity.db "SELECT ts,level,msg FROM activity_log ORDER BY rowid DESC LIMIT 10;"
cat broadcast/heartbeat.json
```

## 8. Contribution seats (SRT / WHIP) and their credentials

Seat publishes are authenticated since 2026-10-21 (mediamtx
`authInternalUsers`). Before that the ingest bus accepted any publisher
from any IP — anyone who could reach :9000 could inject on air. Now:

- **Loopback (the box itself) needs no credentials.** OBS's `monitor`
  publish, the ffmpeg deck pipelines, OBS's own SRT reads
  (`streamid=read:slot-cam`) and the dock's WHEP proxy all keep working
  unchanged.
- **A seat credential is one path, publish-only.** Generated by
  `setup.sh` into `broadcast/secrets.env` (`SEAT_CAM_PASS`,
  `SEAT_SCREEN_PASS`, `SEAT_AUDIO_PASS`, `SEAT_AD_PASS`); the mediamtx
  unit carries the EnvironmentFile that feeds them into the config.
- **SRT seat URL** (OBS or ffmpeg, from OUTSIDE the box):

  ```
  srt://HOST:9000?streamid=publish:slot-cam:seat-cam:$SEAT_CAM_PASS&latency=800000
  ```

  A seat credential cannot publish `monitor` (its permission names one
  path), cannot read, and an anonymous remote client matches no entry.
- **WHIP seat** (browser tab, `station/whip.html`): the credentials field
  takes `user:pass` (e.g. `seat-cam:<SEAT_CAM_PASS>`) — mediamtx internal
  auth speaks HTTP Basic there, not Bearer.
- **The firewall adds source restriction on top.** Nothing seat-shaped is
  open by default. Put a seat on the map with:

  ```bash
  sudo bash station/setup.sh --seat 203.0.113.7/32   # repeatable
  ```

  which opens SRT 9000/udp + WHIP 8889/tcp + the WebRTC ICE mux 8189/udp
  FROM THAT NETWORK ONLY. No `--seat` = loopback + tunnels only.

Rotating a seat: edit the pass in `broadcast/secrets.env`, then
`systemctl --user restart station-mediamtx` (brief ingest-bus blip; OBS
inputs reconnect on their own).

## 9. The VPS

The station moves to a headless box eventually. `docs/VPS.md` has the spec
sheet, the platform shortlist, the security posture, and the code changes
that a GPU-less box needs. Read it before provisioning anything.

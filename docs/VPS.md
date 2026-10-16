# VPS runbook — fresh box to verified air

Target: Ubuntu 24.04 LTS, 4 vCPU / 8 GB, no GPU. Everything below is also
what `station/setup.sh` automates; this file is the human-readable contract
for what "provisioned" means. Lab lessons that shaped it are marked (LAB).

## 1. Provision and reach it

- Create the box. Note its public IP and the CPU flags (`lscpu` — the
  CasparCG gate needs AVX2/FMA; record them even though MVP doesn't).
- `ssh` in. All work happens over SSH; the VPS never gets a desktop session.
- Open NOTHING inbound except SSH (and later: nothing else, ever — operator
  access rides an SSH tunnel, see §5).

## 2. OS dependencies (apt, as root)

```bash
apt update && apt install -y git ffmpeg python3 curl xvfb flatpak tcpdump
```
(LAB: Arch calls it `xorg-server-xvfb`; Ubuntu calls it `xvfb`. Flatpak OBS
arrives below. `tcpdump` optional but recommended — every unexplained stall
so far yielded to packet evidence or nothing.)

```bash
flatpak install -y flathub com.obsproject.Studio
```

## 3. Clone and provision (as the broadcast user, NOT root)

```bash
git clone <repo-url> station && cd station
BROADCAST_ROOT=/var/broadcast sudo -E bash station/setup.sh
```

`setup.sh` creates `/var/broadcast/{media,assets,overlays,backups,recordings}`,
writes a chmod-600 `secrets.env` template, fetches pinned MediaMTX, pins the
Flatpak OBS build, renders both scene collections, installs systemd units
(system-wide as root, user units otherwise), and enables autostart. It does
NOT start obs/daemon — deliberate (see §4).

(LAB: setup.sh renders paths for wherever the repo was cloned; re-running it
after moving the checkout is safe and idempotent.)

## 4. Secrets and media, then first start

1. Fill `/var/broadcast/secrets.env`: `YOUTUBE_STREAM_KEY` (VPS-only,
   backup copy with the operator), `OBS_PASS` (strong, generated), Discord
   webhook when wanted. Never commit, never show presenters.
2. Load media: intake from YouTube-unlisted links or `scp` finished files
   into `/var/broadcast/media/`, then fix `playlist.json` (or let intake
   append with `--playlist`).
3. Set the OBS profile ONCE (output 1080p30, x264 superfast CBR 6000k,
   keyframe 2s, AAC 128k; websocket 127.0.0.1:4455 + OBS_PASS; load the
   SMILE-Station collection). Profiles can't be safely templated — GUI or
   `obs-websocket` once, then never again.
   - Director monitor is NOT the stream: /studio's program LIVE plays the
     MediaMTX `monitor` path over WHEP. That path needs a publisher: either
     the main stream output routed to it (lab does this — profile service
     `rtmp_custom` to local MediaMTX) or, on the VPS where the main output
     goes to YouTube, a second output (multi-RTMP plugin or vcam+ffmpeg —
     undecided, do NOT improvise on air day).
   - WebRTC H264 has no B-frames: whatever encodes the monitor path must
     run a B-frame-free preset (lab: ultrafast), or MediaMTX closes the
     session mid-handshake with "doesn't support H264 streams with
     B-frames". Verified live 2026-10-16.
   - Lab discovery 2026-10-16: a fresh OBS profile ships EMPTY (no
     service, no output/video settings). The lab profile now carries
     service.json (rtmp_custom→local monitor) + basic.ini [Video]
     (1920×1080 canvas, 960×540 output) + advanced output mode with
     `streamEncoder.json` — NOT [SimpleOutput] keys. Why: simple mode
     ignores keyint_sec (proven: keyint stays 250), and the x264 custom-
     options string is never read (verified absent from the plugin
     binary). The file that matters is
     `profiles/CONFORM_Y/streamEncoder.json`:
     `{"rate_control":"CBR","bitrate":2500,"keyint_sec":2,
     "preset":"ultrafast","profile":"high","tune":"","bf":0}` with
     basic.ini `[Output] Mode=Advanced` + minimal `[AdvOut]`
     (`Track1Bitrate=160`). Verified in the encoder log
     (`advanced_video_stream ... keyint: 60`) and by 4s WHEP joins.
     These live in ~/.var (machine-local, NOT the repo) — re-apply by
     hand from this list when re-provisioning.
4. `systemctl start station-xvfb station-mediamtx station-overlay station-obs`,
   wait for boot (~90s), then `systemctl start station-daemon`.
5. Verify: `daemon.py status` (stream active after key entry),
   program scene on Meet, deck progressing, one SSH-tunneled look at the
   console. Only then: announce air.
6. Monitor-return check (director panel is blind without it): Start
   Streaming (lab) → `curl :9997/v3/paths/get/monitor` shows
   ready+source → /studio program LIVE plays sub-second video for 60s+
   without dropping. If it drops at ~10s every time, suspect B-frames.

## 5. Remote access discipline (non-negotiable)

- obs-websocket binds **127.0.0.1** and needs the password. No exceptions.
- Lab runs passwordless today (fresh profile, never configured) — harmless
  on loopback-only bind, but the VPS sets OBS_PASS and verifies with a
  wrong-password probe (expect close 4009, not a silent hang).
- Operators (and the phone console) reach it via `ssh -L 4455:localhost:4455
  <vps>` or Tailscale. There is published RCE research through malicious
  browser-source payloads — an exposed 4455 is a takeover waiting for a date.
- The overlay server's BIND stays loopback; the console page is used through
  the same tunnel. No raw ports, no exceptions.

## 6. Failure playbook (what pages whom)

| Symptom | First check | Recovery |
|---|---|---|
| OFF-AIR on program, alerts flowing | journal: `journalctl -u station-daemon` | daemon already cut harbour; fix source, `resume`/`return` |
| Daemon restarting in a loop | `systemctl status`, activity.db tail | systemd rate-caps; read the logged cause, don't disable the cap |
| OBS restarting in a loop | same, `-u station-obs` | rate cap holds it stopped after 3/10min; investigate, don't force-start blindly |
| Total silence (no alerts, no air) | external monitor (Uptime Kuma / hosted cron on the YouTube stream) | VPS itself is the SPOF: rebuild from this repo (`clone && setup.sh`, <1h) |
| Full rebuild | new box + §§1–5 | media restores from intake sources, not from backups we don't keep |

## 7. What this box never does

Test changes (the laptop is the lab; the VPS only ever runs tagged,
rehearsed commits). Edit the on-air scene. Store the stream key anywhere
but `secrets.env`. Reach the internet for media from the render plane.

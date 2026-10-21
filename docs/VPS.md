# Moving the station to a headless VPS

The station runs 24/7 and will eventually live on a headless Linux box
(Ubuntu LTS or Arch). This file is the spec sheet, the platform
shortlist, the security posture, and the list of code changes a GPU-less
box needs.

---

## 1. What the box actually has to do

| Workload | What it costs |
|---|---|
| **OBS rendering** | 1280×720 @ 30 fps. On a desktop with an Intel HD 520 this is trivial (~20 % of a core). **On a VPS there is no GPU: it is llvmpipe (software GL)**, which is roughly 10–20× the CPU for the same picture. |
| **The playout daemon** | 20–190 ms per pass, every 2 s. Negligible. |
| **yt-dlp downloads** | Network-bound; the CPU cost is the merge and the loudness pass. |
| **The loudness pass** | ffmpeg loudnorm on a 4-minute video: ~50 s of one core. Two-pass linear mode doubles the measurement cost. |
| **The spool cache** | Up to `STREAM_SPOOL_MAX_GB` (3 GB default) plus the raw copies (~2× that) plus `broadcast/media` (up to `CACHE_CAP_BYTES`, 50 GB default). |
| **The watchdog / panel / overlay** | Trivial. |

**The single biggest consequence of moving: no GPU.** Everything else is
cheap. A VPS can run this station comfortably — but the render settings
have to change, and the box needs real cores.

## 2. Recommended specification

Two honest anchors before the numbers:

- **The laptop datapoint does not transfer.** "OBS ran fine on the i3/i7
  laptop while I did other things" was OBS IDLE — not encoding. The
  streaming cost is the x264 encode plus (on a GPU-less box) llvmpipe
  compositing, and neither was measured on that laptop.
- **The config tree is the source of truth for what airs.** The shipped
  profile (`station/config/video.json` + `encoder.json`) is 960x540 @30,
  x264 ultrafast CBR 2500k — that is the *lab* profile. The 1080p60
  target is a different box class, not a config nudge.

Cost model on a GPU-less VPS (llvmpipe + x264, modern dedicated x86):

| Profile | Render (llvmpipe) | Encode (x264) | vCPU needed | RAM |
|---|---|---|---|---|
| 960x540 @30 / 2500k ultrafast (shipped) | ~0.5-1 core | ~0.5 core | **3** | 4 GB |
| 1280x720 @60 / 4000k veryfast | ~1.5 cores | ~1.5 cores | **4-5** | 8 GB |
| 1920x1080 @60 / 6000k veryfast (target) | ~2-3 cores | ~3 cores | **8** | 16 GB |

The deck pipelines cost nothing (HLS -> MPEGTS `-c copy`, no re-encode);
intake's loudness pass is offline (~50 s of one core per 4-minute item)
and can simply take longer. The daemon/panel/overlay are trivial. OBS is
the whole story.

```
Budget pick  — 1080p60 (the stated target):
CPU      8 vCPU dedicated (Hetzner CPX41-class AMD EPYC)
RAM      16 GB          — OBS+CEF ~2 GB, page cache for the 50 GB media cache
DISK     200+ GB NVMe   — media cache cap (50 GB) + spool (raw+blessed ~2x) + flatpak
NETWORK  20 TB class    — 6000 kbps 24/7 ≈ 2 TB/mo out, plus deck pulls in
OS       Ubuntu 24.04 LTS (or Arch)
≈ $26-30/month. Fits the budget at the top end.

Comfort pick — if 1080p30 or 720p60 is acceptable:
CPU      4-5 vCPU dedicated (Hetzner CPX31)
≈ $15-18/month, real headroom.

Floor pick — the shipped 540p30 profile, cheapest real box:
CPU      3 vCPU dedicated (Hetzner CPX21)
≈ $9-11/month.
```

**Non-negotiables:** *dedicated* vCPU (a shared "2 vCPU" burst line will
drop frames the moment the loudness pass overlaps a scene render); NVMe
(not SSD-archive tiers); and 8 GB RAM minimum for the 1080p60 profile —
a 4 GB box page-thrashes the media cache against OBS and it shows up as
"the station is struggling".

**$5-10 tier, honestly:** at that price only shared-vCPU or very old
cycles are on the table. That runs the 540p30 lab profile marginally at
best; it will not hold 1080p60. If the budget is hard-capped, the right
move is the floor profile on a CPX21-class box, not a cheap box chasing
the 1080p60 target.

## 3. Platform shortlist

Prices move; check before buying. Ordered by value.

| Provider | Why | Watch out for |
|---|---|---|
| **Hetzner** (CCX/CPX, dedicated vCPU) | The best value per core in the market, and the CPUs are genuinely good for llvmpipe. Locations in Germany/Finland/USA. | Traffic quotas (20 TB is plenty here). The IPv4 costs a little extra. |
| **OVHcloud** (dedicated or "d2" ranges) | Very good value, EU and CA. | The "vCPU" tiers are shared; the dedicated ones are the ones worth it. |
| **Netcup** (VPS 1000 G11 and up) | Good value, strong CPU, EU. | Smaller footprint. |
| **Vultr / DigitalOcean / Linode** | Easiest: hourly billing, many regions, good docs. | 2–4× the price of the value providers. |
| **Contabo** | Cheapest per core by a wide margin. | Oversold shared CPU; the single-core performance is poor, which is exactly what llvmpipe needs. Not recommended. |

**Recommendation (2026-10-21, priced against a real budget):** Hetzner
CPX41 (8 dedicated vCPU, 16 GB, 320 GB NVMe) for the 1080p60 target —
~€26/month; CPX31 (4 vCPU) if the profile drops to 1080p30/720p60;
CPX21 (3 vCPU) for the shipped 540p30 profile. The old €40-70 CCX
suggestion was sized for a 720p30 render the config tree no longer
carries; the CPX line hits the same cores for less.

**Do not** buy a cheap VPS with 1–2 vCPU "for now": software GL plus a
loudness pass on 2 cores will drop frames, and the first symptom is the
one that looks like "the daemon is struggling" — which would send you
chasing the wrong bug.

## 4. Region

The station's egress is a YouTube RTMP push plus yt-dlp downloads.

- **YouTube's ingest** is anycast; the region barely matters for it.
- **yt-dlp** is the part that is region-sensitive: some datacentre IP
  ranges hit "Sign in to confirm you're not a bot" more often. The
  mitigation is cookies (`YTDLP_COOKIES=browser:chromium` or a
  `cookies.txt`), not the region — but a residential-friendly range
  helps.
- **The operator** (you) needs a low-latency path to the box for the
  dock: the dock is a browser page served by the box. If the box is in
  Germany and you are elsewhere, use a Tailscale/WireGuard tunnel and
  keep the box's ports closed to the internet.
- **Pick a region with a good path to wherever your contributors are**
  (the SRT/WHIP seats).

## 5. Security posture

**Are VPS livestreams targeted?** Yes, but not in the way people fear:

- The **stream key** is the crown jewel. Anyone with it can broadcast
  *your* channel, and YouTube will happily take the connection. A leaked
  key is a real incident: rotate it, and never let it into a log, a
  commit, a PR body or a chat.
- **Credential stuffing and SSH brute force** are the generic internet
  background noise. A VPS with a password SSH login gets scanned within
  the hour.
- **DMCA/copyright**: the content you publish is the exposure, not the
  box. A stream that plays other people's videos is a takedown risk
  regardless of hosting.
- **Ransomware-style mass exploitation** of the box itself: real but
  generic. Patch, and do not run a web server you do not need.

**The plan:**

| Exposure | Rule |
|---|---|
| SSH (22) | **Key only**, password login off, no root login, fail2ban optional. Better: Tailscale/WireGuard and close 22 to the internet entirely. |
| Panel (8220) | **Never public.** It is the control plane: it can write the playlist and restart units. Keep it on loopback and reach it through the tunnel. |
| Overlay server (7070) | **Never public** without `STATION_TOKEN`. It can change scenes and restart units. `BIND=127.0.0.1` + a tunnel. |
| obs-websocket (4455) | **Never public.** It is full OBS control. It is loopback in the current setup — keep it that way (OBS binds `*` by default, so firewall 4455 explicitly). |
| MediaMTX (1935, 8889, 9000) | The ingest bus. The seats publish here. If the seats are remote, allow only their addresses; otherwise keep them on the tunnel. |
| The publish leg (YouTube) | Outbound only. The key lives in `secrets.env` (600). |
| The firewall | `ufw default deny incoming`, then allow SSH (or the tunnel). Seat ports (SRT 9000/udp, WHIP 8889/tcp, ICE 8189/udp) open per SOURCE NETWORK with `setup.sh --seat <CIDR>` — never world-open; mediamtx `authInternalUsers` carries the credentials. |

Set `STATION_TOKEN` on any box that is reachable from a network you do not
control: it turns the overlay control plane from "any web page in your
browser can POST to it" into "only the holder of the token".

## 6. What changes in the code for a GPU-less box

| Change | Why | Effort |
|---|---|---|
| **Software-GL plane on a GPU-less box** | `setup.sh` **renders `station-obs.service` per box** at provision time: headless (no X socket) → the plane moves to the Xvfb `:99` the unit already Requires, plus `--env=LIBGL_ALWAYS_SOFTWARE=1` (flatpak form, proven pre-2026-10-20); a session without a GPU driver keeps `:0` but forces software GL; session + GPU → the lab shape, untouched. Re-run `setup.sh` to re-render — each run starts from the pristine unit in git, so the render never compounds, and a mismatched unit text fails LOUD instead of booting a `:0` plane on a box with no `:0`. `station-vnc` is skipped on headless boxes (wayvnc has no session to mirror there). | done in setup.sh |
| **BrowserHWAccel=false on first boot** | The guard used to touch only an EXISTING `global.ini` — a fresh box has none until OBS's first run, so its first boot ran CEF with hardware accel and died ~30s in, every boot (the 2026-10-15 lab outage). `setup.sh` now creates the minimal file (`[General] BrowserHWAccel=false`) when missing. | done in setup.sh |
| **Lower the output** to 960×540 @ 30 (or 720p @ 25) | Software GL cost scales with pixels. | config |
| **Keep the window small (1280×720)** and never scale up | Scaling in software is expensive. | already the case |
| **Set `STREAM_SPOOL_MAX_GB` down to 2** | A 3 GB item through a 20 Mbps link is 20 minutes. | knob |
| **Turn `spool`'s loudness pass to two-pass but with a smaller budget** | The loudness pass is the CPU hog; on 8 cores it is fine, but do not run two at once. | knob/tweak |
| **Use `BROADCAST_ROOT=/var/broadcast`** | `setup.sh` now writes the units with the real secrets path and the real root. | done in setup.sh |
| **Give the daemon a `WorkingDirectory`** that matches `BROADCAST_ROOT` | The daemon defaults its root to `<cwd>/broadcast`. | unit |
| **Run the watchdog as a user unit on the box** | Same as here. | done |

**The GUI question.** A headless box has no desktop. Two options:

1. **Do not need a GUI.** The station is a service: OBS renders the
   programme, MediaMTX carries the streams, the dock is a web page. The
   only reason to see the OBS window is to *debug* it.
2. **Need a GUI for debugging** (recommended): on the VPS the plane lives
   on Xvfb `:99` (see the render above), so the lab's own 2026-10-18
   recipe mirrors it directly — `x11vnc -display :99 -rfbauth <passfile>
   -localhost` over an SSH tunnel (`ssh -L 5900:127.0.0.1:5900`). No
   desktop session, no Wayland compositor needed. `wayvnc` is the wrong
   tool there: it mirrors a Wayland session, and the VPS has none —
   which is why `setup.sh` skips `station-vnc` on headless boxes.

## 7. Migration order

1. Provision the box; `setup.sh`; install the Flatpak OBS and the pinned
   manifest.
2. Copy the *configuration* (not the live state): `station/config/`,
   `overlay/`, the units.
3. Bring up the render plane alone and check that it renders at the
   intended size (this is the step that proves the software-GL budget).
4. Bring up MediaMTX, the overlay server and the panel.
5. Start the daemon with an empty playlist and watch it cut a local file.
6. Only then copy the live playlist across and let it air.
7. Set the real stream key and enable the publish leg **last**.

Do not copy `broadcast/` wholesale: it contains the cursor, the fault
history and the lock files. Copy the playlist and the profiles, and let
the daemon build the rest.

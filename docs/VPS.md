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

```
CPU      8 vCPU (dedicated, not shared)   — software GL + loudnorm + downloads
RAM      16 GB                            — OBS (1.5 GB) + ffmpeg + a 3-8 GB page cache for the spool
DISK     200 GB NVMe                       — media cache (50 GB cap) + spool + the flatpak/obs image
NETWORK  5 TB+ monthly, 1 Gbps            — a 3 GB item is a long download at 20 Mbps
OS       Ubuntu 24.04 LTS (or Arch)        — systemd user units either way
REGION   any well-peered region; EU or US  — see §4
```

**Why 8 vCPU and not 4.** Software GL at 720p30 wants ~2 cores of pure
render; the loudness pass wants another; yt-dlp merging wants another; and
the box must stay responsive while all three run, because a starved box
shows up as "the station is struggling". 4 vCPU works at 720p30 with
little headroom; 8 is the point where the station is boring again.

**Why 16 GB and not 8.** OBS with a browser source and a compositor costs
1.5–2 GB; ffmpeg's loudnorm and yt-dlp's merge are memory-hungry on
720p files; the page cache for the spool wants 3–8 GB so a download does
not fight the render. 8 GB works with `STREAM_SPOOL_MAX_GB` at 2, 16 GB
does not need tuning.

**Why 200 GB.** `CACHE_CAP_BYTES` is 50 GB and the spool holds raw +
blessed copies (2× the cap). Plus the Flatpak OBS image, the MediaMTX
binary, the OS. 200 GB NVMe leaves room to raise the media cap.

**GPU-less alternative.** If the box is going to be a VPS, consider whether
it needs OBS at all: the render plane could be replaced by a compositor
that composites the overlay pages and the deck video (OBS is doing scene
management, not effects). That is a rewrite of the render half, not a
config change. Keep OBS: it is the least risky path and it is what the
scenes are built in.

## 3. Platform shortlist

Prices move; check before buying. Ordered by value.

| Provider | Why | Watch out for |
|---|---|---|
| **Hetzner** (CCX/CPX, dedicated vCPU) | The best value per core in the market, and the CPUs are genuinely good for llvmpipe. Locations in Germany/Finland/USA. | Traffic quotas (20 TB is plenty here). The IPv4 costs a little extra. |
| **OVHcloud** (dedicated or "d2" ranges) | Very good value, EU and CA. | The "vCPU" tiers are shared; the dedicated ones are the ones worth it. |
| **Netcup** (VPS 1000 G11 and up) | Good value, strong CPU, EU. | Smaller footprint. |
| **Vultr / DigitalOcean / Linode** | Easiest: hourly billing, many regions, good docs. | 2–4× the price of the value providers. |
| **Contabo** | Cheapest per core by a wide margin. | Oversold shared CPU; the single-core performance is poor, which is exactly what llvmpipe needs. Not recommended. |

**Recommendation:** a Hetzner CCX (8 dedicated vCPU, 32 GB, 240 GB NVMe)
or an OVH equivalent. Budget roughly €40–70/month; anything materially
cheaper will be CPU-starved.

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
| The firewall | `ufw default deny incoming`, then allow SSH (or the tunnel), and the SRT ports you genuinely need. `setup.sh` now does this. |

Set `STATION_TOKEN` on any box that is reachable from a network you do not
control: it turns the overlay control plane from "any web page in your
browser can POST to it" into "only the holder of the token".

## 6. What changes in the code for a GPU-less box

| Change | Why | Effort |
|---|---|---|
| **Re-add `LIBGL_ALWAYS_SOFTWARE=1`** to the OBS unit | A VPS has no GLX driver; without it, OBS may fail to create a context. | one line |
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
2. **Need a GUI for debugging** (recommended): run a headless X/Wayland
   session and mirror it. `wayvnc` mirrors a Wayland session; on a
   headless box, run one (`sway`/`Hyprland` on a virtual output) and
   `wayvnc` on top of it. Alternatively `xpra` over SSH, which is simpler
   to set up and gives a real terminal too.

The current VNC setup assumes a desktop session already exists
(`wayvnc` on the user session). On a VPS there is none, so this needs its
own recipe — see `docs/KNOWN_ISSUES.md`.

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

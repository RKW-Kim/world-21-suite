# Scene portability: design anywhere, air everywhere

The operator's idea, confirmed and bounded: an OBS scene collection is
portable JSON. Lay out positioning, filters, layering, and mixer levels on
the MBA (or any machine), export, commit, render, load on the VPS — pixel
for pixel, provided the rules below hold.

## Station contract (non-negotiable names)

The daemon finds things by name and fails fast at boot if they are absent.
Any collection — authored or generated — must contain:

- Scenes exactly: `SMILE | Starting`, `SMILE | Meet`, `SMILE | Q&A`,
  `SMILE | Tech Diffs`, `SMILE | Off Air`, `SMILE | End Credits`
- Inputs exactly: `PLAYOUT_A`, `PLAYOUT_B` (ffmpeg media inputs, inside
  `SMILE | Meet`), `IDENT` (the ident sting, inside `SMILE | Starting`)
- Transition: `Fade` available (the daemon's default; override with
  the `TRANSITION` env var, never by renaming)

`render_scenes.py --check` validates structure; the daemon's boot probe
validates presence against the live render plane. Either one failing is a
stop-ship, not a warning.

## What transfers, what does not

Transfers: scene/item layout, transforms, crop, filters + their settings,
mixer volumes and mutes, transition set and durations, nested scenes,
text content and fonts (if installed on both ends), browser source URLs.

Does NOT transfer and must be rebound per machine: camera / microphone /
display / window captures (device IDs differ), VLC and media absolute
paths, plugins absent on the target, encoder choice and bitrate headroom
(MBA VideoToolbox vs VPS x264 — re-tune, never copy blindly), the stream
key (lives in the profile, and profiles are NEVER committed).

## Canvas discipline

Both ends 1920x1080 base and output before export. A collection authored
at another canvas will still load, but every coordinate is wrong in the
quiet way that airs embarrassment at 3 a.m. Check with
`GetVideoSettings` on both ends; fix the MBA, not the VPS.

## Workflow

1. On the design machine: set canvas 1920x1080, lay out scenes keeping
   the contract names above, use `{{MEDIA}}`-style thinking — no absolute
   `/Users/…` paths anywhere (media arrives via intake on every machine).
2. OBS → Scene Collection → Export → save as
   `station/collections/incoming/<name>.json` in this repo.
3. Replace machine paths with the template variables (`{{MEDIA}}`,
   `{{OVERLAY}}`, `{{ASSETS}}`) or broadcast-absolute paths, then
   `python3 station/render_scenes.py --check`.
4. Load the rendered collection in a scratch OBS (or the lab plane) and
   eyeball every scene once — render only checks structure, never taste.
5. Commit, push, pull on the target, load, run the daemon's boot probe.

## Profiles travel separately

Output, stream, and encoder settings live in the *profile*
(`basic/profiles/<name>/basic.ini`), not the collection. Copy profiles
between same-OS machines only, and strip the stream key before committing
anything — secrets never enter the repo, no exceptions.

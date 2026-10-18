# world-21 suite — agent rules

## Speak up before debug spirals (NEVER forget)

Before (or the moment) the work turns into a fix/debug/restart cycle that
looks like it may not end quickly — plane restarts, hangs, watchdog
wedges, flaky-anything — STOP and tell the user FIRST:

- what went wrong, in one sentence
- what I'm about to try and roughly how many steps it may take
- whether it blocks their current goal, or can wait

Then let them say "go" (or skip it). Token spend on invisible churn is
their call to make, never mine. Same applies mid-cycle: if it's clearly
not converging after 2-3 attempts, report state and propose handing it
to them rather than grinding on.

## Station ops notes

- The render plane (headless OBS) occasionally wedges or goes deaf;
  a single restart usually heals it, but don't loop restarts silently.
- OBS must NOT run with --minimize-to-tray on Xvfb (no tray exists):
  some boots hide the main window entirely -> black VNC with a "running"
  OBS. Window must plain open. Verified 2026-10-18.
- systemd user units live in ~/.config/systemd/user/ (daemon unit is
  Wants= not Requires= so plane restarts don't kill the daemon).
- Demo state after ad tests: restore sane ad config before leaving
  (playlist.json ad pool / ad_every were armed for tests).

## PR Checklist

- [ ] `html-validate` CI check passes (runs automatically on PR)
- [ ] Overlay file is **self-contained**: no external assets except Google Fonts
- [ ] Tested in OBS as a browser source at 1920×1080
- [ ] Canonical smile SVG (100-viewBox, chord-centered at x=50) preserved if touching mascot
- [ ] V7 strap choreography + V9 surgical fixes preserved if touching strap (these are SACRED — see `docs/archive/SMILE-ARCHIVE.md` §7-8)
- [ ] `docs/archive/SMILE-ARCHIVE.md` updated if a new strap/card state, landmine, or design rule is introduced
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]`

## Visual verification (for UI changes)

Describe what the eyes should report when testing in OBS:

- **Key pressed**: <kbd>?</kbd>
- **Expected**: <one-sentence description of the visual>

Attach a screenshot if possible.

# smile.co.ke — broadcast overlay kit

Scenes and modules for a Smile.co.ke livestream. Plain HTML, CSS and one
inline script per page. No build step, no framework, no dependencies.

Every page is a standalone OBS **Browser Source**. Drop the file in, set the
size, done.

---

## Layout

```
overlay/     the kit — 14 live pages + the museum + the lab archive   (5.7M)
core/        source-of-truth originals and the Qwen design reference  (384K)
docs/        SKILLS-GUIDE.md — every agent skill installed on this box
audit/       best-moment reference frames, one per scene              (8.3M)
scripts/     deploy-pages-branch.sh — the only script that matters
brand.json   the brand tokens
CHANGELOG.md
```

Deploy with:

```bash
bash scripts/deploy-pages-branch.sh
```

It regenerates `gh-pages` from `prototype/overlay/` and pushes. Live at
`https://rkw-kim.github.io/world-21-suite/`.

> The folder is `overlay/` — singular. It has been called `overly/` before and
> that was a mistake.

---

## The contract

These rules hold across every page. Breaking one breaks compositing in OBS.

| Rule | Why |
|---|---|
| **Scenes are opaque. Modules are transparent.** | Scenes paint their own room. `ticker`, `watermark` and `speaking` must composite over gameplay. |
| **No `color-scheme` meta on transparent pages.** | It makes Chromium paint an opaque root canvas, turning a transparent source into a dark rectangle. All three carry a comment saying so. |
| **Bottom 76px is the ticker's dock.** | `--safe-b: 76px` on every scene. The ticker module is exactly 1920×76. |
| **Corners stay clear.** | Top-left is where the watermark docks. |
| **No canvas, no rAF.** | At most one gated `setInterval` per page — the clock. Everything else is compositor CSS. |
| **Motion is transform/opacity only.** | No animated blur, no animated filter. |
| **Reduced motion is a real poster state**, not a disabled animation. |
| **The logo is verbatim.** | `Smile-Logo.svg` paths copied exactly, never redrawn. |

### Modules — layer these above any scene

| Module | Size | Params |
|---|---|---|
| `ticker.html` | 1920×76 | `?mode=market\|offair` · `?scale=` |
| `watermark.html` | transparent | `?corner=tl\|tr\|bl\|br` · `?size=s\|m\|l\|xl` · `?icon=1` · `?scrim=1` · `?anim=breathe` |

`coming-up.html` is a full-screen bumper, not a transparent module.

### Scenes

`starting-soon` · `brb` · `intermission` · `intermission-b` · `qa` ·
`tech-diff` · `speaking` · `end` · `end-credits`

Most accept the schedule contract: `?plan=` · `?who=` · `?next=` · `?ep=`.
`speaking.html` adds `?names=` · `?emojis=` · `?ad=` · `?adimg=` · `?screen=1` ·
`?noad=1` · `?chat=right` · `?nochat=1` · `?bg=studio` · `?guide=1`.

---

## Driving it

Every scene is driven entirely by URL params — no file to write, no server, no
bot bridge. `?plan=`, `?next=`, `?who=`, `?ep=`, `?ad=`, `?names=`, and so on.
That is deliberate: an OBS browser source can be pointed at a URL with a query
string, and Streamer.bot can swap scenes by editing that string.

**Not implemented:** there is no `state.json` live-feed bridge. Older docs
referenced one; no scene ever read it. If you want trades pushed into the
ticker at runtime, that has to be built — the ticker markup is static HTML
today.

---

## Editing a scene

Open the HTML. There is no build step and nothing to compile — reload in OBS
and the change is live. Every page carries a header comment explaining what it
is and which decisions were deliberate; **read it before you edit.** Most of the
odd-looking choices (the 76px dock, the absent color-scheme meta, the flat
faces) are there because the alternative was tried and broke something.

`speaking.html` is the reference implementation of the compositing rules. If
you add a scene, copy its structure rather than reinventing it.

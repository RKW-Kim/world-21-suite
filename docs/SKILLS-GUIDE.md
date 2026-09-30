# Your Installed Skills — A Working Guide

**Machine:** `rkw@omarchy` · **Catalogued:** 2026-09-30 · **476 skills across 7 agent directories**
**Live path for this project:** `~/.agents/skills/` (mirrored to `.claude`, `.hermes`, `.pi`, `.kiro`, `.trae`, `.config/opencode`)

---

## Read this first: you have a context problem

I measured it rather than guessing.

| Metric | Value |
|---|---|
| Skills installed | **476** |
| Frontmatter loaded at every session start | **34,729 tokens** |
| Share of a 200k context window, before you type anything | **17.4%** |
| Share of a 1M window | 3.5% |
| Total skill content on disk | 110 MB / 2,703 files |

Anthropic's docs are explicit that this cost is unavoidable: *"until a Skill is triggered, only its name and description occupy context."* You pay 34.7k tokens for the privilege of having 476 things you *might* need.

This isn't a hypothetical. A Reddit user running ~20 skills measured *"first prompt — 30-50k tokens gone."* Another, on a 200-skill library, noted the platform now caps skills around 200. **You are 2.4× over that line.**

### The second, worse problem: semantic collision

Skills don't just cost tokens, they *compete*. From a context-engineering write-up on r/ClaudeCode:

> Context confusion is the common flavor. Too many semantically similar tools or agents (`ui-agent`, `frontend-agent`, `nextjs-agent`) and the model calls the wrong one at the wrong time.

You have **at least nine skills that all claim to be "the anti-slop design skill"** — `impeccable`, `design-taste-frontend`, `gpt-taste`, `antislop`, `antislop-ui`, `no-ai-design-slop`, `audit-ai-design-slop`, `high-end-visual-design`, and the seven `better-*` family. Load two and their vocabularies fight.

Impeccable's own documentation says this about itself:

> Two skills with different design vocabularies collide and cancel each other out. **Pick one.**

One Reddit user put it as a hiring rule:

> If you can't explain what each plugin does for your specific workflow without looking it up, delete it. 30 plugins means a massive system prompt which means less context for your actual code. Plugins should fix specific pain points, not be collected like Pokémon.

### The verdict

**Cutting your library from 476 to ~60 would save roughly 30,000 tokens per session and remove a real source of wrong-skill dispatch.** That is the single highest-value change available to you, and it costs nothing but a decision. Section 7 gives you the exact cut list.

---

## How skills actually work (so the rest of this makes sense)

From Anthropic's official docs and the Agent Skills spec — this is the mechanism, not folklore.

**Progressive disclosure, three levels:**

1. **Frontmatter** (`name` + `description`) — injected into your system prompt at startup. *Always paid.* ~100 tokens each on your machine.
2. **`SKILL.md` body** — read via `bash` only when a request matches the description. This is where the actual instructions live.
3. **`references/` and `scripts/`** — loaded only if the body explicitly points at them.

The practical consequence: **a skill's description is the only thing standing between you and paying for it.** A 2,140 KB skill like `impeccable` costs the same 226 tokens as a 3 KB one until it fires.

**What makes a skill actually fire:** the description must state *what it does* **and** *when to use it*. The spec requires both. A vague description is a skill that never loads.

**Two frontmatter fields worth using immediately:**

| Field | Effect |
|---|---|
| `disable-model-invocation: true` | Only you can trigger it via `/name`. Use for anything with side effects — deploys, commits, sends. |
| `user-invocable: false` | Background knowledge only; hides it from the `/` menu. Use for reference material. |
| `paths:` | Glob-gated. Loads only when you're touching matching files. |

**The architecture rule people get wrong.** A Reddit post worth reading put it best: *"Your SKILL.md is likely 3x more expensive than it needs to be."* A 1,200-line monolith loads all of it on every trigger (20% of the window). The same instructions restructured as a 180-line spine pointing at three reference files load only what's needed — **7% cost, identical output.** Most of your library is monolithic.

**Security.** Anthropic's guidance: *"Use Skills only from trusted sources."* Skills can execute scripts. You installed 476 of them from third parties without auditing any. That's a standing risk, not a hypothetical one — and it's a good reason to cut the list rather than maintain it.

---

## The design-skill landscape, researched

I went and looked at what these actually are and how practitioners use them.

### impeccable — the strongest of the set

**By Paul Bakaus** (jQuery UI co-creator, ex-Google devrel on AMP and Google for Creators). Apache 2.0. Released March 2026; **~65k GitHub stars** by September. Your installed copy is **v4.3.1**.

It has three layers:

1. **`/impeccable init`** writes `PRODUCT.md` and `DESIGN.md` — persistent design context every later command reads. This is the part people skip and it's the part that matters most.
2. **23 commands** giving the model a shared design vocabulary: `shape`, `craft`, `critique`, `audit`, `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize`, `live`, `extract`, `document`, `init`.
3. **44–46 deterministic detectors** that run with **no LLM and no API key** — this is the genuinely novel part. It catches AI tells mechanically: Inter-everywhere, purple-blue gradients, cards nested in cards, bounce easing, dark glows, 1px-border-plus-wide-shadow, cramped padding, small touch targets, skipped headings.

```bash
# the parts that work with no key at all — this is the reliable value
npx impeccable detect src/
npx impeccable detect --fast --json .        # regex only, CI-friendly, non-zero exit on slop
npx impeccable detect https://example.com    # headless browser
```

**Practitioner verdicts, in order of usefulness:**

- **8.4/10**, "best-in-class for AI-assisted frontend design. No real competition in this category yet."
- A developer who ran it on his own site got **25/40 — one point under the "borderline AI slop" cutoff.** It flagged five real problems, of which he'd caught two and three were lazy defaults he'd never noticed.
- Re-running after fixes: **32/40.**
- Its `critique` reliably finds: ambiguous competing CTAs, cognitive load, glassmorphism overuse, missing brand signature, weak hierarchy. *"I've stopped trusting my own taste on layouts I've stared at too long. I run `critique` instead."*
- The `detect` CLI on a demo page caught an insufficient touch target, an `h1`→`h3` heading skip, and a visually de-emphasised CTA. *"All three were real issues. None of them would have been caught by a standard linter."*

**The honest caveats — and one is a problem for you:**

| Caveat | Detail |
|---|---|
| **Token overhead is real** | One reviewer now loads it selectively: *"loaded for design-focused sessions, unloaded for refactor sessions."* |
| **It is opinionated against your house style** | It pushes OKLCH, 8px grids, and bans bounce easing. It has a strong preference structure. |
| **Live mode is alpha and flaky** | Browser sessions drop and need restarting; component selection misfires on deep DOM; one long session **wrote a change to the wrong file in a monorepo**. |
| **`adapt` broke layout twice** | Required manual revert. |
| **Western modernist bias** | *"The reference files lean heavily on a specific aesthetic tradition — clean type, generous space, restrained color, minimal ornament. If your project requires a different visual tradition… the skill will push back. Sometimes that pushback is right. Sometimes it isn't."* |
| **It is a partner, not a validator** | *"It has a point of view. Push back with a reason and it'll work with you. Ignore the opinion without a reason and output gets worse."* |

**That last row matters for you specifically.** Your brand is a committed world — yellow on near-black, Space Grotesk, broadcast chrome. Impeccable will read that as "dark UI" and reach for its own defaults. You need to write your `DESIGN.md` deliberately, or its opinions become your opinions by default.

### design-taste-frontend (taste-skill) — the anti-ban approach

28.7k stars. The v2 rewrite reads the brief, infers a direction, then tunes three dials:

| Dial | Range | Meaning |
|---|---|---|
| **VARIANCE** | 1–10 | Layout variation, not repeated patterns |
| **MOTION** | 1–10 | Animation intensity |
| **DENSITY** | 1–5 | Whitespace and information density |

Then it maps signals to dials — `"minimalist / Linear-style"` → VARIANCE 5-6, MOTION 3-4; `"playful / Awwwards / agency"` → 9-10, 8-10; `"trust-first / accessibility-critical"` → 3-4, 2-4.

**Its hard bans are the whole point.** Unlike Impeccable's nudges, taste-skill just forbids: Inter as a lazy default, the AI-purple `#7C3AFF→#3B82F6` gradient, the warm-beige-plus-brass "premium DTC" palette, Fraunces and Instrument Serif as generic display faces, three-equal-feature-card rows, em-dashes, and — the one I'd flag for you — **`div`-based fake screenshots, banned outright.**

The strongest rule in it, and the one worth stealing regardless of which skill you run:

> **MOTION MUST BE MOTIVATED (mandatory).** Before adding any animation, ask "what does this animation communicate?" Valid: hierarchy, storytelling, feedback, state transition. Invalid: *"it looked cool."* If you cannot articulate the reason in one sentence, drop the animation.

**Critical scope limit, and it excludes you:** taste-skill's own docs say *"Landing pages, portfolios, and redesigns. **Not dashboards, not data tables, not multi-step product UI.**"* One reviewer added: *"Skip it: pure functional dashboard/admin UI where aesthetics don't matter."*

Your overlay kit is **neither** — it's brand-critical display design. So taste-skill is arguably a *better* fit than Impeccable for this project, for exactly the opposite reason to the one people usually cite.

### The `better-*` family

A 7-skill suite (`better-interface`, `better-ui`, `better-typography`, `better-layout`, `better-colors`, `better-writing`, `better-accessibility`) plus `better-interface` as a combined review. Individual skills are narrow and well-scoped: fonts, type scale, spacing, contrast, hit areas, optical alignment.

There is **no external research** on this suite. On reputation and structure it's the most disciplined of your library — each skill owns one dimension and `better-interface` chains them. But I can't give you practitioner verdicts because nobody appears to have written any up.

### The rest of the anti-slop cluster

- **`antislop`** + 5 sub-skills (`-ui`, `-human`, `-code`, `-layoutmobile`, `-copywriting`). A gate, not a design system. `-human` is the interesting one for you — contrast, keyboard, focus, states, for real people and AT.
- **`no-ai-design-slop` / `audit-ai-design-slop`** — audit-shaped rather than authoring-shaped. Useful as a *review* pass after a design session.
- **`high-end-visual-design`** — the taste-skill "soft" variant. Calm, expensive, whitespace-heavy. **A poor fit for a dense broadcast overlay** where every pixel is contested.
- **`minimalist-ui`**, **`industrial-brutalist-ui`**, **`agency-grid-layout-minimal`** — these are *aesthetic locks*. Loading one closes off the others. Only useful once a direction is already chosen.

---

## Which one should you run?

| | Impeccable | design-taste-frontend |
|---|---|---|
| Mechanism | Vocabulary + 23 commands + 46 mechanical detectors | Bans + 3 tuning dials + brief inference |
| **Objective quality gate** | **Yes — deterministic, no LLM, CI-able** | No |
| Works on a committed brand | Needs a strong `DESIGN.md` to not override you | Better — it infers from the brief |
| Scope | Any surface | Marketing/editorial, explicitly *not* dense product UI |
| Bias risk | High (opinionated defaults) | Medium (bans are blunt) |
| Setup cost | Run `init` once | None |
| **Verdict for your kit** | **Use `detect` + `critique` only** | **Use as the authoring brain** |

**My recommendation: run both, but disjointly.** Let `design-taste-frontend` drive authoring, and use impeccable's `detect` and `critique` as an objective review gate *after*. They never hold the pen at the same time, so they can't cancel each other. Never load them into the same authoring pass.

---

## What this means for the starting-soon iteration

You want a new `starting-soon` on tech-diff's design language. The relevant skills:

| Need | Skill | Why |
|---|---|---|
| Lock the look | `impeccable shape` → `craft` | Establishes hierarchy before code |
| Anti-slop authorship | `design-taste-frontend` v2 dials | Your house style is the brief; set VARIANCE 7-8, MOTION 6-7, DENSITY 3-4 |
| Mechanical gate | `impeccable detect --json overlay/` | Catches what taste can't see |
| Colour discipline | `color-system`, `oklch-skill` | You're on a fixed brand palette — read, don't reinvent |
| Motion discipline | `animation-principles` | The "why does this animate?" test |
| Visual proof | `agent-browser` | You have it installed; it's how I verify renders |
| Real feedback | `contrast-checker` | Broadcast compression kills low-contrast small type |

**And the standing rule from impeccable's own craft floor, which I'd make the house rule:**

> Refinement preserves; redesign replaces. And: a committed visual world overrides the mechanical checks.

That last clause is the permission slip you need. The detector will flag your dark glows, your marquee, your pulsing dots, your codex grid. **Keep them.** They're a ticker, a live indicator, and a market floor. The craft floor says the committed world wins. Use `detect` for the things it genuinely catches — contrast, cramped padding, small type — and ignore it on the things that are the product.

---

## 7. The cut list

**Move to Tier 2 / stop auto-loading:** the 13 skills that duplicate a better one.

`gpt-taste` (tighter taste-skill for GPT), `design-taste-frontend-v1` (superseded by v2), `antislop-ui` (overlaps impeccable detect + taste), `high-end-visual-design` (wrong register for broadcast), `audit-ai-design-slop` (overlaps no-ai-design-slop), `better-interface` (when you only need one `better-*`), `ponytail`, `craft` (alias inside impeccable), `shape` (alias inside impeccable).

**Move wholesale:** everything with zero relevance to this project.

- All 9 `3d-*` — 3D realtime for a 2D overlay kit
- All 35 `hyperframes*` + 13 video/motion-graphics — you're not rendering video
- All `*-expo` / `write-swift` / `omarchy` / `diagnose-crash`
- All 20+ `x-bookmark-*` / `write-like-meng-on-x` — unless you post

That's roughly **90 skills, ~9,000 tokens, near-zero loss.**

**Set `disable-model-invocation: true`** on anything with side effects: `workflow-ship-change`, `diagnosing-bugs`, `implement`, `codebase-design`, `git-guardrails-claude-code`, `setup-*`, `install-*`, every `*-deploy*`.

**Prune the descriptions.** Your frontmatter averages 73 tokens. `hyperframes-registry` spends 228 tokens on a description for a skill you'll never invoke here. Cutting every description to <40 tokens saves ~12,000 tokens without deleting a single skill.

**Don't uninstall — relocate.** Project-scoped skills in `.claude/skills/` inside the repo only load when you're in that repo. Moving the 3D and video skills there is strictly better than deleting them.

---

## Appendix — all 476 skills

Tier 1 = core design (use deliberately). Tier 2 = situational. Tier 3 = adjacent design/motion/build. Everything else = full inventory by category.

### Tier 1 — core design skills (41)

| Skill | What it does |
|---|---|
| `antislop` | "Anti Slop: Rules for AI Coding Agents. The core filter. Load always to stop generic AI slop." |
| `animation-systems` | Use when designing or implementing product-grade web motion like Stripe, Linear, Apple, and Vercel. Covers motion principles, easing/duration defaults, choreography patterns,… |
| `motion-system` | Define motion tokens — durations, easing vocabulary, and reduced-motion handling — for consistency product-wide. Use when standardising motion across a system. For crafting one specific… |
| `workflow-progress-screenshots` | Show the user real screenshots of the work as it progresses, without being asked. Capture the start, the key moment and the result of every visual change, send them as files with… |
| `antislop-human` | "Human and accessibility skill for antislop. Contrast, keyboard, focus, and states for real people. Includes the contrast checker." |
| `better-colors` | Helps you build a color system and answer anything about color in your project. You can generate palettes, use semantic tokens, convert between formats, check contrast and more. |
| `color-system` | Build a product colour system — tonal scales, semantic roles, and contrast compliance. Use when defining or rebuilding colour from scratch. For dark-mode adaptation use… |
| `critique-color` | Critique a rendered screen's colour — contrast ratios, palette coherence, and semantic meaning. Use when reviewing one screen. For a product-wide WCAG audit use `accessibility-audit`… |
| `dark-mode-design` | Adapt an existing palette to dark mode — surface elevation, contrast rebalancing, and desaturation rules. Use when you already have a light palette to translate. For building the base… |
| `theming-system` | Design theming architecture — brand variants, dark mode, and high-contrast — mapped through token layers. Use when one system must serve multiple themes. For a single palette use… |
| `antislop-copywriting` | "Copy and text skill for antislop. Use when writing or editing prose: headlines, tone, CTAs, and anti-AI-writing patterns. Load with the core." |
| `image-to-code` | Elite website image-to-code skill for Codex. For visually important web tasks, it must first generate the design image(s) itself, deeply analyze them, then implement the website to match… |
| `antislop-code` | "Code comment hygiene for AI coding agents: remove generic AI-slop comments, keep the valuable ones, never touch the code." |
| `critique-affordance` | Critique a rendered screen's affordances — what looks clickable, state visibility, CTA clarity, and action discoverability. Use when reviewing an existing screen. For sizing and… |
| `critique-information-density` | Critique a rendered screen's density — cognitive load, content prioritisation, scanning patterns, and progressive disclosure. Use when a screen feels overwhelming. For the underlying… |
| `critique-visual-hierarchy` | Critique a rendered screen's hierarchy — entry point, eye flow, weight distribution, and emphasis. Use when attention lands in the wrong place. For establishing hierarchy in new work,… |
| `animate` | Build an animation from scratch, making the decisions in the order that determines whether it feels right — should it animate at all, what purpose, which tool, which properties, which… |
| `animation-principles` | Apply animation principles — easing, staging, follow-through — to one specific UI motion. Use when tuning how an animation feels. For product-wide duration and easing tokens use… |
| `antislop-layoutmobile` | "Mobile layout skill for antislop. Use for layouts that reflow across screen sizes, phone to desktop: grids, overflow, tap targets. Load with the core." |
| `antislop-ui` | "UI and visual skill for antislop. Use when building or editing any interface: color, layout, components, motion. Load with the core." |
| `audit-ai-design-slop` | Audit websites, apps, screenshots, mockups, and design code for harmful AI-design clichés, generic generated defaults, and established UI defects. Use when the user wants evidence-backed… |
| `better-interface` | Combines all of the `better-*` skills into a single review across accessibility, layout, writing, typography, color and UI polish. |
| `better-layout` | Helps with grouping, alignment, reading order, progressive disclosure and other details that make a good layout. |
| `better-typography` | Focuses on type scale, spacing, sizing, variable fonts, OpenType features, wrapping, truncation and other details that make typography feel great across your product. |
| `better-ui` | Polishes and improves the UI in your project. Covers concentric border radius, optical alignment, surface depth, contextual icons, hit areas and more. |
| `brandkit` | Premium brand-kit image generation skill for creating high-end brand-guidelines boards, logo systems, identity decks, and visual-world presentations. Trained for minimalist, cinematic,… |
| `critique-composition` | Critique a rendered screen's composition — balance, whitespace, rhythm, and gestalt grouping. Use when a layout feels off but hierarchy is fine. For emphasis and eye flow specifically,… |
| `critique-typography` | Critique a rendered screen's typography — scale usage, readability, consistency, and token compliance. Use when reviewing type on a screen. For defining the scale itself, use… |
| `design-taste-frontend` | Anti-slop frontend skill for landing pages, portfolios, and redesigns. The agent reads the brief, infers the right design direction, and ships interfaces that do not look templated. Real… |
| `design-taste-frontend-v1` | The original v1 taste-skill, preserved for projects depending on its exact behavior. The current default is `design-taste-frontend` (v2 experimental), which is a substantial rewrite. Use… |
| `design-token` | Define and organise tokens for colour, spacing, type, and elevation with naming and usage rules. Use when establishing the token layer. For auditing existing usage use… |
| `gpt-taste` | Elite UX/UI & Advanced GSAP Motion Engineer. Enforces Python-driven true randomization for layout variance, strict AIDA page structure, wide editorial typography (bans 6-line wraps),… |
| `high-end-visual-design` | Teaches the AI to design like a high-end agency. Defines the exact fonts, spacing, shadows, card structures, and animations that make a website feel expensive. Blocks all the common… |
| `imagegen-frontend-web` | Elite frontend image-direction skill for generating premium, conversion-aware website design references. CRITICAL OUTPUT RULE — generate ONE separate horizontal image FOR EVERY section.… |
| `impeccable` | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend… |
| `motion-graphics` | > A short, design-led motion graphic where motion is the message — kinetic typography, stat count-up, chart/data-viz hit, logo sting / brand lockup, lower-third / callout / social… |
| `no-ai-design-slop` | Prevent and remove generic AI-generated design defaults, incoherent visual choices, and established UI defects while creating, revising, or reviewing websites, apps, screenshots,… |
| `oklch-skill` | OKLCH color space for web projects. Convert hex/rgb/hsl to oklch, generate palettes, check contrast, handle gamut boundaries, and theme with Tailwind v4. Triggers on oklch, color… |
| `agent-browser` | Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data,… |
| `3d-retina-resolution` | Render a 3D canvas sharply on Retina and HiDPI displays, including explicit 200 percent resolution, synchronized renderer and post-processing sizes, correct pointer coordinates, and… |
| `redesign-existing-projects` | Upgrades existing websites and apps to premium quality. Audits current design, identifies generic AI patterns, and applies high-end design standards without breaking functionality. Works… |

### Tier 2 — situational (19)

| Skill | What it does |
|---|---|
| `better-accessibility` | Helps your project comply with accessibility standards and best practices. |
| `gsap` | Use when you need to add or debug professional web animations with GSAP (timelines, ScrollTrigger, stagger, transforms) in HTML/CSS/JS/React. Includes patterns for smooth motion,… |
| `design-qa-checklist` | Build a QA checklist for verifying that a build matches the design. Use at implementation review. For the spec engineers build from, use `handoff-spec`. |
| `agency-grid-layout-minimal` | "Create a minimal agency design system with a disciplined editorial grid, oversized typography, quiet uppercase utility labels, restrained image blocks, and subtle structural detail." |
| `landing-page-design` | "Complete system for building high converting landing pages: intake questions, page structure, layout selection, conversion copywriting, SEO, plus strict visual rules for typography,… |
| `layout-grid` | Define a responsive grid — columns, gutters, margins, and breakpoint behaviour. Use when establishing page structure. For the spacing scale inside components use `spacing-system`; for… |
| `pointer-trail-emitter` | Build a cursor trail whose spacing stays constant at any hand speed, by emitting motes per unit of distance travelled rather than on a timer, so a flick draws the same continuous ribbon… |
| `readable-measure` | Set line length and measure for comfortable reading across type sizes and breakpoints. Use when tuning body text. Covers measure only — for the full size and weight scale, use… |
| `simplify` | "Simplify content and interactions to reduce cognitive load. Chains: plain-language-design, cognitive-load-assessment, focus-attention-design. Use when given content, a flow, or an… |
| `spacing-system` | Create a spacing scale from a base unit with rules for when each step applies. Use when standardising padding and margins. For page-level columns and gutters, use `layout-grid`. |
| `typography-scale` | Create a modular type scale with size, weight, and line-height relationships. Use when establishing typographic structure. For line length only use `readable-measure`; for judging type… |
| `web-design-engineer` | "Build or redesign polished browser-rendered visual artifacts with HTML/CSS/JavaScript/React: pages, dashboards, prototypes, slide decks, animations, UI mockups, and data visualizations.… |
| `3d-four-seasons` | Add coordinated spring, summer, fall, and winter states to a 3D scene, blending foliage, sunlight, sky, ground materials, snow, and particles without rebuilding the world. Use for… |
| `accessibility-audit` | Audit an existing interface against WCAG, producing findings with severity ratings and remediation steps. Use when you have a design or build to assess now. Not for planning future… |
| `3d-falling-leaves` | Build recognizable falling leaves in world space using instanced geometry, independent tumble, coupled sideways drift, shared wind, scene occlusion, and camera-aware recycling. Use for… |
| `3d-sky-rays` | Add sun shafts and crepuscular rays to a Three.js or equivalent 3D scene, using scene occlusion, a projected sun position, controlled foreground spill, and scalable post-processing. Use… |
| `add-shader-cursor-trail` | "Add the Shaders WebGPU mouse effect used for the Tidal Commons hero: a white twinkling halftone cursor trail driven by ChromaFlow, masked through a DotGrid, finished with chromatic… |
| `accessibility-test-plan` | Plan accessibility testing — assistive technologies, participant criteria, WCAG coverage, and session protocol. Use when scheduling testing with real AT users. Not for evaluating a… |
| `compliance-mapping` | "Map design decisions to accessibility standards and legal requirements. Use when documenting WCAG conformance, preparing for audits, tracking compliance status, or when legal or… |

### Tier 3 — adjacent design / motion / build (232)

| Skill | What it does |
|---|---|
| `build-threejs-enemy-systems` | Build or refactor reusable, data-driven enemy archetype and moveset systems for Three.js action games. Use for enemy content schemas, model and rig conventions, combat move timing and… |
| `build-threejs-scroll-worlds` | Build rich, scroll-controlled real-time Three.js experiences as one persistent 3D world whose camera, lighting, atmosphere, materials, objects, DOM story, and interactions evolve across… |
| `build-vesperfall-review-assets` | Build truthful Vesperfall asset-library review pairs from transparent PNG references and live Three.js, FBX, or img2threejs models. Use when adding a character, enemy, prop, or equipment… |
| `globe-gl` | Use when implementing globe.gl (Globe.GL) for 3D globe data visualization with WebGL/ThreeJS, including setup, data layers (points, arcs, polygons, labels), and integration patterns in… |
| `threejs-weather` | Put weather into a Three.js scene that reads as weather — rain anchored inside the frustum, a storm that is the rain leaned on rather than a second system, lightning on its own light… |
| `design-debt-audit` | Inventory and prioritise accumulated design inconsistencies across a product. Use when drift has built up over time. For token coverage specifically use `design-token-audit`… |
| `generate-reference-inspired-brand-worlds` | Generate multiple original brand campaign worlds from a supplied visual reference while controlling how close the new work feels without copying protected signature elements. Use when a… |
| `ambient-section-particles` | Add a restrained particle atmosphere inside one section with configurable shapes, density, gravity, wind, sway, rotation, recycling or settling, pointer disturbance, visibility pausing,… |
| `animate-expo` | Build animations in React Native and Expo, making the decisions in the order that determines whether they feel right — should it animate, which thread it runs on, which properties,… |
| `animation-on-scroll` | Create an on-scroll animation trigger using IntersectionObserver with Tailwind-friendly animation classes and keyframes. Use when asked for scroll-reveal, animate-on-scroll, or… |
| `animation-vocabulary` | Reverse-lookup glossary that turns a vague description of a web animation or motion effect into its exact term ("the bouncy thing when a popover opens" → Pop in; "the iOS rubber-band… |
| `build-awwwards-quality-sites` | Art-direct and implement distinctive, motion-rich marketing, editorial, portfolio, and landing websites with original reference-inspired imagery, standout heroes, GSAP choreography, one… |
| `build-game-monster-system` | Build, integrate, audit, or refactor rigged monsters for Three.js and web action games. Use for monster asset contracts, procedural or imported creature rigs, semantic joints and… |
| `build-rigged-game-assets` | Create, integrate, or audit production-ready rigged 3D characters and monsters with a main model, skeleton, animation library, sockets, collision contracts, separate character equipment,… |
| `cinematic-gsap-lenis-motion-system` | Create premium cinematic web motion systems with GSAP, ScrollTrigger, and Lenis. Use for luxury editorial websites, creative studio portfolios, Awwwards-style interactions, smooth scroll… |
| `create-game-vfx` | Create readable, performance-safe Three.js game visual effects. Use for attacks, impacts, damage feedback, status effects, spell trails, particles, shaders, telegraphs, quality tiers,… |
| `emotional-design` | How the AI responds to user frustration, confusion, delight, and distress. |
| `frustration-detection` | Reading user emotional state from text signals — caps, punctuation density, repetition, latency — and adapting before the user disengages. |
| `gesture-alternatives` | "Design alternatives to gesture-based and motion-based interactions. Use when designing swipe actions, pinch-to-zoom, shake-to-undo, tilt controls, multi-finger gestures, or any… |
| `html-to-interaction-prompts` | Convert a supplied HTML page or generated HTML reference into a screenshot-backed article containing multiple reusable interaction prompts. Use when the user provides an HTML file,… |
| `hyperframes` | > Mandatory entry point: read this first for any request to make, create, edit, animate, or render a video, animation, or motion graphic, including a promo, explainer, captioned clip,… |
| `hyperframes-animation` | "All animation knowledge for HyperFrames — atomic motion rules, multi-phase scene blueprints, scene transitions, broader motion-design techniques, AND the seven runtime adapters (GSAP… |
| `hyperframes-keyframes` | > Use when a HyperFrames composition needs a punch-in, punch-out, zoom, reframe, Ken Burns treatment, camera move, visual match/whip handoff, or other seek-safe 2D/3D keyframes; also for… |
| `improve-animations` | Survey a codebase's animation and motion code as a senior motion advisor, then produce a prioritized audit and self-contained implementation plans for other agents (or cheaper models) to… |
| `jobs-to-be-done` | Map functional, emotional, and social jobs with outcome expectations. Use when reframing decisions around motivation rather than features. For who the user is, use `user-persona`. |
| `journey-map` | Map one persona's end-to-end experience with stages, touchpoints, emotions, and pain points. Use when improving an existing experience. For the multi-channel ecosystem use… |
| `motion-sensitivity` | "Design for people with vestibular disorders, motion sensitivity, or seizure conditions. Use when designing animations, transitions, parallax scrolling, video backgrounds, carousels, or… |
| `multimedia-accessibility` | "Design accessible video, audio, and multimedia content with captions, transcripts, and audio descriptions. Use when creating or reviewing video, audio, podcasts, webinars, animations,… |
| `optimize-threejs-games` | Profile, diagnose, and improve Three.js or WebGL game performance without regressing gameplay. Use for frame-time drops, CPU/GPU pressure, draw calls, texture and geometry budgets,… |
| `remotion-to-hyperframes` | 'Port an existing Remotion (React) composition''s source to HyperFrames HTML. Use ONLY on an explicit ask to port/convert/migrate/translate a Remotion source — one-way, Remotion-only. A… |
| `review-animations` | Reviews animation and motion code against a high craft bar derived from Emil Kowalski's design engineering philosophy. Default to flagging; approval is earned. |
| `scroll-progress-timeline` | Turn any ordered process into a data-driven vertical or horizontal scroll story with a base line, progress fill, active step states, responsive collapse, semantic fallback, and… |
| `scroll-scrubbed-word-reveal` | Reveal marked-up text word by word as scroll progress advances, while preserving semantic inline links, emphasis, responsive line wrapping, and reduced-motion readability. Use for… |
| `staggered-word-reveal` | Create subtle editorial word-by-word text reveal animations where each word fades and rises into place once it enters the viewport. Use for premium portfolio headlines, hero copy,… |
| `stitched-full-page-capture` | Capture or repair reliable full-page screenshots for lazy-loaded, scroll-animated, Framer, WebGL/canvas, or reveal-heavy web pages. Use when full-page screenshots are blank, gray, white,… |
| `unicorn-studio` | Use when embedding and customizing Unicorn Studio interactive animations on the web (embed, responsive sizing, performance, layering with UI, fallbacks). |
| `user-flow-diagram` | Diagram screen-level paths, decision points, and branch logic. Use when specifying how a feature is traversed. For the emotional end-to-end arc, use `journey-map` (design-research). |
| `user-persona` | Build research-grounded personas with goals, frustrations, and behavioural patterns. Use when decisions need a consistent user reference. For one session's emotional snapshot use… |
| `vantajs` | Use when adding animated WebGL background effects with Vanta.js (setup, parameters, resizing, performance, integration in React/Next.js). |
| `zeigarnik-effect` | Apply the Zeigarnik Effect — incomplete tasks stay mentally active. Use when designing progress indicators, saved drafts, and return hooks. For the emotional shape of the ending, use… |
| `data-visualization` | Select chart types and design data encodings — marks, axes, labels, and accessible chart styling. Use when presenting data graphically. Owns chart selection and encoding only; the… |
| `editorial-tech` | "Blend editorial magazine composition with precision product-tech detailing using asymmetrical grids, cinematic media bands, mono utility labels, and restrained accent color." |
| `falling-leaves` | Build falling leaves that read as leaves, with each one tumbling on its own axis so it presents a face, thins to an edge, and opens out again, and with its sideways slip driven by that… |
| `gooey-blob-system` | "Create a gooey blob system using SVG filters where multiple shapes merge into a single fluid form. Use overlapping circles combined with a Gaussian blur and color matrix filter to… |
| `media-use` | Agent Media OS, the single skill for every media need in a HyperFrames project. Resolve BGM, SFX, image, icon, brand logo, voice, color grade, or LUT into a frozen local file or… |
| `threejs-landscape` | Build a live Three.js landscape that stays quiet behind a subject — a noise heightfield on a polar grid so resolution follows the lens, ground coloured by slope and moisture rather than… |
| `better-writing` | Focuses on improving product copy in your project. |
| `design-review-process` | Establish review gates — criteria, checkpoints, and approval flow. Use when work ships without consistent review. For running one individual session, use `design-critique`. |
| `ponytail-audit` | > Whole-repo audit for over-engineering. Like ponytail-review, but scans the entire codebase instead of a diff: a ranked list of what to delete, simplify, or replace with stdlib/native… |
| `ponytail-review` | > Code review focused exclusively on over-engineering. Finds what to delete: reinvented standard library, unneeded dependencies, speculative abstractions, dead flexibility. One line per… |
| `design-token-audit` | Audit token usage across a product for coverage, drift, and hard-coded values. Use when tokens exist and you suspect they are being bypassed. For defining tokens in the first place, use… |
| `design-critique` | Facilitate a structured team critique — framing, feedback rules, and actionable outcomes. Use when running a session with people in the room. For a solo expert review, use… |
| `heuristic-evaluation` | Run an expert review against Nielsen's heuristics and domain criteria, with severity ratings. Use when you need findings without recruiting participants. For a facilitated team feedback… |
| `x-bookmark-quote-posts` | Check a user's latest X/Twitter bookmarks and turn recent saved posts into source-backed quote-post drafts calibrated against the user's latest 100 authored posts. Use when asked to… |
| `critique-brand-consistency` | Critique a rendered screen against mood.md, voice.md, and tokens.md. Use when those brand files exist and you are checking compliance. For defining the visual language itself, use… |
| `aesthetic-usability` | Apply the Aesthetic-Usability Effect — polished, consistent interfaces are perceived as more usable and forgive minor friction. Use when justifying visual polish or diagnosing why a… |
| `apple-design` | Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet… |
| `audit` | "Audit an interface for multi-modal interaction support. Chains: keyboard-navigation, touch-target-design, multi-modal-input, gesture-alternatives, feedback-and-status,… |
| `audit-reference-originality` | Audit a website or digital experience against its supplied source references for originality and plagiarism risk. Use when Codex must compare current or historical site output with… |
| `beam-glow-states` | Create React loading, processing, selected, current, focus, and pressed states with the border-beam package's animated edge glow. Use when a card, button, input, tab, option, task panel,… |
| `blue-cloudy-clean-modern` | "Create a clean modern design system with a luminous blue sky atmosphere, soft drifting cloud light, minimal white framing, and serene premium typography." |
| `blue-laser-clean-glass-layout` | "Create a clean dark glass layout system with a thin blue laser atmosphere, frosted premium shells, and polished dashboard structure." |
| `bright-green-tech-system-webgl` | "Create a bright-green technical design system with structured split layouts, hard-framed dark surfaces, mono utility labels, and a prominent WebGL visualization zone." |
| `build-daily-inspiration-sites` | Turn a completed daily UI inspiration capture into exactly five original landing-page builds, one per separate Codex task, using Sites. Use when the user asks to turn the daily… |
| `build-mobile-threejs-games` | Build, tune, or test a Three.js game for mobile web. Use for touch movement, action controls, target selection, touch inventory, safe areas, portrait/landscape layouts, responsive HUD,… |
| `cinematic-scroll-storytelling` | Create cinematic scroll-driven landing pages with Lenis smooth scrolling, GSAP ScrollTrigger, scroll-linked progression, staggered text reveals, sticky card stacks, parallax backgrounds,… |
| `clean-minimal-beige-light-mode` | "Create a clean minimal beige light-mode design system with warm neutral shells, quiet process grids, restrained accent color, and elegant low-contrast structure." |
| `cognitive-load-assessment` | "Assess and reduce cognitive load in interfaces, flows, and content. Use when designing or reviewing any multi-step process, complex form, dashboard, decision flow, or information-dense… |
| `container-lines` | Add vertical container-size guide lines with mini corner squares for precise, structured web layouts. Use when asked for container lines, measured layout guides, vertical boundary lines,… |
| `daily-ui-inspiration-capture` | Create a recurring daily UI inspiration capture. Use when the user asks to run, refresh, package, or validate dated UI inspiration bundles, especially for… |
| `dark-blue-contrasting-clean` | "Create a dark-blue clean design system with strong contrast, cobalt gradient feature blocks, crisp framed structure, and restrained premium glow." |
| `dark-glass-clean-layout` | "Create a dark glass layout system with frosted premium shells, clean multi-column workspace structure, floating data cards, and restrained atmospheric depth." |
| `design-first-ui-prompting` | Use when you need design-first, spec-driven, skimmable prompts for UI generation. Covers prompt structure, constraints, variations, typography/spacing rules, and iteration workflow for… |
| `design-game-encounters` | Design, implement, tune, or test Three.js action-game encounters. Use for arena layout, enemy composition, spawn pacing, objectives, boss phases, reward cadence, encounter fixtures, and… |
| `documentary-brutalist-agency` | Create or redesign creative agency, production studio, architecture, culture, and portfolio websites with billboard typography, hard black-and-white chapters, exposed grids, documentary… |
| `editorial-portfolio-chapters` | Create or redesign creative-studio, agency, photographer, artist, and portfolio websites where project work leads the story. Use for dark editorial shells, full-bleed campaign media,… |
| `editorial-service-booking` | Create or redesign appointment-based service websites for salons, barbers, spas, wellness studios, clinics, and hospitality brands. Use for warm editorial layouts, serif-led identity,… |
| `emil-design-eng` | This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great. |
| `faceless-explainer` | "Turn arbitrary text — an article, notes, a topic, a brief — into a faceless explainer video: there is no site or footage to capture, so the visuals are invented per scene (typography,… |
| `figma` | Import Figma content into a HyperFrames composition — rendered assets, brand tokens, components, storyboard sections → reconstructed motion (frames read as states, not slides)… |
| `find-animation-opportunities` | Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't. Read-only; it proposes motion with exact values, it does not implement it. Use… |
| `flexible-typography` | "Design typography systems that adapt to user needs — scaling, spacing, and font preferences. Use when designing type systems, setting font sizes, defining line heights, or reviewing… |
| `framed-grid-layout` | Create minimal framed grid layouts with thin visible boundary lines, L-shaped corner brackets, subtle diagonal line texture, and strict section alignment. Use when asked for clean,… |
| `general-video` | > Author or edit a custom HyperFrames composition when no specialized workflow fits, or when BRIEF.md sets flow: companion. Use for longer or multi-scene pieces, brand and sizzle reels,… |
| `glass-dark-ui` | Build dark-mode glassmorphism interfaces with readable contrast, frosted surfaces, and gradient borders using a pseudo-element mask. Use when asked for glass cards, frosted dark hero… |
| `globe-particles` | Create a globe-like 3D particle visualization with a dense luminous spherical core and thinner orbital ring or flattened disc. Use when a design needs a premium planetary, orbital,… |
| `gsap-scrolltrigger-storytelling` | "Build cinematic sticky product storytelling with GSAP ScrollTrigger, progressive UI reveals, scroll-synced animation, smooth interpolation, and immersive section transitions." |
| `handoff-spec` | Write the implementation handoff — measurements, behaviours, assets, states, and edge cases. Use when engineering picks up the work. For verifying the result afterwards use… |
| `high-contrast-skeuomorphic-clean` | "Create a high-contrast clean skeuomorphic design system with molded dark surfaces, crisp light separation, tactile inset depth, and restrained signal accents." |
| `hyperframes-audio` | > Use when audio already placed in a HyperFrames composition needs to be mixed: fade-in/fade-out, crossfade, track gain or volume, volume automation, ducking, a music bed that fights a… |
| `hyperframes-cli` | > Use the HyperFrames CLI development loop: init, add, catalog, capture, lint, check, snapshot, compare, grade-compare, preview, play, present, beats, keyframes, single or batch render,… |
| `hyperframes-creative` | Non-animation creative direction for HyperFrames videos. Use for design spec (frame.md / design.md) handling, palettes, typography, narration, beat planning, audio-reactive visuals,… |
| `image-first-grid-layout` | "Create an image-led grid design system with full-bleed photography, structural guide lines, anchored content blocks, and restrained technical overlays." |
| `industrial-brutalist-ui` | Raw mechanical interfaces fusing Swiss typographic print with military terminal aesthetics. Rigid grids, extreme type scale contrast, utilitarian color, analog degradation effects. For… |
| `interface-review` | Reviews your work across multiple categories like UI, typography, layout, color, writing and accessibility and gives you a detailed analysis of the findings. |
| `interfaces-that-feel` | Apply an emotional resonance lens to a UI that is technically correct but flat, prescribing changes at the copy, motion, and interaction layer. Use when a design tests fine but lands… |
| `landing-page` | Use when designing or rewriting a high-converting landing page (single-offer page) for SaaS/apps/services. Covers structure, layout patterns, conversion strategies, copywriting, SEO/AEO,… |
| `law-of-common-region` | Apply the Law of Common Region — a shared container, background, or border groups elements regardless of spacing. Use when grouping must survive a tight layout. For grouping by spacing… |
| `liquid-metal-border` | Add and tune animated liquid-metal WebGL borders with the React `metal-fx` package. Use when buttons, icon controls, chips, tabs, cards, or selected surfaces need a metallic active,… |
| `make-interfaces-feel-better` | >- Design engineering principles for making interfaces feel polished. Use when building UI components, reviewing frontend code, implementing animations, hover states, shadows, borders,… |
| `mesh-gradient-dark-blue-clean` | Create a futuristic, premium, clean dark-blue mesh-gradient design system across background rendering, hero shell, navigation, floating nodes, framed sections, CTAs, and motion. Use when… |
| `micro-interaction-spec` | Specify one micro-interaction completely — trigger, rules, feedback, loops, and modes. Use when handing a single interaction to engineering. For motion craft alone use… |
| `minimalist-ui` | Clean editorial-style interfaces. Warm monochrome palette, typographic contrast, flat bento grids, muted pastels. No gradients, no heavy shadows. |
| `mobile-native` | Make a web app feel native on a phone — the small CSS and meta-tag fixes that separate "a website in a browser" from something that feels installed. Covers sticky hover states, tap… |
| `naming-convention` | Establish naming rules for components, tokens, and layers with patterns and worked examples. Use when names are inconsistent or being set. For what the tokens actually contain, use… |
| `nested-container-frames` | "Create a container-in-container layout system using nested frames. Use an outer centered container with visible vertical boundary lines and corner markers. Inside, place inner… |
| `omarchy` | > REQUIRED for end-user customization of Linux desktop, window manager, or system config. Use when editing ~/.config/hypr/, ~/.config/omarchy/, ~/.config/alacritty/, ~/.config/foot/,… |
| `optimize-web-animations` | Profile, audit, and optimize frontend page performance with emphasis on animation work, memory-leak risks, long-session slowdowns, CSS animations, canvas/WebGL requestAnimationFrame… |
| `plain-language-design` | "Write and review content for plain language accessibility. Use when writing interface copy, error messages, instructions, onboarding text, help content, legal or medical information,… |
| `preference-audit` | "Audit an existing interface for respect of user preferences including motion, contrast, colour scheme, and text scaling. Chains: user-preference-respect, responsive-accessibility,… |
| `pricing-page` | Use when designing or rewriting a high-converting SaaS pricing page (structure, plan design, copywriting, SEO/AEO, FAQs, layout patterns, experiments). Includes checklists, templates,… |
| `readable-content` | "Write and structure content for diverse reading abilities and cognitive styles. Use when writing long-form content, help documentation, product descriptions, policies, terms, or any… |
| `responsive-accessibility` | "Design responsive layouts that maintain accessibility across screen sizes, zoom levels, and orientations. Use when designing responsive interfaces, testing zoom behaviour, or reviewing… |
| `responsive-design` | Design layouts and interactions that adapt across screen sizes and input methods. Use when one design must serve many viewports. For the underlying column grid use `layout-grid`; for… |
| `responsive-review` | "Review responsive and flexible layout for accessibility across devices, zoom levels, and orientations. Chains: responsive-accessibility, flexible-typography, information-density. Use… |
| `scroll-world-storytelling` | "Turn an article, case study, brand narrative, product journey, or long-form story into a cinematic scroll-driven landing page using one of three renderers: scrubbed video, a real-time… |
| `setup-matt-pocock-skills` | "Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills." |
| `shaders-cursor-ripples` | Add cursor-following fluid WebGPU distortion over an existing image with the Shaders library's ImageTexture and CursorRipples components. Use when a hero, gallery, or media panel needs a… |
| `specify` | "Specify adaptive behaviour for an interface. Chains: user-preference-respect, responsive-accessibility, flexible-typography, colour-independence, simplified-views, information-density.… |
| `split-layout-technical` | "Create a technical split-screen design system with dual panels, fine frame lines, mono metadata, quiet editorial typography, and premium inset surfaces." |
| `stitch-design-taste` | Semantic Design System Skill for Google Stitch. Generates agent-friendly DESIGN.md files that enforce premium, anti-generic UI standards — strict typography, calibrated color, asymmetric… |
| `tailwindcss` | Use when designing/implementing UI with Tailwind CSS (layout, typography, responsive, theming, component patterns). Includes quick recipes and conventions for clean, consistent web design. |
| `technical-wireframe-info-layout` | "Create a monochrome technical wireframe design system with exploded 3D structure, connector annotations, sparse information labels, and precise dark diagnostic framing." |
| `thinking-orbs` | Add accessible animated AI loading and agent-status indicators with the React thinking-orbs library. Use when a chat, copilot, voice, search, generation, or tool-running interface needs… |
| `threejs` | Use when building or debugging interactive 3D scenes on the web with Three.js (scene/camera/renderer, lights/materials, GLTF loading, controls, performance). Helpful for designers… |
| `threejs-towers` | Generate architecture procedurally in Three.js and film it assembling — a small geometry vocabulary that builds pagodas, castles, domes and spires from parameters instead of mesh files,… |
| `user-preference-respect` | "Design interfaces that detect and respond to system-level user preferences. Use when implementing dark mode, reduced motion, high contrast, text scaling, or any user preference that… |
| `video-to-superprompt` | Turn a reference video into a super detailed recreation or inspiration prompt. Use when the user provides, mentions, uploads, links, or points to a video and asks to analyze the design,… |
| `visual-hierarchy` | Establish hierarchy through size, weight, colour, spacing, and position so the eye lands in the intended order. Use when composing new work. For judging an existing screen, use… |
| `web-technique-to-skill` | Turn a visual or interaction technique you already built into a reusable web-design skill, by isolating the one mechanism that makes it work while reproducing its approved reference… |
| `webgl-3d-object` | Create a real 3D WebGL object with geometric mesh depth, physically based material, directional and ambient lighting, perspective camera, subtle rotation, and floating motion. Use when a… |
| `webgl-laser` | Create a fixed full-screen WebGL laser background effect with a thin white-hot vertical core, restrained brand-colored halo, and soft smoky fog around the beam. Use only for laser… |
| `wireframe-spec` | Specify wireframe layout — content priority, component placement, and annotation. Use when defining structure before visual design. For grid mechanics, use `layout-grid` (ui-design). |
| `3d-sky-background` | Create a camera-correct sky background for a 3D scene with a procedural atmosphere or panorama, horizon haze, aligned sunlight, and coherent environment lighting. Use for architectural… |
| `add-mouse-driven-orbit` | Add restrained mouse-driven orbit and parallax depth to a Three.js hero by damping one pointer target and splitting it across camera translation, look-at, and small object rotations. Use… |
| `background-grid-webgl` | "Create a perspective WebGL background grid with fading lines, subtle particle haze, slow forward drift, and gentle camera parallax." |
| `design-negotiation` | Advocate for design quality, scope, and timeline with partners and leadership using evidence and shared goals. Use in the conversation itself. For the commercial vocabulary behind it,… |
| `handoff-protocols` | Designing smooth transitions between agents and between AI and humans. |
| `law-of-continuity` | Apply the Law of Continuity — the eye follows alignment and unbroken paths. Use when sequencing steps, aligning content, or designing carousels and timelines. For grouping rather than… |
| `marquee-loop` | "Apply seamless infinite marquee loops using duplicated items." |
| `masked-reveal` | Create masked staggered word reveals on scroll with GSAP ScrollTrigger. Use when headings, hero copy, section titles, or editorial text should reveal word-by-word through an overflow… |
| `affinity-diagram` | Cluster many qualitative data points into themes and insight statements. Use when synthesising across multiple sessions or sources. For a single transcript use `summarize-interview`; for… |
| `css-alpha-masking` | Apply CSS alpha masking with linear-gradient for horizontal or vertical edge fades (mask-image and -webkit-mask-image). Use when asked for alpha masks, fade edges, or CSS mask gradients. |
| `empathy-map` | Build a Says, Thinks, Does, Feels map for one user or segment. Use when sharing user understanding quickly. For a composite archetype with goals and behaviours use `user-persona`; for… |
| `feedback-and-status` | "Design feedback and status communication that works across senses — visual, auditory, and haptic. Use when designing loading states, success messages, progress indicators,… |
| `illustration-style` | Define an illustration style guide — visual language, colour usage, and application rules. Use when commissioning or standardising illustration. For icons, use `icon-system`… |
| `law-of-similarity` | Apply the Law of Similarity — shared colour, shape, or size signals that elements belong to one category. Use when signalling relationships across distance. For grouping by position, use… |
| `progressive-blur` | Create a layered CSS progressive blur (top or bottom) using multiple backdrop-filter masks for depth and softness. Use when asked for “progressive blur”, “gradient blur overlay”, or… |
| `reveal-hover-effect` | Build cursor-following spotlight reveals that expose a second aligned image through a soft radial mask. Use for hover-to-color, before-and-after, x-ray, material, texture,… |
| `summarize-interview` | Turn one interview transcript into themes, supporting quotes, and action items. Use immediately after a session. For synthesising many sessions at once, use `affinity-diagram`. |
| `3d-virtual-tour` | Build guided and interactive virtual tours through a 3D environment with authored camera paths, room and floor-plan navigation, orbit inspection, smooth mode handoffs, and progressive… |
| `ask-sonner` | Guide to Sonner, the React toast library — install and wire up the Toaster, pick the right toast() call, promise and loading toasts, updating, dismissing and persisting toasts, styling,… |
| `assess-load` | "Assess cognitive load across a complete multi-step process and produce a load map. Chains: cognitive-load-assessment, memory-load-reduction, wayfinding-navigation. Use when evaluating a… |
| `author-game-levels` | Author or revise readable, flat-world Three.js game levels. Use for movement and camera routes, collision and navigation, encounter zones, landmarks, objectives, pickups, motivated… |
| `beautiful-shadows` | Apply exact Tailwind arbitrary shadow utilities for polished, layered neutral elevation. Use when compact cards, controls, panels, popovers, hero media, feature callouts, or modal-like… |
| `behavioral-consistency` | Ensuring the AI behaves predictably across sessions, edge cases, and modalities. |
| `book-serif-index` | "Create an archival book-reader design system with serif-led pages, mono index navigation, aged paper surfaces, margin notes, and a premium catalog frame." |
| `break` | Renders a component you choose in every state and scenario on a temporary page and stress tests it. |
| `browser-video-recording` | Create polished 60 fps 4:3 4K browser screen-recording style videos from Codex in-app browser captures, with browser-only crop, natural macOS cursor styling, deliberate click… |
| `build-game-changelog` | Design, implement, backfill, audit, and release in-game changelogs with contiguous versioning, deployment provenance, menu-state navigation, accessible toggle, close, and Escape… |
| `build-hybrid-game-assets` | Plan, create, integrate, or audit a hybrid asset pipeline for a Three.js or web game. Use when choosing among imported meshes, procedural 3D geometry, AI-generated reference art, 2D UI… |
| `build-interactive-particle-trail` | Build a cursor or touch particle interaction that emits by distance along the traveled segment into a recycled GPU point pool, with optional keyboard-triggered bursts. Use for… |
| `click-test-plan` | Design first-click and click tests for findability and navigation. Use when testing whether people can locate something. For full task-based observation, use `test-scenario`. |
| `codebase-design` | Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more… |
| `codex-gpt-image-2-5-flare` | "Generate or edit artwork with built-in Codex image gen, especially transparent PNG ornaments, game sprites, emblems, and UI graphics. Use when the user requests GPT 2.5 Flare,… |
| `colour-independence` | "Design interfaces where colour is never the only way information is communicated. Use when designing status indicators, data visualisations, form validation, alerts, maps, or any… |
| `competitive-analysis` | Compare UX patterns, features, strengths, and gaps across rival products. Use when you need to know what others actually do. For deliberately adopting their conventions, use `jakobs-law`… |
| `component-spec` | Specify one component — props, states, variants, accessibility, and usage rules. Use when defining a library component. For the reusable doc scaffold use `documentation-template`; for a… |
| `content-strategy` | Define what content a product needs, how it is structured, and who owns it. Use when content itself is the problem. For the words in the interface use `ux-writing` (designer-toolkit);… |
| `conversational-ux` | Design voice and conversational interfaces — dialog flows, error recovery, and persona. Use when the interface speaks and listens rather than being tapped. For graphical input… |
| `corner-diagonals` | Apply diagonal-cut corners and chamfered edges to buttons, cards, panels, and container shells. Use when a design needs precise geometric framing, sci-fi UI surfaces, clipped-corner… |
| `css-border-gradient` | Apply subtle gradient-border treatments for premium web surfaces. Use when cards, pricing panels, nav bars, modals, buttons, or hero surfaces need a refined edge highlight without a loud… |
| `design-flow` | "Design an interaction flow with inclusive input and output options from the start. Chains: multi-modal-input, keyboard-navigation, touch-target-design, feedback-and-status. Use when… |
| `design-system-adoption` | Create adoption strategy and enablement materials to drive design system usage. Use when the system exists but teams ignore it. For contribution and versioning rules, use… |
| `dither-laser-dark-mode` | "Create a dark premium design system that combines near-black surfaces, subtle ordered-dither texture, and a thin accent-colored laser atmosphere." |
| `documentation-template` | Generate a reusable documentation scaffold for components, patterns, or guidelines. Use when standardising how the system is documented. For the content of one component's spec, use… |
| `error-handling-ux` | Design error prevention, detection, and recovery across a product — message content, placement, and escape routes. Use when errors span multiple flows. For validation inside a single… |
| `error-prevention-recovery` | "Design error prevention, error messages, and recovery flows for cognitive accessibility. Use when designing forms, checkout flows, account creation, settings, data entry, or any flow… |
| `explain-interface` | Helps you figure out how something was built on the web. |
| `focus-attention-design` | "Design interfaces that support sustained focus and reduce distractions. Use when designing for users with ADHD, attention difficulties, anxiety, or any context where focus matters —… |
| `form-design` | Design a form end to end — field order, grouping, validation, and completion. Use when the artifact is a form. For product-wide error strategy use `error-handling-ux`; for first-run… |
| `form-labelling` | "Design form labels, instructions, and grouping that work for screen readers and cognitive accessibility. Use when designing or reviewing forms, input fields, checkboxes, radio buttons,… |
| `framed-tech-dark-border-gradient` | "Create a framed dark technical design system with border-gradient shells, asymmetrical grid panels, mono utility labeling, and restrained monochrome atmosphere." |
| `funky-purple-container-tech` | "Create a dark container-led technical design system with fuchsia-purple accents, layered rounded shells, crisp frame lines, and playful futuristic focal objects." |
| `generative-ui` | Designing interfaces where AI generates UI components dynamically. |
| `glass-dark-mode-clock` | "Create a dark glass design system with frosted shells, soft beam grids, circular clock-like calibration dials, and precise sci-fi instrument framing." |
| `gpt-image-2` | 面向 GPT Image 2 的图像生成 / 编辑技能。可在 3 种环境下使用：(A) Garden 本地模式，通过 OpenAI 兼容接口直接出图并落盘；(B) Host-Native 模式，把本 Skill 当作提示词工程指引，把渲染好的 prompt 交给宿主 Agent 自带的图像工具出图；(C) Advisor 模式，宿主无任何图像工具时退化为高质量… |
| `heading-structure` | "Design heading hierarchies and content structure that work for screen readers and cognitive accessibility. Use when structuring pages, articles, dashboards, forms, or any content-heavy… |
| `heuristic-evaluation-ai` | Adapting Nielsen's heuristics and new AI-specific heuristics for AI interfaces. |
| `hyperframes-registry` | Search, install, and wire registry blocks and components into HyperFrames compositions. Use BEFORE hand-building any named visual — whenever a brief, a user, or a storyboard names a… |
| `hyperframes-studio` | > Use when working with a person on a HyperFrames project in Studio: first, whether their message asks for a change at all (questions, loose ideas and "don't change anything" get an… |
| `imagegen-frontend-mobile` | Elite mobile app image-generation skill for creating premium, app-native screen concepts and flows. Designed for iOS, Android, and cross-platform mobile products. Prioritizes clean… |
| `information-architecture` | Design content structure, hierarchy, labelling, and the navigation model. Use when organising what exists. For the UI that exposes it use `navigation-patterns` (interaction-design); for… |
| `information-density` | "Design interfaces where information density can be adjusted to suit different cognitive needs and preferences. Use when designing dashboards, data tables, feeds, inboxes, settings… |
| `keyboard-navigation` | "Design keyboard navigation and focus management for users who cannot or prefer not to use a mouse or touch screen. Use when designing any interactive interface — forms, menus, modals,… |
| `keyboard-review` | "Review keyboard navigation and focus management in an existing interface. Chains: keyboard-navigation, feedback-and-status. Use when testing or reviewing keyboard accessibility… |
| `law-of-figure-ground` | Apply the Law of Figure-Ground — establish which layer is foreground and actionable versus background. Use when designing modals, overlays, and depth. For emphasising one element among… |
| `law-of-proximity` | Apply the Law of Proximity — spatial closeness groups elements more strongly than any other cue. Use when spacing alone must carry grouping. For grouping via containers use… |
| `light-mode-paper-technical` | "Create a light-mode technical design system with warm paper surfaces, dark outer framing, subtle diagonal texture, precise bracketed geometry, and restrained accent signals." |
| `link-text-design` | "Write link text that makes sense out of context for screen reader users and improves usability for everyone. Use when writing or reviewing links, calls to action, navigation labels, or… |
| `memory-load-reduction` | "Design interfaces that minimise demands on working memory. Use when designing multi-step flows, dashboards, comparison tools, forms that span multiple screens, or any interface where… |
| `metrics-definition` | Define UX metrics and KPIs that connect design decisions to measurable outcomes. Use when choosing what to measure. For presenting the results afterwards, use `design-impact-reporting`… |
| `multi-modal-input` | "Design interfaces that offer multiple input methods so users can choose what works for their abilities and context. Use when designing any interactive system where users provide input —… |
| `multimodal-orchestration` | Coordinating text, image, voice, and tool-use modalities in a single interaction. |
| `navigation-patterns` | Select and design a navigation pattern — tabs, drawer, hierarchy, or hub — matched to product structure and user tasks. Use when choosing how users move between sections. For the… |
| `nested-container-clean-agency` | "Create a clean agency design system built from nested containers, with an outer editorial shell, inset dark feature blocks, rounded premium cards, and restrained accent color." |
| `onboarding-design` | Design the first-run experience — activation path, progressive disclosure, and time to first value. Use for a user's very first session. For the mechanics of the signup form itself, use… |
| `orange-clean-paper-saas` | "Create a clean paper-toned SaaS design system with warm neutrals, orange accent signals, rounded premium forms, and polished product illustration surfaces." |
| `pattern-library` | Structure a pattern entry — problem context, solution, usage examples, and related patterns. Use when documenting a recurring solution rather than a component. For a single component's… |
| `performance-profiling` | Guide performance profiling for Apple platform apps with Instruments, Xcode diagnostics, and MetricKit. Use when investigating app hangs, stutters, high CPU, memory leaks, memory growth,… |
| `pick-ui-library` | Pick the right library for a given frontend task from a curated, opinionated list — numbers, OTP inputs, charts, command menus, virtualization, drag and drop, toasts, state, styling, and… |
| `ponytail` | > Forces the laziest solution that actually works, simplest, shortest, most minimal. Channels a senior dev who has seen everything: question whether the task needs to exist at all… |
| `product-proof-saas` | Create or redesign SaaS and AI product landing pages where a real workflow, interface, or deterministic demo is the central proof. Use for pale atmospheric shells, product UI in the… |
| `prototype` | Build multiple genuinely different versions of a UI piece you describe, rendered behind a visual picker so you can flip through them live and promote the one that feels right. Only runs… |
| `review` | "Run a full cognitive accessibility review of a flow, screen, or interface. Chains: cognitive-load-assessment, plain-language-design, wayfinding-navigation, error-prevention-recovery,… |
| `scroll-scrubbed-visual-sequence` | Build reversible scroll-controlled visual transformations with a pinned or sticky stage, normalized progress, and video, image-sequence, canvas, SVG, or DOM renderers. Use for hero… |
| `search-ux` | Design search — query input, zero results, refinement, and result presentation. Use when users retrieve rather than browse. For browse structure, use `navigation-patterns`. |
| `simplified-views` | "Design simplified and reduced-complexity views of interfaces for users who need less visual noise and fewer options. Use when designing settings, dashboards, complex tools, or any… |
| `skeuomorphic-ui` | Create skeuomorphic web UI surfaces with layered gradients, stacked inner and outer shadows, reflective gradient borders, micro texture, and embossed text or icon details. Use when asked… |
| `slideshow` | > Author a HyperFrames slideshow — a presentation, pitch deck, or interactive deck with discrete slides, fragment reveals, branching, hotspot navigation, and built-in presenter mode with… |
| `state-machine` | Model component behaviour as explicit states, events, and transitions. Use when a component has many interacting states that must be exhaustive. For the feel and feedback of a single… |
| `tech-green-dark-mode-modern` | "Create a modern dark-mode technical design system with matte-black surfaces, emerald signal accents, mono system labeling, framed dashboard cards, and restrained glow." |
| `touch-target-design` | "Design touch targets and pointer interactions that work for people with motor difficulties, tremors, limited dexterity, or who use assistive pointing devices. Use when designing… |
| `trust-calibration` | Helping users form warranted trust in the AI — neither overtrust nor undertrust — through deliberate confidence and source signalling. |
| `tune-enemy-ai` | Build, debug, balance, or test combat enemy AI for playable action games. Use for aggro, target selection, navigation, spacing, attack choices, telegraphs, retreats, boss behavior,… |
| `ux-writing` | Write interface copy — microcopy, error messages, empty states, and CTAs. Use when the words are the deliverable. For content structure and ownership, use `content-strategy` (ux-strategy). |
| `variant` | Builds multiple variants of a component you're working on and helps you iterate and pick one. |
| `version-control-strategy` | Define version control for design files, components, and libraries — branching, naming, and release. Use when file history is chaotic. For design system contribution rules, use… |
| `vision-skills` | >- Local vision CLIs: glance (describe/ask/OCR an image), ground (locate a target, pixel box), detect (element inventory), trace (image to SVG geometry), crop (cut a pixel box to a… |
| `voice-interaction` | "Design voice interactions and speech interfaces that work for people with diverse speech patterns, accents, and communication styles. Use when designing voice commands, voice search,… |
| `wayfinding-navigation` | "Design navigation and information architecture for cognitive accessibility. Use when designing or reviewing navigation, site maps, page hierarchies, breadcrumbs, search, multi-step… |
| `wizard` | Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an… |

### Everything else, by category (184)


**Engineering & Code** (28)

| Skill | What it does |
|---|---|
| `ask-matt` | Ask which skill or flow fits your situation. A router over the skills in this repo. |
| `aura-asset-images` | "Use when you need high-quality stock-style images from Aura Assets (aura.build/assets) similar to Unsplash for design mockups and marketing: backgrounds, abstract wallpapers,… |
| `behavioural-analytics` | Read funnels, retention curves, and event data as a designer — separating a design problem from a tracking artefact. Use when handed product data you did not design and asked why people… |
| `bias-detection-design` | Designing review workflows to surface and mitigate bias in AI outputs. |
| `build-game-inventory` | Build or repair game inventory, loot, equipment, tooltips, drag-and-drop, persistence, and progression systems. Use for item schemas, pickup flows, stack rules, equipment slots, atomic… |
| `code-review` | "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the… |
| `comparative-evaluation` | A/B testing, side-by-side comparison, and preference ranking for AI outputs. |
| `concept-selection` | Choose between competing concepts against criteria fixed in advance, and record what each rejected concept was testing. Use when several directions are alive and one has to win. For… |
| `design-impact-reporting` | Communicate design's contribution to business and user outcomes in stakeholder language. Use when reporting results upward. For choosing the metrics in the first place, use… |
| `design-sprint-plan` | Plan and facilitate a design sprint from challenge framing through prototype testing. Use when compressing discovery into days. For ongoing team cadence, use `team-workflow`. |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow. |
| `doherty-threshold` | Apply the Doherty Threshold — keep system response under 400ms to preserve user flow. Use when diagnosing perceived slowness or setting a performance budget. For what to show during… |
| `full-output-enforcement` | Overrides default LLM truncation behavior. Enforces complete code generation, bans placeholder patterns, and handles token-limit splits cleanly. Apply to any task requiring exhaustive,… |
| `git-guardrails-claude-code` | Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add… |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `human-in-the-loop` | Designing intervention points where humans review, approve, or redirect agent work. |
| `implement` | "Implement a piece of work based on a spec or set of tickets." |
| `implement-spec` | "Implement the result of /to-spec and /to-tickets in code." |
| `improve-codebase-architecture` | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick. |
| `install-anti-slop` | Install, configure, update, or upgrade vendored anti-slop Oxlint plugins. Use when adding anti-slop, picking up upstream rules or fixes, or migrating an existing installation while… |
| `iterate-until-verified` | Apply a prompt-agnostic execution and verification loop to any substantial task while preserving the original request. Use when the user asks to fan out work, use subagents or… |
| `observability-design` | Making multi-agent workflows visible and debuggable for designers and developers. |
| `ponytail-debt` | > Harvest every `ponytail:` comment in the codebase into a debt ledger, so the deliberate shortcuts and deferrals ponytail leaves behind get tracked instead of rotting into "later means… |
| `ponytail-gain` | > Show ponytail's measured impact as a compact scoreboard: less code, less cost, more speed, from the benchmark medians. One-shot display, not a persistent mode, and not a per-repo… |
| `prompt-versioning` | Managing prompt iterations, testing changes, and tracking what works. |
| `prototype-strategy` | Choose prototype fidelity and method to match the design question and the decision at stake. Use before building a prototype. For what to test once it exists, use `test-scenario`. |
| `tdd` | Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests. |
| `workflow-score-to-target` | Score work out of 10 against a clear rubric, then improve it round by round until every item reaches the target score the user named (for example "get it to 8 out of 10", "bring… |

**Other / Unclassified** (31)

| Skill | What it does |
|---|---|
| `atmosphere-background` | "Create a dark atmospheric background with drifting vertical light folds, screen-blended glow, and a concentrated luminous corner or lower-edge bloom." |
| `chain-of-thought-design` | Designing reasoning chains that produce better outputs. |
| `consent-and-agency` | Designing for informed user consent, opt-out, and human override. |
| `corner-lasers` | "Create a corner-anchored laser composition with thin beams, a bright emitter node, bloom, and atmospheric glow or fog." |
| `cultural-adaptation` | Adapting AI behavior for different cultural contexts, languages, and norms. |
| `design-principles` | Define actionable principles that resolve trade-offs when the team disagrees. Use when the same decisions keep getting relitigated. For a single project's framing, use `design-brief`. |
| `design-system-governance` | Define how the system evolves — contribution model, versioning, deprecation, and change management. Use when multiple teams contribute. For driving uptake use `design-system-adoption`… |
| `escalation-design` | When and how AI should escalate to humans, refuse, or ask for clarification. |
| `feedback-loops` | User correction, thumbs up/down, inline editing, and reinforcement signals. |
| `feedback-patterns` | Design confirmations, status updates, and notifications that tell users an action registered. Use when the system must acknowledge success or change. For waiting states use… |
| `few-shot-patterns` | Crafting examples that steer AI behavior effectively. |
| `gesture-patterns` | Design gesture interactions for touch and pointer — swipe, drag, long-press, and their discoverability. Use when input is gestural. For OS-standard gestures on iOS and Android, use… |
| `guardrail-design` | Defining behavioral boundaries — what the AI should and shouldn't do. |
| `harm-anticipation` | Proactively identifying failure modes, misuse, and unintended consequences. |
| `jakobs-law` | Apply Jakob's Law — users expect your product to work like the others they already use. Use when deciding whether to innovate on a familiar pattern. For OS-mandated conventions… |
| `kb-retriever` | 面向本地知识库目录的检索和问答助手。核心流程：(1)分层索引导航 (2)遇到PDF/Excel时必须先读取references学习处理方法 (3)处理文件后再检索。按文件类型组合使用 grep、Read、pdfplumber、pandas 进行渐进式检索，避免整文件加载。用户问题涉及"从知识库目录回答问题/检索信息/查资料"时使用。 |
| `longitudinal-measurement` | Tracking AI product quality over time — drift, degradation, and improvement. |
| `mixed-initiative-flow` | When the AI leads vs. when the user leads, and how to hand off control. |
| `number-details` | "Add decorative 01, 02, 03 numeric detail markers." |
| `opportunity-framework` | Identify, score, and prioritise design opportunities against impact and effort. Use when there are more ideas than capacity. For framing the one you choose, use `design-brief`. |
| `output-quality-rubrics` | Defining what "good" looks like for AI outputs — accuracy, relevance, helpfulness. |
| `parallel-concepts` | Build several genuinely different solutions to the same problem at once, spread across what the user does rather than how it looks. Use when one direction is on the table and the team is… |
| `platform-conventions` | Design to iOS and Android conventions — what each OS mandates, where they diverge, and when to unify. Use when shipping native apps. For breakpoint adaptation use `responsive-design`;… |
| `serial-position-effect` | Apply the Serial Position Effect — first and last items in a sequence are recalled best. Use when ordering menus, lists, and steps. For emphasising one item regardless of its position,… |
| `service-blueprint` | Map service delivery across frontstage actions, backstage processes, and supporting systems. Use when staff and operations are part of the experience. For the customer-visible layer… |
| `stakeholder-alignment` | Build alignment artifacts — responsibility matrices, decision rights, and communication plans. Use when unclear ownership stalls decisions. For persuading in the moment, use… |
| `to-questionnaire` | Turn a decision you can't fully answer into a questionnaire for someone else to fill in. |
| `transparency-patterns` | Showing users what the AI knows, doesn't know, and how confident it is. |
| `unsplash-asset-images` | Use when you need to pick high-quality Unsplash images for product/design assets (avatars, headshots, portraits, large website backgrounds, and abstract wallpapers) and output real… |
| `user-satisfaction-signals` | Interpreting implicit and explicit feedback — edits, regenerations, abandonment. |
| `value-specification` | Translating organisational values and user expectations into system constraints. |

**UX Research & Law** (27)

| Skill | What it does |
|---|---|
| `card-sort-analysis` | Analyse open or closed card sort results into a proposed grouping and label set. Use after running a sort study. For turning that evidence into a full structure, use… |
| `case-study` | Craft a portfolio case study with narrative arc, process evidence, and outcomes. Use when telling a project's story to an external audience. For an internal stakeholder deck, use… |
| `diary-study-plan` | Design a diary study — prompts, cadence, duration, participant criteria, and analysis frame. Use when behaviour unfolds over days or weeks. For a single-session study, use… |
| `error-personality` | How the AI communicates mistakes, uncertainty, and limitations gracefully. |
| `experience-map` | Map the full ecosystem of touchpoints, channels, and relationships across a service. Use when the experience spans more than one product. For one persona's linear journey use… |
| `fitts-law` | Apply Fitts's Law — target acquisition time depends on size and distance. Use when sizing and positioning controls, especially for touch. For how many controls to show at once, use… |
| `grill-me` | A relentless interview to sharpen a plan or design. |
| `grill-with-docs` | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. |
| `hicks-law` | Apply Hick's Law — decision time grows with the number of simultaneous choices. Use when a screen offers too many options at once. For how many items survive in memory afterwards, use… |
| `interview-script` | Write a structured interview guide — warm-up, core exploration, and wrap-up. Use before running interviews. For analysing what comes back, use `summarize-interview`. |
| `law-of-closure` | Apply the Law of Closure — the eye completes implied shapes from partial forms. Use when reducing visual weight by dropping borders or letting negative space suggest structure. For… |
| `millers-law` | Apply Miller's Law — chunk information into groups of about four to fit working memory. Use when grouping fields, menu items, or steps. For reducing the number of choices offered, use… |
| `operational-enterprise-ai` | Create or redesign enterprise AI, automation, security, and operations product pages that explain system boundaries, approvals, auditability, exceptions, and rollback. Use for dark… |
| `peak-end-rule` | Apply the Peak-End Rule — a flow is remembered by its most intense moment and its last. Use when designing completion, celebration, or cancellation moments. For sustaining engagement… |
| `persona-architecture` | Defining AI character, voice, and personality traits. |
| `presentation-deck` | Structure a design presentation for a specific audience and decision. Use when presenting internally. For a portfolio narrative use `case-study`; for the written argument use… |
| `progressive-disclosure` | Revealing AI capability gradually to match user mental models. |
| `qual-quant-triangulation` | Reconcile what the numbers say with what users say, and design the study that settles it rather than restates it. Use when behavioural data and research findings point different ways.… |
| `research` | Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered,… |
| `research-repository` | Build a repository that makes findings findable, reusable, and cumulative across teams. Use when the same research keeps getting redone. For synthesising one study, use `affinity-diagram`. |
| `survey-design` | Design unbiased survey instruments — question wording, scales, and sampling — to measure attitudes at scale. Use when you need quantitative breadth. For behavioural experiments, use… |
| `teslers-law` | Apply Tesler's Law — every process has irreducible complexity that someone must absorb. Use when deciding whether the product or the user carries it. For reducing apparent choice, use… |
| `test-scenario` | Write realistic usability task scenarios with success criteria and facilitation notes. Use when you have a study and need the tasks. For the surrounding study design, use… |
| `to-spec` | "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed." |
| `usability-test-plan` | Design a usability study — research questions, methodology, participant criteria, metrics, and facilitation guide. Use when planning the study as a whole. For writing the task scenarios… |
| `von-restorff-effect` | Apply the Von Restorff Effect — the element that differs from its neighbours is the one remembered. Use when a single action must dominate. For overall ordering rather than… |
| `write-like-meng-on-x` | Write, rewrite, review, or continuously refine X/Twitter posts in Meng To's current voice using his deduplicated authored-post corpus, personal and product context, shared resources, and… |

**Accessibility** (22)

| Skill | What it does |
|---|---|
| `a-b-test-design` | Design an A/B experiment — hypothesis, variants, primary metric, and sample size. Use when a change can be measured quantitatively at scale. For observing behaviour qualitatively, use… |
| `ability-spectrum-mapping` | "Map how a product or feature works across the full spectrum of human ability — not just 'can use' and 'can't use'. Use when planning accessibility coverage, identifying gaps, or… |
| `accessibility-debt-tracking` | "Track and manage accessibility debt — known accessibility issues that have been deferred. Use when managing a backlog of accessibility issues, planning remediation, or when… |
| `accessibility-testing-strategy` | "Plan what to test, how to test, and who should test for accessibility. Use when defining a testing approach, planning QA, setting up automated and manual testing, or deciding what level… |
| `alt-text-design` | "Write meaningful alternative text for images, charts, diagrams, and visual content. Use when creating or reviewing alt text, image descriptions, chart summaries, or any visual content… |
| `assistive-technology-scenarios` | "Write usage scenarios that include assistive technology and diverse interaction methods. Use when writing scenarios, use cases, user journeys, or storyboards. Triggers on: assistive… |
| `audit-stories` | "Audit user stories for disability inclusion. Chains: inclusive-user-stories, edge-case-identification. Use when reviewing an existing backlog, sprint, or set of user stories to check… |
| `contextual-help-design` | "Design help systems and support patterns that work for people with cognitive disabilities. Use when designing help content, tooltips, onboarding, FAQs, support flows, documentation, or… |
| `decision-documentation` | "Document accessibility decisions and the reasoning behind them so they survive team changes, redesigns, and time. Use when making accessibility tradeoffs, choosing between approaches,… |
| `disability-inclusive-personas` | "Create user personas that include disability as a natural dimension of human diversity — not as a separate 'accessibility persona'. Use when creating personas, user profiles,… |
| `document` | "Document accessibility decisions and tradeoffs for a feature. Chains: decision-documentation, tradeoff-analysis, compliance-mapping. Use when a feature is being designed or shipped and… |
| `edge-case-identification` | "Identify and design for edge cases that disproportionately affect users with disabilities. Use when reviewing designs for completeness, planning test cases, or when someone says 'that's… |
| `generate` | "Generate a diverse, inclusive persona set for a product. Chains: disability-inclusive-personas, situational-impairment-mapping, assistive-technology-scenarios, ability-spectrum-mapping.… |
| `handoff` | "Generate an accessibility decision handoff for engineering. Chains: decision-documentation, compliance-mapping, accessibility-testing-strategy. Use when a design is ready for… |
| `inclusive-user-stories` | "Write user stories that account for disability and diverse abilities from the start. Use when writing user stories, acceptance criteria, jobs to be done, or requirements. Triggers on:… |
| `rewrite` | "Rewrite content in plain language while preserving meaning. Chains: readable-content, link-text-design. Use when given content that is too complex, jargon-heavy, or inaccessible for the… |
| `scenario-map` | "Map inclusive usage scenarios across ability spectrums for a product or feature. Chains: ability-spectrum-mapping, situational-impairment-mapping, assistive-technology-scenarios. Use… |
| `situational-impairment-mapping` | "Map situational impairments that affect all users in specific contexts — not just people with permanent disabilities. Use when designing for mobile, outdoor, noisy, stressful, or… |
| `stakeholder-communication` | "Communicate accessibility decisions, requirements, and value to stakeholders who aren't accessibility specialists. Use when presenting accessibility work to leadership, product… |
| `structure` | "Structure content for screen reader and assistive technology use. Chains: heading-structure, alt-text-design, table-accessibility, form-labelling. Use when building a new page,… |
| `test-playable-web-games` | Test a playable browser game end to end with deterministic fixtures and real browser evidence. Use for gameplay QA, regression testing, controls, accessibility, responsive/mobile… |
| `tradeoff-analysis` | "Analyse accessibility tradeoffs when a design decision improves accessibility for one group but may affect another, or when accessibility competes with other requirements. Use when… |

**3D / WebGL / Realtime** (16)

| Skill | What it does |
|---|---|
| `3d-high-poly-models` | Create or integrate highly detailed 3D models with smooth silhouettes, shaped surfaces, believable bevels, and close-up geometry, then prepare suitable runtime LODs and loading. Use when… |
| `3d-high-resolution-textures` | Build sharp, physically coherent high-resolution materials for 3D rendering with appropriate PBR maps, texel density, UV direction, mipmaps, anisotropic filtering, and progressive asset… |
| `3d-ultra-realistic-water` | Build an ultra-realistic open ocean in Three.js with a deep-water Gerstner spectrum shaded per pixel from analytic derivatives, each wave faded at its own pixel footprint, plus Fresnel… |
| `build-game-audio-feedback` | Design or implement responsive audio feedback for a Three.js or web game. Use for action sounds, combat layers, music states, spatial audio, mix priorities, mute controls, accessibility,… |
| `build-game-camera-controls` | Implement or tune Three.js game cameras. Use for isometric framing, follow behavior, orbit/zoom limits, occlusion, lock-on, camera shake, touch camera controls, and camera regression tests. |
| `build-game-map-editor` | Build, extend, or audit production-linked browser map editors for Three.js and isometric games. Use when Codex needs to create a private director view, derive a versioned editor document… |
| `build-isometric-arpg` | Build or extend a playable isometric action RPG in Three.js, React, or similar web technology. Use for game-loop architecture, camera and movement, zones, combat integration, content… |
| `build-wireframe-scan-reveal` | Reveal Three.js geometry with an expanding world-space scan whose wire cage leads the solid surface, then burns away. Use for wireframe scanning, radial mesh reveals, survey pulses,… |
| `business-design` | Read financials, map competitive landscapes, and argue design decisions in the language of value. Use when defending design to commercial stakeholders. For the live negotiation itself,… |
| `cobejs` | Use when adding a lightweight interactive globe with cobe (canvas setup, markers, interaction, performance, integration with React/Next.js). |
| `implement-fog-of-war` | Implement, tune, debug, or validate soft wall-aware fog of war and gameplay perception in Three.js action games. Use for orthographic or isometric visibility masks, obstacle-aware line… |
| `matterjs` | Use when implementing 2D physics interactions with Matter.js, including Engine/World setup, Render/Runner configuration, adding bodies and constraints, and scroll/interaction-friendly… |
| `setup-pre-commit` | Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged,… |
| `ship-web-games` | Package, deploy, and verify a playable Three.js or web game. Use for release builds, asset delivery, private/public deployment, production smoke tests, browser proof, release notes,… |
| `talking-head-recut` | Package an existing talking-head / interview / podcast video with timed, designed GRAPHIC OVERLAY cards — kinetic titles, lower-thirds, data callouts, quotes, side panels,… |
| `webgl-landing-steering` | Use when creating or refining WebGL-heavy landing pages and you need to steer toward a specific visual outcome (premium, technical, playful, cinematic) while balancing conversion… |

**Content, Copy & Voice** (21)

| Skill | What it does |
|---|---|
| `audit-verify-explain-grade-5` | Audit work, verify claims with concrete evidence, and explain the result in simple grade-5 language. Use when the user asks to review, audit, check, verify, explain a change, explain a… |
| `constraint-specification` | Defining output format, length, tone, and content boundaries within prompts. |
| `design-action-combat` | Design, implement, tune, or test readable tactical action combat for web games. Use for attack timing, guard and dodge windows, hit contact, posture, lock-on, weapons, boss phases,… |
| `design-rationale` | Write rationale connecting decisions to user needs, business goals, and principles. Use when a decision needs defending in writing. For a live conversation, use `design-negotiation`. |
| `dither-background` | Create a dark monochrome procedural background with enlarged square pixels and visible Bayer-style ordered dithering. Use when a page needs an atmospheric near-black dither field, broad… |
| `domain-modeling` | Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or editing an ADR. |
| `domain-voice` | Tailoring AI behavior for specific professional domains. |
| `failure-taxonomy` | Classifying AI failures — hallucination, refusal, irrelevance, tone mismatch, latency. |
| `loading-states` | Design waiting experiences — spinners, skeletons, optimistic updates, and progressive reveal. Use when content takes time to arrive. For the latency budget itself use… |
| `localization-design` | Design for multiple languages, writing directions, and cultural contexts — text expansion, RTL mirroring, and locale formats. Use when shipping beyond one locale. For the words… |
| `migrate-to-shoehorn` | Migrate test files from `as` type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace `as` in tests, or needs partial test data. |
| `pr` | "Use when writing a PR body." |
| `publish-project-to-github` | Package a finished local project into an intentional GitHub repository, create a strong README and visual preview, push it safely, configure a public GitHub Pages URL when the project is… |
| `setup-ts-deep-modules` | Wire dependency-cruiser into a TypeScript repo so each package is a deep module, with implementation hidden in subfolders and reachable only through its entry-point files. User-invoked. |
| `solar-duotone-bold` | "Use Iconify Solar Duotone Bold icon style." |
| `tone-calibration` | Adjusting formality, warmth, confidence, and style per context. |
| `write-swift` | How to write modern Swift well — modeling with value types, Swift 6 data-race safety and approachable concurrency (@concurrent, main-actor-by-default, actors, task groups), protocols and… |
| `writing-beats` | Writing, exploit; assemble raw material into a journey of beats, grounding each term before a beat leans on it. |
| `writing-for-agents` | Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. |
| `writing-fragments` | "Writing, explore: mine raw fragments, no structure yet." |
| `writing-shape` | "Writing, exploit: shape raw material into an article, paragraph by paragraph." |

**Agent, Workflow & Meta** (16)

| Skill | What it does |
|---|---|
| `agent-role-design` | Defining what each agent does, knows, and owns in a multi-agent system. |
| `claude-handoff` | Hand the current conversation off to a fresh background agent that picks up the work immediately. |
| `context-engineering` | Designing what information goes into the context window and in what order. |
| `context-window-design` | Designing around token limits, memory, and conversation persistence. |
| `failure-recovery` | What happens when an agent fails — retry, fallback, escalate, or graceful degradation. |
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending… |
| `loop-me` | Grill me about specs for the workflows I want to build, within this workspace. |
| `ponytail-help` | > Quick-reference card for all ponytail modes, skills, and commands. One-shot display, not a persistent mode. Trigger: /ponytail-help, "ponytail help", "what ponytail commands", "how do… |
| `state-management` | Managing shared context, memory, and state across multiple agents. |
| `system-prompt-structure` | Anatomy of effective system prompts — role, context, constraints, format. |
| `task-decomposition` | Breaking complex user goals into subtasks that agents can handle. |
| `teach` | Teach the user a new skill or concept, within this workspace. |
| `team-workflow` | Design the team's operating rhythm — task management, collaboration rituals, and tooling. Use when the day-to-day cadence needs structure. For a time-boxed sprint, use `design-sprint-plan`. |
| `template-design` | Creating reusable, parameterised prompt templates for consistent outputs. |
| `triage` | Move issues and external PRs through a state machine of triage roles, categorise, verify, grill if needed, and write agent-ready briefs. |
| `wayfinder` | Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the… |

**Video & Motion Graphics** (9)

| Skill | What it does |
|---|---|
| `beautiful-article` | "把用户提供的素材（网页 URL / PDF / DOCX / Markdown / 纯文本 / 截图 / 粘贴材料）编辑、设计成一篇美丽的、可离线打开和分享的**单文件 HTML 网页文章**。基于 reacticle 组件协议：不手写裸 HTML/CSS，而用语义组件 + 受主题约束的 Raw 自由层；按 source→规划→双确认→生成→终审→修复的小型… |
| `elevenlabs-tts` | Generate ElevenLabs text-to-speech audio from scripts or inline text using local voice profiles. Use when the user asks for ElevenLabs, text-to-speech, TTS, narration, voiceover, speech… |
| `embedded-captions` | > Add captions or subtitles to an existing single-subject talking-head video without editing the footage. Use for plain verbatim captions, cinematic captions embedded behind the subject,… |
| `hyperframes-core` | The HyperFrames composition contract — build one renderable project. Use for composition structure, the `data-*` timing attributes, `class="clip"`, tracks, sub-compositions, variables,… |
| `music-to-video` | "Turn a music track (an audio file, a video to pull audio from, or a track generated from a mood brief) into a beat-synced video — lyric video, slideshow, or kinetic promo. The music… |
| `pr-to-video` | "Turn a GitHub pull request (a PR URL, owner/repo#N, or 'this PR' in a checked-out repo) into a code-change explainer video — changelog, feature reveal, fix, or refactor walkthrough… |
| `product-launch-video` | "Turn a product or marketing URL, pasted script, or brief into a product launch / promo video — SaaS promos, feature reveals, product demos, app and company launches. Use when the user… |
| `table-accessibility` | "Design data tables that work for screen readers and cognitive accessibility. Use when creating or reviewing tables, data grids, comparison tables, pricing tables, or any tabular data.… |
| `web-video-presentation` | 把一篇文章或口播稿，做成"看起来像视频"的点击驱动 16:9 网页演示，可选合成口播音频。流程：原始文章 → **一次产出**口播稿 + outline 开发计划 → 用户**一次对齐** 5 件事（稿子 / outline / 主题 / 素材 / 开发模式）→ 网页开发（逐章 / 顺序 / 并行）→ 可选音频合成（provider-agnostic：内置… |

**Image & Visual Generation** (8)

| Skill | What it does |
|---|---|
| `article-prompts-to-skills` | Convert an article, tutorial, or prompt pack into focused reusable AgentSkills, one independent capability per skill, with portable instructions, example prompts, working demos, preview… |
| `company-logos` | "Use Iconify Simple Icons logos (64x64) instead of text logos." |
| `design-brief` | Write a project brief — problem space, constraints, audience, and success criteria. Use at kickoff for one specific project. For long-horizon aspiration use `north-star-vision`; for… |
| `diagnose-crash` | > Diagnose why a program crashed on this machine, from a systemd-coredump core dump. Use when a process has segfaulted, aborted, or otherwise dumped core, when asked why an application… |
| `icon-system` | Specify an icon system — grid, sizing, stroke weight, naming, categories, and implementation. Use when standardising iconography. For broader illustration, use `illustration-style`… |
| `north-star-vision` | Articulate a long-horizon product vision that aligns teams and anchors strategy. Use when direction is contested or absent. For near-term project scope, use `design-brief`. |
| `workflow-ship-change` | Ship every change the way the user requires, with the guardrails. Take screenshots of the start, the key moment and the result; give the change its own changelog version with pictures;… |
| `workflow-threads-manager` | Oversee the other Claude threads (sessions) working on the same project. Check what each is doing, confirm finished work is merged to main, has its changelog entry with screenshots, and… |

**Productivity & Scaffolding** (4)

| Skill | What it does |
|---|---|
| `conversation-patterns` | Turn-taking, repair sequences, grounding, and dialogue structure for human-AI interaction. |
| `retro` | "Conduct a retrospective on a coding session." |
| `scaffold-exercises` | Create exercise directory structures with sections, problems, solutions, and explainers that pass linting. Use when user wants to scaffold exercises, create exercise stubs, or set up a… |
| `wait-what` | "Stop. That last message did not land: re-pitch it." |

**Business, Product & Data** (2)

| Skill | What it does |
|---|---|
| `task-success-metrics` | Measuring whether the AI actually helped users accomplish their goals. |
| `to-tickets` | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per… |

---

## Sources

- Anthropic — [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [Skills in Claude Code](https://code.claude.com/docs/en/skills.md) · [Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) · [Complete Guide to Building Skills (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- impeccable — [computertech.co review 8.4/10](https://computertech.co/impeccable-ai-review/) · [Claude Codex review](https://claude-codex.fr/en/skills/impeccable/) · [mejba.me hands-on test](https://www.mejba.me/blog/impeccable-claude-code-design-skill) · [GhTrends](https://ghtrends.dev/pbakaus/impeccable/) · [official docs](https://impeccable.style/designing) · [Julian Zhou](https://julianzhou.com/en/curated/impeccable-23-design-commands-46-deterministic-rules-for-ai-frontends)
- taste-skill — [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) · [SKILL.md](https://github.com/Leonxlnx/taste-skill/blob/HEAD/skills/taste-skill/SKILL.md) · [tasteskill.dev](https://www.tasteskill.dev/) · [runany.dev](https://runany.dev/blog/taste-skill-anti-slop-frontend/) · [Kondasamy Jayaraman](https://kondasamy.com/blog/2026/taste-skill-anti-slop-frontend-framework/)
- Reddit r/ClaudeCode — [Stop messing with skills](https://www.reddit.com/r/ClaudeCode/comments/1ve5dc7/stop_messing_your_claude_with_skills/) · [How many skills is too many](https://www.reddit.com/r/ClaudeCode/comments/1p8wipb/how_many_claude_skills_are_too_many/) · [Your SKILL.md is 3x more expensive](https://www.reddit.com/r/ClaudeCode/comments/1t26xrj/your_skillmd_is_likely_3x_more_expensive_than_it/) · [What skills are you using](https://www.reddit.com/r/ClaudeCode/comments/1rp02ln/what_skills_are_you_using/) · [Context engineering guide](https://www.reddit.com/r/ClaudeCode/comments/1vepp0s/a_full_guide_to_context_engineering_in_claude_code/)

**Note on coverage:** the design-skill research above is from named published reviews and the projects' own documentation. The `better-*`, `antislop*`, `no-ai-design-slop` and `critique-*` families have **no** third-party evaluations I could find — they're covered from their own SKILL.md and by inference from their siblings. Treat them as unproven rather than as quiet favourites.

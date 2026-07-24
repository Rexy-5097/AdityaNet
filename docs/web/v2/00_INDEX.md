# AdityaNet v2 Frontend — Planning Set

**Date:** 2026-07-24 · **Role:** Creative Technologist · **Status:** planning complete, **no code written**

The v1 visual implementation is abandoned in full: the hero, the Sun shader, every artistic
rendering, all ~600 lines of GLSL. The [Experience Bible](../EXPERIENCE_BIBLE.md) still
governs the story and the three registers. Everything else starts from zero.

## The operating rule

Never *"Can I code this?"* Always *"Does a mature implementation already exist?"*
If yes, integrate it. Custom work is proposed in exactly two places in this entire set, and
both are argued explicitly rather than assumed.

## Where originality is permitted

Storytelling · scientific honesty · the Artistic→Schematic→Measured transition ·
camera choreography · interaction design · information architecture.

**Nowhere else.** Effects, materials, scroll, easing, post-processing, charts, fonts, icons
and lighting are all imported.

## Documents

| # | Document | What it settles |
|---|---|---|
| 1 | [Visual Direction](01_VISUAL_DIRECTION.md) | The governing look; what "Apple/SpaceX pacing" means concretely; the restraint budget |
| 2 | [Effect Catalogue](02_EFFECT_CATALOGUE.md) | Every WebGL effect: purpose, library, cost, support, a11y, composability |
| 3 | [Interaction Catalogue](03_INTERACTION_CATALOGUE.md) | Scroll, hover, cursor, focus, microinteractions, motion hierarchy |
| 4 | [Camera Choreography](04_CAMERA_CHOREOGRAPHY.md) | The shot list — the single most original artefact here |
| 5 | [Asset Manifest](05_ASSET_MANIFEST.md) | Every byte shipped, with verified licence and budget |
| 6 | [Library Selection Matrix](06_LIBRARY_MATRIX.md) | Chosen vs rejected, with reasons for both |
| 7 | [Frontend Architecture](07_FRONTEND_ARCHITECTURE.md) | Astro islands, persistent canvas, state, the `derive(t)` contract |
| 8 | [User Journey](08_USER_JOURNEY.md) | Entry to evidence, including the sceptic's path |
| 9 | **[Experience Script](09_EXPERIENCE_SCRIPT.md)** | **Governing document.** Per-scene emotion, information, and the visual carrying them. Every effect justifies itself here or is removed |

## Approved decisions (owner, 2026-07-24)

| Decision | Resolution |
|---|---|
| Register pivot | **LUT colour grading** — three `.cube` grades cross-faded by `t` |
| Hero footage | **SVS slow-rotation Sun clip** (not a flare event) |
| Spacecraft | **Schematic primitives.** No stock mesh |
| Scroll | **GSAP ScrollTrigger + Lenis** |

Research phase **approved**. Docs 1–8 are settled; Doc 9 governs where it conflicts with
Docs 2 and 3.

## Planning freeze

Planning documents are **frozen** as of 2026-07-24. Critical corrections only, and each
must be recorded in the table below with its justification.

| # | Doc | Correction | Why it was critical |
|---|---|---|---|
| C1 | [Doc 9](09_EXPERIENCE_SCRIPT.md) §9.11 | Vignette reclassified from *expressive* to *ambient framing* (alongside SMAA and dither); held constant through Registers A and S | The Script's per-scene stacks include vignette in scenes 1/3/5 but not 2/4. Implemented literally this produces a visible on/off/on/off flicker of the frame edge — a defect. The ≤3 expressive cap is still honoured; no scene gains an effect the Script did not grant it. Recorded in `timeline.ts` |
| C2 | [Doc 9](09_EXPERIENCE_SCRIPT.md) §9.8 | Watermark opacity **holds** across a register boundary; only the string swaps | The original cross-fade left provenance invisible at exactly `t=0.82` — the frame where the number resolves. §9.8 requires provenance to arrive *with* the value. Caught by a failing gate, not by review |
| C3 | [Doc 4](04_CAMERA_CHOREOGRAPHY.md) §4.2 | The camera **holds** 0.24→0.30 while the schematic register establishes; the former shots 5 (orbit begins) and 6 (opening) merge into one sustained move 0.30→0.46 | §4.2 began the orbit at `t=0.24`, the exact A→S register boundary, breaking §4.1 rule 4 ("no motion during a register change") — the rule §4.1 itself names most important. When shot timing conflicts with rule 4, rule 4 wins. Also better honours "one primary mover". Caught by the register-boundary speed invariant, not by review |

## Directional change (owner, 2026-07-24) — video-first, no geometry

The owner redirected the build: **do not create or model any visual assets.** No
procedural Sun, no spacecraft model, no built geometry of any kind. The Sun, space, and
spacecraft are **background video** — real, public-domain footage. Originality lives only
in scroll choreography, camera/scroll movement, transitions, interaction, information
hierarchy, and the scientific narrative. Integrate mature libraries and licensed/public
assets; build an experience, not a renderer.

Consequences:
- **Slices 3–5 (3D scene, craft, crossing) are replaced** by a DOM + video + GSAP + Lenis
  build. The signature technique is scroll-scrubbed video (the visitor's scroll drives the
  footage playhead).
- **`timeline.ts` survives unchanged** — the register/watermark/number contract is exactly
  the narrative infrastructure the owner wants. Slices 1's gates still hold.
- **`camera.ts` (3D spherical camera) is on ice.** There is no 3D scene to move a camera
  through. Its keyframe-timing concept may later drive a 2D Ken-Burns pan/scale on the
  video, but the 3D pose maths is currently unused. Kept, not deleted; tests still green.
- **The previz harness (`/v2-previz`) is superseded** by the real hero on `/v2`.
- **Assets:** real footage only, licence-verified. First asset landed — SDO AIA 171
  (NASA SVS, public domain), transcoded to `public/video/sun-aia171.mp4` (6.3 MB, audio
  stripped, dense keyframes for scrub) + poster.

## Hero: LOCKED (owner, 2026-07-24)

The opening scene on `/v2` is **approved and locked**. No redesign, no story rewrite, no
choreography change, no asset replacement — bug fixes only. Two changes were made at the
moment of approval and nothing since:

- The approved **flare echo** behind THE EVENT (a defocused afterimage of the same
  illustrative footage, peaking at 0.24 opacity).
- **Bug fix:** the island requested `Inter`, which was never installed, so the hero
  silently fell back to system-ui while every other surface rendered in IBM Plex Sans.
  `/v2` now imports the vendored families and the island uses `var(--font-sans)` /
  `var(--font-mono)`. This was a genuine cross-site inconsistency, not a restyle.

## Flagship pass — the rest of the site

**Mission:** every surface after the hero reaches the same craft. Originality stays in
storytelling, choreography and hierarchy; components come from the design system.

**Key constraint honoured:** evidence surfaces ship **~0 KB JS** (CI budget gate). All
scroll choreography is therefore CSS scroll-driven animation (`animation-timeline`), not a
motion library — zero script, compositor-driven, and degrading to plain visible content
where unsupported. Verified post-build: `/findings`, `/validation`, `/pipeline`, `/build`
all still measure **0.0 KB gz JS**.

| Piece | What it does |
|---|---|
| `src/styles/flagship.css` | The design language: display type scale, `.eyebrow` (the hero's mono kicker, promoted to a token), vertical rhythm, CSS-only reveals, scroll-aware header, reading-progress rail, micro-interactions, page transitions |
| `src/components/shell/PageHeader.astro` | One opening for every surface — eyebrow / display-1 / lede |
| `src/components/shell/Section.astro` | Shared section rhythm, optional eyebrow+heading, reveal |
| `Header.astro` | Sticky, backdrop-blurred, solidifies on scroll (CSS scroll-timeline); nav links get a directional underline |
| `BaseLayout.astro` | Progress rail, `page-content` view-transition region, light display weight |

Applied to `/findings` (reference implementation), `/validation`, `/pipeline`, `/data`,
`/build`, and the homepage's evidence section.

**Gates:** `astro check` 0 errors · 78 tests · production build 14 pages · budget gate all
invariants satisfied (contrast, route budgets, evidence consistency, banned lexicon).

**Known remaining inconsistency:** `/` still mounts the **v1 star renderer** (89.9 KB gz,
4 scripts) rather than the locked v2 hero. Promoting `/v2` → `/` and retiring the old
renderer is the next structural step and needs an owner go-ahead, since it replaces the
site's front door.

## Implementation slices

Vertical, reviewable, each validated before the next begins.

| Slice | Scope | Status | Gates |
|---|---|---|---|
| **1** | `derive(t)` contract + gates (`src/experience/v2/timeline.ts`) | ✅ **complete · frozen** | 24 tests; `tsc` clean; eslint clean |
| **2** | Camera subsystem (`src/experience/v2/camera.ts`) | ✅ complete · **on ice** (no 3D scene under the new direction) | 24 behavioral invariants; still green |
| **3** | Flagship video hero — scroll-scrubbed SDO footage + Lenis + GSAP + register overlays (`V2Experience.tsx`, `/v2`) | ✅ **complete · awaiting browser review** | tsc clean; eslint clean; 78 suite passing; scrub + watermark verified; live scroll needs a real browser |
| 4 | Source space + spacecraft footage; extend the arc to the middle beats | pending | Licence-verified public-domain clips only |
| 5 | Evidence / Register B — the number → the real light curve (uPlot) | pending | ~0 KB JS on evidence routes |
| 6 | Reduced-motion + no-video degradation; accessibility pass | pending | Poster path; keyboard; skip-to-evidence |
| 7 | Promote `/v2` → `/`; retire the old hero | pending | Budgets; full gate suite |

## Research base

Techniques were extracted, not copied, from: [Codrops](https://tympanus.net/codrops/)
(2025 review — 51 tutorials, dominant themes 3D/WebGL/R3F; and the Feb 2026 GSAP+Three+Astro
scroll-gallery tutorial, whose *stack* matches ours exactly), the
[pmndrs/postprocessing](https://github.com/pmndrs/postprocessing) effect set,
[drei](http://drei.docs.pmnd.rs/) (~80 helpers), the
[Theatre.js camera fly-through technique](https://tympanus.net/codrops/2023/02/14/animate-a-camera-fly-through-on-scroll-using-theatre-js-and-react-three-fiber/),
and three.js examples.

## Two findings that changed decisions

1. **Theatre.js is stale.** `@theatre/core` and `@theatre/r3f` last published **2024-05-19**
   — ~26 months ago. Every other candidate shipped within months (three 2026-07-01, fiber
   2026-07-08, postprocessing 2026-07-18, lenis 2026-07-15, gsap 2026-04-13, motion
   2026-06-30). It is the best camera-authoring tool available and it is **rejected as a
   runtime dependency** on maintenance risk. See [Doc 4](04_CAMERA_CHOREOGRAPHY.md) §4 for
   the design-time-only compromise.
2. **LUT colour grading is the register system.** The Artistic→Schematic→Measured pivot —
   the project's whole thesis — is expressible as three colour-grading LUTs cross-faded by
   `t`, using the stock `LUTEffect`. This is the highest-leverage discovery in the set:
   the most important idea in AdityaNet needs **no custom shader at all**.

## Sign-off required before code

[Doc 6](06_LIBRARY_MATRIX.md) §5 and [Doc 5](05_ASSET_MANIFEST.md) §6 list the open owner
decisions. Nothing is implemented until those are answered.

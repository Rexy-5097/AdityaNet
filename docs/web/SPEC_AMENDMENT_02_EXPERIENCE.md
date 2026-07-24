<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Sections 18-19. Experience + Audio architecture. Amends PRODUCT_SPECIFICATION.md. -->
<!-- DATE: 2026-07-23 -->

# Amendment 02 — Experience Architecture (Sections 18-19)

**Status: FROZEN.** Amends `PRODUCT_SPECIFICATION.md`. The scientific architecture
(Sections 9-13) is unchanged and unchallenged by this amendment.

## Superseding changes to Parts 1-4

| Ref | Superseded | Now |
|---|---|---|
| P8 | "Visual fidelity must not exceed information content" | **Domain-scoped** (below) |
| §5.5 L2 | "No animation loops" | Loops permitted in Domain A; Domain B requires a permanent archival stamp |
| §7.6 | Bloom / glass / parallax / cinematic transitions banned | Permitted under Domain A rules |
| §11.6 | Landing 180 KB | **Landing 450 KB gz, lazy, post-LCP** (measured; see below) |
| §3.3 | 5 surfaces | **6 surfaces.** `/` IS the experience (no `/explore`); Pipeline restored |
| §9.4 | Next.js | **Astro 5 + React islands** (Sprint 0 measurement: Next floor 184 KB vs Astro 0 KB) |

---

## P8 — Representational Fidelity (final)

> When a visualization represents **measured scientific observations**, its visual
> encoding must not exceed the information content of the underlying data.
>
> When a visualization serves an **experiential or educational** purpose rather than
> representing measured observations, photorealistic and cinematic rendering is
> permitted, provided it is never presented as observational evidence.
>
> **P8.1 — Domain legibility.** A viewer must be able to determine which domain they
> are viewing without reading body text, and that determination must survive being
> screenshotted out of context.

### Domain enforcement (build-gated)

- Every `<canvas>` must be wrapped in `<ExperienceFrame>` (A) or `<EvidenceFrame source={ArtifactRef}>` (B). An unwrapped canvas **fails CI**.
- Domain A renders `ARTISTIC RENDERING · NOT OBSERVATIONAL DATA` **into the WebGL frame buffer**, not the DOM, so it survives screenshot and canvas export.
- Domain B renders `MEASURED · <artifact> · <commit>`.
- `src/experience/` and `src/scientific/` may not import each other (eslint-plugin-boundaries).
- Domain B shader uniforms are prefixed `uData*` and must resolve to an `ArtifactRef`. Domain A uses `uArt*`.
- No `Math.random()` in either domain. All stochastic input is hash-seeded and deterministic.
- No bitmap solar textures. Procedural only — a texture derived from another mission's imagery would import that mission's observations into our frame.

---

## Section 18 — Experience Architecture

### 18.0 Two-door model (FINAL — owner decisions 1 & 2, 2026-07-23)

**`/` is the environment.** The flagship experience is the root route, not a
destination the user must discover. It is one React island, continuous and stateful,
and it is simultaneously the Overview: the project arc, headline metrics, finding
statement, and persona doors are the narrative beats of the experience rather than a
separate page.

**Six primary surfaces:**

| Route | Nature | JS budget |
|---|---|---|
| `/` | Immersive experience + Overview | <=450 KB lazy, post-LCP |
| `/validation` | Evidence, static | <=15 KB |
| `/findings` | Evidence + 2D charts | <=120 KB |
| `/pipeline` | **Interactive reconstruction**, raw SoLEXS -> validated evidence | <=200 KB |
| `/data/[date]` | Scientific viewers | <=260 KB |
| `/build` | Reproduce, API, hashes | <=20 KB (+400 lazy) |

**Two hard requirements that keep `/` honest for the reviewer persona:**

1. **LCP on `/` is HTML text plus a static poster — never the canvas.** The page is
   readable and navigable before the GPU scene exists. Non-negotiable.
2. **A direct evidence affordance is visible without interaction** on first paint. A
   referee must never be required to fly through a star to reach a contradiction
   record. The immersive path and the evidence path are peers.

Evidence routes remain fast Astro doors to the same artifacts. Neither path is lesser.
No cross-route WebGL persistence is required, because the environment never leaves `/`.

### 18.0.1 Pipeline (owner decision 1)

`/pipeline` is restored as a primary surface and is **no longer a static diagram**. It
is an interactive reconstruction of the processing flow from raw SoLEXS/HEL1OS Level-1
products through parsing, version resolution, canonical build, and validation to
scientific evidence. Domain A/B hybrid: the flow rendering is artistic; every node's
counts, hashes, and rule references are Domain B and traceable.

Reversal noted: Part 4 R-A cut Pipeline for persona redundancy with `/build`. That
reasoning held for a static diagram and does not hold for an interactive
reconstruction, which does a different job — system comprehension — that prose does
badly.

### 18.1 Through-line

**The descent from impression to evidence.** Distance from the star is epistemic
distance. Every interaction must move along this axis or it does not belong.

### 18.2 Interaction vocabulary — five verbs

| Verb | Input | Changes |
|---|---|---|
| ORBIT | drag / one finger | viewpoint |
| APPROACH | wheel / pinch | scale-of-view -> representation mode |
| SCRUB | timeline drag / arrows | time within the archive |
| FOCUS | click / tap / Enter | selection; camera frames target |
| INSPECT | hover / keyboard focus | contextual overlay |

Any interaction that is not one of these five must be justified or cut.

### 18.3 Scale-driven semantic modes

| Scale | Mode | Domain | Content |
|---|---|---|---|
| ~50 R-sun | MISSION | A | 866 days of activity as coronal state |
| ~5 R-sun | PERIOD | A->B | Weeks resolve; 581 M/X events become discrete objects |
| ~1 R-sun | EVENT | B | One flare: real light curve, real timestamps |
| interior | SPECTRUM | B | 340-channel spectrogram as navigable surface |

**Signature moment:** crossing MISSION -> EVENT dissolves the artistic rendering into
the scientific one over 1.2 s — bloom decays, lighting flattens, palette shifts to
viridis, frame squares off, watermark transitions A -> B. This is simultaneously the
emotional climax, the honesty mechanism, and the teaching of P8.

### 18.4 Motion — damped springs, never eased keyframes

| Element | Stiffness | Damping ratio |
|---|---|---|
| Camera position / target / focal length | 120 / 90 / 60 | **1.0 (critical — cameras never overshoot)** |
| UI panels | 200 | 0.75 |
| Hover states | 400 | 0.8 |
| Timeline scrub | 300 | 0.9 |

Orbit inertia on release: angular friction 0.94/frame, floor 0.001 rad/s, dt-scaled so
30 fps and 60 fps feel identical.

### 18.5 Latency budgets

| Path | Budget |
|---|---|
| Pointer -> camera response | **same frame (<=16.6 ms)** |
| Hover -> feedback | <=50 ms |
| Click -> focus transition begins | <=50 ms |
| Mode transition -> first frame | <=100 ms |

**Architectural rule:** input never passes through React. Pointer events write to a
mutable store read inside `useFrame`. React state changes only on discrete semantic
events (mode change, selection, panel open) — ~1/s, not 60/s.

### 18.6 Discoverability

1. Proximity response (objects brighten within ~80 px of cursor)
2. Cursor semantics (states which verb is available)
3. First-visit affordance, once, persisted, dismissible
4. Idle invitation after 20 s — pulses **once**, never loops

Prohibited: tutorial modals, coach marks, bouncing scroll chevrons.

### 18.7 State machine

`BOOT -> POSTER -> MISSION <-> PERIOD <-> EVENT <-> SPECTRUM`, with `EVIDENCE` as an
overlay from any state. Hand-rolled discriminated-union reducer (six states do not
justify a dependency). Invalid transitions throw in development.

**Every state is URL-addressable:** `/explore?mode=event&t=2024-05-14T16:49Z`.
Any moment in the environment is linkable and citable.

### 18.8 Touch

One finger = ORBIT. Pinch = APPROACH. Tap = FOCUS. Long-press = INSPECT.
Vertical swipe in the timeline rail = SCRUB. Page scroll is disabled inside the canvas
and re-enabled outside it. A persistent Evidence affordance guarantees the user is
never trapped.

### 18.9 GPU technique

| Concern | Decision |
|---|---|
| Event picking | GPU ID-buffer picking, O(1). Not raycasting |
| Particles | FBO ping-pong simulation, instanced draw |
| Mode LOD | Separate pre-compiled programs, warmed during POSTER |
| Transitions | Cross-fade between render targets (no compile stutter) |
| Grading | Single 32^3 LUT post-tonemap, shared by both domains |
| Renderer | WebGL2. WebGPU deferred behind the render-graph seam |

### 18.10 Quality tiers

| Tier | Trigger | Config | Target |
|---|---|---|---|
| 0 | No WebGL2 / opted out / reduced-motion | Static AVIF poster + full DOM | — |
| 1 | Mobile / integrated / deviceMemory <=4 | No post, DPR 1.0, 2-shell corona, 20k particles | 30 fps |
| 2 | Default | Bloom, DPR <=1.5, full corona, 80k particles | 60 fps |
| 3 | Discrete GPU + concurrency >=8 | Full composer, DPR <=2.0, volumetric, 200k particles | 60 fps |

Probe frame time over first 90 frames post-warm-up; p95 > 20 ms sustained 2 s drops one
tier. **Never upgrade mid-session** (oscillation is worse than a lower tier).

### 18.11 Budgets (measured, not estimated)

Spike 2026-07-23, Vite production build, gzip:

| Configuration | Size |
|---|---|
| three + R3F + drei + postprocessing + React | **314.17 KB gz** |
| three + R3F + React (no drei, no postprocessing) | **292.57 KB gz** |
| **Delta for the entire effects stack** | **21.6 KB** |

**Finding:** three.js core (~245 KB gz) is the floor and is irreducible. The
pre-committed fallback "drop postprocessing if over budget" is **void** — it sacrifices
the whole effects stack for 7%.

**Revised budget: `/explore` <= 450 KB gz**, lazy-loaded post-LCP behind the poster.
Justified because it is one opt-in route, LCP is HTML text + poster (never the canvas),
and evidence routes remain <=15 KB.

| Surface | JS (gz) | LCP |
|---|---|---|
| `/explore` | **<=450 KB lazy** | <1.8 s (text + poster) |
| `/validation` | <=15 KB | <0.8 s |
| `/findings` | <=120 KB | <1.2 s |
| `/build` | <=20 KB (+400 lazy) | <1.0 s |
| `/data/[date]` | <=260 KB | <2.0 s |

Assets: procedural only. Poster AVIF <=90 KB. Total experience assets <=100 KB.

### 18.12 Extensibility seams (designed, not built)

| Future | Seam required at v1 |
|---|---|
| WebGPU | Render-graph abstraction: passes declared as data |
| Multiple cameras | Camera rig interface; active rig is swappable state |
| GPU compute | FBO simulation generalizes |
| XR / VR | Input adapter layer; the five verbs are abstract |
| Plugin visualizations | `VisualizationModule { id, domain, mount, unmount, budget }` |
| Multi-view / collaborative | State machine URL serialization is the sync protocol |

### 18.13 Accessibility

Lighthouse a11y **100 on every surface including `/explore`**. Canvas is `role="img"`
with text alternative, not in tab order, never a focus trap. Reduced motion -> Tier 0
composed still (not a paused scene). No luminance flash >3 Hz (WCAG 2.3.1), enforced in
the tone-mapping pass. Text over 3D sits on a scrim guaranteeing >=7:1. Every fact in
the scene exists in the DOM and on a Tier-2 surface.

### 18.14 Testing

Unit: tier selection, scroll->camera mapping, particle seeding determinism, blackbody.
Compile: every `.glsl` compiles headless. Determinism: same seed + state -> identical
uniforms. **Domain audit:** every canvas wrapped; every `uData*` resolves to an
ArtifactRef; watermark present in rendered output. Fallback: Tier 0 with WebGL mocked
absent; context-loss path. Visual regression: Tier 0 poster only.

---

## Section 19 — Audio Architecture

### 19.1 Principles

1. **Muted by default, always.** Opt-in, persisted, never autoplay.
2. **Audio has domains.** Domain A = atmosphere and UI. Domain B = sonification of
   measured data, which would require chart-grade traceability. **Domain B audio is
   out of scope for v1**; the architecture accommodates it.
3. Sound is never the sole carrier of information (WCAG 1.1.1, 1.4.2).
4. **Synthesized, not sampled** — Web Audio oscillators and filtered noise. 0 bytes
   shipped, no licensing, no repetition fatigue. Mirrors the procedural-texture rule.

### 19.2 Palette

| Cue | Synthesis | Duration | Peak |
|---|---|---|---|
| Hover | 2 kHz sine, 8 ms attack | 40 ms | -32 dBFS |
| Click / focus | 800 + 1200 Hz, fast decay | 80 ms | -24 dBFS |
| Mode transition | Filtered noise sweep, spatialized | 400 ms | -20 dBFS |
| **Domain crossing A->B** | Detune resolving to unison | 1.2 s | -18 dBFS |
| Ambient bed | 2 detuned sub-osc + pink noise, LP | continuous | -42 dBFS |
| Error / invalid | Single low pulse | 120 ms | -28 dBFS |

Only the domain-crossing cue carries semantic weight: dissonance resolving to
consonance as the user passes from impression to evidence. It reinforces the visual
transition; it never replaces it.

### 19.3 Engineering

Web Audio API (not `<audio>` — needs <20 ms latency and spatialization). One
`AudioContext`, created on first user gesture. `PannerNode` for spatial hover. Master
limiter at -6 dBFS; **no cue may ever startle**. Ducked to silence on `document.hidden`;
context suspended when muted (zero CPU). Budget: **0 KB assets, <=6 KB code**.

### 19.4 Accessibility

Off by default. Header toggle adjacent to reduced-motion, persisted.
`prefers-reduced-motion: reduce` **also disables transition and ambient cues**, keeping
only discrete UI confirmation. Every cue duplicates something already visible. Ambient
ducks -12 dB when an `aria-live` region updates.

# 6 · Library Selection Matrix

Licences read from npm registry metadata (`npm view <pkg> license`), not recalled.
Publish dates checked this session as a maintenance signal.

## 6.1 Adopted

| Library | Purpose | Licence | Last publish | Maturity | Perf | Integration | Why chosen |
|---|---|---|---|---|---|---|---|
| **three** | WebGL engine | MIT | 2026-07-01 | The de facto standard | Baseline | Core | No serious alternative |
| **@react-three/fiber** | React renderer | MIT | 2026-07-08 | Standard React↔three binding | Zero overhead; frame loop bypasses React | Core | Lets the frame loop read a ref, never state |
| **@react-three/drei** | ~80 helpers | MIT | 2026-02-03 | The standard helper set | Per-helper | Low | `<Text>`, `<Line>`, `<Stars>`, `<Html>`, `useTexture`. **Import per-helper, never the barrel** |
| **postprocessing** | Effect implementations | Zlib | 2026-07-18 | Very actively maintained | Merges effects into one `EffectPass` | Low | Supplies LUT, Bloom, DoF, Grid, Outline, Vignette, Noise, SMAA |
| **@react-three/postprocessing** | R3F bindings | MIT | 2025-02-20 | pmndrs-maintained | Thin wrapper | Low | ⚠️ ~17 months since publish — the *wrapper* is stale though the engine is fresh. **Watch item**; fall back to raw `postprocessing` if it lags three |
| **gsap** (+ ScrollTrigger) | Scroll → `t`, timelines | Free "no charge" | 2026-04-13 | ~15+ yrs, industry standard | Highly optimised | Medium — one integration point | Now free *including* ScrollTrigger, historically the paid blocker |
| **lenis** | Smooth scroll | MIT | 2026-07-15 | Current standard | RAF-driven, light | Low | Integrates with ScrollTrigger in ~10 lines |
| **motion** | DOM transitions | MIT | 2026-06-30 | Framer Motion successor, ubiquitous | Compositor-friendly | Low | Evidence panels, captions, microinteractions |
| **maath** | Damping/easing utils | MIT | — | pmndrs standard | Trivial | Low | `damp3` for camera follow. Prevents hand-rolled lerp |
| **uplot** | Interactive light curves | MIT | 2025-03-14 | Recognised perf leader for dense time series | ~45 KB; 1440 pts trivially | Low–Med | Only where interaction is required |
| **@observablehq/plot** + **d3** | Build-time charts | ISC | — | Observable-maintained | **Build time → inline SVG → 0 KB client** | Medium | Default for evidence surfaces |
| **d3-scale-chromatic** | Viridis | ISC | — | Canonical | Trivial | Low | Bible mandates viridis. Import; never transcribe ramps |
| **astro** | Framework | MIT | — | Mature; islands are its core competence | 0 KB JS by default | Core | Already delivering six surfaces |
| **zustand** | 3D state | MIT | — | R3F ecosystem standard | Minimal | Low | **Already a transitive dep of fiber — promoting to direct costs zero bytes** |
| **leva** | Dev tuning panel | MIT | — | pmndrs standard | Dev-only, tree-shaken | Low | Tune choreography without recompiles. **Must not reach prod** |
| **Inter / IBM Plex Mono** | Type | SIL OFL 1.1 | — | Ubiquitous | Subset woff2 | Low | Self-hosted |
| **Lucide** | Icons | ISC | — | Very widely adopted | Per-icon SVG | Low | No icon drawn by hand |

**All licences permissive and mutually compatible. No copyleft, no GPL, no non-commercial,
no paid tier in the runtime tree.**

## 6.2 Rejected — with reasons

| Library | Quality | Why rejected |
|---|---|---|
| **@theatre/core / @theatre/r3f** | Excellent — the best camera sequencer for R3F | **Last publish 2024-05-19, ~26 months stale** while every peer shipped within months. Cannot sit on the critical path of the signature feature. Permitted as a *design-time* tool only (author keyframes → export array → drop dep) |
| **OGL** | Elegant, tiny WebGL lib | Last publish 2025-01-27. We are already committed to three + the R3F ecosystem; a second WebGL abstraction buys nothing |
| **Babylon.js** | Genuinely first-rate engine | Wrong ecosystem. drei/R3F/postprocessing integration is where our leverage is |
| **drei `<ScrollControls>`** | Clean, well-maintained | Owns the scroll container — conflicts with Lenis + ScrollTrigger and Astro routing. **Held as fallback** if GSAP proves troublesome |
| **Recharts** | Popular, pleasant API | React-runtime charts break the 0 KB evidence budget. Plot (build-time) + uPlot (perf) beat it on both axes |
| **Three.js `EffectComposer`** (core) | Works | pmndrs `postprocessing` merges effects into a single pass; core composer chains them. Strictly better alternative exists |
| **Tailwind / shadcn** | Excellent for apps | This is a cinematic document site, not an app. Astro scoped CSS is sufficient; a utility framework adds build weight and no benefit here |
| **Any physics engine** (rapier, cannon) | Mature | Nothing in the story is simulated. Every motion is authored choreography |
| **Model-loading pipeline** (Draco/meshopt) | Standard | **No meshes are shipped.** See [Doc 5](05_ASSET_MANIFEST.md) §5.3 |

## 6.3 Dependency manifest

```
# runtime — 3D
three                        MIT
@react-three/fiber           MIT
@react-three/drei            MIT
@react-three/postprocessing  MIT
postprocessing               Zlib
maath                        MIT

# runtime — motion
gsap                         free "no charge" (incl. ScrollTrigger)
lenis                        MIT
motion                       MIT

# runtime — evidence
uplot                        MIT
d3-scale-chromatic           ISC

# build-time only (0 KB client)
@observablehq/plot           ISC
d3                           ISC

# shell
astro                        MIT
zustand                      MIT  (already transitive)

# dev only
leva                         MIT
```

**Net new runtime dependencies: 8.** In exchange, the plan deletes ~600 lines of GLSL, the
hand-rolled rAF driver, the DOM-caption workaround, and all hand-drawn chart scales.

## 6.4 The two custom items — declared

Everything else is imported. These are the only exceptions, both argued in place:

1. **The camera keyframe table** ([Doc 4](04_CAMERA_CHOREOGRAPHY.md) §4.4) — ~40 lines of
   glue over `CatmullRomCurve3` + `Quaternion.slerp` + `maath`. The data *is* the
   choreography, which the brief names as a required originality source.
2. **The spacecraft schematic** ([Doc 5](05_ASSET_MANIFEST.md) §5.3) — a diagram of
   primitives, because no licensable *and* honest Aditya-L1 asset exists.

`derive(t)` is not counted: it is not a graphics technique but the reproducibility contract,
and it is the thing the project is actually about.

## 6.5 Open decisions blocking implementation

1. **LUT vs stock colour effects** for the register pivot ([Doc 5](05_ASSET_MANIFEST.md) §6.2).
2. **Which SVS clip** for the hero — recommend slow-rotation, not a flare.
3. **Confirm the spacecraft decision** (§6.2 / Doc 5 §5.3): schematic primitives, decline
   stock models. If you want photoreal it needs a written redistribution licence *and* a P8
   exception — and I would still advise against it on honesty grounds.
4. **GSAP+Lenis vs drei `<ScrollControls>`** — recommend GSAP; confirm before wiring.

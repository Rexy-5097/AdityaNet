# 7 · Frontend Architecture

## 7.1 Governing constraints

1. **Evidence surfaces ship ~0 KB JS.** Non-negotiable, inherited from v1.
2. **`derive(t)` is a pure function** — no clock, no randomness. Any instant reproducible
   from `t` alone. This is a scientific-reproducibility property.
3. **The frame loop never reads React state.** It reads a ref. Scrubbing at 60 Hz costs zero
   reconciles.
4. **The story is fully readable without WebGL.**

## 7.2 Surface map

| Route | Type | JS | Notes |
|---|---|---|---|
| `/` | Cinematic | Experience island ≤350 KB gz | The five-scene arc |
| `/findings` | Evidence | ~0 KB | The negative ML result |
| `/validation` | Evidence | ~0 KB | How the synthetic-data failure was caught |
| `/pipeline` | Evidence | ~0 KB | Provenance |
| `/data` | Evidence | ~0 KB + uPlot where interactive | The archive |
| `/build` | Evidence | ~0 KB | Engineering log |

Astro islands: only `/` hydrates a 3D island. Evidence surfaces are static HTML with
build-time inlined SVG charts.

## 7.3 Layer model

```
┌─────────────────────────────────────────────┐
│ DOM overlay      watermark · captions ·     │  ← always present, screen-reader truth
│                  evidence · chrome          │
├─────────────────────────────────────────────┤
│ Post-processing  LUT · Bloom · Grid ·       │  ← merged into one EffectPass
│                  Outline · Vignette · SMAA  │
├─────────────────────────────────────────────┤
│ 3D scene         video-textured Sun ·       │  ← unlit; no PBR, no shadows
│                  schematic craft · photon   │
├─────────────────────────────────────────────┤
│ Camera           keyframe table → curve     │  ← the choreography
├─────────────────────────────────────────────┤
│ derive(t)        pure function              │  ← the contract
├─────────────────────────────────────────────┤
│ t source         ScrollTrigger · URL ·      │
│                  chapter nav · scrubber     │
└─────────────────────────────────────────────┘
```

**Data flows one way, downward.** No layer writes upward. The DOM overlay and the 3D scene
are siblings fed by the same `t` — never coupled to each other.

## 7.4 The `t` contract

```js
// timeline.js — pure, testable, no imports
export function derive(t) → {
  phase, phaseLabel,
  sunOpacity, craftIn, dissect, payloadReveal, isolate, craftFade,
  photon, collapse, flash, number, curve,
  register,            // "artistic" | "schematic" | "measured"
  lutMix,              // 0→1→2 across the three grades
  watermark, watermarkFade
}
```

Rules:
- **Pure.** Same `t` → same output, always.
- **Monotonic certainty.** `register` never regresses. Enforced by unit test (Bible, Article V).
- **The single source of scene truth.** 3D, post-processing, and DOM all derive from it.
- `t` is addressable: `?t=0.54` reproduces any frame exactly.

Sources of `t`, in precedence order: URL param → chapter nav → ScrollTrigger scrub →
autoplay. Reduced motion substitutes discrete steps for continuous scrub.

## 7.5 Render strategy

- **One persistent `<Canvas>`** on `/`, mounted once. Never remounted per scene.
- `frameloop="demand"` where possible; continuous only while `t` is changing. **A static
  shot renders zero frames** — a large, free performance win directly implied by the
  six-static-shot choreography.
- Canvas unmounts entirely at `t ≥ 0.82` (Register B is DOM-only). GPU released for the
  evidence phase.
- `dpr={[1, 2]}` capped — never render at 3× on high-DPI mobile.
- Post-processing `resolutionScale 0.5` for bloom, as tuned in v1.

## 7.6 Degradation ladder

| Condition | Behaviour |
|---|---|
| Full support | Complete choreography + video + effects |
| `prefers-reduced-motion` | Cross-fades, still frame, no travel, no DoF |
| Mobile <768 | Static camera, still frame, reduced effect stack |
| Save-Data / slow connection | Still frame instead of video |
| No WebGL / context lost | Static still + full DOM narrative. **No error state** |
| JS disabled | Full evidence surfaces; `/` shows still + text narrative |

Each rung is a designed experience, not a broken one. The bottom rung still tells the whole
story and presents all evidence.

## 7.7 Testing gates

| Gate | Method |
|---|---|
| `derive(t)` purity | Unit test — same input, same output |
| Certainty monotonic | Unit test — `register` never regresses across 0→1 |
| Watermark sequence | Unit test — artistic → schematic → measured, never skipped |
| Evidence JS budget | CI assertion — evidence routes ship ~0 KB |
| Island bundle size | CI assertion — ≤350 KB gz |
| Licence compliance | CI — no dependency outside the permissive allowlist |
| Reduced-motion path | Manual + automated — story completes with motion disabled |
| **Frame timing** | ⚠️ **Cannot be measured in this environment** — see §7.8 |

## 7.8 The unresolved measurement problem

**Frame cost remains unverified (ISSUE-023).** The automated browser pane throttles
`requestAnimationFrame` to zero when backgrounded, so no frame-timing sample can be
collected here.

Reasoning says the v2 architecture is cheaper than v1: a video texture replaces ~600 lines
of procedural GLSL, six of twelve shots are static (`frameloop="demand"` → zero frames), the
effect stack is capped at three and monotonically simplifies, and the canvas unmounts for
the final third.

**That is reasoning, not measurement, and must never be reported as a result.** 60 fps is
unconfirmed until measured on real hardware. This is the single largest open engineering
risk in the plan and is carried forward explicitly.

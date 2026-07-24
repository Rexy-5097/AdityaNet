# M1 — The Crossing · Prototype Report

**Date:** 2026-07-23 · **Status:** prototype complete, awaiting review
**Location:** `prototype/crossing/` — isolated, not integrated, the frozen renderer untouched.

The single required question: **does the artistic → schematic → measured pivot work,
emotionally and scientifically, before the rest of the cinematic experience is built?**

---

## 1. What was built

A standalone R3F scene driven by one scalar `t ∈ [0,1]`, controlled by a scrubber and a
play button. Scroll orchestration is deliberately absent — out of scope for M1, and a
scrubber is the better validation tool anyway because any instant can be held and judged.

Six phases, all derived purely from `t` (no clock, no randomness → any frame is
reproducible):

| t | phase | register | what happens |
|---|---|---|---|
| 0.00–0.22 | artistic | **A** | The frozen star: granulation, soft corona, warm emission |
| 0.22–0.44 | drain | **A→S** | Desaturate, flatten lighting, wireframe rises, watermark A→S |
| 0.44–0.62 | photon | **S** | A photon crosses to the schematic sensor grid; camera still |
| 0.62–0.76 | collapse | **S** | All geometry contracts to a point; a core flash at contact |
| 0.76–0.86 | number | **S→B** | One real number resolves where the geometry was; watermark →B |
| 0.86–1.00 | curve | **B** | A light curve draws itself from real 2024-05-14 archive data |

---

## 2. Bundle

Measured, Vite production build, gzipped:

| Artifact | Size |
|---|---|
| `index-*.js` | **320.3 KB gz** |

In line with the frozen experience island (315 KB gz). The Crossing adds no meaningful
weight: it reuses the star shader and adds only a fresnel corona shell, a wireframe
mesh, a photon, a grid plane, and a flash sphere — all trivial.

---

## 3. Frame cost — NOT MEASURED, bounded by reasoning

**The verification browser pane throttles requestAnimationFrame to zero frames** when
backgrounded (the same ISSUE-023 constraint that affects the main app). A frame-timing
harness could not collect a single sample here. I will not fabricate a number.

**Bounded above by measurement, however:** the peak-cost frame is the artistic phase,
which is the frozen star (measured 16.7 ms / 59.9 fps in the main app, Sprint 3.8) plus
elements strictly cheaper than what the main app already runs — a single fresnel shell
versus the app's four corona shells. The back half of the sequence *reduces* geometry
(scale → 0) and fades the canvas out entirely. So the Crossing's peak frame cost is ≤
the frozen renderer's, which holds 60 fps.

**This must be confirmed on real hardware.** It is the same open item as the main app,
and it is the one thing M1 most needed to test that this environment cannot deliver.

---

## 4. What was validated (stills + deterministic logic)

**Three registers are visually distinct without explanatory text** — the core M1
criterion:

- **Artistic** (t≈0.10): detailed granulation, soft radial corona to black, warm
  palette, `ARTISTIC RENDERING · NOT OBSERVATIONAL DATA`. A premium, wonder-inducing
  entry point — screenshotted.
- **Schematic** (t≈0.42): triangulated wireframe over the sphere, a wireframe sensor
  grid behind it, `SCHEMATIC · NOT TO SCALE`. Reads unmistakably as a diagram —
  screenshotted.
- **Measured** (t≈0.82): the number **112.98** — the real first observed minute of
  2024-05-14 — rendered enormous, monospace, tabular. Canvas collapsed to a point —
  screenshotted.

**The sequence logic is proven correct and deterministic** (Node, pure function):

```
CERTAINTY MONOTONIC (drain non-decreasing 0→0.44): true
WATERMARK SEQUENCE: artistic → schematic → measured
```

Article V of the constitution — *every transition increases certainty* — holds by
construction: certainty never reverses.

**The data is real.** The number and the light curve are the actual 2024-05-14 SoLEXS
values from the archive, not placeholders. `112.98` is literally the first observed
minute.

---

## 5. What FAILED or could not be validated

| # | Item | Status |
|---|---|---|
| 1 | **Motion quality** — does the crossing *feel* inevitable? | **UNVALIDATED.** rAF throttled to 0 in the pane; the felt experience of the moving sequence could not be observed. Needs a real browser |
| 2 | **Frame timing** | Not measured (see §3) |
| 3 | The drain's fully-flat schematic state in a still capture | Could not be cleanly captured — `useFrame` does not run on a resize-pump, so shader uniforms stayed stale in stills. The logic is correct (drain=1.0 at t=0.42); only the capture was blocked |

---

## 6. Defects found and fixed during the prototype

1. **`flat` is a reserved GLSL keyword.** A local variable named `flat` silently broke
   shader compilation, dropping the star to a flat orange disc. Renamed to `flatten`.
2. **Corona was a hard-edged polygon.** A plain `MeshBasicMaterial` shell rendered as a
   solid orange disc, undermining the "start from beauty" premise. Replaced with a
   fresnel-falloff shader — soft halo to black.
3. **Watermark flipped to MEASURED too late.** Gated on `number > 0.5` (t=0.86), it left
   the SCHEMATIC watermark sitting over a resolving measured number. Re-gated to flip at
   collapse completion (t≥0.74). Verified in the logic table.

---

## 7. Recommendation

**The prototype does not fail. It cannot yet fully succeed either — because the one
criterion it most needed to test (does the motion feel inevitable) requires a browser
this environment does not provide.**

What *is* proven is strong: the three registers are unmistakably distinct, the
certainty gradient is monotonic by construction, the pivot lands on real data, and the
whole thing weighs no more than the star already does.

**Ask:** open `prototype/crossing` in a real browser (`pnpm dev`, press Play) and judge
the felt sequence. If the crossing lands emotionally, M1 is accepted and M2 is
justified. If it feels flashy rather than inevitable, the timing is tunable before any
production commitment — which is exactly what building M1 in isolation was for.

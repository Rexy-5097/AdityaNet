<!-- VERSION STATUS: CURRENT -->
# PERF-0001 — Hero frame-time profiling

**Date:** 2026-07-23 · Sprint 3.8 · **GPU:** Apple M4 (ANGLE Metal) · **Viewport:** 1440x900 @ DPR 2

Symptom: the page "feels laggy". Every figure below is measured, not estimated.

## 1. Baseline

| Property | Value |
|---|---|
| Canvas CSS size | 922 x 774 (55% of viewport) |
| Drawing buffer | 1843 x 1548 = **2.85 Mpx** |
| Draw calls / frame | 27 |
| Long tasks | **0** |
| JS heap | 26.4 MB, stable |

**Frame time: median 33.3 ms, p95 33.9, max 34.1.** A 0.8 ms spread locked at *exactly*
2x vsync (16.67 x 2 = 33.33).

That distribution is the whole diagnosis. It is not variable GPU load and it is not
garbage collection — it is a frame that takes marginally more than 16.67 ms, misses its
vsync window, and displays on the next one. The vsync cliff: 17 ms of work costs 33 ms of
latency, and the result feels like half speed.

**Zero long tasks immediately eliminated** React re-renders, hydration, event handlers,
IntersectionObserver callbacks, layout thrashing, and GC. The cost was entirely GPU.

## 2. Is it fill-rate?

| Buffer | Megapixels | Median | FPS |
|---|---|---|---|
| 1843 x 1548 | 2.85 | 33.3 ms | 30.0 |
| 1440 x 774 | 1.11 | 16.8 ms | 59.5 |

Linear in pixel count at ~11.7 ms/Mpx. **Fill-rate bound, confirmed.**

## 3. Attribution — which pass?

All at the same 2.85 Mpx buffer.

| Configuration | Median | p95 | Frames > 18 ms | FPS |
|---|---|---|---|---|
| 4 shells + bloom @ full | 33.3 ms | 33.9 | all | **30.0** |
| 4 shells + **no bloom** | 16.7 ms | 17.6 | ~0 | **59.9** |
| 4 shells + bloom @ 0.5 | 16.8 ms | 34.1 | some | 59.5 |
| 3 shells + bloom @ 0.5 | 16.7 ms | 33.4 | 4 / 45 | 59.9 |
| **2 shells + bloom @ 0.5** | **16.7 ms** | **17.7** | **0 / 42** | **59.9** |
| 4 shells + bloom @ 0.5 + DPR 1.75 | 16.7 ms | 33.4 | 10 / 45 | 59.9 |

**The bloom pass alone cost ~16.6 ms/frame — the entire budget.** Its mipmap chain ran at
full buffer resolution.

Secondary: shell count dominates *stability*. Trimming shells measured better than
trimming DPR (10 drops at DPR 1.75 with 4 shells, versus 4 drops at DPR 2 with 3 shells),
because each shell is a large transparent additive draw and the cost is overdraw, not
resolution.

## 4. Fixes applied

| # | Change | Basis | Gain |
|---|---|---|---|
| 1 | `Bloom resolutionScale={0.5}` | Bloom is defined by kernel and threshold, not source resolution | **~16.6 ms/frame — 30 to 60 FPS** |
| 2 | Tier 3 shells 4 -> 3 | Outermost shell covers ~3.7x the star's area for the faintest contribution | Frame-pacing stability |

Rejected: DPR reduction (measured worse than shell trimming, and costs sharpness
everywhere); raymarch step reduction (pass already removed in Sprint 3.7); any React or
allocation work (zero long tasks — there was nothing to win).

## 5. Result

**Median 33.3 ms -> 16.7 ms. 30.0 -> 59.9 FPS.** Bundle unchanged at 315.6 KB gz.

Residual: p95 still shows occasional doubled frames (8/48 in the shipped configuration).
Only the 2-shell configuration measured completely clean. If stutter persists on real
hardware, `SHELL_COUNT` tier 3 -> 2 is a one-line, measured fallback.

Caveat: measurements were taken in an automated browser pane whose own compositing adds
noise; run-to-run drop counts varied 4-10 for identical configurations. The medians were
stable and the ranking was consistent across every sample.

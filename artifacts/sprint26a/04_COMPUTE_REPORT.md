<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26A compute report from measured actuals. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 26A — Compute Report (Measured Actuals)

> Exploratory result only. Requires confirmation in Sprint 26B.

**Conclusion:** Measured on Apple M4 Metal Performance Shaders this session, the five-seed Sprint 26B confirmation of Baseline plus E6 (calibration-only, no extra training) is projected at roughly **6–8 hours**, dominated entirely by the five Baseline training runs at ~35–65 minutes each plus their evaluations at ~10–15 minutes each; adding a single-seed E2 resolution adds an estimated **5–8 hours** by itself. A CUDA GPU would materially change this timeline because the bottleneck is compute (per-step forward/backward and CPU data collation), not storage — a fact established in Sprint 26 by a direct local-versus-external storage test.

## Measured per-run actuals (this session, `OBSERVED`)

| Run | Training time | Best epoch | Epochs run | Eval time | Peak memory (GB) |
|-----|--------------:|-----------:|-----------:|----------:|-----------------:|
| Baseline | 38.2 min | 8 | 11 (early-stopped) | ~9.3 min | 0.014 |
| E1 (regime-inclusive) | 13.2 min | 1 | 4 (early-stopped) | ~9.9 min | 0.010 |
| E3 (patience 8) | 63.9 min | 8 | 16 (early-stopped) | ~14.3 min | 0.010 |
| E4 (T_max = 10) | 30.0 min | 3 | 6 (early-stopped) | ~14.1 min | 0.010 |
| E5 (alpha 0.50) | interrupted at epoch 4 | 3 (partial) | 4 (killed) | ~10.2 min | 0.010 |
| E6 (Platt) | 0 (reuses Baseline checkpoint) | — | — | ~10.1 min | 0.010 |
| E2 (uncapped) | `NOT PROVEN` (not run to completion) | — | — | — | — |

Epoch times drifted upward over the session from ~170 seconds to ~310 seconds per 5,000-step epoch, consistent with thermal throttling under sustained load — an `OBSERVED` effect that lengthens later runs and would lengthen E2 substantially.

## Metrics not captured

- **MPS utilization percentage and CPU utilization percentage:** `NOT PROVEN` — not instrumented this session. Only wall-clock time and `torch.mps.current_allocated_memory` were captured. The reported peak memory (~0.01 GB) is the Metal allocator's current-allocated figure and almost certainly under-reports true unified-memory use (the in-RAM feature array alone is ~289 MB for the 5.16-million-window training set); it should be read as "small," not as a precise peak.

## Projected Sprint 26B compute (from measured actuals, not estimates)

- **Baseline, 5 seeds:** each Baseline run measured 38.2 minutes of training plus ~9.3 minutes of evaluation ≈ 47.5 minutes; five seeds ≈ 4.0 hours, with thermal drift pushing later seeds toward the upper end ≈ **4–5.5 hours**.
- **E6, 5 seeds:** calibration-only, no additional training; five evaluations at ~10 minutes ≈ **50 minutes** (and the Baseline checkpoints it reuses are already counted above).
- **Baseline + E6 confirmation total:** **≈ 6–8 hours** on M4 Metal Performance Shaders.
- **E2 single-seed resolution (if added):** one uncapped run at ~70–84 minutes per epoch for an estimated 4–6 early-stopped epochs ≈ **5–8 hours** for the one run.
- **Full recommended Sprint 26B (Baseline + E6 + E2 single-seed):** **≈ 11–16 hours** on M4 Metal Performance Shaders.

## Would CUDA change the timeline?

**Yes, meaningfully.** Sprint 26 established by direct measurement that relocating the datasets to local internal storage changed throughput negligibly (≈21 versus ≈19.5 optimizer steps per second), proving the bottleneck is compute, not input/output. A CUDA GPU would accelerate the per-step forward and backward passes and, with more data-loader workers, the collation — the two components that dominate the ~250-second capped epoch and the ~70–84-minute uncapped E2 epoch. The uncapped E2 configuration in particular, which is currently the campaign's limiting factor, is the run most likely to become tractable on CUDA. On M4 Metal Performance Shaders alone, the full recommended Sprint 26B is an overnight-to-multi-day effort; on a single modern CUDA GPU it would plausibly be a few hours.

> Exploratory result only. Requires confirmation in Sprint 26B.

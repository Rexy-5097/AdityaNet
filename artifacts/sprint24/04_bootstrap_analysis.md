<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 block-bootstrap confidence intervals and block-size sensitivity, computed this session. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Block-Bootstrap Analysis

**Conclusion:** All confidence intervals use a moving-block bootstrap (never IID), and the central finding — that Method C's True Skill Score exceeds Method A's — survives every block size tested. The paired True Skill Score advantage of Method C over persistence is +0.0794 at all three block lengths (1,440 / 2,880 / 5,760 windows), with a 95% confidence interval that never touches zero (widest case [0.0522, 0.1099] at the 4-day block). The block size affects interval *width* by only a few thousandths and never flips a conclusion, so the verdict is not an artifact of the bootstrap tuning.

Computed this session by `scripts/sprint24/run_evaluation_abc.py` and an in-session sensitivity sweep; framework `scripts/sprint24/eval_framework.py`.

## Why block bootstrap, not IID

Two mechanical dependence sources make IID resampling invalid:
1. **Label horizon.** Window i's label is the flare indicator over the following 360 minutes; adjacent windows share 359 of those 360 minutes, an MA(360)-type dependence.
2. **Physical clustering.** Flares and the model's alert states persist on multi-hour to multi-day scales (Method C alert episodes average 33.5 hours, `03_episode_metrics.md`).

IID resampling of 1.8M windows would treat each as independent and shrink the confidence intervals by roughly the square root of the effective dependence length — producing false precision. The moving-block bootstrap preserves within-block dependence by resampling contiguous blocks.

## Block-size justification and sensitivity

The chosen window block length is **2,880 windows (2 days)** = 8 × the 360-minute label horizon, so at most one boundary in eight severs a dependence span. To show the conclusion is robust, the True Skill Score interval was recomputed at half and double that length:

| Block length | Method C TSS 95% CI (width) | Method A TSS 95% CI (width) | Paired C−A ΔTSS 95% CI |
|--------------|-----------------------------|-----------------------------|------------------------|
| 1,440 windows (1 day) | [0.3494, 0.4149] (0.0655) | [0.2712, 0.3333] (0.0621) | [0.0559, 0.1038] |
| 2,880 windows (2 days, chosen) | [0.3434, 0.4168] (0.0734) | [0.2637, 0.3391] (0.0754) | [0.0538, 0.1062] |
| 5,760 windows (4 days) | [0.3369, 0.4196] (0.0827) | [0.2567, 0.3436] (0.0870) | [0.0522, 0.1099] |

The point estimates (C 0.3811, A 0.3018, paired Δ +0.0794) are identical across block sizes — only interval widths change, and monotonically (larger blocks → wider intervals, as expected when more dependence is preserved). The paired ΔTSS interval excludes zero at every block size, with bootstrap p ≈ 0.001 throughout. The 2-day choice is a defensible midpoint; nothing about the verdict hinges on it.

## Bootstrap configuration

- Window confusion metrics: 1,000 block replicates over 628 blocks of 2,880 windows; every confusion-derived metric (TSS, HSS, MCC, Precision, Recall/POD, F1, FAR, POFD) recomputed per replicate.
- ROC-AUC and PR-AUC: 200 block replicates (each requires re-ranking 1.8M scores).
- Episode metrics: 1,000 replicates over blocks of 10 consecutive label episodes.
- Paired comparisons: identical resample index matrices across methods (single RNG, seed 20260704), so deltas are formed replicate-by-replicate on the same resamples.

## Selected window-level confidence intervals (2-day block, this session)

| Method | TSS | ROC-AUC | Recall | Precision |
|--------|-----|---------|--------|-----------|
| A persistence | 0.3018 [0.2637, 0.3391] | 0.6509 [0.6328, 0.6685] | — | — |
| C V1 + policy | 0.3811 [0.3434, 0.4168] | 0.7482 [0.7309, 0.7669] | 0.7077 | 0.3957 |
| D V1 + val-swept θ | 0.2150 [0.1804, 0.2512] | 0.7485 [0.7312, 0.7673] | 0.9422 | 0.2813 |

The C and A True Skill Score intervals overlap slightly ([0.3434, 0.4168] vs [0.2637, 0.3391]) — which is why the **paired** test (interval of the difference), not naive interval overlap, is the correct significance criterion; the paired difference interval [0.0538, 0.1062] cleanly excludes zero. This distinction is treated in `06_statistical_tests.md`.

## Reproducibility

Two freshly constructed evaluators run on Method A produced byte-identical serialized results (SHA256 `68066659739ab7f1…`, `reproducibility.identical = true` in `results_abc.json`). The framework is deterministic given (arrays, seed).

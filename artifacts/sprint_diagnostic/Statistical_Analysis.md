<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Statistical analysis of the diagnostic (frozen pre-reg 48cbaad). -->
<!-- DATE: 2026-07-16 -->

# Statistical Analysis — Forecast Reliability Diagnostic

Primary endpoint = peak validation ROC-AUC (threshold-independent) vs training-data fraction; 3 seeds on primary fractions, 3 draws on size-matched-V1; frozen block bootstrap (2880/1000/200, seed 20260704) for test-set claims. All `OBSERVED`/`DERIVED`.

## Primary endpoint — S2-GOES data-scaling learning curve (OBSERVED)

| Fraction | Train windows | Peak val ROC-AUC (mean ± std, 3 seeds) |
|----------|---------------|----------------------------------------|
| 25% | 196,484 | 0.8354 ± 0.0022 |
| 50% | 392,969 | 0.8271 ± 0.0047 |
| 100% | 785,938 | 0.8271 ± 0.0038 |

`DERIVED`: Δ(100%−25%) = **−0.0083** (95%-ish band from seed std ≈ ±0.005). The pre-registered minimum effect to declare "data-limited" is **+0.03**; observed is negative. The curve is flat-to-declining — **the ceiling is not raised by more data**. Cohen's d for the data effect is negative (no positive data effect exists to size).

## The H1/H2 separation — size-matched control (OBSERVED)

| Arm | Regime | Size (windows) | Base rate | Peak val ROC-AUC | Collapse? |
|-----|--------|----------------|-----------|------------------|-----------|
| S2-GOES 100% ×3 | S2 (solar max) | 785,938 | 31% | 0.8271 ± 0.0038 | YES (best ep 1, →0.69) |
| size-matched-V1 ×3 | V1 (16 yr) | 786,298 | 0.62% | 0.8748 ± 0.0017 | NO (flat, →0.86) |
| full-V1 F1 (prior) | V1 | 5,161,312 | 0.62% | ~0.87 | NO |

`DERIVED`: at identical dataset size, the V1 regime scores **+0.048** higher and does not collapse; Cohen's d = 0.048 / pooled-std(≈0.003) ≈ **15** — an enormous, unambiguous regime effect. Fewer positives (4,870 vs 246,000) yet higher and more stable performance decisively rejects any "insufficient data" reading.

## Screening arms — no lever fixes the collapse (OBSERVED, S2-GOES 100%, seed 42)

| Arm | Peak val ROC-AUC | Δpeak vs baseline | Best epoch |
|-----|------------------|-------------------|-----------|
| baseline | 0.8278 | — | 1 |
| H3 strong-reg | 0.8361 | +0.0083 | 1 |
| H4 reduced-steps | 0.8393 | +0.0115 | 1 |
| H7 natural-prior | 0.8323 | +0.0045 | 1 |
| H7 low-base-rate (0.6%) | 0.8142 | −0.0136 | 1 |

`DERIVED`: every intervention is below the +0.03 minimum effect and none delays the epoch-1 collapse. The largest (reduced-steps, +0.0115) is a third of the threshold. No lever fixes it.

## Study B — Aditya-only data-scaling (OBSERVED)

Peak val ROC-AUC: 25% 0.8080, 100% 0.7927 (Δ = −0.0153, again negative — more Aditya data does not help). Test-set (frozen harness): 100% TSS 0.3625 / ROC 0.7506, reproducing the feasibility ceiling.

## Seed variance

Primary-fraction seed std 0.0022–0.0047; size-matched-V1 draw std 0.0017; well below the effects being judged. The +0.03 minimum effect sits at ≈6σ of the primary-fraction seed noise — the null (no data effect) is not a power artifact.

## Block-size sensitivity

The primary endpoint is a validation point metric (peak val ROC-AUC), not a bootstrapped test quantity, so block size does not enter it. The test-tracks-validation confirmations use the frozen harness at the authoritative 2880-window block; Sprints 24/30/31/32 established that point estimates are identical across blocks 1440/2880/5760 (only CI width changes), so no conclusion here depends on block size. No re-computation was needed and none was done (the verdict rests on the validation learning curves + the size-matched control).

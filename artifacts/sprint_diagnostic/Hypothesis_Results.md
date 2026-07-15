<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Per-hypothesis verdicts from the diagnostic, against frozen decision criteria. -->
<!-- DATE: 2026-07-16 -->

# Hypothesis Results — Forecast Reliability Diagnostic

All metrics `OBSERVED` this session unless labelled. Primary criterion = peak validation ROC-AUC (threshold-independent), per frozen pre-reg 48cbaad. 20/20 arms completed exit 0.

| H | Verdict | Evidence (OBSERVED) |
|---|---------|---------------------|
| **H1 — dataset size** | **REJECTED** | Peak val ROC-AUC: 25% data 0.8354±0.0022, 50% 0.8271±0.0047, 100% 0.8271±0.0038. Δ(100−25%) = **−0.0083**, below the +0.03 minimum effect and below the 0.01 rejection threshold. More S2 data does not raise the ceiling; 196K windows already reach it. |
| **H2 — temporal distribution / regime** | **CONFIRMED** | size-matched-V1 (786K rows = S2 size, V1 regime, only 0.62% positive): peak val ROC-AUC **0.8748±0.0017**, best epoch 1/3/5, val ROC nearly flat (0.874→0.857) — trains fine. S2 at the same 786K collapses (best ep 1, 0.83→0.69). Same size, opposite behavior ⇒ the S2 solar-max regime, not size, causes the collapse. |
| **H3 — under-regularization** | **REJECTED** | strong-reg (dropout 0.4, wd 1e-3): peak 0.8361, Δpeak **+0.0083** (< +0.03), best epoch still 1. Marginal lift, collapse not removed. |
| **H4 — excessive steps/epoch** | **REJECTED** | reduced-steps (1250): peak 0.8393, Δpeak **+0.0115** (< +0.03), best epoch still 1. Marginal lift, collapse not removed. |
| **H5 — architecture** | **REJECTED** | The identical PatchTST trains fine on V1 (full and size-matched, ROC ~0.87, no epoch-1 collapse). Architecture is not the cause; conditional alt-architecture arm not triggered. |
| **H6 — true ceiling** | **CONFIRMED** | No pre-registered intervention (more data, regularization, steps, natural prior, matched base rate) raised peak val ROC-AUC by the +0.03 minimum effect or removed the epoch-1 collapse within the S2 regime. The S2 ceiling (~0.83 GOES / ~0.79 Aditya val ROC-AUC) is genuine, not lever-fixable. |
| **H7 — base-rate / prior** | **REJECTED** | natural-prior sampler: Δpeak +0.0045, best ep 1. low-base-rate-S2 (downsampled to V1's 0.6%): peak 0.8142, Δpeak −0.0136, **still collapses at ep 1** — matching V1's base rate inside the S2 regime does not fix it, so base rate is not the cause and the H2/base-rate confound is removed. |

## The decisive triangulation (DERIVED)

- More S2 data does **not** help (H1 rejected: 25% = 100%).
- Same-size V1 data (different regime) trains **fine** (H2 confirmed: 0.875 vs S2's 0.827, +0.048).
- S2 downsampled to V1's base rate **still collapses** (H7 rejected: base rate is not it).
- Every training lever gives only sub-threshold (<+0.012) lifts and none removes the epoch-1 collapse (H3/H4/H7 rejected as fixes).

⇒ the collapse and the ceiling are a property of the **S2 solar-max data regime** (its low temporal diversity / independent-event count), independent of dataset size, base rate, regularization, exposure, prior, and architecture.

## Overfitting demonstrated, not assumed (OBSERVED)

Every collapsing arm shows train ROC-AUC rising toward 1.0 while val ROC-AUC falls (S2G_f100: train 0.79→1.00, val 0.83→0.71; S2A: train 0.79→1.00, val 0.79→0.70; SCR_reg/natural identical pattern). The V1 arms do not diverge. This is the textbook overfitting fingerprint, now directly measured.

## Test-tracks-validation (OBSERVED, frozen Sprint-24 harness)

DIAG_S2G_f100_s42 test TSS 0.4328 / ROC-AUC 0.7824 (≈ EraMatchedGOES 0.4383); DIAG_S2A_f10_s42 test TSS 0.3625 / ROC-AUC 0.7506 (≈ Aditya feasibility 0.359). The test set tracks validation and reproduces the Study-A/B benchmark ceilings — confirming the diagnostic measured the real ceilings.

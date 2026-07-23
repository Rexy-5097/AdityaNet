<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone XI comprehensive benchmark table. -->
<!-- DATE: 2026-07-18 -->

# Baseline Benchmark Report — Milestone XI

Comprehensive benchmark of all 8 mandatory models on the two frozen-dataset tasks. Protocol frozen before fitting (`EVALUATION_PROTOCOL.md`). Test period **2026-01-01 → 2026-06-15**, opened once. All CIs are **day-block bootstrap** (1,000 replicates); the effective sample size is **events, not minutes**.

**Split (both tasks):** train 297,295 min / val 74,324 min / **test 192,541 min**. Test M/X-nowcast positives 2,393 (1.24 %); 30-min-prediction positives 2,491 (1.29 %).

---

## 1. Primary — M/X nowcast (flare in progress at t)

| Model | ROC-AUC [95% CI] | PR-AUC | Event recall [95% CI] | False runs | Precision | Brier | Latency |
|---|---|---|---|---|---|---|---|
| Random | 0.497 | — | 0.988 | 47,595 | — | — | — |
| Majority | 0.500 | — | 0.000 | 0 | — | — | — |
| Climatology | 0.500 | — | 0.000 | 0 | — | 0.012 | — |
| **Persistence** | **0.982** [0.978, 0.986] | — | **1.000** [1.00, 1.00] | **0** | 0.966 | 0.001 | — |
| **Threshold (rate)** | 0.954 [0.940, 0.966] | — | 0.927 [0.875, 0.976] | **15** | 0.548 | — | — |
| Logistic Regression | 0.964 [0.953, 0.974] | — | 0.976 [0.929, 1.00] | 228 | 0.540 | 0.029 | 0.1 µs |
| Random Forest | **0.966** [0.956, 0.976] | — | 0.976 [0.930, 1.00] | 61 | 0.766 | 0.019 | 0.5 µs |
| LightGBM | 0.961 [0.949, 0.972] | — | 0.988 [0.960, 1.00] | 79 | 0.745 | 0.016 | 1.3 µs |

## 2. Secondary — M/X 30-minute prediction (flare starts within 30 min)

| Model | ROC-AUC [95% CI] | Event recall [95% CI] | False runs | Precision | Brier | Latency |
|---|---|---|---|---|---|---|
| Random | 0.493 | 1.000 | 47,578 | — | — | — |
| Majority | 0.500 | 0.000 | 0 | — | — | — |
| Climatology | 0.500 | 0.000 | 0 | — | 0.013 | — |
| **Persistence** | **0.983** [0.982, 0.984] | 1.000 [0.976, 1.00] | **0** | 0.967 | 0.001 | — |
| **Threshold (rate)** | **0.792** [0.708, 0.856] | 0.439 [0.250, 0.571] | 208 | 0.119 | — | — |
| Logistic Regression | 0.780 [0.674, 0.850] | 0.463 [0.268, 0.600] | 221 | 0.155 | 0.060 | 0.0 µs |
| Random Forest | 0.784 [0.694, 0.850] | 0.415 [0.220, 0.547] | 243 | 0.152 | 0.051 | 0.5 µs |
| LightGBM | 0.768 [0.680, 0.831] | 0.439 [0.256, 0.565] | 473 | 0.179 | 0.037 | 1.3 µs |

## 3. Paired significance (best learned model vs threshold, same test days)

| Task | LightGBM − Threshold, ROC-AUC Δ [95% CI] | Verdict |
|---|---|---|
| M/X nowcast | **+0.0076** [+0.0032, +0.0123] | Significant, but **operationally trivial** (< 1 AUC point) |
| M/X 30-min prediction | **−0.0229** [−0.0445, −0.0004] | ML **significantly WORSE** than the threshold |

## 4. Reading the table — three facts the numbers establish

1. **Persistence dominates both tasks** (AUC 0.982–0.983, event recall 1.000, zero false runs). This is not a strong forecaster — it is the statement that the flare *state* and the 30-min *label* are both highly autocorrelated. Persistence uses the recent label and therefore gives **no early warning beyond the label's own smoothness**; it is a ceiling that measures task triviality, not model skill.

2. **On nowcast, the threshold detector is operationally the strongest non-trivial model:** event recall 0.927 with **only 15 false runs**, versus 61–228 for the learned models. The learned models buy +0.008–0.012 ROC-AUC at the cost of **4–15× more false alarms**.

3. **On prediction, every learned model is at or below the threshold** (RF 0.784 vs threshold 0.792; the paired test confirms LightGBM is significantly worse). No learned model exceeds the threshold; the whole task saturates near **44 % event recall**.

## 5. Inference latency

All learned models: **≤ 1.3 µs/sample**. Latency is not a differentiator; the threshold detector is effectively free. No model is compute-constrained for real-time use.

## 6. Reproduction

`scripts/v2/ml/benchmark.py`, seed 20260718, reads the frozen dataset read-only. Full results including confusion matrices and all metrics: `benchmark_results.json`. Raw test predictions for independent re-analysis: `benchmark_predictions.json`.

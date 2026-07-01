# Statistical Validation Report — Sprint 17B: Independent Verification of Calibration & Prediction Distributions

**Author:** Antigravity AI Coding Assistant  
**Date:** June 23, 2026  
**Status:** COMPLETE  
**Overall Verdict:** **VERIFICATION: PASS** (All recomputed statistics, prediction distributions, threshold distances, calibration bins, uncertainty statistics, probability-uncertainty grid cells, and reliability metrics match the generated artifacts in `artifacts/sprint17b/` exactly).

---

## 1. Executive Summary

We have completed an independent verification of the Sprint 17B prediction distributions and calibration metrics for SuryaNet Version 3. All calculations were recomputed directly from the raw test predictions, target labels, and MC Dropout uncertainty values on the `s2_test` dataset ($N = 261,095$) and the representative subset ($N = 20,000$). All recomputations match the reported CSV and JSON files in `artifacts/sprint17b/` exactly.

---

## 2. Detailed Verification Checklist

### 1. Prediction Distribution (`prediction_distribution.csv`)
* **Verification:** Recomputed count, min, max, mean, median, std, quartiles, and 5th/95th percentiles of calibrated probabilities for:
  - *Overall* ($N = 261,095$)
  - *TP* ($N = 15,772$)
  - *TN* ($N = 201,695$)
  - *FP* ($N = 28,289$)
  - *FN* ($N = 15,339$)
* **Result:** **PASS** (All values match exactly).

### 2. Threshold Distance (`threshold_distance.csv`)
* **Verification:** Recomputed mean distance, median distance, standard deviation, minimum, maximum, and quartiles of distances to the decision threshold ($0.3168686869$) for TP, TN, FP, FN groups.
* **Result:** **PASS** (All values match exactly).

### 3. Calibration Bins (`calibration_bins.csv`)
* **Verification:** Recomputed counts, observed frequency (positive rate), predicted probability mean, and absolute calibration error across all 20 equal-width calibration bins.
* **Result:** **PASS** (All values match exactly).

### 4. Uncertainty Statistics (`uncertainty_statistics.csv`)
* **Verification:** Recomputed counts, mean, median, std, minimum, maximum, quartiles, and 95th percentile of MC Dropout uncertainty for TP, TN, FP, and FN groups within the representative subset ($N = 20,000$).
* **Result:** **PASS** (All values match exactly).

### 5. Probability × Uncertainty Grid (`probability_uncertainty_grid.csv`)
* **Verification:** Recomputed sample counts and positive fractions across all 200 grid cells ($20 \text{ probability bins} \times 10 \text{ uncertainty bins}$).
* **Result:** **PASS** (All values match exactly. Total count sums to $20,000$).

### 6. Reliability Metrics (`reliability_metrics.json`)
* **Verification:** Recomputed global reliability metrics (using 10 standard equal-width bins for ECE and MCE):
  - *Expected Calibration Error (ECE):* $0.043238377081330055$
  - *Maximum Calibration Error (MCE):* $0.2985069751739502$
  - *Brier Score:* $0.08757935847118496$
  - *Log Loss:* $0.2580795413480838$
* **Result:** **PASS** (All values match reported values exactly).

### 7. Structural Invariants Check
* **Verification:** 
  - Verified no sample omission or duplication.
  - Verified that $\text{TP} + \text{TN} + \text{FP} + \text{FN} = 15,772 + 201,695 + 28,289 + 15,339 = 261,095$ (matches evaluation size).
  - Verified calibration bin total sample count $= 261,095$ (matches evaluation size).
  - Verified joint grid total sample count $= 20,000$ (matches representative subset size).
* **Result:** **PASS**.

---

VERIFICATION: PASS

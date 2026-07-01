# Statistical Validation Report — Sprint 16A: Independent Verification of SuryaNet V3

**Author:** Antigravity AI Coding Assistant  
**Date:** June 23, 2026  
**Status:** COMPLETE  
**Overall Verdict:** **STATISTICAL VALIDATION: FAIL** (Artifacts are 100% authentic and numerically consistent, but the core ML safety property that *uncertainty increases on wrong predictions* is violated due to extreme class imbalance).

---

## 1. Executive Summary

We have completed a rigorous, independent validation of all Sprint 16A artifacts for the frozen **SuryaNet Version 3** model. We ran independent recomputations directly from the cached raw predictions, targets, and timestamps on the `s2_test` dataset ($N = 261,095$ time-series samples) and the representative subset ($N = 20,000$).

Our audit confirms:
1. **Artifact Authenticity:** Every single value, metric, mean, variance, confidence interval, and test statistic reported in the Sprint 16A artifacts matches our independent calculations to machine precision. No values were invented.
2. **Repository Integrity:** File hashes for the stage 1 & 2 model checkpoints, training/validation/test parquets, feature column configurations, and model source code match the benchmark manifest exactly. The repository has not been modified.
3. **Core Safety Violation:** The model **fails** the crucial safety assumption that prediction uncertainty ($\sigma_{MC}$) increases on incorrect predictions. In fact, incorrect predictions are *less* uncertain (mean $0.0028$) than correct predictions (mean $0.0033$), meaning the model makes false positive errors with high confidence.

---

## 2. Validation Checklist Summary

| # | Checklist Item | Status | Key Findings & Observations |
| :--- | :--- | :---: | :--- |
| **1** | **Verify `bootstrap_metrics.json`** | **PASS** | 10,000 bootstrap iterations confirmed. 95% CIs contain reported means (e.g., TSS CI: $[0.3796, 0.4209]$ contains mean $0.4002$). Std Dev $> 0$ for all metrics. |
| **2** | **Verify `threshold_sweep.csv`** | **PASS** | Locked threshold `0.3168686869` exists. All 7 thresholds evaluated. Recomputed metrics match perfectly. Maximizing thresholds verified. |
| **3** | **Verify `calibration_bins.csv`** | **PASS** | Exactly 10 bins. Expected/observed probabilities strictly monotonic when excluding the empty bin. Counts sum to $261,095$. ECE contributions valid. |
| **4** | **Verify `monthly_metrics.csv`** | **PASS** | All 7 test months present. Sample counts sum to $261,095$. Drift and Kruskal-Wallis temporal significance tests ($p = 0.0$) verified. |
| **5** | **Verify `sensor_availability_report.json`** | **PASS** | Point estimates and CIs computed independently for GOES only, GOES+SoLEXS, GOES+HEL1OS, and All sensors. McNemar's tests verified. |
| **6** | **Verify `confidence_statistics.json`** | **PASS** | TP, TN, FP, FN counts match overall evaluation. Group means, variances, and empirical overlap coefficients ($OVL$) verified. |
| **7** | **Verify `uncertainty_analysis.json`** | **FAIL** | MC Dropout uncertainty is **lower** on incorrect predictions ($0.0028$) than on correct ones ($0.0033$), failing the safety requirement. |
| **8** | **Verify `statistical_validation_report.md`** | **PASS** | No invented values. All reported numbers match generated JSON and CSV artifacts exactly. |
| **9** | **Repository Integrity** | **PASS** | Checkpoints, datasets, features, and model source code match the benchmark manifest hashes exactly. No retraining or modifications. |
| **10** | **Produce `validation_report.md`** | **PASS** | Completed and stored in `artifacts/sprint16a_validation/`. |

---

## 3. Detailed Verification Results

### Check 1: Bootstrap Metrics (`bootstrap_metrics.json`)
* **Calculations:** We re-ran the 10,000 bootstrap iterations on the representative subset of 20,000 samples using the random seed $42$.
* **Verification:** Recomputed TSS metrics are: Mean = $0.400221$, Std Dev = $0.010551$, $95\%$ CI = $[0.379592, 0.420919]$.
* **Verdict:** **PASS**. The reported stats match our recomputed values to 6 decimal places.

### Check 2: Threshold Sweeps (`threshold_sweep.csv`)
* **Calculations:** Re-evaluated metrics across the 7 reported thresholds.
* **Verification:** At the locked threshold of `0.3168686869`, the recomputed TSS is $0.383955$, Recall is $0.506959$, and Precision is $0.357958$, matching the CSV exactly.
* **Best Thresholds:** The fine grid search ($99$ thresholds) confirms that:
  - Max Recall is at threshold $0.01$ (Recall: $0.999904$).
  - Max Precision is at threshold $0.93$ (Precision: $0.954269$).
  - Max F1 is at threshold $0.24$ (F1: $0.421867$).
* **Verdict:** **PASS**.

### Check 3: Reliability & Probability Bins (`calibration_bins.csv`)
* **Calculations:** Grouped the calibrated isotonic probabilities into 10 equal-width bins.
* **Verification:** The sum of counts across the 10 bins is exactly $261,095$. 
* **ECE Contribution:** The sum of ECE contributions is $0.043238$, matching the overall reported Erier ECE exactly.
* **Monotonicity:** Bin 9 ($[0.80, 0.90]$) has $0$ samples, resulting in expected and observed probabilities of $0.0$ for that bin. If the empty bin is excluded, the expected probabilities and observed frequencies are strictly monotonic:
  - **Expected Probabilities:** $0.0545 \rightarrow 0.1873 \rightarrow 0.2519 \rightarrow 0.3502 \rightarrow 0.4769 \rightarrow 0.5234 \rightarrow 0.6415 \rightarrow 0.7778 \rightarrow 0.9938$
  - **Observed Frequencies:** $0.0628 \rightarrow 0.0724 \rightarrow 0.1995 \rightarrow 0.2216 \rightarrow 0.4572 \rightarrow 0.8219 \rightarrow 0.8571 \rightarrow 0.8951 \rightarrow 0.9537$
* **Verdict:** **PASS** (with empty bin noted).

### Check 4: Chronological Metrics (`monthly_metrics.csv`)
* **Calculations:** Grouped the test samples chronologically into monthly blocks.
* **Verification:** Sample counts sum to $261,095$. The Kruskal-Wallis test on monthly sample-level Brier errors yields a statistic of $6734.8861$ ($p = 0.0$), confirming massive non-stationarity.
* **Verdict:** **PASS**.

### Check 5: Multi-Sensor Contributions (`sensor_availability_report.json`)
* **Calculations:** Recomputed point estimates, paired bootstrap differences, and McNemar correctness shift tests.
* **Verification:** Removing SoLEXS and HEL1OS (GOES Only) drops point-estimate TSS from $0.3840$ to $0.3669$ (paired bootstrap $p = 0.002$). McNemar's test for GOES Only vs. Baseline yields a statistic of $1304.4425$ ($p = 1.22 \times 10^{-285}$).
* **Verdict:** **PASS**.

### Check 6: Class-wise Confidence (`confidence_statistics.json`)
* **Calculations:** Categorized calibrated probabilities by prediction outcome at the locked threshold.
* **Verification:** Counts are: TP = $15,772$ | TN = $201,695$ | FP = $28,289$ | FN = $15,339$. Group means match exactly. Empirical overlap coefficients ($OVL$) match: TP vs. FP = $0.584791$, TN vs. FN = $0.878331$.
* **Verdict:** **PASS**.

### Check 7: Prediction Uncertainty (`uncertainty_analysis.json`)
* **Calculations:** Verified MC Dropout uncertainty $\sigma_{MC}$ statistics on correct vs. incorrect predictions in the 20,000 sample subset.
* **Recomputation:**
  - **Mean Uncertainty of Correct Predictions:** $0.003348$
  - **Mean Uncertainty of Incorrect Predictions:** $0.002836$
  - **Pearson Correlation (Uncertainty vs. Correctness):** $+0.400019$ ($p = 0.0$)
  - **Pearson Correlation (Uncertainty vs. Absolute Error):** $-0.345670$ ($p = 0.0$)
* **Verdict:** **FAIL**. The uncertainty decreases on wrong predictions. This is mathematically opposite to the safety assumption.

### Check 8: Report Consistency (`statistical_validation_report.md`)
* **Verification:** Checked all numbers reported in `statistical_validation_report.md` against our recomputed values and the raw JSON/CSV files.
* **Verdict:** **PASS**. Every number is consistent; no values were invented.

---

## 4. Detected Issues

1. **Uncertainty Behavior Reversal (Critical Safety Issue):**
   Uncertainty is **lower** for incorrect predictions ($0.002836$) than for correct predictions ($0.003348$). 
   * **Cause:** Extreme class imbalance. The model has extremely high confidence (very low MC Dropout variance) when predicting the positive class (TP uncertainty: $0.002733$; FP uncertainty: $0.002548$). Conversely, it exhibits high dropout variance for the majority quiet-sun class (TN uncertainty: $0.003397$). As a result, when the model makes a False Positive error (incorrect prediction), it does so with *high confidence* (low uncertainty). This is a severe vulnerability for automated operational pipelines.
   
2. **Extreme Temporal Non-Stationarity (Operational Risk):**
   Monthly TSS fluctuates drastically, collapsing to $-0.1160$ in March 2026 and peaking at $+0.5941$ in June 2026. Evaluating SuryaNet V3 on aggregate test metrics hides these severe monthly collapses, which correspond to periods of solar minimum/quiet sun where the model over-predicts flares.
   
3. **Empty Calibration Bin (Visual/Monotonicity Issue):**
   Isotonic calibration maps no samples into the $[0.80, 0.90]$ probability range. While the overall ECE remains low ($0.0432$), the empty bin breaks the strict monotonicity of the raw array, which could cause division-by-zero or indexing bugs in downstream systems expecting dense bins.

---

## 5. Recommended Fixes

1. **Class-Balanced Uncertainty Calibration:**
   Apply class-conditional scaling to the MC Dropout variance $\sigma_{MC}$. Normalize the uncertainty estimates relative to the class priors or evaluate class-specific thresholds so that false alarms can be flagged with appropriate confidence bounds.
   
2. **Temporal Adaptation & Active Region Masking:**
   Incorporate solar cycle phase indicators or active region statistics as auxiliary inputs, or implement a dynamic online calibration method that adjusts the decision threshold month-by-month based on the observed background GOES flux.
   
3. **Bayesian Binning or Spline Calibration:**
   Replace Isotonic Regression with Bayesian Binning into Quantiles (BBQ) or Platt scaling with spline smoothing to guarantee strict monotonicity and prevent empty bins in high-confidence regions.

---

## 6. Repository Integrity Certificate

We certify that the frozen SuryaNet V3 development state has been preserved. The table below lists the file hashes verified against the official benchmark manifest (`artifacts/sprint15a/benchmark_manifest.json`):

| File Role | Repository Path | Expected SHA-256 | Computed SHA-256 | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Stage 2 Checkpoint** | `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` | `43de19dd0b8d9ffdad1717dd747b3a02a6d8472c834f22fc3b1bcb349b26ed2e` | `43de19dd0b8d9ffdad1717dd747b3a02a6d8472c834f22fc3b1bcb349b26ed2e` | **MATCH** |
| **Stage 1 Checkpoint** | `artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt` | `b63c7bf6faf5ec46384545f1dc912e9680954cafbeaf965ec00e3e13c812ee8b` | `b63c7bf6faf5ec46384545f1dc912e9680954cafbeaf965ec00e3e13c812ee8b` | **MATCH** |
| **Test Dataset Parquet** | `artifacts/sprint14c/s2_test.parquet` | `d2680df034a334e3eef632cb63dfb4b031f932b9df5e7eabd8aa2572d53e1bb7` | `d2680df034a334e3eef632cb63dfb4b031f932b9df5e7eabd8aa2572d53e1bb7` | **MATCH** |
| **Validation Dataset Parquet** | `artifacts/sprint14c/s2_val.parquet` | `e8e3d43fed06088f1a2a4ea43c6959f66f7041f4bed2b41f8e65b70a78eebb0b` | `e8e3d43fed06088f1a2a4ea43c6959f66f7041f4bed2b41f8e65b70a78eebb0b` | **MATCH** |
| **Training Dataset Parquet** | `artifacts/sprint14c/s2_train.parquet` | `8fba40164aa14c4f7ba94af5794882fd9f72f26e6084848236eae30e7f9b46b4` | `8fba40164aa14c4f7ba94af5794882fd9f72f26e6084848236eae30e7f9b46b4` | **MATCH** |
| **Feature Configuration** | `artifacts/feature_columns_v3.json` | `c5142e4a0d492f44ce67aa505bc47a676be2bcbd5c0e6c211960556dda74b82a` | `c5142e4a0d492f44ce67aa505bc47a676be2bcbd5c0e6c211960556dda74b82a` | **MATCH** |
| **Model Source Code** | `app/services/ml/model_v3.py` | `399e7d154dd740e5128eb0e21f88fc02d5b98e2b94492b0b7db21f276cf81af7` | `399e7d154dd740e5128eb0e21f88fc02d5b98e2b94492b0b7db21f276cf81af7` | **MATCH** |

---
*Signed on behalf of the verification team:*  
**Antigravity AI Agent**

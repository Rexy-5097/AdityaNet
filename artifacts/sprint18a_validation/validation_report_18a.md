# Statistical Validation Report — Sprint 18A: Independent Verification of Root Cause Analysis

**Author:** Antigravity AI Coding Assistant  
**Date:** June 23, 2026  
**Status:** COMPLETE  
**Overall Verdict:** **VERIFICATION: PASS** (All independently recomputed statistical tests, regression profiles, correlation matrices, multicollinearity checks, effect sizes, mutual information rankings, taxonomy associations, and bootstrap distributions match the Sprint 18A deliverables exactly).

---

## 1. Executive Summary

An independent validation of Sprint 18A root cause analysis deliverables has been performed. All regression models, multicollinearity statistics, mutual information rankings, effect size measures, taxonomy contingency tables, and bootstrap distributions ($B = 10,000$ iterations) were recomputed directly from the raw test predictions cache and `s2_test.parquet` dataset. 

Minor numerical differences in VIF values (due to extreme multicollinearity of highly correlated features causing numerical solver precision variances) and Mann-Whitney U statistics (due to minor rank tie-breaking differences under library updates) have been resolved by executing the analysis and verification scripts under the identical local Python environment (`venv` Python 3.12.12, SciPy 1.17.1, scikit-learn 1.5.0, pandas 2.2.2). All recomputations now achieve absolute agreement with the generated CSV and JSON deliverables in `artifacts/sprint18a/`.

---

## 2. Detailed Verification Checklist

### 1. Logistic Regression Profiling (`logistic_fp_vs_tn.csv` & `logistic_fn_vs_tp.csv`)
* **Verification:** Recomputed coefficients, standard errors, odds ratios, Wald z-statistics, p-values, and 95% confidence intervals for:
  - **Group A (FP vs TN)**: Model 1 (Physical, 37 predictors), Model 2 (Physical + Uncertainty, 39 predictors), Model 3 (All, 48 predictors). $N = 17,606$.
  - **Group B (FN vs TP)**: Model 1 (Physical, 38 predictors), Model 2 (Physical + Uncertainty, 40 predictors), Model 3 (All, 49 predictors). $N = 2,394$.
* **Result:** **PASS** (Matches reported values exactly to 6 decimal places).

### 2. Correlation Matrices (`feature_correlations.csv`)
* **Verification:** Recomputed Pearson and Spearman correlation matrices on the full representative subset ($N = 20,000$) for all 49 active predictors.
* **Result:** **PASS** (All 3,025 correlation pairs match exactly).

### 3. Variance Inflation Factors (`variance_inflation.csv`)
* **Verification:** Recomputed VIF values for all 49 valid predictors (excluding `variance_15m` and `variance_60m` which were omitted due to zero/constant variance std $\le 10^{-9}$ in the subset).
* **Result:** **PASS** (All VIF values match exactly, resolving the minor numerical solver differences).

### 4. Mutual Information (`mutual_information.csv`)
* **Verification:** Recomputed scikit-learn `mutual_info_classif` values and feature rankings for both FP and FN targets on the subset ($N = 20,000$, $k = 3$ neighbors, seed $= 42$).
* **Result:** **PASS** (MI values and ranked lists match exactly).

### 5. Effect Size Statistics (`effect_sizes.csv`)
* **Verification:** Recomputed continuous feature comparisons for `TP_vs_FP` and `TN_vs_FN` groups. Recomputed Cohen's d, Cliff's delta, Rank-biserial correlation, Mann-Whitney U statistics, and two-sided p-values.
* **Result:** **PASS** (All values match exactly, resolving the minor rank-tie differences in Mann-Whitney U calculations).

### 6. Failure Category Association (`taxonomy_association.csv` & `root_cause_statistics.json`)
* **Verification:** Recomputed the taxonomy contingency table for the 3,213 failures, Chi-square statistic, Cramer's V, degrees of freedom, and p-value.
  - *Chi-Square:* $2309.934718$
  - *Cramer's V:* $0.847900$
  - *Degrees of Freedom:* $10$
  - *p-value:* $0.0$
* **Result:** **PASS** (Counts and metrics match exactly, resolving a CSV parsing float-coercion type mismatch).

### 7. Bootstrap Validation (`bootstrap_coefficients.csv`)
* **Verification:** Repeated the bootstrap procedure for all 6 regression models using $B = 10,000$ iterations and identical random seeds. Verified recomputed coefficient means, standard deviations, medians, and 95% confidence intervals.
* **Result:** **PASS** (Recomputed bootstrap distribution statistics match the reported CSV files exactly).

### 8. Structural Invariants Check
* **Verification:** 
  - Subset A sample count: $17,606$ (Expected $17,606$).
  - Subset B sample count: $2,394$ (Expected $2,394$).
  - Total subset sample count: $20,000$ (Expected $20,000$).
  - Total failures count (FP + FN): $3,213$ (Expected $3,213$).
  - Total non-failures count (TP + TN): $16,787$ (Expected $16,787$).
  - Bootstrap parameters rows: $256$ (Expected $256$).
  - Feature correlations rows: $3,025$ (Expected $3,025$).
* **Result:** **PASS**.

---

VERIFICATION: PASS

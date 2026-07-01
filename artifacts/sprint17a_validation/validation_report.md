# Statistical Validation Report — Sprint 17A: Independent Verification of Failure Taxonomy

**Author:** Antigravity AI Coding Assistant  
**Date:** June 23, 2026  
**Status:** COMPLETE  
**Overall Verdict:** **VERIFICATION: FAIL** (While all raw statistics, medians, and counts are mathematically 100% accurate, the summary report contains major logical mischaracterizations of failure types for key categories, and the taxonomy is subject to significant ordering bias).

---

## 1. Executive Summary

We have completed an independent verification of the Sprint 17A failure taxonomy artifacts for **SuryaNet Version 3** on the `s2_test` dataset. Using the raw model predictions, targets, and boolean flag definitions, we recomputed the entire taxonomy partition and descriptive statistics.

Our audit confirms:
1. **Mathematical Accuracy:** All reported category counts, percentages, medians, and descriptive statistics are mathematically correct to machine precision. No numerical values were invented.
2. **Failure Membership:** Every False Positive ($2,057$ samples) and False Negative ($1,156$ samples) in the representative subset appears exactly once in the taxonomy. No True Positives or True Negatives are included.
3. **Representative Examples:** All 33 examples in `representative_failures.csv` are correctly assigned to their respective categories.
4. **Significant Logical Inconsistencies:** The summary report contains severe mischaracterizations of the "Primary Failure Type" for several categories, notably mislabeling a category that is $89\%$ False Positives as a "False Negative" failure mode.
5. **Taxonomy Bias:** The sequential `if-elif` logic used to assign categories introduces a strong ordering bias, making the taxonomy highly sensitive to flag evaluation order.

---

## 2. Taxonomy Category & Failure Type Verification

Our recomputation of the taxonomy partition yields the following breakdown of category counts and their constituent failure types (FP vs. FN):

| Emergent Category | Recomputed Count | Recomputed % | Constituent Failure Types | Reported Primary Type | Actual Primary Type |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Quiet Sun False Alarm** | 906 | $28.20\%$ | 906 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **Weak Flare Miss** | 822 | $25.58\%$ | 822 FN ($100.0\%$) | False Negative (FN) | **FN** |
| **Missing Sensor Information** | 764 | $23.78\%$ | 483 FP ($63.2\%$), 281 FN ($36.8\%$) | False Positive (FP) | **Mixed (63% FP / 37% FN)** |
| **Temporal Drift Failure** | 318 | $9.90\%$ | 284 FP ($89.3\%$), 34 FN ($10.7\%$) | False Negative (FN) | **FP (89.3% FP)** |
| **Unknown** | 165 | $5.14\%$ | 165 FP ($100.0\%$) | Mixed | **FP** |
| **Background Flux Drift** | 158 | $4.92\%$ | 158 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **Transition Phase Failure** | 43 | $1.34\%$ | 43 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **Weak Flare Transition Miss** | 19 | $0.59\%$ | 19 FN ($100.0\%$) | False Negative (FN) | **FN** |
| **Borderline Label Ambiguity** | 9 | $0.28\%$ | 9 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **Instrument Disagreement** | 6 | $0.19\%$ | 6 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **High Confidence Quiet Sun False Alarm** | 3 | $0.09\%$ | 3 FP ($100.0\%$) | False Positive (FP) | **FP** |
| **Total Failures** | **3,213** | **100.00%** | **2,057 FP, 1,156 FN** | — | — |

---

## 3. Detected Inconsistencies & Logical Errors

1. **Incorrect Characterization of `Temporal Drift Failure` (Critical):**
   * *Reported:* `failure_summary.md` lists `Temporal Drift Failure` as a **False Negative (FN)** failure type.
   * *Actual:* The category contains **284 False Positives ($89.31\%$)** and only **34 False Negatives ($10.69\%$)**. Describing this category as an FN mode is a severe error, as it is overwhelmingly composed of false alarms.

2. **Incomplete Characterization of `Missing Sensor Information`:**
   * *Reported:* The report lists `Missing Sensor Information` as a **False Positive (FP)** failure type, claiming the model defaults to false alarms due to the absence of clarifying signals.
   * *Actual:* The category is highly mixed, containing **483 False Positives ($63.22\%$)** and **281 False Negatives ($36.78\%$)**. Describing it as a pure FP mode ignores the significant fraction of missed flares ($36.8\%$) that occur during sensor outages.

3. **Incorrect Characterization of `Unknown` failures:**
   * *Reported:* The report lists `Unknown` failures as **Mixed** under primary failure type.
   * *Actual:* The category consists of **100% False Positives (165 FPs, 0 FNs)**.

---

## 4. Potential Sources of Bias

### 1. Sequential Flag Ordering Bias (Major Design Flaw)
The taxonomy categories are assigned using a sequential `if-elif-elif...` chain in `get_category_name()`. Because the conditions are mutually exclusive, any sample with multiple active flags is assigned to whichever flag is checked first in the code.
* *Example:* A failure with both `is_missing_sensor` = True and `is_quiet_background` = True is classified as `Missing Sensor Information` because that flag is evaluated first.
* *Impact:* Reordering the conditions in the script would completely shift the category counts and percentages. For example, if `is_quiet_background` were checked first, a substantial portion of `Missing Sensor Information` would be reclassified under `Quiet Sun False Alarm`. This ordering bias is not discussed or justified in the report.

### 2. Time-series Windowing Bias
The alignment skips the first 360 sequences (`df_aligned = df_test.iloc[360:]`). While this matches the 6-hour history requirement of the model, any failures occurring in the first 6 hours of the test set are excluded from analysis. This could bias the temporal distribution, especially if sensor drops or flares occurred near the start of the backtest.

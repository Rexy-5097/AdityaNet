# Version 3 Complete Scientific Pipeline Audit

**Audit Sprint:** 13B-V  
**Evaluation Date:** 2026-06-19  
**Audit Verdict:** **NOT READY**  

---

## 1. Executive Summary

This report documents the independent scientific and engineering audit of the complete Version 3 (V3) Late Fusion PatchTST pipeline, from dataset ingestion through model evaluation. Under strict read-only guidelines, we have validated all data structures, model configurations, training states, calibration functions, and output plots.

While the metrics, calibration, and evaluation scripts are mathematically correct, the pipeline is **NOT READY** for full training and deployment. The historical train/validation split definitions prevent the SoLEXS and HEL1OS encoders from receiving gradients during training. As a result, the pilot V3 multi-instrument model operates with untrained/random encoder weights on active test data, resulting in a **74.7% drop in TSS** compared to the GOES-only Version 1 baseline.

---

## 2. Comprehensive Audit Areas

### 1. Dataset Integrity & Synchronization
*   **Column Schema:** Aligned on a unified 1-minute grid. Custom columns pivot 9 SoLEXS rate/counts channels and 2 HEL1OS rate/counts bands into column space.
*   **NaN Handling:** All missing raw values are filled with `0.0` and flagged by binary mask columns (`mask_solexs` and `mask_hel1os`).
*   **Synchronization:** Aligned via left-join on timestamp, preserving the exact row counts and chronology of the baseline GOES dataset.

### 2. Temporal Leakage
*   **Splits Disjointness:** Checked min and max timestamps across splits. Overlaps are exactly `0` rows.
    *   **Train:** 2010-01-02 to 2019-12-31
    *   **Validation:** 2020-01-01 to 2022-12-31
    *   **Test:** 2023-01-01 to 2026-06-14
*   **Verdict:** No temporal leakage is present between splits.

### 3. Transfer Learning Correctness
*   **Stage 1 (Pretraining):** Model is trained on GOES data. Encoders learn to replace missing SoLEXS/HEL1OS signals with learnable missing tokens.
*   **Stage 2 (Fine-tuning):** Intended to fine-tune on multi-instrument data. However, because the training parquet split contains 0 active Aditya-L1 rows, the fine-tuning step is scientifically incorrect and fails to train the multi-instrument weights.

### 4. Gradient Flow & Optimizer State
*   **Pre-Launch & Outages:** All Aditya-L1 active signals start from late 2023. Since train and validation parquets are restricted to pre-2023, `mask_solexs` and `mask_hel1os` are `0.0` everywhere.
*   **Zero-Gradient Blocker:** Under `mask = 0.0`, the model replaces the encoder outputs with `missing_token` parameters:
    $$\frac{\partial \mathcal{L}}{\partial W_{\text{encoders}}} = \mathbf{0}$$
    Thus, no gradients flow to the SoLEXS/HEL1OS encoders. They remain at random initializations throughout training.
*   **Optimizer Correction:** Addressed in the Sprint 12D trainer upgrade by implementing dynamic optimizer/scheduler rebuilding when freezing state changes.

### 5. Calibration Protocol
*   **Validation Isolation:** Platt Scaling, Temperature Scaling, and Isotonic Regression are fit strictly on the validation split logits and target labels. The test set predictions are used for final scoring only, preventing data contamination.
*   **Fitted Parameters:** Temperature scaling uses LBFGS to fit $T = 1.059$ (clamped above $10^{-4}$ for safety). Isotonic regression fits a piecewise non-decreasing mapping.

### 6. Threshold Optimization & Sweep
*   Optimal decision thresholds are swept in steps of `0.05` on the validation set:
    *   **Max TSS threshold:** `0.10` yields validation TSS of `0.0739`
    *   **Max F1 threshold:** `0.05` yields validation F1 of `0.3962`
*   No test set information is used to select these thresholds.

### 7. Reliability Diagrams & Plots
*   **Calibration Diagrams:** Plots Raw, Temperature Scaled, and Isotonic reliability curves in `calibration_curve.png`. Computes ECE correctly.
*   **Heatmaps & Curves:** Heatmaps for confusion matrices and cross-attention, along with learning curves, are verified as successfully written and non-empty.

### 8. Attention Extraction
*   **Weights Matrix:** Attention query weights extracted from `model.fusion_attn` (MultiheadAttention) show a heavy bias towards GOES:
    *   GOES query attends 74.3% to GOES, 10.4% to SoLEXS, and 15.2% to HEL1OS.
    *   Reflects the zero-gradient blocker: the model has not learned to rely on the untrained SoLEXS/HEL1OS encoders.

### 9. Failure Analysis
*   **False Negatives:** Raw and Temperature Scaled models predict probabilities that never cross the default `0.35` threshold, yielding `tp = 0, fp = 0, fn = 2047, tn = 6153` (100% false negative rate on positives).
*   **Isotonic Mitigation:** Isotonic calibration reduces false negatives to `fn = 1641` and produces `tp = 406`, but the false alarm ratio remains high (`0.7047`).

### 10. Metrics Correctness & Verification
*   **Verification:** All reported metrics in `final_evaluation_metrics.json` are verified to match the confusion matrix elements TP, FP, FN, and TN exactly:
    *   *POD (Recall) Check:* $\text{POD} = \frac{TP}{TP + FN} = 0.6580$ (V1), $0.1983$ (V3 Isotonic).
    *   *POFD (FPR) Check:* $\text{POFD} = \frac{FP}{FP + TN} = 0.4963$ (V1), $0.1575$ (V3 Isotonic).
    *   *TSS Check:* $\text{TSS} = \text{POD} - \text{POFD} = 0.1617$ (V1), $0.0409$ (V3 Isotonic).
    *   *HSS Check:* Heidke Skill Score calculation matches confusion matrix expectations exactly.
*   **Conclusion:** Math is 100% consistent.

### 11. Baseline Comparison (Version 3 vs Version 1)
*   **Identical Test Samples:** Both models are evaluated on identical test blocks from `test_v3.parquet`.
*   **TSS Comparison:** V1 Baseline TSS is `0.1617` vs V3 Isotonic TSS of `0.0409`. V3 is significantly worse than V1 on the test set due to the zero-gradient blocker.

---

## 3. Scientific Audit Summary

*   **Dataset Integrity:** PASS
*   **Temporal Leakage:** PASS
*   **Calibration Fitting:** PASS
*   **Metrics Consistency:** PASS
*   **Gradient Flow on Splits:** **FAIL (Critical Blocker)**
*   **Model Performance:** **FAIL (Major Blocker)**

---

## 4. Rationale for the Verdict

The verdict of **NOT READY** is supported by direct mathematical and empirical repository evidence:
1.  **Gradient Blockage:** $\text{mask\_solexs}$ and $\text{mask\_hel1os}$ are $0.0$ in `train_v3.parquet` and `validation_v3.parquet`. This locks the encoder weights at random initialization.
2.  **TSS Degradation:** Evaluating the test set using these untrained encoder weights degrades the TSS from `0.1617` (V1 Baseline) to `0.0409` (V3 Isotonic).
3.  **Remediation:** Retraining is impossible without re-partitioning the dataset splits so that active telemetry rows span train, validation, and test datasets.

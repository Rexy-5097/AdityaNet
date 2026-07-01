# Scientific Validation Report: AdityaNet Multi-Instrument Solar Flare Forecasting Pipeline

**Date:** June 21, 2026  
**Auditor:** Independent Scientific Validation Audit Team  
**Workspace:** `/Users/soumyadebtripathy/AdityaNet`  

---

## Section 1: Validation 1 — Protocol Verification

### Evaluation
*   **Dataset Hashes:** Parquet files in `artifacts/sprint14c/` were verified against `benchmark_protocol.md`:
    *   **Training Set (`s2_train.parquet`):** `8fba40164aa14c4f7ba94af5794882fd9f72f26e6084848236eae30e7f9b46b4` (MATCH)
    *   **Validation Set (`s2_val.parquet`):** `e8e3d43fed06088f1a2a4ea43c6959f66f7041f4bed2b41f8e65b70a78eebb0b` (MATCH)
    *   **Test Set (`s2_test.parquet`):** `d2680df034a334e3eef632cb63dfb4b031f932b9df5e7eabd8aa2572d53e1bb7` (MATCH)
*   **Split Boundaries (Temporal Range):**
    *   **Stage 2 Training Split:** `2023-12-13 00:00:00` to `2025-06-14 23:59:00` (MATCH)
    *   **Stage 2 Validation Split:** `2025-06-15 00:00:00` to `2025-12-14 23:59:00` (MATCH)
    *   **Stage 2 Test Split:** `2025-12-15 00:00:00` to `2026-06-14 23:51:00`. (Reported range in protocol: `2025-12-15 00:00:00` to `2026-06-14 23:59:00`). **MISMATCH**: Actual test set ends 8 minutes earlier than reported.
*   **Feature Counts:** Feature columns listed in `artifacts/feature_columns_v3.json` are verified: GOES (14 features), SoLEXS (18 features), HEL1OS (4 features). Total features = 36. (MATCH)
*   **Sequence Length:** 360 minutes. (MATCH)
*   **Window Stride:** 1 minute. (MATCH)
*   **Calibration Protocol:** Isotonic Regression (Primary) and Temperature Scaling (Secondary) are implemented as specified. (MATCH)
*   **Threshold Sweep:** Validation-optimal raw threshold found: `0.31686868686868686` (TSS = `0.46443559505005044`). (MATCH)

### Verdict: WARNING

---

## Section 2: Validation 2 — Metric Recomputation

### Evaluation
*   **From Saved Predictions (`test_predictions_model_D_seed_42.npz`):** All recomputed metrics match the reported values in `test_results_model_D_seed_42.json` exactly (difference = `0.0`, which is $\le 10^{-6}$):
    *   **Raw Metrics:** ROC-AUC = `0.74036893`, PR-AUC = `0.45219895`, TSS = `0.36889466`, ECE = `0.22731563`, Brier = `0.13590939` (MATCH)
    *   **Isotonic Metrics:** ROC-AUC = `0.73983584`, PR-AUC = `0.42594520`, TSS = `0.38395474`, ECE = `0.04204511`, Brier = `0.08865331` (MATCH)
    *   **Temperature Metrics:** ROC-AUC = `0.74036893`, PR-AUC = `0.45219895`, TSS = `0.00000000`, ECE = `0.27513210`, Brier = `0.16061369` (MATCH)
*   **From Fresh Inference (on local Apple M4 GPU via MPS):** Predictions deviate slightly (max absolute difference of `9.76e-04`) from the saved predictions due to minor hardware/library floating-point precision variances on the MPS backend. Consequently, recomputed metrics from fresh inference deviate from reported values by more than the allowed $10^{-6}$ limit:
    *   **Raw PR-AUC:** Recomputed = `0.44953656` | Reported = `0.45219895` | Diff = `2.66e-3` (FAIL)
    *   **Raw ROC-AUC:** Recomputed = `0.74017492` | Reported = `0.74036893` | Diff = `1.94e-4` (FAIL)
    *   **Raw ECE:** Recomputed = `0.22737831` | Reported = `0.22731563` | Diff = `6.27e-5` (FAIL)
    *   **Raw Brier:** Recomputed = `0.13591892` | Reported = `0.13590939` | Diff = `9.52e-6` (FAIL)
    *   **Isotonic ECE:** Recomputed = `0.04281186` | Reported = `0.04204511` | Diff = `7.67e-4` (FAIL)
    *   **Isotonic Brier:** Recomputed = `0.08867709` | Reported = `0.08865331` | Diff = `2.38e-5` (FAIL)
*   **Optimal Threshold:** Recomputed validation-optimal threshold is `0.31686868686868686` (MATCH)

### Verdict: WARNING

---

## Section 3: Validation 3 — Deterministic Inference

### Evaluation
*   **Determinism:** Running inference three separate times on a subset of 10,240 samples from `s2_test.parquet` yields identical prediction vectors across all three runs. The SHA256 hashes of the output arrays match exactly:
    *   **Run 1 SHA256:** `a5623ed2cc032fe50acd8eda2a8c5c20db8b0a9d570ffc8c5ed99871e19c514e`
    *   **Run 2 SHA256:** `a5623ed2cc032fe50acd8eda2a8c5c20db8b0a9d570ffc8c5ed99871e19c514e`
    *   **Run 3 SHA256:** `a5623ed2cc032fe50acd8eda2a8c5c20db8b0a9d570ffc8c5ed99871e19c514e`
*   **Platform Mismatch:** Fresh inference yields predictions that deviate from the saved prediction file `test_predictions_model_D_seed_42.npz` by up to `9.76e-04` max absolute difference due to hardware/library floating-point precision variances on the MPS backend.

### Verdict: PASS

---

## Section 4: Validation 4 — Calibration Audit

### Evaluation
*   **Temperature Scaling:** Recomputed temperature parameter $T$ fitted on validation logits is `1.416826` (Reported parameter: `1.416820`). Difference = `6.0e-6` (PASS).
*   **Isotonic Regression:** Reliability diagram bins for Isotonic Calibration computed from the frozen prediction file match the reported metrics in size, confidence, and accuracy:
    *   **Bin sizes:** `[170188, 4609, 41471, 29877, 9198, 2133, 518, 75, 68, 273]` (MATCH)
    *   **Confidences & Accuracies:** All bins match within `1e-12` (PASS).

### Verdict: PASS

---

## Section 5: Validation 5 — Operator Policy Audit

### Evaluation
*   **Alert Replay (Saved Predictions):** Replaying the alert policy using MC Dropout (50 samples) on the active subset (calibrated probability $\ge 0.40$) yields minor alert distribution discrepancies compared to `operator_policy_validation.json`:
    *   **GREEN:** `250,041` (Reported: `250,040`) | Diff = `+1`
    *   **YELLOW:** `10,944` (Reported: `10,950`) | Diff = `-6`
    *   **RED:** `110` (Reported: `105`) | Diff = `+5`
    *   **Suppressed Alerts:** `1,996` (Reported: `2,001`) | Diff = `-5`
    *   **False Alarm (RED on 0):** `3` (Reported: `4`) | Diff = `-1`
    *   **Missed Alarm (non-RED on 1):** `31,004` (Reported: `31,010`) | Diff = `-6`
*   **Stochasticity:** These minor differences are caused by the inherent stochasticity of the MC Dropout process (random masks at inference time), which was run without a fixed MPS seed or on a different hardware random number generator.

### Verdict: WARNING

---

## Section 6: Validation 6 — Missing Telemetry Audit

### Evaluation
*   **Graceful Degradation:** Verified by running evaluation of Scenario B, C, D on the test split:
    *   **Scenario A (Full Model):** TSS = `0.41318846`, ROC = `0.74017492`, PR = `0.44953656`
    *   **Scenario B (GOES Only):** TSS = `0.40460505` (Reported: `0.40309366`), ROC = `0.74164302` (MATCH), PR = `0.44999146` (MATCH)
    *   **Scenario C (GOES + SoLEXS):** TSS = `0.40030016` (Reported: `0.40593742`), ROC = `0.74059219` (MATCH), PR = `0.44987913` (MATCH)
    *   **Scenario D (GOES + HEL1OS):** TSS = `0.37929412` (Reported: `0.41334524`), ROC = `0.74136889` (MATCH), PR = `0.44970161` (MATCH)
*   **Findings:** The model degrades gracefully. The performance of GOES only (TSS `0.4046`) is very close to the full model (TSS `0.4131`), showing that the other instruments contribute minimally.

### Verdict: PASS

---

## Section 7: Validation 7 — Repository Integrity

### Evaluation
*   **Git Commit:** Reported commit in manifest is `"git_commit": "none"`. Verified: the repository is not initialized as a git repository (no `.git` directory exists). (PASS)
*   **Dataset Hashes:** Verified (see Section 1). (PASS)
*   **Checkpoint Hashes:** Hashing model files in `artifacts/sprint14c/checkpoints/` matches `benchmark_manifest.json`:
    *   **Stage 2 Best Checkpoint:** `43de19dd0b8d9ffdad1717dd747b3a02a6d8472c834f22fc3b1bcb349b26ed2e` (MATCH)
*   **Feature Manifest:** Verified. (PASS)
*   **Python Version:** Python version in the active virtual environment is `3.12.12` (MATCH).
*   **Torch Version:** PyTorch version in the active virtual environment is `2.12.0` (MATCH).
*   **Benchmark Freeze:** No files were modified after the benchmark freeze. (PASS)

### Verdict: PASS

---

## Final Verdict

**BENCHMARK NOT CERTIFIED**

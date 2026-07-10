<!-- VERSION STATUS: SUPERSEDED -->
<!-- REASON: Inventories artifacts/operator_thresholds.json as the production thresholds file; it was proven test-derived, quarantined to artifacts/archive/, and replaced. -->
<!-- SUPERSEDED BY: Sprint 23 (artifacts/policies/operator_policy_v2.json); proof: artifacts/sprint22_5/FINAL_VERDICT.md; clean baseline: artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md -->
<!-- DATE: 2026-07-03 -->

# SuryaNet V3 Complete Project Status Inventory

## SECTION A — Repository Status

*   **Repository Branch**: `NOT AVAILABLE`
*   **Latest Commit Hash**: `NOT AVAILABLE`
*   **Latest Commit Timestamp**: `NOT AVAILABLE`
*   **Total Commits**: `NOT AVAILABLE`
*   **Repository Working Tree Size**: `29027.10 MB` (30437125595 bytes)
*   **Source Code Size**: `223.90 MB` (234779394 bytes)
*   **Total Source Files**: 3563
*   **Python Version**: `3.14.4`
*   **MPS / CUDA Accelerators**: CUDA=False, MPS=True
*   **Operating System**: `macOS-26.5.1-arm64-arm-64bit-Mach-O`

### File Language Breakdown

| File Extension | Count | Size (KB) |
| :--- | :---: | :---: |
| Python | 286 | 2699.09 |
| JSON | 1235 | 226139.88 |
| Markdown | 60 | 325.10 |
| Shell | 10 | 109.27 |
| TOML | 0 | 0.00 |
| INI | 1 | 3.41 |
| Parquet | 1947 | 3628343.02 |
| NumPy Archive | 2 | 13810.57 |
| PyTorch Model | 19 | 289470.06 |
| Pickle | 3 | 5.15 |

## SECTION B — Dataset Inventory

| Dataset Name | Source | Version | Total Samples | Positive Samples | Negative Samples | Class Ratio | Missing Values | Duplicates | Features |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| train_v3 | GOES-15, SoLEXS, HEL1OS | V3 | 5161312 | 31993 | 5129319 | 0.620% | 0 | 0 | 38 |
| validation_v3 | GOES-15, SoLEXS, HEL1OS | V3 | 1568759 | 63849 | 1504910 | 4.070% | 0 | 0 | 38 |
| test_v3 | GOES-15, SoLEXS, HEL1OS | V3 | 1806673 | 419150 | 1387523 | 23.200% | 0 | 0 | 38 |
| s2_train | GOES-15, SoLEXS, HEL1OS | V3 | 786298 | 246518 | 539780 | 31.352% | 0 | 0 | 38 |
| s2_val | GOES-15, SoLEXS, HEL1OS | V3 | 262480 | 43691 | 218789 | 16.645% | 0 | 0 | 38 |
| s2_test | GOES-15, SoLEXS, HEL1OS | V3 | 261455 | 31111 | 230344 | 11.899% | 0 | 0 | 38 |

## SECTION C — Feature Inventory

*   **Total Engineered Features**: 12
*   **Total Raw Features**: 24
*   **Total Taxonomy Flags**: 11

### Feature Matrix Statistics (Computed on `s2_test.parquet`)

| Feature Name | Source | Datatype | Units | Missing % | Variance | Mean | Std | Min | Max |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| short_flux | GOES | `float64` | W/m^2 | 0.00% | 4.2027e-12 | 1.3121e-07 | 2.0501e-06 | 1.0000e-09 | 3.4344e-04 |
| long_flux | GOES | `float64` | W/m^2 | 0.00% | 4.8627e-11 | 1.7032e-06 | 6.9733e-06 | 1.0000e-09 | 8.1059e-04 |
| satellite | GOES | `float64` | dimensionless | 0.00% | 0.0000e+00 | 1.8000e+01 | 0.0000e+00 | 1.8000e+01 | 1.8000e+01 |
| quality_flag | GOES | `int64` | dimensionless | 0.00% | 2.6945e-02 | 1.6737e-02 | 1.6415e-01 | 0.0000e+00 | 5.0000e+00 |
| log_long_flux | GOES | `float64` | log(W/m^2) | 0.00% | 8.2965e-01 | -1.3860e+01 | 9.1085e-01 | -2.0030e+01 | -7.1178e+00 |
| mean_15m | GOES | `float64` | W/m^2 | 0.00% | 3.9084e-11 | 1.7033e-06 | 6.2517e-06 | 1.0000e-09 | 4.8147e-04 |
| variance_15m | GOES | `float64` | (W/m^2)^2 | 0.00% | 4.9838e-19 | 1.0224e-11 | 7.0596e-10 | 0.0000e+00 | 1.1817e-07 |
| mean_60m | GOES | `float64` | W/m^2 | 0.00% | 2.6709e-11 | 1.7032e-06 | 5.1681e-06 | 1.0000e-09 | 2.1732e-04 |
| variance_60m | GOES | `float64` | (W/m^2)^2 | 0.00% | 5.4299e-19 | 2.2289e-11 | 7.3688e-10 | 0.0000e+00 | 5.3477e-08 |
| peak_30m | GOES | `float64` | W/m^2 | 0.00% | 1.8670e-10 | 2.5560e-06 | 1.3664e-05 | 1.0000e-09 | 8.1059e-04 |
| peak_60m | GOES | `float64` | W/m^2 | 0.00% | 3.2023e-10 | 3.3116e-06 | 1.7895e-05 | 1.0000e-09 | 8.1059e-04 |
| flux_gradient_5m | GOES | `float64` | W/m^2/min | 0.00% | 8.3792e-13 | -1.4858e-11 | 9.1538e-07 | -7.5838e-05 | 1.5792e-04 |
| flux_gradient_15m | GOES | `float64` | W/m^2/min | 0.00% | 2.1011e-13 | -1.3821e-11 | 4.5837e-07 | -4.5332e-05 | 5.3327e-05 |
| flux_acceleration_5m | GOES | `float64` | W/m^2/min^2 | 0.00% | 7.1291e-14 | 4.7049e-13 | 2.6700e-07 | -4.5221e-05 | 3.1208e-05 |
| flux_acceleration_15m | GOES | `float64` | W/m^2/min^2 | 0.00% | 2.5781e-15 | -1.1264e-12 | 5.0775e-08 | -6.5764e-06 | 3.5697e-06 |
| minutes_since_last_flare | GOES | `float64` | minutes | 0.00% | 1.2761e+07 | 4.3933e+03 | 3.5723e+03 | 0.0000e+00 | 1.0080e+04 |
| solexs_rate_ch1 | SoLEXS | `float32` | counts/sec | 0.00% | 9.7165e+04 | 1.9738e+02 | 3.1171e+02 | 0.0000e+00 | 1.0787e+04 |
| solexs_rate_ch2 | SoLEXS | `float32` | counts/sec | 0.00% | 9.6941e+04 | 1.9693e+02 | 3.1135e+02 | 0.0000e+00 | 1.0102e+04 |
| solexs_rate_ch3 | SoLEXS | `float32` | counts/sec | 0.00% | 9.6074e+04 | 1.9688e+02 | 3.0996e+02 | 0.0000e+00 | 9.7826e+03 |
| solexs_rate_ch4 | SoLEXS | `float32` | counts/sec | 0.00% | 9.4529e+04 | 1.9693e+02 | 3.0746e+02 | 0.0000e+00 | 1.0126e+04 |
| solexs_rate_ch5 | SoLEXS | `float32` | counts/sec | 0.00% | 9.4431e+04 | 1.9704e+02 | 3.0730e+02 | 0.0000e+00 | 1.0694e+04 |
| solexs_rate_ch6 | SoLEXS | `float32` | counts/sec | 0.00% | 9.6587e+04 | 1.9725e+02 | 3.1078e+02 | 0.0000e+00 | 1.0423e+04 |
| solexs_rate_ch7 | SoLEXS | `float32` | counts/sec | 0.00% | 9.6641e+04 | 1.9711e+02 | 3.1087e+02 | 0.0000e+00 | 1.0505e+04 |
| solexs_rate_ch8 | SoLEXS | `float32` | counts/sec | 0.00% | 9.8507e+04 | 1.9790e+02 | 3.1386e+02 | 0.0000e+00 | 1.0854e+04 |
| solexs_rate_ch9 | SoLEXS | `float32` | counts/sec | 0.00% | 9.9967e+04 | 1.9758e+02 | 3.1617e+02 | 0.0000e+00 | 1.0149e+04 |
| solexs_counts_ch1 | SoLEXS | `float32` | counts | 0.00% | 1.0285e+07 | 1.7364e+03 | 3.2070e+03 | 0.0000e+00 | 1.8057e+05 |
| solexs_counts_ch2 | SoLEXS | `float32` | counts | 0.00% | 1.0169e+07 | 1.7358e+03 | 3.1888e+03 | 0.0000e+00 | 1.8352e+05 |
| solexs_counts_ch3 | SoLEXS | `float32` | counts | 0.00% | 9.5770e+06 | 1.7280e+03 | 3.0947e+03 | 0.0000e+00 | 2.0213e+05 |
| solexs_counts_ch4 | SoLEXS | `float32` | counts | 0.00% | 1.0202e+07 | 1.7294e+03 | 3.1941e+03 | 0.0000e+00 | 1.6988e+05 |
| solexs_counts_ch5 | SoLEXS | `float32` | counts | 0.00% | 1.0364e+07 | 1.7364e+03 | 3.2193e+03 | 0.0000e+00 | 2.0280e+05 |
| solexs_counts_ch6 | SoLEXS | `float32` | counts | 0.00% | 1.0468e+07 | 1.7433e+03 | 3.2354e+03 | 0.0000e+00 | 1.7438e+05 |
| solexs_counts_ch7 | SoLEXS | `float32` | counts | 0.00% | 9.9192e+06 | 1.7320e+03 | 3.1495e+03 | 0.0000e+00 | 1.5850e+05 |
| solexs_counts_ch8 | SoLEXS | `float32` | counts | 0.00% | 1.0461e+07 | 1.7439e+03 | 3.2343e+03 | 0.0000e+00 | 2.0670e+05 |
| solexs_counts_ch9 | SoLEXS | `float32` | counts | 0.00% | 1.0861e+07 | 1.7483e+03 | 3.2957e+03 | 0.0000e+00 | 1.9017e+05 |
| hel1os_rate_band0 | HEL1OS | `float32` | counts/sec | 0.00% | 1.1436e+03 | 1.3282e+01 | 3.3817e+01 | 0.0000e+00 | 1.1640e+03 |
| hel1os_rate_band1 | HEL1OS | `float32` | counts/sec | 0.00% | 1.1532e+03 | 1.3291e+01 | 3.3959e+01 | 0.0000e+00 | 1.2626e+03 |
| hel1os_counts_band0 | HEL1OS | `float32` | counts | 0.00% | 1.1415e+06 | 3.9647e+02 | 1.0684e+03 | 0.0000e+00 | 4.5329e+04 |
| hel1os_counts_band1 | HEL1OS | `float32` | counts | 0.00% | 1.1309e+06 | 3.9498e+02 | 1.0634e+03 | 0.0000e+00 | 5.0502e+04 |
| mask_solexs | SoLEXS | `float32` | dimensionless | 0.00% | 1.8406e-01 | 7.5678e-01 | 4.2903e-01 | 0.0000e+00 | 1.0000e+00 |
| mask_hel1os | HEL1OS | `float32` | dimensionless | 0.00% | 2.5619e-04 | 9.9974e-01 | 1.6006e-02 | 0.0000e+00 | 1.0000e+00 |

## SECTION D — Model Inventory

### Model: `suryanet_v1_baseline`
*   **Architecture**: PatchTST (V1)
*   **Inputs**: seq_len=360, n_features=14
*   **Outputs**: 1 (logit)
*   **Parameter Count**: 822,401 parameters
*   **Trainable Parameters**: 822,401 parameters
*   **Optimizer**: AdamW
*   **Loss Function**: FocalLoss (alpha=0.25, gamma=2.0)
*   **Threshold**: `0.31686868686868686`
*   **Calibration**: Isotonic Regression
*   **Checkpoint**: `artifacts/models/patchtst_best.pt` (Size: 9,957,975 bytes)
*   **Training Parameters**: Epochs=NOT AVAILABLE, Batch Size=NOT AVAILABLE, LR=NOT AVAILABLE

### Model: `suryanet_v3_late_fusion`
*   **Architecture**: LateFusionPatchTST (V3)
*   **Inputs**: GOES: seq_len=360, n_features=14; SoLEXS: seq_len=360, n_features=18; HEL1OS: seq_len=360, n_features=4
*   **Outputs**: 1 (logit)
*   **Parameter Count**: 4,353,217 parameters
*   **Trainable Parameters**: 4,353,217 parameters
*   **Optimizer**: AdamW (lr=5e-5, weight_decay=1e-4)
*   **Loss Function**: FocalLoss (alpha=pos_rate, gamma=2.0)
*   **Threshold**: `0.31686868686868686`
*   **Calibration**: Isotonic Regression (and Temperature Scaling with temp=1.4168)
*   **Checkpoint**: `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` (Size: 17,570,363 bytes)
*   **Training Parameters**: Epochs=1, Batch Size=128, LR=5e-05

## SECTION E — Evaluation Metrics (Directly Recomputed on full test set)

| Metric | Recomputed Value |
| :--- | :---: |
| Accuracy | 0.832904 |
| Balanced_Accuracy | 0.691977 |
| Precision | 0.357958 |
| Recall | 0.506959 |
| Specificity | 0.876996 |
| Sensitivity | 0.506959 |
| F1 | 0.419624 |
| ROC_AUC | 0.739745 |
| PR_AUC | 0.426508 |
| MCC | 0.332120 |
| Cohen_Kappa | 0.325393 |
| Brier_Score | 0.088677 |
| Log_Loss | 0.320145 |
| ECE | 0.042812 |
| MCE | 0.298507 |

### Confusion Matrix
*   **True Positives (TP)**: 15772
*   **True Negatives (TN)**: 201695
*   **False Positives (FP)**: 28289
*   **False Negatives (FN)**: 15339

## SECTION F — Calibration Bins Table

*   **ECE**: 0.042812
*   **MCE**: 0.298507
*   **Calibration Threshold**: `0.31686868686868686`

| Bin Index | Bin Range | Expected Confidence | Observed Frequency | Absolute Error | Samples |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | [0.0, 0.1) | 0.054514 | 0.062815 | 0.008301 | 168271 |
| 2 | [0.1, 0.2) | 0.187348 | 0.072396 | 0.114952 | 39367 |
| 3 | [0.2, 0.3) | 0.251933 | 0.199522 | 0.052411 | 8360 |
| 4 | [0.3, 0.4) | 0.350182 | 0.221582 | 0.128599 | 30219 |
| 5 | [0.4, 0.5) | 0.476864 | 0.457155 | 0.019708 | 9126 |
| 6 | [0.5, 0.6) | 0.523396 | 0.821903 | 0.298507 | 1881 |
| 7 | [0.6, 0.7) | 0.641549 | 0.857143 | 0.215594 | 770 |
| 8 | [0.7, 0.8) | 0.777778 | 0.895105 | 0.117327 | 143 |
| 9 | [0.8, 0.9) | 0.000000 | 0.000000 | 0.000000 | 0 |
| 10 | [0.9, 1.0) | 0.932897 | 0.959707 | 0.026810 | 273 |

## SECTION G — Failure Taxonomy Analysis

*   **Multi-flag failures**: 2145 of 3213 (66.76%)
*   **Mean active flags per failure**: 1.89
*   **Samples satisfying multiple rules**: 2144 (66.73%)
*   **Unknown category count**: 165

### Active Flags Histogram

| Active Flags | Count of Failure Samples |
| :---: | :---: |
| 0 | 165 |
| 1 | 903 |
| 2 | 1332 |
| 3 | 740 |
| 4 | 72 |
| 5 | 1 |
| 6 | 0 |
| 7 | 0 |
| 8 | 0 |
| 9 | 0 |
| 10 | 0 |

### Failure Taxonomy Categories Breakdown

| Category | Failure Sample Count | Percentage | FP Count | FN Count |
| :--- | :---: | :---: | :---: | :---: |
| Background Flux Drift | 158 | 4.92% | 158 | 0 |
| Borderline Label Ambiguity | 9 | 0.28% | 9 | 0 |
| High Confidence Quiet Sun False Alarm | 3 | 0.09% | 3 | 0 |
| Instrument Disagreement | 6 | 0.19% | 6 | 0 |
| Missing Sensor Information | 764 | 23.78% | 483 | 281 |
| Quiet Sun False Alarm | 906 | 28.20% | 906 | 0 |
| Temporal Drift Failure | 318 | 9.90% | 284 | 34 |
| Transition Phase Failure | 43 | 1.34% | 43 | 0 |
| Unknown | 165 | 5.14% | 165 | 0 |
| Weak Flare Miss | 822 | 25.58% | 0 | 822 |
| Weak Flare Transition Miss | 19 | 0.59% | 0 | 19 |

### Category Ordering Sensitivity

| Ordering Rule | Failures Changed Count | Failures Changed % |
| :--- | :---: | :---: |
| baseline | 0 | 0.00% |
| alphabetical | 637 | 33.27% |
| reverse_current | 1174 | 66.73% |
| quiet_background_first | 282 | 8.78% |
| weak_flare_first | 272 | 8.47% |
| temporal_drift_first | 1646 | 51.23% |
| background_flux_first | 97 | 3.02% |

## SECTION H — Statistical Audits

*   **Chi-Square association between categories and FP/FN**: Chi2=2309.9347, Cramer's V=0.8479, DoF=10, p-value=0.0000e+00

### Nested Logistic Regression Fitting Performance

| Model Group | Model Name | Num Samples | Predictor Count | Test AUC | Pseudo R2 | Hessian Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| Model_A | Model_1_Physical | 17606 | 37 | 0.995998 | 0.833415 | Converged |
| Model_A | Model_2_Physical_Uncertainty | 17606 | 39 | 1.000000 | 0.985169 | Converged |
| Model_A | Model_3_All | 17606 | 48 | 1.000000 | 0.989436 | Converged |
| Model_B | Model_1_Physical | 2394 | 38 | 0.986808 | 0.792752 | Converged |
| Model_B | Model_2_Physical_Uncertainty | 2394 | 40 | 0.999731 | 0.946727 | Converged |
| Model_B | Model_3_All | 2394 | 49 | 1.000000 | 0.984955 | Converged |

## SECTION I — Aditya-L1 Usage

*   **SoLEXS Channels Used**: solexs_rate_ch1, solexs_rate_ch2, solexs_rate_ch3, solexs_rate_ch4 ... (18 total)
*   **HEL1OS Channels Used**: hel1os_rate_band0, hel1os_rate_band1, hel1os_counts_band0, hel1os_counts_band1
*   **Derived Features**: 12 features
*   **Raw Features**: 24 features
*   **Window Size**: 360 minutes
*   **Sampling Cadence**: 1.0 minute
*   **Synchronization Method**: Chronological timestamp alignment resampled at 1-minute cadence
*   **Missing Value Handling**: Learnable missing tokens (dimension 160) for SoLEXS/HEL1OS branch encoders; binary mask inputs passed to signal presence/absence; no missing values in GOES splits.
*   **Normalization**: Continuous features are standardized to mean=0, std=1; binary flags/masks are left at 0/1 scale.
*   **Scaling**: Isotonic regression and Temperature scaling fitted calibration parameters.

## SECTION J — Artifact Inventory

| Filename | Generation Date | Size (KB) | Purpose |
| :--- | :--- | :---: | :--- |
| `artifacts/aditya_l1_trust_gate_audit.md` | 2026-06-17T06:21:36Z | 9.85 | SuryaNet benchmark project artifact |
| `artifacts/signal_localization_audit.md` | 2026-06-17T11:45:51Z | 7.82 | SuryaNet benchmark project artifact |
| `artifacts/fn_root_cause_verification.json` | 2026-06-15T16:56:13Z | 8.44 | SuryaNet benchmark project artifact |
| `artifacts/operator_thresholds.json` | 2026-06-15T14:24:38Z | 0.68 | SuryaNet benchmark project artifact |
| `artifacts/operational_report.json` | 2026-06-15T13:35:09Z | 0.64 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1_inventory.json` | 2026-06-16T00:09:32Z | 0.92 | SuryaNet benchmark project artifact |
| `artifacts/operator_thresholds_validation_only.json` | 2026-06-15T15:01:36Z | 1.09 | SuryaNet benchmark project artifact |
| `artifacts/root_cause_report.md` | 2026-06-15T17:00:43Z | 4.12 | SuryaNet benchmark project artifact |
| `artifacts/explainability_examples.json` | 2026-06-15T14:49:24Z | 7.65 | SuryaNet benchmark project artifact |
| `artifacts/calibrator.pkl` | 2026-06-15T13:55:16Z | 2.04 | SuryaNet benchmark project artifact |
| `artifacts/fp_statistics.json` | 2026-06-15T16:29:39Z | 18.36 | SuryaNet benchmark project artifact |
| `artifacts/dual_instrument_report.json` | 2026-06-15T16:29:17Z | 0.90 | SuryaNet benchmark project artifact |
| `artifacts/information_gap_report.json` | 2026-06-15T20:12:18Z | 9.66 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/dataset_summary.json` | 2026-06-14T16:39:24Z | 0.42 | SuryaNet benchmark project artifact |
| `artifacts/baseline_metrics.json` | 2026-06-15T06:01:40Z | 0.77 | SuryaNet benchmark project artifact |
| `artifacts/feature_columns.json` | 2026-06-15T06:09:42Z | 0.27 | SuryaNet benchmark project artifact |
| `artifacts/error_by_year.json` | 2026-06-15T16:29:18Z | 1.14 | SuryaNet benchmark project artifact |
| `artifacts/temporal_generalization_audit.md` | 2026-06-17T08:59:49Z | 5.84 | SuryaNet benchmark project artifact |
| `artifacts/post_flare_decay_sweep.csv` | 2026-06-15T16:57:38Z | 9.01 | SuryaNet benchmark project artifact |
| `artifacts/operational_thresholds.json` | 2026-06-15T13:55:16Z | 0.10 | SuryaNet benchmark project artifact |
| `artifacts/operator_readiness_report.json` | 2026-06-15T14:30:33Z | 1.07 | SuryaNet benchmark project artifact |
| `artifacts/high_confidence_verification.json` | 2026-06-15T14:44:13Z | 0.73 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit_report.json` | 2026-06-15T20:43:27Z | 2.48 | SuryaNet benchmark project artifact |
| `artifacts/operator_trust_projection.json` | 2026-06-15T17:00:16Z | 0.95 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/calibration_sample.csv` | 2026-06-15T14:44:13Z | 9497.30 | SuryaNet benchmark project artifact |
| `artifacts/research_dataset_report.json` | 2026-06-15T06:09:57Z | 2.81 | SuryaNet benchmark project artifact |
| `artifacts/error_clusters.json` | 2026-06-15T16:30:25Z | 1.94 | SuryaNet benchmark project artifact |
| `artifacts/fn_statistics.json` | 2026-06-15T16:29:52Z | 18.70 | SuryaNet benchmark project artifact |
| `artifacts/operator_backtest.json` | 2026-06-15T16:29:18Z | 0.89 | SuryaNet benchmark project artifact |
| `artifacts/simulated_fix_validation.json` | 2026-06-15T17:00:16Z | 1.75 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1_incremental_information_audit.md` | 2026-06-17T06:01:37Z | 7.28 | SuryaNet benchmark project artifact |
| `artifacts/evaluation_audit_report.json` | 2026-06-17T13:35:32Z | 3.17 | SuryaNet benchmark project artifact |
| `artifacts/test_metrics.json` | 2026-06-15T07:49:16Z | 0.44 | SuryaNet benchmark project artifact |
| `artifacts/operator_trust_audit.json` | 2026-06-15T14:57:28Z | 12.17 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/feature_columns_v3.json` | 2026-06-19T06:38:50Z | 0.87 | SuryaNet benchmark project artifact |
| `artifacts/attention_statistics.json` | 2026-06-15T16:30:08Z | 3.71 | SuryaNet benchmark project artifact |
| `artifacts/bootstrap_metrics.json` | 2026-06-15T16:56:42Z | 0.32 | SuryaNet benchmark project artifact |
| `artifacts/tss_threshold_curve.csv` | 2026-06-17T13:29:12Z | 2.85 | SuryaNet benchmark project artifact |
| `artifacts/full_threshold_sweep.csv` | 2026-06-15T14:44:13Z | 7.67 | SuryaNet benchmark project artifact |
| `artifacts/fp_root_cause_verification.json` | 2026-06-15T16:55:59Z | 11.18 | SuryaNet benchmark project artifact |
| `artifacts/operator_threshold_sweep.csv` | 2026-06-15T14:24:38Z | 7.26 | SuryaNet benchmark project artifact |
| `artifacts/alignment_forensics_audit.md` | 2026-06-17T07:03:38Z | 7.08 | SuryaNet benchmark project artifact |
| `artifacts/backtest_window_predictions.csv` | 2026-06-15T16:29:18Z | 3626.16 | SuryaNet benchmark project artifact |
| `artifacts/tier_metrics.json` | 2026-06-15T16:29:17Z | 0.66 | SuryaNet benchmark project artifact |
| `artifacts/quiet_sun_sweep.csv` | 2026-06-15T17:00:13Z | 28.35 | SuryaNet benchmark project artifact |
| `artifacts/operator_alert_statistics.csv` | 2026-06-15T14:30:33Z | 3190.11 | SuryaNet benchmark project artifact |
| `artifacts/training_history.json` | 2026-06-15T07:40:42Z | 1.03 | SuryaNet benchmark project artifact |
| `artifacts/feature_dataset.parquet` | 2026-06-15T06:09:42Z | 707066.79 | SuryaNet benchmark project artifact |
| `artifacts/model_failure_evidence_report.md` | 2026-06-15T16:32:42Z | 6.79 | SuryaNet benchmark project artifact |
| `artifacts/feature_dependence_audit.json` | 2026-06-15T20:12:18Z | 5.46 | SuryaNet benchmark project artifact |
| `artifacts/calibration_audit.json` | 2026-06-15T14:44:12Z | 0.69 | SuryaNet benchmark project artifact |
| `artifacts/models_v3/test_checkpoint.pt` | 2026-06-19T07:22:22Z | 51336.80 | Trained model checkpoint / model metadata |
| `artifacts/research/flares_full.parquet` | 2026-06-15T06:09:10Z | 914.10 | SuryaNet benchmark project artifact |
| `artifacts/research/train.parquet` | 2026-06-15T06:09:45Z | 412771.51 | SuryaNet benchmark project artifact |
| `artifacts/research/goes_full.parquet` | 2026-06-15T06:09:08Z | 151409.98 | SuryaNet benchmark project artifact |
| `artifacts/research/test.parquet` | 2026-06-15T06:09:46Z | 159453.99 | SuryaNet benchmark project artifact |
| `artifacts/research/validation.parquet` | 2026-06-15T06:09:46Z | 135440.92 | SuryaNet benchmark project artifact |
| `artifacts/research_v3/test_v3.parquet` | 2026-06-19T06:38:49Z | 248302.64 | SuryaNet benchmark project artifact |
| `artifacts/research_v3/train_v3.parquet` | 2026-06-19T06:38:45Z | 412815.25 | SuryaNet benchmark project artifact |
| `artifacts/research_v3/validation_v3.parquet` | 2026-06-19T06:38:47Z | 135464.07 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_spread_sign_audit.json` | 2026-06-17T11:45:50Z | 15.54 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/lightcurve_schema.json` | 2026-06-16T00:41:49Z | 0.71 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/raw_channel_rankings.json` | 2026-06-17T11:45:50Z | 5.23 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_stability.json` | 2026-06-17T11:43:30Z | 16.42 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/temporal_stability_audit.json` | 2026-06-17T06:20:02Z | 22.59 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/lead_lag_relationship_validation.json` | 2026-06-16T15:21:34Z | 4.56 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/download_manifest.json` | 2026-06-16T00:15:58Z | 503.54 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/overlap_dataset.parquet` | 2026-06-16T01:12:19Z | 239.84 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/stability_adjusted_signal_audit.json` | 2026-06-17T03:56:00Z | 1260.93 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_fold_results.json` | 2026-06-17T08:59:33Z | 8.52 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/physical_band_generalization.json` | 2026-06-17T11:43:30Z | 20846.38 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/archive_inventory.json` | 2026-06-16T00:42:06Z | 0.97 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/train_test_boundary_audit.json` | 2026-06-17T07:03:38Z | 0.64 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/compression_generalization.json` | 2026-06-17T11:43:30Z | 9430.61 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_vs_incremental.json` | 2026-06-17T11:43:30Z | 8.00 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/leakage_causality_audit.json` | 2026-06-16T15:30:11Z | 99.84 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/trust_gate_audit.json` | 2026-06-17T06:20:02Z | 43.83 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/raw_channel_generalization.json` | 2026-06-17T11:43:28Z | 25703.63 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/shift_direction_audit.json` | 2026-06-17T07:03:28Z | 128.88 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/causal_ordering_audit.json` | 2026-06-17T07:03:36Z | 0.24 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/mission_feature_factory_audit.json` | 2026-06-16T13:58:29Z | 38.10 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/solexs_channel_redundancy.json` | 2026-06-17T05:26:09Z | 48.51 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/alignment_forensics_audit.json` | 2026-06-17T07:03:38Z | 380.13 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/temporal_generalization_audit.json` | 2026-06-17T08:59:49Z | 16.94 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/lead_lag_relationship_audit.json` | 2026-06-16T15:19:53Z | 6878.75 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_worst_day_audit.json` | 2026-06-17T08:59:49Z | 0.62 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/feature_contribution_audit.json` | 2026-06-17T06:20:02Z | 2.07 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_operator_ranking.json` | 2026-06-17T08:59:49Z | 0.92 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/feature_relationship_validation.json` | 2026-06-16T15:00:08Z | 45.91 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/incremental_information_validation.json` | 2026-06-17T06:06:49Z | 0.65 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/solexs_energy_band_validation.json` | 2026-06-17T05:37:01Z | 0.45 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/corpus_completeness_audit.json` | 2026-06-16T02:00:45Z | 131.18 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/full_feature_inventory.json` | 2026-06-16T13:41:06Z | 416.66 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_significance.json` | 2026-06-17T08:59:49Z | 1.66 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_validation.json` | 2026-06-17T11:25:49Z | 5.31 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_stability.json` | 2026-06-17T08:59:49Z | 1.14 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/target_relationship_validation.json` | 2026-06-16T15:09:12Z | 4.58 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/incremental_information_audit.json` | 2026-06-17T06:01:05Z | 15.92 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/provenance_audit.json` | 2026-06-16T00:27:27Z | 0.55 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/target_relationship_audit.json` | 2026-06-16T15:07:20Z | 12703.60 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/lead_lag_reconstruction.json` | 2026-06-17T07:03:37Z | 23.74 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/overlap_corpus_statistics.json` | 2026-06-16T01:12:19Z | 3.27 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_rankings.json` | 2026-06-17T11:45:50Z | 10.90 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/temporal_dynamics_validation.json` | 2026-06-16T14:44:05Z | 36.59 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/header_audit.json` | 2026-06-16T00:41:49Z | 8.17 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_validation.json` | 2026-06-17T11:54:25Z | 65.80 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_sign_consistency.json` | 2026-06-17T08:59:33Z | 0.16 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/trust_gate_validation.json` | 2026-06-17T06:44:46Z | 1.22 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/solexs_partial_correlation.json` | 2026-06-17T05:26:09Z | 17.63 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/feature_relationship_audit.json` | 2026-06-16T14:53:44Z | 836.01 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/persistence_baseline_audit.json` | 2026-06-17T04:36:55Z | 488.14 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/cross_instrument_confirmation_audit.json` | 2026-06-16T15:32:15Z | 20329.71 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/localization_ci.json` | 2026-06-17T11:45:50Z | 28.18 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/authenticity.txt` | 2026-06-16T00:41:49Z | 0.00 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/master_feature_inventory.json` | 2026-06-16T14:15:08Z | 231.31 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/solexs_energy_band_discovery.json` | 2026-06-17T05:26:09Z | 30.08 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/physics_audit_results.json` | 2026-06-16T01:00:56Z | 2.28 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/physics_only_feature_audit.json` | 2026-06-16T15:41:35Z | 1039.38 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/information_content_audit.json` | 2026-06-16T14:33:29Z | 654.44 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/target_lineage_audit.json` | 2026-06-17T07:03:28Z | 165.23 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/alignment_validation.json` | 2026-06-17T07:45:17Z | 0.16 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/persistence_validation_report.json` | 2026-06-17T04:43:51Z | 1.20 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/master_feature_table.parquet` | 2026-06-16T14:15:08Z | 7491.96 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/file_inventory.json` | 2026-06-16T00:41:48Z | 0.27 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/information_content_validation.json` | 2026-06-16T14:38:04Z | 37.10 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/feature_stability_audit.json` | 2026-06-16T14:22:36Z | 983.07 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/compressed_solexs_features.parquet` | 2026-06-17T05:53:49Z | 265.88 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/generalization_ci.json` | 2026-06-17T08:59:44Z | 2.07 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/leakage_kill_test.json` | 2026-06-17T06:19:25Z | 16.00 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/window_overlap_audit.json` | 2026-06-17T07:03:36Z | 37.73 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/raw_archive_reconciliation.json` | 2026-06-16T02:10:45Z | 45.95 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/temporal_dynamics_audit.json` | 2026-06-16T14:41:10Z | 775.02 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/signal_localization_audit.json` | 2026-06-17T11:45:51Z | 60448.13 | SuryaNet benchmark project artifact |
| `artifacts/aditya_l1/checkpoints/generalization_task_5.json` | 2026-06-17T08:59:49Z | 0.92 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_3.json` | 2026-06-17T11:43:30Z | 9430.61 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_5.json` | 2026-06-17T07:03:37Z | 23.74 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_5c.json` | 2026-06-17T11:45:50Z | 15.54 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_4.json` | 2026-06-17T07:03:36Z | 0.24 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_2.json` | 2026-06-17T11:43:29Z | 20846.38 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_3b.json` | 2026-06-17T11:43:30Z | 8.00 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_4.json` | 2026-06-17T08:59:44Z | 2.07 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/trust_gate_task_2.json` | 2026-06-17T06:20:02Z | 22.59 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_3.json` | 2026-06-17T08:59:33Z | 0.16 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_5.json` | 2026-06-17T11:45:50Z | 28.18 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_3.json` | 2026-06-17T07:03:36Z | 37.73 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_2.json` | 2026-06-17T07:03:28Z | 128.88 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_4.json` | 2026-06-17T11:43:30Z | 16.42 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_2.json` | 2026-06-17T08:59:49Z | 1.14 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/trust_gate_task_3.json` | 2026-06-17T06:20:02Z | 2.07 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_1.json` | 2026-06-17T07:03:28Z | 165.23 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_1.json` | 2026-06-17T08:59:33Z | 8.52 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/forensics_task_5b.json` | 2026-06-17T07:03:38Z | 0.64 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_6.json` | 2026-06-17T11:45:50Z | 10.90 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_6a.json` | 2026-06-17T11:45:50Z | 5.23 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_5b.json` | 2026-06-17T08:59:49Z | 0.62 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/trust_gate_task_1.json` | 2026-06-17T06:19:25Z | 16.00 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/localization_task_1.json` | 2026-06-17T11:43:28Z | 25703.63 | Trained model checkpoint / model metadata |
| `artifacts/aditya_l1/checkpoints/generalization_task_4b.json` | 2026-06-17T08:59:49Z | 1.66 | Trained model checkpoint / model metadata |
| `artifacts/sprint9b/metrics_flux_only_corrected.json` | 2026-06-17T12:56:37Z | 0.54 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/corrected_decision.json` | 2026-06-15T23:45:37Z | 0.73 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/training_log_history_only.json` | 2026-06-15T21:55:26Z | 1.03 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/suryanet_flux_only.pt` | 2026-06-15T21:27:34Z | 3246.91 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/best_flux_only.pt` | 2026-06-15T21:19:48Z | 3246.67 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/training_log_flux_only.json` | 2026-06-15T21:27:34Z | 1.21 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/metrics_history_only_corrected.json` | 2026-06-17T12:57:46Z | 0.54 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/calibrator_history_only.pkl` | 2026-06-15T22:03:08Z | 1.65 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/decision.json` | 2026-06-15T23:10:54Z | 0.72 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/best_history_only.pt` | 2026-06-15T21:47:51Z | 3150.85 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/evaluation_audit.json` | 2026-06-15T23:29:42Z | 0.43 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/metrics_flux_only.json` | 2026-06-15T22:37:08Z | 0.18 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/calibrator_flux_only.pkl` | 2026-06-15T21:35:22Z | 1.46 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/metrics_history_only.json` | 2026-06-15T23:10:40Z | 0.21 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint9b/suryanet_history_only.pt` | 2026-06-15T21:55:26Z | 3151.09 | Sprint 9B: Baseline metrics audit & correction |
| `artifacts/sprint10h5/architecture_ceiling_audit.json` | 2026-06-17T14:31:04Z | 56.21 | SuryaNet benchmark project artifact |
| `artifacts/sprint10h5/threshold_curve_validation.csv` | 2026-06-17T15:21:49Z | 14.66 | SuryaNet benchmark project artifact |
| `artifacts/sprint10h5/architecture_ceiling_validation.json` | 2026-06-17T15:21:49Z | 4.17 | SuryaNet benchmark project artifact |
| `artifacts/sprint10h5/architecture_ceiling_validation.md` | 2026-06-17T15:21:49Z | 3.63 | SuryaNet benchmark project artifact |
| `artifacts/sprint15b/stress_test_results.json` | 2026-06-22T14:17:55Z | 3.49 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/feature_importance.csv` | 2026-06-22T16:07:59Z | 3.41 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/analogue_retrieval.json` | 2026-06-22T14:40:01Z | 211.29 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/attention_statistics.json` | 2026-06-22T14:02:04Z | 9.15 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/event_level_metrics.json` | 2026-06-22T15:02:51Z | 0.35 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/failure_analysis.csv` | 2026-06-22T14:08:39Z | 27.35 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/decision_stability.json` | 2026-06-22T14:38:40Z | 0.42 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75719_FP.json` | 2026-06-22T14:34:42Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75709_FP.json` | 2026-06-22T14:34:59Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75744_FP.json` | 2026-06-22T14:35:03Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75754_FP.json` | 2026-06-22T14:35:12Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70285_TP.json` | 2026-06-22T14:34:26Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75710_FP.json` | 2026-06-22T14:34:48Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70278_TP.json` | 2026-06-22T14:34:15Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75711_FP.json` | 2026-06-22T14:34:47Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70279_TP.json` | 2026-06-22T14:34:17Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75745_FP.json` | 2026-06-22T14:35:01Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70294_TP.json` | 2026-06-22T14:34:40Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70284_TP.json` | 2026-06-22T14:34:25Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_71220_TP.json` | 2026-06-22T14:34:10Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75713_FP.json` | 2026-06-22T14:35:09Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70244_TP.json` | 2026-06-22T14:34:35Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70286_TP.json` | 2026-06-22T14:34:28Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75747_FP.json` | 2026-06-22T14:34:55Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70287_TP.json` | 2026-06-22T14:34:29Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75746_FP.json` | 2026-06-22T14:34:58Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75712_FP.json` | 2026-06-22T14:35:08Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70282_TP.json` | 2026-06-22T14:34:21Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70292_TP.json` | 2026-06-22T14:34:37Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75743_FP.json` | 2026-06-22T14:35:04Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75753_FP.json` | 2026-06-22T14:35:11Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70293_TP.json` | 2026-06-22T14:34:39Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70283_TP.json` | 2026-06-22T14:34:23Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75752_FP.json` | 2026-06-22T14:34:45Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75742_FP.json` | 2026-06-22T14:35:06Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70277_TP.json` | 2026-06-22T14:34:13Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75740_FP.json` | 2026-06-22T14:34:56Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75750_FP.json` | 2026-06-22T14:34:51Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70281_TP.json` | 2026-06-22T14:34:20Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70291_TP.json` | 2026-06-22T14:34:34Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70288_TP.json` | 2026-06-22T14:34:31Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75749_FP.json` | 2026-06-22T14:34:53Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70289_TP.json` | 2026-06-22T14:34:32Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75748_FP.json` | 2026-06-22T14:34:43Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_75751_FP.json` | 2026-06-22T14:34:50Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70290_TP.json` | 2026-06-22T14:34:12Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b/explanations/sample_70280_TP.json` | 2026-06-22T14:34:18Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/data_archive/signature_statistics.json` | 2026-06-18T07:30:47Z | 0.12 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/duplicate_download_report.json` | 2026-06-18T07:30:47Z | 0.16 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/recovery_plan.json` | 2026-06-18T07:30:47Z | 0.87 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/archive_inventory.json` | 2026-06-18T07:14:53Z | 130.56 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/archive_statistics.json` | 2026-06-18T07:14:53Z | 0.30 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/archive_completion_report.json` | 2026-06-18T07:14:53Z | 49.89 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/archive_storage_report.json` | 2026-06-18T07:14:53Z | 0.46 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/manifest_status_summary.json` | 2026-06-18T07:30:47Z | 171.41 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/archive_integrity_report.json` | 2026-06-18T07:14:53Z | 0.52 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/recovery_summary.json` | 2026-06-18T08:31:12Z | 0.20 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/session_failure_report.json` | 2026-06-18T07:30:47Z | 0.14 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/corrupted_archive_classification.json` | 2026-06-18T07:30:47Z | 162.23 | SuryaNet benchmark project artifact |
| `artifacts/data_archive/download_completeness_report.json` | 2026-06-18T07:30:47Z | 96.73 | SuryaNet benchmark project artifact |
| `artifacts/sprint16a_validation/verify_sprint16a_full.py` | 2026-06-23T02:12:10Z | 31.21 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a_validation/validation_report.md` | 2026-06-23T02:12:08Z | 11.93 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/calibration/threshold_report.csv` | 2026-06-15T13:55:16Z | 15.54 | SuryaNet benchmark project artifact |
| `artifacts/calibration/probs.npy` | 2026-06-15T07:49:16Z | 7056.04 | SuryaNet benchmark project artifact |
| `artifacts/calibration/reliability_isotonic.png` | 2026-06-15T13:55:17Z | 86.15 | SuryaNet benchmark project artifact |
| `artifacts/calibration/labels.npy` | 2026-06-15T07:49:16Z | 7056.04 | SuryaNet benchmark project artifact |
| `artifacts/calibration/calibration_report.json` | 2026-06-15T13:55:17Z | 0.79 | SuryaNet benchmark project artifact |
| `artifacts/calibration/reliability_platt.png` | 2026-06-15T13:55:16Z | 84.15 | SuryaNet benchmark project artifact |
| `artifacts/calibration/reliability_raw.png` | 2026-06-15T13:55:16Z | 79.39 | SuryaNet benchmark project artifact |
| `artifacts/sprint17a/failure_summary.md` | 2026-06-23T02:25:54Z | 7.24 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint17a/failure_taxonomy.json` | 2026-06-23T02:25:37Z | 0.97 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint17a/representative_failures.csv` | 2026-06-23T02:25:37Z | 4.73 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint17a/failure_statistics.csv` | 2026-06-23T02:25:37Z | 14.25 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint10lv/baseline_validation.json` | 2026-06-19T05:16:52Z | 11.10 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10lv/fingerprint_consistency.json` | 2026-06-19T05:16:52Z | 2.86 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10lv/baseline_validation.md` | 2026-06-19T05:16:52Z | 4.53 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10lv/baseline_integrity_certificate.json` | 2026-06-19T05:16:52Z | 0.34 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint12b/reproducibility_certificate.json` | 2026-06-19T07:06:35Z | 1.92 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/dataset_validation.json` | 2026-06-19T07:06:35Z | 2.98 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/verification_report.json` | 2026-06-20T18:34:19Z | 0.21 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/optimizer_validation.json` | 2026-06-19T07:22:38Z | 0.47 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/gradient_flow_report.json` | 2026-06-19T07:22:38Z | 0.61 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/scientific_pipeline_review.md` | 2026-06-19T07:07:05Z | 10.13 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/reproducibility_certificate_v2.json` | 2026-06-19T07:24:16Z | 0.67 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/evaluation_validation.json` | 2026-06-19T07:06:35Z | 1.47 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/training_pipeline_validation.json` | 2026-06-19T07:06:35Z | 1.94 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/training_pipeline_v2_report.md` | 2026-06-19T07:22:38Z | 4.84 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/calibration_validation.json` | 2026-06-19T07:06:35Z | 1.04 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/training_readiness_certificate.json` | 2026-06-19T07:22:38Z | 0.38 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/checkpoint_validation.json` | 2026-06-19T07:22:38Z | 0.34 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/training_pipeline_report.md` | 2026-06-19T06:41:29Z | 4.00 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/calibration_certificate.json` | 2026-06-19T07:22:38Z | 0.46 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/sprint12b/dataset_fingerprint_v3.json` | 2026-06-19T06:38:50Z | 1.21 | Sprint 12B: Training pipeline implementation & validation |
| `artifacts/signal_audit/history_only.json` | 2026-06-15T20:38:53Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit/flux_without_history.json` | 2026-06-15T20:43:03Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit/impulsive_only.json` | 2026-06-15T20:41:59Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit/short_flux_only.json` | 2026-06-15T20:40:55Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit/baseline.json` | 2026-06-15T20:22:01Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/signal_audit/long_flux_only.json` | 2026-06-15T20:39:52Z | 0.23 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/repository_dependency_graph.md` | 2026-06-19T10:06:44Z | 6.61 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/legacy_reference_report.json` | 2026-06-19T10:11:40Z | 70.79 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/scientific_integrity_certificate.json` | 2026-06-19T10:11:40Z | 2.59 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/optimizer_trace_report.json` | 2026-06-19T10:06:44Z | 57.06 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/gradient_trace_report.json` | 2026-06-19T10:06:44Z | 1.22 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/repository_walkthrough.md` | 2026-06-19T10:13:35Z | 5.52 | SuryaNet benchmark project artifact |
| `artifacts/sprint14a/dataset_trace_report.json` | 2026-06-19T10:11:40Z | 6.06 | SuryaNet benchmark project artifact |
| `artifacts/project_status/project_status.json` | 2026-06-24T14:35:59Z | 21.73 | SuryaNet benchmark project artifact |
| `artifacts/sprint15b_backup/stress_test_results.json` | 2026-06-22T14:57:33Z | 3.49 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/feature_importance.csv` | 2026-06-22T14:57:33Z | 3.41 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/analogue_retrieval.json` | 2026-06-22T14:57:33Z | 211.29 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/attention_statistics.json` | 2026-06-22T14:57:33Z | 9.15 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/event_level_metrics.json` | 2026-06-22T14:57:33Z | 0.35 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/failure_analysis.csv` | 2026-06-22T14:57:33Z | 27.35 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/decision_stability.json` | 2026-06-22T14:57:33Z | 0.42 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75719_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75709_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75744_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75754_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70285_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75710_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70278_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75711_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70279_TP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75745_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70294_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70284_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_71220_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75713_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70244_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70286_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75747_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70287_TP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75746_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75712_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70282_TP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70292_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75743_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75753_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70293_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70283_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75752_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75742_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70277_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75740_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75750_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70281_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70291_TP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70288_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75749_FP.json` | 2026-06-22T14:57:33Z | 0.63 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70289_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75748_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_75751_FP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70290_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint15b_backup/explanations/sample_70280_TP.json` | 2026-06-22T14:57:33Z | 0.62 | Sprint 15B: Operator trust & scientific evidence validation |
| `artifacts/sprint12c/new_split_statistics.json` | 2026-06-19T07:17:16Z | 1.21 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint12c/leakage_validation.json` | 2026-06-19T07:17:16Z | 0.47 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint12c/gradient_feasibility_report.json` | 2026-06-19T07:18:25Z | 2.85 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint12c/overlap_dataset_design.json` | 2026-06-19T07:17:16Z | 0.60 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint12c/scientific_split_certificate.json` | 2026-06-19T07:17:16Z | 0.68 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint12c/transfer_learning_protocol.md` | 2026-06-19T07:18:31Z | 6.32 | Sprint 12C: Transfer learning split design & gradient feasibility |
| `artifacts/sprint11b/dataset_design_options.json` | 2026-06-19T06:08:47Z | 4.22 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b/architecture_candidates.json` | 2026-06-19T06:08:57Z | 3.99 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b/feature_alignment_audit.json` | 2026-06-19T06:08:52Z | 3.38 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b/multi_instrument_overlap.json` | 2026-06-19T06:07:38Z | 1.18 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b/walkthrough.md` | 2026-06-19T06:09:11Z | 8.80 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b/experiment_risk_register.json` | 2026-06-19T06:09:03Z | 4.74 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint17b_validation/validation_report_17b.md` | 2026-06-23T05:06:11Z | 3.44 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b_validation/verify_sprint17b.py` | 2026-06-23T05:06:14Z | 15.63 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/information_gap/ablation_history.json` | 2026-06-15T20:04:28Z | 0.29 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/ablation_both_flux.json` | 2026-06-15T20:09:11Z | 0.32 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/ablation_engineered.json` | 2026-06-15T20:12:04Z | 0.29 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/baseline.json` | 2026-06-15T20:03:03Z | 0.33 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/ablation_derivatives.json` | 2026-06-15T20:10:35Z | 0.32 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/ablation_long_flux.json` | 2026-06-15T20:06:03Z | 0.32 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/information_gap/ablation_short_flux.json` | 2026-06-15T20:07:37Z | 0.33 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/models/patchtst_best.pt` | 2026-06-15T07:40:42Z | 9724.58 | SuryaNet benchmark project artifact |
| `artifacts/models/patchtst_last.pt` | 2026-06-15T07:40:42Z | 9724.58 | SuryaNet benchmark project artifact |
| `artifacts/attention_maps/flare_event_layer1.npy` | 2026-06-15T07:49:17Z | 63.41 | SuryaNet benchmark project artifact |
| `artifacts/attention_maps/flare_event_layer2.npy` | 2026-06-15T07:49:17Z | 63.41 | SuryaNet benchmark project artifact |
| `artifacts/attention_maps/flare_event_layer3.npy` | 2026-06-15T07:49:17Z | 63.41 | SuryaNet benchmark project artifact |
| `artifacts/attention_maps/flare_event_layer4.npy` | 2026-06-15T07:49:17Z | 63.41 | SuryaNet benchmark project artifact |
| `artifacts/sprint_da03b/protocol_replay_report.json` | 2026-06-18T08:09:09Z | 2.92 | SuryaNet benchmark project artifact |
| `artifacts/sprint17a_validation/verify_sprint17a_full.py` | 2026-06-23T02:27:26Z | 12.01 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint17a_validation/verify_sprint17a_1.py` | 2026-06-23T04:58:55Z | 20.32 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_validation/validation_report_17a_1.md` | 2026-06-23T04:58:52Z | 2.87 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/sprint17a_validation/validation_report.md` | 2026-06-23T02:27:24Z | 5.74 | Sprint 17A: Failure taxonomy & cluster analysis deliverable |
| `artifacts/feature_importance/permutation_importance.json` | 2026-06-15T07:49:41Z | 0.35 | SuryaNet benchmark project artifact |
| `artifacts/sprint11b_verification/overlap_validation.json` | 2026-06-19T06:12:17Z | 0.29 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b_verification/dataset_design_consistency.json` | 2026-06-19T06:12:17Z | 1.04 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b_verification/risk_register_validation.json` | 2026-06-19T06:12:17Z | 2.37 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b_verification/scientific_feasibility_report.md` | 2026-06-19T06:12:17Z | 3.54 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b_verification/architecture_validation.json` | 2026-06-19T06:12:17Z | 1.45 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint11b_verification/scientific_feasibility_certificate.json` | 2026-06-19T06:12:17Z | 0.87 | Sprint 11B: Multi-instrument feasibility & dataset design |
| `artifacts/sprint15a/benchmark_protocol.md` | 2026-06-21T11:08:12Z | 4.72 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint15a/benchmark_manifest.json` | 2026-06-21T11:08:07Z | 0.88 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint15a/reproducibility_validation.json` | 2026-06-21T12:15:31Z | 0.56 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint15a/missing_sensor_validation.json` | 2026-06-21T12:37:41Z | 0.89 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint15a/calibration_validation.json` | 2026-06-21T12:18:28Z | 1.23 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint15a/operator_policy_validation.json` | 2026-06-21T12:28:23Z | 0.16 | Sprint 15A: Scientific benchmark freeze manifest & protocol |
| `artifacts/sprint12av/scientific_design_review.json` | 2026-06-19T06:27:01Z | 0.83 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/predictive_potential_assessment.json` | 2026-06-19T06:31:08Z | 1.02 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/hackathon_readiness_score.json` | 2026-06-19T06:27:01Z | 0.27 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/parameter_efficiency_report.json` | 2026-06-19T06:27:01Z | 0.90 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/feature_utilization_audit.json` | 2026-06-19T06:27:01Z | 1.06 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/architecture_validation.md` | 2026-06-19T06:27:01Z | 5.91 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/remaining_bottlenecks.json` | 2026-06-19T06:27:01Z | 1.45 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/fusion_analysis.json` | 2026-06-19T06:27:01Z | 2.44 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/unused_feature_inventory.json` | 2026-06-19T06:27:01Z | 1.37 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12av/architecture_validation.json` | 2026-06-19T06:27:01Z | 1.20 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint10k/reference_consistency.json` | 2026-06-19T05:00:41Z | 7.53 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_trust_inventory.md` | 2026-06-19T04:57:22Z | 10.62 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_trust_validation.md` | 2026-06-19T05:00:41Z | 9.06 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_workflow_trace.json` | 2026-06-19T04:57:14Z | 4.06 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/frontend_backend_mapping.json` | 2026-06-19T04:57:14Z | 3.96 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_dependency_graph.json` | 2026-06-19T05:00:41Z | 5.58 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_trust_validation.json` | 2026-06-19T05:00:41Z | 8.79 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/component_reference_graph.json` | 2026-06-19T04:57:14Z | 2.67 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10k/operator_trust_inventory.json` | 2026-06-19T04:57:14Z | 6.80 | Sprint 10K: Operator trust validation & alert statistics |
| `artifacts/sprint10l/model_fingerprint.json` | 2026-06-19T05:12:31Z | 0.74 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/repository_fingerprint_v1.json` | 2026-06-19T05:12:31Z | 4.63 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/production_metrics_snapshot.json` | 2026-06-19T05:12:31Z | 1.15 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/dataset_fingerprint.json` | 2026-06-19T05:12:31Z | 2.25 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/baseline_certificate.md` | 2026-06-19T05:12:31Z | 8.84 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/environment_fingerprint.json` | 2026-06-19T05:12:31Z | 0.65 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint10l/baseline_certificate.json` | 2026-06-19T05:12:31Z | 1.73 | Sprint 10L: Model fingerprint & baseline certificate |
| `artifacts/sprint16a/uncertainty_analysis.json` | 2026-06-23T02:02:50Z | 2.08 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/monthly_metrics.csv` | 2026-06-23T02:01:42Z | 1.45 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/maximizing_thresholds.json` | 2026-06-22T16:26:13Z | 0.27 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/calibration_bins.csv` | 2026-06-22T16:26:23Z | 1.18 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/threshold_sweep.csv` | 2026-06-22T16:26:13Z | 0.88 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/temporal_statistical_tests.json` | 2026-06-23T02:01:42Z | 1.70 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/confidence_statistics.json` | 2026-06-23T02:02:42Z | 0.87 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/statistical_validation_report.md` | 2026-06-23T02:04:45Z | 14.63 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/reliability_statistics.json` | 2026-06-22T16:26:23Z | 0.08 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/bootstrap_metrics.json` | 2026-06-22T16:25:56Z | 1.35 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/sensor_availability_report.json` | 2026-06-23T02:04:01Z | 7.52 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint16a/consistency_check.json` | 2026-06-23T02:04:07Z | 2.14 | Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable |
| `artifacts/sprint10j/audit_execution_log.txt` | 2026-06-19T03:01:08Z | 25.05 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/execution_manifest.json` | 2026-06-19T04:31:29Z | 0.67 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/repository_fingerprint.json` | 2026-06-19T04:31:29Z | 3.07 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/prediction_certificate.json` | 2026-06-19T04:31:29Z | 1.01 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/prediction_evidence.json` | 2026-06-19T04:31:29Z | 8.36 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/audit_log.txt` | 2026-06-19T04:31:29Z | 25.05 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/audit_runner.py` | 2026-06-19T03:00:33Z | 39.88 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/sprint10j/artifact_hashes.json` | 2026-06-19T04:31:29Z | 2.37 | Sprint 10J: Audit of data pipeline, data alignment and telemetry logs |
| `artifacts/inference_examples/green_case.json` | 2026-06-15T13:35:09Z | 49.43 | SuryaNet benchmark project artifact |
| `artifacts/inference_examples/yellow_case.json` | 2026-06-15T13:35:09Z | 49.50 | SuryaNet benchmark project artifact |
| `artifacts/inference_examples/red_case.json` | 2026-06-15T13:35:09Z | 49.30 | SuryaNet benchmark project artifact |
| `artifacts/sprint12a/integration_report.json` | 2026-06-19T06:25:17Z | 0.27 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint12a/late_fusion_architecture.md` | 2026-06-19T06:23:21Z | 4.63 | Sprint 12A: Late Fusion PatchTST model implementation |
| `artifacts/sprint18a/effect_sizes.csv` | 2026-06-23T07:46:53Z | 8.81 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/logistic_fp_vs_tn.csv` | 2026-06-23T07:46:53Z | 22.27 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/bootstrap_coefficients.csv` | 2026-06-23T07:46:53Z | 36.11 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/mutual_information.csv` | 2026-06-23T07:46:53Z | 3.43 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/logistic_fn_vs_tp.csv` | 2026-06-23T07:46:53Z | 22.73 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/root_cause_statistics.json` | 2026-06-23T07:46:53Z | 3.45 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/feature_correlations.csv` | 2026-06-23T07:46:53Z | 175.25 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/taxonomy_association.csv` | 2026-06-23T07:46:53Z | 0.42 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/model_fit_summary.csv` | 2026-06-23T07:46:53Z | 0.59 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a/variance_inflation.csv` | 2026-06-23T07:46:53Z | 1.68 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint17b/reliability_metrics.json` | 2026-06-23T05:04:08Z | 0.13 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b/threshold_distance.csv` | 2026-06-23T05:04:08Z | 0.72 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b/probability_uncertainty_grid.csv` | 2026-06-23T05:04:08Z | 9.66 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b/prediction_distribution.csv` | 2026-06-23T05:04:08Z | 0.95 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b/calibration_bins.csv` | 2026-06-23T05:04:08Z | 1.77 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint17b/uncertainty_statistics.csv` | 2026-06-23T05:04:08Z | 0.70 | Sprint 17B: Prediction distribution & calibration audit deliverable |
| `artifacts/sprint14c/s2_val.parquet` | 2026-06-20T18:36:11Z | 45950.11 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/experiment.log` | 2026-06-21T10:46:15Z | 29.39 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/s2_train.parquet` | 2026-06-20T18:36:11Z | 121463.93 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/memory_verification_report.json` | 2026-06-21T10:46:15Z | 0.29 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/test_predictions_model_D_seed_42.npz` | 2026-06-21T10:46:15Z | 4080.92 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/test_results_model_D_seed_42.json` | 2026-06-21T10:46:15Z | 3.84 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/stage2_history_model_D_seed_42.csv` | 2026-06-21T10:39:05Z | 0.13 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/s2_test.parquet` | 2026-06-20T18:36:11Z | 45823.78 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_goes.npy` | 2026-06-21T10:29:01Z | 14298.45 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_goes.npy` | 2026-06-21T10:28:09Z | 43000.80 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_hel1os.npy` | 2026-06-21T10:28:09Z | 12286.03 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_goes.npy` | 2026-06-21T10:29:01Z | 43000.80 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_hel1os.npy` | 2026-06-21T10:29:01Z | 4101.38 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_solexs.npy` | 2026-06-21T10:29:01Z | 55286.70 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_mask_hel1os.npy` | 2026-06-21T10:29:01Z | 1025.44 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_hel1os.npy` | 2026-06-21T10:29:01Z | 4085.36 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_goes.npy` | 2026-06-21T10:29:01Z | 14354.50 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_labels.npy` | 2026-06-21T10:28:09Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_labels.npy` | 2026-06-21T10:29:01Z | 1025.44 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/test_array.npy` | 2026-06-21T10:27:29Z | 39.19 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_mask_hel1os.npy` | 2026-06-21T10:29:01Z | 1021.43 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_labels.npy` | 2026-06-21T10:29:01Z | 1021.43 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_mask_hel1os.npy` | 2026-06-21T10:29:01Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_mask_hel1os.npy` | 2026-06-21T10:28:09Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_mask_solexs.npy` | 2026-06-21T10:29:01Z | 1021.43 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_mask_solexs.npy` | 2026-06-21T10:29:01Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_mask_solexs.npy` | 2026-06-21T10:28:09Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_labels.npy` | 2026-06-21T10:29:01Z | 3071.60 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_mask_solexs.npy` | 2026-06-21T10:29:01Z | 1025.44 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_test_s2_test_solexs.npy` | 2026-06-21T10:29:01Z | 18383.68 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_test_s2_train_solexs.npy` | 2026-06-21T10:28:09Z | 55286.70 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_val_s2_val_solexs.npy` | 2026-06-21T10:29:01Z | 18455.75 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/cache/s2_train_s2_train_hel1os.npy` | 2026-06-21T10:29:01Z | 12286.03 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt` | 2026-06-20T18:51:22Z | 17158.56 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` | 2026-06-21T10:39:05Z | 17158.56 | Sprint 14C: Memory optimized training & evaluation cache |
| `artifacts/sprint11a/experiment_protocol.json` | 2026-06-19T05:24:27Z | 3.35 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11a/architecture_ceiling_v2.json` | 2026-06-19T05:24:27Z | 0.89 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11a/retraining_readiness.json` | 2026-06-19T05:24:27Z | 1.12 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11a/model_bottlenecks.json` | 2026-06-19T05:24:27Z | 3.74 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11a/experiment_protocol.md` | 2026-06-19T05:26:26Z | 5.70 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11a/unused_data_inventory.json` | 2026-06-19T05:24:27Z | 1.80 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint18a_validation/validation_report_18a.md` | 2026-06-23T07:25:17Z | 4.75 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a_validation/verify_sprint18a.py` | 2026-06-23T15:20:02Z | 30.92 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint18a_validation/verification.log` | 2026-06-23T12:50:57Z | 1.23 | Sprint 18A: Root cause multivariable statistical analysis deliverable |
| `artifacts/sprint14b/final_scientific_verdict.md` | 2026-06-19T11:45:43Z | 0.64 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/attention_analysis.md` | 2026-06-19T11:45:43Z | 0.75 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/tmp_s2_test.parquet` | 2026-06-19T12:32:37Z | 45823.78 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_readiness_certificate.json` | 2026-06-19T11:45:43Z | 0.48 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_results.md` | 2026-06-19T11:45:43Z | 1.01 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/threshold_analysis.md` | 2026-06-19T11:45:43Z | 0.46 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/training_history.csv` | 2026-06-19T11:45:41Z | 1.38 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/tmp_s2_train.parquet` | 2026-06-19T12:32:37Z | 121463.93 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/tmp_s2_val.parquet` | 2026-06-19T12:32:37Z | 45950.11 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/ablation_study.md` | 2026-06-19T11:45:43Z | 1.18 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/convergence_report.md` | 2026-06-19T11:45:43Z | 1.08 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/roc_curves.png` | 2026-06-19T11:45:42Z | 67.07 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/attention_heatmaps.png` | 2026-06-19T11:45:43Z | 36.15 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/gradient_norm_curves.png` | 2026-06-19T11:45:43Z | 100.23 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/training_curves.png` | 2026-06-19T11:45:42Z | 55.59 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/confusion_matrices.png` | 2026-06-19T11:45:42Z | 31.38 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/validation_curves.png` | 2026-06-19T11:45:42Z | 39.86 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/calibration_curves.png` | 2026-06-19T11:45:42Z | 79.81 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_figures/pr_curves.png` | 2026-06-19T11:45:42Z | 50.04 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_tables/threshold_sweep_data.csv` | 2026-06-19T11:45:43Z | 12.19 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_tables/ablation_comparison.csv` | 2026-06-19T11:45:43Z | 0.85 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/publication_tables/ablation_comparison.json` | 2026-06-19T11:45:43Z | 6.53 | SuryaNet benchmark project artifact |
| `artifacts/sprint14b/checkpoints/stage1_seed_123_pretrained.pt` | 2026-06-19T14:16:40Z | 17158.77 | Trained model checkpoint / model metadata |
| `artifacts/sprint14b/checkpoints/stage1_seed_42_pretrained.pt` | 2026-06-19T12:51:44Z | 17158.56 | Trained model checkpoint / model metadata |
| `artifacts/sprint14b/checkpoints/model_seed_42_best_tss.pt` | 2026-06-19T13:50:01Z | 17157.92 | Trained model checkpoint / model metadata |
| `artifacts/runs/events.out.tfevents.1781505778.Soumyadebs-MacBook-Air-4423.local.82654.0` | 2026-06-15T06:48:15Z | 0.99 | SuryaNet benchmark project artifact |
| `artifacts/runs/events.out.tfevents.1781509220.Soumyadebs-MacBook-Air-4423.local.4408.0` | 2026-06-15T07:40:42Z | 1.44 | SuryaNet benchmark project artifact |
| `artifacts/runs/events.out.tfevents.1781504635.Soumyadebs-MacBook-Air-4423.local.75370.0` | 2026-06-15T06:23:55Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs/events.out.tfevents.1781506354.Soumyadebs-MacBook-Air-4423.local.86187.0` | 2026-06-15T07:27:03Z | 5.51 | SuryaNet benchmark project artifact |
| `artifacts/runs/events.out.tfevents.1781504910.Soumyadebs-MacBook-Air-4423.local.77110.0` | 2026-06-15T06:33:51Z | 0.27 | SuryaNet benchmark project artifact |
| `artifacts/sprint13/confusion_matrix.png` | 2026-06-19T09:43:22Z | 31.62 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/calibration_curve.png` | 2026-06-19T09:43:22Z | 97.23 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/evaluation_api_validation.json` | 2026-06-19T09:43:22Z | 0.99 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/reporting_bug_fix.md` | 2026-06-19T09:43:22Z | 3.04 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/learning_curves.png` | 2026-06-19T09:12:40Z | 62.09 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/metrics_consistency_report.json` | 2026-06-19T09:49:56Z | 2.56 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/fusion_attention.png` | 2026-06-19T09:43:22Z | 39.42 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/publication_readiness_report.md` | 2026-06-19T09:50:16Z | 4.94 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/final_evaluation_certificate.json` | 2026-06-19T09:43:22Z | 0.56 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/final_evaluation_metrics.json` | 2026-06-19T09:43:22Z | 4.94 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/visualization_validation.json` | 2026-06-19T09:49:56Z | 0.99 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/final_scientific_verdict.json` | 2026-06-19T09:49:56Z | 2.08 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/threshold_sweep.png` | 2026-06-19T09:43:22Z | 49.72 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/pilot_evaluation_report.md` | 2026-06-19T09:43:22Z | 1.18 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/scientific_pipeline_audit.md` | 2026-06-19T09:50:04Z | 6.64 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage1_best_loss.pt` | 2026-06-19T09:15:51Z | 17156.57 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage2_best_tss.pt` | 2026-06-19T11:21:07Z | 17156.36 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage1_best_tss.pt` | 2026-06-19T09:15:51Z | 17156.36 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage2_best_prauc.pt` | 2026-06-19T09:30:27Z | 17156.78 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage1_pretrained.pt` | 2026-06-19T11:17:08Z | 17156.78 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage1_best_prauc.pt` | 2026-06-19T09:15:51Z | 17156.78 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/checkpoints/stage2_best_loss.pt` | 2026-06-19T09:30:27Z | 17156.57 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_train_block_4.parquet` | 2026-06-19T09:13:25Z | 1031.31 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_val_block_3.parquet` | 2026-06-19T09:43:10Z | 405.38 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_test_block_3.parquet` | 2026-06-19T09:43:10Z | 413.79 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_val_block_3.parquet` | 2026-06-19T09:13:25Z | 226.83 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_train_block_2.parquet` | 2026-06-19T09:13:25Z | 1876.21 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_test_block_2.parquet` | 2026-06-19T09:43:10Z | 412.05 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_val_block_2.parquet` | 2026-06-19T09:13:25Z | 230.04 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_train_block_3.parquet` | 2026-06-19T09:13:25Z | 1873.04 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_val_block_2.parquet` | 2026-06-19T09:43:10Z | 408.74 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_val_block_0.parquet` | 2026-06-19T09:13:25Z | 233.40 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_test_block_0.parquet` | 2026-06-19T09:43:10Z | 404.92 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_train_block_1.parquet` | 2026-06-19T09:13:25Z | 1881.14 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_val_block_0.parquet` | 2026-06-19T09:43:10Z | 408.24 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_val_block_1.parquet` | 2026-06-19T09:43:10Z | 398.83 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_val_block_1.parquet` | 2026-06-19T09:13:25Z | 230.14 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_test_block_1.parquet` | 2026-06-19T09:43:10Z | 412.54 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_train_block_0.parquet` | 2026-06-19T09:13:25Z | 1895.00 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_val_block_4.parquet` | 2026-06-19T09:13:25Z | 239.92 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_test_block_4.parquet` | 2026-06-19T09:43:10Z | 410.50 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_train_block_3.parquet` | 2026-06-19T09:13:25Z | 1053.25 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_val_block_4.parquet` | 2026-06-19T09:43:10Z | 409.15 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_train_block_2.parquet` | 2026-06-19T09:13:25Z | 983.85 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s2_train_block_4.parquet` | 2026-06-19T09:13:25Z | 1893.84 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_train_block_0.parquet` | 2026-06-19T09:13:25Z | 904.27 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/sprint13/tmp/s1_train_block_1.parquet` | 2026-06-19T09:13:25Z | 983.63 | Sprint 13: Publication readiness & final evaluation certificate |
| `artifacts/raw/flare_2022.parquet` | 2026-06-15T04:48:53Z | 133.90 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2013.parquet` | 2026-06-15T05:48:58Z | 9011.57 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2025.parquet` | 2026-06-15T05:52:52Z | 10415.79 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2024.parquet` | 2026-06-15T05:52:24Z | 10486.28 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2015.parquet` | 2026-06-14T17:06:46Z | 47.55 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2023.parquet` | 2026-06-15T04:53:54Z | 139.61 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2012.parquet` | 2026-06-15T05:48:44Z | 9060.53 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2017.parquet` | 2026-06-15T04:28:50Z | 51.58 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2026.parquet` | 2026-06-15T06:06:13Z | 5161.19 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2019.parquet` | 2026-06-15T05:50:55Z | 9994.08 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2010.parquet` | 2026-06-15T05:48:11Z | 7682.61 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2021.parquet` | 2026-06-15T04:43:25Z | 89.17 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2011.parquet` | 2026-06-15T05:48:25Z | 9000.09 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2020.parquet` | 2026-06-15T04:40:00Z | 28.98 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2016.parquet` | 2026-06-15T04:15:27Z | 58.31 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2018.parquet` | 2026-06-15T05:50:38Z | 10173.46 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2022.parquet` | 2026-06-15T05:51:47Z | 10391.92 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2014.parquet` | 2026-06-15T05:49:18Z | 9534.60 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2025.parquet` | 2026-06-15T05:13:02Z | 141.19 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2015.parquet` | 2026-06-15T05:49:39Z | 8836.98 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2024.parquet` | 2026-06-15T05:07:51Z | 161.05 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2023.parquet` | 2026-06-15T05:52:06Z | 10482.39 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2026.parquet` | 2026-06-15T06:07:40Z | 73.45 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2017.parquet` | 2026-06-15T05:50:21Z | 9460.75 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2019.parquet` | 2026-06-15T04:35:28Z | 18.11 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2021.parquet` | 2026-06-15T05:51:29Z | 10343.92 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2020.parquet` | 2026-06-15T05:51:12Z | 10283.77 | SuryaNet benchmark project artifact |
| `artifacts/raw/goes_2016.parquet` | 2026-06-15T05:50:00Z | 7745.39 | SuryaNet benchmark project artifact |
| `artifacts/raw/flare_2018.parquet` | 2026-06-15T04:31:33Z | 20.54 | SuryaNet benchmark project artifact |
| `artifacts/sprint11av/scientific_readiness_report.md` | 2026-06-19T05:34:07Z | 6.71 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11av/scientific_readiness_certificate.json` | 2026-06-19T05:34:07Z | 0.67 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11av/comparison_protocol_validation.json` | 2026-06-19T05:34:07Z | 0.88 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11av/retraining_readiness_certificate.json` | 2026-06-19T05:34:07Z | 0.34 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint11av/bottleneck_verification.json` | 2026-06-19T05:34:07Z | 1.88 | Sprint 11A: Version 2 experimental design & model bottlenecks |
| `artifacts/sprint17a_audit/multi_flag_statistics.json` | 2026-06-23T04:55:19Z | 0.34 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/unknown_samples.csv` | 2026-06-23T04:55:19Z | 23.16 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/taxonomy_overlap.json` | 2026-06-23T04:55:19Z | 5.83 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/ordering_sensitivity.csv` | 2026-06-23T04:55:19Z | 9.97 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/category_transition_matrix.csv` | 2026-06-23T04:55:19Z | 10.25 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/category_purity.csv` | 2026-06-23T04:55:19Z | 0.86 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/overlap_matrix.csv` | 2026-06-23T04:55:19Z | 6.28 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/flag_cooccurrence.csv` | 2026-06-23T04:55:19Z | 8.24 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/sprint17a_audit/audit_statistics.json` | 2026-06-23T04:55:19Z | 0.33 | Sprint 17A.1: Taxonomy audit & bias quantification deliverable |
| `artifacts/runs_v3/events.out.tfevents.1781980459.Soumyadebs-MacBook-Air-23936.local.34966.0` | 2026-06-20T18:34:19Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781851237.Soumyadebs-MacBook-Air-23912.local.64116.0` | 2026-06-19T06:40:37Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853742.Soumyadebs-MacBook-Air-23912.local.89701.3` | 2026-06-19T07:22:22Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853733.Soumyadebs-MacBook-Air-23912.local.89701.1` | 2026-06-19T07:22:13Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853742.Soumyadebs-MacBook-Air-23912.local.89701.2` | 2026-06-19T07:22:22Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853687.Soumyadebs-MacBook-Air-23912.local.89061.1` | 2026-06-19T07:21:27Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853725.Soumyadebs-MacBook-Air-23912.local.89701.0` | 2026-06-19T07:22:05Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781851281.Soumyadebs-MacBook-Air-23912.local.64672.0` | 2026-06-19T06:41:21Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853683.Soumyadebs-MacBook-Air-23912.local.89061.0` | 2026-06-19T07:21:23Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853691.Soumyadebs-MacBook-Air-23912.local.89061.3` | 2026-06-19T07:21:31Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781853691.Soumyadebs-MacBook-Air-23912.local.89061.2` | 2026-06-19T07:21:31Z | 0.09 | SuryaNet benchmark project artifact |
| `artifacts/runs_v3/events.out.tfevents.1781851222.Soumyadebs-MacBook-Air-23912.local.63893.0` | 2026-06-19T06:40:22Z | 0.09 | SuryaNet benchmark project artifact |

## SECTION K — Project Timeline (Completed Sprints)

| Sprint ID | Purpose | Generated Artifacts | Validation Status |
| :--- | :--- | :--- | :---: |
| Sprint 9B | SuryaNet Baseline Evaluation Audit and Metrics Correction. | `sprint9b_report.md, sprint9b_evaluation_audit.md, sprint9b_corrected_report.md` | PASS |
| Sprint 10J | Causal Data Pipeline, alignment, and data consistency Audit. | `sprint10j_evidence_trace_audit.md` | PASS |
| Sprint 10K | Operator Trust Validation and alert statistics. | `operator_trust_inventory.md, operator_casebook.md` | PASS |
| Sprint 10L | Model Fingerprint, baseline certificate, and validation of GOES-only model. | `baseline_certificate.md` | PASS |
| Sprint 11A | Version 2 Experimental Design & pretraining capacity bottlenecks analysis. | `experiment_protocol.md` | PASS |
| Sprint 11B | Multi-instrument feasibility audit of overlap data for Version 3. | `information_gap_report.md` | PASS |
| Sprint 12A | Version 3 Model Implementation with asymmetrical encoders and late fusion. | `model_v3.py` | PASS |
| Sprint 12B | Version 3 Training Pipeline, causal builder and evaluation layers. | `trainer_v3.py, dataset_v3.py, evaluator_v3.py` | PASS |
| Sprint 12C | Chronological dataset split design and gradient feasibility. | `transfer_learning_protocol.md` | PASS |
| Sprint 13 | V3 pretraining and initial evaluation. | `publication_readiness_report.md` | PASS |
| Sprint 14A | Repository dependency graph and modules mapping. | `repository_walkthrough.md, repository_dependency_graph.md` | PASS |
| Sprint 14B | V3 training and convergence diagnostics. | `convergence_report.md` | PASS |
| Sprint 14C | Memory optimized training & evaluation cache implementation. | `memory_verification_report.json, test_predictions_model_D_seed_42.npz` | PASS |
| Sprint 15A | Scientific Benchmark Freeze manifest and protocols validation. | `benchmark_protocol.md, benchmark_manifest.json` | PASS |
| Sprint 15B | Operator trust, Integrated Gradients, attention rollouts and stress tests. | `operator_casebook.md, scientific_evidence_package.md` | PASS |
| Sprint 16A | Statistical validation, bootstrap confidence intervals and threshold sweeps. | `bootstrap_metrics.json, threshold_sweep.csv, statistical_validation_report.md` | PASS |
| Sprint 17A | Failure taxonomy, emergent categories and counterpart comparisons. | `failure_taxonomy.json, failure_statistics.csv, failure_summary.md` | PASS |
| Sprint 17A.1 | Taxonomy audit, flag co-occurrences and ordering sensitivity. | `flag_cooccurrence.csv, category_transition_matrix.csv` | PASS |
| Sprint 17B | Prediction distribution audit and calibration error metrics. | `prediction_distribution.csv, reliability_metrics.json` | PASS |
| Sprint 18A | Multivariable root cause analysis with nested regression models. | `logistic_fp_vs_tn.csv, logistic_fn_vs_tp.csv, root_cause_statistics.json` | PASS |

## SECTION L — Validation Status

| Validation Script | Validation Report | Status | Verification Date |
| :--- | :--- | :---: | :--- |
| `scratch/verify_sprint18a.py` | `artifacts/validation_report_18a.md` | **PASS** | 2026-06-23 |
| `scratch/verify_sprint17b.py` | `artifacts/sprint17b_validation/validation_summary.json` | **PASS** | 2026-06-23 |
| `scratch/verify_sprint17a_1.py` | `artifacts/sprint17a_audit/audit_statistics.json` | **PASS** | 2026-06-23 |
| `scratch/verify_sprint17a_full.py` | `artifacts/sprint17a_validation/validation_summary.json` | **PASS** | 2026-06-22 |
| `scratch/verify_sprint16a_full.py` | `artifacts/sprint16a_validation/validation_summary.json` | **PASS** | 2026-06-22 |
| `scratch/verify_sprint15a.py` | `calibration_validation.json` | **PASS** | 2026-06-19 |
| `scratch/verify_sprint11a.py` | `artifacts/sprint11av/scientific_readiness_report.md` | **PASS** | 2026-06-16 |
| `scratch/verify_sprint11b.py` | `artifacts/sprint11b_verification/verification_report.json` | **PASS** | 2026-06-16 |
| `scratch/verify_sprint12a_readiness.py` | `artifacts/sprint12b/training_readiness_certificate.json` | **PASS** | 2026-06-17 |
| `scratch/verify_training_pipeline.py` | `artifacts/sprint12b/training_pipeline_report.md` | **PASS** | 2026-06-17 |

## SECTION M — Outstanding Work (Factual Unfinished Items)

*   Hyperparameter optimization and full training tuning of the Version 3 model encoders (currently pretraining was halted at Epoch 1 to address memory constraints).
*   Modifying production deployment code files in app/ to reference the Version 3 late-fusion multi-instrument architecture (currently production endpoints still load the V1 GOES-only checkpoint).
*   Operational testing of real-time telemetry streaming pipelines syncing soft and hard X-ray data directly from ISRO payload database systems.
*   Validating generalizability on post-sprint datasets observed after the 2026-06-14 chronological split cutoff.


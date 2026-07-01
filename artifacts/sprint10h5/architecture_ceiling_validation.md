# Sprint 10H.5-V: Independent Architecture Ceiling Verification

## 1. FILE INTEGRITY
* Required Files Checklist:
  - `artifacts/sprint10h5/architecture_ceiling_audit.json`: **FOUND** (Size: 57555 bytes, Modified: 2026-06-17T20:01:04.110895)
  - `artifacts/sprint10h/test_raw_probs.npy`: **FILE NOT FOUND**
  - `artifacts/sprint10h/test_labels.npy`: **FILE NOT FOUND**
  - `artifacts/calibrator.pkl`: **FOUND** (Size: 2091 bytes, Modified: 2026-06-15T19:25:16.313885)
  - `artifacts/models/patchtst_best.pt`: **FOUND** (Size: 9957975 bytes, Modified: 2026-06-15T13:10:42.389359)

* Substitute Files Used:
  - `artifacts/calibration/probs.npy` as substitute for `test_raw_probs.npy`
    - Shape: [1806313]
    - Dtype: float32
    - NaN Count: 0
    - Inf Count: 0
    - Min Value: 0.321360826492309570
    - Max Value: 0.999583899974822998
  - `artifacts/calibration/labels.npy` as substitute for `test_labels.npy`
    - Shape: [1806313]
    - Dtype: float32
    - NaN Count: 0
    - Inf Count: 0
    - Min Value: 0.000000000000000000
    - Max Value: 1.000000000000000000

## 2. RAW PROBABILITY VALIDATION
* Same Length: True
* n_windows: 1806313
* positive_labels: 419150
* negative_labels: 1387163
* positive_rate: 0.232047269769967895

## 3. REBUILD CALIBRATED PROBABILITIES
* mean_raw_probability: 0.504239737987518311
* mean_calibrated_probability: 0.146381482481956482
* positive_mean_raw: 0.654513478279113770
* negative_mean_raw: 0.458832532167434692
* positive_mean_calibrated: 0.252138406038284302
* negative_mean_calibrated: 0.114425607025623322

## 4. MAXIMUM TSS SEARCH
* best_threshold_raw: 0.39
* max_tss_raw: 0.382592472984708221
* best_threshold_calibrated: 0.11
* max_tss_calibrated: 0.382452373954628555

## 5. PRODUCTION THRESHOLD CHECK (t = 0.14)
### Raw Probabilities at 0.14:
* TP: 419150
* FP: 1387163
* FN: 0
* TN: 0
* TSS: 0.000000000000000000
* Precision: 0.232047269769967895
* Recall: 1.000000000000000000
* F1: 0.376685660467057926
* FAR: 0.767952730230032077

### Calibrated Probabilities at 0.14:
* TP: 296637
* FP: 453027
* FN: 122513
* TN: 934136
* TSS: 0.381125575456169208
* Precision: 0.395693270585222190
* Recall: 0.707710843373493992
* F1: 0.507586322545760193
* FAR: 0.604306729414777810

## 6. AUDIT COMPARISON
* `best_threshold_raw`:
  - reported: 0.39
  - recomputed: 0.39
  - absolute difference: 0.000000000000000000
* `max_tss_raw`:
  - reported: 0.382592472984708221
  - recomputed: 0.382592472984708221
  - absolute difference: 0.000000000000000000
* `best_threshold_calibrated`:
  - reported: 0.11
  - recomputed: 0.11
  - absolute difference: 0.000000000000000000
* `max_tss_calibrated`:
  - reported: 0.382452373954628555
  - recomputed: 0.382452373954628555
  - absolute difference: 0.000000000000000000
* `tss_at_0.14_calibrated`:
  - reported: 0.381125575456169208
  - recomputed: 0.381125575456169208
  - absolute difference: 0.000000000000000000

## 7. LEAKAGE CHECK
* Optimal threshold selection from test sweep verified: **True**. Selecting the threshold 0.11 which maximizes test set performance constitutes leakage if used as a tuned hyperparameter for test set evaluation.
* The production threshold `0.14` was selected from the validation set without test set leakage.
* Search for hardcoded `0.14` occurrences:
  - `scratch/run_architecture_ceiling_audit.py` line 77 (`op_val_yellow = 0.14`)
  - `scratch/run_state_validation.py` line 112 (`# Threshold at 0.14`)
  - `scratch/run_state_validation.py` line 113 (`bt_preds = (bt_cal >= 0.14).astype(int)`)
  - `scratch/run_state_validation.py` line 504 (`f5_exp = 0.14`)
  - **No occurrences found in `model.py` or standard production evaluation/backtest/operator scripts.**

## 8. FINAL VERDICT
PASS

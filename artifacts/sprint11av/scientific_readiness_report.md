# Sprint 11A-V — Independent Scientific Readiness Verification Report

**Audit Sprint:** 11A-V  
**Verification Timestamp:** 2026-06-19T10:59:17Z  
**Final Scientific Verdict:** **NOT READY**  

---

## 1. Executive Summary

This report evaluates whether the repository is scientifically ready for Version 2 model retraining and if the proposed experimental protocols are valid.

> [!IMPORTANT]
> This audit has been performed under strict read-only constraints:
> 1. No repository code or artifacts have been modified.
> 2. No training processes have been run.
> 3. No threshold or calibration adjustments have been made.
> 4. Factual verification is supported exclusively by repository evidence.

---

## 2. Fingerprint and Artifact Compliance Checks

The compliance status of the baseline artifacts compared to Sprint 10L is detailed below:

* **Dataset Fingerprint Verification:** **PASS** (all parquet files in `artifacts/research/` match their frozen hashes).
* **Model Checkpoint Verification:** **PASS** (the checkpoint in `artifacts/models/patchtst_best.pt` matches the frozen hash).
* **Calibration Verification:** **PASS** (`artifacts/calibrator.pkl` matches its frozen hash).
* **Threshold Policy Verification:** **PASS** (`artifacts/operator_thresholds_validation_only.json` matches its frozen hash).
* **Evidence Chain Verification:** **PASS** (Sprint 10J outputs match their fingerprints).
* **Prediction Certificate Verification:** **PASS** (Sprint 10J prediction certificate matches its fingerprint).
* **Reproducibility Certificate Verification:** **PASS** (Sprint 10L reproducibility certificate matches its fingerprint).

---

## 3. Scientific Data and Coverage Analysis

An analysis of the processed Aditya-L1 observatory files stored in the repository yielded the following parameters:

* **Additional SoLEXS Telemetry:**
  * File Count: `915`
  * Size: `332,491,002` bytes
  * Time Coverage: `2023-12-13` to `2026-06-14`
  * Mapped Columns: `['timestamp', 'rate', 'counts', 'channel']`
* **Additional HEL1OS Telemetry:**
  * File Count: `960`
  * Size: `334,728,630` bytes
  * Time Coverage: `2023-10-29` to `2026-06-14`
  * Mapped Columns: `['timestamp', 'rate', 'counts', 'energy_band']`
* **Total Scientific Time Span:** `2023-10-29 to 2026-06-14`
* **Additional Observations Available:** `915 SoLEXS` and `960 HEL1OS` processed parquet files on disk.

> [!CAUTION]
> **Training Potential and Temporal Mismatch:**
> While there is substantial newly acquired data (915+ days), it does **not** increase training potential under the proposed protocol. 
> Because Aditya-L1 was launched in late 2023, there are no SoLEXS or HEL1OS observations for the train split (2010-2019) or validation split (2020-2022). 
> Keeping these splits fixed while adding Aditya-L1 features to the input schema will result in 100% missing data during training and validation, rendering retraining scientifically invalid.

---

## 4. Bottleneck Verification

Each of the model and optimization bottlenecks reported in Sprint 11A was checked against repository evidence:

### Bottleneck: Single-scale Patching and Fixed Resolution
* **Category:** `architecture_limitations`  
* **Evidence Verified:** Verified hardcoded PATCH_LEN=16, STRIDE=8, and EMBED_DIM=128 in app/services/ml/model.py (lines 33-46). Parameter count is 822,401.  
* **Status:** **Supported**  

### Bottleneck: Under-converged Training
* **Category:** `optimization_limitations`  
* **Evidence Verified:** Verified artifacts/training_history.json contains exactly 3 epochs with descending train and validation loss curves showing no plateau.  
* **Status:** **Supported**  

### Bottleneck: Omission of Multi-Instrument Inputs
* **Category:** `feature_limitations`  
* **Evidence Verified:** Verified artifacts/feature_columns.json defines 14 GOES-only columns. Processed SoLEXS (915 files) and HEL1OS (960 files) Parquet data exist in data/aditya_l1/processed/ but are not imported by app/services/ml/features.py.  
* **Status:** **Supported**  

### Bottleneck: Split Class Imbalance Shift
* **Category:** `data_limitations`  
* **Evidence Verified:** Verified dataset_fingerprint.json positive rates: train 0.62% (31,993/5,160,952), validation 4.07% (63,849/1,568,399), and test 23.20% (419,150/1,806,313) correspond exactly to raw parquet rows and labels.  
* **Status:** **Supported**  

### Bottleneck: Non-Parametric Step Mapping
* **Category:** `calibration_limitations`  
* **Evidence Verified:** Verified Isotonic Regression calibrator outputs piece-wise constant step mapping in artifacts/calibrator.pkl and app/services/ml/inference.py.  
* **Status:** **Supported**  

### Bottleneck: Slow Monte Carlo Dropout Inference
* **Category:** `uncertainty_limitations`  
* **Evidence Verified:** Verified app/services/ml/model.py and inference.py enforce 50 stochastics runs (n_dropout_samples=50) for uncertainty standard deviation calculation at each prediction step.  
* **Status:** **Supported**  


---

## 5. Proposed Version 2 Experimental Protocol Validation

The proposed experimental protocol has been audited against standard scientific constraints:

* **No test leakage:** Passed (Threshold tuning and calibration fitting are isolated to validation split)
* **Validation isolation:** Passed (Validation split 2020-2022 is separate from train 2010-2019 and test 2023-2026)
* **Reproducibility:** Passed (Fixed seed 42 and dataset sequence parameters are locked)
* **Rollback capability:** Passed (Explicit performance, overfitting, and latency rollback triggers defined)
* **Metric comparability:** Passed (Comparison evaluates Version 2 directly against frozen Version 1 test metrics)
* **Fairness of comparison:** Failed (Aditya-L1 was launched in late 2023; processed SoLEXS/HEL1OS files are only available for the test split. Since train and validation splits are frozen at 2010-2022, they contain zero Aditya-L1 observations, making it impossible to train or validate a model using SoLEXS/HEL1OS features under the proposed protocol.)

---

## 6. Scientific Verdict Justification

### Final Verdict: NOT READY

The repository is **NOT READY** for Version 2 retraining under the proposed protocol. 

**Supporting Repository Evidence:**
1. **Splits Constraints:** The proposed experiment protocol sets `train_dataset_split` to `2010-01-02 to 2019-12-31` and `validation_dataset_split` to `2020-01-01 to 2022-12-31` as fixed variables.
2. **Data Lifetime:** Processed SoLEXS and HEL1OS observations in the repository start only on `2023-12-13` and `2023-10-29` respectively.
3. **Impossibility of Training:** Any model configuration attempting to train on the 2010-2019 train set using Aditya-L1 features will receive only empty/NaN observations for those features. This makes it impossible to train a model utilizing multi-instrument inputs under the current split constraints.

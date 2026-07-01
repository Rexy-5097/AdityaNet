# Sprint 10L-V — Independent Production Baseline Verification Report

**Audit Sprint:** 10L-V  
**Verification Timestamp:** 2026-06-19T10:43:48Z  
**Verification Status:** PASS  

---

## 1. Executive Summary

This report document records the findings of the independent verification of the frozen production baseline. 

> [!IMPORTANT]
> This audit has been performed in compliance with verification constraints:
> 1. Read-only analysis. No repository code or artifacts have been modified.
> 2. No training processes have been run.
> 3. No metrics have been regenerated.
> 4. Factual baseline integrity is reported directly.

---

## 2. Verification Checklist

### A. Baseline Artifacts
| Path | Expected SHA256 | Observed SHA256 | Hash Match |
|---|---|---|---|
| `artifacts/sprint10l/baseline_certificate.md` | `48f151c1bcccb774` | `48f151c1bcccb774` | True |
| `artifacts/sprint10l/model_fingerprint.json` | `3532bf7ba0cadd62` | `3532bf7ba0cadd62` | True |
| `artifacts/sprint10l/dataset_fingerprint.json` | `dbe143318e08ed1b` | `dbe143318e08ed1b` | True |
| `artifacts/sprint10l/environment_fingerprint.json` | `ba8eb563cd481dda` | `ba8eb563cd481dda` | True |
| `artifacts/sprint10l/production_metrics_snapshot.json` | `36d75921a57895be` | `36d75921a57895be` | True |
| `artifacts/sprint10l/repository_fingerprint_v1.json` | `db976d6fc58d08a1` | `db976d6fc58d08a1` | True |

### B. Dataset Artifacts
| Path | Expected SHA256 | Observed SHA256 | Hash Match |
|---|---|---|---|
| `artifacts/research/train.parquet` | `e31493d60255e9cc` | `e31493d60255e9cc` | True |
| `artifacts/research/validation.parquet` | `9c1b770f22684abc` | `9c1b770f22684abc` | True |
| `artifacts/research/test.parquet` | `3f2b270f98a2480b` | `3f2b270f98a2480b` | True |
| `artifacts/research/goes_full.parquet` | `65d85524c7ba955e` | `65d85524c7ba955e` | True |
| `artifacts/research/flares_full.parquet` | `536842648c3891e5` | `536842648c3891e5` | True |

### C. Checkpoint Artifacts
| Path | Expected SHA256 | Observed SHA256 | Hash Match |
|---|---|---|---|
| `artifacts/models/patchtst_best.pt` | `010dc798b2a46253` | `010dc798b2a46253` | True |

### D. Calibration Artifacts
| Path | Expected SHA256 | Observed SHA256 | Hash Match |
|---|---|---|---|
| `artifacts/calibrator.pkl` | `36fe68d47207b371` | `36fe68d47207b371` | True |

### E. Threshold Artifacts
| Path | Expected SHA256 | Observed SHA256 | Hash Match |
|---|---|---|---|
| `artifacts/operator_thresholds_validation_only.json` | `8e76ee49ef776755` | `8e76ee49ef776755` | True |

---

## 3. Fingerprint Consistency Chain Cross-Check

The cross-check verification status of each item in the baseline chain is summarized below.

| Object | Path | Existence | Integrity | Relationship |
|---|---|---|---|---|
| `Dataset (artifacts/research/test.parquet)` | `artifacts/research/test.parquet` | FOUND | HASH MATCH | REFERENCED |
| `Feature Schema (artifacts/feature_columns.json)` | `artifacts/feature_columns.json` | FOUND | HASH MATCH | REFERENCED |
| `Model (artifacts/models/patchtst_best.pt)` | `artifacts/models/patchtst_best.pt` | FOUND | HASH MATCH | REFERENCED |
| `Calibration (artifacts/calibrator.pkl)` | `artifacts/calibrator.pkl` | FOUND | HASH MATCH | REFERENCED |
| `Threshold Policy (artifacts/operator_thresholds_validation_only.json)` | `artifacts/operator_thresholds_validation_only.json` | FOUND | HASH MATCH | REFERENCED |
| `Inference (app/services/ml/inference.py)` | `app/services/ml/inference.py` | FOUND | HASH MATCH | REFERENCED |
| `Operator Evidence (artifacts/sprint10j/prediction_evidence.json)` | `artifacts/sprint10j/prediction_evidence.json` | FOUND | HASH MATCH | REFERENCED |
| `Certificate (artifacts/sprint10j/prediction_certificate.json)` | `artifacts/sprint10j/prediction_certificate.json` | FOUND | HASH MATCH | REFERENCED |
| `Repository Fingerprint (artifacts/sprint10l/repository_fingerprint_v1.json)` | `artifacts/sprint10l/repository_fingerprint_v1.json` | FOUND | HASH MATCH | REFERENCED |

---

## 4. Environment Check Results

* **Python version match:** {env_matches['python_version']} (Actual: `{actual_env['python_version'][:40]}`)
* **PyTorch version match:** {env_matches['torch_version']} (Actual: `{actual_env['torch_version']}`)
* **Numpy version match:** {env_matches['numpy_version']} (Actual: `{actual_env['numpy_version']}`)
* **Pandas version match:** {env_matches['pandas_version']} (Actual: `{actual_env['pandas_version']}`)

---

## 5. Verification Verdict

### Verdict: PASS
Every baseline fingerprint, hash, dataset, model, calibration artifact, threshold artifact, and evidence artifact exactly matches the production repository.

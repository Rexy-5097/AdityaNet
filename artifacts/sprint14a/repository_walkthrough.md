# Sprint 14A — Repository-Wide Scientific Forensic Verification: Walkthrough

**Audit Date:** 2026-06-19T10:11:40Z
**Overall Verdict:** PASS — 17/17 checks passed
**Certificate ID:** CERT-V3-FORENSIC-SPRINT14A-FINAL

---

## Executive Summary

Central question: Is the Version 3 pipeline actually training on the Sprint 12C
redesigned overlap dataset, and NOT accidentally using the legacy historical splits?

FINDING: CONFIRMED. The pipeline is correctly structured. Zero legacy dataset
references exist in any V3 pipeline module. All 17 forensic checks passed.

---

## 1. Dataset Source Verification

### File Roles (SHA256 verified)

| File | SHA256 | Rows | Period | SoLEXS | HEL1OS | Role |
|:--|:--|--:|:--|:--:|:--:|:--|
| train_v3.parquet | 08ff98f399f81f93... | 5,161,312 | 2010-01-02 to 2019-12-31 | 0% | 0% | Stage 1 pretraining |
| validation_v3.parquet | 7c519088c85d1d7c... | 1,568,759 | 2020-01-01 to 2022-12-31 | 0% | 0% | Stage 1 validation |
| test_v3.parquet | 2aaf8d57c52e67c0... | 1,806,673 | 2023-01-01 to 2026-06-14 | 54.85% | 76.08% | Stage 2 overlap (time-filtered) |

CRITICAL EVIDENCE: train_v3 and validation_v3 have SoLEXS=0%, HEL1OS=0%.
This is physical proof Stage 1 contains only GOES data — exactly as required.
test_v3 has active multi-instrument coverage — proof Stage 2 uses the overlap period.

### Stage 2 Time-Filter Verification

pilot_train_v3.py lines 358-360:
  stage2_train = test_full_df[(timestamp >= 2023-12-13) & (timestamp <= 2025-06-14)]
  stage2_val   = test_full_df[(timestamp >= 2025-06-15) & (timestamp <= 2025-12-14)]
  stage2_test  = test_full_df[(timestamp >= 2025-12-15) & (timestamp <= 2026-06-14)]

Row counts verified against Sprint 12C scientific_split_certificate.json:
  Stage 2 train:  786,298 rows  (cert: 786,298)  MATCH
  Stage 2 val:    262,480 rows  (cert: 262,480)  MATCH
  Stage 2 test:   261,455 rows  (cert: 261,455)  MATCH

---

## 2. Temporal Chronology

  train_v3 ends 2019-12-31 before validation_v3 starts 2020-01-01        PASS
  validation_v3 ends 2022-12-31 before test_v3 starts 2023-01-01          PASS
  Stage 1 val ends 2022-12-31 before Stage 2 starts 2023-12-13            PASS
  Stage 2 train -> val -> test strictly chronological                      PASS
  Sprint 12C row counts verified by time-filter                            PASS

---

## 3. Gradient Flow Verification

Stage 1 (SoLEXS + HEL1OS frozen):
  GOES encoder:      non-zero gradient  CORRECT
  SoLEXS encoder:    ZERO gradient      CORRECT (frozen)
  HEL1OS encoder:    ZERO gradient      CORRECT (frozen)
  Fusion attention:  non-zero gradient  CORRECT
  Classifier head:   non-zero gradient  CORRECT
  Stage 1 verdict:   PASS

Stage 2 (all encoders active):
  GOES encoder:      non-zero gradient  CORRECT
  SoLEXS encoder:    non-zero gradient  CORRECT
  HEL1OS encoder:    non-zero gradient  CORRECT
  Fusion attention:  non-zero gradient  CORRECT
  Classifier head:   non-zero gradient  CORRECT
  Stage 2 verdict:   PASS

---

## 4. Calibration Leakage Verification

  evaluator.fit_calibrators(val_logits, val_targets)   <- val set ONLY
  evaluator.evaluate(test_probs, test_targets, ...)    <- AFTER calibrators locked

Test set is never used during calibration fitting.
VERDICT: CALIBRATION IS LEAKAGE-FREE   PASS

---

## 5. Legacy Reference Scan

Total suspicious pattern hits:     150
In V3 pipeline scripts:            0   (CLEAN)

Classification:
  V1 baseline scripts (scripts/, sprint10*)   75   Expected — V1 preserved intentionally
  Documentation artifacts (old sprint files)  73   Historical records
  Transfer learning protocol contextual ref    2   Contextual mention only
  dataset_builder.py (V1 API, not V3)          1   Not imported by any V3 module
  V3 pipeline scripts                          0   CLEAN

VERDICT: PASS — Zero legacy references in V3 pipeline

---

## 6. Checkpoints

  stage1_best_loss.pt    PRESENT
  stage1_best_prauc.pt   PRESENT
  stage1_best_tss.pt     PRESENT (used for Stage 2 initialization)
  stage2_best_loss.pt    PRESENT
  stage2_best_prauc.pt   PRESENT
  stage2_best_tss.pt     PRESENT (used for evaluation)

VERDICT: PASS — 6/6 checkpoints present

---

## 7. All Verdicts (17/17 PASS)

  stage1_uses_goes_only_data                  PASS
  stage2_uses_multiinstrument_data            PASS
  stage2_train_slice_correct                  PASS
  stage2_val_slice_correct                    PASS
  stage2_test_slice_correct                   PASS
  stage2_active_solexs_telemetry              PASS
  stage2_active_hel1os_telemetry              PASS
  stage1_gradient_flow_correct                PASS
  stage2_gradient_flow_correct                PASS
  all_checkpoints_present                     PASS
  no_legacy_refs_in_v3_pipeline               PASS
  temporal_chronology_train_val               PASS
  temporal_chronology_val_test                PASS
  stage1_val_independent_from_stage2          PASS
  calibration_uses_val_only                   PASS
  feature_manifest_consistent                 PASS
  sprint12c_row_counts_verified               PASS

  OVERALL:  PASS (17/17)

---

## 8. Deliverables in artifacts/sprint14a/

  dataset_trace_report.json            SHA256 + rows + duty cycles + stage mapping
  gradient_trace_report.json           Per-stage gradient norms
  optimizer_trace_report.json          Checkpoint SHA256 + optimizer + scheduler state
  legacy_reference_report.json         Classified repo scan (0 critical)
  scientific_integrity_certificate.json  Signed PASS certificate
  repository_dependency_graph.md       Full pipeline data flow diagram
  repository_walkthrough.md            This document

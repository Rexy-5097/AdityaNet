<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Corrective forensic record; one errata applied in Sprint 23.5 — the sprint14b entries in §A and the sprint15b explanation samples were over-included: closer inspection (Sprint 23.5 targeted grep) found their "0.524x" values are model ROC-AUC / feature scores, coincidental numeric matches with no dependence on the leaked operator thresholds. They are NOT in the blast radius and were not annotated. -->
<!-- SUPERSEDED BY: n/a (errata only; all other findings stand) -->
<!-- DATE: 2026-07-03 -->

# 05 — Impact Analysis: Artifacts Invalidated by the Proven Leak

**Conclusion:** The leak invalidates every metric computed *at or downstream of* the deployed thresholds (yellow=0.46 / red=0.88) — most prominently the operator readiness numbers (trust score 0.524, precision 91.12%) that would anchor a submission deck. Critically, a substantial set of artifacts is **NOT** invalidated: the model checkpoint, the calibrator (validation-fit), the threshold-free metrics (ROC-AUC, PR-AUC, Brier, ECE), the val-tuned-threshold test evaluation, and — importantly — the Sprint 5.6/7 backtest and bootstrap artifacts, which were computed under the *validation-only* policy and are the honest replacement numbers. One attribution error in the Sprint 22 planning documents must also be corrected.

Identification only, per instructions; no values re-estimated.

---

## A. Directly invalidated (metrics computed at test-tuned thresholds)

| Artifact | What is invalid | Basis |
|----------|-----------------|-------|
| `artifacts/operator_thresholds.json` | The artifact itself: yellow=0.46, red=0.88 and the embedded `yellow_selection`/`red_selection` metric blocks are test-optimized | Proven in `04_leakage_proof.md` (Condition A) |
| `artifacts/operator_threshold_sweep.csv` | Entire sweep computed on test predictions (same run, same-second mtime 2026-06-15 19:54:38) | `optimize_operational_policy.py:58,259` |
| `artifacts/operator_readiness_report.json` | All operator metrics at those thresholds: trust score 0.524, precision 91.12%, recall 3.97%, TSS 0.039, episode counts (77/70/7), criteria_passed 3/5 | Matched leaked-value fingerprint grep this session; mtime 20:00:33 (6 min after thresholds); doubly compromised — evaluated on the same test data the thresholds were tuned on. Note: its generating script is absent from the tree (see `03_execution_path.md`) |
| `scratch/extracted_json_values.json`, `scratch/verification_checklist_results.json`, `scratch/verify_results.json` | Snapshot/verification records embedding the leaked values | Matched fingerprint grep this session |
| `artifacts/sprint10k/operator_trust_inventory.{json,md}`, `operator_trust_validation.{json,md}`, `operator_dependency_graph.json`, `operator_workflow_trace.json`, `component_reference_graph.json`, `reference_consistency.json`, `frontend_backend_mapping.json` | Sprint 10K inventoried and consistency-certified the leaked configuration as the production operator-trust system | `operator_trust_inventory.json` matched the distinctive fingerprint grep; the set documents `operator_thresholds.json` as production (`scratch/generate_sprint10k_artifacts.py:20,193–195,251`) |
| `artifacts/sprint10h5/architecture_ceiling_audit.json` | References the leaked file as `OPERATIONAL_PROD_PATH`; any ceiling conclusions expressed at those operating points | `scratch/run_architecture_ceiling_audit.py:20`; matched fingerprint grep |
| `artifacts/sprint10l/repository_fingerprint_v1.json`, `artifacts/sprint10lv/baseline_validation.json` | Fingerprint/baseline records certifying the leaked file's presence and hash as canonical | `scratch/generate_sprint10l_artifacts.py:197` |
| `artifacts/sprint14b/ablation_study.md`, `publication_results.md`, `publication_tables/ablation_comparison.json` | **Publication materials** citing leaked-policy values | Matched distinctive fingerprint grep this session (`0.524 \| 91.12 \| 0.430802 \| yellow=0.46 \| red=0.88`) — every operator-threshold-dependent number in them requires excision or recomputation under an honest policy |
| `artifacts/sprint15b/explanations/sample_70291_TP.json` (+ `sprint15b_backup/` copy) | Explanation samples labeled with alert decisions made at leaked thresholds | Matched fingerprint grep |

## B. Invalidated as documentation (repeat leaked values as authoritative)

| Document | Correction required |
|----------|--------------------|
| `PROJECT_STATUS.md` | Presents yellow=0.46/red=0.88 as "PRODUCTION THRESHOLDS" and reports operator readiness metrics (0.524, 91.12%, 3.97%) as verified; must be annotated as test-leaked |
| `context/architecture.md`, `context/memory.md`, `context/workflow.md` | AgentOS context files state 0.46/0.88 as production source of truth (workflow.md Rule 3 explicitly instructs using them); Rule 3 must be inverted |
| `artifacts/sprint22/Sprint22_Scientific_Baseline.md`, `Sprint22_Bottleneck_Analysis.md` | Already characterize the leak correctly, but repeat one attribution error (see D below) |
| `artifacts/project_status/project_inventory.md`, `project_status.json` | Inventory records listing the leaked configuration | 

## C. NOT invalidated (explicitly, to prevent over-correction)

| Artifact | Why it survives |
|----------|-----------------|
| `artifacts/models/patchtst_best.pt` | Model training never saw test data; split hygiene independently audited (`artifacts/aditya_l1/train_test_boundary_audit.json`, `window_overlap_audit.json` — PASS) |
| `artifacts/calibrator.pkl` | Fit on validation predictions (`calibrate_model.py:191–202`); selection on validation Brier (222–262) |
| Threshold-free test metrics: ROC-AUC 0.7485, PR-AUC 0.4950, Brier, ECE (raw & isotonic) in `artifacts/calibration/calibration_report.json` | Computed on test for *reporting*, not selection; no threshold involved |
| `artifacts/evaluation_audit_report.json` (TSS 0.2298 at t=0.3367) | Its threshold is the checkpoint's `best_threshold`, "tuned on val TSS" (`train_patchtst.py:318` print statement; report confirms `thresholds_match: true`) |
| `artifacts/operator_thresholds_validation_only.json` | Validation-only by construction (`refine_thresholds.py:63–68`; self-stamped `test_data_used: false`) |
| `artifacts/operator_backtest.json` | Honest evaluation: validation-only thresholds applied once to test (`backtest_operator_policy.py` header; `thresholds_source` field) — **this is the legitimate operator baseline** (TSS 0.38172, Recall 0.72265, EventRecall 0.69634) |
| `artifacts/bootstrap_metrics.json`, `artifacts/operator_trust_projection.json` | Generated by `scripts/simulated_fix_validation.py` (Sprint 7) from the *backtest* predictions (`PREDICTIONS_PATH = artifacts/backtest_window_predictions.csv`, lines 40–46) — downstream of the validation-only policy, not the leaked one. Confirmed: projection baseline (Precision 0.39033, Recall 0.72265) equals `operator_backtest.json` exactly, and every backtest point estimate falls inside the corresponding bootstrap CI |
| `artifacts/operator_trust_audit.json` | The audit that *documented* the leak; it is evidence, not casualty |
| V3 / sprint14c results (`test_results_model_D_seed_42.json`, `scientific_validation_report.md`) | Separate pipeline; V3 threshold 0.3169 selected on S2 *validation* (`scientific_validation_report.md` §1: "Validation-optimal raw threshold") |
| The broad-grep matches under `artifacts/aditya_l1/*.json` (localization/generalization/redundancy audits) | Matched only on incidental numeric substrings ("0.46"/"0.88" as unrelated values); no dependence on the operator threshold file was found in this session's targeted greps — excluded from the blast radius per the NOT PROVEN discipline |

## D. Attribution error to correct in Sprint 22 documents (self-correction)

`artifacts/sprint22/Sprint22_Scientific_Baseline.md` and `Sprint22_Bottleneck_Analysis.md` (and `PROJECT_STATUS.md` §Verified Performance) describe `artifacts/bootstrap_metrics.json` TSS CI [0.369, 0.393] as computed "at operator thresholds" — implying the leaked 0.46/0.88 policy. This session established it derives from the **validation-only** policy backtest (Sprint 7 chain, §C above). The correction *strengthens* the honest baseline: legitimate CIs for the corrective policy already exist.

## E. Summary of what a submission deck may and may not use

- **May not use:** trust score 0.524, precision 91.12%, recall 3.97%, TSS 0.039, thresholds 0.46/0.88, any Sprint 5.5 / 10K / 14B operator-policy number.
- **May use (with citation to their provenance):** ROC-AUC 0.7485, PR-AUC 0.4950, calibrated ECE 0.088, TSS 0.2298 @ val-tuned 0.3367, and the honest operator numbers — TSS 0.382, Recall 0.723, EventRecall 0.696, FalseEpisodes/month 6.92 at validation-only thresholds (`operator_backtest.json`) with bootstrap CIs (`bootstrap_metrics.json`).

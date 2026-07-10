# 01 — Dependency Graph: Production Inference → Threshold Origin

**Conclusion:** The production decision layer resolves, through an unbroken and fully verified chain, to predictions made on the test split. The chain is: HTTP `/predict/nowcast` → `app/main.py` → `app/api/v1/api.py` → `app/api/v1/endpoints/inference.py` → `SuryaNetInferenceService` (no-arg, default paths) → `artifacts/operator_thresholds.json` ← written by `scripts/optimize_operational_policy.py` ← reading `artifacts/calibration/probs.npy`/`labels.npy` ← written by `scripts/train_patchtst.py` during **test-set** evaluation ← `artifacts/research/test.parquet`. Every node below was read in this session.

---

## Forward chain (request → thresholds)

| # | Node | Evidence (path:line, read this session) |
|---|------|------------------------------------------|
| 1 | FastAPI app mounts API router | `app/main.py:54` — `app.include_router(api_router, prefix=settings.API_V1_STR)` |
| 2 | API router mounts predict endpoint | `app/api/v1/api.py:11` — `api_router.include_router(inference.router, prefix="/predict", tags=["predict"])` |
| 3 | Endpoint lazily instantiates the service **with no arguments** | `app/api/v1/endpoints/inference.py:38` — `_service = SuryaNetInferenceService()` inside `get_inference_service()` (lines 30–45; lazy global singleton) |
| 4 | Service constructor default threshold path | `app/services/ml/inference.py:86` — `thresholds_path: str = os.path.join("artifacts", "operator_thresholds.json")` |
| 5 | Service loads that file and consumes every policy key | `app/services/ml/inference.py:121–142` — reads `yellow_threshold` (127), `red_threshold` (128), `uncertainty_suppress_red_to_yellow/_yellow_to_green/_all_to_green` (131–133), `confidence_high_prob_min` (136), `confidence_medium_prob_min` (138); logs them at 142 |
| 6 | Loaded values drive alerting | `app/services/ml/inference.py:149–151` (tier assignment), 156 (`_apply_tiered_uncertainty_suppression`), 196–228 (RED confirmation uses `self.red_threshold`) |

No override exists anywhere: `grep -rn "InferenceService(\|thresholds_path" app/ scripts/` shows the only instantiation is the no-arg call at `app/api/v1/endpoints/inference.py:38`, and `grep -rn "validation_only" app/` returns **no matches** (verified this session).

## Backward chain (thresholds → data origin)

| # | Node | Evidence (path:line, read this session) |
|---|------|------------------------------------------|
| 7 | `artifacts/operator_thresholds.json` written by exactly one script | `scripts/optimize_operational_policy.py:57` — `THRESHOLDS_OUT = os.path.join("artifacts", "operator_thresholds.json")`; write at lines 295–296 (`with open(THRESHOLDS_OUT, "w") ... json.dump`). Repo-wide grep for `operator_thresholds.json` (this session) found **no other writer** — all other references (`scratch/compute_hashes.py:8`, `scratch/extract_all_json_values.py:36`, `scratch/generate_sprint10l_artifacts.py:197` (fstat), `scratch/verify_sprint15a.py:32`, `scratch/run_architecture_ceiling_audit.py:20`, etc.) are readers/verifiers |
| 8 | The script's output schema matches the deployed file key-for-key | `scripts/optimize_operational_policy.py:262–293` emits `yellow_threshold`, `red_threshold`, hardcoded tiers `0.10/0.15/0.20` (lines 267–269), `confidence_high_prob_min = red_threshold` (271), `confidence_medium_prob_min = yellow_threshold` (273), `yellow_selection`/`red_selection` metric blocks (276–291), `roc_auc` (292) — the exact keys present in the deployed `artifacts/operator_thresholds.json` (read this session: yellow=0.46, red=0.88, tiers 0.10/0.15/0.20, confidence_high_prob_min=0.88, confidence_medium_prob_min=0.46) |
| 9 | The script's inputs | `scripts/optimize_operational_policy.py:55–56` — `PROBS_PATH = artifacts/calibration/probs.npy`, `LABELS_PATH = artifacts/calibration/labels.npy`; loaded at 166–167; swept at 102 (0.05→0.95, step 0.01); docstring line 6: *"Sweeps calibrated probability thresholds on the saved test-set probabilities"* |
| 10 | `probs.npy`/`labels.npy` written by the training script during **test** evaluation | `scripts/train_patchtst.py:327–329` — under banner "Saving Calibration Data": `np.save(os.path.join(CALIB_DIR, "probs.npy"), all_probs)` / `labels.npy`, where `all_probs, all_labels` come from `trainer.evaluate_test(test_loader)` at line 315, under banner "Test Set Evaluation (Best Checkpoint)" (line 314). Header docstring lines 17–19: `artifacts/calibration/probs.npy ← test sigmoid probabilities`, `labels.npy ← test true labels` |
| 11 | The test loader's data source | `scripts/train_patchtst.py:66` — `TEST_PARQUET = os.path.join("artifacts", "research", "test.parquet")`; dataset built at 242 (`split_name="test"`), loader at 254 |

## Array-identity confirmation (computed this session)

- `probs.npy` shape = (1,806,313), `labels.npy` positives = **419,150** (23.2047%) — exactly equal to the test split per `artifacts/evaluation_audit_report.json` → `dataset_consistency`: `test_parquet_total: 1806313`, `test_parquet_pos: 419150`, `saved_labels_total: 1806313`, `saved_labels_pos: 419150`, `passed: true`.
- Applying t=0.46 and t=0.88 to these arrays reproduces the deployed file's `yellow_selection` and `red_selection` blocks **exactly, to all six recorded decimal places** (precision 0.425314 / recall 0.613888 / tss 0.363247 / far 0.574686 / f1 0.502491 at yellow; 0.517326 / 0.353255 / 0.253664 / 0.482674 / 0.41983 at red), and ROC-AUC recomputes to 0.748514 = deployed `roc_auc`.

## Graph

```
POST /predict/nowcast
  └─ app/main.py:54 ──> app/api/v1/api.py:11 ──> app/api/v1/endpoints/inference.py:38
        └─ SuryaNetInferenceService()            [no-arg → all defaults]
              └─ app/services/ml/inference.py:86,121–142
                    └─ artifacts/operator_thresholds.json     [yellow=0.46, red=0.88, tiers, confidence]
                          ▲ sole writer
                    scripts/optimize_operational_policy.py:57,295–296
                          ▲ inputs (lines 55–56, 166–167)
                    artifacts/calibration/probs.npy + labels.npy    [N=1,806,313; pos=419,150]
                          ▲ writer (lines 327–329, from evaluate_test at 315)
                    scripts/train_patchtst.py  ──reads──  artifacts/research/test.parquet (line 66)
                                                          [TEST SPLIT, 2023 → 2026-06-14]
```

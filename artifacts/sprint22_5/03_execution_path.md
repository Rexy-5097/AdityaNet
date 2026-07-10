# 03 — Execution Path: Live Code, Dead Code, and the Deployment Sequence

**Conclusion:** The live production path is `train_patchtst.py → calibrate_model.py → optimize_operational_policy.py → operator_thresholds.json → inference.py`. The scientifically correct branch — `refine_thresholds.py → operator_thresholds_validation_only.json → backtest_operator_policy.py` (Sprint 5.6) — was fully built, executed, and validated, then abandoned one step short of deployment: no code in `app/` ever loads its output. One earlier threshold artifact (`operational_thresholds.json`) is dead, superseded within its own sprint.

---

## The LIVE production path (every hop verified this session)

```
[1] scripts/train_patchtst.py
      reads  artifacts/research/{train,validation,test}.parquet (lines 64–66)
      trains V1 PatchTST → artifacts/models/patchtst_best.pt
      evaluates on TEST (line 315: trainer.evaluate_test(test_loader))
      SAVES TEST PREDICTIONS → artifacts/calibration/probs.npy, labels.npy (lines 327–329)
      mtime of outputs: 2026-06-15 13:19:16

[2] scripts/calibrate_model.py                          ← calibration: CLEAN
      generates fresh VALIDATION predictions (lines 144–184)
      fits Platt + Isotonic on VALIDATION (lines 191–202)
      selects winner on VALIDATION Brier (lines 222–262)
      → artifacts/calibrator.pkl (mtime 19:25:16)
      (also writes artifacts/operational_thresholds.json — dead, see below)

[3] scripts/optimize_operational_policy.py              ← thresholds: LEAKED
      reads artifacts/calibration/probs.npy + labels.npy   [TEST SPLIT] (lines 55–56)
      sweeps 0.05→0.95 (line 102), trust_score selection (lines 176–239)
      → artifacts/operator_thresholds.json  (yellow=0.46, red=0.88)
      → artifacts/operator_threshold_sweep.csv
      mtime of both outputs: 2026-06-15 19:54:38 (same second)

[4] app/services/ml/inference.py :: SuryaNetInferenceService
      default thresholds_path = artifacts/operator_thresholds.json (line 86)
      loads yellow/red + uncertainty tiers + confidence cutoffs (lines 121–142)
      applies them in alert tiering (149–151), suppression (156), RED confirmation (196–228)

[5] app/api/v1/endpoints/inference.py
      get_inference_service() → SuryaNetInferenceService()  [no arguments] (line 38)
      mounted at /predict via app/api/v1/api.py:11 and app/main.py:54
```

## The ABANDONED corrective branch (Sprint 5.6 — built, run, never deployed)

```
[A] scripts/refine_thresholds.py                 (mtime 20:11:32)
      "Sprint 5.6 — Task E: Validation-Only Threshold Optimization" (line 4)
      explicitly never reads test.parquet / probs.npy / labels.npy (_NOT_LOADED, lines 63–68)
      → artifacts/operator_thresholds_validation_only.json  (yellow=0.14, red=0.95; mtime 20:31:36)
        output self-stamps: "data_used_for_selection": "validation", "test_data_used": false

[B] scripts/backtest_operator_policy.py          "Sprint 5.6 — Task F: Test-Split Backtest"
      loads thresholds FROM the validation-only file (THRESHOLDS_PATH, line ~48)
      evaluates on test.parquet at hourly stride, explicitly not reading probs.npy/labels.npy
      → artifacts/operator_backtest.json  (read this session):
        TSS 0.38172 | Precision 0.39033 | Recall 0.72265 | EventRecall 0.69634
        FalseEpisodesPerMonth 6.92 | thresholds: yellow 0.14, red 0.95

[C] scripts/simulated_fix_validation.py          "Sprint 7 — Task C & D"
      loads artifacts/backtest_window_predictions.csv + test.parquet (lines 40–41)
      → artifacts/bootstrap_metrics.json (mtime 22:26:42) — 1,000-resample CIs
      → artifacts/operator_trust_projection.json — its "baseline" block equals the
        backtest numbers (Precision 0.39033, Recall 0.72265), i.e., the VALIDATION-ONLY policy

[X] DEPLOYMENT — never happened.
      grep -rn "validation_only" app/  →  NO MATCHES (this session)
      app/services/ml/inference.py last modified 20:56:41 — AFTER the validation-only
      file existed (20:31:36) — and its default path (line 86) still names the leaked file.
```

**Interpretation of the mtime at 20:56:41:** the production service was edited after the corrective artifact existed, and the edit did not repoint it. Whether that edit touched the path line cannot be determined without version history (none exists — `MIGRATION_REPORT.md:39`); what is certain is the file's final state loads the leaked thresholds.

## Dead / superseded components

| Component | Status | Evidence |
|-----------|--------|----------|
| `artifacts/operational_thresholds.json` (yellow=0.09/red=0.19) | DEAD — superseded same era | Written by `calibrate_model.py:38,355–357`; the repo's own tooling labels it `OPERATIONAL_OLD_PATH` vs `operator_thresholds.json` = `OPERATIONAL_PROD_PATH` (`scratch/run_architecture_ceiling_audit.py:20–21`); `inference.py` never references it |
| `artifacts/operator_thresholds_validation_only.json` | COMPUTED + BACKTESTED, NEVER WIRED | See branch [A]–[X] above |
| `artifacts/models_v3/test_checkpoint.pt` | Abandoned V3 artifact (untrained; best_val_tss=-1.0 per `PROJECT_STATUS.md` model inventory) | Unrelated to the threshold chain; listed for completeness of the execution map |
| `scratch/verify_*.py`, `scratch/generate_sprint10*_artifacts.py`, `scratch/compute_hashes.py` | Read-only verifiers/inventories of the threshold files | Grep this session showed they reference but never write `operator_thresholds.json` |
| Writer of `artifacts/operator_readiness_report.json` | **ABSENT from the tree** | Repo-wide grep this session found only readers (`scratch/extract_all_json_values.py:38`, `scratch/run_full_validation_check.py:275`, `scratch/verify_everything.py:190`, `scratch/verify_sprint10k.py`); the generating script is not present — a provenance gap in that report (its mtime 20:00:33 and its content — trust score 0.524 at yellow=0.46/red=0.88 — tie it to the leaked policy era, but its exact generation procedure is NOT PROVEN) |

## Training-through-deployment sequence (chronological, from mtimes + script content)

1. **13:19** — V1 training run completes; test evaluation writes `probs.npy`/`labels.npy` (Sprint 5).
2. **19:25** — Calibrator fit on validation; isotonic selected (`calibration_report.json`).
3. **19:54** — Sprint 5.5: thresholds swept **on the test arrays**; `operator_thresholds.json` + sweep CSV written.
4. **20:00** — Operator readiness evaluated at those thresholds (`operator_readiness_report.json`).
5. **20:11–20:31** — Sprint 5.6: leak recognized; validation-only rerun built and executed (`refine_thresholds.py` → `operator_thresholds_validation_only.json`). The in-repo audit `artifacts/operator_trust_audit.json` records the finding explicitly: `"test_data_used_for_optimization": true`.
6. **20:56** — `inference.py` receives its final modification; production path remains on the leaked file.
7. **22:26** — Sprint 7 bootstrap/projection work proceeds on the *backtest* (validation-only policy) predictions.
8. **2026-07-01** — Repository migrated to this SSD via `rsync -a` (`MIGRATION_REPORT.md:3,45`); mtimes preserved.

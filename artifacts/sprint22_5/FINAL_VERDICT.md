LEAKAGE PROVEN

# Final Verdict — Production Decision Layer Test-Set Leakage

All four required conditions are CONFIRMED simultaneously. The production alert thresholds (yellow=0.46, red=0.88) were selected by sweeping predictions made on the test split, they are exactly what the deployed inference service loads, no validation-only replacement ever entered the production path, and the filesystem provenance trail — rsync-preserved timestamps, same-second output pairing, script content, and the repository's own audit records — coherently supports this sequence. Full condition-by-condition proof: `04_leakage_proof.md`.

## The chain, in one paragraph

`scripts/train_patchtst.py` saved its **test-set** sigmoid probabilities and labels to `artifacts/calibration/probs.npy`/`labels.npy` (lines 315, 327–329; test source `artifacts/research/test.parquet`, line 66) at 13:19 on 2026-06-15. That evening (19:54:38), `scripts/optimize_operational_policy.py` — whose own docstring says it "sweeps calibrated probability thresholds on the saved **test-set** probabilities" (line 6) — swept those arrays and wrote `artifacts/operator_thresholds.json` (lines 55–57, 295–296). The production service `app/services/ml/inference.py` loads exactly that file by default (line 86), is instantiated with no arguments in the live `/predict` endpoint (`app/api/v1/endpoints/inference.py:38`, mounted via `app/api/v1/api.py:11` and `app/main.py:54`), and consumes every value in it (lines 121–142).

## Decisive quantitative evidence (computed this session)

1. **Array identity:** `labels.npy` has N=1,806,313 with 419,150 positives — byte-count-exact match to the test split (`artifacts/evaluation_audit_report.json` → `dataset_consistency.passed: true`). The validation split (1,568,759 rows, 4.07% positive) cannot produce this fingerprint.
2. **Exact reproduction:** applying the deployed thresholds to those arrays reproduces the deployed file's embedded selection metrics to **all six recorded decimal places** (yellow: 0.425314/0.613888/0.363247/0.574686/0.502491; red: 0.517326/0.353255/0.253664/0.482674/0.41983) and its ROC-AUC (0.748514). The deployed values are a deterministic function of the test data.
3. **Prior internal knowledge:** the repository's own audit, `artifacts/operator_trust_audit.json`, already records `"test_data_used_for_optimization": true` with the identical provenance chain — the leak was detected internally, a validation-only replacement was built and backtested (`operator_thresholds_validation_only.json`, 20:31:36; `operator_backtest.json`), and production was never repointed: `grep "validation_only" app/` returns nothing, and `inference.py`'s final modification (20:56:41) post-dates the replacement while still defaulting to the leaked file.

## What this means for the submission

- **Compromised and unusable:** trust score 0.524, precision 91.12%, recall 3.97%, the 0.46/0.88 thresholds, and every Sprint 5.5 / 10K / 14B number expressed at those operating points (full list: `05_impact_analysis.md` §A–B).
- **Clean and usable today:** the model checkpoint, the validation-fit calibrator, all threshold-free metrics (ROC-AUC 0.7485, PR-AUC 0.4950, calibrated ECE 0.088), the val-tuned-threshold evaluation (TSS 0.2298 @ 0.3367), and — the honest operator baseline — TSS 0.382 / Recall 0.723 / EventRecall 0.696 at the validation-only thresholds with existing bootstrap CIs (`operator_backtest.json`, `bootstrap_metrics.json`; `05_impact_analysis.md` §C).
- **Fix:** three-commit specification in `06_fix_specification.md` — quarantine, replacement policy (a validated stopgap already exists in the repository), provenance-gated loader with regression tests. Rollback is a one-line revert.

## Scope notes (honesty requirements)

The calibrator is **not** part of the leak — `scripts/calibrate_model.py` fits on validation (lines 191–202). Three residual unknowns are documented in `04_leakage_proof.md` (content of the final `inference.py` edit, the absent generator of `operator_readiness_report.json`, no runtime log capture of threshold loading); none weakens any of the four conditions. One attribution error in the Sprint 22 planning documents (bootstrap CI provenance) is corrected in `05_impact_analysis.md` §D — in the honest direction.

## Document index

| File | Content |
|------|---------|
| `01_dependency_graph.md` | Full request→origin chain, every node with path:line |
| `02_threshold_provenance.md` | Creation time, generator, dataset, newer artifacts, timestamp-trust argument |
| `03_execution_path.md` | Live path vs abandoned corrective branch vs dead code; training→deployment sequence |
| `04_leakage_proof.md` | Conditions A–D, each CONFIRMED with cited evidence |
| `05_impact_analysis.md` | Invalidated artifacts; explicitly-not-invalidated artifacts; deck guidance |
| `06_fix_specification.md` | Quarantine + replacement + provenance-gated loader; tests; gates; rollback |

# Sprint 23 — Deployment Report

**Conclusion:** `artifacts/policies/operator_policy_v2.json` (policy_id `operator_policy_v2.0.0`) is deployed: production `app/services/ml/inference.py` loads it by default, verified end-to-end with the real model and calibrator under the venv (Gate 2). The quarantined leaked policy is physically out of the production path and structurally unloadable. One operationally significant property carries over from Sprint 5.6 and needs operator awareness: the RED tier is effectively disabled at red=0.95.

## Deployed policy

| Property | Value |
|----------|-------|
| File | `artifacts/policies/operator_policy_v2.json` |
| policy_id / versions | `operator_policy_v2.0.0` · schema 1.0 · operator 2.0.0 · scientific V1-2026.06 |
| Thresholds | yellow = **0.14**, red = **0.95** |
| Derivation | Sprint 5.6 validation-only trust-score sweep (`scripts/refine_thresholds.py`), promoted by `scripts/sprint23/promote_sprint56_policy.py` per `06_fix_specification.md` Variant A |
| Dataset | `artifacts/research/validation.parquet` — SHA256 9c1b770f2268…, 1,568,759 rows, 1,568,399 windows, 63,849 positives (4.07%) |
| Calibration | `artifacts/calibrator.pkl` (isotonic, validation-fit) — unchanged |
| Generator pin | sha256:46209ddd6199… (any edit to the promotion script invalidates the policy at startup — regenerate, don't edit) |
| Uncertainty tiers | 0.10/0.15/0.20 — carried Sprint 5.5 design constants, labelled `not_data_derived` |

## Expected operational behavior (honest backtest, `artifacts/operator_backtest.json`)

Hourly-stride evaluation of exactly these thresholds on the held-out period: window Precision 0.390 · Recall 0.723 · TSS 0.382 · F1 0.507 · EventRecall 0.696 · median lead time 11.8 h · ~6.9 false episodes/month · alert mix GREEN 17,176 / YELLOW 12,930 / **RED 0**.

**Known limitation (recorded in the policy's `lineage.known_limitations`):** red=0.95 produced zero RED alerts — the RED tier, its confirmation logic, and the coincidence filter are effectively dormant; the system operates as a GREEN/YELLOW forecaster. This is the honest trade Sprint 5.6's constraint relaxation produced (red precision 1.0 at recall 0.012 on validation). Accepted as the stopgap; the Sprint 22 cost-loss policy (Variant B, episode-level selection) is the planned successor with a functioning RED tier.

## Production path verification

- Endpoint chain unchanged: `POST /predict/nowcast` → `get_inference_service()` → `SuryaNetInferenceService()` (no-arg) → default `thresholds_path = ACTIVE_POLICY_PATH`. The default — the exact mechanism that carried the leak (Sprint 22.5 Condition B) — is now the gated path.
- Gate 2 executed the true production constructor: model onto MPS, calibrator unpickled, policy loaded + startup-validated (9/9 PASS), thresholds mapped. Alert logic itself is byte-unchanged from Sprint 5.5.
- Negative control in the same run: pointing the constructor at the archived leaked file raises `PolicyLeakageError` before the service exists.

## Quarantine state

`artifacts/archive/`: `operator_thresholds.json` (QUARANTINE_REASON injected; pre-injection SHA256 033063ef… recorded inside), `operator_threshold_sweep.csv` (byte-identical, SHA256 4e79cdaa…), sidecar, README. Originals removed from `artifacts/` root. Nothing in `app/` references the old path (the only runtime consumer was `inference.py`, now migrated).

## Rollback

Single-commit revert of `inference.py` + restore of the archived JSON minus injected fields (byte-verifiable against the recorded pre-injection hash). Doing so redeploys a proven-leaked policy; the procedure exists for completeness, not as an option.

## Human review recommended before external exposure

1. **Operator sign-off on the GREEN/YELLOW-only alert behavior** at 0.14/0.95 (materially different alert volumes than the void 0.46/0.88 behavior: ~12,930 YELLOW windows per backtest period vs the old regime's sparse-but-fake alerts).
2. **Cost-ratio choice for the Variant B successor** (Sprint 22 WP4 publishes a frontier; the operator, not the optimizer, should pick the miss/false-alarm trade).
3. **Documentation blast-radius sweep** (`05_impact_analysis.md` §A/§B) — historical docs still cite the void numbers.

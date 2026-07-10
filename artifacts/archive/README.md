# Quarantine Archive — Leaked Test-Derived Policy Artifacts

**These files document a known test-set leakage incident. They must never be
used for evaluation, threshold selection, deployment, or any metric claim.**

## Incident

Sprint 22.5 proved (verdict: **LEAKAGE PROVEN**, all four conditions confirmed —
`artifacts/sprint22_5/FINAL_VERDICT.md`, `04_leakage_proof.md`) that the
production operator thresholds (yellow=0.46, red=0.88) were selected by sweeping
predictions made on the **test split**. The generator,
`scripts/optimize_operational_policy.py`, states this in its own docstring
(line 6) and read `artifacts/calibration/probs.npy`/`labels.npy` — the
1,806,313-window test predictions saved by `scripts/train_patchtst.py`
(lines 315, 327–329). The deployed file's embedded selection metrics reproduce
exactly (six decimal places) from those test arrays.

Every metric reported at these thresholds is optimistically biased and invalid:
trust score 0.524, precision 91.12%, recall 3.97% (`artifacts/operator_readiness_report.json`)
and all Sprint 10K / 14B numbers expressed at 0.46/0.88
(full blast radius: `artifacts/sprint22_5/05_impact_analysis.md`).

## Files

| File | What it is | Marking |
|------|-----------|---------|
| `operator_thresholds.json` | The leaked Sprint 5.5 policy (yellow=0.46, red=0.88), formerly loaded by production `inference.py` | `QUARANTINE_REASON: LEAKED_TEST_DERIVED` field injected; original pre-injection SHA256 recorded inside under `quarantine_details` (033063ef…) for evidence continuity |
| `operator_threshold_sweep.csv` | The full test-split threshold sweep from the same generation run (identical mtime 2026-06-15 19:54:38) | Bytes preserved **unmodified** as evidence; reason carried in the sidecar below |
| `operator_threshold_sweep.QUARANTINE.json` | Sidecar marking the CSV (`QUARANTINE_REASON: LEAKED_TEST_DERIVED`, SHA256 4e79cdaa…) | — |

## Enforcement

These artifacts are structurally unloadable: `app/services/ml/policy.py`
rejects any document carrying a `QUARANTINE_REASON` field before any other
check (`PolicyLeakageError`), and independently rejects any policy whose
dataset fingerprint matches the proven leaked test fingerprint
(1,806,313 windows / 419,150 positives).

## Successor

The production service loads `artifacts/policies/operator_policy_v2.json` —
validation-derived (Sprint 5.6, `scripts/refine_thresholds.py`), promoted with
full provenance metadata by `scripts/sprint23/promote_sprint56_policy.py`, and
honestly backtested (`artifacts/operator_backtest.json`: TSS 0.382,
Recall 0.723, EventRecall 0.696).

*Quarantined 2026-07-03 (Sprint 23). Do not delete: these files are the
evidentiary record of the incident.*

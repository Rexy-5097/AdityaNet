<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Definitive clean-policy performance baseline for frozen Version 3. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Scientific Baseline (Clean-Policy Numbers Only)

**Conclusion:** This is the definitive, leakage-free performance record of frozen Version 3. Every number below derives from decisions (thresholds, calibrator, model selection) made exclusively on training or validation data and evaluated on data those decisions never saw. The void leaked-policy numbers (trust score 0.524, precision 91.12%, recall 3.97% at yellow=0.46/red=0.88) appear nowhere in this table and must never be cited as Version 3 performance.

## Methodology summary

| Element | Specification |
|---------|---------------|
| Production model | V1 PatchTST, 822,401 trainable parameters (828,161 incl. positional-encoding buffers), checkpoint epoch 3 — `artifacts/models/patchtst_best.pt` |
| Window construction | 360-minute sliding windows over 14 engineered GOES features (`artifacts/feature_columns.json`); stride 1 for window-level metrics; stride 60 (hourly) for the operator backtest |
| Evaluation splits | Chronological, leakage-audited (`artifacts/aditya_l1/train_test_boundary_audit.json`, `window_overlap_audit.json` — both PASS): train 2010-01-02→2019-12-31 (0.62% positive), validation 2020-01-01→2022-12-31 (4.07%), test 2023-01-01→2026-06-14 (23.20%, 1,806,313 windows) |
| Calibration source | `artifacts/calibrator.pkl` — isotonic regression fit on validation predictions (`scripts/calibrate_model.py` lines 191–202), selected on validation Brier |
| Operator policy | `artifacts/policies/operator_policy_v2.json` (yellow=0.14, red=0.95) — validation-only trust-score sweep (Sprint 5.6), promoted with full provenance in Sprint 23; dataset fingerprint SHA256 9c1b770f…, 1,568,399 validation windows / 63,849 positives |
| Uncertainty | MC Dropout, 50 forward passes; suppression tiers 0.10/0.15/0.20 are Sprint 5.5 design constants, **not data-derived** (recorded in the policy's `tier_provenance`) |

## Table 1 — V1 threshold-free discrimination and calibration (full test set, N=1,806,313)

| Metric | Raw | Isotonic calibrated | Source |
|--------|-----|--------------------|--------|
| ROC-AUC | 0.7485 | 0.7482 | `artifacts/calibration/calibration_report.json` |
| PR-AUC | 0.4950 | 0.4747 | same |
| Brier | 0.2365 | 0.1594 | same |
| ECE | 0.2722 | 0.0876 | same |

## Table 2 — V1 fixed-threshold test evaluation (threshold 0.3367, tuned on validation TSS)

Triple-verified — original, recomputed, and fresh-inference passes agree exactly (`artifacts/evaluation_audit_report.json`).

| Metric | Value |
|--------|-------|
| TSS | 0.2298 |
| Precision / Recall | 0.2865 / 0.9286 |
| F1 / FAR | 0.4379 / 0.7135 |
| Confusion (tp/fp/fn/tn) | 389,229 / 969,386 / 29,921 / 417,777 |

## Table 3 — Operator policy performance (deployed policy, honest backtest)

Hourly-stride evaluation of yellow=0.14/red=0.95 on the held-out period; thresholds never saw this data (`artifacts/operator_backtest.json`); 95% bootstrap CIs from 1,000 resamples (`artifacts/bootstrap_metrics.json`).

| Metric | Value | 95% CI |
|--------|-------|--------|
| TSS | 0.3817 | [0.3689, 0.3933] |
| Precision | 0.3903 | [0.3823, 0.3981] |
| Recall | 0.7227 | [0.7120, 0.7328] |
| F1 | 0.5069 | [0.4984, 0.5148] |
| FAR | 0.6097 | [0.6019, 0.6177] |
| Event recall (episode level) | 0.6963 | — |
| False episodes per month | 6.92 | — |
| Median lead time | 11.77 hours | — |
| Alert mix (n=30,106 windows) | GREEN 17,176 / YELLOW 12,930 / RED 0 | — |

**Material caveat:** the RED tier issues zero alerts at red=0.95 — Version 3 operates as a GREEN/YELLOW forecaster (recorded in the policy's `lineage.known_limitations`). `[V4]` A cost-loss, episode-level successor policy with a functioning RED tier is the designated follow-on.

## Table 4 — V3 research model (LateFusionPatchTST, not deployed; S2 test, N=261,095, 11.92% positive)

Threshold 0.3169 selected on S2 validation (clean — `scientific_validation_report.md` §1); results from `artifacts/sprint14c/test_results_model_D_seed_42.json`, seed 42.

| Metric | Raw | Isotonic |
|--------|-----|----------|
| TSS | 0.3689 | 0.3840 |
| ROC-AUC | 0.7404 | 0.7398 |
| PR-AUC | 0.4522 | 0.4259 |
| ECE | 0.2273 | 0.0420 |
| Brier | 0.1359 | 0.0887 |

Instrument ablation (`scientific_validation_report.md` §6): full model TSS 0.4131 vs GOES-only 0.4046 — SoLEXS/HEL1OS contribute marginally; the multi-instrument benefit is unproven on flare-containing joint data (`[V4]` SCI-001, see `VERSION3_OPEN_RESEARCH.md`).

## Provenance guarantees behind these numbers

Calibrator: validation-fit (verified in code). Thresholds: validation-swept, fingerprint-verified at every service startup against `artifacts/research/validation.parquet` bytes. Test set: used exactly once per evaluation, never for selection. Leakage protections: five-layer guard, 15 regression tests, gate outputs on record (`artifacts/sprint23/Validation_Report.md`).

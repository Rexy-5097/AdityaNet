<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 27 Version 4 requirements derived from repository evidence. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 27 — Version 4 Requirements (Q7)

**Five MANDATORY requirements. The single most critical: every Version 4 skill claim must be measured on the frozen Sprint 24 episode-level harness against matched persistence and climatology baselines with paired block-bootstrap intervals — because the repository's history shows that every prior headline number that skipped this discipline (leaked thresholds, window-level metrics, validation-optimal operating points) later collapsed under audit.**

## MANDATORY — without these, V4 cannot claim scientific improvement over V3

| # | Requirement | Evidence |
|---|-------------|----------|
| M1 | All skill claims scored once, post-selection, on the frozen Sprint 24 `UnifiedEvaluator` (episode-level, block bootstrap, matched persistence 0.3018 / climatology 0.0000 floors) | `artifacts/sprint24/08_final_verdict.md` (the model-vs-persistence verdict was only decidable on this harness); `artifacts/sprint24/06_statistical_tests.md` (window-level and IID statistics shown invalid); `artifacts/sprint22_5/FINAL_VERDICT.md` (what happens without matched discipline) |
| M2 | Multi-seed evidence (minimum 3 seeds) with across-seed variance for any headline configuration | `artifacts/sprint26a/01_SCREENING_RESULTS.md` and `artifacts/sprint26b/GO_NO_GO_DECISION.md` label every single-seed result exploratory; `artifacts/sprint23_5/VERSION3_LIMITATIONS.md` (single-seed limitation carried since sprint14c) |
| M3 | Sprint 23 provenance gating extended to every V4 artifact class — models, datasets, calibrators, policies: 13-field provenance, self-hash, leakage guard, validation-only selection | `artifacts/sprint23/Policy_Architecture.md`; `artifacts/sprint22_5/04_leakage_proof.md` (proven test-set threshold leakage in V3's history); `app/services/ml/policy.py` |
| M4 | Any Aditya-L1 fusion or instrument-value claim requires flare-bearing joint evidence: an extended aligned corpus containing M/X events (P0 of `06_EXPERIMENT_CAMPAIGN.md`) plus multi-seed instrument ablations — the current official-target evidence base is vacuous (median AND max correlation 0.0 across all 2,109 features against `target_6hr_binary`) and the only model ablation is single-seed with a +0.0085 gap | `artifacts/aditya_l1/target_relationship_audit.json`; `artifacts/aditya_l1/overlap_dataset.parquet` (zero M/X positives); `scientific_validation_report.md` §6 |
| M5 | Fair-input precondition for instrument conclusions: deduplicated (12 of 22 current columns are duplicates), log-scaled, physics-engineered Aditya features before any verdict on instrument value — otherwise V4 would repeat V3's unfair test | `artifacts/sprint27/01_ADITYA_FEATURE_AUDIT.md` and `02_FEATURE_VALUE_ANALYSIS.md` (this sprint, computed correlations r=0.85–0.99, no normalization anywhere in the pipeline) |

## SHOULD — strong repository evidence this matters for operator trust

| # | Requirement | Evidence |
|---|-------------|----------|
| S1 | A functioning RED tier selected by cost-loss, episode-level optimization on validation | `artifacts/sprint24/05_operator_analysis.md` (RED fired 0 times through the deployed suppression chain in the honest backtest; 94 episodes at threshold-only) |
| S2 | Yellow duty-cycle reduction from the measured 0.42–0.45 of all time toward "rare, sharp, early" alerting | `artifacts/sprint24/05_operator_analysis.md` (41.5% duty cycle called operator-hostile); `artifacts/sprint26b/E2_EXECUTION_REPORT.md` (recall gains bought by duty cycle do not survive the primary metric) |
| S3 | Per-timestep availability masking replacing the label-minute scalar | `app/services/ml/dataset_v3.py:110-111` vs `scripts/build_multi_instrument_dataset.py:114,120` (this sprint's trace); SoLEXS available only 75.6% of Stage-2 minutes (computed this session) |
| S4 | Walk-forward regime monitoring of calibration and operating points across the solar cycle | `artifacts/sprint24/results_d.json` (validation-optimal threshold collapsing 0.5689→0.2150 across the regime shift); `artifacts/sprint26a/01_SCREENING_RESULTS.md` E1 (regime-inclusive training alone did not fix transfer) |
| S5 | Version control and continuous integration before any retraining campaign | `artifacts/sprint23_5/VERSION4_RISK_REGISTER.md` R6 (no git, single external SSD, prior original-deletion incident per `ORIGINAL_DELETION_CERTIFICATE.md`) |

## OPTIONAL — improves the system, not blocking

| # | Requirement | Evidence |
|---|-------------|----------|
| O1 | Token-level cross-attention fusion (only after M5 and only if campaign arm C5 shows signal) | `artifacts/sprint27/05_FUSION_LIMITATIONS.md` (fusion is not the binding constraint) |
| O2 | Conformal prediction as an alternative uncertainty layer | `artifacts/sprint23_5/VERSION3_OPEN_RESEARCH.md` (open item; no repository evidence of necessity) |
| O3 | Operator dashboard surfacing alerts with policy provenance | `artifacts/sprint23_5/VERSION3_DEPLOYMENT_BASELINE.md` (absent; API-only) |
| O4 | MPS determinism pinning / archived-prediction canonicalization codified | `scientific_validation_report.md` §3 (9.76e-4 cross-platform drift; convention already documented) |

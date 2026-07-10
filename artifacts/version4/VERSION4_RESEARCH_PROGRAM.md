<!-- VERSION STATUS: CURRENT -->
<!-- REASON: V4 scientific questions and assumption audit, written at V4 planning. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Research Program

**Conclusion:** V4 must answer six scientific questions, of which the first — does the model beat persistence under matched, episode-level evaluation? — is existential: `artifacts/baseline_metrics.json` puts persistence at TSS 0.3029 while the model's fixed-threshold test TSS is 0.2298 (`artifacts/evaluation_audit_report.json`), and no matched comparison exists. The assumption audit below finds two of V3's fifteen implicit assumptions FALSE, seven UNVALIDATED, and only four fully VALIDATED — the program is ordered to convert the highest-consequence unvalidated assumptions first.

## Research questions

### RQ1 — Does AdityaNet outperform trivial forecasters under operator-relevant evaluation? (existential)
**Evidence motivating it:** persistence TSS 0.3029 (`artifacts/baseline_metrics.json`; generating script and split NOT PROVEN — must be regenerated reproducibly) vs V1 fixed-threshold TSS 0.2298; V1 operator-policy backtest TSS 0.3817 (`artifacts/operator_backtest.json`) is the only number above persistence and is not methodologically matched (hourly stride, suppression active, 30,106 windows vs the persistence evaluation's 1,707,349). Short-horizon persistence AUC reaches 0.89–0.99 (`artifacts/aditya_l1/persistence_validation_report.json` target_persistence_benchmarks), so autocorrelation-driven pseudo-skill is a live threat at 6 h too.
**Success criterion:** V1 (and any V4 candidate) exceeds persistence AND climatology on episode-level TSS and event recall with non-overlapping 95% block-bootstrap intervals, all three scored by the identical harness on the identical test episodes. A negative result triggers the documented contingency: reposition the system as calibrated-probability guidance plus the provenance/policy contribution, and make model improvement Phase D's sole focus.

### RQ2 — What operating point does an informed operator actually choose? (operator trust)
**Evidence:** the deployed red=0.95 yields zero RED alerts (`artifacts/operator_backtest.json`); the leaked-era 0.46/0.88 yielded 3.97% recall (`artifacts/operator_readiness_report.json`, INVALIDATED); nobody with operational accountability has ever chosen a miss-vs-false-alarm trade-off — the 6-hour horizon's actionability itself is an unvalidated assumption (`context/vision.md`, no requirements artifact).
**Success criterion:** a published cost-loss frontier (episode miss rate vs false-episode rate for cost ratios 2–20) with a recorded, named selection and its rationale; RED tier issues alerts at the chosen point with episode precision and recall both reported with intervals.

### RQ3 — Do SoLEXS/HEL1OS add predictive information on flare-bearing joint data? (SCI-001)
**Evidence:** ablation gap 0.0085 TSS (`scientific_validation_report.md` §6); conditional MI ≈ 0 (`artifacts/aditya_l1/incremental_information_audit.json`); joint corpus has zero flares (`artifacts/aditya_l1/overlap_dataset.parquet`); raw archive spans Oct 2023–Jun 2026 (`data/aditya_l1/processed/`), overlapping SC25 maximum, so flare-bearing joint intervals almost certainly exist unextracted — though SoLEXS saturation during large events is NOT PROVEN either way.
**Success criterion:** ≥10 M/X episodes inside verified joint coverage with per-event data-quality audit; pre-registered paired test (McNemar + paired block bootstrap, α=0.05) between GOES-only and fusion predictions on those episodes; verdict published regardless of direction, with the V3 integrate-or-retire ADR as its consequence.

### RQ4 — Are thresholds and calibration portable across the solar cycle? (SC24→SC25)
**Evidence:** train 0.62% positive vs test 23.20% (`artifacts/research_dataset_report.json`); pooled calibrated ECE 0.088 (`artifacts/calibration/calibration_report.json`) hides monthly structure; no walk-forward artifact exists.
**Success criterion:** monthly walk-forward evaluation over 2023–2026 (each month scored by calibrator/thresholds fit strictly on prior data): monthly ECE ≤ 0.10 and episode-metric drift bounds published; if violated, a rolling-recalibration procedure with governance rules is specified and backtested.

### RQ5 — Is MC-Dropout uncertainty informative, and can suppression tiers be earned rather than assumed?
**Evidence:** tiers 0.10/0.15/0.20 are hardcoded (`artifacts/policies/operator_policy_v2.json` tier_provenance); no artifact correlates std_prob with realized error.
**Success criterion:** measured relationship between MC-Dropout std and episode-level error rates; tiers re-derived on validation with positive marginal episode-level benefit per tier, or tiers removed; conformal prediction evaluated as the alternative with episode-aware coverage.

### RQ6 — What causes stealth-flare misses, and can they be reduced without post-flare false-alarm regression?
**Evidence:** FN cohort mean 3,489 minutes since last flare, attention entropy ≈ 1.0; FP cohort mean 441 minutes post-flare (`artifacts/model_failure_evidence_report.md`); naive decay suppression already produced negative gains (`artifacts/operator_trust_projection.json`).
**Success criterion:** stealth-stratum episode recall improves with overall episode precision degrading ≤ 2 points, measured on the RQ2 harness; candidate mechanisms (quiet-background-relative features, flare-location covariates per P28, HEL1OS precursors contingent on RQ3) tested as pre-registered ablations.

## Assumption audit

Every assumption V3 makes, implicitly or explicitly, with classification and evidence:

| # | Assumption | Classification | Evidence |
|---|------------|----------------|----------|
| A1 | GOES X-ray flux history carries usable 6-hour M/X signal | PARTIALLY VALIDATED | ROC-AUC 0.7485 on 1.8M test windows (`artifacts/evaluation_audit_report.json`) — discrimination exists; skill *over persistence* is RQ1 |
| A2 | The model beats trivial baselines | **UNVALIDATED, leaning FALSE at window level** | persistence TSS 0.3029 (`artifacts/baseline_metrics.json`) > V1 fixed-threshold TSS 0.2298; matched comparison absent |
| A3 | History features are legitimate signal, not persistence proxies | PARTIALLY VALIDATED | removing history collapses TSS to 0.0 (`artifacts/information_gap_report.json`); history-only achieves TSS 0.371 (`artifacts/signal_audit_report.json`) — consistent with *either* real precursor memory or persistence mimicry; RQ1 disambiguates |
| A4 | Chronological split prevents temporal leakage | VALIDATED | `artifacts/aditya_l1/train_test_boundary_audit.json` and `window_overlap_audit.json`, both PASS |
| A5 | Calibrator fit on validation only | VALIDATED | `scripts/calibrate_model.py` lines 191–202; `artifacts/operator_trust_audit.json` |
| A6 | Deployed thresholds derived without test data | VALIDATED (post-Sprint 23) | `artifacts/policies/operator_policy_v2.json` provenance + 9 startup checks (`artifacts/sprint23/Validation_Report.md`) |
| A7 | Isotonic calibration valid across the operating era | PARTIALLY VALIDATED | pooled test ECE 0.088 (`artifacts/calibration/calibration_report.json`); monthly stability NOT PROVEN |
| A8 | Validation-era (2020–22) thresholds transfer to SC25 operations | UNVALIDATED | regime gap 4.07% vs 23.20% positive (`PROJECT_STATUS.md` dataset inventory); no walk-forward artifact |
| A9 | MC-Dropout std predicts error | UNVALIDATED | no artifact; tiers hardcoded (`artifacts/policies/operator_policy_v2.json`) |
| A10 | Aditya-L1 instruments add information | UNVALIDATED, leaning FALSE | CMI ≈ 0 (`artifacts/aditya_l1/incremental_information_audit.json`); ablation gap 0.0085 (`scientific_validation_report.md` §6); zero-flare joint corpus |
| A11 | 6-hour horizon is operationally actionable for ISRO | UNVALIDATED | asserted in `context/vision.md`; no operator-requirements artifact exists |
| A12 | Window-level stride-1 metrics reflect operational performance | **FALSE** | 359/360 input overlap between adjacent windows; window recall 0.9286 vs honest episode-policy behavior differing drastically (`artifacts/evaluation_audit_report.json` vs `artifacts/operator_backtest.json`); i.i.d. bootstrap on these windows understates variance |
| A13 | `target_6hr_binary` labels are correct | UNVALIDATED | no label-audit artifact exists — NOT PROVEN |
| A14 | Single seed (42) is representative of V3 training variance | UNVALIDATED | only `artifacts/sprint14c/test_results_model_D_seed_42.json` exists |
| A15 | Archived predictions are reproducible | VALIDATED within platform, FALSE across platforms | SHA256-identical across 3 same-hardware runs; MPS-vs-saved max |Δ| 9.76e-4 (`scientific_validation_report.md` §3) |

**Program ordering follows consequence × uncertainty:** A2/A12 (Sprint 24), A8/A7 (Phase C), A10 (Phase B), A9 (Sprint 24–25), A3/A13/A14 (Phase D), A11 (operator elicitation attached to RQ2).

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Governing Version 4 planning document, written at V4 kickoff (Sprint 23.75 planning). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Master Plan

**V4's objective in one sentence: prove — under a single, episode-level, autocorrelation-honest evaluation harness — that AdityaNet forecasts M/X flares better than trivial persistence and delivers a functioning GREEN/YELLOW/RED alert policy whose error trade-offs an ISRO operator explicitly chose, because today neither of those things is established.**

The uncomfortable center of this plan: `artifacts/baseline_metrics.json` records a persistence baseline at TSS 0.3029 while the V1 model's fixed-threshold test evaluation records TSS 0.2298 (`artifacts/evaluation_audit_report.json`). The only V1 number that beats persistence is the operator-policy backtest (TSS 0.3817, `artifacts/operator_backtest.json`) — and those two evaluations are not methodologically matched (the persistence confusion matrix sums to 1,707,349 windows against the test set's 1,806,313; the generating script and split for `baseline_metrics.json` are NOT PROVEN in this session). Until model and persistence are scored by the same harness, on the same episodes, with block-bootstrap intervals, AdityaNet's core skill claim is unproven. V4 exists to make that claim true and provable — or to learn honestly that it is not.

## Scope and inheritance

V4 builds on frozen Version 3 (`artifacts/sprint23_5/VERSION3_FINAL_CERTIFICATE.md`): the leakage-free decision layer, the provenance-gated policy system, the clean baseline record, and 24 open items (`VERSION3_OPEN_RESEARCH.md`). No V3 artifact is modified by V4 work; V4 produces new, versioned artifacts measured against the V3 baseline.

## Problem classification

Every open issue from `artifacts/sprint23_5/VERSION3_LIMITATIONS.md` (L1–L15) and `VERSION3_OPEN_RESEARCH.md` (24 items), classified and statused with evidence:

| # | Issue | Class | V3 status | Evidence |
|---|-------|-------|-----------|----------|
| P1 | RED tier dormant (0 RED alerts at red=0.95) | OPERATOR DECISION | UNSOLVED | `artifacts/operator_backtest.json` alert_distribution RED: 0 |
| P2 | Model-vs-persistence superiority unestablished under matched conditions | RESEARCH | UNSOLVED (newly surfaced) | `artifacts/baseline_metrics.json` (persistence TSS 0.3029) vs `artifacts/evaluation_audit_report.json` (V1 TSS 0.2298); provenance of baseline file NOT PROVEN |
| P3 | Episode-level, block-bootstrap evaluation not the standard | RESEARCH | PARTIALLY SOLVED | Episode metrics computed once (`artifacts/operator_backtest.json` EventRecall); window bootstrap is i.i.d. (`app/services/ml/metrics.py::paired_bootstrap_test`) |
| P4 | Uncertainty tiers not data-derived | CALIBRATION | UNSOLVED | `artifacts/policies/operator_policy_v2.json` `tier_provenance: hardcoded_design_constants_sprint_5.5_not_data_derived` |
| P5 | Aditya-L1 incremental value unproven (SCI-001) | DATA + RESEARCH | UNSOLVED | `artifacts/aditya_l1/overlap_dataset.parquet` (4 days, 0 flares); `scientific_validation_report.md` §6 (ablation gap 0.0085 TSS); `artifacts/aditya_l1/incremental_information_audit.json` (conditional MI ≈ 0) |
| P6 | SC24→SC25 threshold/calibration portability (SCI-003) | CALIBRATION | UNSOLVED | positive rate 0.62%→23.20% (`artifacts/research_dataset_report.json`, `PROJECT_STATUS.md` dataset inventory); no walk-forward artifact exists |
| P7 | Stealth-flare false negatives | MODEL | UNSOLVED | `artifacts/model_failure_evidence_report.md` (FN mean 3,489 min since last flare; attention entropy ≈ 1.0) |
| P8 | Post-flare-decay false positives | MODEL | PARTIALLY EXPLORED — naive suppression already falsified | `artifacts/operator_trust_projection.json` (decay-suppression experiment: negative precision/recall gains) |
| P9 | Single-seed V3 evidence | TRAINING | UNSOLVED | only `artifacts/sprint14c/test_results_model_D_seed_42.json` |
| P10 | Temperature scaling collapse (TSS 0.000 at T=1.4168) | CALIBRATION | UNSOLVED (contained) | `scientific_validation_report.md` §2 |
| P11 | V3 model integrate-or-retire decision | MODEL + DEPLOYMENT | UNSOLVED (gated by P5) | `app/services/ml/inference.py` loads V1 only |
| P12 | model_v3.py defaults incompatible with checkpoint | MODEL | UNSOLVED (trivial) | `app/services/ml/model_v3.py` (25/10) vs sprint14c checkpoint shapes (18/4) |
| P13 | Conformal prediction unexplored | RESEARCH | UNSOLVED | no artifact |
| P14 | MC-Dropout std never validated as an error predictor | CALIBRATION | UNSOLVED | no artifact correlating std_prob with realized error |
| P15 | Cross-platform non-determinism (MPS ±9.76e-4) | DEPLOYMENT | PARTIALLY SOLVED (convention only) | `scientific_validation_report.md` §3 |
| P16 | Test coverage limited to policy layer | DEPLOYMENT | PARTIALLY SOLVED | `tests/` (15 + 1 tests); everything else 0% |
| P17 | No git | DEPLOYMENT | UNSOLVED | `MIGRATION_REPORT.md` line 39 |
| P18 | No CI/CD | DEPLOYMENT | UNSOLVED | absent |
| P19 | No application Dockerfile | DEPLOYMENT | UNSOLVED | `docker-compose.yml` covers DB/Redis only |
| P20 | No API authentication | DEPLOYMENT | UNSOLVED | `PROJECT_STATUS.md` Backend Status table |
| P21 | No real-time ingestion scheduler | DATA + DEPLOYMENT | UNSOLVED | backfill scripts only (`app/services/backfill/`) |
| P22 | No frontend/dashboard | DEPLOYMENT + EXPLAINABILITY | UNSOLVED | `PROJECT_STATUS.md` Frontend Status: ABSENT |
| P23 | No monitoring/drift detection | DEPLOYMENT + CALIBRATION | UNSOLVED | absent |
| P24 | Diffuse attention makes FN explainability uninformative | EXPLAINABILITY | UNSOLVED | `artifacts/model_failure_evidence_report.md` (entropy ≈ 1.0) |
| P25 | Provenance-constant maintenance is manual | DEPLOYMENT | PARTIALLY SOLVED | constants exist in `app/services/ml/policy.py`; no process |
| P26 | Documentation-staleness detection is manual | DEPLOYMENT | PARTIALLY SOLVED | Sprint 23.5 sweep done by hand; no lint |
| P27 | 6-hour horizon operational actionability | RESEARCH | UNSOLVED — assumption, no operator evidence | asserted in `context/vision.md`; no requirements artifact |
| P28 | Flare-location blindness (X-ray flux only; no disk position) | DATA + MODEL | UNSOLVED (newly surfaced in adversarial review) | feature manifest `artifacts/feature_columns.json` contains no positional feature |

## Contribution positioning (from adversarial review)

V4's defensible contributions, in order of strength: (1) an operationally honest alerting system with provable provenance — the leakage discovery, structural remediation, and cost-loss policy design are a genuine systems-for-science contribution; (2) a rigorous negative-or-positive verdict on multi-instrument L1 X-ray fusion for flare forecasting — publishable either way once the joint corpus exists; (3) forecast skill improvements — only claimable after P2 is settled. Chasing (3) before (1) and (2) repeats V3's central mistake of building sophistication on an unproven yardstick.

## Governing principles

1. **One yardstick.** Every model, baseline, and policy is scored by the same episode-level harness with block-bootstrap intervals. No number enters a report from any other path.
2. **Baselines before architecture.** Nothing about model architecture is decided until persistence and climatology are on the yardstick.
3. **Operators choose trade-offs.** The cost ratio behind the alert policy is an explicit, recorded operator decision, not an optimizer artifact (frontier published; choice documented).
4. **Provenance or it does not ship.** The Sprint 23 policy gates extend to every V4 artifact class (models, calibrators, datasets).
5. **NOT PROVEN is a valid answer.** Where evidence is absent, documents say so.

## Phase overview (detail in VERSION4_SPRINT_ROADMAP.md)

Phase A — Honest Yardstick and Decision Layer (Sprints 24–25) → Phase B — Settle the Instruments (Sprints 26–27, parallelizable with C) → Phase C — Regime Robustness (Sprints 27–28) → Phase D — Model Science (Sprints 29–31) → Phase E — Operational Pilot (Sprints 32+). The single recommended next sprint is specified in `VERSION4_FIRST_SPRINT.md`.

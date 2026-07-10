<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Definition of Version 4 completion across operator trust, scientific validity, and deployment readiness. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Success Metrics

**Conclusion:** Version 4 is complete when three pillars each clear their gates: an operator can trust the alerts (a RED tier that fires at a trade-off the operator chose, with live behavior matching backtest), a reviewer can trust the science (matched baselines beaten or the negative result formally adopted; every V3 assumption resolved from UNVALIDATED), and an engineer can trust the deployment (30-day shadow run through provenance-gated infrastructure). TSS appears below only once, and only relative to persistence — a deliberate demotion of leaderboard metrics per the sprint brief.

## Pillar 1 — Operator trust (primary)

| Gate | Definition of done | Baseline today (evidence) |
|------|--------------------|---------------------------|
| OT-1 Functioning RED tier | RED alerts issued at an operating point selected from the published cost-loss frontier by a named decision-maker, with the choice and rationale recorded in the policy artifact | RED alerts in backtest: 0 (`artifacts/operator_backtest.json`) |
| OT-2 Honest error budget | Episode-level false-episode rate and missed-episode rate at the chosen point, each with 95% block-bootstrap intervals, published and re-confirmed monthly in shadow operation | single hourly backtest, i.i.d.-window CIs only (`artifacts/bootstrap_metrics.json`) |
| OT-3 Earned uncertainty handling | Every suppression tier demonstrates positive marginal episode-level benefit, or is removed; no unexplained constants in the deployed policy | tiers hardcoded (`artifacts/policies/operator_policy_v2.json` tier_provenance) |
| OT-4 Lead-time transparency | Lead-time distribution (not just the mean) per alert tier published with the policy | single mean value, leaked-era provenance (`artifacts/operator_readiness_report.json`, INVALIDATED) |
| OT-5 Live consistency | 30 consecutive shadow-mode days with live episode metrics inside the backtest confidence bounds | no live operation exists (`PROJECT_STATUS.md` Backend Status: scheduler ABSENT) |
| OT-6 Provenance at the surface | Every alert response carries policy_id + provenance summary; operator can trace any alert to its policy, calibrator, and dataset fingerprints | service exposes metadata internally (`app/services/ml/inference.py` policy_metadata) but the API response does not surface it |

## Pillar 2 — Scientific validity

| Gate | Definition of done | Baseline today (evidence) |
|------|--------------------|---------------------------|
| SV-1 Beats trivial forecasting | Episode-level TSS and event recall exceed BOTH persistence and climatology with non-overlapping 95% block-bootstrap intervals on the matched harness — or the negative result is formally adopted with the RQ1 contingency | NOT ESTABLISHED: persistence 0.3029 vs model 0.2298 unmatched (`artifacts/baseline_metrics.json`, `artifacts/evaluation_audit_report.json`) |
| SV-2 Instrument verdict | SCI-001 answered at α = 0.05 on ≥ 10 joint flare episodes, or impossibility documented; V3 integrate-or-retire ADR filed | zero joint flare episodes (`artifacts/aditya_l1/overlap_dataset.parquet`) |
| SV-3 Regime bounds | Monthly walk-forward ECE ≤ 0.10 across 2023–2026, or an adopted rolling procedure achieving it in backtest | pooled ECE only (`artifacts/calibration/calibration_report.json`) |
| SV-4 Assumption ledger closed | All 15 audited assumptions (`VERSION4_RESEARCH_PROGRAM.md`) classified VALIDATED, FALSE-and-mitigated, or ACCEPTED-LIMITATION — zero remaining UNVALIDATED | 7 UNVALIDATED, 2 FALSE today |
| SV-5 Variance known | Multi-seed variance for any model whose numbers are published; label audit for `target_6hr_binary` completed | single seed (`artifacts/sprint14c/test_results_model_D_seed_42.json`); no label audit |
| SV-6 Provenance-complete artifacts | Every published number regenerable from a provenance-stamped artifact chain (the Sprint 23 gate discipline extended to models and datasets) | policy layer only (`artifacts/sprint23/Policy_Architecture.md`) |

## Pillar 3 — Deployment readiness

| Gate | Definition of done | Baseline today (evidence) |
|------|--------------------|---------------------------|
| DR-1 Live data | Automated GOES ingestion with gap-handling policy; ≥ 99% scheduler uptime over the shadow month | manual backfill only (`app/services/backfill/`) |
| DR-2 Access control | Authenticated API before any non-local exposure | none (`PROJECT_STATUS.md` Backend Status) |
| DR-3 Reproducible service | Application Dockerfile; deployment resolves the policy dataset-fingerprint requirement (risk R15) | compose covers DB/Redis only |
| DR-4 Safety net | Test coverage on the full inference path (features → model → calibration → policy → response) + CI running it on change; git with remote | 16 tests, policy layer only; no git (`MIGRATION_REPORT.md` line 39) |
| DR-5 Latency budget | Defined nowcast latency SLO, measured; 50-pass MC-Dropout cost known (risk R14) | NOT PROVEN — no measurement exists |
| DR-6 Drift watch | Phase C monitoring curves computed live, alerting on bound violation | none |

## What "V4 complete" is NOT

Not a TSS target hit in isolation; not a leaderboard placement; not feature count. A V4 that honestly concludes "GOES-history models plateau near persistence-plus-epsilon at 6 hours; here is a calibrated, provenance-perfect, operator-tuned system at that ceiling, live for 30 days" **passes**, provided SV-1's contingency was formally adopted. A V4 with a higher TSS that cannot show matched baselines, episode-level intervals, and live consistency **fails**.

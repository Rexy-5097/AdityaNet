# Sprint 23 — Scientific Integrity Report

**Conclusion:** As of this sprint, every number the production system can produce is traceable to validation-derived decisions, and the proven-leaked configuration is both physically archived and structurally unloadable. The integrity restoration is complete for the decision layer; it does **not** retroactively repair the historical record (Sprint 5.5/10K/14B artifacts still contain void numbers) and does not resolve the independent scientific issues (SC24→SC25 shift, Aditya-L1 null-benefit question) — those remain open and documented.

## Integrity state: before vs after

| Question | Before Sprint 23 | After Sprint 23 |
|----------|------------------|-----------------|
| Where do production thresholds come from? | Test-split sweep, proven (`sprint22_5/04_leakage_proof.md`, all four conditions CONFIRMED) | Validation-only sweep (Sprint 5.6), verified stamps + fingerprint, honest backtest on record |
| Can that be verified at runtime? | No — raw `json.load`, zero provenance | Yes — 9 startup checks incl. recomputed dataset SHA256 and generator hash; abort on failure |
| Can a test-derived policy return? | Nothing prevented it | Five layers reject it; 6/6 rejection pathways demonstrated (Gate 4); 15 regression tests pin the behavior |
| Is the incident preserved? | At risk of silent overwrite | Quarantined with evidence continuity (pre-injection SHA256 recorded); README documents the incident |
| Are the operator metrics honest? | Trust 0.524 / precision 91.1% / recall 4.0% — void (thresholds evaluated on their own selection data) | TSS 0.382 / Recall 0.723 / EventRecall 0.696 / ~6.9 false episodes/month (`operator_backtest.json`, thresholds never saw the evaluation data) with bootstrap CIs (`bootstrap_metrics.json`) |

## What a submission may now claim (and cite)

- Threshold-free model quality: ROC-AUC 0.7485, PR-AUC 0.4950, calibrated ECE 0.088 (`calibration_report.json` — calibrator validation-fit, `calibrate_model.py:191–202`).
- Val-tuned-threshold test evaluation: TSS 0.2298 @ 0.3367 (`evaluation_audit_report.json`, triple-verified).
- Operator-level, leakage-free: the backtest numbers above, at the deployed 0.14/0.95 policy.
- Process claim: the leak was detected, proven with exact reproduction, quarantined, and structurally prevented — with runnable gates as evidence (`sprint22_5/`, `sprint23/`).

## What remains scientifically outstanding (unchanged by this sprint)

1. **RED tier dormant** at red=0.95 (0 RED alerts in backtest) — successor policy (Sprint 22 Variant B, cost-loss + episode-level) is the fix; requires operator cost-ratio input.
2. **Validation↔test regime gap** — thresholds derive from 2020–2022 (4.07% positive) and operate in SC25 conditions; Sprint 22 Phase 3 (walk-forward recalibration backtest) addresses threshold portability.
3. **Uncertainty tiers not data-derived** — carried Sprint 5.5 constants, now labelled; derivation is Sprint 22 WP4.
4. **Historical record uncorrected** — `PROJECT_STATUS.md`, `context/workflow.md` Rule 3, `context/memory.md`, `context/architecture.md`, Sprint 10K/14B publication artifacts still cite void numbers (blast radius: `sprint22_5/05_impact_analysis.md`); a documentation sweep is follow-up work, deliberately not smuggled into a code sprint.
5. **Aditya-L1 benefit (SCI-001) and SC24→SC25 shift (SCI-003)** — untouched, by scope.
6. **Window-level metric autocorrelation** — the honest backtest uses hourly stride (better), but episode-level block-bootstrap as the standard harness is Sprint 22 WP3.

## Process integrity note

Sprint 22.5 established that this repository once *detected* this exact leak (Sprint 5.6 built the fix; `operator_trust_audit.json` recorded `test_data_used_for_optimization: true`) and then failed to deploy the correction. Sprint 23's structural difference is that correctness is no longer a matter of remembering: the default production path *is* the gated path, and regression tests + startup aborts replace institutional memory. The remaining single point of failure is human: the fingerprint blocklist and expected-split constants in `policy.py` must be maintained as datasets evolve.

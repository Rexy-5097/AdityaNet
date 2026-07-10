<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Known limitations of frozen Version 3 as a research baseline. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Known Limitations

**Conclusion:** Frozen Version 3 is scientifically honest but operationally and scientifically limited: it is a GREEN/YELLOW-only forecaster whose thresholds derive from a quieter solar regime than the one it forecasts, whose flagship multi-instrument hypothesis remains unproven, and whose engineering hardening covers only the policy layer. Each limitation is stated with evidence and carries a `[V4]` tag where it defines follow-on work (catalogued in `VERSION3_OPEN_RESEARCH.md`).

## Scientific limitations

1. **RED tier dormant.** red=0.95 produced zero RED alerts in the honest backtest (`artifacts/operator_backtest.json`, alert_distribution RED: 0); the RED confirmation chain and coincidence filter never execute. Version 3 cannot issue its highest-severity alert in practice. `[V4]`
2. **Regime gap between threshold derivation and operation.** Thresholds derive from 2020–2022 validation (4.07% positive); the operational era (SC25 maximum, test split 23.20% positive) differs by ~6×. Threshold portability across the cycle is unquantified — no walk-forward backtest exists. `[V4]`
3. **Aditya-L1 incremental value unproven (SCI-001).** GOES-only ablation reaches 97.9% of the full V3 model's TSS (0.4046 vs 0.4131, `scientific_validation_report.md` §6); conditional mutual information of SoLEXS/HEL1OS features given GOES ≈ 0; the only joint aligned corpus is 4 days with zero flares (`artifacts/aditya_l1/overlap_dataset.parquet`). The flagship multi-instrument claim cannot be asserted. `[V4]`
4. **Uncertainty suppression tiers are not data-derived.** 0.10/0.15/0.20 are Sprint 5.5 hardcoded constants, honestly labelled in the policy's `tier_provenance` but never validated against realized error rates. `[V4]`
5. **Window-level metrics are autocorrelated.** Stride-1 windows share 359/360 of their input; i.i.d. bootstrap CIs understate variance. The operator backtest mitigates via hourly stride, but episode-level block bootstrap is not the standard harness. `[V4]`
6. **Single-seed V3 evidence.** The research model's results rest on seed 42 alone; no variance estimate across seeds exists. `[V4]`
7. **Cross-platform non-determinism.** MPS inference deviates up to 9.76e-4 from archived predictions (`scientific_validation_report.md` §2–3); archived arrays are canonical, hardware must be pinned for certification. `[V4]`
8. **Temperature scaling anomaly unexplained.** T=1.4168 yields TSS=0.000 on the V3 test set; isotonic is used, but an unexplained calibration-component failure remains on the record. `[V4]`
9. **Stealth-flare failure mode untreated.** False negatives cluster in quiet backgrounds (mean 3,489 minutes since last flare) with near-uniform attention entropy; false positives cluster in post-flare decay (`artifacts/model_failure_evidence_report.md`). No mitigation attempted. `[V4]`
10. **Historical record annotated, not corrected.** Sprint 5.5/10K/14B artifacts and older reports retain void leaked-policy numbers beneath VERSION STATUS annotations — readable for traceability, but any citation must go through `VERSION3_SCIENTIFIC_BASELINE.md`.

## Engineering limitations

11. **model_v3.py default parameters incompatible with its own trained checkpoint** (`n_features_solexs=25` vs 18; `n_features_hel1os=10` vs 4) — loading with defaults raises a shape mismatch; not production-critical because V3 is not deployed, but a landmine for V4 work. `[V4]`
12. **Test coverage limited to the policy layer** (15 regression + 1 integration test); model, features, dataset builders, API handlers, and alert-logic behavior are untested by automation. `[V4]`
13. **No git, no CI/CD, no application Dockerfile, no authentication, no real-time ingestion, no frontend, no monitoring** — enumerated with consequences in `VERSION3_DEPLOYMENT_BASELINE.md`. `[V4]`
14. **Provenance constants require maintenance.** The leaked-fingerprint blocklist and expected-split identifier in `app/services/ml/policy.py` are the human-maintained heart of the leakage defence; new splits or rebuilt datasets require deliberate updates. `[V4]`
15. **Sprint self-reporting was historically unreliable** (Sprint 20B summary claimed PASS against an audit FAIL; Sprint 5.6's computed fix went undeployed for 18 days). Sprint 23 replaced memory with structural gates for the policy layer only; other subsystems still rely on discipline. `[V4]`

## What these limitations do NOT undermine

The frozen baseline's headline numbers (`VERSION3_SCIENTIFIC_BASELINE.md`) are leakage-free, provenance-verified, and reproducible from archived artifacts; the chronological split integrity is audited PASS; the calibrator is validation-fit in verified code. Version 3 is a *trustworthy* baseline — the limitations bound its *scope*, not its honesty.

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Open questions and improvement opportunities carried out of frozen Version 3. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Open Research and Improvement Register

**Conclusion:** Twenty-four open items carry forward out of frozen Version 3, each tagged `[V4]` with a one-sentence description. Per the Sprint 23.5 brief these are identified only — no design, planning, or implementation belongs in this document.

## Scientific

- `[V4]` **Cost-loss operator policy with a functioning RED tier** — replace the dormant red=0.95 stopgap with episode-level, operator-cost-ratio-driven threshold selection (the Sprint 22 "Variant B" concept).
- `[V4]` **Settle SCI-001 (Aditya-L1 incremental value)** — extend the joint GOES+SoLEXS+HEL1OS aligned corpus backward from the existing raw archive until it contains enough M/X flare episodes for a paired significance verdict.
- `[V4]` **SC24→SC25 threshold and calibration portability (SCI-003)** — walk-forward recalibration backtest across the 2023–2026 era to quantify and mitigate solar-cycle regime drift.
- `[V4]` **Data-derived uncertainty suppression tiers** — replace the hardcoded 0.10/0.15/0.20 constants with tiers validated against realized episode-level error rates.
- `[V4]` **Episode-level block-bootstrap evaluation harness as standard** — make episode metrics with autocorrelation-aware confidence intervals the default yardstick instead of stride-1 window metrics.
- `[V4]` **Stealth-flare false-negative mitigation** — attack the quiet-background missed-flare mode (precursor-sensitive features or a quiet-regime branch), measured on the documented FN cohort.
- `[V4]` **Post-flare-decay false-positive mitigation** — reduce alerts triggered by residual decay flux, without trading away stealth-flare recall.
- `[V4]` **Multi-seed variance for the V3 research model** — rerun the sprint14c protocol across seeds to bound the single-seed (42) uncertainty.
- `[V4]` **Temperature-scaling failure forensics** — explain why T=1.4168 collapses TSS to 0.000 on the S2 test set.
- `[V4]` **Conformal prediction for coverage-guaranteed alerting** — evaluate distribution-free prediction sets as a successor or complement to MC-Dropout suppression.
- `[V4]` **V3 model production decision** — integrate the multi-instrument model into the inference service or formally retire it, contingent on the SCI-001 verdict.
- `[V4]` **Baseline comparisons for publication** — benchmark against persistence, climatology, and the NOAA operational forecast, which no current artifact does.

## Engineering

- `[V4]` **Fix model_v3.py default parameters** — align `n_features_solexs`/`n_features_hel1os` defaults (25/10) with the trained checkpoint (18/4) so naive loads stop raising shape mismatches.
- `[V4]` **Broaden the automated test suite** — extend coverage from the policy layer to features, dataset construction, model forward pass, alert logic, and API handlers.
- `[V4]` **Initialize git version control** — replace file-hash provenance substitutes with commit-pinned history and enable rollback.
- `[V4]` **CI/CD pipeline** — run the test suite and quality gates automatically on change.
- `[V4]` **Application Dockerfile and deployment packaging** — containerize the FastAPI service alongside the existing TimescaleDB/Redis compose services.
- `[V4]` **API authentication and authorization** — gate `/predict/nowcast` and administrative endpoints before any external exposure.
- `[V4]` **Real-time ingestion scheduler** — automate GOES (and Aditya-L1/PRADAN) data flow so the service can operate live rather than on manual backfills.
- `[V4]` **Operator frontend/dashboard** — a human interface for alerts, provenance display, and episode review.
- `[V4]` **Operational monitoring and drift detection** — track calibration ECE, alert rates, and input-distribution drift in production.
- `[V4]` **Deterministic evaluation pinning** — codify the archived-predictions-are-canonical convention and a pinned-hardware certification path for MPS float variance.
- `[V4]` **Provenance-constant maintenance process** — a checked procedure for updating the leaked-fingerprint blocklist and expected-split identifiers when datasets evolve.
- `[V4]` **Documentation debt automation** — a lint-style check that flags documents citing superseded metrics without a VERSION STATUS annotation, so reconciliation cannot silently regress.

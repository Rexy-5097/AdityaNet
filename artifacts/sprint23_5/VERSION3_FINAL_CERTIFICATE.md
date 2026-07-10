<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Formal closure certificate freezing Version 3 as the permanent research baseline. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Final Certificate

**Declaration:** Version 3 of SuryaNet/AdityaNet is complete and frozen as the permanent research baseline for the ISRO submission, effective Sprint 23.5, 2026-07-03. Its performance record is `VERSION3_SCIENTIFIC_BASELINE.md` (clean-policy numbers only); its deployment state is `VERSION3_DEPLOYMENT_BASELINE.md`; its history is `VERSION3_SCIENTIFIC_TIMELINE.md` and `VERSION3_CHANGELOG.md`; its boundaries are `VERSION3_LIMITATIONS.md`; everything it leaves open is `VERSION3_OPEN_RESEARCH.md`.

## What Version 3 is

A 6-hour-ahead M/X-class solar flare forecasting platform: V1 PatchTST (822,401 parameters, 16-year GOES training base) with validation-fit isotonic calibration, MC-Dropout uncertainty, and a provenance-gated GREEN/YELLOW operator alert policy (yellow=0.14, red=0.95, validation-derived), served by FastAPI over TimescaleDB/Redis; plus a non-deployed multi-instrument research model (LateFusionPatchTST, GOES+SoLEXS+HEL1OS) with a complete audited evaluation record.

## Resolved within Version 3

1. **Operator-policy test-set leakage** — proven with exact six-decimal reproduction (`artifacts/sprint22_5/FINAL_VERDICT.md`: LEAKAGE PROVEN, conditions A–D all CONFIRMED), corrected structurally (Sprint 23), and reconciled documentarily (Sprint 23.5).
2. **Decision-layer provenance** — every deployed policy now carries 13 mandatory provenance fields, self-hash integrity, and passes nine startup checks including recomputed dataset and generator hashes; five leakage-rejection layers verified (6/6 pathways, `artifacts/sprint23/Validation_Report.md`).
3. **Quarantine with evidence continuity** — the leaked policy and its sweep are archived, marked `LEAKED_TEST_DERIVED`, structurally unloadable, and hash-traceable (`artifacts/archive/README.md`).
4. **Honest operator baseline** — TSS 0.3817 [0.3689, 0.3933], recall 0.7227, event recall 0.6963, ~6.9 false episodes/month at the deployed thresholds, with the derivation-evaluation separation verified.
5. **First automated tests** — 15 regression tests plus a real-stack integration test, all green with output on record.
6. **Governance** — AgentOS v1.0.0 at 100/100; split-integrity audits PASS; calibration provenance verified clean in code.

## Explicitly NOT resolved (carried to V4 — see VERSION3_OPEN_RESEARCH.md)

The RED alert tier is dormant at red=0.95 (zero RED alerts in backtest); the Aditya-L1 multi-instrument benefit is unproven (SCI-001: 4-day joint corpus, zero flares); solar-cycle regime drift between threshold derivation (2020–2022) and operation (SC25) is unquantified (SCI-003); uncertainty tiers are hardcoded design constants; test coverage stops at the policy layer; frontend, authentication, real-time ingestion, application containerization, CI/CD, and git are absent; historical Sprint 5.5/10K/14B artifacts retain void numbers beneath annotations by design.

## Citation rule for the frozen baseline

Any external claim about Version 3 performance must cite `artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md`. The numbers trust score 0.524, precision 91.12%, recall 3.97%, and thresholds yellow=0.46/red=0.88 are void wherever they appear and are never citable as Version 3 performance.

## Closure

Version 3 opened with the V1 training run of 2026-06-15 and closes with Sprint 23.5 on 2026-07-03: implementation (Sprints 5–14c), audit (15a–20b, 22), proof (22.5), correction (23), reconciliation (23.5). This certificate is the final Version 3 artifact.

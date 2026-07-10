# Project Vision — SuryaNet / AdityaNet

> **Owner:** Soumyadeb Tripathy
> **Update Frequency:** Major pivots only
> **Cross-refs:** `context/architecture.md` · `context/state.md`

---

## Problem Statement

Satellite operators at ISRO have no domestic, scientifically rigorous, 6-hour-ahead solar flare
forecast with calibrated probability and epistemic uncertainty. The NOAA SWPC forecast is foreign
and not integrated with Aditya-L1 observations. A missed M/X-class flare can cause satellite upsets,
communication outages, and radiation damage to missions in LEO and GEO.

---

## Objectives

| # | Objective | Priority | Success Metric |
|---|-----------|----------|----------------|
| 1 | Forecast M/X-class flares 6 hours ahead with TSS ≥ 0.38 | Critical | TSS on held-out SC25 test set |
| 2 | Provide calibrated probability + epistemic uncertainty (MC Dropout) | Critical | ECE ≤ 0.10 post-calibration |
| 3 | Issue GREEN / YELLOW / RED operator alerts with ≤ 10% false episode rate | Critical | Episode-level evaluation on test set |
| 4 | Incorporate Aditya-L1 SoLEXS + HEL1OS instruments | High | TSS improvement over GOES-only baseline |
| 5 | Serve real-time inference via FastAPI + TimescaleDB | High | Latency ≤ 2s per nowcast request |
| 6 | Be scientifically trustworthy enough for ISRO operational use | High | Independent validation report PASS |

---

## Success Criteria

| Criterion | How to Measure | Target | Deadline |
|-----------|----------------|--------|----------|
| Model TSS (production threshold) | `artifacts/evaluation_audit_report.json` | ≥ 0.38 | Current: 0.230 at threshold 0.337; 0.381–0.393 at operator thresholds |
| Calibration ECE | Post-calibration ECE on test set | ≤ 0.10 | Current V1: 0.088 ✅ |
| PR-AUC | Area under precision-recall curve | ≥ 0.45 | Current V1: 0.495 ✅ |
| False episode rate | False alarm episodes per month | ≤ 10% | Current: 9.1% ✅ |
| Aditya-L1 benefit | V3 TSS vs GOES-only ablation | Statistically significant | UNRESOLVED — SCI-001 |
| API latency | p99 latency for /predict/nowcast | ≤ 2 seconds | Not benchmarked yet |
| Test coverage | Unit + integration tests | ≥ 80% coverage on inference path | 0% — GAP-001 |

---

## Stakeholders

| Role | Name / Group | Interest | Decision Authority |
|------|-------------|----------|--------------------|
| Project Lead | Soumyadeb Tripathy | Delivery, science, engineering | All decisions |
| End Users (Target) | ISRO Satellite Operators | Reliable alerts, low false alarms | Feature validation |
| Scientific Reviewers | External/Independent | Scientific methodology validity | Publication gating |
| Instruments | ISRO Aditya-L1 / SoLEXS / HEL1OS | Data availability | Data feed reliability |

---

## Scope

**In Scope:**
- GOES XRS 1-minute cadence X-ray flux forecasting (14 engineered features, 16-year archive)
- Aditya-L1 SoLEXS (18 features) and HEL1OS (4 features) fusion (when available post-2023)
- V1 PatchTST model (production) — GOES-only, 822K parameters
- V3 LateFusionPatchTST model (research) — multi-instrument, 4.35M parameters
- Monte Carlo Dropout uncertainty quantification (50 forward passes)
- Isotonic regression calibration
- Tiered operator alert system (GREEN/YELLOW/RED) with uncertainty suppression and RED confirmation
- FastAPI backend with TimescaleDB and Redis
- ISRO mission-specific impact assessment

**Out of Scope (Non-Goals):**
- CME forecasting (different physical phenomenon)
- Proton event forecasting
- Solar wind forecasting
- Any instrument other than X-ray (no EUV, no magnetogram, no radio)
- Frontend / dashboard (absent — GAP-002)
- Prediction beyond 6-hour horizon
- Retrospective event reconstruction

---

## Constraints

| Type | Constraint | Impact |
|------|-----------|--------|
| Data | Aditya-L1 real-time feed requires PRADAN/ISAC connection | No automated ingestion yet — GAP-005 |
| Science | Only 4 days of GOES+Aditya-L1 joint data (zero flare events) | SCI-001 cannot be resolved until joint flares observed |
| Distribution | SC24 training (0.62% positive) vs SC25 test (23.2% positive) | Calibration and thresholds may drift across solar cycle |
| Compute | Apple M4 MPS only (no CUDA) | Training slower; inference non-deterministic across hardware platforms |
| Engineering | No git history, no CI/CD, no test suite | Regressions may go undetected — GAP-001, GAP-006, GAP-008 |
| Security | No API authentication | Cannot expose to external operators — GAP-003 |

---

## Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| SoLEXS/HEL1OS provide no statistically significant benefit | High (ablation shows TSS gap of 0.008) | High — invalidates V3 scientific rationale | Collect joint flare data; if null result, pivot to V1-only | Soumyadeb |
| Solar Cycle 25 peak causes threshold drift | High (SC25 far more active than SC24) | High — operational alerts degraded | Monitor calibration ECE monthly; re-calibrate per cycle | Soumyadeb |
| Calibration leakage (test data used to fit isotonic regressor) | Medium | Critical — invalidates all published metrics | Audit calibration data provenance (SCI-002) | Soumyadeb |
| No test suite means silent regressions | High (0 tests exist) | High | Add integration tests for inference path immediately (GAP-001) | Soumyadeb |

---

## Assumptions

- GOES XRS data continues at 1-minute cadence with < 1% gap rate
- Aditya-L1 will continue producing SoLEXS and HEL1OS data through the project
- M/X-class flare events will occur during SC25 peak that are observable jointly by GOES and Aditya-L1
- ISRO mission impact definitions in `app/services/operations/impact.py` are correct
- The 6-hour forecast horizon is operationally actionable for satellite operators

---

*Last updated: 2026-07-03 by Soumyadeb Tripathy (AgentOS onboarding). Next review: First joint flare event observed.*

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 1 — missing-data structure and gap-policy accounting. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 31 — Missing Data Report (dataset_v4.1.0-s2)

**Headline (OBSERVED): the "SoLEXS is down one quarter of the time" concern dissolves under per-minute analysis — the 24.4% unavailability consists entirely of micro-gaps (median 1 minute, maximum 9 minutes across 145,006 gap runs in train), so 100% of masked minutes fall inside the pre-registered ≤15-minute forward-fill regime. After the §2 gap policy, feature-level availability is 99.9997% with mean staleness 0.32 minutes, and the normalized-space neutral-imputation path processed only 48/32/40 cells (train/validation/test) — all leading-edge derivative NaNs, none instrument gaps.**

## Raw missingness (OBSERVED from the frozen builder masks)

| Instrument / split | Observed fraction | Gap runs | Run length p50/p90/p99/max | Masked minutes in runs ≤ 15 |
|--------------------|-------------------|----------|----------------------------|------------------------------|
| SoLEXS train | 0.7563 | 145,006 | 1 / 2 / 4 / 9 | 191,623 of 191,623 (100.0%) |
| SoLEXS validation | 0.7560 | (same structure) | — | 100.0% |
| SoLEXS test | 0.7568 | (same structure) | — | 100.0% |
| HEL1OS train | 0.99976 | 191 | 1 / 1 / 1 / 1 | 100.0% |
| HEL1OS val/test | 0.9998 / 0.9997 | — | — | 100.0% |

The raw parquets ZERO-FILL these minutes (SoLEXS rates read 0.0 against a genuine minimum of 150; HEL1OS 0.0 against a minimum of 5.0) — the exact out-of-manifold defect Sprint 27 documented (`artifacts/sprint27/01_ADITYA_FEATURE_AUDIT.md` §2). The V4 build replaces every zero-filled minute with NaN before any feature computation; no feature ever ingests a fake zero.

## Gap-policy accounting (§2, OBSERVED)

| Quantity | train | validation | test |
|----------|-------|------------|------|
| Post-ffill feature availability | 99.99975% | ≈ same | ≈ same |
| Long-gap (> 15 min) NaN fraction | 2.5×10⁻⁶ | ≈ 0 | ≈ 0 |
| Mean staleness (min, capped 60) | 0.322 | ≈ same | ≈ same |
| Neutral-imputed cells (of split × 32 features) | 48 | 32 | 40 |

## Disclosure to the model (§3, OBSERVED)

Missingness is not hidden by the fill: `solexs_available` / `hel1os_available` (binary, observed-not-filled semantics) and `solexs_staleness_n` / `hel1os_staleness_n` (staleness/60 ∈ [0,1]) are model input channels 33–36, so F2 sees exactly which minutes are measurements and how stale each filled value is.

## Consequence pre-declared for Phase 5 stratification

Because the micro-gaps are scattered nearly uniformly, every 360-minute window has SoLEXS availability_fraction ≈ 0.756 and staleness ≈ 0.32 min — per-window quality (§5 formula) concentrates near 0.75 for essentially all windows. The pre-registered strata (quality ≥ 0.9 vs < 0.9) are therefore expected to be degenerate (one empty stratum), and "Aditya present vs absent" (availability ≥ 0.5) likewise (~all present). Phase 5 computes and reports the actual stratum populations; if degenerate, that is reported as the measured fact — the stratification question ("is performance availability-dependent?") is unanswerable on this span because availability has no variance, and that itself is a finding.

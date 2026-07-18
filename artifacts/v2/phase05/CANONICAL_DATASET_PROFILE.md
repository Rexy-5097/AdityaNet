<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Canonical dataset profile — descriptive engineering inventory (M-VII deliverable). -->
<!-- DATE: 2026-07-17 -->

# Canonical Dataset Profile

**Descriptive only.** This document is an engineering inventory of the canonical dataset produced by the Milestone VII build under contract r5. It records counts and statistics; it interprets nothing. Quantities marked **[A-14]** or **[M-VIII]** are unexplained by design and await Milestone VIII.

Build: `scripts/v2/phase05/build_canonical.py`, 93.75 min. Store: `artifacts/v2/phase05/canonical/`.

## 1. Row counts

| Table | Files | Rows |
|---|---|---|
| T1 `solexs_lc_1min` | 424 | 610,560 |
| T2 `solexs_spec_1min` | 424 | 610,560 |
| T3 `hel1os_lc_1min` | 373 | 1,027,773 |
| T4 `hel1os_hk_1min` | 389 | 277,054 |
| T5 `hel1os_spec_1min` | 373 | 1,026,816 |
| T6 `gti_intervals` | 1 | 2,130 |
| T7 `provenance_manifest` | 1 | 5,199 |

## 2. Date coverage

| Table | First | Last |
|---|---|---|
| T1/T2 (SoLEXS) | 2024-02-01 00:00:00+00:00 | 2026-06-15 23:59:00+00:00 |
| T3 (HEL1OS LC) | 2025-12-07 00:00:00+00:00 | 2026-06-17 23:59:00+00:00 |
| T4 (HEL1OS HK) | 2025-12-07 00:00:00+00:00 | 2026-06-17 23:59:00+00:00 |

## 3. Missing-value statistics

- **T1** `counts_total`: 25,623 NaN of 610,560 rows (4.20%). `q_no_data` minutes: 25,623; `q_partial`: 2,063.
- **T2**: `q_no_data` minutes: 25,623 of 610,560. Channel arrays preserve NaN per the r2/r5 rules; never imputed.
- **T3** band-rate cells: 15,418,723 NaN of 20,555,460 (75.01%) across 20 band columns.
- No imputation, filling, or interpolation exists anywhere in the pipeline (verified by test suite).

## 4. GTI coverage (T6)

- Intervals: 2,130 ({'solexs': 2130})
- Total good exposure: **33829521 s** (391.5 days)
- Interval duration: min 2.0 s | median 4363.0 s | mean 15882.4 s | max 59916.0 s
- SoLEXS detector activity: SDD2 active 425 days; SDD1 inactive (F-12) on 426 of 850 parsed GTI files.
- T1 live time total: 33829521 s. GTI-excluded seconds carrying finite counts are counted per day and **[A-14] remain unexplained — Milestone VIII**.

## 5. Version-resolution statistics

- Orbit files examined: 391
- Owned (minute, detector) pairs: 1,065,572
- Conflicting pairs: 48,604 in 256 distinct conflicts
- Resolved by R1 (higher version): 47,328
- Resolved by R2 (longer duration): 1,276
- R3 (processing date) invoked: 0 — HEL1OS primaries carry no `DATE` header
- F-14 terminations: 0
- Unique ownership: **holds** — every owned pair has exactly one provenance owner (asserted at map construction and by F-15 output guards).

## 6. Provenance completeness (T7)

- Provenance rows: 5,199; duplicate (file, product, detector) rows: 0
- Output rows missing provenance: {'T1': 0, 'T3': 0, 'T4': 0}
- Orphan rows (src_file absent from T7): {'T1': 0, 'T3': 0, 'T4': 0}

## 7. Descriptive statistics (no interpretation)

- T1 `rate_total` (cts/s): min 1.0 | median 21.6 | mean 102.0 | max 76088.3
- T3 detector row counts: {'CZT1': 256945, 'CZT2': 256945, 'CDTE2': 256944, 'CDTE1': 256939}
- T4 `suninfov` true: 268,885 of 277,054 minutes (97.1%)
- T5 `detchans` distribution: {341: 513434, 511: 513382} (CZT=341, CdTe=511 carried explicitly; never merged)
- HK inversion statistics (recorded, never thresholded): 389 orbits; max backward step 1153.398 s
- R-1 epoch resolutions: {'relative_seconds': 1556}

## 8. Archive inventory

- SoLEXS archives processed: **424 / 436**
- HEL1OS orbits processed: **389 / 391**
- Skipped products: **14**, by rule: {'F-19': 12, 'F-16': 2}
  - F-19: SoLEXS GTI `STOP <= START` (archive defect; CONTRADICTION-005 Defect C)
  - F-01: unreadable/gzip-corrupt SoLEXS members
  - F-16: duplicate HK `mjd` timestamps (archive defect; CONTRADICTION-006 Defect B, ruled working-as-designed)
  - Every skip is individually logged with its rule id in `canonical_build_stats.json`.

## 9. Data quality summary

Validation executed during the build (counts from `checks`):
- NaN ⇒ GTI-excluded implication (r5): held on all **424** built SoLEXS days (violation = F-09 = skip; none skipped for F-09)
- V-PI-3 (`.pi TSTART[0]` == `.lc TSTART`): **424** days
- SoLEXS GTI files parsed: 850; F-12 inactive detections: 426
- HEL1OS builds: LC 389, HK 389, spectra 389 orbits
- Validation failures: none among built products (failures terminate and become skips, §8)

**Assumptions awaiting Milestone VIII:** **A-8** (GTI exposure identity across all 436 SoLEXS archives), **A-11** (relative-seconds convention across all 391 orbits — 1,180/1,180 spectra products resolved `relative_seconds` in this build), **A-12** (HK inversion distribution), **A-13** (per-family `DETCHANS` across all orbits), **A-14** (the GTI-exclusion excess — unexplained). **CONTRADICTION-003** (SoLEXS LC↔PI relationship) remains OPEN for M-VIII.

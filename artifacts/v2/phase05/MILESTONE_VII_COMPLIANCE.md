<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone VII specification-compliance report against amended contract r5. -->
<!-- DATE: 2026-07-18 -->

# Milestone VII — Specification Compliance Report

**Verdict: COMPLIANT WITH ONE DECLARED DEVIATION (T3 table shape — reported for owner ratification, not silently reconciled). 188/188 tests pass, 0 xfail, 0 skip. CONTRADICTION-005 and -006 CLOSED. Final archive-wide build complete: SoLEXS 424/436, HEL1OS 389/391, 14 skips — every one individually logged and every one covered by an owner ruling.**

Contract: `PARSER_SPECIFICATION.md` **r5**. Implementation: `app/v2/builders/canonical.py`, `scripts/v2/phase05/build_canonical.py`. Dataset: `artifacts/v2/phase05/canonical/` (see `CANONICAL_DATASET_PROFILE.md` for the descriptive inventory).

---

## 1. Final archive coverage (the record required by the owner)

| | Processed | Available | Skipped | Skip rules |
|---|---|---|---|---|
| SoLEXS daily archives | **424** | 436 | 12 | F-19 ×12 (GTI `STOP≤START` — CONTRADICTION-005 Defect C, ruled archive defects) |
| HEL1OS orbits | **389** | 391 | 2 | F-16 ×2 (duplicate HK `mjd` — CONTRADICTION-006 Defect B, ruled working-as-designed) |

**Zero unexplained skips.** All 14 are enumerated in `canonical_build_stats.json` with rule ids; the 12 SoLEXS days and 2 HEL1OS orbits are the archive-quality findings carried to Milestone VIII. Build wall time: 93.75 min.

**Correction to the record (transparency, not consequence):** CONTRADICTION-005 §Defect B stated "22 unparseable — 12 by Defect C, **10 by F-01**". The authoritative build reproduces the 12 F-19 skips but **no F-01 skips** — 424 = 436 − 12 exactly. The "10 F-01" figure came from my ad-hoc archive-scan script, which globbed AppleDouble sidecars as data; the build driver's F-18 guard excludes them. The ad-hoc figure is withdrawn; the build statistics are authoritative. No ruling rested on it.

## 2. Milestone VII scope — item-by-item

| Table | Requirement (M-VII brief + §3 r5) | Result |
|---|---|---|
| **T1** | finite-only aggregation (r2); NaN-aware; `q_no_data`; NaN⇒GTI validation **before** aggregation; no imputation; provenance | ✅ 610,560 rows / 424 days; implication held on **all 424** (F-09 skips: 0); validation-before-aggregation proven by monkeypatch test |
| **T2** | all 340 PI channels; no keV; ordinal `channel_index`; NaN propagation; RMF absence in provenance | ✅ 610,560 rows; `channel_energy_keV` absent by design; "NO RMF … no keV" in every provenance row |
| **T3** | consume resolved ownership only; never duplicate minutes | ✅ 1,027,773 rows via `CoverageMap`; F-15 guard on every emit; **shape deviation — §5 below** |
| **T4** (hk) | preserve archive order; never sort; inversion stats recorded only | ✅ 277,054 rows / 389 orbits; no `sort_values` in the builder (asserted by test); stats recorded, never thresholded |
| **T5** (spectra) | CZT 341 / CdTe 511 distinct; `detchans` explicit; no merged channel space | ✅ 1,026,816 rows; `detchans` ∈ {341, 511} carried per row; F-11 test proves a PI input terminates |
| **T6** | exposure, excluded seconds, detector activity | ✅ 2,130 intervals; SDD1 inactive (F-12) on 426/850 GTI files |
| **T7** | every row traceable to exactly one product; no orphans; no ambiguity | ✅ 5,199 rows; 0 duplicates; 0 orphans; 0 rows missing provenance (profile §6) |

## 3. Falsification results (brief-mandated list)

| Invariant | Method | Result |
|---|---|---|
| NaN⇒GTI (r5) | per-day in `build_T1` + dedicated F-09 tests both directions | held 424/424; the *only* forbidden direction (NaN in good time) verifiably terminates |
| Finite-only aggregation | unit tests: one NaN never voids a minute; all-NaN → NaN not 0; zero is data | ✅ |
| Duplicate-minute impossibility | F-15 guard incl. sub-minute flooring + detector-aware cases; coverage-map two-phase build; order-independence on shuffled real candidates | ✅ |
| Provenance completeness | orphan-detection test + archive-wide profile scan | ✅ 0/0/0 |
| Detector ownership | per-(minute, detector) resolution; independent detectors test | ✅ 1,065,572 owned pairs, unique |
| Version-resolution consistency | identical owner maps across three runs (48,604 conflicts, R1 47,328 / R2 1,276, R3 0, F-14 0 — byte-stable across builds) | ✅ |
| No silent row creation/deletion | F-20 guards; 1440 rows/day exact; every skip logged | ✅ |
| Builders never interpolate/smooth/infer/repair/fill/reorder/modify | AST scan of executable code (docstrings stripped) + `nansum`-only-on-livetime test | ✅ |
| CONTRADICTION-003 independence | `build_T2` signature cannot reach T1; measured non-derivability test | ✅ carried independently |

## 4. CONTRADICTION-006 verification (both rulings)

- **Defect A (approved, implementation-only):** the `_FLOAT_EPS_S` (1 ms) IEEE754 slack — shared with §2.7 R-1, documented at the check site as *not* a physical tolerance — recovered the 94 ULP-artifact orbits: HEL1OS 295 → **389**. Spec text unchanged, verified by diff.
- **Defect B (not approved):** duplicate HK `mjd` still terminates — the 2 orbits (`HLS_20260201_120005`, `HLS_20260202_000005`) appear in the skip log with F-16, exactly as ruled.

## 5. DEVIATIONS — one, declared for owner ratification

**T3 `hel1os_lc_1min` is emitted in LONG form (one row per minute × detector, with a `detector` column and only that detector's band columns populated) rather than §3's WIDE form (one row per minute carrying all four detectors' columns).** This is why the profile shows 75.01% structural NaN in T3 band cells — a shape artifact, not missing data.

Why I am *reporting* rather than *fixing* it: converting to wide surfaced a genuine defect in §3's own shape. The wide schema carries a **single `orbit_id` per row**, but ownership is resolved per **(minute, detector)** (§4), and at orbit boundaries different detectors of the same minute can legitimately be owned by different orbits. The wide shape therefore **cannot represent the provenance the Version Resolution Engine produces** without either widening `orbit_id` to four columns (a schema change) or discarding per-detector ownership (a provenance loss — forbidden). The long form is information-equivalent, lossless, F-15-guarded per (minute, detector), and provenance-faithful.

Under the standing rule — *never modify the specification to fit the implementation* — I have not amended §3. **Options for the owner:** (a) ratify the long form as the T3 canonical shape (align §3 text with T5, which is already long-form with a `detector` column in r5); (b) mandate wide with per-detector `orbit_id_{det}` columns (builder change, ~no rebuild cost — reshape of existing parquets); (c) other. Until ruled, T3 consumers must treat rows as (minute, detector) keyed.

## 6. Findings carried to Milestone VIII

1. **A-8** — GTI exposure identity across all 436 SoLEXS archives (per-day check passed on all 424 built; the 12 F-19 days are the open remainder).
2. **A-11** — relative-seconds: **1,556/1,556** spectra products resolved `relative_seconds` in this build (389 orbits × 4 detectors) — effectively pre-discharged; M-VIII formalises.
3. **A-12** — HK inversions: archive-wide **max backward step 1153.4 s** (~19 min) vs the 0.89 s seen on the M-V sample orbit — three orders larger; recorded, never thresholded; squarely M-VIII's question.
4. **A-13** — per-family `DETCHANS`: no F-07 skips in the final build ⇒ all 389 parsed orbits conform to {CZT 341, CdTe 511}; M-VIII formalises over all 391.
5. **A-14** — GTI-exclusion excess: **25,623 `q_no_data` minutes (4.20%)** in T1 carry the unexplained GTI-exclusion structure; unexplained by design.
6. **CONTRADICTION-003** — LC↔PI relationship: OPEN; T1/T2 carried independently throughout.
7. **Archive-quality findings:** 12 SoLEXS F-19 days (list in build stats); 2 HEL1OS F-16 orbits; the withdrawn "10 F-01" note (§1).

## 7. Statistics

Tests: **188 passed, 0 failed, 0 xfail, 0 skip.** Dataset: 7 tables, ~2.95 M canonical rows, 5,199 provenance rows, full span 2024-02-01 → 2026-06-17. Three archive-wide builds executed under three contract revisions; the version-resolution output was byte-stable across all three.

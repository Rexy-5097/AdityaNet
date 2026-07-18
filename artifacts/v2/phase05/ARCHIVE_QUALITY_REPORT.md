<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone VIII archive-quality inventory. Descriptive; no interpretation. -->
<!-- DATE: 2026-07-18 -->

# Archive Quality Report

**Complete inventory of every archive anomaly discovered during AdityaNet v2, Phase 0.5.** Counts, affected products, governing rule ids, and disposition. **No interpretation.** Each disposition is the ruling already recorded in the cited contradiction or contract revision.

Source of record: `canonical_build_stats.json` (the authoritative archive-wide build), `version_resolution_log.json`, and the Phase 0.5.1 manifest.

---

## 1. Summary

| Anomaly class | Rule | Count | Products affected | Disposition |
|---|---|---|---|---|
| GTI interval `STOP ≤ START` | F-19 | **12** | SoLEXS daily archives | Archive defect (CONTRADICTION-005 Defect C) — excluded, logged |
| Duplicate HK `mjd` timestamp | F-16 | **2** | HEL1OS orbits | Archive defect (CONTRADICTION-006 Defect B) — excluded, logged |
| Inactive detector (empty GTI) | F-12 | **426** | SoLEXS SDD1 GTI files | Legal state, not an error — SDD1 is GTI-only, SDD2 carries science |
| HK time inversions (jitter) | — | see A-12 | HEL1OS orbits | Characterised in `MILESTONE_VIII_VALIDATION_REPORT.md` (A-12) |
| Two PHA channel families | F-07→resolved | 0 (resolved) | HEL1OS CZT/CdTe | Contract corrected (CONTRADICTION-005 Defect A, r5) — 0 residual failures |
| AppleDouble `._*` sidecars | F-18 | (excluded) | filesystem artifacts | exFAT/macOS artifacts, never data — excluded by allowlist |

**Total products excluded from the canonical dataset: 14** (12 SoLEXS + 2 HEL1OS), of 436 + 391 = 827 available. Coverage: SoLEXS **424/436**, HEL1OS **389/391**.

## 2. F-19 — SoLEXS GTI `STOP ≤ START` (12 archives)

A GTI interval whose stop time is at or before its start time. `STOP ≤ START` is not a convention question; it is an internal inconsistency in the archived GTI table. F-19 terminates on parse.

**Affected (all SoLEXS daily archives):**
`AL1_SLX_L1_20240422_v1.0`, `20240501`, `20250729`, `20251205`, `20260406`, `20260407`, `20260408`, `20260409`, `20260411`, `20260413`, `20260414`, `20260415`.

**Disposition:** archive defect. Excluded from the canonical dataset, individually logged. No amendment (F-19 behaves as designed). Note the temporal clustering (8 of 12 in April 2026) — recorded as an observation, not interpreted.

## 3. F-16 — Duplicate HK `mjd` (2 orbits)

Two housekeeping rows sharing an identical `mjd` timestamp. §2.8 (r4) requires HK `mjd` to be unique; a duplicate terminates via F-16.

**Affected (HEL1OS orbits):**
- `HLS_20260201_120005_43198sec_lev1_V111` — 2 duplicated values (of 63,298 rows)
- `HLS_20260202_000005_43183sec_lev1_V111` — 1 duplicated value

**Disposition:** archive defect (CONTRADICTION-006 Defect B, owner ruled **not approved** for amendment — F-16 continues to terminate). Excluded, logged. 389 of 391 orbits have fully unique HK `mjd`.

## 4. F-12 — Inactive detectors (426 GTI files)

A GTI table with zero rows (`NAXIS2 = 0`), which the contract treats as a **legal** inactive-detector state, not an error (the single deliberately non-terminating rule). `OBSERVED`: SoLEXS SDD1 supplies GTI only (no `.lc`/`.pi`), and its GTI is empty across the archive; SDD2 carries all science.

**Count:** 426 F-12 detections among 850 parsed SoLEXS GTI files (SDD1 across the built days). **Disposition:** expected structural property of the SoLEXS archive; not a defect.

## 5. Two PHA channel families (resolved, 0 residual)

`OBSERVED` during the archive-wide build: HEL1OS has two detector families with different PHA channel counts — **CZT = 341, CdTe = 511**. The r0 contract asserted a single `DETCHANS = 341`, which blocked all 391 orbits at F-07.

**Disposition:** contract corrected (CONTRADICTION-005 Defect A → spec r5: per-family allowlist; F-11 restated over three incommensurable channel spaces — SoLEXS PI 340, HEL1OS CZT PHA 341, HEL1OS CdTe PHA 511). After the fix: **0 F-07 DETCHANS failures** archive-wide. Not an archive defect — an archive property the contract now encodes.

## 6. AppleDouble sidecars (`._*`)

macOS writes `._<name>` metadata sidecars on the exFAT volume. These are filesystem artifacts, never instrument data. F-18 (allowlist + `._*` guard) excludes them. **Disposition:** not data; excluded structurally. *(Note: the withdrawn "10 F-01 unreadable days" figure from CONTRADICTION-005 originated in an ad-hoc scan that globbed these sidecars; the authoritative build has no F-01 skips.)*

## 7. Lost / unavailable dates (not defects of parsed data)

From Phase 0.5.1: exactly **one** genuinely lost SoLEXS date (`2023-12-13`, an interrupted download in `downloads/corrupted/`), and the HEL1OS archive begins only **2025-12-07** (combined SoLEXS+HEL1OS coverage = 179 days). These are **acquisition gaps**, not quality defects of the data on hand; carried to Phase 0.5.3.

## 8. Disposition ledger

| Product(s) | Rule | Permanent disposition |
|---|---|---|
| 12 SoLEXS F-19 archives (§2) | F-19 | **Archive defect** — permanently excluded |
| 2 HEL1OS F-16 orbits (§3) | F-16 | **Archive defect** — permanently excluded |
| 426 SDD1 empty GTIs (§4) | F-12 | **Legal inactive** — not excluded, not a defect |
| CZT/CdTe channel counts (§5) | F-07→r5 | **Archive property** — contract corrected, 0 residual |
| `._*` sidecars (§6) | F-18 | **Not data** — structurally excluded |
| 2023-12-13, pre-2025-12 HEL1OS (§7) | — | **Acquisition gap** — Phase 0.5.3 |

These are the permanent archive findings of Phase 0.5.

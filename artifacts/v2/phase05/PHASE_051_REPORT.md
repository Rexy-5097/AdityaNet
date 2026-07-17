<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Phase 0.5.1 Extraction & Archive Manifest — deliverable report. -->
<!-- DATE: 2026-07-17 -->

# Phase 0.5.1 — Extraction & Archive Manifest: Report

**Verdict: PASS on extraction and integrity — 827/827 archives extracted, 0 failures, 0 CRC errors, 8,010 members, 135.57 GB, in 6.8 minutes. But the coverage report contains a finding that materially constrains the project and was not anticipated by roadmap r1: SoLEXS and HEL1OS overlap on only 179 days. The ISRO problem statement requires *combined* SoLEXS + HEL1OS data, so the combined-instrument dataset is ~5.9 months, not the ~2.4 years r1 assumed.**

Source treated as immutable evidence: `data_pipeline/downloads/raw/` opened read-only, never modified or moved. Extracted to a separate versioned store `data/aditya_l1/real_l1_v1/`. Fail-loud rule enforced: every archive and member carries an explicit status; nothing was skipped.

Artifacts: `archive_manifest.json` (827 records, SHA-256 + integrity + member counts), `member_inventory.json` (8,010 records with per-member SHA-256), `extraction_log.json`, `analysis.json`. Code: `scripts/v2/phase05/{extract_archive,analyze_archive}.py`.

---

## 1. Archive Manifest & Integrity Report

| Metric | Value |
|---|---|
| Archives discovered | **827** (`.zip` under `downloads/raw`, instrument inferred from path, never assumed) |
| SHA-256 computed | 827 / 827 |
| ZIP CRC integrity (`testzip`) | **OK: 827 / 827** — zero corrupt archives |
| Extraction status | **EXTRACTED: 827 / 827** — zero failures, zero partials |
| Members extracted | **8,010 / 8,010**, each with SHA-256 |
| Path-traversal rejections | 0 |
| Undated archives (unparseable stem) | 0 |
| Instrument = UNKNOWN (path not recognised) | 0 |

## 2. Storage Statistics

| Metric | Value |
|---|---|
| Compressed | 22.36 GB |
| Uncompressed / extracted | **135.57 GB** (6.06× ratio) |
| Disk before → after | 38 GiB → ~174 GiB used; **867 GiB free** |
| Wall time | 6.8 min (~20 GB/min sustained) |

## 3. Instrument Inventory

| Instrument | Archives | Members | Size | Product granularity |
|---|---|---|---|---|
| **SoLEXS** | 436 | 1,754 | 3.47 GB | one archive per **day** |
| **HEL1OS** | 391 | 6,256 | **132.10 GB** | one archive per **orbit** (~2/day) |

HEL1OS is 97% of the volume; `events/evt.fits` alone is 85.7 GB (391 files, ~219 MB each).

## 4. Product-Type Inventory

**SoLEXS** (per daily archive): `.lc.gz` light curve ×1 (0.118 GB total), `.pi.gz` spectrum ×1 (3.34 GB), `.gti.gz` good-time-intervals ×2 (one per SDD detector).

**HEL1OS** (per orbit archive): `events/evt.fits` ×1 (85.7 GB), `cdte/*_spectra_*` ×2 (16.6 GB), `czt/*_spectra_*` ×2 (11.1 GB), `czt/lightcurve_czt*` ×2 (8.75 GB), `cdte/lightcurve_cdte*` ×2 (8.74 GB), `aux/hk.fits` housekeeping ×1 (1.18 GB), `aux/gticdte*`/`gticzt*` ×2 each, `aux/cztdis/*dispix.txt` ×2.

The `aux/hk.fits` housekeeping and the event lists are retained deliberately: Phase 1a needs them for gain-mode and pile-up characterisation. Extracting the full archive rather than only science products was a considered decision — 135 GB against 867 GB free is affordable, and under-extracting the data layer is the exact error pattern that produced v1.

## 5. Coverage Report — **the critical finding**

| Instrument | Unique days | First | Last | Span | Coverage within span |
|---|---|---|---|---|---|
| SoLEXS | **436** | 2024-02-01 | 2026-06-15 | 866 d | 50.3% (430 days missing) |
| HEL1OS | **189** | **2025-12-07** | 2026-06-17 | 193 d | 97.9% (4 days missing) |
| **BOTH (same day)** | **179** | **2025-12-07** | **2026-06-15** | — | — |

`OBSERVED`: SoLEXS-only days: 257. HEL1OS-only days: 10. **Combined-instrument days: 179 (~5.9 months).**

**Why this matters.** The ISRO brief specifies "combined time-series data from SoLEXS and HEL1OS." Roadmap r1's replacement assumption 3′ stated the archive spans "2024-02 → 2026-06" for both instruments and that ~431 real SoLEXS days would suffice for Phases 1–3. That is now `OBSERVED` false for the combined case: **HEL1OS on disk begins only 2025-12-07.** Any combined-instrument model has ~179 days; a SoLEXS-only model has 436 days spread across 28 months at 50% duty.

**Largest SoLEXS gaps:** 2025-02-03→2025-06-17 (135 d), 2024-06-01→2024-09-30 (122 d), 2024-10-26→2024-12-11 (47 d), 2024-12-13→2025-01-18 (37 d), 2024-10-02→2024-10-24 (23 d).

### Monthly Coverage Summary (days present)

| Month | SoLEXS | HEL1OS | | Month | SoLEXS | HEL1OS |
|---|---|---|---|---|---|---|
| 2024-02 | 29 | — | | 2025-09 | 22 | — |
| 2024-03 | 28 | — | | 2025-10 | 27 | — |
| 2024-04 | 30 | — | | 2025-11 | 28 | — |
| 2024-05 | 31 | — | | 2025-12 | 29 | **25** |
| 2024-10 | 2 | — | | 2026-01 | 31 | 31 |
| 2024-12 | 1 | — | | 2026-02 | 25 | 27 |
| 2025-01 | 1 | — | | 2026-03 | 31 | 31 |
| 2025-02 | 1 | — | | 2026-04 | 26 | 29 |
| 2025-06 | 11 | — | | 2026-05 | 30 | 30 |
| 2025-07 | 15 | — | | 2026-06 | 13 | 16 |
| 2025-08 | 25 | — | | | | |

Note the SoLEXS structure: a dense Feb–May 2024 block (118 d, which **contains the May-2024 X-flare storm** — the Phase 0.5.2 validation target), a near-empty Jun 2024–May 2025 year (6 d), then a dense Jun 2025–Jun 2026 block (312 d).

## 6. Duplicate Report

- **Identical-content archives (same SHA-256): 0.** No byte-level duplicates.
- **SoLEXS duplicate dates: 0.** 436 archives = 436 unique days, exactly 1:1. *(This falsifies my own pre-extraction estimate of "~5 duplicate dates," which came from comparing a `sort -u` count against a file count — the discrepancy was 436 vs 431, and 431 turns out to be the count of *structurally standard* archives, not unique dates. See §8.)*
- **HEL1OS multiple archives per day: expected, not duplication** — orbit-level products, ~2/day (154 days ×2, 19 ×3, 13 ×1, 2 ×4, 1 ×5).
- **HEL1OS version variants `OBSERVED`:** V111 ×371, V211 ×16, V112 ×3, V311 ×1. **46 time-overlapping archive pairs** exist (e.g. `HLS_20251208_000008_43178sec_..._V111` and `..._V211` — same start, same duration, different version). Their `evt.fits` SHA-256 values **differ**, so they are genuinely different reprocessings, not byte-copies. **This is a live hazard for Phase 0.5.2: naive ingestion of all orbit files would double-count photons across 46 overlapping intervals.** A version-selection rule (highest version per time interval) must be part of the parser spec.
- **Shared member SHAs across archives: 2** — the empty `czt2dispix.txt` and the 13-byte `czt1dispix.txt`; benign constants.

## 7. Corrupt / Failed-Download Report

`data_pipeline/downloads/corrupted/`: **427 files, all SoLEXS, ~0 GB of real content** (425 are 65-byte stubs — almost certainly server error responses; plus one 4,288 B file and one 204,974 B file, and one `.part`). Dates span 2023-12 → 2026-06. **426 of the 427 dates are present in the successfully extracted set**, so these are retry artifacts from a flaky download campaign, not lost data. Exactly **one** date appears only here: **2023-12-13** (`AL1_SLX_L1_20231213_v1.0.zip.part`, an interrupted download).

## 8. Falsification Pass (self-review)

Attempted to break the inventory on the seven axes required:

1. **Missing months** — `OBSERVED` and reported: the SoLEXS Jun 2024–May 2025 hole (6 days in 12 months) and the total absence of HEL1OS before 2025-12-07. The latter is the report's headline finding; it was *not* predicted by r1 and would have silently halved the project's premise had extraction not quantified it.
2. **Duplicate archives** — my own pre-extraction prediction of ~5 duplicate SoLEXS dates was **wrong and is withdrawn**; measurement shows 1:1 date mapping. The real duplication risk is elsewhere and worse: HEL1OS version-overlapping orbits (§6).
3. **Inconsistent directory structures** — `OBSERVED`: SoLEXS has **two** profiles — 431 archives with the standard `{lc×1, pi×1, gti×2}` and **5 archives carrying extra `.png` and an extra `.gz` member**. HEL1OS is perfectly uniform: **1 distinct profile across all 391 archives**. The 5 anomalous SoLEXS archives must be inspected in 0.5.2, not assumed benign.
4. **Damaged FITS** — CRC-verified at the ZIP layer only (827/827 OK). **FITS-level validity is NOT established by this phase** — that is 0.5.2's job, and this report claims nothing about it.
5. **Unexpected file types** — `OBSERVED`: 5 `.png` and 5 non-standard `.gz` members inside the 5 anomalous SoLEXS archives; 782 `.txt` pixel maps (expected). No executables, no archives-within-archives beyond the expected `.gz` science products.
6. **Metadata inconsistencies** — `OBSERVED`: 391 zero-byte `czt2dispix.txt` members (one per HEL1OS archive) — a systematic ISSDC quirk, benign for our purposes but recorded.
7. **Instrument misattribution** — 0 archives with UNKNOWN instrument; all 827 resolved from path structure and confirmed by filename convention (`AL1_SLX_*` / `HLS_*`).

**What this phase does NOT establish** (stated to prevent over-reading): that any FITS parses correctly; that the data is scientifically authentic (that is 0.5.4's coincidence check); that HEL1OS pre-2025-12 does not exist *at ISSDC* — only that it is not on disk.

## 9. Directory Tree (extracted store)

```
data/aditya_l1/real_l1_v1/
├── solexs/                       436 archives, 3.47 GB
│   └── AL1_SLX_L1_<YYYYMMDD>_v1.0/
│       ├── SDD1/AL1_SOLEXS_<date>_SDD1_L1.{lc,pi,gti}.gz
│       └── SDD2/AL1_SOLEXS_<date>_SDD2_L1.{lc,pi,gti}.gz
└── hel1os/                       391 archives, 132.10 GB
    └── HLS_<YYYYMMDD>_<HHMMSS>_<N>sec_lev1_V<ver>/
        └── <YYYY>/<MM>/<DD>/HLS_.../
            ├── events/evt.fits              (~219 MB)
            ├── cdte/{lightcurve_cdte1,2, hel1os_cdte_spectra_cdte1,2}.fits
            ├── czt/{lightcurve_czt1,2, hel1os_czt_spectra_czt1,2}.fits
            └── aux/{hk.fits, gticdte1,2.fits, gticzt1,2.fits, cztdis/*.txt}
```

## 10. Verdict & Consequences

**PASS** — Gate G0.5 criterion (i) is satisfied: 100% of the 827 archives extracted with a SHA-256 manifest, zero corrupt, zero silent skips.

**Two findings are escalated to Phase 0.5.3 (Coverage Quantification & Gap-Fill Request), where the roadmap already places them:**

1. **Combined SoLEXS+HEL1OS coverage is 179 days**, not ~2.4 years. This directly contradicts roadmap r1 standing assumption 3′ and is material to what Phases 1–3 can conclude. It does not invalidate Phase 0.5 (0.5.3 exists precisely to quantify coverage and define the gap-fill request), but the owner should know now: **the gap-fill request is no longer optional for the combined-instrument framing** — HEL1OS Feb 2024 – Nov 2025 becomes the highest-value acquisition target, and whether it exists at ISSDC is unknown.
2. **A SoLEXS-only arm has 436 days** including the May-2024 X-flare storm — sufficient for Phase 1's SoLEXS characterisation and Gate 1's capability study to proceed on schedule regardless of the HEL1OS gap.

**Carried into Phase 0.5.2 as parser requirements:** the HEL1OS version-overlap rule (46 pairs; must not double-count), the 5 structurally anomalous SoLEXS archives, and the `.pi` spectra as the per-day bulk (SoLEXS light curves are only 0.118 GB total — the spectra are where the spectral dimension v1 discarded actually lives).

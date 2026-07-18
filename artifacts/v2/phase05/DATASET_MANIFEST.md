<!-- VERSION STATUS: FROZEN — IMMUTABLE -->
<!-- REASON: Milestone IX dataset freeze. This document defines the immutable scientific baseline. -->
<!-- DATE: 2026-07-18 -->

# Dataset Manifest — `AdityaNet_v2_dataset_r1`

**This dataset is FROZEN and IMMUTABLE.** From this point forward, machine-learning code MUST NOT modify raw measurements, canonical tables, or provenance. Every experiment consumes this dataset read-only.

---

## 1. Identity

| Field | Value |
|---|---|
| **Dataset version** | **`AdityaNet_v2_dataset_r1`** |
| **Dataset hash** | `43fd0e228b28ae6bc7e468c3acf68722768bd62b73798eb6631e9e6233b71ed9` |
| **Provenance hash** (T7) | `7282b7c34fbd6c2eae7dfca6757f46cdc497b88a9b6312089715479e67be8498` |
| **Build commit** | `be0b7e5114db41e24f592f6483fa643d98586d02` (`be0b7e5`) |
| **Specification revision** | **r6** (`PARSER_SPECIFICATION.md`) |
| **Parser revision** | M-V family (§2.1–§2.9) at r5 + CONTRADICTION-006 Defect-A float-ε |
| **Builder revision** | M-VII (§3) at r5 + T3 long-form (r6) |
| **Validation revision** | M-VIII (`MILESTONE_VIII_VALIDATION_REPORT.md`) |
| **Archive span** | **2024-02-01 → 2026-06-17 UTC** |
| **Build timestamp** | 2026-07-18 (build wall time 93.75 min) |
| **Frozen at** | 2026-07-18 UTC |

The **dataset hash** is the SHA-256 over the sorted SHA-256s of all 1,985 parquet files — order-independent and sensitive to any change in any file.

## 2. Table inventory

| Table | Name | Files | Rows | Table hash (16) |
|---|---|---|---|---|
| **T1** | `solexs_lc_1min` | 424 | **610,560** | `5e6d95be2b4359d0` |
| **T2** | `solexs_spec_1min` | 424 | **610,560** | `4124d5ee4f598b12` |
| **T3** | `hel1os_lc_1min` | 373 | **1,027,773** | `d814d3ad4c2edcfc` |
| **T4** | `hel1os_hk_1min` | 389 | **277,054** | `fdb005c60811f51a` |
| **T5** | `hel1os_spec_1min` | 373 | **1,026,816** | `ff7f5a90a1a3a728` |
| **T6** | `gti_intervals` | 1 | **2,130** | `5930fe126f49e96f` |
| **T7** | `provenance_manifest` | 1 | **5,199** | `12c2b6d073b99dc0` |
| | **Total** | **1,985** | **3,560,092** | 596.9 MB |

Per-file SHA-256 for all 1,985 files: `freeze_manifest.json`.

**Archive coverage:** SoLEXS **424 / 436** daily archives; HEL1OS **389 / 391** orbits. The 14 excluded products are archive defects with owner rulings (`ARCHIVE_QUALITY_REPORT.md`).

## 3. Software environment

| Field | Value |
|---|---|
| Python | **3.12.12** |
| Platform | macOS-26.5.2-arm64 (Apple Silicon) |
| Lockfile | `artifacts/v2/phase05/requirements.lock` (92 packages) |
| **Lockfile SHA-256** | `6899e001b1c4d64a5aec01b3ee1d2cfce2a3ff38ab64f827a75ab9d55fd13d3f` |

Critical pins: `numpy==1.26.4`, `pandas==2.2.2`, `pyarrow==16.1.0`, `astropy==6.1.7`, `scipy==1.17.1`, `scikit-learn==1.5.0`.

> **numpy is pinned deliberately.** An unpinned `pip install astropy` silently upgraded numpy to 2.5.1 during Phase 0 and was reverted; the lockfile exists so that cannot recur.

## 4. Provenance chain

Every canonical row traces to exactly one archive product:

```
ISSDC ZIP  →(SHA-256, Phase 0.5.1 manifest)→  extracted L1 FITS
           →(frozen parsers, §2)→  ParsedProduct + Provenance
           →(builders, §3)→  canonical row  [src_file, src_sha256, archive_version]
           →(T7)→  provenance_manifest  [5,199 rows]
```

T7 completeness: **0 orphan rows, 0 duplicate provenance entries, 0 rows missing provenance** (verified archive-wide).

## 5. Reproducibility instructions

```bash
# 1. environment (exact pins matter — see §3)
python3.12 -m venv venv
./venv/bin/pip install -r artifacts/v2/phase05/requirements.lock

# 2. extract the raw ISSDC archive (827 ZIPs → 135 GB)
./venv/bin/python scripts/v2/phase05/extract_archive.py

# 3. rebuild the canonical dataset (~94 min)
./venv/bin/python scripts/v2/phase05/build_canonical.py

# 4. verify identity against this manifest
./venv/bin/python scripts/v2/phase05/freeze_dataset.py       # → dataset_hash
./venv/bin/python scripts/v2/phase05/verify_reproducibility.py

# 5. re-run the scientific validation (optional, ~20 min)
./venv/bin/python scripts/v2/phase05/validate_scientific.py
```

A faithful rebuild reproduces the canonical tables **byte-identically** in this pinned environment (demonstrated 12/12 on T1 and T2 — see `REPRODUCIBILITY_REPORT.md`). The single exception is T7's `parsed_at_utc` column, which records build wall-clock time by design and is therefore excluded from reproducible content hashes.

## 6. Immutability rules (binding from this point)

1. **No ML code may write to** `artifacts/v2/phase05/canonical/` — the dataset is read-only.
2. **No ML code may modify** raw measurements, canonical tables, or provenance.
3. Feature engineering, normalisation, resampling, and splitting produce **derived artifacts in separate locations**; the frozen tables are inputs only.
4. Any change to a canonical table requires a **new dataset version** (`_r2`, …) with its own manifest, a proven parser-level contradiction, and an owner ruling.
5. **Wide-form T3** and any other reshaping are **derived views**, never replacements (spec r6).

## 7. Companion documents

`CANONICAL_DATASET_PROFILE.md` (descriptive inventory) · `MILESTONE_VII_COMPLIANCE.md` (build compliance) · `MILESTONE_VIII_VALIDATION_REPORT.md` (assumptions discharged) · `SCIENTIFIC_FINDINGS.md` (F-1…F-7) · `ARCHIVE_QUALITY_REPORT.md` (anomalies) · `DATA_DICTIONARY.md` (every column) · `REPRODUCIBILITY_REPORT.md` (rebuild proof) · `ML_READINESS_REPORT.md` (readiness review) · `PARSER_SPECIFICATION.md` r6 (the contract).

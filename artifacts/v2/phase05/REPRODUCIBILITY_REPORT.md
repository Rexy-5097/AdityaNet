<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone IX reproducibility proof for AdityaNet_v2_dataset_r1. -->
<!-- DATE: 2026-07-18 -->

# Reproducibility Report — `AdityaNet_v2_dataset_r1`

**Result: PASS. Rebuilding from the raw ISSDC archive reproduces the canonical tables BYTE-IDENTICALLY — 12/12 sampled days, both T1 and T2, byte match AND content match.** Evidence: `reproducibility_check.json`.

---

## 1. What was tested

Twelve days were selected by even spacing across the full archive span (2024-02-01 → 2026-06-15) — not cherry-picked — and rebuilt **from the raw L1 FITS**, through the frozen parsers and builders, then compared against the frozen dataset.

Two distinct claims were measured separately, because they are not the same thing:

- **Content identity** — the *values* are identical. This is the scientific claim: a rebuild must reproduce the same measurements.
- **Byte identity** — the *parquet file bytes* are identical. Stronger, but partly a property of the writer environment (parquet embeds library metadata), so it was measured rather than assumed.

## 2. Result

| Day | T1 content | T1 byte | T2 content | Rebuild |
|---|---|---|---|---|
| 2024-02-01 | ✅ | ✅ | ✅ | 0.6 s |
| 2024-03-10 | ✅ | ✅ | ✅ | 0.4 s |
| 2024-04-20 | ✅ | ✅ | ✅ | 0.4 s |
| 2024-05-31 | ✅ | ✅ | ✅ | 0.4 s |
| 2025-08-09 | ✅ | ✅ | ✅ | 0.4 s |
| 2025-09-30 | ✅ | ✅ | ✅ | 0.4 s |
| 2025-11-12 | ✅ | ✅ | ✅ | 0.4 s |
| 2025-12-23 | ✅ | ✅ | ✅ | 0.4 s |
| 2026-02-01 | ✅ | ✅ | ✅ | 0.4 s |
| 2026-03-15 | ✅ | ✅ | ✅ | 0.4 s |
| 2026-05-04 | ✅ | ✅ | ✅ | 0.4 s |
| 2026-06-15 | ✅ | ✅ | ✅ | 0.4 s |

**Content identity: T1 12/12, T2 12/12. Byte identity: T1 12/12, T2 12/12.**

Both the 340-channel spectral arrays (T2) and the scalar light-curve table (T1) reproduce exactly. Row counts match (1,440 rows/day) on every sample.

## 3. Determinism: why it holds

The pipeline contains **no non-deterministic operation** by construction:

| Property | Guarantee |
|---|---|
| No randomness | No RNG anywhere in parsers or builders (no sampling, no shuffling, no initialisation) |
| No imputation | NaN is preserved as the missing-data sentinel; never filled, never dropped (verified by AST scan + tests) |
| No reordering | The parser preserves archive order losslessly; HK sorting is an explicit out-of-parser utility |
| Order-independent resolution | The Version Resolution Engine builds a coverage map in two phases (collect → resolve); shuffled candidate order yields identical maps, proven on real data |
| Order-independent aggregation | All minute statistics are sum/mean/max/min over finite values |
| Fixed hashing | Provenance SHAs come from the frozen Phase 0.5.1 manifest, not recomputed at build time |

**Version-resolution stability across three independent full builds:** 1,065,572 owned (minute, detector) pairs, 48,604 conflicts, R1 47,328 / R2 1,276 / R3 0 / F-14 0 — byte-stable every time.

## 4. The one documented exception

**T7 `provenance_manifest` contains `parsed_at_utc`**, a build wall-clock timestamp. This column differs between builds *by design* — it records when a build ran. Every other T7 column is deterministic.

Consequently:
- The reproducible **content hash** of T7 **excludes** `parsed_at_utc` (`NON_REPRODUCIBLE_COLUMNS` in `freeze_dataset.py`).
- The **file SHA-256** of T7 in the manifest pins *this* frozen artifact exactly, as it does for every other file.

This is stated rather than engineered away: removing the timestamp would have modified the dataset after freezing, and the timestamp is legitimate provenance.

## 5. Environment

| Field | Value |
|---|---|
| Python | 3.12.12 |
| numpy / pandas | 1.26.4 / 2.2.2 |
| pyarrow / astropy | 16.1.0 / 6.1.7 |
| Platform | macOS-26.5.2-arm64 (Apple Silicon) |
| Lockfile SHA-256 | `6899e001b1c4d64a5aec01b3ee1d2cfce2a3ff38ab64f827a75ab9d55fd13d3f` |

**Scope of the byte-identity claim:** demonstrated in this pinned environment. Byte identity depends on the parquet writer (`pyarrow==16.1.0`); a different pyarrow may produce different bytes for identical data. **Content identity is the portable guarantee**; byte identity is the observed, stronger result here. Both are reported so the distinction is not lost.

## 6. Timing

| Stage | Time |
|---|---|
| Per-day rebuild (T1 + T2, from raw FITS) | **0.4 s** median |
| Full archive rebuild (424 SoLEXS days + 389 HEL1OS orbits) | **93.75 min** |
| Archive extraction (827 ZIPs → 135 GB) | 6.8 min |
| Scientific validation | ~20 min |
| Sample verification (this report) | ~6 s |

## 7. How to reproduce

See `DATASET_MANIFEST.md` §5. In short: install from the lockfile, run `extract_archive.py`, run `build_canonical.py`, then `freeze_dataset.py` and compare `dataset_hash` against `43fd0e228b28ae6bc7e468c3acf68722768bd62b73798eb6631e9e6233b71ed9`.

**Verdict: the dataset is reproducible from the raw archive.** Content-identical by construction and byte-identical in the pinned environment, with one documented, deliberate exception (`parsed_at_utc`).

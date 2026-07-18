<!-- VERSION STATUS: FROZEN — describes AdityaNet_v2_dataset_r1 -->
<!-- REASON: Milestone IX data dictionary. Every canonical column. No scientific interpretation. -->
<!-- DATE: 2026-07-18 -->

# Data Dictionary — `AdityaNet_v2_dataset_r1`

Every column of every canonical table. **No scientific interpretation** — field definitions, units, derivations, and missing-value semantics only.

**Universal conventions**

| Convention | Rule |
|---|---|
| Time | All timestamps `datetime64[ns, UTC]`, timezone-aware, minute-aligned (T1–T5) |
| Missing | **NaN only.** Never imputed, filled, interpolated, or dropped. Zero is a valid measurement, never "missing" |
| Quality flags | `q_*` are boolean, **True = problem** |
| Aggregation | Minute statistics are over **finite observations only**; one NaN never voids a minute; a minute with no finite observation is NaN |
| Provenance | Every row carries `src_file` + `src_sha256`; joins to T7 |
| Channels | **Ordinal indices, not energies.** No RMF/ARF exists in the archive; no keV mapping is possible or provided |

---

## T1 — `solexs_lc_1min` (610,560 rows · 424 files)

One row per minute of a SoLEXS observing day. Source: `.lc` (light curve) + `.gti`, SDD2.

| Column | Type | Units | Source / derivation | Allowed values | Missing semantics |
|---|---|---|---|---|---|
| `timestamp` | datetime64[ns,UTC] | — | minute index of the observation day | 1,440/day, monotonic, unique | never missing |
| `counts_total` | float64 | counts | Σ of `.lc COUNTS` over **finite** seconds in the minute | ≥ 0 | NaN ⟺ no finite second (`q_no_data`) |
| `live_time_s` | float64 | s | GTI-covered seconds in the minute (**inclusive** endpoints, `STOP−START+1`) | 0 … 60 | never missing; 0 = fully excluded |
| `rate_total` | float64 | counts/s | `counts_total / live_time_s` | ≥ 0 | NaN where `live_time_s == 0` — **not imputed** |
| `gti_fraction` | float64 | — | `live_time_s / 60` | 0.0 … 1.0 | never missing |
| `n_seconds_present` | int16 | count | number of **finite** `.lc` seconds in the minute | 0 … 60 | never missing |
| `q_no_data` | bool | — | `n_seconds_present == 0` | True/False | flag |
| `q_partial` | bool | — | `0 < gti_fraction < 1` | True/False | flag |
| `detector` | category | — | SoLEXS detector | `SDD2` only | never missing |
| `src_file` | object | — | source `.lc` path | — | never missing |
| `src_sha256` | object | — | SHA-256 of the source archive (Phase 0.5.1 manifest) | 64 hex | never missing |
| `archive_version` | object | — | ISSDC archive variant | `v1.0`, `v1.1` | never missing |

> `counts_total` (light curve) is **band-limited** and is **not** Σ(T2 `counts`) — see `SCIENTIFIC_FINDINGS.md` F-1. The two are carried independently; neither is derived from the other.

## T2 — `solexs_spec_1min` (610,560 rows · 424 files)

One row per minute; the full SoLEXS spectrum. Source: `.pi` (OGIP Type II PHA) + `.gti`, SDD2.

| Column | Type | Units | Source / derivation | Allowed values | Missing semantics |
|---|---|---|---|---|---|
| `timestamp` | datetime64[ns,UTC] | — | minute index | 1,440/day | never missing |
| `counts` | object → **array[340]** float64 | counts | per-channel Σ over **finite** seconds in the minute | ≥ 0 per channel | NaN per channel where no finite second |
| `live_time_s` | float64 | s | GTI-covered seconds (inclusive) | 0 … 60 | never missing |
| `gti_fraction` | float64 | — | `live_time_s / 60` | 0.0 … 1.0 | never missing |
| `n_seconds_present` | int16 | count | finite spectra contributing | 0 … 60 | never missing |
| `q_no_data` | bool | — | no finite spectrum in the minute | True/False | flag |
| `q_partial` | bool | — | partial GTI coverage | True/False | flag |
| `detector` | category | — | SoLEXS detector | `SDD2` | never missing |
| `chantype` | category | — | channel type from `CHANTYPE` | `PI` | never missing |
| `src_file`, `src_sha256`, `archive_version` | object | — | provenance | — | never missing |

**Channel axis:** `counts[i]` is PI channel `i`, `i ∈ [0, 339]` — an **ordinal** index. **No `channel_energy_keV` column exists, by design:** the archive contains no response matrix, so no channel→energy mapping is possible. Do not assume linearity in energy.

## T3 — `hel1os_lc_1min` (1,027,773 rows · 373 files)

**LONG form (spec r6): one row per (minute, detector)**, keyed uniquely by that pair. Source: HEL1OS `lightcurve_*.fits`, ownership from the Version Resolution Engine.

| Column | Type | Units | Source / derivation | Allowed values | Missing semantics |
|---|---|---|---|---|---|
| `timestamp` | datetime64[ns,UTC] | — | minute index | — | never missing |
| `detector` | object | — | the detector this row describes | `CZT1`,`CZT2`,`CDTE1`,`CDTE2` | never missing |
| `{det}_{lo}_{hi}_rate` | float64 | **counts/s** | mean of `CTR` over the minute's samples | ≥ 0 | **NaN when `{det}` ≠ this row's `detector`** (structural) |
| `{det}_{lo}_{hi}_stat_err` | float64 | counts/s | mean of `STAT_ERR` | ≥ 0 | as above |
| `{det}_{lo}_{hi}_n_samples` | float64 | count | samples contributing to the minute | ≥ 1 | as above |
| `orbit_id` | object | — | owning orbit (version-resolved) | `HLS_…_V###` | never missing |
| `orbit_version` | object | — | orbit product version | `V111`,`V211`,`V112`,`V311` | never missing |
| `src_file`, `src_sha256`, `archive_version` | object | — | provenance | — | never missing |

**Band columns present** (edges parsed from `EXTNAME`, allowlist-validated):
- **CZT1/CZT2:** `20_40`, `40_60`, `60_80`, `80_150`, `18_160` (keV)
- **CDTE1/CDTE2:** `5_20`, `20_30`, `30_40`, `40_60`, `1p8_90` (keV; `1p8` = 1.8)

> **Structural NaN:** because the table is long-form, each row populates only its own detector's band columns; the other three detectors' columns are NaN **by construction, not by missing data**. Filter by `detector` before using band columns. A wide view may be derived, but the canonical form is long (spec r6) because ownership is per (minute, detector).

## T4 — `hel1os_hk_1min` (277,054 rows · 389 files)

One row per minute of HEL1OS housekeeping. Source: `aux/hk.fits`.

| Column | Type | Units | Derivation | Notes |
|---|---|---|---|---|
| `timestamp` | datetime64[ns,UTC] | — | minute index | never missing |
| `czt1temp`, `czt2temp`, `cdte1temp`, `cdte2temp` | float64 | °C | minute **mean** | detector temperatures |
| `czthvmon`, `cdtehvmon` | float64 | V | minute **mean** | high-voltage monitors |
| `czt1ctr`, `czt2ctr`, `cdte1ctr`, `cdte2ctr` | float64 | counts/s | minute **mean** | per-detector rate monitors |
| `czt1enth` | float64 | keV | minute **mean** | energy threshold |
| `cdte1enerthr`, `cdte2enerthr` | float64 | *(undeclared)* | minute **mean** | energy thresholds; unit not declared in the archive |
| `cdte1pilectr`, `cdte2pilectr` | float64 | count | minute **max** | pile-up counters |
| `czt1satctr1`, `czt2satctr1` | float64 | count | minute **max** | saturation counters |
| `czt1hotpixcnt`, `czt2hotpixcnt` | float64 | count | minute **max** | hot-pixel counters |
| `sunradeg`, `sundecdeg` | float64 | degrees | minute **mean** | Sun pointing |
| `fehkstat` | float64 | — | minute **mean** | front-end housekeeping status word |
| `suninfov` | bool | — | minute **min** (conservative: True only if **every** sample is True) | Sun-in-field-of-view |
| `n_samples` | int64 | count | HK records in the minute | ≥ 1 |
| `orbit_id`, `src_file`, `src_sha256`, `archive_version` | object | — | provenance | never missing |

> **Ordering:** the parser preserves **archive (telemetry-arrival) order** and never sorts. Source records contain sub-second out-of-order steps (`SCIENTIFIC_FINDINGS.md` F-3). All aggregations used here are order-independent. A consumer needing chronological order must call `app.v2.utils.timeseries.chronological_sort()` explicitly.

## T5 — `hel1os_spec_1min` (1,026,816 rows · 373 files)

One row per (minute, detector); HEL1OS spectra. Source: `hel1os_*_spectra_*.fits`.

| Column | Type | Units | Derivation | Allowed values | Missing semantics |
|---|---|---|---|---|---|
| `timestamp` | datetime64[ns,UTC] | — | minute index | — | never missing |
| `detector` | object | — | spectra detector | `CZT1`,`CZT2`,`CDTE1`,`CDTE2` | never missing |
| `counts` | object → **array[`detchans`]** float64 | counts | per-channel Σ over finite spectra in the minute | ≥ 0 | NaN per channel where absent |
| `stat_err` | object → array[`detchans`] float64 | counts | per-channel Σ of `STAT_ERR` | ≥ 0 | as above |
| `live_time_s` | float64 | s | Σ `EXPOSURE` of contributing spectra | ≥ 0 | never missing |
| `n_spectra` | int64 | count | spectra contributing to the minute | ≥ 1 | never missing |
| `chantype` | category | — | from `CHANTYPE` | `PHA` | never missing |
| **`detchans`** | int16 | count | channel-space size — **carried explicitly (r5)** | **341** (CZT) or **511** (CdTe) | never missing |
| `orbit_id`, `src_file`, `src_sha256`, `archive_version` | object | — | provenance | — | never missing |

> **Three incommensurable channel spaces** (F-4): SoLEXS PI **340**, HEL1OS CZT PHA **341**, HEL1OS CdTe PHA **511**. **Never concatenate `counts` arrays across families or instruments** — always filter by `detchans`/`detector` first. Channel indices are ordinal; no response matrix exists.

## T6 — `gti_intervals` (2,130 rows · 1 file)

Long-form good-time intervals, one row per interval.

| Column | Type | Units | Derivation | Notes |
|---|---|---|---|---|
| `instrument` | object | — | source instrument | `solexs` |
| `detector` | object | — | detector | `SDD2` (SDD1 contributes no intervals — F-12 inactive) |
| `start_utc` | datetime64[ns,UTC] | — | interval start | **inclusive** |
| `stop_utc` | datetime64[ns,UTC] | — | interval stop | **inclusive** |
| `duration_s` | float64 | s | `stop − start + 1` (**inclusive** convention) | > 0 always |
| `src_file`, `src_sha256` | object | — | provenance | never missing |

> A GTI-excluded second **may** carry a finite count (spec r5). The invariant is one-directional: `NaN(counts) ⇒ GTI-excluded`. The excess is unexplained (A-14 / F-2).

## T7 — `provenance_manifest` (5,199 rows · 1 file)

One row per parsed source file. Every canonical row traces here via `src_file`.

| Column | Type | Derivation | Notes |
|---|---|---|---|
| `src_file` | object | source path | join key; unique with (`product`,`detector`) |
| `src_sha256` | object | archive SHA-256 (Phase 0.5.1 manifest) | 64 hex |
| `instrument` | object | `solexs` / `hel1os` | — |
| `detector` | object | e.g. `SDD1`,`SDD2`,`CZT1`,`CDTE2` | `None` for whole-orbit products |
| `product` | object | `lc`,`pi`,`gti`,`hk`,`spectra`,`lightcurve`,`events` | — |
| `archive_version` | object | `v1.0`,`v1.1`,`V111`,… | — |
| `obs_date` | object | `YYYYMMDD` | — |
| `orbit_id` | object | HEL1OS orbit, else `None` | — |
| `creator` | object | producing pipeline, from the FITS header | e.g. `solexs_pipeline-1.4` |
| `processing_date` | object | header `DATE` | `None` for HEL1OS (no `DATE` header) |
| `rows_in` / `rows_out` | int64 | source rows / emitted rows | `0/0` legal for F-12 inactive detectors |
| `parser_version` | object | parser identity | `v2-0.5.2` |
| **`parsed_at_utc`** | object | **build wall-clock time** | **the one non-reproducible field** — excluded from content hashes |
| `time_epoch_resolution` | object | resolved time convention | `unix_seconds` (SoLEXS) / `relative_seconds` (HEL1OS spectra) / `mjd_days` |
| `assumptions_applied` | object → array[str] | assumptions recorded at parse | audit trail |

---

## Provenance behaviour (all tables)

1. Every canonical row carries `src_file` + `src_sha256`; **no row lacks provenance** (verified: 0 orphans, 0 duplicates, 0 missing).
2. `src_sha256` is the **archive** SHA-256 from the Phase 0.5.1 manifest — it pins the input, not the output.
3. HEL1OS tables additionally carry `orbit_id`, resolved by the Version Resolution Engine per (minute, detector). Two detectors in the same minute may legitimately have different `orbit_id`s at orbit boundaries.
4. Provenance columns are **not** measurements; they must not be used as features.

<!-- VERSION STATUS: CURRENT — CONTRACT -->
<!-- REASON: Phase 0.5.2 parser specification. Implementation must satisfy this contract. -->
<!-- DATE: 2026-07-17 -->

# Phase 0.5.2 — Real FITS Parser Specification (CONTRACT)

**Status: specification only. No parser code exists. This document is the contract the implementation must satisfy; deviations require a logged amendment, not a code change.**

**Method note (deviation declared).** This brief said "Do NOT parse FITS." Governing roadmap r1, self-review item 6, mandates the opposite for *structure*: "blind to outcomes, never to units/schemas" — the amendment written specifically because Experiment E measured the wrong object through schema-blindness. A schema contract authored blind to the schema would repeat that failure. I therefore performed **structure-only discovery**: HDU layouts, column names, declared units, header keywords, row counts. **No data distributions, no science values, no analysis.** Every schema statement below is `OBSERVED` from the real archive on 2026-07-17. This is specification input, not implementation.

---

## 1. Supported Archive Layouts

### 1.1 SoLEXS (436 daily archives, 3.47 GB)

```
AL1_SLX_L1_<YYYYMMDD>_v<1.0|1.1>/          ← outer stem (repeats inside the zip)
└── AL1_SLX_L1_<YYYYMMDD>_v<VER>/
    ├── SDD1/ AL1_SOLEXS_<date>_SDD1_L1.gti.gz          ← GTI ONLY
    └── SDD2/ AL1_SOLEXS_<date>_SDD2_L1.{gti,lc,pi}.gz  ← ALL science
        [v1.1 only] AL1_SOLEXS_<date>_SDD2_L1.hk.gz
        [v1.1 only] AL1_SOLEXS_<date>_SDD2_L1_lightcurve.png
```

`OBSERVED`, archive-wide (436/436): **`.lc` and `.pi` exist for SDD2 only; SDD1 supplies `.gti` only.** On 2024-05-14 the SDD1 GTI has **NAXIS2 = 0 (zero rows)** and its primary `TSTART`/`TSTOP` are **empty strings**. `INFERRED`: SDD1 contributed no usable science in the sampled archive; whether this holds for all 436 days is an implementation-time measurement, not an assumption.

**Version variants:** `v1.0` (431 archives, profile `{lc×1, pi×1, gti×2}`) and **`v1.1` (5 archives: 2024-10-01, 2024-10-25, 2024-12-12, 2025-01-19, 2025-02-02)**, which add `.hk.gz` housekeeping and a quicklook PNG. No date has both variants → **no SoLEXS version conflict exists** (verified: 436 archives, 436 unique dates, 0 duplicates).

### 1.2 HEL1OS (391 orbit archives, 132.10 GB)

```
HLS_<YYYYMMDD>_<HHMMSS>_<DUR>sec_lev1_V<XYZ>/
└── <YYYY>/<MM>/<DD>/HLS_.../
    ├── events/evt.fits                       ~219 MB, 4 detector HDUs
    ├── czt/  lightcurve_czt{1,2}.fits, hel1os_czt_spectra_czt{1,2}.fits
    ├── cdte/ lightcurve_cdte{1,2}.fits, hel1os_cdte_spectra_cdte{1,2}.fits
    └── aux/  hk.fits, gticzt{1,2}.fits, gticdte{1,2}.fits, cztdis/czt{1,2}dispix.txt
```

`OBSERVED`: **1 structural profile across all 391 archives** — perfectly uniform. Granularity is **orbit** (~2/day, ~12 h each), not day. `czt2dispix.txt` is zero-byte in all 391 (benign, recorded).

### 1.3 Anomalies carried from Phase 0.5.1

| Anomaly | Count | Spec response |
|---|---|---|
| SoLEXS v1.1 with extra `.hk.gz` + `.png` | 5 archives | Parse `.hk` where present (§2.5); PNG ignored by allowlist, logged |
| HEL1OS time-overlapping orbit pairs | 46 | §4 version policy — **hard requirement** |
| Zero-byte `czt2dispix.txt` | 391 | Not consumed; allowlist excludes |
| SDD1 empty GTI | ≥1 confirmed | Fail-loud rule F-12 → `sdd1_active=False`, not an error |
| Genuinely lost date 2023-12-13 | 1 | Out of scope; 0.5.3 acquisition |

---

## 2. Parsing Specification per File Type

### 2.1 SoLEXS `.lc.gz` — light curve

**Purpose:** total-band count time series. **Schema `OBSERVED`:** HDU0 `PRIMARY`; HDU1 `RATE` (BinTableHDU, OGIP `HDUCLAS1='LIGHTCURVE'`, `HDUCLAS2='TOTAL'`, **`HDUCLAS3='COUNTS'`**).
**Columns:** `TIME` (D, **unit undeclared**), `COUNTS` (D, **unit undeclared**). `NAXIS2 = 86400`.
**Timestamps:** `MJDREFI=40587`, `MJDREFF=0` → **MJD 40587 = 1970-01-01 = Unix epoch**; `TIMESYS='UTC'`, `TIMEUNIT='s'`, `TIMEDEL=1`, `TIMZERO=0`. **∴ `TIME` = Unix seconds UTC.** Verified: `TSTART=1715644800.0` = 2024-05-14T00:00:00Z.
**Units:** despite `EXTNAME='RATE'`, `HDUCLAS3='COUNTS'` declares the values are **counts per 1-s bin**, not a rate. The parser MUST use `HDUCLAS3`, never `EXTNAME`, to decide semantics (F-07).
**Coordinate system:** none (non-imaging, Sun-pointed photometry). No spatial columns exist.
**Missing values (AMENDED r2 — see §10 / CONTRADICTION-002):** **SoLEXS `COUNTS` uses NaN as the missing-data sentinel.** On the validated reference archive the **NaN set is exactly equal to the GTI-excluded set**. NaN values represent **absent measurements**. **Zero remains a valid physical count** and MUST NOT be treated as missing.

**Parser behaviour (binding).** NaN values MUST: pass through **unchanged**; **never** be imputed; **never** be converted to zero; **never** be removed. The parser is responsible **only** for preserving them — all interpretation happens at aggregation (§3).

`OBSERVED` on 2024-05-14 SDD2: 5 NaN at day-offsets **[0, 5, 30072, 30078, 83951]**, identical to the GTI-excluded set; 0 NaN inside GTI; 0 finite outside GTI; finite count **86,395 == `EXPOSURE`**. *(This independently re-confirms the r1 inclusive convention: under the exclusive reading GTI would exclude ~10 s and could never match the 5 NaNs.)*

**Scope (§8 A-9):** VERIFIED on the reference archive only. Milestone VIII MUST verify the invariant across all **436** SoLEXS archives; any violation is a scientific finding and **TERMINATES validation**.
**Metadata to capture:** `MISSION, TELESCOP, INSTRUME, ORIGIN, CREATOR, FILENAME, OBS_DATE, OBS_ID, DATE (processing date), FILTER (=SDD2), TSTART, TSTOP, TIMEDEL, NUMBAND`.
**Validation:** `NAXIS2==86400`; `TIME` **finite** and strictly increasing, Δ==1 s (**F-16** — a NaN timestamp would silently defeat the monotonicity test, since all NaN comparisons are False); `TSTART==TIME[0]`; `OBS_DATE` matches path date; `FILTER` matches directory SDD; `TIMESYS=='UTC'`; `MJDREFI==40587` (F-05 if not). **`COUNTS` finiteness is NOT validated at parser level — NaN is data, not an error** (r2). Frozen F-19 covers negative counts only and is inherently NaN-safe (`NaN < 0` is `False`).

**Cross-product integrity (AMENDED r2 — REQUIRED archive-consistency check).** For **every** parsed SoLEXS day: **`NaN(COUNTS)` set MUST equal the GTI-excluded second set exactly.** Any mismatch **terminates validation via F-09**. This is materially stronger than either product can assert alone: it validates the light curve against its GTI *and* re-verifies the inclusive convention on every day. It requires both `.lc` and `.gti` and is therefore enforced at the day-assembly layer (Milestone VII), not inside the single-file `.lc` parser.

### 2.2 SoLEXS `.pi.gz` — spectra **(the scientific core)**

**Purpose:** per-second spectra. **`OBSERVED`:** HDU1 `SPECTRUM`, OGIP **Type II PHA** (`HDUCLAS4='TYPE:II'`), **`DETCHANS=340`**, **`CHANTYPE='PI'`** (gain-corrected pulse-invariant), `HDUCLAS3='COUNTS'`, `POISSERR=False`, `AREASCAL=1.0`, `CORRSCAL=1.0`, `FILTER='SDD2'`.
**Columns:** `TSTART` (D, `s`), `TELAPSE` (D, `s`), `SPEC_NUM` (J), `CHANNEL` (**340K**), `COUNTS` (**340D**), `EXPOSURE` (D, `s`). `NAXIS2 = 86400` → **one 340-channel spectrum per second**.
**Timestamps:** `TSTART` per row, unit `s`; epoch inherited from the same mission convention (Unix). **Validation rule V-PI-3 must confirm `TSTART[0]` equals the `.lc` `TSTART` for the same day; mismatch → F-06.**
**Units:** `COUNTS` = counts per `EXPOSURE` seconds in each channel. **`CHANNEL` is an ordinal PI index, NOT energy.**
> **CRITICAL GAP `OBSERVED`: no RMF/ARF response file exists anywhere in the archive.** SoLEXS PI-channel → keV conversion is therefore **impossible from archive contents alone**. **Binding rule: no v2 artifact may state a SoLEXS energy in keV until a response file is acquired.** Channels are ordinal indices only. Escalated to 0.5.3 as an acquisition item, ranked second only to the HEL1OS gap. (Contrast §2.6: HEL1OS ships calibrated keV.)

**Missing values:** none declared; use GTI + `EXPOSURE`.
**Validation:** `DETCHANS==340`; every row's `CHANNEL` vector identical (constant map) → else F-08; `COUNTS.shape==(86400,340)`; `EXPOSURE>0` within GTI; `CHANTYPE=='PI'`.
**Volume note (design-binding):** `NAXIS1=5468 B × 86400` ≈ **472 MB/day decompressed**; 436 days ≈ **206 GB**. The parser MUST stream day-by-day and MUST NOT hold multiple days of `COUNTS` in memory (16 GB RAM). `CHANNEL` is 235 MB/day of pure redundancy — read once, validate constant, discard.

### 2.3 SoLEXS `.gti.gz` — good time intervals

**Purpose:** live-time intervals. **`OBSERVED`:** HDU1 `GTI`, OGIP; columns `START` (D), `STOP` (D), **units undeclared**; primary `TSTART`/`TSTOP` are **ISO-8601 strings** (`'2024-05-14T00:00:01+00:00'`) while HDU1 `EXPOSURE` is a **string** (`'86395.0'`).
**Timestamps:** `START`/`STOP` are **Unix seconds** — verified: first row `1715644801.0` = 2024-05-14T00:00:01Z, consistent with the primary ISO string.

**Interval convention (AMENDED r1 — see §10 CONTRADICTION-001).** `START`/`STOP` are **INCLUSIVE second-marks** at 1-s sampling:

> **`live_time(interval) = STOP − START + 1`**

`OBSERVED` on 2024-05-14 SDD2: 5 intervals; `Σ(STOP−START+1) = 86395.0 s` = declared `EXPOSURE` with **exactly zero error**; independent second-coverage confirms 86,395 of 86,400 s. The excluded seconds are day-offsets **[0, 5, 30072, 30078, 83951]** — second 0 (data begins 00:00:01, matching the primary ISO `TSTART`) plus four isolated 1-s dropouts. *(The pre-amendment reading — "4 gaps of ~2 s" — was an artifact of the exclusive assumption.)*

**Scope of the convention (binding, §8 A-8):** VERIFIED for the implementation target (2024-05-14 SDD2) only. **It is NOT promoted to universal archive truth.** Milestone VIII MUST verify exact equality across all **436** SoLEXS archives; **any deviation is a scientific finding and MUST terminate validation** (never tolerate, never widen).

**Validation:** `START<STOP` per row; rows sorted and non-overlapping; **`Σ(STOP−START+1) == EXPOSURE` (EXACT equality, tolerance 0 s)** → else F-09; all intervals within `[OBS_DATE 00:00, 23:59:59]`; **NAXIS2==0 is legal** → detector inactive (F-12 path).

### 2.4 SoLEXS `.hk.gz` — housekeeping (**v1.1 only, 5 days**)

**Purpose:** instrument state. **`OBSERVED`:** HDU1 `HK`, `NAXIS2=86400`; columns `SDD_TEMP, ELECTRONIC_BOX_TEMPERATURE, COOLER_CURRENT, BACK_CONTACT, SUN_ANGLE, HV_ENABLE, RESET_ENABLE, FLARE_TRIGGER, FAST_COUNTS_LOW, FAST_COUNTS_MED, FAST_COUNTS_HIGH, FAST_COUNTS, SLOW_COUNTS` — **all units undeclared (unit=None on every column)**.
`FLARE_TRIGGER` is an onboard flare flag; `HV_ENABLE` is gain-relevant. **Constraint `OBSERVED`: SoLEXS instrument state exists for only 5 of 436 days (1.1%)** — Phase 1a cannot characterise SoLEXS gain/mode from housekeeping across the archive. Escalate to 0.5.3.
**Validation:** parse only where present; never synthesise; absence is normal for v1.0 (not an error).

### 2.5 HEL1OS `evt.fits` — event lists

**Purpose:** photon events. **`OBSERVED`:** HDU1-4 = `CDTE1-EVENTS`, `CDTE2-EVENTS`, `CZT1-EVENTS`, `CZT2-EVENTS`; ~1.3–1.6 M rows per detector per orbit; `DETNAM` per HDU.
**Columns:** `mjd` (D), `hlsobt` (D, `s`), `currtemp` (D, `degC`), `chn` (I), `ener` (D, **`keV`**), `recnum` (J), `utc-isot` (23A); **CZT additionally** `pix` (B), `offsetchn` (I).
**Timestamps:** header `TSTART/TSTOP` in **MJD** (61017.0000988685 = 2025-12-08); columns provide `mjd`, spacecraft `hlsobt`, and an ISO string — **three redundant representations**. Canonical = `mjd`; `utc-isot` is a cross-check (V-EVT-2).
**Units:** `ener` is **already energy-calibrated in keV** (unlike SoLEXS). `currtemp` is a per-event detector temperature.
**Validation:** all 4 HDUs present (F-03); `DETNAM` matches EXTNAME; `mjd` non-decreasing; `ener>0`; `mjd` within `[TSTART,TSTOP]`.
**Volume:** 85.7 GB total. **Not required for the canonical tables** — retained for Phase 1a pile-up/gain work. The 0.5.2 parser MUST expose an event reader but MUST NOT ingest events into the canonical minute tables.

### 2.6 HEL1OS `lightcurve_{czt,cdte}{1,2}.fits` — band light curves

**Purpose:** per-detector, per-band rates. **`OBSERVED`:** 5 BinTable HDUs per file, **one per energy band, band edges encoded in `EXTNAME`**:
- **CZT1/CZT2:** `20–40`, `40–60`, `60–80`, `80–150` keV + total `18–160` keV
- **CdTe1/CdTe2:** `5–20`, `20–30`, `30–40`, `40–60` keV + total `1.8–90` keV

**Columns:** `MJD` (D, `MJD`), `ISOT` (30A, `UT`), **`CTR` (D, `cts/sec`)**, `STAT_ERR` (D, `cts/sec`). `NAXIS2 ≈ 43171` ≈ 1 s cadence over a ~12 h orbit.
**Units:** `CTR` is a **rate** with units **declared** — the opposite convention from SoLEXS `.lc` (undeclared counts). The parser MUST NOT assume a shared convention across instruments (F-07).
**Validation:** exactly 5 band HDUs per file; band edges parse from `EXTNAME` against the expected set above → mismatch = F-10 (**never silently accept an unknown band**); `CTR ≥ 0`; `MJD` strictly increasing.
**Design rule:** band edges are **parsed from `EXTNAME` and validated against the allowlist**, never hardcoded by position — HDU order is not a contract.

### 2.7 HEL1OS `hel1os_{czt,cdte}_spectra_{det}.fits`

**Purpose:** per-detector spectra. **`OBSERVED`:** HDU1 `SPECTRUM`, Type II, **`DETCHANS=341`**, **`CHANTYPE='PHA'`**, `HDUCLAS3='COUNT'` (singular).
**Columns:** `SPEC_NUM` (I), `CHANNEL` (341J), `COUNTS` (341D, **`cts`**), `STAT_ERR` (341D), `ROWID` (12A), `TSTART` (D, `s`), `TSTOP` (D, `s`), `EXPOSURE` (D, `s`). `NAXIS2 = 2157` over a 43178 s orbit → **~20 s cadence**.
> **AMBIGUITY `OBSERVED` — must be resolved empirically, not assumed:** column `TSTART` declares unit `s`, but header `TSTART` is **MJD** (61017.0). The column epoch is undetermined from metadata. **Resolution rule R-1:** at implementation, test the column against both hypotheses (Unix-s and MJD-days) and accept the one reproducing the header `TSTART/TSTOP` span to <1 s; if neither fits → **F-06, terminate**. The chosen interpretation is recorded in the provenance table.

**Note the cross-instrument asymmetry (do not conflate):** SoLEXS = 340 **PI** channels @ 1 s; HEL1OS = 341 **PHA** channels @ ~20 s. `PI ≠ PHA` (gain-corrected vs raw pulse height) and 340 ≠ 341. **No v2 code may treat these as a common channel space** (F-11).

### 2.8 HEL1OS `aux/hk.fits` — housekeeping (**Phase 1a's key asset**)

**Purpose:** instrument state, orbit-resolved. **`OBSERVED`:** HDU1 `HLSHK`; ~60 columns including — decisive for Phase 1a:
- **Pile-up:** `cdte1pilectr`, `cdte2pilectr` (pile-up counters)
- **Saturation:** `czt1satctr1`, `czt2satctr1`
- **Gain/HV:** `czthvmon` (V), `cdtehvmon` (V), `czt1enth` (keV), `cdte1enerthr`, `cdte2enerthr`
- **Thermal:** `czt1temp`, `czt2temp`, `cdte1temp`, `cdte2temp` (degC)
- **Detector health:** `czt{1,2}hotpix`, `hotpixcnt`, `hotpixthr`, `hotpixlgcstat`, `bunpxctr`, `fehkstat`
- **Rates:** `czt1ctr`, `czt2ctr`, `cdte1ctr`, `cdte2ctr` (`c/s`)
- **Pointing:** `sunradeg`, `sundecdeg`, **`suninfov`**, `sun2yawdeg`, `sun2rolldeg`, `sun2pitchdeg`
- **Time:** `mjd`, `l0dhobt`, plus decomposed `l0utc{yr,mon,dy,hr,min,sc,msc}`

**Binding rule:** `suninfov` is a **first-class quality flag** — data outside Sun-in-FOV is not solar signal. It MUST propagate to the canonical tables (§3).
**Validation:** `mjd` non-decreasing; `czt1temp`/`czt2temp` finite; `suninfov ∈ {0,1}`.
**Note:** `czt1enth` has unit `keV` but `czt2enth` has **unit=None** for the same physical quantity — a metadata inconsistency; the parser applies the `czt1enth` unit to both and records the assumption (§8 A-4).

### 2.9 HEL1OS `aux/gti{czt,cdte}{1,2}.fits`

**`OBSERVED`:** HDU1 `GTI_<DET>`; columns **lowercase** `tstart`, `tstop` (D, units undeclared); `NAXIS2 = 1` on the sample orbit. **Column-name case differs from SoLEXS (`START`/`STOP` uppercase)** → all column access MUST be case-insensitive (§8 A-2).

---

## 3. Canonical Output Schema (**stable for all of v2**)

Format: Parquet, one file per instrument-product per UTC day, partitioned `year=/month=`. Index: `timestamp` (UTC, tz-aware, `datetime64[ns]`), **1-minute cadence**, monotonic, no duplicates.

**Cadence rationale:** 1 min matches the v2 modelling cadence and the inherited harness; native resolution (1 s SoLEXS, ~20 s HEL1OS spectra) remains available from L1 for Phase 1a. Time-averaging to 1 min is declared as the *only* permitted aggregation at this stage; **no spectral aggregation is performed** — all 340/341 channels are retained (roadmap r1: "no lossy aggregation before the capability study").

**Aggregation contract (AMENDED r2 — binding for T1/T2).** Aggregation is defined over **finite observations only** (`np.nansum` semantics). **One NaN MUST NEVER invalidate an otherwise valid minute** — a naive `sum()` over a minute containing a single NaN returns NaN and silently destroys up to 1,439 good seconds. A minute containing **no finite observations** is represented as `counts_total = NaN`, `q_no_data = True`. **No imputation. No filling.**

### T1 `solexs_lc_1min`
| column | dtype | unit | notes |
|---|---|---|---|
| `timestamp` | datetime64[ns, UTC] | — | index, 1-min |
| `counts_total` | float64 | counts | Σ over **finite** seconds in the minute (r2); NaN iff no finite second exists |
| `live_time_s` | float64 | s | GTI∩minute |
| `rate_total` | float64 | **cts/s** | `counts_total/live_time_s`; NaN if `live_time_s==0` |
| `gti_fraction` | float64 | — | `live_time_s/60` ∈[0,1] |
| `n_seconds_present` | int16 | — | **finite** seconds found in `.lc` (r2) |
| `q_no_data` | bool | — | no finite observation in the minute (r2) |
| `q_partial` | bool | — | `0<gti_fraction<1` |
| `detector` | category | — | `'SDD2'` |
| `src_file` | string | — | provenance |
| `src_sha256` | string | — | provenance (member SHA from 0.5.1) |
| `archive_version` | category | — | `v1.0`/`v1.1` |

### T2 `solexs_spec_1min`
`timestamp`; `counts` **`list<double>[340]`** (Σ over **finite** seconds, channel-wise, per the r2 aggregation contract); `live_time_s` float64; `channel_index` list<int32>[340] (validated constant, stored once in T7); `q_*` flags; provenance as T1.
**`channel_energy_keV` is ABSENT BY DESIGN** — no RMF exists (§2.2). Adding it later requires a schema revision + an acquired response file.

### T3 `hel1os_lc_1min`
`timestamp`; then per detector∈{czt1,czt2,cdte1,cdte2} × band: `{det}_{lo}_{hi}_rate` float64 **cts/s** and `{det}_{lo}_{hi}_stat_err` float64 cts/s (band edges from §2.6, e.g. `czt1_20_40_rate`, `cdte1_5_20_rate`); `{det}_live_time_s`; `{det}_gti_fraction`; `q_suninfov` bool; `q_no_data` bool; `orbit_id` string; `orbit_version` string; provenance.

### T4 `hel1os_hk_1min`
`timestamp`; `czt1temp, czt2temp, cdte1temp, cdte2temp` (degC); `czthvmon, cdtehvmon` (V); `cdte1pilectr, cdte2pilectr, czt1satctr1, czt2satctr1` (counters, minute-max); `czt1hotpixcnt, czt2hotpixcnt`; `czt1enth, cdte1enerthr, cdte2enerthr`; `suninfov` (bool, minute-min = conservative); `sunradeg, sundecdeg`; `fehkstat`; provenance.

### T5 `hel1os_spec_1min`
`timestamp`; `detector` category; `counts` list<double>[**341**]; `stat_err` list<double>[341]; `live_time_s`; `chantype` category (`'PHA'`); provenance. **Kept separate from T2 — different channel space (F-11).**

### T6 `gti_intervals` (long)
`instrument`, `detector`, `start_utc`, `stop_utc` (datetime64[ns,UTC]), `duration_s`, `src_file`, `src_sha256`.

### T7 `provenance_manifest`
One row per parsed source file: `src_file`, `src_sha256` (must equal 0.5.1 manifest → F-13), `instrument`, `detector`, `product`, `archive_version`, `obs_date`, `orbit_id`, `creator`, `processing_date` (`DATE`), `rows_in`, `rows_out`, `parser_version`, `parsed_at_utc`, `time_epoch_resolution` (R-1 outcome), `assumptions_applied` (list).

**Quality-flag convention (uniform):** `q_*` are booleans, **True = problem**. Never impute; never fill. Absent data is `NaN` + `q_no_data=True`.

---

## 4. Version-Selection Policy (HEL1OS) — **naive ingestion made impossible**

**Identification.** Filename regex `HLS_(?P<date>\d{8})_(?P<start>\d{6})_(?P<dur>\d+)sec_lev1_V(?P<ver>\d{3})`. `OBSERVED` distribution: V111 ×371, V211 ×16, V112 ×3, V311 ×1. **The semantics of the three digits are undocumented in the archive** — treated as opaque (§8 A-1).

**Precedence (deterministic, applied in order):**
1. Higher `ver` integer wins (V311 > V211 > V112 > V111).
2. Tie → longer `dur` wins (more coverage).
3. Tie → later header `DATE` (processing date) wins.
4. Still tied → **F-14 terminate**. Never coin-flip.

**Conflict resolution is at SAMPLE level, not file level.** Two overlap classes `OBSERVED`:
- **Class A — identical interval, different version** (e.g. `HLS_20251208_000008_43178sec_V111` vs `..._V211`): file-level selection by precedence.
- **Class B — partial overlap, different start/duration** (e.g. `20251207_120003_43195sec_V211` vs `20251207_121028_42570sec_V111`): file-level selection is **insufficient** — each covers seconds the other lacks.

**Mandatory mechanism.** The parser MUST build an explicit **minute-level coverage map** with provenance before emitting T3/T4/T5:
1. Enumerate every (minute, detector) each orbit file claims.
2. Any minute claimed by ≥2 files → resolve by precedence; **log every resolution** to `version_resolution_log.json` with winner, losers, and rule invoked.
3. A minute may have exactly one provenance row. Post-condition assert: `len(T3) == len(unique(T3.timestamp))` → else F-15.
4. The merge function MUST accept the coverage map as a required argument. **There is no API that concatenates orbit files directly** — this is the structural guarantee that naive ingestion cannot occur, rather than a convention someone must remember.

`OBSERVED`: 46 overlapping pairs exist; their `evt.fits` SHA-256 values **differ**, so they are genuine reprocessings, not byte-copies — deduplication by content hash would fail. Precedence is required.

**SoLEXS:** no version policy needed (436 archives = 436 unique dates, 0 conflicts). `v1.1` is a *superset* variant, not a competing version.

---

## 5. Fail-Loud Rules (Failure Matrix)

**Simulation fallback is permanently prohibited. No silent repair. No default-on-missing-key** (`header.get(K, default)` is banned for any physically meaningful key — that idiom is the direct cause of v1's thirty-sprint failure). Every rule below **terminates the run** with a diagnostic naming file, HDU, and expectation.

| ID | Condition | Rationale |
|---|---|---|
| F-01 | FITS unreadable / not FITS / gzip error | — |
| F-02 | Expected HDU absent by **name** (never by index) | HDU order is not a contract |
| F-03 | `evt.fits` lacking any of the 4 detector HDUs | Silent detector loss |
| F-04 | Column absent by name (case-insensitive lookup fails) | v1 sought `RATE`; real is `COUNTS` |
| F-05 | `MJDREFI≠40587` or `TIMESYS≠'UTC'` or `TIMEUNIT≠'s'` (SoLEXS) | v1 defaulted `MJDREF=58484` → ~49-yr error |
| F-06 | Epoch resolution R-1 fails, or `.pi TSTART[0] ≠ .lc TSTART` | Ambiguous time |
| F-07 | Declared unit contradicts assumption (`HDUCLAS3` vs `EXTNAME`; `cts/sec` vs counts) | Cross-instrument mismatch |
| F-08 | `.pi CHANNEL` vector not constant across rows | Channel map assumption void |
| F-09 | **`Σ(STOP−START+1)` ≠ `EXPOSURE` (EXACT, tolerance 0 s)** — *amended r1* | GTI inconsistent. Exact, not approximate: the relation is definitional, and a tolerance would re-admit the ambiguity that produced CONTRADICTION-001 |
| F-10 | Band `EXTNAME` outside the §2.6 allowlist | Unknown band silently ingested |
| F-11 | Any attempt to merge SoLEXS PI(340) with HEL1OS PHA(341) | Incommensurable channel spaces |
| F-12 | GTI `NAXIS2==0` **→ not fatal**: set `detector_active=False`, emit zero rows, log | Legal state (SDD1) |
| F-13 | Member SHA-256 ≠ 0.5.1 manifest | Archive mutated |
| F-14 | Version precedence unresolved after all tie-breaks | No coin-flips |
| F-15 | Duplicate `(timestamp, detector)` in output | Double-counting |
| F-16 | Timestamps non-monotonic or duplicated in input | — |
| F-17 | `NAXIS2` ≠ expected (86400 for SoLEXS daily) | Truncated product |
| F-18 | Unknown file type in archive not on allowlist | Unsupported structure |
| F-19 | Negative counts / negative `EXPOSURE` / `live_time_s > 60` | Physically impossible |
| F-20 | Output row count ≠ expected minutes for the day | Silent loss |

**F-12 is the single deliberate non-terminating rule** and is enumerated here so the exception is explicit rather than discovered.

---

## 6. Validation Protocol (≥3 manually inspected days)

**D1 — 2024-05-14 (mandated; GOES X8.7 at 16:51 UTC).** SoLEXS-only (**no HEL1OS exists before 2025-12-07**).
*Expected files:* `AL1_SLX_L1_20240514_v1.0` → SDD1 `.gti`(0 rows); SDD2 `.gti`(5 rows), `.lc`(86400), `.pi`(86400×340).
*Expected observations:* 1440 T1 rows; 1440 T2 rows; **live time exactly 86395 s** (`Σ(STOP−START+1)`); **5 excluded seconds at day-offsets [0, 5, 30072, 30078, 83951]** — second 0 plus four isolated 1-s dropouts *(amended r1; the earlier "4 gaps of ~2 s" was an exclusive-convention artifact — see §10)*.
*Acceptance:* all F-rules pass; T1 `rate_total` peak **within ±2 min of 16:51 UTC**; peak/quiet contrast ≥ 3×; T2 channel sums reconcile with T1 `counts_total` to ≤ 0.1%.
*Failure:* no peak within ±10 min of 16:51 → **STOP, escalate** (parser or archive wrong; do not proceed).

**D2 — combined-instrument flare day.** *Selection rule (deterministic, no cherry-picking):* the day in the 179-day SoLEXS∩HEL1OS window (2025-12-07…2026-06-15) with the **largest catalogued GOES peak flux**; ties → earliest.
*Expected files:* one SoLEXS daily archive + all HEL1OS orbits for that date (post version selection).
*Expected observations:* 1440 T1/T2 rows; T3/T4 rows only where orbits cover; `suninfov` present.
*Acceptance:* SoLEXS and HEL1OS peaks coincide within ±5 min; version resolution log non-empty **or** provably no overlap; zero F-15 duplicates.
*Failure:* instrument peaks disagree > 15 min → STOP (time-system error).

**D3 — quiet control.** *Selection rule:* the day in the overlap window with the **lowest catalogued peak flux** and ≥ 95 % GTI on both instruments.
*Acceptance:* no flare-like excursion; rates stable; `q_*` flags near-zero.
*Failure:* spurious excursions → STOP (background/artifact contamination).

**Common to all three:** every F-rule green; T7 provenance complete; SHA cross-check vs 0.5.1; a human-readable dump (counts, live time, flags) archived for manual inspection.

---

## 7. Scientific Sanity Checks (before any ML work)

| Check | Method | Pass criterion |
|---|---|---|
| **Flare-catalog coincidence** | Superposed-epoch of T1 `rate_total` about all catalogued M/X peaks in the SoLEXS window | Mean rate rises significantly at t=0 vs a matched-quiet baseline; **this is the 0.5.4 authenticity gate — the exact check v1 never ran** |
| **GTI correctness** | `Σ(STOP−START+1)` vs `EXPOSURE` (r1, exact); live time vs `n_seconds_present` | exact; no data outside GTI |
| **NaN⟺GTI bijection** *(new, r2 — REQUIRED)* | per day: `NaN(COUNTS)` set vs GTI-excluded second set | **exactly equal**; mismatch → **F-09**. Milestone VIII runs it across all 436 archives (A-9) |
| **Monotonic timestamps** | T1–T5 index | strictly increasing, unique, 1-min |
| **Plausible count rates** | T1/T3 distributions vs instrument design range | no negatives; quiet-Sun floor > 0; no non-physical spikes beyond saturation |
| **Detector consistency** | CZT1 vs CZT2, CdTe1 vs CdTe2 rate correlation on shared bands | high correlation; disagreement flagged, **not corrected** |
| **Spectrum integrity** | T2 channel-sum vs T1 `counts_total`; T5 vs T3 band sums | ≤ 0.1 % (SoLEXS); HEL1OS within band-definition tolerance |
| **Cross-instrument timing** | SoLEXS vs HEL1OS peak times on D2 | ≤ 5 min |

**Binding:** a failure here is a **scientific stop**, not a warning. No Phase 1 work proceeds on data that fails the coincidence check.

---

## 8. Self-Review — Falsification of This Specification

**Hidden assumptions (now explicit):**
- **A-1** HEL1OS version digits are ordinal (V311 > V211 > V111). *Undocumented.* Mitigation: opaque treatment + tie-breaks; if 0.5.3 obtains ISSDC documentation contradicting this, the policy is amended, not the data.
- **A-2** Column names are stable across 2.5 years. *Already falsified in miniature:* SoLEXS `START`/`STOP` vs HEL1OS `tstart`/`tstop`. → case-insensitive lookup mandatory.
- **A-3** SDD1 is inactive archive-wide. *Only one day sampled.* → measure per-day; never assume.
- **A-4** `czt2enth` shares `czt1enth`'s keV unit. *Metadata says unit=None.* → assumption recorded in T7.
- **A-5** SoLEXS `.pi TSTART` shares the `.lc` Unix epoch. → enforced by F-06, not assumed.
- **A-6** `.lc NUMBAND='4'` semantics unknown while only `TIME`/`COUNTS` columns exist. → captured as metadata, not interpreted.
- **A-7** The 1-min cadence is adequate. Defensible (matches harness) but it **is** an aggregation; native data remains reachable.
- **A-9** *(added r2)* The **NaN⟺GTI bijection** (`NaN(COUNTS)` set == GTI-excluded set) is **VERIFIED on the reference archive only** — 2024-05-14 SDD2, 1 of 436. **Milestone VIII MUST verify it across all 436 SoLEXS archives; any violation is a scientific finding that TERMINATES validation** — never tolerated, never absorbed. Same scoping discipline as A-8, and for the same reason: CONTRADICTION-001 and -002 both originated in a convention asserted from a single reading.
- **A-8** *(added r1)* The **inclusive** GTI convention (`live_time = STOP−START+1`) is **VERIFIED on 2024-05-14 SDD2 only** — one archive of 436. It is deliberately **NOT** promoted to universal archive truth. **Milestone VIII MUST test exact equality across all 436 SoLEXS archives; any deviation is a scientific finding that TERMINATES validation** and is reported, never tolerated and never absorbed by widening the tolerance. Rationale: this assumption is the direct descendant of CONTRADICTION-001, whose root cause was exactly a convention asserted from one reading without arithmetic verification.

**Ambiguous FITS fields:** `.pi`/HEL1OS-spectra `TSTART` epoch (R-1); `EXPOSURE` as string `'86395.0'`; SoLEXS primary `TSTART` as ISO string vs `.lc` HDU1 `TSTART` as float; SDD1 `TSTART=''`; `HDUCLAS3='COUNTS'` (SoLEXS) vs `'COUNT'` (HEL1OS); `EXTNAME='RATE'` containing counts.

**Parser failure modes anticipated:** memory blow-up on `.pi` (472 MB/day → streaming mandated); silent double-count on Class-B overlaps (→ §4 coverage map + F-15); band drift across versions (→ F-10 allowlist); epoch misinterpretation (→ F-05/F-06 — *the exact v1 defect*); zero-row GTI mistaken for failure (→ F-12); AppleDouble `._*` files on this exFAT volume being globbed as data (→ **F-18 allowlist must exclude `._*`** — `OBSERVED` present in the extracted store).

**Maintenance risks:** band edges live in `EXTNAME` strings (brittle → allowlist + F-10); the RMF gap blocks all SoLEXS energy claims indefinitely; 5-day SoLEXS housekeeping cannot support archive-wide gain characterisation; `evt.fits` at 85.7 GB will tempt future shortcuts (→ event ingestion is explicitly out of the canonical path).

**Revisions made during this self-review:** added F-18's `._*` exclusion; added R-1 as a *rule* rather than an assumption after finding the spectra `TSTART` unit/header contradiction; made §4's coverage map a **required function argument** rather than a documented convention, because "naive ingestion must be impossible" cannot be enforced by documentation; separated T2/T5 after observing 340-PI vs 341-PHA (an earlier draft had one spectral table — that would have been a silent scientific error).

**What this spec cannot guarantee:** that the archive is scientifically authentic (§7 / 0.5.4 decides that); that SoLEXS channels can ever be expressed in keV without an external RMF; that HEL1OS pre-2025-12 exists at ISSDC.

---

## 9. Deliverables Satisfied

Parser Specification (§1–2), Data Schema Specification (§3), Version Policy (§4), Failure Matrix (§5), Validation Protocol (§6–7), Self-Review Report (§8).

**Implementation may not begin until this contract is approved.**

---

## 10. Specification Revision History

### r0 — 2026-07-17, commit `6de0eb2` (frozen)
Original contract, grounded in structure-only schema discovery of the real archive.

### r1 — 2026-07-17 (owner-approved; raised by CONTRADICTION-001)

**Trigger.** Milestone II implementation proved r0 **impossible to satisfy**: rule F-09 as frozen (`Σ(STOP−START)` ≈ `EXPOSURE` ±1 s) *rejected the valid, mandated D1 reference file* `AL1_SOLEXS_20240514_SDD2_L1.gti.gz` — computing 86390.0 s against a declared `EXPOSURE` of 86395.0 s, a −5.0 s error outside the ±1.0 s tolerance. The parser correctly refused to parse the reference file of the reference day.

**Evidence (triple-confirmed, `OBSERVED`).** (a) `Σ(STOP−START+1)` = 86395.0 s = `EXPOSURE`, error **exactly 0.0 s**; the −5.0 s discrepancy equals the interval count precisely — the signature of an off-by-one endpoint convention, not of corrupt data. (b) Independent inclusive second-coverage = **86,395 / 86,400 s**, equal to `EXPOSURE` exactly. (c) The excluded seconds `[0, 5, 30072, 30078, 83951]` are physically coherent: second 0 (data begins 00:00:01, matching the primary ISO `TSTART`) plus four isolated 1-s dropouts.

**Root cause of the r0 defect.** When drafting §2.3 I asserted the standard OGIP *exclusive* convention **without summing the intervals**. Structure-only discovery captured the schema correctly but never tested the *arithmetic relationship between two fields* — a gap in the discovery method, not in the data. r0 was additionally **internally inconsistent**: §5 F-09 implied 86390 s while §6 D1 already stated "live time ≈ 86395 s"; the real data adjudicated for §6.

**Changes.** §2.3 — inclusive convention declared explicitly (`live_time = STOP−START+1`) with the measured excluded-second description replacing the inferred "4×2 s gaps". §5 F-09 — restated as `Σ(STOP−START+1) == EXPOSURE`, **tolerance tightened from ±1 s to EXACT**, because the relation is definitional and a tolerance would re-admit the ambiguity that caused the defect. §6 D1 — measured description substituted. §8 — assumption **A-8** added, scoping the convention to the verified target and mandating the 436-archive check at Milestone VIII with termination on any deviation.

**Unchanged.** Every other rule, schema, table, and policy of r0. This amendment narrows and sharpens; it weakens nothing.

**Disposition.** **CONTRADICTION-001: CLOSED** by this revision.

### r2 — 2026-07-17 (owner-approved; raised by CONTRADICTION-002)

**Trigger.** Milestone III implementation established that §2.1's missing-value clause — *"absence is expressed via GTI, not sentinels"* — is **factually false**. The real archive uses **NaN in `COUNTS` as a missing-data sentinel**. Unlike r1 the contract remained *satisfiable* (the clause was descriptive, not prescriptive), so Milestone III completed; but the clause would have licensed an incorrect aggregation strategy at Milestone VII.

**Evidence (`OBSERVED`, exact bijection).** 2024-05-14 SDD2: NaN `COUNTS` at day-offsets **[0, 5, 30072, 30078, 83951]** == GTI-excluded seconds **[0, 5, 30072, 30078, 83951]**; **0** NaN inside GTI; **0** finite outside GTI; finite count **86,395 == `EXPOSURE`**. The correspondence holds in both directions. **This independently re-confirms r1**: under the exclusive convention GTI would exclude ~10 s and could never match the 5 NaNs — two mutually confirming lines of evidence from different files now support the inclusive rule.

**Two defects, separated.** (A) *Implementation*: the M-III parser raised F-19 on non-finite `COUNTS`, an invented check — frozen F-19 covers negative counts only, and §2.1's validation list never mentioned finiteness. Fixed under the implementer's own authority; no contract change required. (B) *Contract*: the false clause, amended here.

**Changes.** §2.1 missing-value description replaced (NaN is the sentinel; zero remains a valid count); parser behaviour made binding (pass through unchanged; never impute, zero-fill, or remove); §2.1 validation clarified (`TIME` finiteness → F-16; `COUNTS` finiteness NOT validated — NaN is data); **new REQUIRED cross-product integrity rule** (`NaN(COUNTS)` set == GTI-excluded set, mismatch → **F-09**), enforced at the day-assembly layer since it needs both `.lc` and `.gti`; §3 **aggregation contract** added (finite-only aggregation; one NaN must never invalidate a minute; empty minute → `counts_total = NaN`, `q_no_data = True`; no imputation, no filling); §7 sanity-check table gains the bijection row; §8 gains **A-9** scoping the invariant to the reference archive with a Milestone VIII archive-wide obligation.

**Unchanged.** Every other rule, schema, table, and policy. The 20 fail-loud rule identifiers are untouched — r2 adds a new *application* of F-09, not a new rule. This amendment strengthens: it adds an integrity check the contract lacked and closes a silent data-destruction path at T1 before any code depended on it. **Nothing weakened.**

**Disposition.** **CONTRADICTION-002: CLOSED** by this revision.

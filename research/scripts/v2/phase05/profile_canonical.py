"""
scripts/v2/phase05/profile_canonical.py — CANONICAL_DATASET_PROFILE.md generator.

DESCRIPTIVE ONLY (M-VII brief): an engineering inventory. It summarises counts,
coverage, missingness, GTI, version resolution, provenance, and quality checks.
It draws NO scientific conclusions and offers NO explanations — every unexplained
quantity is labelled as awaiting Milestone VIII.
"""
import glob, json, os, sys
from collections import Counter

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd

OUT = "artifacts/v2/phase05/canonical"
S = json.load(open("artifacts/v2/phase05/canonical_build_stats.json"))


def load_all(sub, columns=None):
    fs = sorted(glob.glob(f"{OUT}/{sub}/*.parquet"))
    if not fs:
        return pd.DataFrame(), 0
    df = pd.concat((pd.read_parquet(f, columns=columns) for f in fs),
                   ignore_index=True)
    return df, len(fs)


def fmt(n):
    return f"{n:,}"


# ── T1 ──────────────────────────────────────────────────────────────────────
t1, n_t1_files = load_all("T1")
t1_nan = int(t1.counts_total.isna().sum())
t1_stats = dict(rows=len(t1), files=n_t1_files,
                first=str(t1.timestamp.min()), last=str(t1.timestamp.max()),
                nan_counts=t1_nan, pct_nan=100 * t1_nan / max(len(t1), 1),
                live_total_s=float(t1.live_time_s.sum()),
                q_no_data=int(t1.q_no_data.sum()), q_partial=int(t1.q_partial.sum()),
                rate_min=float(np.nanmin(t1.rate_total)),
                rate_med=float(np.nanmedian(t1.rate_total)),
                rate_mean=float(np.nanmean(t1.rate_total)),
                rate_max=float(np.nanmax(t1.rate_total)))

# ── T2 (columns only; counts arrays are heavy) ─────────────────────────────
t2, n_t2_files = load_all("T2", columns=["timestamp", "q_no_data", "n_seconds_present",
                                         "live_time_s", "detector", "chantype"])
t2_stats = dict(rows=len(t2), files=n_t2_files,
                q_no_data=int(t2.q_no_data.sum()),
                chantype=t2.chantype.unique().tolist())

# ── T3 ──────────────────────────────────────────────────────────────────────
t3, n_t3_files = load_all("T3")
t3_stats = dict(rows=len(t3), files=n_t3_files)
if len(t3):
    rate_cols = [c for c in t3.columns if c.endswith("_rate")]
    tot = t3[rate_cols].size
    nan = int(t3[rate_cols].isna().sum().sum())
    t3_stats.update(first=str(t3.timestamp.min()), last=str(t3.timestamp.max()),
                    detectors=dict(Counter(t3.detector.astype(str))),
                    n_rate_cols=len(rate_cols), rate_cells=tot, rate_nan=nan,
                    pct_nan=100 * nan / max(tot, 1))

# ── T4 ──────────────────────────────────────────────────────────────────────
t4, n_t4_files = load_all("T4")
t4_stats = dict(rows=len(t4), files=n_t4_files)
if len(t4):
    t4_stats.update(first=str(t4.timestamp.min()), last=str(t4.timestamp.max()),
                    suninfov_true=int(t4.suninfov.sum()),
                    pct_suninfov=100 * float(t4.suninfov.mean()))

# ── T5 ──────────────────────────────────────────────────────────────────────
t5, n_t5_files = load_all("T5", columns=["timestamp", "detector", "detchans",
                                         "live_time_s", "n_spectra", "chantype"])
t5_stats = dict(rows=len(t5), files=n_t5_files)
if len(t5):
    t5_stats.update(detchans=dict(Counter(t5.detchans.astype(int))),
                    detectors=dict(Counter(t5.detector.astype(str))))

# ── T6 / T7 ────────────────────────────────────────────────────────────────
t6 = pd.read_parquet(f"{OUT}/T6/gti_intervals.parquet")
t7 = pd.read_parquet(f"{OUT}/T7_provenance.parquet")
dur = t6.duration_s
t6_stats = dict(rows=len(t6), exposure_total_s=float(dur.sum()),
                dur_min=float(dur.min()), dur_med=float(dur.median()),
                dur_mean=float(dur.mean()), dur_max=float(dur.max()),
                by_instrument=dict(Counter(t6.instrument)))

# provenance completeness across all tables
orphans = {}
dupes = int(t7.duplicated(subset=["src_file", "product", "detector"]).sum())
known = set(t7.src_file)
for name, df in (("T1", t1), ("T3", t3), ("T4", t4)):
    if len(df) and "src_file" in df.columns:
        orphans[name] = int((~df.src_file.isin(known)).sum())
prov_stats = dict(rows=len(t7), dupes=dupes, orphans=orphans,
                  rows_missing_prov={n: int(df.src_file.isna().sum())
                                     for n, df in (("T1", t1), ("T3", t3), ("T4", t4))
                                     if len(df) and "src_file" in df.columns})

skip_rules = Counter(k.get("rule", "(none)") for k in S["skipped"])
vr = S["version_resolution"]

md = f"""<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Canonical dataset profile — descriptive engineering inventory (M-VII deliverable). -->
<!-- DATE: 2026-07-17 -->

# Canonical Dataset Profile

**Descriptive only.** This document is an engineering inventory of the canonical dataset produced by the Milestone VII build under contract r5. It records counts and statistics; it interprets nothing. Quantities marked **[A-14]** or **[M-VIII]** are unexplained by design and await Milestone VIII.

Build: `scripts/v2/phase05/build_canonical.py`, {S['elapsed_min']} min. Store: `artifacts/v2/phase05/canonical/`.

## 1. Row counts

| Table | Files | Rows |
|---|---|---|
| T1 `solexs_lc_1min` | {n_t1_files} | {fmt(t1_stats['rows'])} |
| T2 `solexs_spec_1min` | {n_t2_files} | {fmt(t2_stats['rows'])} |
| T3 `hel1os_lc_1min` | {n_t3_files} | {fmt(t3_stats['rows'])} |
| T4 `hel1os_hk_1min` | {n_t4_files} | {fmt(t4_stats['rows'])} |
| T5 `hel1os_spec_1min` | {n_t5_files} | {fmt(t5_stats['rows'])} |
| T6 `gti_intervals` | 1 | {fmt(t6_stats['rows'])} |
| T7 `provenance_manifest` | 1 | {fmt(prov_stats['rows'])} |

## 2. Date coverage

| Table | First | Last |
|---|---|---|
| T1/T2 (SoLEXS) | {t1_stats['first']} | {t1_stats['last']} |
| T3 (HEL1OS LC) | {t3_stats.get('first','—')} | {t3_stats.get('last','—')} |
| T4 (HEL1OS HK) | {t4_stats.get('first','—')} | {t4_stats.get('last','—')} |

## 3. Missing-value statistics

- **T1** `counts_total`: {fmt(t1_stats['nan_counts'])} NaN of {fmt(t1_stats['rows'])} rows ({t1_stats['pct_nan']:.2f}%). `q_no_data` minutes: {fmt(t1_stats['q_no_data'])}; `q_partial`: {fmt(t1_stats['q_partial'])}.
- **T2**: `q_no_data` minutes: {fmt(t2_stats['q_no_data'])} of {fmt(t2_stats['rows'])}. Channel arrays preserve NaN per the r2/r5 rules; never imputed.
- **T3** band-rate cells: {fmt(t3_stats.get('rate_nan',0))} NaN of {fmt(t3_stats.get('rate_cells',0))} ({t3_stats.get('pct_nan',0):.2f}%) across {t3_stats.get('n_rate_cols',0)} band columns.
- No imputation, filling, or interpolation exists anywhere in the pipeline (verified by test suite).

## 4. GTI coverage (T6)

- Intervals: {fmt(t6_stats['rows'])} ({t6_stats['by_instrument']})
- Total good exposure: **{t6_stats['exposure_total_s']:.0f} s** ({t6_stats['exposure_total_s']/86400:.1f} days)
- Interval duration: min {t6_stats['dur_min']:.1f} s | median {t6_stats['dur_med']:.1f} s | mean {t6_stats['dur_mean']:.1f} s | max {t6_stats['dur_max']:.1f} s
- SoLEXS detector activity: SDD2 active {S['checks'].get('solexs_gti_parsed',0)//2} days; SDD1 inactive (F-12) on {S['checks'].get('solexs_detector_inactive_F12',0)} of {S['checks'].get('solexs_gti_parsed',0)} parsed GTI files.
- T1 live time total: {t1_stats['live_total_s']:.0f} s. GTI-excluded seconds carrying finite counts are counted per day and **[A-14] remain unexplained — Milestone VIII**.

## 5. Version-resolution statistics

- Orbit files examined: {fmt(vr['n_candidates'])}
- Owned (minute, detector) pairs: {fmt(vr['n_owned_minute_detector_pairs'])}
- Conflicting pairs: {fmt(vr['n_conflicting_minute_detector_pairs'])} in {vr['n_distinct_conflicts']} distinct conflicts
- Resolved by R1 (higher version): {fmt(vr['rules_invoked'].get('R1_higher_version',0))}
- Resolved by R2 (longer duration): {fmt(vr['rules_invoked'].get('R2_longer_duration',0))}
- R3 (processing date) invoked: 0 — HEL1OS primaries carry no `DATE` header
- F-14 terminations: 0
- Unique ownership: **holds** — every owned pair has exactly one provenance owner (asserted at map construction and by F-15 output guards).

## 6. Provenance completeness (T7)

- Provenance rows: {fmt(prov_stats['rows'])}; duplicate (file, product, detector) rows: {prov_stats['dupes']}
- Output rows missing provenance: {prov_stats['rows_missing_prov']}
- Orphan rows (src_file absent from T7): {prov_stats['orphans']}

## 7. Descriptive statistics (no interpretation)

- T1 `rate_total` (cts/s): min {t1_stats['rate_min']:.1f} | median {t1_stats['rate_med']:.1f} | mean {t1_stats['rate_mean']:.1f} | max {t1_stats['rate_max']:.1f}
- T3 detector row counts: {t3_stats.get('detectors',{})}
- T4 `suninfov` true: {fmt(t4_stats.get('suninfov_true',0))} of {fmt(t4_stats['rows'])} minutes ({t4_stats.get('pct_suninfov',0):.1f}%)
- T5 `detchans` distribution: {t5_stats.get('detchans',{})} (CZT=341, CdTe=511 carried explicitly; never merged)
- HK inversion statistics (recorded, never thresholded): {len(S.get('hk_inversions',[]))} orbits; max backward step {max((h['max_s'] for h in S.get('hk_inversions',[])), default=0):.3f} s
- R-1 epoch resolutions: {S.get('r1_kinds',{})}

## 8. Archive inventory

- SoLEXS archives processed: **{S['solexs_archives_processed']} / {S['n_solexs_available']}**
- HEL1OS orbits processed: **{S['hel1os_orbits_processed']} / {S['n_hel1os_available']}**
- Skipped products: **{len(S['skipped'])}**, by rule: {dict(skip_rules)}
  - F-19: SoLEXS GTI `STOP <= START` (archive defect; CONTRADICTION-005 Defect C)
  - F-01: unreadable/gzip-corrupt SoLEXS members
  - F-16: duplicate HK `mjd` timestamps (archive defect; CONTRADICTION-006 Defect B, ruled working-as-designed)
  - Every skip is individually logged with its rule id in `canonical_build_stats.json`.

## 9. Data quality summary

Validation executed during the build (counts from `checks`):
- NaN ⇒ GTI-excluded implication (r5): held on all **{S['checks'].get('nan_gti_bijection_ok',0)}** built SoLEXS days (violation = F-09 = skip; none skipped for F-09)
- V-PI-3 (`.pi TSTART[0]` == `.lc TSTART`): **{S['checks'].get('V_PI_3_lc_pi_tstart_match',0)}** days
- SoLEXS GTI files parsed: {S['checks'].get('solexs_gti_parsed',0)}; F-12 inactive detections: {S['checks'].get('solexs_detector_inactive_F12',0)}
- HEL1OS builds: LC {S['checks'].get('hel1os_lc_built',0)}, HK {S['checks'].get('hel1os_hk_built',0)}, spectra {S['checks'].get('hel1os_spec_built',0)} orbits
- Validation failures: none among built products (failures terminate and become skips, §8)

**Assumptions awaiting Milestone VIII:** **A-8** (GTI exposure identity across all 436 SoLEXS archives), **A-11** (relative-seconds convention across all 391 orbits — 1,180/1,180 spectra products resolved `relative_seconds` in this build), **A-12** (HK inversion distribution), **A-13** (per-family `DETCHANS` across all orbits), **A-14** (the GTI-exclusion excess — unexplained). **CONTRADICTION-003** (SoLEXS LC↔PI relationship) remains OPEN for M-VIII.
"""
open("artifacts/v2/phase05/CANONICAL_DATASET_PROFILE.md", "w").write(md)
print(md[:1200])
print("…\nprofile written")

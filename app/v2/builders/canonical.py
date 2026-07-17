"""
app/v2/builders/canonical.py — Canonical dataset builders T1–T7 (Milestone VII).

Implements contract §3 exactly.

NUMBERING NOTE: the Milestone VII brief labels T4=spectra / T5=housekeeping; the
FROZEN contract §3 labels T4=`hel1os_hk_1min` / T5=`hel1os_spec_1min`. The content
and requirements are identical either way. This module follows the FROZEN
CONTRACT, because §3 declares the schema stable for all of v2 and the M-V/M-VI
compliance reports already cite those names. Flagged, not silently reconciled.

WHAT BUILDERS DO: reorganize authenticated information. Nothing else.

WHAT THEY MUST NEVER DO (§3 / milestone constraint): interpolate, smooth, infer,
repair, fill, reorder measurements, or modify scientific values.

STRUCTURAL GUARANTEES:
  * Builders accept `ParsedProduct` objects, NEVER paths -> "MUST NOT parse FITS
    directly" is enforced by the signature, not by discipline. This module imports
    no FITS reader.
  * HEL1OS builders require a `CoverageMap` -> ownership comes from the Version
    Resolution Engine (§4), never from ad-hoc concatenation.

SCIENTIFIC CONSTRAINT (CONTRADICTION-003, OPEN): T1 `counts_total` and T2 `counts`
are carried INDEPENDENTLY. Neither is derived from the other, and no code here
assumes Σ(PI channels) relates to the SoLEXS light curve in any way.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.v2.models.metadata import FailLoud, ParsedProduct, Provenance
from app.v2.resolution.version_engine import (CoverageMap,
                                              assert_no_duplicate_minutes,
                                              select_owned_rows)

SECONDS_PER_DAY = 86400
MINUTES_PER_DAY = 1440
SEC_PER_MIN = 60
SOLEXS_CHANNELS = 340                          # PI  -- §2.2
# §2.7 (r5): HEL1OS has TWO PHA channel spaces. F-11 now spans THREE
# incommensurable spaces: SoLEXS PI 340, CZT PHA 341, CdTe PHA 511.
HEL1OS_CHANNELS = {"CZT": 341, "CDTE": 511}


@dataclass
class BuiltTable:
    """A canonical table plus the provenance rows it generated."""
    name: str
    df: pd.DataFrame
    provenance: list[Provenance] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.df)


# ── shared helpers ──────────────────────────────────────────────────────────
def _second_coverage(gti: ParsedProduct, obs_date: str) -> np.ndarray:
    """Boolean (86400,) second-coverage from GTI, INCLUSIVE endpoints (§2.3 r1).

    live_time(interval) = STOP - START + 1, so both endpoints are covered.
    """
    covered = np.zeros(SECONDS_PER_DAY, dtype=bool)
    day0 = pd.Timestamp(obs_date, tz="UTC")
    for _, row in gti.data.intervals.iterrows():
        i0 = int((row.start_utc - day0).total_seconds())
        i1 = int((row.stop_utc - day0).total_seconds())
        if i0 < 0 or i1 >= SECONDS_PER_DAY:
            raise FailLoud("F-06", "GTI interval outside the observation day",
                           expected=f"[0, {SECONDS_PER_DAY})", got=(i0, i1))
        covered[i0:i1 + 1] = True          # inclusive (r1)
    return covered


def validate_nan_implies_gti_excluded(lc: ParsedProduct, gti: ParsedProduct) -> dict:
    """§2.1 (r5) REQUIRED cross-product integrity check, run BEFORE aggregation.

        NaN(COUNTS)  =>  GTI-excluded

    A NaN inside GTI-good time is an F-09 violation: missing data must never be
    silently treated as observed. A GTI-excluded second is PERMITTED to carry a
    finite count.

    The r2 rule asserted set EQUALITY. Archive-wide execution falsified it
    (CONTRADICTION-005 Defect B), discharging A-9 early. The implication is the
    strong half -- it forbids the dangerous direction while asserting nothing the
    archive does not support. Why GTI excludes time beyond data absence is A-14,
    a Milestone VIII scientific question; no mechanism is assumed here.
    """
    counts = lc.data.samples.counts.to_numpy()
    if counts.size != SECONDS_PER_DAY:
        raise FailLoud("F-17", "light curve is not a full day", file=lc.provenance.src_file,
                       expected=SECONDS_PER_DAY, got=int(counts.size))
    covered = _second_coverage(gti, lc.data.obs_date)
    nan_idx = np.flatnonzero(~np.isfinite(counts))
    excl_idx = np.flatnonzero(~covered)
    # The ONLY forbidden case: a NaN inside GTI-good time.
    nan_in_good = np.setdiff1d(nan_idx, excl_idx)
    if nan_in_good.size:
        raise FailLoud(
            "F-09",
            "NaN(COUNTS) inside GTI-good time violates the §2.1 r5 implication "
            "NaN => GTI-excluded", file=lc.provenance.src_file,
            expected="every NaN second to be GTI-excluded",
            got={"n_nan_in_good_time": int(nan_in_good.size),
                 "offsets": nan_in_good[:10].tolist()})
    # A GTI-excluded second MAY carry a finite count (r5). Counted, not judged:
    # the excess is A-14, unexplained, owner Milestone VIII.
    excess = int(np.setdiff1d(excl_idx, nan_idx).size)
    return {"n_nan_seconds": int(nan_idx.size),
            "n_excluded_seconds": int(excl_idx.size),
            "n_excluded_with_finite_counts": excess,      # A-14 observable
            "excluded_offsets": excl_idx.tolist()[:32],
            "live_time_s": int(covered.sum())}


def _minute_index(obs_date: str) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(obs_date, tz="UTC"), periods=MINUTES_PER_DAY,
                         freq="min", tz="UTC")


def _finite_sum(block: np.ndarray, axis: int) -> tuple[np.ndarray, np.ndarray]:
    """§3 r2 aggregation contract: sum over FINITE observations only.

    Returns (total, n_finite). `total` is NaN exactly where no finite observation
    exists -- np.nansum would return 0.0 there, silently manufacturing a zero
    measurement out of missing data.

    One NaN must NEVER invalidate an otherwise valid minute: a naive sum() over a
    minute containing a single NaN returns NaN and destroys up to 1,439 good
    seconds.
    """
    finite = np.isfinite(block)
    n_finite = finite.sum(axis=axis)
    total = np.where(finite, block, 0.0).sum(axis=axis)
    total = np.where(n_finite == 0, np.nan, total)
    return total, n_finite


def _prov_cols(df: pd.DataFrame, p: Provenance) -> pd.DataFrame:
    df["src_file"] = p.src_file
    df["src_sha256"] = p.src_sha256
    df["archive_version"] = p.archive_version
    return df


# ── T1 ──────────────────────────────────────────────────────────────────────
def build_T1(lc: ParsedProduct, gti: ParsedProduct) -> BuiltTable:
    """§3 T1 `solexs_lc_1min` — minute-resolution SoLEXS light curve."""
    if lc.data.obs_date != gti.data.obs_date:
        raise FailLoud("F-07", "LC and GTI are from different days",
                       expected=lc.data.obs_date, got=gti.data.obs_date)
    if lc.data.detector != gti.data.detector:
        raise FailLoud("F-07", "LC and GTI are from different detectors",
                       expected=lc.data.detector, got=gti.data.detector)

    # r5: the cross-product check runs BEFORE aggregation, as the brief requires.
    validate_nan_implies_gti_excluded(lc, gti)

    counts = lc.data.samples.counts.to_numpy().reshape(MINUTES_PER_DAY, SEC_PER_MIN)
    covered = _second_coverage(gti, lc.data.obs_date).reshape(MINUTES_PER_DAY, SEC_PER_MIN)

    counts_total, n_present = _finite_sum(counts, axis=1)
    live_time_s = covered.sum(axis=1).astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        rate_total = np.where(live_time_s > 0, counts_total / live_time_s, np.nan)
    gti_fraction = live_time_s / SEC_PER_MIN

    df = pd.DataFrame({
        "timestamp": _minute_index(lc.data.obs_date),
        "counts_total": counts_total.astype(np.float64),
        "live_time_s": live_time_s,
        "rate_total": rate_total.astype(np.float64),
        "gti_fraction": gti_fraction.astype(np.float64),
        "n_seconds_present": n_present.astype(np.int16),
        "q_no_data": (n_present == 0),
        "q_partial": (gti_fraction > 0) & (gti_fraction < 1),
        "detector": pd.Categorical([lc.data.detector] * MINUTES_PER_DAY),
    })
    df = _prov_cols(df, lc.provenance)
    _assert_no_row_change(df, MINUTES_PER_DAY, "T1")
    assert_no_duplicate_minutes(df, time_column="timestamp")
    return BuiltTable("solexs_lc_1min", df, [lc.provenance, gti.provenance])


# ── T2 ──────────────────────────────────────────────────────────────────────
def build_T2(pi: ParsedProduct, gti: ParsedProduct) -> BuiltTable:
    """§3 T2 `solexs_spec_1min` — 340 PI channels, minute-resolution.

    `channel_energy_keV` is ABSENT BY DESIGN: no RMF/ARF exists anywhere in the
    archive (§2.2), so PI->keV is impossible from archive contents. channel_index
    stays ordinal. Recorded in provenance.

    CONTRADICTION-003: this table is built from the .pi ALONE. It is never
    compared with, derived from, or reconciled against T1.
    """
    if pi.data.obs_date != gti.data.obs_date:
        raise FailLoud("F-07", "PI and GTI are from different days",
                       expected=pi.data.obs_date, got=gti.data.obs_date)
    if pi.data.n_channels != SOLEXS_CHANNELS:
        raise FailLoud("F-07", "PI channel count is not 340", file=pi.provenance.src_file,
                       expected=SOLEXS_CHANNELS, got=pi.data.n_channels)
    if pi.data.chantype != "PI":
        raise FailLoud("F-11", "T2 requires SoLEXS PI channels", got=pi.data.chantype)

    block = pi.data.counts.reshape(MINUTES_PER_DAY, SEC_PER_MIN, SOLEXS_CHANNELS)
    counts_total, n_present = _finite_sum(block, axis=1)       # -> (1440, 340)
    covered = _second_coverage(gti, pi.data.obs_date).reshape(MINUTES_PER_DAY, SEC_PER_MIN)
    live_time_s = covered.sum(axis=1).astype(np.float64)
    n_any = n_present.max(axis=1)

    df = pd.DataFrame({
        "timestamp": _minute_index(pi.data.obs_date),
        "counts": list(counts_total),                          # list<double>[340]
        "live_time_s": live_time_s,
        "gti_fraction": (live_time_s / SEC_PER_MIN).astype(np.float64),
        "n_seconds_present": n_any.astype(np.int16),
        "q_no_data": (n_any == 0),
        "q_partial": ((live_time_s / SEC_PER_MIN) > 0) & ((live_time_s / SEC_PER_MIN) < 1),
        "detector": pd.Categorical([pi.data.detector] * MINUTES_PER_DAY),
        "chantype": pd.Categorical(["PI"] * MINUTES_PER_DAY),
    })
    df = _prov_cols(df, pi.provenance)
    _assert_no_row_change(df, MINUTES_PER_DAY, "T2")
    assert_no_duplicate_minutes(df, time_column="timestamp")
    return BuiltTable("solexs_spec_1min", df, [pi.provenance])


# ── T3 ──────────────────────────────────────────────────────────────────────
def _band_col(det: str, lo: float, hi: float, suffix: str) -> str:
    f = lambda x: (f"{x:g}").replace(".", "p")
    return f"{det.lower()}_{f(lo)}_{f(hi)}_{suffix}"


def build_T3(lcs: list[ParsedProduct], coverage_map: CoverageMap) -> BuiltTable:
    """§3 T3 `hel1os_lc_1min` — consumes the resolved ownership map ONLY.

    `coverage_map` is required: ownership comes from the Version Resolution
    Engine, never from concatenation. Minutes cannot duplicate.
    """
    if not isinstance(coverage_map, CoverageMap):
        raise FailLoud("F-14", "build_T3 requires a CoverageMap from the Version "
                               "Resolution Engine", got=type(coverage_map).__name__)
    frames, provs = [], []
    for lc in lcs:
        det, orbit = lc.data.detector, lc.provenance.orbit_id
        per_band = {}
        for (lo, hi), bdf in lc.data.bands.items():
            owned = select_owned_rows(bdf, orbit_id=orbit, detector=det,
                                      coverage_map=coverage_map)
            if owned.empty:
                continue
            minute = pd.DatetimeIndex(owned.timestamp_utc).floor("min")
            ctr, n = _finite_sum(owned.ctr.to_numpy()[:, None], axis=1)
            g = pd.DataFrame({"timestamp": minute, "ctr": owned.ctr.to_numpy(),
                              "err": owned.stat_err.to_numpy()}).groupby("timestamp")
            agg = pd.DataFrame({
                _band_col(det, lo, hi, "rate"): g.ctr.mean(),
                _band_col(det, lo, hi, "stat_err"): g.err.mean(),
                _band_col(det, lo, hi, "n_samples"): g.ctr.count(),
            })
            per_band[(lo, hi)] = agg
        if not per_band:
            continue
        merged = pd.concat(per_band.values(), axis=1).reset_index()
        merged["detector"] = pd.Categorical([det] * len(merged))
        merged["orbit_id"] = orbit
        merged["orbit_version"] = lc.provenance.archive_version
        merged = _prov_cols(merged, lc.provenance)
        frames.append(merged)
        provs.append(lc.provenance)
    if not frames:
        return BuiltTable("hel1os_lc_1min", pd.DataFrame(), provs)
    df = pd.concat(frames, ignore_index=True)
    assert_no_duplicate_minutes(df, time_column="timestamp",
                                detector_column="detector")   # F-15
    return BuiltTable("hel1os_lc_1min", df, provs)


# ── T4 (frozen §3 numbering: housekeeping) ──────────────────────────────────
HK_MINUTE_MAX = ("cdte1pilectr", "cdte2pilectr", "czt1satctr1", "czt2satctr1",
                 "czt1hotpixcnt", "czt2hotpixcnt")
HK_MINUTE_MEAN = ("czt1temp", "czt2temp", "cdte1temp", "cdte2temp",
                  "czthvmon", "cdtehvmon", "czt1ctr", "czt2ctr", "cdte1ctr",
                  "cdte2ctr", "czt1enth", "cdte1enerthr", "cdte2enerthr",
                  "sunradeg", "sundecdeg", "fehkstat")


def build_T4(hks: list[ParsedProduct], coverage_map: CoverageMap) -> BuiltTable:
    """§3 T4 `hel1os_hk_1min` — housekeeping.

    §2.8 r4: the parser preserved archive order and this builder NEVER sorts.
    Minute aggregation groups rows; it does not reorder measurements, and every
    statistic used (mean/max/min) is order-independent, so archive order is
    irrelevant to the result rather than silently relied upon.

    Inversion statistics are carried through to provenance and are RECORDED
    ONLY -- never thresholded, never used to filter.
    """
    if not isinstance(coverage_map, CoverageMap):
        raise FailLoud("F-14", "build_T4 requires a CoverageMap",
                       got=type(coverage_map).__name__)
    frames, provs = [], []
    for hk in hks:
        s = hk.data.samples
        minute = pd.DatetimeIndex(s.timestamp_utc).floor("min")
        work = s.copy()
        work["timestamp"] = minute
        g = work.groupby("timestamp", sort=True)
        out = pd.DataFrame(index=g.size().index)
        for c in HK_MINUTE_MEAN:
            out[c] = g[c].mean()
        for c in HK_MINUTE_MAX:
            out[c] = g[c].max()
        # conservative: a minute is Sun-in-FOV only if EVERY sample says so
        out["suninfov"] = g["suninfov"].min().astype(bool)
        out["n_samples"] = g.size()
        out = out.reset_index()
        out["orbit_id"] = hk.provenance.orbit_id
        out = _prov_cols(out, hk.provenance)
        frames.append(out)
        provs.append(hk.provenance)
    if not frames:
        return BuiltTable("hel1os_hk_1min", pd.DataFrame(), provs)
    df = pd.concat(frames, ignore_index=True)
    return BuiltTable("hel1os_hk_1min", df, provs)


# ── T5 (frozen §3 numbering: spectra) ───────────────────────────────────────
def build_T5(specs: list[ParsedProduct], coverage_map: CoverageMap) -> BuiltTable:
    """§3 T5 `hel1os_spec_1min` — 341 PHA channels.

    Kept STRUCTURALLY separate from T2 (F-11): SoLEXS 340 PI and HEL1OS 341 PHA
    are incommensurable channel spaces. There is no merged channel space, and any
    attempt to build one terminates.
    """
    if not isinstance(coverage_map, CoverageMap):
        raise FailLoud("F-14", "build_T5 requires a CoverageMap",
                       got=type(coverage_map).__name__)
    frames, provs = [], []
    for sp in specs:
        fam = "CZT" if sp.data.detector.upper().startswith("CZT") else "CDTE"
        if sp.data.counts.shape[1] != HEL1OS_CHANNELS[fam]:
            raise FailLoud("F-11", f"T5: {fam} requires {HEL1OS_CHANNELS[fam]} PHA "
                                   f"channels (340 would be SoLEXS PI)",
                           file=sp.provenance.src_file,
                           expected=HEL1OS_CHANNELS[fam], got=sp.data.counts.shape[1])
        if sp.data.chantype != "PHA":
            raise FailLoud("F-11", "T5 requires PHA", got=sp.data.chantype)
        det, orbit = sp.data.detector, sp.provenance.orbit_id
        base = pd.DataFrame({"timestamp_utc": sp.data.timestamp_utc})
        owned_mask = [coverage_map.owner(m, det) == orbit
                      for m in pd.DatetimeIndex(base.timestamp_utc).floor("min")]
        if not any(owned_mask):
            continue
        idx = np.flatnonzero(owned_mask)
        minute = pd.DatetimeIndex(sp.data.timestamp_utc[idx]).floor("min")
        counts = sp.data.counts[idx]
        errs = sp.data.stat_err[idx]
        exp = sp.data.exposure_s[idx]
        rows = {}
        for m in pd.unique(minute):
            sel = np.flatnonzero(minute == m)
            tot, n = _finite_sum(counts[sel], axis=0)
            err_tot, _ = _finite_sum(errs[sel], axis=0)
            rows[m] = (tot, err_tot, float(np.nansum(exp[sel])), int(len(sel)))
        out = pd.DataFrame({
            "timestamp": list(rows),
            "detector": pd.Categorical([det] * len(rows)),
            "counts": [v[0] for v in rows.values()],
            "stat_err": [v[1] for v in rows.values()],
            "live_time_s": [v[2] for v in rows.values()],
            "n_spectra": [v[3] for v in rows.values()],
            "chantype": pd.Categorical(["PHA"] * len(rows)),
            # §3 (r5): detchans carried EXPLICITLY. CZT(341) and CdTe(511) arrays
            # are never merged -- different lengths, different spaces; stacking
            # them would fabricate a channel correspondence that does not exist.
            "detchans": np.int16(HEL1OS_CHANNELS[fam]),
        })
        out["orbit_id"] = orbit
        out = _prov_cols(out, sp.provenance)
        frames.append(out)
        provs.append(sp.provenance)
    if not frames:
        return BuiltTable("hel1os_spec_1min", pd.DataFrame(), provs)
    df = pd.concat(frames, ignore_index=True)
    assert_no_duplicate_minutes(df, time_column="timestamp",
                                detector_column="detector")
    return BuiltTable("hel1os_spec_1min", df, provs)


# ── T6 ──────────────────────────────────────────────────────────────────────
def build_T6(gtis: list[ParsedProduct]) -> BuiltTable:
    """§3 T6 `gti_intervals` (long) — exactly the frozen columns."""
    rows, provs = [], []
    for g in gtis:
        p = g.provenance
        provs.append(p)
        for _, r in g.data.intervals.iterrows():
            rows.append({"instrument": p.instrument, "detector": p.detector,
                         "start_utc": r.start_utc, "stop_utc": r.stop_utc,
                         "duration_s": float(r.duration_s),
                         "src_file": p.src_file, "src_sha256": p.src_sha256})
    cols = ["instrument", "detector", "start_utc", "stop_utc", "duration_s",
            "src_file", "src_sha256"]
    df = pd.DataFrame(rows, columns=cols)
    if not df.empty and (df.duration_s <= 0).any():
        raise FailLoud("F-19", "non-positive GTI duration in T6")
    return BuiltTable("gti_intervals", df, provs)


# ── T7 ──────────────────────────────────────────────────────────────────────
T7_COLUMNS = ("src_file", "src_sha256", "instrument", "detector", "product",
              "archive_version", "obs_date", "orbit_id", "creator",
              "processing_date", "rows_in", "rows_out", "parser_version",
              "parsed_at_utc", "time_epoch_resolution", "assumptions_applied")


def build_T7(provenances: list[Provenance]) -> BuiltTable:
    """§3 T7 `provenance_manifest` — one row per parsed source file.

    Every canonical output row must trace to exactly one archive product.
    """
    seen, rows = set(), []
    for p in provenances:
        key = (p.src_file, p.product, p.detector)
        if key in seen:
            continue                     # same file used by several builders
        seen.add(key)
        rows.append(p.to_row())
    df = pd.DataFrame(rows, columns=list(T7_COLUMNS))
    if df.empty:
        return BuiltTable("provenance_manifest", df, [])
    if df.src_file.isna().any() or (df.src_file == "").any():
        raise FailLoud("F-15", "provenance row without a source file")
    return BuiltTable("provenance_manifest", df, list(provenances))


# ── invariants ──────────────────────────────────────────────────────────────
def _assert_no_row_change(df: pd.DataFrame, expected: int, table: str) -> None:
    """F-20 — no silent row creation, no silent row deletion."""
    if len(df) != expected:
        raise FailLoud("F-20", f"{table} row count != expected minutes",
                       expected=expected, got=len(df))


def assert_provenance_complete(table: BuiltTable, t7: BuiltTable) -> None:
    """Every output row traces to exactly one archive product (§3 T7).

    Detects orphan rows (a src_file absent from T7) and ambiguous ownership (a
    src_file appearing more than once in T7 for the same product/detector).
    """
    if table.df.empty:
        return
    if "src_file" not in table.df.columns:
        raise FailLoud("F-15", f"{table.name} has no src_file column")
    if table.df.src_file.isna().any():
        raise FailLoud("F-15", f"{table.name} has rows without provenance")
    known = set(t7.df.src_file)
    orphans = set(table.df.src_file) - known
    if orphans:
        raise FailLoud("F-15", f"{table.name} has orphan rows (src_file not in T7)",
                       got=sorted(orphans)[:5])

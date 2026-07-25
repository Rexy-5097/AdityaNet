"""
Milestone III self-tests: SoLEXS LC parser (contract §2.1).

Synthetic FITS are fail-loud TEST FIXTURES only, never a data source.
`real_archive` tests run against the real 2024-05-14 D1 file.
"""
import gzip
import os

import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from app.v2.models.metadata import FailLoud
from app.v2.parsers.solexs_lc import SolexsLcParser

P = SolexsLcParser()

REAL = ("data/aditya_l1/real_l1_v1/solexs/AL1_SLX_L1_20240514_v1.0/"
        "AL1_SLX_L1_20240514_v1.0/SDD2/AL1_SOLEXS_20240514_SDD2_L1.lc.gz")
real_only = pytest.mark.skipif(not os.path.exists(REAL),
                               reason="real archive not extracted")

D0 = 1715644800.0          # 2024-05-14T00:00:00Z
N = 86400


def _make_lc(tmp, *, n=N, t0=D0, counts=None, det="SDD2", date="20240514",
             obs_date=None, instrume="SoLEXS", mjdrefi=40587, mjdreff=0.0,
             timesys="UTC", timeunit="s", timedel=1, timzero=0.0,
             hduclas3="COUNTS", hduclas1="LIGHTCURVE", extname="RATE",
             filt=None, tstart=None, tstop=None, drop_col=None, drop_hdu=False,
             time=None):
    primary = fits.PrimaryHDU()
    for k, v in (("MISSION", "ADITYA-L1"), ("TELESCOP", "AL1"),
                 ("INSTRUME", instrume), ("ORIGIN", "SoLEXSPOC"),
                 ("CREATOR", "solexs_pipeline-1.4"), ("CONTENT", "LIGHT CURVE"),
                 ("DATE", "2026-05-06"), ("OBS_DATE", obs_date or date),
                 ("OBS_ID", "N00_0000_000147")):
        primary.header[k] = v
    t = np.arange(n, dtype=float) * timedel + t0 if time is None else np.asarray(time, float)
    c = np.full(n, 200.0) if counts is None else np.asarray(counts, float)
    cols = []
    if drop_col != "TIME":
        cols.append(fits.Column(name="TIME", format="D", array=t))
    if drop_col != "COUNTS":
        cols.append(fits.Column(name="COUNTS", format="D", array=c))
    h = fits.BinTableHDU.from_columns(cols, name=extname)
    for k, v in (("HDUCLASS", "OGIP"), ("HDUCLAS1", hduclas1),
                 ("HDUCLAS2", "TOTAL"), ("HDUCLAS3", hduclas3),
                 ("FILTER", filt or det), ("TIMEDEL", timedel), ("TIMZERO", timzero),
                 ("MJDREFI", mjdrefi), ("MJDREFF", mjdreff), ("TIMESYS", timesys),
                 ("TIMEREF", "LOCAL"), ("TIMEUNIT", timeunit), ("NUMBAND", "4"),
                 ("CREATOR", "solexs_pipeline-1.4")):
        h.header[k] = v
    h.header["TSTART"] = float(t[0]) if tstart is None else tstart
    h.header["TSTOP"] = float(t[-1]) if tstop is None else tstop
    hdus = [primary] if drop_hdu else [primary, h]
    p = tmp / f"AL1_SOLEXS_{date}_{det}_L1.lc.gz"
    raw = tmp / "t.fits"
    fits.HDUList(hdus).writeto(raw, overwrite=True)
    with open(raw, "rb") as f, gzip.open(p, "wb") as g:
        g.write(f.read())
    return str(p)


# ── happy path ──────────────────────────────────────────────────────────────
def test_parses_valid_lc(tmp_path):
    r = P.parse(_make_lc(tmp_path))
    assert len(r.data.samples) == N
    assert r.data.detector == "SDD2"
    assert r.data.timedel_s == 1.0
    assert str(r.data.samples.timestamp_utc.iloc[0]) == "2024-05-14 00:00:00+00:00"
    assert r.provenance.time_epoch_resolution == "unix_seconds"


def test_counts_are_counts_per_bin_not_a_rate(tmp_path):
    """§2.1: EXTNAME='RATE' but HDUCLAS3='COUNTS'. Values must pass through raw."""
    c = np.full(N, 7.0); c[:5] = [1, 2, 3, 4, 5]
    r = P.parse(_make_lc(tmp_path, counts=c))
    assert list(r.data.samples.counts[:5]) == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert r.header["hduclas3"] == "COUNTS"


# ── F-05: the exact v1 defect ───────────────────────────────────────────────
def test_F05_wrong_mjdrefi_terminates__the_v1_defect(tmp_path):
    """v1 defaulted MJDREF=58484 (2019-01-01) -> ~49-year error. Now impossible."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, mjdrefi=58484))
    assert e.value.rule == "F-05" and e.value.expected == 40587


def test_F05_nonzero_mjdreff_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, mjdreff=0.5))
    assert e.value.rule == "F-05"


def test_F05_non_utc_timesys_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, timesys="TT"))
    assert e.value.rule == "F-05"


def test_F05_non_second_timeunit_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, timeunit="d"))
    assert e.value.rule == "F-05"


def test_F05_nonzero_timzero_terminates(tmp_path):
    """TIMZERO!=0 would require an offset this parser deliberately never applies."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, timzero=100.0))
    assert e.value.rule == "F-05"


# ── F-07: semantics from HDUCLAS3, never EXTNAME ────────────────────────────
def test_F07_hduclas3_not_counts_terminates(tmp_path):
    """If ISSDC ever ships true RATEs in the RATE HDU, we must NOT read them as counts."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, hduclas3="RATE"))
    assert e.value.rule == "F-07" and e.value.got == "RATE"


def test_F07_hduclas1_not_lightcurve_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, hduclas1="SPECTRUM"))
    assert e.value.rule == "F-07"


def test_F07_filter_disagrees_with_directory(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, det="SDD2", filt="SDD1"))
    assert e.value.rule == "F-07"


def test_F07_timedel_not_one_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, timedel=4))
    assert e.value.rule == "F-07"


def test_F07_wrong_instrument(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, instrume="HEL1OS"))
    assert e.value.rule == "F-07"


def test_F07_obs_date_disagrees_with_filename(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, obs_date="20990101"))
    assert e.value.rule == "F-07"


# ── F-17 / F-16 / F-19 / F-06 ───────────────────────────────────────────────
def test_F17_wrong_row_count_terminates(tmp_path):
    """A truncated daily product must never be silently accepted."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, n=1000))
    assert e.value.rule == "F-17" and e.value.got == 1000


def test_F16_nonfinite_time_terminates(tmp_path):
    """A NaN timestamp would silently defeat the monotonicity test."""
    t = np.arange(N, dtype=float) + D0
    t[10] = np.nan
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, time=t, tstart=D0, tstop=D0 + N - 1))
    assert e.value.rule == "F-16"


def test_F16_time_not_increasing_terminates(tmp_path):
    t = np.arange(N, dtype=float) + D0
    t[1000] = t[999]                       # duplicate second
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, time=t))
    assert e.value.rule == "F-16"


def test_F16_time_gap_terminates(tmp_path):
    """A missing second must fail loudly - never be interpolated or ignored."""
    t = np.arange(N, dtype=float) + D0
    t[1000:] += 10.0                       # an 11 s step where 1 s is required
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, time=t))
    assert e.value.rule == "F-16"


def test_F19_negative_counts_terminate(tmp_path):
    with pytest.raises(FailLoud) as e:
        cneg = np.full(N, 7.0); cneg[2] = -3.0
        P.parse(_make_lc(tmp_path, counts=cneg))
    assert e.value.rule == "F-19"


def test_nan_counts_are_the_missing_data_sentinel_not_an_error(tmp_path):
    """§2.1 (r2): NaN COUNTS is the missing-data sentinel, not an error.

    Binding parser behaviour: pass through unchanged; never imputed, never
    converted to zero, never removed. F-19 covers negative counts only.
    """
    c = np.full(N, 7.0)
    c[[0, 5, 30072]] = np.nan
    r = P.parse(_make_lc(tmp_path, counts=c))
    assert r.header["n_nan_counts"] == 3
    assert r.header["n_finite_counts"] == N - 3
    assert len(r.data.samples) == N                       # nothing dropped
    assert bool(np.isnan(r.data.samples.counts.iloc[0]))  # nothing filled


def test_F06_tstart_mismatch_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, tstart=D0 - 999))
    assert e.value.rule == "F-06"


def test_F06_mjd_epoch_data_terminates(tmp_path):
    """If TIME were MJD-days, the day-bounds check must catch it."""
    t = 60444.0 + np.arange(N) * 1.0       # MJD-days misread as Unix-seconds
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, time=t))
    assert e.value.rule == "F-06"


# ── F-02 / F-04 / F-18 / F-01 ───────────────────────────────────────────────
def test_F02_missing_rate_hdu_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, drop_hdu=True))
    assert e.value.rule == "F-02"


def test_F02_hdu_renamed_terminates(tmp_path):
    """HDU is looked up BY NAME; a renamed extension must fail, not be found by index."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, extname="LIGHTCURVE"))
    assert e.value.rule == "F-02"


def test_F04_missing_counts_column_terminates(tmp_path):
    """v1 looked for a column named RATE; the real column is COUNTS."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_lc(tmp_path, drop_col="COUNTS"))
    assert e.value.rule == "F-04"


def test_F18_bad_filename_rejected(tmp_path):
    p = tmp_path / "whatever.lc.gz"
    p.write_bytes(b"x")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-18"


def test_F01_corrupt_terminates_never_simulates(tmp_path):
    p = tmp_path / "AL1_SOLEXS_20240514_SDD2_L1.lc.gz"
    p.write_bytes(b"garbage")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-01"


# ── real archive: contract §6 D1 ────────────────────────────────────────────
@real_only
def test_real_20240514_has_86400_rows():
    r = P.parse(REAL)
    assert len(r.data.samples) == 86400          # mandated by the brief
    assert r.header["nrows"] == 86400


@real_only
def test_real_20240514_metadata_matches_observed_schema():
    r = P.parse(REAL)
    assert r.data.detector == "SDD2"
    assert r.data.tstart_unix == 1715644800.0
    assert r.data.tstop_unix == 1715731199.0
    assert r.data.timedel_s == 1.0
    assert r.header["numband"] == "4"
    assert r.header["hduclas3"] == "COUNTS"
    assert r.provenance.creator == "solexs_pipeline-1.4"
    assert r.provenance.archive_version == "v1.0"
    assert r.provenance.obs_date == "20240514"


@real_only
def test_real_20240514_timestamps_span_the_day_exactly():
    r = P.parse(REAL)
    s = r.data.samples
    assert str(s.timestamp_utc.iloc[0]) == "2024-05-14 00:00:00+00:00"
    assert str(s.timestamp_utc.iloc[-1]) == "2024-05-14 23:59:59+00:00"
    assert s.timestamp_utc.is_monotonic_increasing
    assert s.timestamp_utc.is_unique
    assert (s.timestamp_utc.diff().dropna() == pd.Timedelta(seconds=1)).all()


@real_only
def test_real_20240514_counts_are_physical():
    """Finite counts must be non-negative. NaN is legitimate data (§2.1 r2)."""
    r = P.parse(REAL)
    c = r.data.samples.counts.to_numpy()
    finite = np.isfinite(c)
    assert (c[finite] >= 0).all()
    assert finite.sum() == 86395            # == EXPOSURE
    assert r.header["n_nan_counts"] == 5


@real_only
def test_real_20240514_nan_positions_equal_gti_excluded_seconds():
    """§2.1 (r2) REQUIRED cross-product integrity rule.

    NaN(COUNTS) set MUST equal the GTI-excluded second set exactly; mismatch
    terminates via F-09. Enforced for real at the day-assembly layer (M-VII);
    asserted here on the reference archive. Scope is A-9: VERIFIED on this
    archive only -- Milestone VIII must prove it across all 436.
    """
    from app.v2.parsers.solexs_gti import SolexsGtiParser

    lc = P.parse(REAL)
    gti = SolexsGtiParser().parse(REAL.replace(".lc.gz", ".gti.gz"))
    day0 = pd.Timestamp("2024-05-14", tz="UTC")

    covered = np.zeros(86400, dtype=bool)
    for _, row in gti.data.intervals.iterrows():
        i0 = int((row.start_utc - day0).total_seconds())
        i1 = int((row.stop_utc - day0).total_seconds())
        covered[i0:i1 + 1] = True                     # inclusive (spec r1)

    nan_idx = set(np.where(~np.isfinite(lc.data.samples.counts.to_numpy()))[0].tolist())
    excluded_idx = set(np.where(~covered)[0].tolist())
    assert nan_idx == excluded_idx == {0, 5, 30072, 30078, 83951}

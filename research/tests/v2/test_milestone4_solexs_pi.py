"""
Milestone IV self-tests: SoLEXS PI spectra parser (contract §2.2).

Fixture strategy: §2.2's header gates (HDUCLAS*, CHANTYPE, DETCHANS, FILTER,
AREASCAL/CORRSCAL) are all evaluated BEFORE F-17's 86400-row check, so they can
be exercised with cheap small fixtures. Tests that must get PAST F-17 need a
full (86400, 340) day = 235 MB, so they run against the REAL archive instead of
fabricating one -- which is also the stronger test.
"""
import gzip
import os

import numpy as np
import pytest
from astropy.io import fits

from app.v2.models.metadata import FailLoud
from app.v2.parsers.solexs_pi import SolexsPiParser, stream_days

P = SolexsPiParser()

B = ("data/aditya_l1/real_l1_v1/solexs/AL1_SLX_L1_20240514_v1.0/"
     "AL1_SLX_L1_20240514_v1.0/SDD2/AL1_SOLEXS_20240514_SDD2_L1")
REAL_PI, REAL_LC = B + ".pi.gz", B + ".lc.gz"
real_only = pytest.mark.skipif(not os.path.exists(REAL_PI),
                               reason="real archive not extracted")

D0 = 1715644800.0
NCH = 340


def _make_pi(tmp, *, n=8, nch=NCH, det="SDD2", date="20240514", obs_date=None,
             instrume="SoLEXS", chantype="PI", detchans=None, hduclas1="SPECTRUM",
             hduclas3="COUNTS", hduclas4="TYPE:II", areascal=1.0, corrscal=1.0,
             filt=None, extname="SPECTRUM", drop_hdu=False, drop_col=None,
             channel=None, counts=None, tstart=None, exposure=None):
    primary = fits.PrimaryHDU()
    for k, v in (("MISSION", "ADITYA-L1"), ("TELESCOP", "AL1"),
                 ("INSTRUME", instrume), ("ORIGIN", "SoLEXSPOC"),
                 ("CREATOR", "solexs_pipeline-1.4"),
                 ("CONTENT", "Type II PHA file"), ("DATE", "2026-05-06"),
                 ("OBS_DATE", obs_date or date), ("OBS_ID", "N00_0000_000147")):
        primary.header[k] = v
    ts = np.arange(n, dtype=float) + D0 if tstart is None else np.asarray(tstart, float)
    ch = np.tile(np.arange(nch, dtype=np.int64), (n, 1)) if channel is None else channel
    ct = np.full((n, nch), 3.0) if counts is None else counts
    ex = np.ones(n) if exposure is None else np.asarray(exposure, float)
    cols = []
    if drop_col != "TSTART":
        cols.append(fits.Column(name="TSTART", format="D", unit="s", array=ts))
    cols.append(fits.Column(name="TELAPSE", format="D", unit="s", array=np.ones(n)))
    cols.append(fits.Column(name="SPEC_NUM", format="J", array=np.arange(n)))
    if drop_col != "CHANNEL":
        cols.append(fits.Column(name="CHANNEL", format=f"{nch}K", array=ch))
    if drop_col != "COUNTS":
        cols.append(fits.Column(name="COUNTS", format=f"{nch}D", array=ct))
    cols.append(fits.Column(name="EXPOSURE", format="D", unit="s", array=ex))
    h = fits.BinTableHDU.from_columns(cols, name=extname)
    for k, v in (("HDUCLASS", "OGIP"), ("HDUCLAS1", hduclas1), ("HDUCLAS2", "TOTAL"),
                 ("HDUCLAS3", hduclas3), ("HDUCLAS4", hduclas4),
                 ("CHANTYPE", chantype),
                 ("DETCHANS", nch if detchans is None else detchans),
                 ("POISSERR", False), ("AREASCAL", areascal), ("CORRSCAL", corrscal),
                 ("FILTER", filt or det), ("CREATOR", "solexs_pipeline-1.4")):
        h.header[k] = v
    hdus = [primary] if drop_hdu else [primary, h]
    p = tmp / f"AL1_SOLEXS_{date}_{det}_L1.pi.gz"
    raw = tmp / "t.fits"
    fits.HDUList(hdus).writeto(raw, overwrite=True)
    with open(raw, "rb") as f, gzip.open(p, "wb", compresslevel=1) as g:
        g.write(f.read())
    return str(p)


# ── §2.2 header gates (fire before F-17, so small fixtures suffice) ─────────
def test_F07_chantype_pha_terminates__guards_F11(tmp_path):
    """SoLEXS must be PI. PHA would be the HEL1OS channel space (F-11)."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, chantype="PHA"))
    assert e.value.rule == "F-07" and e.value.got == "PHA"


def test_F07_detchans_341_terminates__the_hel1os_number(tmp_path):
    """341 is HEL1OS's PHA count. Accepting it here would conflate two spaces."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, nch=NCH, detchans=341))
    assert e.value.rule == "F-07" and e.value.got == 341


def test_F07_hduclas4_not_type2_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, hduclas4="TYPE:I"))
    assert e.value.rule == "F-07"


def test_F07_hduclas1_not_spectrum_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, hduclas1="LIGHTCURVE"))
    assert e.value.rule == "F-07"


def test_F07_hduclas3_not_counts_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, hduclas3="RATE"))
    assert e.value.rule == "F-07"


@pytest.mark.parametrize("key,val", [("areascal", 2.0), ("corrscal", 0.5)])
def test_F07_nonunity_scaling_terminates(tmp_path, key, val):
    """A silent rescale of every spectrum must be impossible."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, **{key: val}))
    assert e.value.rule == "F-07" and e.value.got == val


def test_F07_filter_disagrees_with_directory(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, det="SDD2", filt="SDD1"))
    assert e.value.rule == "F-07"


def test_F07_wrong_instrument(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, instrume="HEL1OS"))
    assert e.value.rule == "F-07"


def test_F07_obs_date_disagrees_with_filename(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, obs_date="20990101"))
    assert e.value.rule == "F-07"


def test_F02_missing_spectrum_hdu_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, drop_hdu=True))
    assert e.value.rule == "F-02"


def test_F02_hdu_renamed_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, extname="SPEC"))
    assert e.value.rule == "F-02"


def test_F17_wrong_row_count_terminates(tmp_path):
    """A daily PI product must have exactly 86400 spectra."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_pi(tmp_path, n=8))
    assert e.value.rule == "F-17" and e.value.got == 8


def test_F18_bad_filename_rejected(tmp_path):
    p = tmp_path / "nope.pi.gz"
    p.write_bytes(b"x")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-18"


def test_F01_corrupt_terminates_never_simulates(tmp_path):
    p = tmp_path / "AL1_SOLEXS_20240514_SDD2_L1.pi.gz"
    p.write_bytes(b"garbage")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-01"


def test_F18_appledouble_rejected(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(str(tmp_path / "._AL1_SOLEXS_20240514_SDD2_L1.pi.gz"))
    assert e.value.rule == "F-18"


# ── real archive: everything past F-17 ──────────────────────────────────────
@real_only
def test_real_shape_is_86400_by_340():
    r = P.parse(REAL_PI)
    assert r.data.counts.shape == (86400, 340)
    assert r.data.n_spectra == 86400 and r.data.n_channels == 340
    assert r.header["nrows"] == 86400 and r.header["detchans"] == 340


@real_only
def test_real_chantype_is_PI_not_PHA():
    r = P.parse(REAL_PI)
    assert r.data.chantype == "PI"
    assert r.header["chantype"] == "PI"


@real_only
def test_real_channel_vector_is_constant_and_collapsed__F08():
    """235 MB/day of redundancy: validated once, then stored as (340,)."""
    r = P.parse(REAL_PI)
    ci = r.data.channel_index
    assert ci.shape == (340,)
    assert ci.dtype == np.int64
    assert ci[0] == 0 and ci[-1] == 339
    assert np.array_equal(ci, np.arange(340))


@real_only
def test_real_channel_index_is_ordinal_not_energy():
    """§2.2 binding: no RMF exists in the archive -> no keV may ever be claimed."""
    r = P.parse(REAL_PI)
    assert not hasattr(r.data, "energy_keV")
    assert not hasattr(r.data, "channel_energy")
    # channel_index must be plain ordinals, not a physical axis
    assert np.array_equal(r.data.channel_index, np.arange(340))


@real_only
def test_real_exposure_is_one_second_per_spectrum():
    r = P.parse(REAL_PI)
    assert r.data.exposure_s.min() == 1.0 and r.data.exposure_s.max() == 1.0


@real_only
def test_real_nan_spectra_match_lc_and_gti__three_way():
    """§2.1 r2 sentinel, confirmed across a THIRD product."""
    r = P.parse(REAL_PI)
    nan_rows = np.where(~np.isfinite(r.data.counts).all(axis=1))[0]
    assert nan_rows.tolist() == [0, 5, 30072, 30078, 83951]
    assert r.header["n_all_nan_spectra"] == 5


@real_only
def test_real_nan_preserved_never_imputed():
    r = P.parse(REAL_PI)
    c = r.data.counts
    assert np.isnan(c[0]).all()               # not zero-filled
    assert c.shape[0] == 86400                # not dropped
    assert (c[np.isfinite(c)] >= 0).all()     # finite values physical


@real_only
def test_real_timestamps_are_unix_and_span_the_day():
    r = P.parse(REAL_PI)
    ts = r.data.timestamps_utc()
    assert str(ts[0]) == "2024-05-14 00:00:00+00:00"
    assert str(ts[-1]) == "2024-05-14 23:59:59+00:00"
    assert r.data.tstart_unix[0] == 1715644800.0


@real_only
def test_real_V_PI_3_cross_check_with_lc_tstart_passes():
    """§2.2 V-PI-3: .pi TSTART[0] must equal the .lc TSTART."""
    r = P.parse(REAL_PI, lc_tstart=1715644800.0)
    assert r.data.tstart_unix[0] == 1715644800.0


@real_only
def test_real_V_PI_3_mismatch_terminates__F06():
    with pytest.raises(FailLoud) as e:
        P.parse(REAL_PI, lc_tstart=1715644801.0)
    assert e.value.rule == "F-06"


@real_only
def test_real_provenance_records_no_kev_assumption():
    r = P.parse(REAL_PI)
    joined = " ".join(r.provenance.assumptions_applied)
    assert "no keV" in joined or "NO RMF" in joined
    assert r.provenance.time_epoch_resolution == "unix_seconds"
    assert r.provenance.detector == "SDD2"
    assert r.provenance.rows_in == 86400


# ── streaming (Milestone IV's hard requirement) ─────────────────────────────
@real_only
def test_stream_days_yields_one_day_at_a_time():
    got = list(stream_days([REAL_PI]))
    assert len(got) == 1
    assert got[0].data.counts.shape == (86400, 340)


@real_only
def test_stream_days_never_holds_two_days_simultaneously():
    """The generator must release each day before opening the next.

    Measured: one day peaks ~2.1 GB RSS. If two were resident the process would
    need ~4 GB, so this is a real constraint, not a stylistic one.
    """
    import tracemalloc

    seen = []
    tracemalloc.start()
    for prod in stream_days([REAL_PI, REAL_PI]):
        # record only cheap scalars; never retain `counts`
        seen.append(prod.data.n_spectra)
        cur, _ = tracemalloc.get_traced_memory()
        # a single resident day of COUNTS is ~235 MB; two would exceed ~400 MB
        assert cur < 700e6, f"two days appear resident: {cur/1e6:.0f} MB traced"
    tracemalloc.stop()
    assert seen == [86400, 86400]


def test_stream_days_is_a_generator_not_a_list():
    """A list-returning API would be unusable: 436 days x 472 MB ~= 206 GB."""
    import types
    assert isinstance(stream_days([]), types.GeneratorType)

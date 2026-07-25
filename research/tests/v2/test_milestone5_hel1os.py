"""
Milestone V self-tests: HEL1OS parser family (contract §2.5–§2.9, amended r4).

Orbit files are NOT merged here — merging is Milestone VI (§4).
"""
import glob
import os

import numpy as np
import pandas as pd
import pytest

from app.v2.models.metadata import FailLoud
from app.v2.parsers.hel1os import (HEL1OSEventsParser, HEL1OSGtiParser,
                                   HEL1OSHkParser, HEL1OSLcParser,
                                   HEL1OSSpectraParser)
from app.v2.parsers.hel1os_base import (EXPECTED_BANDS_KEV, EpochResolution,
                                        absolute_time_from_R1, detector_family,
                                        parse_band_extname, resolve_epoch_R1)
from app.v2.utils.timeseries import chronological_sort, inversion_stats

ORBIT = ("data/aditya_l1/real_l1_v1/hel1os/"
         "HLS_20251208_000008_43178sec_lev1_V111")
real_only = pytest.mark.skipif(not os.path.isdir(ORBIT),
                               reason="real archive not extracted")


def F(pat):
    m = [x for x in glob.glob(f"{ORBIT}/**/{pat}", recursive=True) if "/._" not in x]
    assert m, f"missing {pat}"
    return m[0]


# ── §2.7 R-1 (amended r4): H3 → H1 → H2 ─────────────────────────────────────
HDR_T0, HDR_T1 = 61017.0000988685, 61017.49963590554
SPAN = (HDR_T1 - HDR_T0) * 86400.0


def test_R1_H3_relative_seconds_is_tried_first():
    col = np.arange(0.0, 43121.0, 20.0)
    stop = col + 20.0
    r = resolve_epoch_R1(col, HDR_T0, HDR_T1, file="f", hdu="SPECTRUM",
                         exposure_s=20.0, col_tstop=stop)
    assert r.kind == "relative_seconds"
    assert r.origin_mjd == HDR_T0


def test_R1_H1_mjd_days_still_supported__future_compatibility():
    """r4 retains H1: a reprocessed product could switch to an absolute epoch."""
    col = HDR_T0 + np.arange(3) / 86400.0
    r = resolve_epoch_R1(col, HDR_T0, HDR_T1, file="f", hdu="S")
    assert r.kind == "mjd_days"


def test_R1_H2_unix_seconds_still_supported__future_compatibility():
    unix0 = (HDR_T0 - 40587) * 86400.0
    col = unix0 + np.arange(3, dtype=float)
    r = resolve_epoch_R1(col, HDR_T0, HDR_T1, file="f", hdu="S")
    assert r.kind == "unix_seconds"


def test_R1_terminates_only_when_all_three_fail__F06():
    col = np.array([12345.0, 12365.0])          # non-zero start, wrong span
    with pytest.raises(FailLoud) as e:
        resolve_epoch_R1(col, HDR_T0, HDR_T1, file="f", hdu="S", exposure_s=20.0,
                         col_tstop=col + 20)
    assert e.value.rule == "F-06"
    assert set(e.value.got) >= {"H3_span_residual_s", "H1_residual_if_mjd_days_s",
                                "H2_residual_if_unix_seconds_s"}


def test_R1_H3_requires_exactly_zero_first_value():
    col = np.arange(1.0, 43122.0, 20.0)         # starts at 1.0, not 0.0
    with pytest.raises(FailLoud) as e:
        resolve_epoch_R1(col, HDR_T0, HDR_T1, file="f", hdu="S", exposure_s=20.0,
                         col_tstop=col + 20)
    assert e.value.rule == "F-06"


def test_R1_composition_rule_absolute_equals_origin_plus_offset():
    """§2.7 r4: absolute_time = header TSTART + column offset."""
    col = np.array([0.0, 20.0, 40.0])
    ep = EpochResolution("relative_seconds", 0.0, origin_mjd=HDR_T0)
    ts = absolute_time_from_R1(col, ep)
    assert (ts[1] - ts[0]).total_seconds() == 20.0
    expected0 = pd.to_datetime((HDR_T0 - 40587) * 86400.0, unit="s", utc=True)
    assert abs((ts[0] - expected0).total_seconds()) < 1e-3


# ── §2.6 band allowlist ─────────────────────────────────────────────────────
def test_band_extname_parsed_and_allowlisted():
    det, lo, hi = parse_band_extname("CZT1_LC_BAND_20.00KEV_TO_40.00KEV")
    assert (det, lo, hi) == ("CZT1", 20.0, 40.0)


def test_F10_unknown_band_terminates__never_silently_ingested():
    with pytest.raises(FailLoud) as e:
        parse_band_extname("CZT1_LC_BAND_99.00KEV_TO_123.00KEV")
    assert e.value.rule == "F-10"


def test_F10_malformed_extname_terminates():
    with pytest.raises(FailLoud) as e:
        parse_band_extname("CZT1_SOMETHING_ELSE")
    assert e.value.rule == "F-10"


def test_cdte_and_czt_have_distinct_band_sets():
    assert EXPECTED_BANDS_KEV["CZT"] != EXPECTED_BANDS_KEV["CDTE"]
    assert (5.0, 20.0) in EXPECTED_BANDS_KEV["CDTE"]
    assert (5.0, 20.0) not in EXPECTED_BANDS_KEV["CZT"]


def test_detector_family_rejects_unknown():
    with pytest.raises(FailLoud) as e:
        detector_family("SDD2")            # a SoLEXS detector -- wrong instrument
    assert e.value.rule == "F-07"


# ── §2.8 r4: chronological_sort lives OUTSIDE the parser ────────────────────
def test_inversion_stats_reports_never_thresholds():
    t = np.array([0.0, 1.0, 0.5, 2.0])
    n, mx = inversion_stats(t, unit="s")
    assert n == 1 and mx == pytest.approx(0.5)


def test_inversion_stats_zero_for_sorted():
    assert inversion_stats(np.arange(10.0), unit="s") == (0, 0.0)


def test_chronological_sort_preserves_every_row_and_value():
    df = pd.DataFrame({"t": [3.0, 1.0, 2.0], "v": ["c", "a", "b"]})
    out, rec = chronological_sort(df, "t", unit="s")
    assert len(out) == 3                                   # every row
    assert sorted(out.v) == ["a", "b", "c"]                # every value
    assert list(out.t) == [1.0, 2.0, 3.0]
    # inversion_stats counts BACKWARD STEPS, not out-of-place elements:
    # [3,1,2] -> diff [-2,+1] -> exactly one backward step of 2.0 s.
    assert rec.n_out_of_order == 1
    assert rec.max_backward_step_s == pytest.approx(2.0)
    assert rec.was_already_sorted is False


def test_chronological_sort_is_deterministic_and_stable():
    df = pd.DataFrame({"t": [1.0, 1.0, 0.0], "v": ["first", "second", "z"]})
    out, _ = chronological_sort(df, "t", unit="s")
    # ties keep archive order -> never reorders equal keys nondeterministically
    assert list(out.v) == ["z", "first", "second"]
    out2, _ = chronological_sort(df, "t", unit="s")
    assert out.equals(out2)


def test_chronological_sort_records_provenance():
    df = pd.DataFrame({"t": [2.0, 1.0]})
    _, rec = chronological_sort(df, "t", unit="s")
    row = rec.to_row()
    for k in ("time_column", "n_rows", "n_out_of_order", "max_backward_step_s",
              "was_already_sorted", "algorithm", "utility_version", "applied_at_utc"):
        assert k in row
    assert row["algorithm"] == "stable_mergesort"


def test_chronological_sort_missing_column_fails_loud():
    with pytest.raises(FailLoud) as e:
        chronological_sort(pd.DataFrame({"a": [1]}), "t")
    assert e.value.rule == "F-04"


# ── real archive ────────────────────────────────────────────────────────────
@real_only
def test_real_lc_five_bands_per_detector():
    r = HEL1OSLcParser().parse(F("lightcurve_czt1.fits"))
    assert r.data.detector == "CZT1"
    assert set(r.data.bands) == set(EXPECTED_BANDS_KEV["CZT"])
    assert len(r.data.bands[(20.0, 40.0)]) == 43171


@real_only
def test_real_lc_cdte_bands_differ_from_czt():
    r = HEL1OSLcParser().parse(F("lightcurve_cdte1.fits"))
    assert set(r.data.bands) == set(EXPECTED_BANDS_KEV["CDTE"])


@real_only
def test_real_lc_ctr_is_a_declared_rate_not_counts():
    """§2.6: opposite convention from SoLEXS .lc (undeclared counts)."""
    r = HEL1OSLcParser().parse(F("lightcurve_czt1.fits"))
    df = r.data.bands[(20.0, 40.0)]
    assert "ctr" in df.columns and "stat_err" in df.columns
    assert (df.ctr.dropna() >= 0).all()


@real_only
def test_real_gti_parses_lowercase_columns():
    """§2.9 lowercase tstart/tstop vs SoLEXS uppercase — A-2 earns its keep."""
    r = HEL1OSGtiParser().parse(F("gticzt1.fits"))
    assert r.detector_active and len(r.data.intervals) == 1
    assert r.data.intervals.duration_s.iloc[0] == pytest.approx(43178.29, abs=0.1)


@real_only
def test_real_spectra_341_pha_channels():
    r = HEL1OSSpectraParser().parse(F("hel1os_czt_spectra_czt1.fits"))
    assert r.data.counts.shape[1] == 341            # NOT 340 (SoLEXS PI) -- F-11
    assert r.data.chantype == "PHA"
    assert r.header["detchans"] == 341


@real_only
def test_real_spectra_R1_resolves_to_relative_seconds():
    r = HEL1OSSpectraParser().parse(F("hel1os_czt_spectra_czt1.fits"))
    assert r.header["epoch_kind"] == "relative_seconds"
    assert r.data.epoch_kind == "relative_seconds"
    assert "R-1 resolved empirically" in " ".join(r.provenance.assumptions_applied)


@real_only
def test_real_spectra_absolute_time_is_composed_correctly():
    r = HEL1OSSpectraParser().parse(F("hel1os_czt_spectra_czt1.fits"))
    ts = r.data.timestamp_utc
    assert r.data.tstart[0] == 0.0                       # raw column is an offset
    assert str(ts[0]).startswith("2025-12-08")           # composed absolute time
    assert (ts[1] - ts[0]).total_seconds() == 20.0
    assert ts.is_monotonic_increasing


@real_only
def test_real_spectra_channel_constant_then_collapsed__F08():
    r = HEL1OSSpectraParser().parse(F("hel1os_czt_spectra_czt1.fits"))
    assert r.data.channel_index.shape == (341,)


@real_only
def test_real_hk_preserves_archive_order__r4_lossless():
    """§2.8 r4 BINDING: the parser must NOT sort. It is a lossless reader."""
    r = HEL1OSHkParser().parse(F("hk.fits"))
    t = r.data.samples.timestamp_utc
    assert len(t) == 9514
    # archive order is NOT chronological -- proving no sorting occurred
    assert not t.is_monotonic_increasing
    assert r.header["n_out_of_order"] == 424


@real_only
def test_real_hk_records_inversion_statistics_without_thresholding():
    r = HEL1OSHkParser().parse(F("hk.fits"))
    assert r.header["n_out_of_order"] == 424
    assert r.header["max_backward_step_s"] == pytest.approx(0.8924, abs=1e-3)
    joined = " ".join(r.provenance.assumptions_applied)
    assert "never thresholded" in joined and "NOT sorted" in joined


@real_only
def test_real_hk_sortable_via_the_explicit_utility():
    """Consumers opt in visibly; the parser never does it for them."""
    r = HEL1OSHkParser().parse(F("hk.fits"))
    out, rec = chronological_sort(r.data.samples, "timestamp_utc")
    assert out.timestamp_utc.is_monotonic_increasing
    assert len(out) == len(r.data.samples)              # lossless
    assert rec.n_out_of_order == 424


@real_only
def test_real_hk_exposes_phase1a_instrument_state():
    """§2.8: hk.fits is Phase 1a's ONLY source of pile-up/saturation/HV state."""
    r = HEL1OSHkParser().parse(F("hk.fits"))
    d = r.data.samples
    for c in ("cdte1pilectr", "cdte2pilectr", "czt1satctr1", "czt2satctr1",
              "czthvmon", "cdtehvmon", "czt1temp", "suninfov"):
        assert c in d.columns, f"Phase 1a needs {c}"
    assert d.suninfov.dtype == bool                     # first-class quality flag


@real_only
def test_real_events_all_four_detector_hdus__F03():
    r = HEL1OSEventsParser().parse(F("evt.fits"))
    assert set(r.data.n_events) == {"CDTE1", "CDTE2", "CZT1", "CZT2"}
    assert r.header["n_events_total"] == 5796441


@real_only
def test_real_events_are_not_ingested_by_default():
    """§2.5: 85.7 GB archive-wide -- eager column loading would be a trap."""
    r = HEL1OSEventsParser().parse(F("evt.fits"))
    assert "NOT ingested" in " ".join(r.provenance.assumptions_applied)
    assert r.provenance.rows_out == 0

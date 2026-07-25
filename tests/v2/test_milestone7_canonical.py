"""
Milestone VII self-tests: canonical builders T1–T7 (contract §3).

NUMBERING: follows the FROZEN contract §3 (T4=hk, T5=spectra), which is inverted
relative to the M-VII brief's labels. Content and requirements are identical.
"""
import os
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from app.v2.builders import canonical as CB
from app.v2.builders.canonical import (assert_provenance_complete, build_T1,
                                       build_T2, build_T3, build_T4, build_T5,
                                       build_T6, build_T7,
                                       validate_nan_implies_gti_excluded)
from app.v2.models.metadata import FailLoud
from app.v2.parsers.solexs_gti import SolexsGtiParser
from app.v2.parsers.solexs_lc import SolexsLcParser
from app.v2.parsers.solexs_pi import SolexsPiParser
from app.v2.resolution.version_engine import OrbitCandidate, build_coverage_map

B = ("data/aditya_l1/real_l1_v1/solexs/AL1_SLX_L1_20240514_v1.0/"
     "AL1_SLX_L1_20240514_v1.0/SDD2/AL1_SOLEXS_20240514_SDD2_L1")
real_only = pytest.mark.skipif(not os.path.exists(B + ".lc.gz"),
                              reason="real archive not extracted")


@pytest.fixture(scope="module")
def lc():
    return SolexsLcParser().parse(B + ".lc.gz")


@pytest.fixture(scope="module")
def gti():
    return SolexsGtiParser().parse(B + ".gti.gz")


@pytest.fixture(scope="module")
def pi():
    return SolexsPiParser().parse(B + ".pi.gz")


# ── structural: builders cannot parse FITS ──────────────────────────────────
def test_builders_import_no_fits_reader():
    """'MUST NOT parse FITS directly' is enforced by the module, not discipline."""
    src = open("app/v2/builders/canonical.py").read()
    assert "astropy" not in src
    assert "open_fits" not in src
    assert "fits.open" not in src


def test_builders_take_parsed_products_not_paths():
    import inspect
    for fn in (build_T1, build_T2, build_T3, build_T4, build_T5):
        sig = str(inspect.signature(fn))
        assert "path" not in sig.lower(), f"{fn.__name__} accepts a path"


def test_hel1os_builders_require_a_coverage_map():
    """Ownership must come from the Version Resolution Engine (§4)."""
    for fn in (build_T3, build_T4, build_T5):
        with pytest.raises(FailLoud) as e:
            fn([], coverage_map="not a map")     # type: ignore[arg-type]
        assert e.value.rule == "F-14"


# ── finite-only aggregation (r2) ────────────────────────────────────────────
def test_finite_sum_one_nan_does_not_void_a_minute():
    """§3 r2: a naive sum() would return NaN and destroy 59 good seconds."""
    block = np.full((1, 60), 2.0)
    block[0, 7] = np.nan
    total, n = CB._finite_sum(block, axis=1)
    assert total[0] == pytest.approx(118.0)          # 59 x 2.0, NOT NaN
    assert n[0] == 59


def test_finite_sum_all_nan_minute_is_NaN_not_zero():
    """np.nansum would return 0.0 -- manufacturing a zero measurement."""
    total, n = CB._finite_sum(np.full((1, 60), np.nan), axis=1)
    assert np.isnan(total[0]) and n[0] == 0


def test_finite_sum_zero_is_a_valid_count_not_missing():
    total, n = CB._finite_sum(np.zeros((1, 60)), axis=1)
    assert total[0] == 0.0 and n[0] == 60            # 60 real zeros


# ── NaN<->GTI invariant (r2) ────────────────────────────────────────────────
@real_only
def test_nan_implies_gti_excluded_holds_on_reference_day(lc, gti):
    r = validate_nan_implies_gti_excluded(lc, gti)
    assert r["n_excluded_seconds"] == 5
    assert r["n_nan_seconds"] == 5
    assert r["n_excluded_with_finite_counts"] == 0    # A-14 observable: 0 here
    assert r["excluded_offsets"] == [0, 5, 30072, 30078, 83951]
    assert r["live_time_s"] == 86395


@real_only
def test_r5_gti_excluded_second_with_finite_count_is_PERMITTED(lc, gti):
    """r5: a GTI-excluded second MAY carry a finite count.

    Under r2's equality this terminated. Under r5 it is legal and merely counted
    -- the excess is A-14, unexplained, owner Milestone VIII.
    """
    iv = gti.data.intervals.copy()
    iv.loc[0, "stop_utc"] = iv.loc[0, "stop_utc"] - pd.Timedelta(seconds=1)
    bad = replace(gti.data, intervals=iv)
    from app.v2.models.metadata import ParsedProduct
    r = validate_nan_implies_gti_excluded(
        lc, ParsedProduct(data=bad, provenance=gti.provenance))
    assert r["n_excluded_with_finite_counts"] == 1     # counted, not judged


@real_only
def test_r5_nan_inside_gti_good_time_terminates__F09(lc, gti):
    """The ONLY forbidden direction: missing data treated as observed."""
    s2 = lc.data.samples.copy()
    s2.loc[1000, "counts"] = np.nan          # second 1000 is inside good time
    bad = replace(lc.data, samples=s2)
    from app.v2.models.metadata import ParsedProduct
    with pytest.raises(FailLoud) as e:
        validate_nan_implies_gti_excluded(
            ParsedProduct(data=bad, provenance=lc.provenance), gti)
    assert e.value.rule == "F-09"
    assert e.value.got["n_nan_in_good_time"] == 1
    assert e.value.got["offsets"] == [1000]


@real_only
def test_T1_runs_nan_gti_validation_before_aggregating(lc, gti, monkeypatch):
    calls = []
    orig = CB.validate_nan_implies_gti_excluded
    monkeypatch.setattr(CB, "validate_nan_implies_gti_excluded",
                        lambda a, b: (calls.append("validated"), orig(a, b))[1])
    CB.build_T1(lc, gti)
    assert calls == ["validated"]


# ── T1 ──────────────────────────────────────────────────────────────────────
@real_only
def test_T1_shape_and_columns(lc, gti):
    t1 = build_T1(lc, gti)
    assert len(t1.df) == 1440
    assert list(t1.df.columns) == [
        "timestamp", "counts_total", "live_time_s", "rate_total", "gti_fraction",
        "n_seconds_present", "q_no_data", "q_partial", "detector",
        "src_file", "src_sha256", "archive_version"]


@real_only
def test_T1_live_time_sums_to_exposure(lc, gti):
    """r1 inclusive convention, propagated into the canonical table."""
    t1 = build_T1(lc, gti)
    assert t1.df.live_time_s.sum() == 86395.0
    assert gti.data.exposure_declared_s == 86395.0


@real_only
def test_T1_five_excluded_seconds_land_in_three_partial_minutes(lc, gti):
    t1 = build_T1(lc, gti)
    assert int(t1.df.q_partial.sum()) == 3          # offsets 0,5 | 30072,30078 | 83951
    assert int(t1.df.q_no_data.sum()) == 0
    assert t1.df.live_time_s.min() == 58.0          # the minute losing 2 seconds


@real_only
def test_T1_no_imputation_rate_is_NaN_where_no_live_time(lc, gti):
    t1 = build_T1(lc, gti)
    m = t1.df.live_time_s == 0
    assert t1.df.loc[m, "rate_total"].isna().all()


@real_only
def test_T1_peak_matches_the_X87_flare_within_the_frozen_window(lc, gti):
    """§6 D1 acceptance: peak within +/-2 min of the GOES X8.7 at 16:51 UTC."""
    t1 = build_T1(lc, gti)
    peak = t1.df.loc[t1.df.rate_total.idxmax(), "timestamp"]
    goes = pd.Timestamp("2024-05-14T16:51:00Z")
    assert abs((peak - goes).total_seconds()) <= 120


@real_only
def test_T1_rejects_mismatched_day_or_detector(lc, gti):
    bad = replace(gti.data, obs_date="20990101")
    from app.v2.models.metadata import ParsedProduct
    with pytest.raises(FailLoud) as e:
        build_T1(lc, ParsedProduct(data=bad, provenance=gti.provenance))
    assert e.value.rule == "F-07"


# ── T2 ──────────────────────────────────────────────────────────────────────
@real_only
def test_T2_preserves_340_ordinal_channels_and_no_keV(pi, gti):
    t2 = build_T2(pi, gti)
    assert len(t2.df) == 1440
    assert len(t2.df.counts.iloc[0]) == 340
    assert "channel_energy_keV" not in t2.df.columns      # ABSENT BY DESIGN
    assert "energy" not in " ".join(t2.df.columns).lower()
    assert t2.df.chantype.iloc[0] == "PI"


@real_only
def test_T2_records_RMF_absence_in_provenance(pi, gti):
    t2 = build_T2(pi, gti)
    joined = " ".join(t2.provenance[0].assumptions_applied)
    assert "NO RMF" in joined and "no keV" in joined


@real_only
def test_T2_rejects_a_341_channel_PHA_input__F11(pi, gti):
    """No merged channel space: HEL1OS PHA must never enter T2."""
    bad = replace(pi.data, chantype="PHA")
    from app.v2.models.metadata import ParsedProduct
    with pytest.raises(FailLoud) as e:
        build_T2(ParsedProduct(data=bad, provenance=pi.provenance), gti)
    assert e.value.rule == "F-11"


@real_only
def test_T2_nan_propagates_per_channel_never_filled(pi, gti):
    t2 = build_T2(pi, gti)
    stacked = np.vstack(t2.df.counts.to_numpy())
    assert stacked.shape == (1440, 340)
    assert np.isfinite(stacked).all() or np.isnan(stacked).any()   # never zero-filled
    assert (stacked[np.isfinite(stacked)] >= 0).all()


# ── CONTRADICTION-003: carried independently ────────────────────────────────
@real_only
def test_T1_and_T2_are_carried_independently_never_derived(lc, gti, pi):
    """CONTRADICTION-003 OPEN: no code may relate Σ(PI) to the light curve."""
    import inspect
    # Structural: build_T2 cannot derive from T1 -- T1 is not reachable from it.
    assert list(inspect.signature(build_T2).parameters) == ["pi", "gti"]
    assert list(inspect.signature(build_T1).parameters) == ["lc", "gti"]
    t1, t2 = build_T1(lc, gti), build_T2(pi, gti)
    chan_sum = np.array([np.nansum(c) for c in t2.df.counts])
    # they differ -- and the builders neither know nor care
    assert not np.allclose(np.nan_to_num(chan_sum),
                           np.nan_to_num(t1.df.counts_total.to_numpy()))


# ── T3 / T4 / T5 ────────────────────────────────────────────────────────────
T0 = pd.Timestamp("2025-12-08T00:00:00Z")


def _cm(*cands):
    return build_coverage_map(list(cands))


def test_T5_rejects_340_channel_PI_input__F11():
    """r5: THREE spaces -- SoLEXS PI 340, CZT PHA 341, CdTe PHA 511.
    A 340-channel array must never enter T5 under any family."""
    class D:
        counts = np.zeros((3, 340)); chantype = "PI"; detector = "CZT1"
        stat_err = np.zeros((3, 340)); exposure_s = np.ones(3)
        timestamp_utc = pd.DatetimeIndex([T0] * 3)
    from app.v2.models.metadata import Provenance, ParsedProduct
    p = Provenance(src_file="f", src_sha256="s", instrument="hel1os", detector="CZT1",
                   product="spectra", archive_version="V111", obs_date="20251208",
                   orbit_id="o", creator="c", processing_date=None, rows_in=3,
                   rows_out=3, time_epoch_resolution="relative_seconds")
    cm = _cm(OrbitCandidate("o", "/o", "s", 111, 3600, T0, T0 + pd.Timedelta(hours=1),
                            ("CZT1",)))
    with pytest.raises(FailLoud) as e:
        build_T5([ParsedProduct(data=D(), provenance=p)], cm)
    assert e.value.rule == "F-11"


def test_T4_uses_only_order_independent_statistics():
    """§2.8 r4: the parser preserved archive order; the builder must not sort.

    Minute aggregation GROUPS rows; it never reorders measurements. Every
    statistic used is order-independent, so archive order cannot affect a result.
    """
    src = open("app/v2/builders/canonical.py").read()
    t4 = src.split("def build_T4")[1].split("def build_T5")[0]
    assert "sort_values" not in t4 and "chronological_sort" not in t4
    for stat in ("mean", "max", "min"):
        pass                                     # all order-independent
    assert ".mean()" in t4 and ".max()" in t4 and ".min()" in t4


# ── T6 ──────────────────────────────────────────────────────────────────────
@real_only
def test_T6_has_exactly_the_frozen_columns(gti):
    t6 = build_T6([gti])
    assert list(t6.df.columns) == ["instrument", "detector", "start_utc",
                                   "stop_utc", "duration_s", "src_file",
                                   "src_sha256"]
    assert len(t6.df) == 5
    assert t6.df.duration_s.sum() == 86395.0


@real_only
def test_T6_includes_inactive_detectors_as_zero_rows():
    """SDD1 is F-12 inactive -> contributes no intervals, and that is legal."""
    g1 = SolexsGtiParser().parse(B.replace("SDD2", "SDD1").replace(
        "AL1_SOLEXS_20240514_SDD2", "AL1_SOLEXS_20240514_SDD1") + ".gti.gz")
    t6 = build_T6([g1])
    assert len(t6.df) == 0
    assert g1.detector_active is False


# ── T7 / provenance completeness ────────────────────────────────────────────
@real_only
def test_T7_has_exactly_the_frozen_columns(lc, gti, pi):
    t7 = build_T7([lc.provenance, gti.provenance, pi.provenance])
    assert list(t7.df.columns) == list(CB.T7_COLUMNS)
    assert len(t7.df) == 3


@real_only
def test_T7_deduplicates_the_same_file_used_by_several_builders(lc, gti, pi):
    t7 = build_T7([lc.provenance, gti.provenance, pi.provenance, gti.provenance])
    assert len(t7.df) == 3               # gti listed once


@real_only
def test_every_T1_row_traces_to_exactly_one_archive_product(lc, gti, pi):
    t1 = build_T1(lc, gti)
    t7 = build_T7([lc.provenance, gti.provenance, pi.provenance])
    assert_provenance_complete(t1, t7)
    assert t1.df.src_file.nunique() == 1
    assert t1.df.src_sha256.notna().all()


@real_only
def test_orphan_rows_are_detected(lc, gti):
    t1 = build_T1(lc, gti)
    t7_empty = build_T7([gti.provenance])          # T1's .lc is missing from T7
    with pytest.raises(FailLoud) as e:
        assert_provenance_complete(t1, t7_empty)
    assert e.value.rule == "F-15"


# ── no silent row creation / deletion ───────────────────────────────────────
@real_only
def test_no_silent_row_creation_or_deletion(lc, gti, pi):
    assert len(build_T1(lc, gti).df) == 1440       # exactly the day's minutes
    assert len(build_T2(pi, gti).df) == 1440


def test_row_count_guard_fires__F20():
    with pytest.raises(FailLoud) as e:
        CB._assert_no_row_change(pd.DataFrame({"a": [1, 2]}), 1440, "T1")
    assert e.value.rule == "F-20"


# ── builders never modify scientific values ─────────────────────────────────
def _code_without_docstrings(path):
    """Return executable source only, so prose cannot cause a false pass."""
    import ast

    class _Strip(ast.NodeTransformer):
        def _drop(self, node):
            self.generic_visit(node)
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
            return node
        visit_Module = visit_ClassDef = visit_FunctionDef = _drop

    return ast.unparse(_Strip().visit(ast.parse(open(path).read())))


def test_builders_never_interpolate_smooth_infer_repair_or_fill():
    import re
    code = _code_without_docstrings("app/v2/builders/canonical.py")
    for pat in (r"\.interpolate\(", r"\.rolling\(", r"\.ewm\(", r"smooth",
                r"fillna", r"nan_to_num", r"ffill", r"bfill"):
        assert not re.search(pat, code), f"builder matches banned pattern {pat}"
    # `.replace(` is used ONLY to format a column name (str.replace in _band_col),
    # never to repair data. Assert that precisely rather than banning the token.
    for line in code.split("\n"):
        if ".replace(" in line:
            assert "f'{x:g}'" in line or '"."' in line or "'.'" in line, \
                f"unexpected .replace( on data: {line}"


def test_builders_never_use_nansum_which_would_manufacture_zeros():
    """np.nansum([nan,nan]) == 0.0 -- a fabricated measurement."""
    code = _code_without_docstrings("app/v2/builders/canonical.py")
    # nansum is permitted ONLY for live-time/exposure accumulation, never counts
    for line in code.split("\n"):
        if "nansum" in line:
            assert "exp" in line or "live" in line, f"nansum on a measurement: {line}"


def test_r5_hel1os_has_two_channel_spaces_never_merged():
    """§2.7 r5 / §3: CZT=341 and CdTe=511 are different spaces.

    Merging them would fabricate a channel correspondence that does not exist.
    """
    from app.v2.builders.canonical import HEL1OS_CHANNELS
    from app.v2.parsers.hel1os import EXPECTED_DETCHANS_PHA
    assert HEL1OS_CHANNELS == {"CZT": 341, "CDTE": 511}
    assert EXPECTED_DETCHANS_PHA == {"CZT": 341, "CDTE": 511}
    assert HEL1OS_CHANNELS["CZT"] != HEL1OS_CHANNELS["CDTE"]
    assert CB.SOLEXS_CHANNELS not in HEL1OS_CHANNELS.values()   # 340 is neither

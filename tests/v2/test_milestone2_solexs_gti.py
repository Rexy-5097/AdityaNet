"""
Milestone II self-tests: SoLEXS GTI parser (contract §2.3).

Synthetic FITS here are TEST FIXTURES for fail-loud paths — never a data source.
Real-archive assertions are marked `real_archive` and run against the actual
2024-05-14 files.
"""
import gzip
import os

import numpy as np
import pytest
from astropy.io import fits

from app.v2.models.metadata import FailLoud
from app.v2.parsers.solexs_gti import SolexsGtiParser

P = SolexsGtiParser()

REAL = ("data/aditya_l1/real_l1_v1/solexs/AL1_SLX_L1_20240514_v1.0/"
        "AL1_SLX_L1_20240514_v1.0/{d}/AL1_SOLEXS_20240514_{d}_L1.gti.gz")
have_real = os.path.exists(REAL.format(d="SDD2"))
real_only = pytest.mark.skipif(not have_real, reason="real archive not extracted")


def _make_gti(tmp, start, stop, *, exposure=None, det="SDD2", date="20240514",
              obs_date=None, instrume="SoLEXS", drop_col=None, drop_hdu=False):
    primary = fits.PrimaryHDU()
    for k, v in (("MISSION", "ADITYA-L1"), ("TELESCOP", "AL1"),
                 ("INSTRUME", instrume), ("ORIGIN", "SoLEXSPOC"),
                 ("CREATOR", "solexs_pipeline-1.4"),
                 ("CONTENT", "GOOD TIME INTERVAL"), ("DATE", "2026-05-06"),
                 ("OBS_DATE", obs_date or date), ("OBS_ID", "N00_0000_000147")):
        primary.header[k] = v
    cols = []
    if drop_col != "START":
        cols.append(fits.Column(name="START", format="D", array=np.array(start)))
    if drop_col != "STOP":
        cols.append(fits.Column(name="STOP", format="D", array=np.array(stop)))
    t = fits.BinTableHDU.from_columns(cols, name="GTI")
    exp = exposure if exposure is not None else float(np.sum(np.array(stop) - np.array(start)))
    t.header["EXPOSURE"] = str(exp)          # archive stores this as a STRING
    hdus = [primary] if drop_hdu else [primary, t]
    p = tmp / f"AL1_SOLEXS_{date}_{det}_L1.gti.gz"
    raw = tmp / "t.fits"
    fits.HDUList(hdus).writeto(raw, overwrite=True)
    with open(raw, "rb") as f, gzip.open(p, "wb") as g:
        g.write(f.read())
    return str(p)


D0 = 1715644800.0          # 2024-05-14T00:00:00Z


def test_parses_valid_gti(tmp_path):
    r = P.parse(_make_gti(tmp_path, [D0 + 1, D0 + 10], [D0 + 5, D0 + 20]))
    assert r.detector_active
    assert len(r.data.intervals) == 2
    assert r.data.exposure_summed_s == pytest.approx(14.0)
    assert str(r.data.intervals.start_utc.iloc[0]) == "2024-05-14 00:00:01+00:00"
    assert r.provenance.time_epoch_resolution == "unix_seconds"


def test_F12_empty_gti_is_legal_not_fatal(tmp_path):
    """The ONE deliberate non-fatal rule. OBSERVED on real SDD1."""
    r = P.parse(_make_gti(tmp_path, [], [], exposure=0.0, det="SDD1"))
    assert r.detector_active is False
    assert len(r.data.intervals) == 0
    assert any("F-12" in w for w in r.warnings)
    # empty table must still be correctly typed - never None, never invented
    assert list(r.data.intervals.columns) == ["start_utc", "stop_utc", "duration_s"]


def test_F09_exposure_mismatch_terminates(tmp_path):
    p = _make_gti(tmp_path, [D0 + 1], [D0 + 11], exposure=9999.0)
    with pytest.raises(FailLoud) as e:
        P.parse(p)
    assert e.value.rule == "F-09"


def test_F09_tolerance_is_one_second(tmp_path):
    P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 11], exposure=10.9))   # within 1s
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 11], exposure=11.5))
    assert e.value.rule == "F-09"


def test_F19_stop_before_start_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 10], [D0 + 5], exposure=-5.0))
    assert e.value.rule == "F-19"


def test_F16_overlapping_intervals_terminate(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1, D0 + 3], [D0 + 10, D0 + 20],
                          exposure=26.0))
    assert e.value.rule == "F-16"


def test_F16_unsorted_intervals_terminate(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 30, D0 + 1], [D0 + 40, D0 + 5],
                          exposure=14.0))
    assert e.value.rule == "F-16"


def test_F02_missing_gti_hdu_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 5], drop_hdu=True))
    assert e.value.rule == "F-02"


def test_F04_missing_column_terminates(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 5], drop_col="STOP"))
    assert e.value.rule == "F-04"


def test_F06_wrong_epoch_terminates(tmp_path):
    """If TIME were MJD (v1's defect class), intervals fall outside OBS_DATE."""
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [60444.0], [60444.1], exposure=0.1))
    assert e.value.rule == "F-06"


def test_F07_obs_date_disagrees_with_filename(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 5], obs_date="20990101"))
    assert e.value.rule == "F-07"


def test_F07_wrong_instrument(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(_make_gti(tmp_path, [D0 + 1], [D0 + 5], instrume="HEL1OS"))
    assert e.value.rule == "F-07"


def test_F18_bad_filename_rejected(tmp_path):
    p = tmp_path / "random_file.gti.gz"
    p.write_bytes(b"x")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-18"


def test_F01_corrupt_file_terminates_never_simulates(tmp_path):
    p = tmp_path / "AL1_SOLEXS_20240514_SDD2_L1.gti.gz"
    p.write_bytes(b"not a gzip nor fits")
    with pytest.raises(FailLoud) as e:
        P.parse(str(p))
    assert e.value.rule == "F-01"


def test_F18_appledouble_rejected(tmp_path):
    with pytest.raises(FailLoud) as e:
        P.parse(str(tmp_path / "._AL1_SOLEXS_20240514_SDD2_L1.gti.gz"))
    assert e.value.rule == "F-18"


# ── real archive (contract §6 D1) ───────────────────────────────────────────
@real_only
@pytest.mark.xfail(strict=True, reason=(
    "BLOCKED by CONTRADICTION-001: frozen F-09 uses sum(STOP-START) (=86390.0) "
    "but the archive's EXPOSURE (=86395.0) follows the INCLUSIVE convention "
    "sum(STOP-START+1). The contract is impossible to satisfy on the mandated D1 "
    "file. strict=True: if this passes, the contract was amended and this marker "
    "MUST be removed. Nothing weakened pending owner approval."))
def test_real_sdd2_20240514_matches_observed_schema():
    r = P.parse(REAL.format(d="SDD2"))
    assert r.detector_active
    assert len(r.data.intervals) == 5                    # OBSERVED in spec §2.3
    assert r.data.exposure_declared_s == pytest.approx(86395.0)
    assert r.data.exposure_summed_s == pytest.approx(86395.0, abs=1.0)
    assert str(r.data.intervals.start_utc.iloc[0]) == "2024-05-14 00:00:01+00:00"
    assert r.data.detector == "SDD2"
    assert r.provenance.creator == "solexs_pipeline-1.4"


@real_only
def test_real_sdd1_20240514_is_empty_via_F12():
    r = P.parse(REAL.format(d="SDD1"))
    assert r.detector_active is False                    # OBSERVED: zero rows
    assert len(r.data.intervals) == 0

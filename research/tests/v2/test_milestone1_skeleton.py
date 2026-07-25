"""Milestone I self-tests: interfaces + metadata models. No FITS access."""
import pytest

from app.v2.models.metadata import (FAIL_RULES, ChanType, FailLoud, Instrument,
                                    PARSER_VERSION, Provenance, TimeEpoch)
from app.v2.parsers.base import (REGISTRY, get_column, get_hdu, is_appledouble,
                                 require_equal, require_header)


def test_all_20_frozen_rules_present():
    assert len(FAIL_RULES) == 20
    assert set(FAIL_RULES) == {f"F-{i:02d}" for i in range(1, 21)}


def test_f12_is_documented_as_the_one_non_fatal_rule():
    assert "NOT FATAL" in FAIL_RULES["F-12"]


def test_failloud_rejects_rules_outside_the_frozen_contract():
    with pytest.raises(KeyError):
        FailLoud("F-99", "invented rule")


def test_failloud_message_is_traceable_to_contract():
    e = FailLoud("F-05", "bad epoch", file="x.lc", expected=40587, got=58484)
    s = str(e)
    assert "F-05" in s and "x.lc" in s and "40587" in s and "58484" in s


class _Hdr(dict):
    pass


def test_require_header_never_defaults__the_v1_defect():
    # v1: header.get("MJDREF", 58484.0) on files whose key is MJDREFI.
    hdr = _Hdr({"MJDREFI": 40587})
    assert require_header(hdr, "MJDREFI") == 40587
    with pytest.raises(FailLoud) as ei:
        require_header(hdr, "MJDREF", file="AL1_SOLEXS.lc")
    assert ei.value.rule == "F-02"


class _Col:
    def __init__(self, name): self.name = name


class _FakeHDU:
    def __init__(self, name, cols, data=None):
        self.name = name
        self.columns = [_Col(c) for c in cols]
        self.data = data or {c: [1, 2, 3] for c in cols}


def test_get_hdu_by_name_not_index():
    hdul = [_FakeHDU("PRIMARY", []), _FakeHDU("GTI", ["START", "STOP"])]
    assert get_hdu(hdul, "gti").name == "GTI"          # case-insensitive
    with pytest.raises(FailLoud) as ei:
        get_hdu(hdul, "RATE", file="f.gti")
    assert ei.value.rule == "F-02"


def test_get_column_is_case_insensitive__A2():
    # SoLEXS uses START/STOP; HEL1OS uses tstart/tstop for the same concept.
    sol = _FakeHDU("GTI", ["START", "STOP"])
    hel = _FakeHDU("GTI_CZT1", ["tstart", "tstop"])
    assert get_column(sol, "start") is not None
    assert get_column(hel, "TSTART") is not None
    with pytest.raises(FailLoud) as ei:
        get_column(sol, "RATE", file="f.gti")
    assert ei.value.rule == "F-04"


def test_require_equal_raises_with_rule_id():
    require_equal(340, 340, "F-17", "ok")
    with pytest.raises(FailLoud) as ei:
        require_equal(9, 340, "F-17", "DETCHANS mismatch")
    assert ei.value.rule == "F-17" and ei.value.got == 9


def test_appledouble_detection__F18():
    assert is_appledouble("a/._AL1_SOLEXS.lc.gz")
    assert is_appledouble("._x.fits")
    assert not is_appledouble("a/AL1_SOLEXS.lc.gz")


def test_registry_unknown_product_fails_loud():
    with pytest.raises(FailLoud) as ei:
        REGISTRY.get("solexs", "nonexistent")
    assert ei.value.rule == "F-18"


def test_chantype_separation_is_modelled__F11():
    assert ChanType.PI.value == "PI" and ChanType.PHA.value == "PHA"
    assert ChanType.PI != ChanType.PHA


def test_time_epoch_unix_constant_matches_contract():
    assert TimeEpoch.UNIX_MJDREFI == 40587           # MJD 40587 == 1970-01-01


def test_provenance_row_has_every_T7_field():
    p = Provenance(src_file="f", src_sha256="s", instrument=Instrument.SOLEXS.value,
                   detector="SDD2", product="lc", archive_version="v1.0",
                   obs_date="20240514", orbit_id=None, creator="solexs_pipeline-1.4",
                   processing_date="2026-05-06", rows_in=86400, rows_out=1440,
                   time_epoch_resolution="unix_seconds")
    row = p.to_row()
    for f in ("src_file", "src_sha256", "instrument", "detector", "product",
              "archive_version", "obs_date", "orbit_id", "creator",
              "processing_date", "rows_in", "rows_out", "parser_version",
              "parsed_at_utc", "time_epoch_resolution", "assumptions_applied"):
        assert f in row, f"T7 field {f} missing"
    assert row["parser_version"] == PARSER_VERSION

"""
Milestone VI self-tests: Version Resolution Engine (contract §4).

Falsifies every precedence rule, exercises both overlap classes on real archive
metadata, and proves duplicate-minute output is impossible.
"""
import json
import re

import numpy as np
import pandas as pd
import pytest

from app.v2.models.metadata import FailLoud
from app.v2.resolution.version_engine import (RULE_DURATION,
                                              RULE_PROCESSING_DATE, RULE_VERSION,
                                              CoverageMap, OrbitCandidate,
                                              assert_no_duplicate_minutes,
                                              build_coverage_map,
                                              resolve_candidates,
                                              select_owned_rows)

T0 = pd.Timestamp("2025-12-08T00:00:00Z")
DETS = ("CZT1", "CZT2", "CDTE1", "CDTE2")


def C(oid, *, ver=111, dur=3600, start=T0, dets=DETS, pdate=None, sha=None):
    return OrbitCandidate(orbit_id=oid, path=f"/x/{oid}", sha256=sha or f"sha_{oid}",
                          version=ver, duration_s=dur, t_start_utc=start,
                          t_stop_utc=start + pd.Timedelta(seconds=dur),
                          detectors=dets, processing_date=pdate)


# ── precedence rule 1: version ──────────────────────────────────────────────
def test_R1_higher_version_wins():
    a, b = C("a", ver=111), C("b", ver=211)
    w, rule = resolve_candidates([a, b])
    assert w.orbit_id == "b" and rule == RULE_VERSION


def test_R1_is_order_independent():
    """A winner must never depend on iteration order."""
    a, b = C("a", ver=111), C("b", ver=211)
    assert resolve_candidates([a, b])[0].orbit_id == "b"
    assert resolve_candidates([b, a])[0].orbit_id == "b"


def test_R1_observed_archive_versions_order_correctly():
    """OBSERVED distribution: V111 x371, V211 x16, V112 x3, V311 x1."""
    cands = [C("v111", ver=111), C("v112", ver=112), C("v211", ver=211),
             C("v311", ver=311)]
    assert resolve_candidates(cands)[0].orbit_id == "v311"
    assert resolve_candidates(list(reversed(cands)))[0].orbit_id == "v311"


# ── precedence rule 2: duration ─────────────────────────────────────────────
def test_R2_longer_duration_wins_when_versions_tie():
    a, b = C("short", ver=111, dur=1000), C("long", ver=111, dur=2000)
    w, rule = resolve_candidates([a, b])
    assert w.orbit_id == "long" and rule == RULE_DURATION


def test_R2_never_overrides_R1():
    """A longer file must NOT beat a higher version -- order is fixed."""
    a = C("longer_but_older", ver=111, dur=99999)
    b = C("shorter_but_newer", ver=211, dur=10)
    w, rule = resolve_candidates([a, b])
    assert w.orbit_id == "shorter_but_newer" and rule == RULE_VERSION


# ── precedence rule 3: processing date ──────────────────────────────────────
def test_R3_later_processing_date_wins_when_version_and_duration_tie():
    a = C("older", ver=111, dur=3600, pdate="2026-01-01")
    b = C("newer", ver=111, dur=3600, pdate="2026-05-06")
    w, rule = resolve_candidates([a, b])
    assert w.orbit_id == "newer" and rule == RULE_PROCESSING_DATE


def test_R3_never_overrides_R2():
    a = C("long_old", ver=111, dur=9000, pdate="2020-01-01")
    b = C("short_new", ver=111, dur=10, pdate="2026-01-01")
    w, rule = resolve_candidates([a, b])
    assert w.orbit_id == "long_old" and rule == RULE_DURATION


# ── precedence rule 4: F-14, never a coin-flip ──────────────────────────────
def test_R4_unresolved_terminates_F14():
    a, b = C("a", ver=111, dur=3600), C("b", ver=111, dur=3600)
    with pytest.raises(FailLoud) as e:
        resolve_candidates([a, b])
    assert e.value.rule == "F-14"


def test_R4_fires_when_processing_date_absent__the_real_hel1os_case():
    """OBSERVED: HEL1OS primaries carry NO `DATE` header.

    So R3 has no data source. If versions and durations tie, the engine MUST
    terminate rather than choose. This is F-14 by design, not a defect.
    """
    a, b = C("a", ver=111, dur=3600, pdate=None), C("b", ver=111, dur=3600, pdate=None)
    with pytest.raises(FailLoud) as e:
        resolve_candidates([a, b])
    assert e.value.rule == "F-14"
    assert "no DATE header" in str(e.value.got)


def test_R4_fires_when_only_one_side_has_a_processing_date():
    a, b = C("a", ver=111, dur=3600, pdate="2026-01-01"), C("b", ver=111, dur=3600)
    with pytest.raises(FailLoud) as e:
        resolve_candidates([a, b])
    assert e.value.rule == "F-14"


def test_R4_fires_when_processing_dates_are_equal():
    a = C("a", ver=111, dur=3600, pdate="2026-01-01")
    b = C("b", ver=111, dur=3600, pdate="2026-01-01")
    with pytest.raises(FailLoud) as e:
        resolve_candidates([a, b])
    assert e.value.rule == "F-14"


# ── Class A: identical interval, different version ──────────────────────────
def test_class_A_identical_interval_different_version():
    """The real pair: HLS_20251208_000008_43178sec V111 vs V211."""
    a = C("HLS_20251208_000008_43178sec_V111", ver=111, dur=43178, start=T0)
    b = C("HLS_20251208_000008_43178sec_V211", ver=211, dur=43178, start=T0)
    cm = build_coverage_map([a, b])
    assert len(cm.resolutions) > 0
    for det in DETS:
        for m in a.claimed_minutes():
            assert cm.owner(m, det) == b.orbit_id      # V211 wins everywhere
    assert {r.rule_invoked for r in cm.resolutions} == {RULE_VERSION}


# ── Class B: partial overlap -- file-level selection is INSUFFICIENT ─────────
def test_class_B_partial_overlap_each_file_keeps_its_exclusive_minutes():
    """The real case: 120003_43195sec_V211 vs 121028_42570sec_V111.

    Each file covers minutes the other lacks, so a file-level winner would
    DESTROY data. Only per-minute ownership is correct.
    """
    a = C("early_V211", ver=211, dur=1800, start=T0)                       # 00:00-00:30
    b = C("late_V111", ver=111, dur=1800, start=T0 + pd.Timedelta(minutes=20))  # 00:20-00:50
    cm = build_coverage_map([a, b])

    # a's exclusive region -> a
    assert cm.owner(T0 + pd.Timedelta(minutes=5), "CZT1") == "early_V211"
    # b's exclusive region -> b, even though b has the LOWER version.
    # A file-level "V211 wins" would have deleted these minutes entirely.
    assert cm.owner(T0 + pd.Timedelta(minutes=45), "CZT1") == "late_V111"
    # contested region -> precedence
    assert cm.owner(T0 + pd.Timedelta(minutes=25), "CZT1") == "early_V211"


def test_class_B_no_minute_is_lost():
    a = C("a", ver=211, dur=1800, start=T0)
    b = C("b", ver=111, dur=1800, start=T0 + pd.Timedelta(minutes=20))
    cm = build_coverage_map([a, b])
    union = set(a.claimed_minutes()) | set(b.claimed_minutes())
    for m in union:
        assert cm.owner(m, "CZT1") is not None, f"minute {m} lost"


# ── minute ownership invariant ──────────────────────────────────────────────
def test_every_minute_detector_has_exactly_one_owner():
    cands = [C("a", ver=111, dur=3600, start=T0),
             C("b", ver=211, dur=3600, start=T0 + pd.Timedelta(minutes=30)),
             C("c", ver=112, dur=3600, start=T0 + pd.Timedelta(minutes=45))]
    cm = build_coverage_map(cands)
    seen = {}
    for (m, d), o in cm._owners.items():
        assert (m, d) not in seen, "duplicate ownership"
        seen[(m, d)] = o
    cm.assert_unique_ownership()


def test_ownership_is_independent_of_candidate_order():
    """No implicit overwrite: last-write-wins must be impossible."""
    a = C("a", ver=111, dur=3600, start=T0)
    b = C("b", ver=211, dur=3600, start=T0)
    m1 = build_coverage_map([a, b])
    m2 = build_coverage_map([b, a])
    assert m1._owners == m2._owners


def test_duplicate_orbit_id_terminates():
    with pytest.raises(FailLoud) as e:
        build_coverage_map([C("same"), C("same", ver=211)])
    assert e.value.rule == "F-14"


def test_detectors_are_resolved_independently():
    a = C("a", ver=211, dur=3600, start=T0, dets=("CZT1",))
    b = C("b", ver=111, dur=3600, start=T0, dets=("CZT2",))
    cm = build_coverage_map([a, b])
    assert cm.owner(T0, "CZT1") == "a"
    assert cm.owner(T0, "CZT2") == "b"       # different detector -> no conflict


# ── the merge gate (§4 point 4) ─────────────────────────────────────────────
def test_select_owned_rows_requires_a_coverage_map():
    """There is no API that concatenates orbit files directly."""
    df = pd.DataFrame({"timestamp_utc": [T0], "v": [1.0]})
    with pytest.raises(FailLoud) as e:
        select_owned_rows(df, orbit_id="a", detector="CZT1",
                          coverage_map="not a map")     # type: ignore[arg-type]
    assert e.value.rule == "F-14"


def test_select_owned_rows_filters_but_never_modifies_values():
    """The engine selects provenance. It must not touch a measurement."""
    a = C("a", ver=211, dur=1800, start=T0)
    b = C("b", ver=111, dur=1800, start=T0 + pd.Timedelta(minutes=20))
    cm = build_coverage_map([a, b])
    ts = pd.date_range(T0, periods=50, freq="min", tz="UTC")
    vals = np.arange(50.0) * 3.7
    df = pd.DataFrame({"timestamp_utc": ts, "ctr": vals})
    out = select_owned_rows(df, orbit_id="a", detector="CZT1", coverage_map=cm)
    # every surviving value is byte-identical to its input -- no averaging,
    # no interpolation, no merging
    for _, row in out.iterrows():
        i = list(ts).index(row.timestamp_utc)
        assert row.ctr == vals[i]
    assert len(out) < len(df)                 # it did filter


def test_select_owned_rows_partitions_without_overlap_or_loss():
    a = C("a", ver=211, dur=1800, start=T0)
    b = C("b", ver=111, dur=1800, start=T0 + pd.Timedelta(minutes=20))
    cm = build_coverage_map([a, b])
    ts = pd.date_range(T0, periods=51, freq="min", tz="UTC")
    df = pd.DataFrame({"timestamp_utc": ts, "ctr": np.arange(51.0)})
    ka = select_owned_rows(df, orbit_id="a", detector="CZT1", coverage_map=cm)
    kb = select_owned_rows(df, orbit_id="b", detector="CZT1", coverage_map=cm)
    merged = pd.concat([ka, kb])
    assert set(ka.timestamp_utc) & set(kb.timestamp_utc) == set()      # no overlap
    assert len(merged) == len(set(merged.timestamp_utc))              # no dupes
    assert_no_duplicate_minutes(merged)                                # F-15 holds


# ── F-15 cannot be bypassed ─────────────────────────────────────────────────
def test_F15_catches_duplicate_minutes_even_if_the_map_is_bypassed():
    """Last line of defence: a hand-built duplicate must still terminate."""
    ts = [T0, T0, T0 + pd.Timedelta(minutes=1)]
    df = pd.DataFrame({"timestamp_utc": ts, "v": [1.0, 2.0, 3.0]})
    with pytest.raises(FailLoud) as e:
        assert_no_duplicate_minutes(df)
    assert e.value.rule == "F-15"


def test_F15_catches_sub_minute_duplicates_after_flooring():
    """Two samples in the same MINUTE are a duplicate even if seconds differ."""
    ts = [T0 + pd.Timedelta(seconds=5), T0 + pd.Timedelta(seconds=55)]
    df = pd.DataFrame({"timestamp_utc": ts, "v": [1.0, 2.0]})
    with pytest.raises(FailLoud) as e:
        assert_no_duplicate_minutes(df)
    assert e.value.rule == "F-15"


def test_F15_is_detector_aware():
    """Same minute, different detectors is legal; same detector is not."""
    df_ok = pd.DataFrame({"timestamp_utc": [T0, T0], "detector": ["CZT1", "CZT2"]})
    assert_no_duplicate_minutes(df_ok, detector_column="detector")
    df_bad = pd.DataFrame({"timestamp_utc": [T0, T0], "detector": ["CZT1", "CZT1"]})
    with pytest.raises(FailLoud) as e:
        assert_no_duplicate_minutes(df_bad, detector_column="detector")
    assert e.value.rule == "F-15"


def test_F15_passes_on_clean_output():
    ts = pd.date_range(T0, periods=10, freq="min", tz="UTC")
    assert_no_duplicate_minutes(pd.DataFrame({"timestamp_utc": ts}))


def test_coverage_map_rejects_unknown_owner():
    a = C("a")
    cm = build_coverage_map([a])
    cm._owners[(T0, "CZT1")] = "ghost_orbit"
    with pytest.raises(FailLoud) as e:
        cm.assert_unique_ownership()
    assert e.value.rule == "F-15"


# ── resolution log (§4) ─────────────────────────────────────────────────────
def test_resolution_log_has_every_required_field(tmp_path):
    a = C("HLS_A_V111", ver=111, dur=3600, start=T0, sha="aaa111")
    b = C("HLS_B_V211", ver=211, dur=3600, start=T0, sha="bbb211")
    cm = build_coverage_map([a, b])
    p = tmp_path / "version_resolution_log.json"
    log = cm.write_resolution_log(str(p))
    on_disk = json.loads(p.read_text())
    assert on_disk == log
    c = log["conflicts"][0]
    assert c["winner"]["orbit_id"] == "HLS_B_V211"          # winner
    assert c["winner"]["sha256"] == "bbb211"                # provenance hash
    assert c["rejected_candidates"][0]["orbit_id"] == "HLS_A_V111"   # rejected
    assert c["rejected_candidates"][0]["sha256"] == "aaa111"         # + its hash
    assert c["precedence_rule_invoked"] == RULE_VERSION      # rule invoked
    assert c["n_timestamps_affected"] > 0                    # timestamps affected
    assert "first" in c["timestamps_affected"]
    assert log["precedence_order"][-1] == "R4_unresolved_F14"


def test_resolution_log_empty_when_no_conflicts(tmp_path):
    cm = build_coverage_map([C("solo")])
    log = cm.write_resolution_log(str(tmp_path / "l.json"))
    assert log["n_conflicting_minute_detector_pairs"] == 0
    assert log["conflicts"] == []


# ── real archive metadata (Class A + Class B together) ─────────────────────
PAT = re.compile(r"HLS_(\d{8})_(\d{6})_(\d+)sec_lev1_V(\d{3})")


def _real_candidates(day="20251207"):
    import glob
    out = []
    for d in sorted(glob.glob(f"data/aditya_l1/real_l1_v1/hel1os/HLS_{day}_*")):
        m = PAT.search(d)
        if not m:
            continue
        date, start, dur, ver = m.groups()
        t0 = pd.Timestamp(f"{date[:4]}-{date[4:6]}-{date[6:]}T"
                          f"{start[:2]}:{start[2:4]}:{start[4:]}Z")
        out.append(OrbitCandidate(
            orbit_id=m.group(0), path=d, sha256=f"sha_{m.group(0)}",
            version=int(ver), duration_s=int(dur), t_start_utc=t0,
            t_stop_utc=t0 + pd.Timedelta(seconds=int(dur)), detectors=DETS))
    return out


@pytest.mark.skipif(not _real_candidates(), reason="real archive not extracted")
def test_real_archive_day_resolves_deterministically(tmp_path):
    """2025-12-07 has 3 orbits incl. a genuine Class-B overlap."""
    cands = _real_candidates("20251207")
    assert len(cands) == 3
    cm = build_coverage_map(cands)
    cm.assert_unique_ownership()
    log = cm.write_resolution_log(str(tmp_path / "log.json"))
    assert log["n_conflicting_minute_detector_pairs"] > 0
    # every claimed minute is owned by exactly one orbit
    union = set()
    for c in cands:
        for m in c.claimed_minutes():
            union.add(m)
    for m in union:
        assert cm.owner(m, "CZT1") is not None


@pytest.mark.skipif(not _real_candidates(), reason="real archive not extracted")
def test_real_archive_is_order_independent():
    import random
    cands = _real_candidates("20251207")
    base = build_coverage_map(cands)._owners
    for seed in (1, 2, 3):
        shuffled = cands[:]
        random.Random(seed).shuffle(shuffled)
        assert build_coverage_map(shuffled)._owners == base

"""HEL1OS parsers — per-field vs spec, no imputation, and §4 version resolution.

`| 18 | 18 | E5 | 900 | L | 17 | per-field vs spec | no imputation | parse fixtures |`

Every assertion cites the clause of `SPEC-parsers@r7` it enforces. Each fail-loud rule is
fired against a product built to violate exactly it — the archive contains no malformed
HEL1OS product, so a violating fixture is the only way to watch a rule reject anything.

r7 adds §5.1's time-representation allowance `ε_t`, so the comparisons that carry it are tested
from both sides: representation noise inside `ε_t` is admitted, and a disagreement beyond it
still terminates. §2.5's non-decreasing event rule is tested as written; the archive falsifies
it and the falsification is recorded OPEN in CONTRA-008 rather than absorbed here.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from contexts.ingest.parsers.hel1os import events, gti, hk, lc, orbit, spectra
from contexts.ingest.tests import hel1os_fixtures as fx
from domain.errors import ContractViolation
from domain.values import Digest, Identifier, Timestamp

DIGEST = Digest("a" * 64)


def violation(caught) -> str:
    return caught.value.message


# ═══════════════════════════════════════════ §4 — orbit identity and precedence


def test_the_orbit_stem_is_parsed_by_the_specified_regex():
    parsed = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    assert (parsed.date, parsed.start, parsed.duration_s, parsed.version) == (
        "20251208", "000008", 43178, 111)
    assert parsed.stem == "HLS_20251208_000008_43178sec_lev1_V111"


@pytest.mark.parametrize("bad", [
    "HLS_20251208_000008_43178sec_lev1", "AL1_SLX_L1_20240514_v1.0",
    "HLS_20251208_000008_43178sec_lev1_V11", "", None,
])
def test_a_name_that_is_not_an_orbit_stem_is_refused(bad):
    with pytest.raises(ContractViolation) as caught:
        orbit.parse_stem(bad)
    assert violation(caught).startswith("F-18")


def test_rule_1_higher_version_wins():
    """§4 precedence 1. Class A: identical interval, different version."""
    a = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    b = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V211")
    assert orbit.precedence(a, b) is b
    assert orbit.precedence(b, a) is b
    assert orbit.rule_applied(a, b) == "rule-1-higher-version"


def test_the_version_digits_are_opaque_not_decomposed():
    """§8 A-1: the three digits are undocumented and compared as one integer.

    V112 vs V211: a major/minor reading would make 1.1.2 lose to 2.1.1 for a reason nobody
    has authority for. As integers 112 < 211, which is what §4 specifies — and the point is
    that the rule is stated, not inferred.
    """
    low = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V112")
    high = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V211")
    assert orbit.precedence(low, high) is high


def test_rule_2_longer_duration_wins_on_a_version_tie():
    a = orbit.parse_stem("HLS_20251207_120003_43195sec_lev1_V111")
    b = orbit.parse_stem("HLS_20251207_120003_42570sec_lev1_V111")
    assert orbit.precedence(a, b) is a
    assert orbit.rule_applied(a, b) == "rule-2-longer-duration"


def test_rule_3_later_processing_date_wins():
    base = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    early = orbit.OrbitId(base.date, base.start, base.duration_s, base.version,
                          Timestamp("2025-12-10T00:00:00Z"))
    late = orbit.OrbitId(base.date, base.start, base.duration_s, base.version,
                         Timestamp("2025-12-20T00:00:00Z"))
    assert orbit.precedence(early, late) is late
    assert orbit.rule_applied(early, late) == "rule-3-later-processing-date"


def test_rule_4_terminates_and_never_coin_flips():
    """§4: "Still tied → F-14 terminate. Never coin-flip."

    The most important rule in §4, because the alternative is a silent, arbitrary choice
    between two products that claim the same coverage.
    """
    a = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    b = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    with pytest.raises(ContractViolation) as caught:
        orbit.precedence(a, b)
    assert violation(caught).startswith("F-14")
    assert "never coin-flip" in violation(caught)
    assert orbit.rule_applied(a, b) == "rule-4-terminate"


def test_an_equal_processing_date_still_terminates():
    base = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    same = Timestamp("2025-12-20T00:00:00Z")
    with pytest.raises(ContractViolation):
        orbit.precedence(
            orbit.OrbitId(base.date, base.start, base.duration_s, base.version, same),
            orbit.OrbitId(base.date, base.start, base.duration_s, base.version, same),
        )


def test_class_b_partial_overlap_is_detected():
    """§4: Class B — different start and duration, each covering seconds the other lacks.

    Detected, not resolved: resolving it needs the minute-level coverage map, which §4 ties
    to emitting T3/T4/T5 and which belongs to M3/E5/#19.
    """
    a = orbit.parse_stem("HLS_20251207_120003_43195sec_lev1_V211")
    b = orbit.parse_stem("HLS_20251207_121028_42570sec_lev1_V111")
    assert orbit.overlaps(a, b)
    assert orbit.overlaps(b, a)


def test_non_overlapping_orbits_are_not_reported_as_overlapping():
    a = orbit.parse_stem("HLS_20251207_000006_43190sec_lev1_V111")
    b = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    assert not orbit.overlaps(a, b)


def test_no_orbit_merge_api_exists():
    """§4.4: "There is no API that concatenates orbit files directly."

    The structural guarantee that naive ingestion cannot occur. #18 supplies the precedence
    rules; the merge that consumes them must take the coverage map as a required argument,
    and it belongs to #19. Shipping a merge here without that map would create precisely the
    API §4 forbids.
    """
    for forbidden in ("merge", "concat", "concatenate", "combine", "coverage_map",
                      "resolve_all", "ingest"):
        assert not hasattr(orbit, forbidden), f"orbit.py grew {forbidden!r}"


@pytest.mark.parametrize("detector, family", [
    ("czt1", "czt"), ("czt2", "czt"), ("cdte1", "cdte"), ("cdte2", "cdte"),
])
def test_each_detector_maps_to_its_family(detector, family):
    assert orbit.family_of(detector) == family


@pytest.mark.parametrize("bad", ["czt3", "sdd2", "solexs", "cdte", ""])
def test_an_unknown_detector_has_no_family(bad):
    with pytest.raises(ContractViolation) as caught:
        orbit.family_of(bad)
    assert violation(caught).startswith("F-07")


def test_the_detector_is_part_of_the_instrument_identity():
    parsed = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    assert parsed.detector_id("CZT1") == Identifier("hel1os-czt1")
    assert parsed.detector_id("cdte2") == Identifier("hel1os-cdte2")


# ═══════════════════════════════════════════ §2.6 — band light curves


def test_the_bands_are_parsed_from_extname(tmp_path):
    product = lc.parse(fx.write_lightcurve(tmp_path / "lc.fits"), DIGEST, detector="czt1")
    assert [(b.low_kev, b.high_kev) for b in product.bands] == list(fx.CZT_BANDS)
    assert product.bands[0].extname == "CZT1_LC_BAND_20.00KEV_TO_40.00KEV"


def test_the_cdte_family_has_its_own_bands(tmp_path):
    product = lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", detector="cdte1"),
                       DIGEST, detector="cdte1")
    assert [(b.low_kev, b.high_kev) for b in product.bands] == list(fx.CDTE_BANDS)


def test_an_unknown_band_is_never_silently_accepted(tmp_path):
    """F-10. §2.6: an unlisted band would attribute a rate to the wrong energy range."""
    bands = ((20.0, 40.0), (40.0, 60.0), (60.0, 80.0), (80.0, 150.0), (200.0, 400.0))
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", bands=bands), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-10")


def test_a_cdte_band_in_a_czt_file_is_refused(tmp_path):
    """The families' allowlists are separate; 5-20 keV is CdTe's, not CZT's."""
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", bands=fx.CDTE_BANDS),
                 DIGEST, detector="czt1")
    assert violation(caught).startswith("F-10")


def test_an_extname_that_encodes_no_band_is_refused(tmp_path):
    names = ["CZT1_LIGHTCURVE"] + [fx.band_extname("czt1", lo, hi)
                                   for lo, hi in fx.CZT_BANDS[1:]]
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", extnames=names), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-10")


def test_the_wrong_number_of_band_hdus_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", bands=fx.CZT_BANDS[:4]),
                 DIGEST, detector="czt1")
    assert violation(caught).startswith("F-10")


def test_the_total_band_is_identified_not_assumed_by_position(tmp_path):
    """HDU order is not a contract, so the total is recognised by its edges."""
    product = lc.parse(fx.write_lightcurve(tmp_path / "lc.fits"), DIGEST, detector="czt1")
    totals = [b for b in product.bands if b.is_total]
    assert len(totals) == 1
    assert (totals[0].low_kev, totals[0].high_kev) == (18.0, 160.0)


def test_the_rate_unit_is_declared_and_differs_from_solexs(tmp_path):
    """F-07: `CTR` is a rate in cts/sec; SoLEXS `.lc` is undeclared counts. Never shared."""
    product = lc.parse(fx.write_lightcurve(tmp_path / "lc.fits"), DIGEST, detector="czt1")
    observed = list(product.observations(source_id=Identifier("issdc-pradan"),
                                         ingest_time=None))
    assert {o.unit for o in observed} == {"cts/s"}

    from contexts.ingest.parsers.solexs import lc as solexs_lc
    assert solexs_lc.UNIT == "counts"
    assert solexs_lc.UNIT != "cts/s"


def test_the_ctr_unit_must_be_declared_as_a_rate(tmp_path):
    """§2.6: `CTR` declares `cts/sec`; the parser reads that rather than assuming it (F-07)."""
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", ctr_unit="counts"), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-07")


def test_an_undeclared_ctr_unit_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", ctr_unit=None), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-07")


def test_a_negative_rate_is_physically_impossible(tmp_path):
    rates = {(20.0, 40.0): [1.0, -2.0] + [3.0] * 118}
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", rates=rates), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-19")


def test_a_nan_rate_is_refused_rather_than_read_as_absent(tmp_path):
    """NO IMPUTATION, and no imported convention either.

    SoLEXS §2.1 declares NaN as its missing-data sentinel. §2.6 declares none for `CTR`.
    Treating a NaN here as "observed to be absent" would import one instrument's convention
    into another, which is exactly what F-07 forbids — so it terminates instead.
    """
    rates = {(20.0, 40.0): [1.0, math.nan] + [3.0] * 118}
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", rates=rates), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-07")
    assert "across instruments" in violation(caught)


def test_a_non_increasing_time_axis_is_refused(tmp_path):
    """§2.6: MJD strictly increasing — unlike §2.8 housekeeping, where r4 removed it."""
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(120)]
    mjd[10] = mjd[9]
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lightcurve(tmp_path / "lc.fits", mjd=mjd), DIGEST,
                 detector="czt1")
    assert violation(caught).startswith("F-16")


def test_the_mjd_epoch_is_converted_exactly(tmp_path):
    """MJD 40587 = the Unix epoch. §2.5 anchors TSTART 61017.0000988685 to 2025-12-08."""
    assert lc.MJD_UNIX_EPOCH == 40587.0
    assert str(lc.mjd_to_timestamp(fx.TSTART_MJD)).startswith("2025-12-08T00:00:08")


# ═══════════════════════════════════════════ §2.7 — spectra and R-1


@pytest.mark.parametrize("detector, detchans", [
    ("czt1", 341), ("czt2", 341), ("cdte1", 511), ("cdte2", 511),
])
def test_detchans_is_validated_against_the_family_allowlist(tmp_path, detector, detchans):
    """§2.7 r5: never a single scalar."""
    product = spectra.parse(
        fx.write_spectra(tmp_path / "s.fits", detector=detector), DIGEST, detector=detector)
    assert product.header.detchans == detchans
    assert spectra.DETCHANS_BY_FAMILY[product.header.family] == detchans


def test_a_czt_file_declaring_the_cdte_channel_count_is_refused(tmp_path):
    """An unlisted (family, DETCHANS) pair terminates via F-07."""
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", detector="czt1", detchans=511),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-07")


@pytest.mark.parametrize("detchans", [340, 342, 512])
def test_any_other_channel_count_is_refused(tmp_path, detchans):
    """340 is SoLEXS's PI space — the nearest miss, and the one F-11 names."""
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", detchans=detchans),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-07")


def test_the_three_channel_spaces_stay_distinct():
    """F-11: SoLEXS PI(340), CZT PHA(341), CdTe PHA(511) are incommensurable."""
    spaces = spectra.INCOMMENSURABLE_CHANNEL_SPACES
    assert spaces[("solexs", "PI")] == 340
    assert spaces[("czt", "PHA")] == 341
    assert spaces[("cdte", "PHA")] == 511
    assert len(set(spaces.values())) == 3

    from contexts.ingest.parsers.solexs import pi as solexs_pi
    assert solexs_pi.DETCHANS == 340
    assert solexs_pi.DETCHANS not in spectra.DETCHANS_BY_FAMILY.values()


def test_the_chantype_is_pha_not_pi(tmp_path):
    """PI is gain-corrected, PHA is raw pulse height. Not the same space."""
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", chantype="PI"),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-07")


def test_hduclas3_is_count_singular(tmp_path):
    """§2.7 `OBSERVED`: 'COUNT', where SoLEXS §2.2 declares 'COUNTS'. Read, not assumed."""
    assert spectra.HDUCLAS3 == "COUNT"
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", hduclas3="COUNTS"),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-07")


def test_r1_resolves_h3_on_the_observed_convention(tmp_path):
    """§2.7 r4: relative seconds from the header epoch, tested first because unit='s'."""
    product = spectra.parse(fx.write_spectra(tmp_path / "s.fits"), DIGEST, detector="czt1")
    assert product.epoch.hypothesis == "H3"
    assert product.epoch.exposure_s == 20.0


def test_r1_records_its_residual(tmp_path):
    """§2.7: "The resolved hypothesis and its residual are recorded in T7 provenance."

    The recording is #19's; the measurement is this parser's, and it must be available.
    """
    product = spectra.parse(fx.write_spectra(tmp_path / "s.fits"), DIGEST, detector="czt1")
    assert product.epoch.residual_s >= 0
    assert math.isfinite(product.epoch.residual_s)


def test_r1_falls_through_to_h1_for_mjd_columns(tmp_path):
    """H1 retained because a reprocessed product could switch to an absolute epoch."""
    columns = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    product = spectra.parse(
        fx.write_spectra(tmp_path / "s.fits", col_tstart=columns), DIGEST, detector="czt1")
    assert product.epoch.hypothesis == "H1"


def test_r1_falls_through_to_h2_for_unix_seconds(tmp_path):
    """H2 retained for the same reason as H1."""
    unix0 = (fx.TSTART_MJD - 40587.0) * 86400.0
    columns = [unix0 + i * 20.0 for i in range(20)]
    product = spectra.parse(
        fx.write_spectra(tmp_path / "s.fits", col_tstart=columns), DIGEST, detector="czt1")
    assert product.epoch.hypothesis == "H2"


def test_r1_terminates_when_every_hypothesis_fails(tmp_path):
    """F-06: §5 admits no ambiguous time."""
    columns = [500_000.0 + i * 20.0 for i in range(20)]
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", col_tstart=columns),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-06")
    assert "R-1" in violation(caught)


def test_h3_requires_the_first_offset_to_be_exactly_zero(tmp_path):
    """§2.7: "col[0] == 0 exactly". A near-zero offset is not H3, and falls through."""
    columns = [0.5 + i * 20.0 for i in range(20)]
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", col_tstart=columns),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-06")


def test_a_two_bin_span_disagreement_still_fails_h3(tmp_path):
    """The MJD-precision allowance covers 79 ns of float error, not a real disagreement.

    A header span two bins longer than the columns cover is a genuine mismatch and must not
    be absorbed. It falls through H3, then H1 and H2, and terminates.
    """
    header_tstop = fx.TSTART_MJD + (20 * 20.0 + 3 * 20.0) / 86400.0
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", header_tstop=header_tstop),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-06")


def test_a_varying_channel_map_is_refused(tmp_path):
    """F-08, same rule as SoLEXS §2.2 but checked separately — sharing it would share a space."""
    varying = [list(range(341))] * 19 + [list(range(1, 342))]
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", channel_map=varying),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-08")


def test_the_spectra_stream_rather_than_materialise(tmp_path):
    import inspect
    assert inspect.isgeneratorfunction(spectra.Spectra.spectra)
    product = spectra.parse(fx.write_spectra(tmp_path / "s.fits"), DIGEST, detector="czt1")
    first = next(iter(product.spectra()))
    assert len(first.counts) == 341
    assert first.exposure == 20.0


def test_a_negative_spectral_count_is_refused(tmp_path):
    counts = np.tile(np.arange(341, dtype=float), (20, 1))
    counts[3][7] = -1.0
    with pytest.raises(ContractViolation) as caught:
        list(spectra.parse(fx.write_spectra(tmp_path / "s.fits", counts=counts),
                           DIGEST, detector="czt1").spectra())
    assert violation(caught).startswith("F-19")


# ═══════════════════════════════════════════ §2.8 — housekeeping


def test_archive_order_is_preserved_exactly(tmp_path):
    """§2.8 r4, binding: the parser performs NO sorting.

    "The parser is a lossless representation of the archive — reading and transforming are
    separate acts, and a parser that silently reorders is no longer a faithful reader."
    """
    jittered = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    jittered[5], jittered[6] = jittered[6], jittered[5]

    product = hk.parse(fx.write_hk(tmp_path / "hk.fits", mjd=jittered), DIGEST)
    assert list(product.mjd) == jittered
    assert list(product.mjd) != sorted(jittered)


def test_no_sorting_function_exists():
    for forbidden in ("sort", "sorted", "reorder", "chronological"):
        assert not any(forbidden in name.lower() for name in dir(hk)), (
            f"hk.py exposes {forbidden!r}; §2.8 places chronological_sort outside the "
            f"parser layer"
        )


def test_an_inversion_is_recorded_not_rejected(tmp_path):
    """§2.8 r4: the non-decreasing requirement was falsified by the archive and removed."""
    jittered = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    jittered[5], jittered[6] = jittered[6], jittered[5]

    product = hk.parse(fx.write_hk(tmp_path / "hk.fits", mjd=jittered), DIGEST)
    assert product.inversions.n_out_of_order == 1
    assert product.inversions.max_backward_step_s > 0


def test_no_jitter_threshold_is_defined():
    """§2.8: "The magnitude is reported, never compared against an invented tolerance."

    So `InversionStats` has no limit, no `is_acceptable`, and nothing to compare against.
    """
    stats = hk.InversionStats(rows=10, steps=9, n_out_of_order=3, max_backward_step_s=0.9)
    public = [name for name in dir(stats) if not name.startswith("_")]
    for forbidden in ("threshold", "limit", "tolerance", "acceptable", "passes", "within"):
        assert not any(forbidden in name.lower() for name in public), (
            f"InversionStats exposes {forbidden!r}; §2.8 reports the magnitude and defines "
            f"no threshold to compare it against"
        )
    assert set(public) == {
        "max_backward_step_ms", "max_backward_step_s", "n_out_of_order", "rows", "steps"
    }


def test_a_duplicate_timestamp_is_a_defect(tmp_path):
    """§2.8 r4 kept this one: an inversion is jitter, a duplicate is a genuine defect."""
    duplicated = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    duplicated[7] = duplicated[6]
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", mjd=duplicated), DIGEST)
    assert violation(caught).startswith("F-16")
    assert "duplicate" in violation(caught)


def test_the_header_span_must_contain_the_measurements(tmp_path):
    """§2.8 r7 assigns this check F-06; the bound is widened by ε_t and by nothing else."""
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", header_tstop=fx.TSTART_MJD), DIGEST)
    assert violation(caught).startswith("F-06")


def test_suninfov_is_a_first_class_flag(tmp_path):
    """§2.8 binding: data outside Sun-in-FOV is not solar signal."""
    flags = [1] * 10 + [0] * 10
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(len(flags))]
    product = hk.parse(
        fx.write_hk(tmp_path / "hk.fits", mjd=mjd, suninfov=flags), DIGEST)
    assert product.sun_in_fov(0) is True
    assert product.sun_in_fov(15) is False
    assert list(product.suninfov) == flags


@pytest.mark.parametrize("bad", [2, -1, 7])
def test_a_suninfov_outside_the_declared_domain_is_refused(tmp_path, bad):
    """Coercing it would decide whether data is solar signal on the parser's authority."""
    flags = [1] * 19 + [bad]
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(len(flags))]
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", mjd=mjd, suninfov=flags), DIGEST)
    assert violation(caught).startswith("F-07")


def test_the_czt2enth_unit_assumption_is_recorded(tmp_path):
    """§8 A-4: the assumption travels with the data rather than living in a docstring."""
    product = hk.parse(fx.write_hk(tmp_path / "hk.fits"), DIGEST)
    assert product.assumptions
    assert any("czt2enth" in a for a in product.assumptions)


def test_the_phase_1a_columns_are_captured(tmp_path):
    """§2.8's decisive columns: pile-up, saturation, thermal, pointing."""
    product = hk.parse(fx.write_hk(tmp_path / "hk.fits"), DIGEST)
    for name in hk.PILEUP + hk.SATURATION + hk.THERMAL:
        assert name in product.columns


# ═══════════════════════════════════════════ §2.9 — GTI


def test_columns_are_read_case_insensitively(tmp_path):
    """§2.9 / §8 A-2: lowercase `tstart`/`tstop`, where SoLEXS uses uppercase START/STOP.

    A case-sensitive lookup would fail as F-04 and look like a missing column rather than a
    spelling difference between instruments.
    """
    product = gti.parse(fx.write_gti(tmp_path / "g.fits"), DIGEST, detector="czt1")
    assert len(product.intervals) == 1
    assert product.detector_active

    from contexts.ingest.parsers.solexs import gti as solexs_gti
    assert solexs_gti is not gti


def test_an_empty_gti_is_legal(tmp_path):
    """F-12, the single deliberate non-terminating rule."""
    product = gti.parse(fx.write_gti(tmp_path / "g.fits", intervals=[]), DIGEST,
                        detector="czt1")
    assert product.detector_active is False
    assert product.intervals == ()


def test_no_exposure_equality_rule_is_imported_from_solexs(tmp_path):
    """§2.3's Σ(STOP−START+1) == EXPOSURE rests on 1 s sampling and a declared EXPOSURE.

    §2.9 declares neither, so importing the rule would apply one instrument's convention to
    another — F-07's whole subject.
    """
    product = gti.parse(fx.write_gti(tmp_path / "g.fits"), DIGEST, detector="czt1")
    assert product.live_time_s > 0
    assert not hasattr(product, "declared_exposure")


def test_a_bound_that_is_not_an_mjd_is_refused(tmp_path):
    """§2.9 leaves the unit undeclared; a bound outside the plausible range is not
    reinterpreted as another epoch."""
    with pytest.raises(ContractViolation) as caught:
        gti.parse(fx.write_gti(tmp_path / "g.fits", intervals=[(1.7e9, 1.7e9 + 100)]),
                  DIGEST, detector="czt1")
    assert violation(caught).startswith("F-05")


def test_an_inverted_interval_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        gti.parse(fx.write_gti(tmp_path / "g.fits",
                               intervals=[(fx.TSTART_MJD + 0.5, fx.TSTART_MJD)]),
                  DIGEST, detector="czt1")
    assert violation(caught).startswith("F-09")


# ═══════════════════════════════════════════ §2.5 — events


def test_all_four_detector_hdus_are_required(tmp_path):
    """F-03: three detectors' events are a different measurement, not a smaller one."""
    with pytest.raises(ContractViolation) as caught:
        events.parse(fx.write_events(tmp_path / "e.fits",
                                     detectors=("czt1", "czt2", "cdte1")), DIGEST)
    assert violation(caught).startswith("F-03")


def test_detnam_must_match_the_hdu_it_labels(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        events.parse(fx.write_events(tmp_path / "e.fits", detnam={"czt1": "CZT2"}), DIGEST)
    assert violation(caught).startswith("F-03")


def test_the_event_reader_emits_no_observations(tmp_path):
    """§2.5, binding: the parser MUST expose an event reader but MUST NOT ingest events
    into the canonical minute tables.

    Enforced by absence — there is no `observations()` to call, so events cannot flow into
    #19's tables by default.
    """
    product = events.parse(fx.write_events(tmp_path / "e.fits"), DIGEST)
    assert not hasattr(product, "observations")
    assert not hasattr(events, "observations")
    for detector in product.detectors:
        assert not hasattr(detector, "observations")


def test_event_energy_is_already_calibrated_in_kev(tmp_path):
    """§2.5: unlike SoLEXS, HEL1OS ships keV. Both facts are true and must not be merged."""
    product = events.parse(fx.write_events(tmp_path / "e.fits"), DIGEST)
    first = next(iter(product.events("czt1")))
    assert first.energy_kev == 20.0
    assert events.ENERGY_UNIT == "keV"

    from contexts.ingest.parsers.solexs import pi as solexs_pi
    assert not hasattr(solexs_pi, "ENERGY_UNIT")


def test_a_non_positive_event_energy_is_refused(tmp_path):
    """§2.5 validates `ener > 0`."""
    energies = [20.0] * 9 + [0.0]
    with pytest.raises(ContractViolation) as caught:
        list(events.parse(fx.write_events(tmp_path / "e.fits", energies=energies),
                          DIGEST).events("czt1"))
    assert violation(caught).startswith("F-19")


def test_events_stream_rather_than_materialise(tmp_path):
    import inspect
    assert inspect.isgeneratorfunction(events.EventList.events)


# ═══════════════════════════════════════════ §5.1 — the time-representation allowance


def test_the_allowance_is_the_contract_value():
    """§5.1: ε_t = 1 ms, and it is the contract's value rather than each module's.

    hk, spectra and events all compare an MJD-derived time against a bound; each imports the
    one constant, so no module can quietly hold a tolerance of its own.
    """
    assert lc.TIME_REPRESENTATION_ALLOWANCE_S == 1e-3
    for module in (spectra, hk, events):
        source = Path(module.__file__).read_text()
        assert "TIME_REPRESENTATION_ALLOWANCE_S" in source
        assert "math.ulp" not in source


def test_h3_admits_representation_error_within_the_allowance(tmp_path):
    """§2.7 r7: the one-bin bound carries ε_t, so float64 noise does not reject a valid product."""
    header_tstop = fx.TSTART_MJD + (20 * 20.0 + 20.0 + 0.4e-3) / 86400.0
    product = spectra.parse(fx.write_spectra(tmp_path / "s.fits", header_tstop=header_tstop),
                            DIGEST, detector="czt1")
    assert product.epoch.hypothesis == "H3"


def test_h3_refuses_a_disagreement_beyond_the_allowance(tmp_path):
    """ε_t is representation, not physics: 3 ms past the bin bound is a disagreement."""
    header_tstop = fx.TSTART_MJD + (20 * 20.0 + 20.0 + 3e-3) / 86400.0
    with pytest.raises(ContractViolation) as caught:
        spectra.parse(fx.write_spectra(tmp_path / "s.fits", header_tstop=header_tstop),
                      DIGEST, detector="czt1")
    assert violation(caught).startswith("F-06")


def test_the_hk_header_span_admits_representation_error(tmp_path):
    """§2.8 r7: a bound a fraction of a millisecond inside the data is representation noise."""
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    product = hk.parse(
        fx.write_hk(tmp_path / "hk.fits", mjd=mjd,
                    header_tstop=max(mjd) - 0.4e-3 / 86400.0), DIGEST)
    assert product.inversions.rows == 20


def test_the_hk_header_span_refuses_a_real_excursion(tmp_path):
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(20)]
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", mjd=mjd,
                             header_tstop=max(mjd) - 3e-3 / 86400.0), DIGEST)
    assert violation(caught).startswith("F-06")


# ═══════════════════════════════════════════ §2.8 — every decisive column, with its unit


def test_every_decisive_column_is_captured_with_its_archive_dtype(tmp_path):
    """§2.8's decisive columns, by the archive's spelling (CONTRA-007 Observation E)."""
    product = hk.parse(fx.write_hk(tmp_path / "hk.fits"), DIGEST)
    for name in hk.CAPTURED:
        assert name in product.columns, name
    for name in ("czt1hotpixcnt", "czt2bunpxctr", "fehkstat", "cdte1pilectr"):
        assert isinstance(product.columns[name][0], int)
    assert isinstance(product.columns["czthvmon"][0], float)


def test_the_stated_units_are_checked_not_assumed(tmp_path):
    product = hk.parse(fx.write_hk(tmp_path / "hk.fits"), DIGEST)
    for name, stated in hk.STATED_UNITS.items():
        assert product.units[name] == stated
    assert product.units["cdte1enerthr"] is None


def test_a_declared_unit_contradicting_section_2_8_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", units={"czthvmon": "mV"}), DIGEST)
    assert violation(caught).startswith("F-07")


def test_czt2enth_takes_the_czt1enth_unit_under_a4(tmp_path):
    """§8 A-4: undeclared, so czt1enth's keV is applied and the assumption travels."""
    product = hk.parse(fx.write_hk(tmp_path / "hk.fits"), DIGEST)
    assert product.units["czt2enth"] == "keV"
    assert any("czt2enth" in assumption for assumption in product.assumptions)


def test_a_contradictory_czt2enth_unit_is_refused(tmp_path):
    """A-4 covers an undeclared unit, never two disagreeing declarations of one quantity."""
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", units={"czt2enth": "meV"}), DIGEST)
    assert violation(caught).startswith("F-07")


def test_a_missing_decisive_column_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", omit=("fehkstat",)), DIGEST)
    assert violation(caught).startswith("F-04")


def test_only_the_two_czt_temperatures_must_be_finite(tmp_path):
    """§2.8 names `czt1temp`/`czt2temp`. The CdTe temperatures are carried, NaN included."""
    rows = 20
    product = hk.parse(
        fx.write_hk(tmp_path / "hk.fits", rows=rows,
                    values={"cdte1temp": [math.nan] * rows}), DIGEST)
    assert math.isnan(product.columns["cdte1temp"][0])

    with pytest.raises(ContractViolation) as caught:
        hk.parse(fx.write_hk(tmp_path / "hk.fits", rows=rows,
                             values={"czt1temp": [math.nan] * rows}), DIGEST)
    assert violation(caught).startswith("F-16")


# ═══════════════════════════════════════════ §2.5 r7 — the event row rules


def test_event_energy_must_be_declared_in_kev(tmp_path):
    """§2.5: HEL1OS ships calibrated keV; the declaration is read, not assumed (F-07)."""
    with pytest.raises(ContractViolation) as caught:
        events.parse(fx.write_events(tmp_path / "e.fits", ener_unit="MeV"), DIGEST)
    assert violation(caught).startswith("F-07")


def test_czt_event_hdus_require_pix_and_offsetchn(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        events.parse(fx.write_events(tmp_path / "e.fits", omit=("pix",)), DIGEST)
    assert violation(caught).startswith("F-04")


def test_czt_events_expose_the_pixel_and_cdte_events_do_not(tmp_path):
    """§2.5 lists `pix`/`offsetchn` for CZT only; a reader that dropped them would be lossy."""
    product = events.parse(fx.write_events(tmp_path / "e.fits"), DIGEST)
    czt = next(iter(product.events("czt1")))
    cdte = next(iter(product.events("cdte1")))
    assert czt.pixel is not None and czt.offset_channel is not None
    assert cdte.pixel is None and cdte.offset_channel is None


def test_an_event_outside_the_header_span_is_refused(tmp_path):
    """§2.5 r7: the span check, widened by ε_t and by nothing else."""
    beyond = [fx.TSTART_MJD + 0.6]
    with pytest.raises(ContractViolation) as caught:
        list(events.parse(fx.write_events(tmp_path / "e.fits", mjd=beyond),
                          DIGEST).events("czt1"))
    assert violation(caught).startswith("F-06")


def test_v_evt_2_accepts_the_millisecond_rounding_the_archive_writes(tmp_path):
    """`utc-isot` is the mjd instant to the millisecond, so it disagrees by ≤ 0.5 ms."""
    product = events.parse(fx.write_events(tmp_path / "e.fits"), DIGEST)
    assert sum(1 for _ in product.events("czt1")) == 10


def test_v_evt_2_refuses_a_disagreeing_isot(tmp_path):
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(5)]
    drifted = [fx.isot_of(value + 0.05 / 86400.0) for value in mjd]
    with pytest.raises(ContractViolation) as caught:
        list(events.parse(fx.write_events(tmp_path / "e.fits", mjd=mjd, isot=drifted),
                          DIGEST).events("czt1"))
    assert violation(caught).startswith("F-06")
    assert "V-EVT-2" in violation(caught)


def test_an_unparseable_isot_is_refused(tmp_path):
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(3)]
    with pytest.raises(ContractViolation) as caught:
        list(events.parse(fx.write_events(tmp_path / "e.fits", mjd=mjd,
                                          isot=["not-an-instant"] * 3),
                          DIGEST).events("czt1"))
    assert violation(caught).startswith("F-06")


def test_a_decreasing_event_timestamp_is_refused(tmp_path):
    """§2.5 as written, enforced although the archive falsifies it (CONTRA-008, OPEN)."""
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(6)]
    mjd[4] = mjd[2]
    with pytest.raises(ContractViolation) as caught:
        list(events.parse(fx.write_events(tmp_path / "e.fits", mjd=mjd), DIGEST).events("czt1"))
    assert violation(caught).startswith("F-16")
    assert "CONTRA-008" in violation(caught)


def test_equal_event_timestamps_are_permitted(tmp_path):
    """§2.5 says non-decreasing, not strictly increasing: events share a packet timestamp."""
    mjd = [fx.TSTART_MJD, fx.TSTART_MJD, fx.TSTART_MJD + 1 / 86400.0]
    product = events.parse(fx.write_events(tmp_path / "e.fits", mjd=mjd), DIGEST)
    assert sum(1 for _ in product.events("czt1")) == 3


def test_rows_before_a_violation_are_yielded_and_valid(tmp_path):
    """Streaming means the consumer sees the valid prefix, then the rule terminates the run."""
    mjd = [fx.TSTART_MJD + i / 86400.0 for i in range(6)]
    mjd[4] = mjd[2]
    stream = events.parse(fx.write_events(tmp_path / "e.fits", mjd=mjd), DIGEST).events("czt1")
    seen = []
    with pytest.raises(ContractViolation):
        for event in stream:
            seen.append(event)
    assert len(seen) == 4


# ═══════════════════════════════════════════ traceability and purity


@pytest.mark.parametrize("product", ["lc", "spectra", "gti", "hk", "events"])
def test_every_product_carries_the_digest_of_its_bytes(tmp_path, product):
    """ADR-0005: every parsed entity traceable to its originating archive and digest."""
    built = {
        "lc": lambda: lc.parse(fx.write_lightcurve(tmp_path / "a.fits"), DIGEST,
                               detector="czt1"),
        "spectra": lambda: spectra.parse(fx.write_spectra(tmp_path / "b.fits"), DIGEST,
                                         detector="czt1"),
        "gti": lambda: gti.parse(fx.write_gti(tmp_path / "c.fits"), DIGEST,
                                 detector="czt1"),
        "hk": lambda: hk.parse(fx.write_hk(tmp_path / "d.fits"), DIGEST),
        "events": lambda: events.parse(fx.write_events(tmp_path / "e.fits"), DIGEST),
    }[product]()
    assert built.source_digest == DIGEST


def test_no_hel1os_parser_reads_a_clock():
    """TIS §0.4: ingest_time is stamped at the acquisition boundary and nowhere else."""
    for module in (lc, spectra, gti, hk, events, orbit):
        source = Path(module.__file__).read_text()
        for forbidden in ("datetime.now", "utcnow", "time.time", "boundary.stamp"):
            assert forbidden not in source, f"{module.__name__} reads a clock"


def test_no_hel1os_parser_interpolates_or_repairs():
    for module in (lc, spectra, gti, hk, events):
        names = {name.lower() for name in dir(module)}
        for forbidden in ("interpolate", "interp", "smooth", "fillna", "impute",
                          "resample", "repair", "ffill", "bfill"):
            assert not any(forbidden in name for name in names), (
                f"{module.__name__} exposes {forbidden!r}")


def test_neither_instrument_imports_the_other():
    """F-07 and F-11 made structural: the two parser packages are independent.

    The only shared code is `_fits`, which knows nothing of either instrument's conventions.
    """
    import contexts.ingest.parsers.solexs as solexs_pkg

    for module in (lc, spectra, gti, hk, events, orbit):
        assert "parsers.solexs" not in Path(module.__file__).read_text()
    for name in ("lc", "pi", "gti"):
        source = Path(getattr(solexs_pkg, name).__file__).read_text()
        assert "parsers.hel1os" not in source

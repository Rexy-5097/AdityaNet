"""SoLEXS parsers — per-field vs spec, and the no-imputation property.

`| 17 | 17 | E5 | 900 | L | 15,12 | per-field vs spec | no imputation | parse fixtures |`

Every assertion below cites the clause of `SPEC-parsers@r6` it enforces. Two halves:

**Per-field vs spec** — each declared keyword, column, unit and count is checked, and each
fail-loud rule (§5) is fired deliberately against a product built to violate exactly it. The
archive contains no malformed product, so a violating fixture is the only way to watch a rule
reject anything.

**No imputation** — the Property column. §2.1 as amended at r2 is binding: NaN passes through
unchanged, is never imputed, never converted to zero, never removed. The property is
quantified over every position and both directions, because collapsing NaN and 0.0 is the one
error that would be undetectable in every downstream artifact.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from contexts.ingest.parsers.solexs import gti, lc, pi
from contexts.ingest.tests import solexs_fixtures as fx
from domain.errors import ContractViolation
from domain.values import Digest, Identifier, Timestamp

DIGEST = Digest("a" * 64)
SOURCE = Identifier("issdc-pradan")


#: Fixtures are written UNCOMPRESSED. astropy reads both, the parsers never inspect the
#: extension, and gzipping every fixture costs 1.26 s against 0.01 s — 126× for no coverage.
#: The real `.gz` path is exercised by `test_a_gzipped_product_parses_identically` below and
#: by every real-corpus test, which read the archive's own compressed products.
def parsed_lc(tmp_path, **kwargs):
    return lc.parse(fx.write_lc(fx.sdd2(tmp_path) / "x.lc", **kwargs), DIGEST)


def parsed_gti(tmp_path, **kwargs):
    return gti.parse(fx.write_gti(fx.sdd2(tmp_path) / "x.gti", **kwargs), DIGEST)


def parsed_pi(tmp_path, **kwargs):
    """A `.pi` product for the NEGATIVE cases, deliberately short.

    Short is safe here because §2.2's declarations and channel space are checked before the
    row count, so a fixture violating F-07/F-08/F-11 fails on the rule under test. Positive
    cases use `full_day_pi`, which is full size and written once per session.
    """
    return pi.parse(fx.write_pi(fx.sdd2(tmp_path) / "x.pi", **kwargs), DIGEST)


@pytest.fixture(scope="session")
def full_day_pi(tmp_path_factory):
    """One real-size `.pi`: 86,400 spectra × 340 channels.

    Session-scoped because writing it costs ~11 s. §2.2 records ~472 MB/day decompressed, so
    this is the one place the suite pays that price, and it pays it once.
    """
    directory = tmp_path_factory.mktemp("pi_full")
    return pi.parse(fx.write_pi(directory / "full.pi", rows=86_400), DIGEST)


def violation(caught) -> str:
    return caught.value.message


# ═══════════════════════════════════════════════════ §2.1 — .lc per-field


def test_the_lightcurve_parses_every_declared_field(tmp_path):
    """§2.1's "Metadata to capture" list, read from the headers that actually carry it."""
    product = parsed_lc(tmp_path)
    header = product.header
    assert header.mission == "ADITYA-L1"
    assert header.telescope == "AL1"
    assert header.instrument == "SoLEXS"
    assert header.origin == "ISSDC"
    assert header.creator == "solexs_pipeline-1.4"
    assert header.obs_date == "2024-05-14"
    assert header.detector == "SDD2"
    assert header.timedel == 1.0
    assert header.numband == "4"
    assert header.rows == 86_400


def test_the_epoch_is_unix_seconds_utc(tmp_path):
    """§2.1: MJDREFI=40587 → MJD 40587 = 1970-01-01 = the Unix epoch.

    Verified against the archive's own anchor: TSTART=1715644800.0 = 2024-05-14T00:00:00Z.
    """
    product = parsed_lc(tmp_path)
    assert product.header.tstart == 1_715_644_800.0
    assert str(lc.unix_to_timestamp(product.header.tstart)) == "2024-05-14T00:00:00Z"
    assert lc.MJDREFI_UNIX == 40587


def test_the_values_are_counts_not_a_rate(tmp_path):
    """F-07: semantics come from HDUCLAS3, never from EXTNAME.

    The HDU is called RATE and holds counts per 1-second bin. Reading the name would divide
    by a second that was never applied.
    """
    product = parsed_lc(tmp_path)
    assert lc.QUANTITY == "counts"
    assert lc.UNIT == "counts"
    observations = list(product.observations(source_id=SOURCE, ingest_time=None))
    assert {o.unit for o in observations} == {"counts"}
    assert {o.quantity for o in observations} == {"counts"}


def test_the_detector_is_part_of_the_instrument_identity(tmp_path):
    """SDD1 and SDD2 are two physical detectors carrying different products (§1.1)."""
    assert parsed_lc(tmp_path).instrument_id == Identifier("solexs-sdd2")


@pytest.mark.parametrize(
    "key, value, rule",
    [
        ("MJDREFI", 58484, "F-05"),   # v1's default — a ~49-year error
        ("MJDREFF", 1, "F-05"),
        ("TIMESYS", "TT", "F-05"),
        ("TIMEUNIT", "d", "F-05"),
        ("TIMZERO", 100, "F-05"),
        ("TIMEDEL", 2, "F-05"),
        ("HDUCLAS1", "SPECTRUM", "F-07"),
        ("HDUCLAS2", "NET", "F-07"),
        ("HDUCLAS3", "RATE", "F-07"),
    ],
)
def test_a_wrong_declaration_fails_loud(tmp_path, key, value, rule):
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, rate_overrides={key: value})
    assert violation(caught).startswith(rule)


@pytest.mark.parametrize("key", ["MJDREFI", "TIMESYS", "TIMEUNIT", "TSTART", "NUMBAND"])
def test_an_absent_keyword_is_never_defaulted(tmp_path, key):
    """§5's opening rule: `header.get(K, default)` is banned for any meaningful key.

    v1 defaulted MJDREF and produced a ~49-year timestamp error that nothing detected.
    """
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, rate_overrides={key: None})
    assert "F-05" in violation(caught)


def test_the_hdu_is_found_by_name_not_by_index(tmp_path):
    """F-02: HDU order is not a contract."""
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, extname="LIGHTCURVE")
    assert violation(caught).startswith("F-02")
    assert "RATE" in violation(caught)


def test_a_truncated_product_is_not_parsed_as_a_whole_day(tmp_path):
    """F-17: NAXIS2 must be 86400 for a SoLEXS daily product."""
    with pytest.raises(ContractViolation) as caught:
        lc.parse(fx.write_lc(fx.sdd2(tmp_path) / "d.lc", rows=86_399,
                             rate_overrides={"NAXIS2": 86_399}), DIGEST)
    assert violation(caught).startswith("F-17")


def test_a_full_day_of_rows_is_accepted(tmp_path):
    """The positive case for F-17, so the check is not simply always-failing."""
    product = parsed_lc(tmp_path)
    assert product.header.rows == lc.EXPECTED_ROWS == 86_400


def test_a_nan_timestamp_is_rejected_before_monotonicity_is_tested(tmp_path):
    """F-16, and §2.1's stated reason: every comparison against NaN is False, so a NaN
    timestamp would defeat the monotonicity test silently."""
    times = [fx.FLARE_DAY_TSTART + i for i in range(86_400)]
    times[7] = math.nan
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, times=times)
    assert violation(caught).startswith("F-16")
    assert "not finite" in violation(caught)


@pytest.mark.parametrize("mutation", ["duplicate", "backwards", "gap"])
def test_a_broken_time_axis_is_rejected(tmp_path, mutation):
    """F-16: Δ must be exactly 1 s. A gap is not repaired — §2.1 declares TIMEDEL=1."""
    times = [fx.FLARE_DAY_TSTART + i for i in range(86_400)]
    if mutation == "duplicate":
        times[10] = times[9]
    elif mutation == "backwards":
        times[10] = times[9] - 5
    else:
        times[10] = times[9] + 4
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, times=times)
    assert violation(caught).startswith("F-16")


def test_tstart_must_equal_the_first_timestamp(tmp_path):
    """F-06: a header and its data disagreeing about when the day began is an ambiguous time."""
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, rate_overrides={"TSTART": fx.FLARE_DAY_TSTART + 1})
    assert violation(caught).startswith("F-06")


def test_a_negative_count_is_physically_impossible(tmp_path):
    """F-19."""
    counts = [10.0] * 86_400
    counts[3] = -1.0
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, counts=counts)
    assert violation(caught).startswith("F-19")


def test_the_negative_count_check_is_nan_safe(tmp_path):
    """§2.1: F-19 is inherently NaN-safe because `NaN < 0` is False.

    Asserted because the ordering of the two branches is what makes it so: if the sign check
    ran before the NaN branch it would still pass, but for the wrong reason.
    """
    counts = [10.0] * 86_400
    counts[3] = math.nan
    product = parsed_lc(tmp_path, counts=counts)
    assert product.counts[3] is None


def test_a_wrong_instrument_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        parsed_lc(tmp_path, primary_overrides={"INSTRUME": "HEL1OS"})
    assert violation(caught).startswith("F-07")


# ═══════════════════════════════════════════ NO IMPUTATION — the Property column


def test_nan_becomes_absent_and_never_zero(tmp_path):
    """§2.1 r2, binding: NaN is the missing-data sentinel; zero remains a valid count.

    Both directions, in one product: the NaN positions become `None`, the measured zero stays
    `0.0`, and neither becomes the other. Collapsing them is the error that would be
    undetectable in every downstream artifact.
    """
    counts = fx.nan_at(86_400, (0, 5, 30))
    product = parsed_lc(tmp_path, counts=counts)

    assert product.absent_offsets == (0, 5, 30)
    for offset in (0, 5, 30):
        assert product.counts[offset] is None
    assert product.counts[1] == 0.0, "a measured zero must not become absent"
    assert product.counts[1] is not None


def test_no_value_is_invented_at_any_position(tmp_path):
    """Quantified over every position: parsed[i] is None iff the archive held NaN there."""
    counts = fx.nan_at(86_400, (0, 5, 30_072, 30_078, 83_951))
    product = parsed_lc(tmp_path, counts=counts)

    assert len(product.counts) == len(counts)
    for index, (raw, parsed) in enumerate(zip(counts, product.counts)):
        if math.isnan(raw):
            assert parsed is None, f"position {index}: NaN was imputed to {parsed!r}"
        else:
            assert parsed == raw, f"position {index}: {raw!r} became {parsed!r}"


def test_absent_seconds_are_never_removed(tmp_path):
    """§2.1: NaN values are never removed. The row count is preserved exactly."""
    counts = fx.nan_at(86_400, fx.ABSENT_OFFSETS)
    product = parsed_lc(tmp_path, counts=counts)

    # §2.1 `OBSERVED` on 2024-05-14 SDD2: 86,395 finite, 5 absent, at these exact offsets.
    assert len(product.counts) == 86_400
    assert product.absent_offsets == fx.ABSENT_OFFSETS
    assert product.n_absent == 5
    assert product.n_finite == 86_395
    assert product.n_finite + product.n_absent == 86_400


def test_absence_survives_into_the_observation(tmp_path):
    """The domain's `None` means observed-to-be-absent (ADR-0017, L-07) — the same meaning.

    The mapping is checked at the boundary where it would be easiest to lose: a generator
    that filtered or filled would produce a shorter or a different sequence.
    """
    counts = fx.nan_at(86_400, (0, 5, 30))
    product = parsed_lc(tmp_path, counts=counts)
    observations = list(product.observations(source_id=SOURCE, ingest_time=None))

    assert len(observations) == 86_400
    assert [o.value for o in observations][:6] == [None, 0.0, 2.0, 3.0, 4.0, None]
    assert observations[0].value_is_absent
    assert not observations[1].value_is_absent
    assert observations[0].quality_flags == ("no_data",)
    assert observations[1].quality_flags == ()


def test_no_interpolation_smoothing_or_repair_function_exists():
    """The prohibition enforced by absence rather than by comment.

    A module that *can* interpolate will interpolate. Nothing in these parsers can.
    """
    for module in (lc, pi, gti):
        names = {name.lower() for name in dir(module)}
        for forbidden in ("interpolate", "interp", "smooth", "fillna", "fill",
                          "impute", "resample", "repair", "ffill", "bfill"):
            assert not any(forbidden in name for name in names), (
                f"{module.__name__} exposes {forbidden!r}"
            )


# ═══════════════════════════════════════════════════ §2.3 — .gti per-field


def test_the_interval_convention_is_inclusive(tmp_path):
    """§2.3 r1: live_time = STOP − START + 1.

    The amendment's whole content. Under the exclusive reading a 59-second interval would
    measure 58 s and the F-09 equality could never hold.
    """
    product = parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59)], exposure="59.0")
    assert product.intervals[0].live_time == 59.0
    assert product.live_time == 59.0


def test_the_exposure_equality_is_exact(tmp_path):
    """F-09, tolerance 0 s. §5: the relation is definitional and a tolerance would re-admit
    the ambiguity that produced CONTRADICTION-001."""
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59)], exposure="59.5")
    assert violation(caught).startswith("F-09")
    assert "tolerance 0" in violation(caught)


def test_even_a_one_second_discrepancy_is_fatal(tmp_path):
    """The exclusive reading, off by exactly the number of intervals. Not tolerated."""
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59)], exposure="58.0")
    assert violation(caught).startswith("F-09")


def test_exposure_is_read_as_the_string_the_archive_stores(tmp_path):
    """§2.3: HDU1 EXPOSURE is a string ('86395.0'). Converted explicitly, never coerced."""
    product = parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59)], exposure="59.0")
    assert product.declared_exposure == 59.0


def test_an_unconvertible_exposure_fails_rather_than_falling_back(tmp_path):
    """A computed fallback would make F-09 compare a number against itself."""
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59)], exposure="unknown")
    assert violation(caught).startswith("F-09")


def test_an_empty_gti_is_legal_and_marks_the_detector_inactive(tmp_path):
    """F-12 — the single deliberate non-terminating rule. §1.1 records SDD1 at zero rows."""
    path = fx.write_gti(fx.sdd1(tmp_path) / "x.gti", intervals=[], exposure="0.0")
    product = gti.parse(path, DIGEST)
    assert product.detector_active is False
    assert product.intervals == ()
    assert product.declared_exposure is None
    assert product.detector == "SDD1"


def test_overlapping_intervals_are_refused(tmp_path):
    """Overlap would double-count live time."""
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 59),
                                  (fx.FLARE_DAY_TSTART + 50, fx.FLARE_DAY_TSTART + 99)])
    assert violation(caught).startswith("F-09")


def test_an_inverted_interval_is_refused(tmp_path):
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART + 59, fx.FLARE_DAY_TSTART + 1)])
    assert violation(caught).startswith("F-09")


def test_an_interval_outside_the_declared_day_is_refused(tmp_path):
    """§2.3: all intervals within [OBS_DATE 00:00, 23:59:59]."""
    with pytest.raises(ContractViolation) as caught:
        parsed_gti(tmp_path, intervals=[(fx.FLARE_DAY_TSTART - 100, fx.FLARE_DAY_TSTART - 41)])
    assert violation(caught).startswith("F-09")


def test_the_detector_comes_from_the_path_because_gti_carries_no_filter(tmp_path):
    """Read from the directory §1.1 places the product in, and failed on rather than guessed."""
    assert parsed_gti(tmp_path).detector == "SDD2"
    stray = tmp_path / "nowhere" / "x.gti"
    fx.write_gti(stray)
    with pytest.raises(ContractViolation) as caught:
        gti.parse(stray, DIGEST)
    assert violation(caught).startswith("F-18")


def test_excluded_seconds_are_reported_for_the_day_assembly_layer(tmp_path):
    """§2.1 places `NaN ⇒ GTI-excluded` at day assembly (#19), which needs this."""
    product = parsed_gti(
        tmp_path,
        intervals=[(fx.FLARE_DAY_TSTART + 1, fx.FLARE_DAY_TSTART + 4),
                   (fx.FLARE_DAY_TSTART + 6, fx.FLARE_DAY_TSTART + 59)],
        exposure="58.0",
    )
    assert product.excluded_seconds(fx.FLARE_DAY_TSTART, 60) == (0, 5)


def test_interval_coverage_is_inclusive_at_both_ends(tmp_path):
    interval = gti.Interval(1000.0, 1058.0)
    assert interval.covers(1000.0) and interval.covers(1058.0)
    assert not interval.covers(999.0) and not interval.covers(1059.0)


# ═══════════════════════════════════════════════════ §2.2 — .pi per-field


def test_the_spectra_product_declares_ogip_type_ii_pha(full_day_pi):
    product = full_day_pi
    assert product.header.detchans == pi.DETCHANS == 340
    assert product.header.chantype == "PI"
    assert product.header.poisserr is False
    assert product.header.areascal == 1.0
    assert product.header.corrscal == 1.0


def test_the_channel_map_is_constant_and_kept_once(full_day_pi):
    """§2.2: CHANNEL is 235 MB/day of pure redundancy — read once, validate, discard."""
    product = full_day_pi
    assert product.channel_map == tuple(range(340))
    assert len(product.channel_map) == 340


def test_a_varying_channel_map_voids_the_assumption_and_fails(tmp_path):
    """F-08: a channel index must mean the same thing in every row."""
    varying = [list(range(340))] * 59 + [list(range(1, 341))]  # short: F-08 precedes F-17
    with pytest.raises(ContractViolation) as caught:
        parsed_pi(tmp_path, channel_map=varying)
    assert violation(caught).startswith("F-08")


@pytest.mark.parametrize("detchans", [341, 511, 339])
def test_a_different_channel_count_is_a_different_channel_space(tmp_path, detchans):
    """F-11: SoLEXS PI(340), HEL1OS CZT PHA(341) and CdTe PHA(511) are incommensurable.

    341 and 511 are chosen deliberately — they are the two spaces F-11 names.
    """
    with pytest.raises(ContractViolation) as caught:
        parsed_pi(tmp_path, detchans=detchans)
    assert violation(caught).startswith("F-11")


def test_a_wrong_chantype_is_refused(tmp_path):
    """PI is gain-corrected pulse-invariant; PHA is not the same space."""
    with pytest.raises(ContractViolation) as caught:
        parsed_pi(tmp_path, spectrum_overrides={"CHANTYPE": "PHA"})
    assert violation(caught).startswith("F-07")


def test_the_spectra_stream_rather_than_materialise(full_day_pi):
    """§2.2 is design-binding: ~472 MB/day decompressed; a day must not be held."""
    import inspect

    assert inspect.isgeneratorfunction(pi.Spectra.spectra)
    first = next(iter(full_day_pi.spectra()))
    assert len(first.counts) == 340
    assert first.valid_time == Timestamp("2024-05-14T00:00:00Z")


def test_every_spectrum_carries_its_second(full_day_pi):
    seconds = []
    for index, spectrum in enumerate(full_day_pi.spectra()):
        seconds.append(spectrum.tstart)
        if index == 4:
            break
    assert seconds == [fx.FLARE_DAY_TSTART + i for i in range(5)]


def test_a_negative_spectral_count_is_refused(tmp_path):
    counts = np.tile(np.arange(340, dtype=float), (86_400, 1))
    counts[4][17] = -1.0
    with pytest.raises(ContractViolation) as caught:
        list(parsed_pi(tmp_path, rows=86_400, counts=counts).spectra())
    assert violation(caught).startswith("F-19")


def test_a_negative_exposure_is_refused(tmp_path):
    exposures = [1.0] * 86_400
    exposures[9] = -1.0
    with pytest.raises(ContractViolation) as caught:
        parsed_pi(tmp_path, rows=86_400, exposures=exposures)
    assert violation(caught).startswith("F-19")


def test_the_pi_epoch_must_agree_with_the_lightcurve(tmp_path, full_day_pi):
    """V-PI-3 / F-06: `.pi TSTART[0]` must equal the `.lc` TSTART for the same day."""
    curve = parsed_lc(tmp_path)
    pi.check_epoch_agrees_with_lightcurve(full_day_pi, curve)

    shifted = parsed_lc(tmp_path, tstart=fx.FLARE_DAY_TSTART + 1)
    with pytest.raises(ContractViolation) as caught:
        pi.check_epoch_agrees_with_lightcurve(full_day_pi, shifted)
    assert violation(caught).startswith("F-06")


# ═══════════════════════════════════════════ §2.2 — the keV prohibition


def test_no_energy_is_stated_anywhere():
    """§2.2, binding: no v2 artifact may state a SoLEXS energy in keV.

    No RMF/ARF exists anywhere in the archive, so PI-channel → keV is impossible from archive
    contents alone. Channels are ordinal indices. Enforced by absence: there is no field, no
    function and no constant to state an energy with.
    """
    for holder in (pi, pi.Spectra, pi.Spectrum, pi.SpectraHeader):
        names = {name.lower() for name in dir(holder)}
        for forbidden in ("kev", "energy", "rmf", "arf", "response", "calibrat"):
            assert not any(forbidden in name for name in names), (
                f"{getattr(holder, '__name__', holder)} exposes {forbidden!r}; §2.2 forbids "
                f"stating a SoLEXS energy until a response file is acquired"
            )

    source = Path(pi.__file__).read_text().lower()
    assert "def to_kev" not in source
    assert "channel_energy" not in source


def test_the_channel_map_is_ordinal_not_physical(full_day_pi):
    """The channel vector is 0..339 — indices, carrying no physical meaning by themselves."""
    product = full_day_pi
    assert product.channel_map[0] == 0
    assert product.channel_map[-1] == 339
    assert all(isinstance(c, int) for c in product.channel_map)


# ═══════════════════════════════════════════ provenance and the clock


def test_every_product_carries_the_digest_of_the_bytes_it_came_from(tmp_path, full_day_pi):
    """Every Observation must be traceable to the original acquired artifact (ADR-0005)."""
    assert parsed_lc(tmp_path).source_digest == DIGEST
    assert parsed_gti(tmp_path).source_digest == DIGEST
    assert full_day_pi.source_digest == DIGEST


def test_the_observation_carries_the_source_digest(tmp_path):
    product = parsed_lc(tmp_path)
    for observation in product.observations(source_id=SOURCE, ingest_time=None):
        assert observation.source_digest == DIGEST
        break


def test_no_parser_reads_a_clock():
    """TIS §0.4: `ingest_time` is stamped at the acquisition boundary and nowhere else."""
    for module in (lc, pi, gti):
        source = Path(module.__file__).read_text()
        for forbidden in ("datetime.now", "utcnow", "time.time", "stamp()"):
            assert forbidden not in source, f"{module.__name__} reads a clock via {forbidden}"


def test_the_ingest_time_is_supplied_not_invented(tmp_path):
    """The parser propagates what the acquisition stamped, including a legitimate None."""
    product = parsed_lc(tmp_path)
    stamped = Timestamp("2024-06-16T09:00:00Z")

    with_time = next(iter(product.observations(source_id=SOURCE, ingest_time=stamped)))
    without = next(iter(product.observations(source_id=SOURCE, ingest_time=None)))
    assert with_time.ingest_time == stamped
    assert without.ingest_time is None


def test_a_gzipped_product_parses_identically(tmp_path):
    """The archive ships `.gz`; the fixtures above are uncompressed for speed.

    This is the one place the two are compared, so the shortcut is proved harmless rather
    than assumed to be: the same bytes, compressed and not, must parse to the same product.
    """
    import gzip
    import shutil

    plain = fx.write_lc(fx.sdd2(tmp_path) / "plain.lc", rows=86_400)
    zipped = plain.with_suffix(".lc.gz")
    with open(plain, "rb") as raw, gzip.open(zipped, "wb") as out:
        shutil.copyfileobj(raw, out)

    from_plain = lc.parse(plain, DIGEST)
    from_gzip = lc.parse(zipped, DIGEST)
    assert from_plain.counts == from_gzip.counts
    assert from_plain.times == from_gzip.times
    assert from_plain.header == from_gzip.header

"""Unit tests for the value objects.

No fixtures, no mocks (TIS E4 §16). Every value here is constructed from literals, which is
possible only because the package is pure — and is the practical demonstration that it is.
"""

from __future__ import annotations

import pytest

from domain.errors import ContractViolation, DomainError
from domain.values import (
    Digest,
    Identifier,
    Interval,
    ReproductionClass,
    RunId,
    Score,
    Severity,
    SplitStrategy,
    Timestamp,
)
from domain.values.numeric import finite

VALID_HEX = "a" * 64
OTHER_HEX = "b" * 64
VALID_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


# --------------------------------------------------------------------------- ContractViolation


def test_contract_violation_carries_a_json_pointer():
    """TIS E4 §15: the violation names the failing field in the schema's own address space."""
    error = ContractViolation("/ingest_time", "must be a Timestamp or None")
    assert error.pointer == "/ingest_time"
    assert error.message == "must be a Timestamp or None"
    assert "/ingest_time" in str(error)


def test_contract_violation_on_the_whole_object_renders_a_root_pointer():
    """An empty pointer means the object, not a missing pointer."""
    assert str(ContractViolation("", "interval lower exceeds upper")).startswith("/:")


def test_contract_violation_is_catchable_without_a_bare_except():
    """TIS §0.2 forbids bare `except`, so the hierarchy has to make a narrow catch possible."""
    with pytest.raises(DomainError):
        Digest("nope")


# --------------------------------------------------------------------------- Digest


def test_digest_accepts_64_lower_case_hex():
    assert Digest(VALID_HEX).hex == VALID_HEX
    assert str(Digest(VALID_HEX)) == VALID_HEX


@pytest.mark.parametrize(
    "bad, why",
    [
        ("a" * 63, "one short"),
        ("a" * 65, "one long"),
        ("", "empty"),
        ("A" * 64, "upper case"),
        ("g" * 64, "not hexadecimal"),
        ("a" * 62 + "!!", "punctuation"),
        (" " + "a" * 63, "leading space"),
    ],
)
def test_digest_rejects_anything_that_is_not_a_sha256(bad, why):
    with pytest.raises(ContractViolation):
        Digest(bad)


def test_digest_rejects_non_strings():
    for bad in (None, 42, b"a" * 64, ["a" * 64]):
        with pytest.raises(ContractViolation):
            Digest(bad)


def test_digest_does_not_lower_case_upper_hex():
    """STD-13 forbids coercion. Two spellings of one digest must not silently become one."""
    with pytest.raises(ContractViolation) as caught:
        Digest("A" * 64)
    assert "lower-case" in caught.value.message


def test_digest_is_frozen_hashable_and_ordered():
    a, b = Digest(VALID_HEX), Digest(OTHER_HEX)
    assert a < b
    assert {a, b, Digest(VALID_HEX)} == {a, b}
    assert sorted([b, a]) == [a, b]
    with pytest.raises(Exception):
        a.hex = OTHER_HEX  # type: ignore[misc]


def test_digest_short_is_twelve_characters_for_logs_only():
    assert Digest(VALID_HEX).short == "a" * 12


def test_digest_cannot_mint_one():
    """ADR-0005: the kernel is the only minting authority, and ADR-0026 bars importing it.

    The absence of a hashing constructor is a decision, not an oversight — `hashlib` is
    standard library and would import cleanly here. This asserts the decision holds.
    """
    import domain.values.digest as module

    assert not hasattr(Digest, "of_bytes")
    assert not hasattr(Digest, "compute")
    assert not hasattr(module, "sha256")
    assert "hashlib" not in module.__dict__


# --------------------------------------------------------------------------- Identifier / RunId


def test_identifier_accepts_the_contract_shape():
    for good in ("goes", "aditya-l1", "solexs_1", "x", "a0"):
        assert str(Identifier(good)) == good


@pytest.mark.parametrize(
    "bad",
    ["", "-leading", "_leading", "Upper", "has space", "dot.sep", "sla/sh", "é", "9" * 65],
)
def test_identifier_rejects_malformed_names(bad):
    with pytest.raises(ContractViolation):
        Identifier(bad)


def test_identifier_rejects_a_digest_shaped_string_only_by_length():
    """A 64-character lower-case hex string is a legal identifier body but exceeds the limit.

    Recorded because it is the near miss: the two types are distinguishable in a signature,
    and this shows the boundary is length rather than alphabet.
    """
    assert len(VALID_HEX) == 64
    assert Identifier(VALID_HEX).value == VALID_HEX
    with pytest.raises(ContractViolation):
        Identifier("a" * 65)


def test_run_id_accepts_crockford_base32():
    assert str(RunId(VALID_ULID)) == VALID_ULID


@pytest.mark.parametrize("bad", ["", "SHORT", VALID_ULID + "X", VALID_ULID.lower()])
def test_run_id_rejects_wrong_length_or_case(bad):
    with pytest.raises(ContractViolation):
        RunId(bad)


@pytest.mark.parametrize("excluded", ["I", "L", "O", "U"])
def test_run_id_rejects_the_four_ambiguous_letters(excluded):
    """Crockford excludes I, L, O and U so a transcribed id cannot be misread."""
    with pytest.raises(ContractViolation):
        RunId(excluded + VALID_ULID[1:])


# --------------------------------------------------------------------------- Timestamp


def test_timestamp_accepts_rfc3339_with_an_explicit_offset():
    for good in (
        "2024-01-01T00:00:00Z",
        "2024-01-01T00:00:00.123456Z",
        "2024-06-30T23:59:59+05:30",
        "2024-06-30T23:59:59-08:00",
    ):
        assert str(Timestamp(good)) == good


@pytest.mark.parametrize(
    "bad, why",
    [
        ("2024-01-01T00:00:00", "no offset — the moment is ambiguous"),
        ("2024-01-01 00:00:00Z", "space instead of T"),
        ("2024-01-01", "date only"),
        ("", "empty"),
        ("not a time", "prose"),
        ("2024-13-01T00:00:00Z", "month 13 — matches the pattern, fails the calendar"),
        ("2024-01-32T00:00:00Z", "day 32 — matches the pattern, fails the calendar"),
    ],
)
def test_timestamp_rejects_malformed_and_impossible_instants(bad, why):
    with pytest.raises(ContractViolation):
        Timestamp(bad)


def test_timestamp_preserves_its_original_text():
    """Re-emitting a normalised form would silently rewrite a recorded value."""
    original = "2024-06-30T23:59:59+05:30"
    assert Timestamp(original).text == original


def test_timestamp_compares_by_instant_not_by_spelling():
    assert Timestamp("2024-01-01T00:00:00Z") == Timestamp("2024-01-01T01:00:00+01:00")
    assert Timestamp("2024-01-01T00:00:00Z") < Timestamp("2024-01-01T00:00:01Z")


def test_timestamp_has_no_clock_reader():
    """TIS §0.4: no context may read wall-clock time. The absence is the enforcement."""
    import domain.values.timestamp as module

    assert not hasattr(Timestamp, "now")
    assert not hasattr(Timestamp, "utcnow")
    assert not hasattr(module, "time")


def test_timestamp_knows_whether_it_is_utc():
    assert Timestamp("2024-01-01T00:00:00Z").is_utc
    assert not Timestamp("2024-01-01T00:00:00+05:30").is_utc


# --------------------------------------------------------------------------- numeric


@pytest.mark.parametrize("bad", [True, False, "1", None, [1]])
def test_finite_rejects_non_numbers_including_bool(bad):
    """`isinstance(True, int)` is true in Python; a score of `True` must not pass."""
    with pytest.raises(ContractViolation):
        finite(bad, "/x", "x")


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_finite_rejects_nan_and_infinity(bad):
    """JSON has no literal for either, so a value that cannot serialise is not admitted."""
    with pytest.raises(ContractViolation):
        finite(bad, "/x", "x")


def test_finite_returns_a_float_for_an_int():
    assert finite(3, "/x", "x") == 3.0


# --------------------------------------------------------------------------- Interval / Score


def interval(**overrides) -> Interval:
    """A literal constructor, not a fixture. Overrides make each test's variable explicit."""
    fields = {
        "lower": 0.80,
        "upper": 0.90,
        "level": 0.95,
        "estimator": "bootstrap",
        "exchangeable_unit": "event",
    }
    fields.update(overrides)
    return Interval(**fields)


def test_interval_accepts_a_wellformed_interval():
    assert interval().width == pytest.approx(0.10)


def test_interval_rejects_inverted_bounds():
    with pytest.raises(ContractViolation) as caught:
        interval(lower=0.9, upper=0.8)
    assert "exceeds" in caught.value.message


def test_interval_accepts_a_degenerate_interval():
    """lower == upper is a zero-width interval, which is a legitimate exact result."""
    assert interval(lower=0.5, upper=0.5).width == 0


@pytest.mark.parametrize("bad_level", [0, 1, -0.1, 1.5])
def test_interval_rejects_levels_outside_the_open_unit_interval(bad_level):
    with pytest.raises(ContractViolation):
        interval(level=bad_level)


def test_interval_requires_a_named_estimator():
    with pytest.raises(ContractViolation) as caught:
        interval(estimator="")
    assert "uninterpretable" in caught.value.message


def test_interval_requires_the_exchangeable_unit():
    """L-01: flares span many minutes, so the row count is not the sample size."""
    with pytest.raises(ContractViolation) as caught:
        interval(exchangeable_unit="")
    assert "L-01" in caught.value.message


def test_interval_contains_is_inclusive_of_both_bounds():
    bounds = interval()
    assert bounds.contains(0.80) and bounds.contains(0.90) and bounds.contains(0.85)
    assert not bounds.contains(0.79) and not bounds.contains(0.91)


def test_interval_round_trips():
    assert Interval.from_dict(interval().to_dict()) == interval()


def test_score_requires_an_interval():
    """STD-05: a bare number in a publication is the failure this platform refuses."""
    with pytest.raises(ContractViolation) as caught:
        Score(metric="tss", value=0.85, interval=None, denominator=10)  # type: ignore[arg-type]
    assert "STD-05" in caught.value.message


def test_score_requires_a_named_metric():
    with pytest.raises(ContractViolation):
        Score(metric="", value=0.85, interval=interval(), denominator=10)


@pytest.mark.parametrize("bad", [0, -1])
def test_score_requires_a_denominator_of_at_least_one(bad):
    """A rate without its denominator cannot be weighed against another rate."""
    with pytest.raises(ContractViolation):
        Score(metric="tss", value=0.85, interval=interval(), denominator=bad)


def test_score_rejects_a_boolean_denominator():
    with pytest.raises(ContractViolation):
        Score(metric="tss", value=0.85, interval=interval(), denominator=True)


def test_score_round_trips():
    score = Score(metric="tss", value=0.85, interval=interval(), denominator=192541)
    assert Score.from_dict(score.to_dict()) == score


# --------------------------------------------------------------------------- enums


def test_reproduction_class_has_exactly_the_three_members_adr_0021_defines():
    assert [c.value for c in ReproductionClass] == ["EXACT", "EQUIVALENT", "UNREPRODUCIBLE"]


def test_severity_has_exactly_the_three_members_adr_0024_defines():
    assert [s.value for s in Severity] == ["CORRECTION", "RETRACTION", "DEPRECATION"]


def test_split_strategy_admits_only_chronological():
    """A shuffled split would let a future minute inform a past one."""
    assert [s.value for s in SplitStrategy] == ["chronological"]


@pytest.mark.parametrize("enum", [ReproductionClass, Severity, SplitStrategy])
def test_enums_reject_unknown_members(enum):
    with pytest.raises(ValueError):
        enum("SOMETHING_ELSE")

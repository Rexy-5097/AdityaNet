"""Closed vocabularies.

Each of these is an enumeration in a contract, and each is closed for the same reason the
objects are: a member added by one producer and unknown to a consumer is a disagreement both
parties believe is agreement. `str` mixin so a member serialises as its own name without a
conversion step that could be forgotten.
"""

from __future__ import annotations

from enum import Enum


class ReproductionClass(str, Enum):
    """What an Evaluation's result can be claimed to guarantee (ADR-0021, STD-21).

    The three members are not a quality ranking. They are three different statements about
    what was pinned, and the third is a refusal to publish rather than a weak result.
    """

    #: Five inputs and platform match. Guarantee: bit-identical scores.
    EXACT = "EXACT"
    #: Five inputs match, platform differs. Guarantee: agreement within the Protocol's
    #: declared tolerance. Cross-architecture bit-identity is not claimed, because it is
    #: not true.
    EQUIVALENT = "EQUIVALENT"
    #: Any input unpinned. May not be published (ADR-0021).
    UNREPRODUCIBLE = "UNREPRODUCIBLE"


class Severity(str, Enum):
    """How badly a superseded release is affected (ADR-0024)."""

    #: Wrong but recoverable.
    CORRECTION = "CORRECTION"
    #: Scientifically invalid. A retraction anywhere in a Claim's provenance DAG fails the
    #: build (STD-22).
    RETRACTION = "RETRACTION"
    #: Superseded, not wrong.
    DEPRECATION = "DEPRECATION"


class SplitStrategy(str, Enum):
    """How a Protocol divides time.

    One member, deliberately. STD-11 requires two instances before an abstraction, and this
    is not an abstraction — it is a closed set that currently has one legal value. A shuffled
    split would let a future minute inform a past one, so the enumeration exists to make
    adding one a contract change rather than a parameter change.
    """

    CHRONOLOGICAL = "chronological"

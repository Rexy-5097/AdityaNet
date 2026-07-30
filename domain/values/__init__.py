"""Value objects: defined wholly by their attributes, compared by value, never mutated.

Every type here is frozen and validates in `__post_init__`, so an invalid value cannot exist
even briefly. That matters more than it sounds: a type that can be constructed invalid and
checked later has a window in which invalid data is indistinguishable from valid data, and
the check becomes something a caller can forget.
"""

from domain.values.digest import HEX_LENGTH, Digest
from domain.values.enums import ReproductionClass, Severity, SplitStrategy
from domain.values.identifier import (
    MAX_IDENTIFIER_LENGTH,
    RUN_ID_LENGTH,
    Identifier,
    RunId,
)
from domain.values.score import Interval, Score
from domain.values.timestamp import PATTERN, Timestamp

__all__ = [
    "Digest",
    "HEX_LENGTH",
    "Identifier",
    "Interval",
    "MAX_IDENTIFIER_LENGTH",
    "PATTERN",
    "RUN_ID_LENGTH",
    "ReproductionClass",
    "RunId",
    "Score",
    "Severity",
    "SplitStrategy",
    "Timestamp",
]

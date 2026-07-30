"""Numeric admission.

One function, used by every entity or value that holds a real number. It lives on its own
rather than inside the first module that needed it because three call sites now import it
(`Score`, `Interval`, `Observation`), and reaching into another module's private helper is
how a private helper quietly becomes public without anyone deciding it should be.
"""

from __future__ import annotations

import math

from domain.errors import ContractViolation


def finite(value: object, pointer: str, label: str) -> float:
    """Accept a real number; reject `bool`, NaN and infinity.

    `bool` is excluded explicitly because `isinstance(True, int)` is true in Python. A score
    of `True` would pass a naive numeric check and serialise as `true`.

    NaN and infinity are rejected because JSON has no literal for either. `json.dumps` emits
    the non-standard `NaN` and `Infinity` tokens by default and many parsers refuse them, so
    a value that cannot survive serialisation is not admitted in the first place. Silently
    substituting `null` instead would be imputation, which ADR-0017 forbids.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolation(
            pointer, f"{label} must be a number, got {type(value).__name__}"
        )
    if not math.isfinite(value):
        raise ContractViolation(pointer, f"{label} must be finite, got {value}")
    return float(value)

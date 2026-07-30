"""`Timestamp` — an RFC 3339 instant, parsed but never read from a clock.

Matches `common.schema.json#/$defs/timestamp` character for character. The schema declares
both `format: date-time` and a `pattern` because `format` is annotation-only in JSON Schema
and is not enforced unless a validator is explicitly configured with a format checker; the
pattern is what every validator actually applies. This type enforces the same shape, so a
string a validator would reject cannot enter the domain by the Python door instead.

NO CLOCK READ (TIS §0.4)
-----------------------
There is deliberately no `Timestamp.now()`. Determinism here is enforced by a pinned input
rather than by discipline, and no context may read wall-clock time except `ingest_time`
capture at E5's acquisition boundary — which is E5's to perform and to pass in, not the
domain's to reach for. A `now()` on this type would be available to every caller; its absence
is what makes the rule structural rather than advisory.

Comparison is by the parsed instant, so two spellings of the same moment under different
offsets compare equal. The original text is preserved verbatim for serialisation: re-emitting
a normalised form would silently rewrite a recorded value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from domain.errors import ContractViolation

# Identical to the contract's pattern.
PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
_RFC3339 = re.compile(PATTERN)


@dataclass(frozen=True, order=True)
class Timestamp:
    """An instant on the timeline, in RFC 3339 form with an explicit offset."""

    #: Original text. Excluded from comparison so ordering is by moment, not by spelling.
    text: str = field(compare=False)
    #: Parsed instant, derived. Compared, so `2024-01-01T00:00:00Z` equals
    #: `2024-01-01T01:00:00+01:00` — the same moment written two ways.
    instant: datetime = field(init=False, compare=True, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise ContractViolation(
                "", f"timestamp must be a string, got {type(self.text).__name__}"
            )
        if _RFC3339.match(self.text) is None:
            raise ContractViolation(
                "", f"timestamp {self.text!r} is not RFC 3339 with an explicit offset"
            )
        try:
            parsed = datetime.fromisoformat(self.text.replace("Z", "+00:00"))
        except ValueError as exc:
            # The pattern admits shapes the calendar does not — month 13, a 32nd day. The
            # parser is the only place those are caught, and rejection is the only permitted
            # response: STD-13 forbids clamping to a nearby valid date.
            raise ContractViolation(
                "", f"timestamp {self.text!r} is not a real instant: {exc}"
            ) from exc
        object.__setattr__(self, "instant", parsed)

    @property
    def is_utc(self) -> bool:
        return self.instant.utcoffset() == timezone.utc.utcoffset(None)

    def __str__(self) -> str:
        return self.text

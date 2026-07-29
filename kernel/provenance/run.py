"""Run — one execution of any process.

WHY A RUN READS THE CLOCK, AND WHY THAT DOES NOT BREAK DETERMINISM.

TIS §0.4 forbids reading wall-clock time inside a context, so that scientific computation is
reproducible. A Run is not scientific computation: it is operational metadata about an
execution, and it is deliberately NOT one of the five pinned inputs that determine an
Evaluation's identity (ADR-0021). Two runs of the same evaluation produce different run_ids
and identical scores. The clock read is therefore outside the property §0.4 protects, and
the tests assert the boundary — uniqueness and ordering, never a specific timestamp.

IDENTIFIER. TIS Part 1 specifies a ULID: a 48-bit millisecond timestamp followed by 80 bits
of randomness, Crockford Base32, 26 characters. It sorts lexicographically in time order,
which makes a directory listing of runs chronological without parsing anything. Implemented
here rather than taken as a dependency, because this package may not import third-party code
(TIS E3 §11).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from enum import Enum

from kernel.provenance.errors import ProvenanceFailure

# Crockford Base32: no I, L, O or U, so that a transcribed identifier cannot be misread.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_LENGTH = 26
_TIMESTAMP_BITS = 48
_RANDOM_BITS = 80

# ULID monotonicity state. Two identifiers minted in the same millisecond must still sort in
# creation order, so the random component is incremented rather than redrawn.
_last_ms = -1
_last_random = 0


class RunStatus(Enum):
    """A Run is started, then ended exactly once. There is no third state and no way back."""

    STARTED = "started"
    OK = "ok"
    FAILED = "failed"


def _encode(value: int) -> str:
    """Encode 128 bits as 26 Crockford Base32 characters, most significant first."""
    chars = []
    for _ in range(_ULID_LENGTH):
        chars.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def new_run_id() -> str:
    """Mint a ULID that is unique and monotonically increasing within this process."""
    global _last_ms, _last_random

    now_ms = int(time.time() * 1000)
    if now_ms == _last_ms:
        # Same millisecond: increment rather than redraw, so ordering is preserved.
        _last_random += 1
        if _last_random >= (1 << _RANDOM_BITS):
            raise ProvenanceFailure("ULID randomness exhausted within one millisecond")
    else:
        _last_ms = max(now_ms, _last_ms)
        _last_random = int.from_bytes(os.urandom(_RANDOM_BITS // 8), "big")

    return _encode((_last_ms << _RANDOM_BITS) | _last_random)


@dataclass(frozen=True)
class Run:
    """Immutable. `end` returns a new Run rather than mutating this one."""

    run_id: str
    context: str
    event: str
    status: RunStatus
    started_ms: int
    ended_ms: int | None = None

    def __post_init__(self) -> None:
        if len(self.run_id) != _ULID_LENGTH:
            raise ValueError(f"run_id must be {_ULID_LENGTH} characters")
        if not self.context or not self.event:
            raise ValueError("a Run must name its context and event")

    @property
    def is_terminal(self) -> bool:
        return self.status is not RunStatus.STARTED

    def end(self, status: RunStatus) -> "Run":
        """Transition to a terminal state.

        A terminal Run is immutable (TIS E3 §9). Ending twice is a ProvenanceFailure rather
        than a silent no-op: it means a caller believes it owns a run it does not, and
        allowing it would let two outcomes be recorded for one execution.
        """
        if self.is_terminal:
            raise ProvenanceFailure(
                f"run {self.run_id} already ended with status {self.status.value}"
            )
        if status is RunStatus.STARTED:
            raise ProvenanceFailure("a run cannot end in the started state")
        return replace(self, status=status, ended_ms=int(time.time() * 1000))


def begin_run(context: str, event: str) -> Run:
    """Start a Run. The only entry point that mints a run_id."""
    return Run(
        run_id=new_run_id(),
        context=context,
        event=event,
        status=RunStatus.STARTED,
        started_ms=int(time.time() * 1000),
    )

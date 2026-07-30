"""The acquisition boundary — the single sanctioned clock read in the system.

ADR-0004: *"`ingest_time` is stamped at the acquisition boundary. This is the single
sanctioned clock read in the system; determinism elsewhere is governed by ADR-0021."*
TIS §0.4 states the same rule from the other side: no context may read wall-clock time,
*"Exception: `ingest_time` capture in E5, which is definitionally a clock read at the
acquisition boundary."*

WHY THE EXCEPTION LIVES IN ITS OWN MODULE
------------------------------------------
`domain/values/Timestamp` deliberately has no `now()`, and `test_timestamp_has_no_clock_reader`
(M2/E4/#12) pins that. The domain is pure, so the moment the system learned something cannot
originate there. It has to originate somewhere, and putting it in one named module with one
exported function means the exception is enumerable: `grep -rn 'ingest.boundary' .` finds
every place in the repository that reads a clock.

An exception spread across several call sites is not an exception, it is a convention.

WHAT THIS DOES NOT DO
---------------------
It does not stamp historical data. E5 §11(ii) is unambiguous: *"No code path writes a non-null
`ingest_time` for historical data."* There is no function here that takes a row and supplies a
time for it, and no default. A row that predates bitemporal capture carries `None`, which
ADR-0022 gives exactly one meaning, and the only way to obtain a stamp is to call `stamp()` at
the moment of an actual acquisition. Backfilling would require calling it and then attaching
the result to old rows — which `domain.invariants.ingest_time_is_not_backfilled` detects, and
which no code here makes convenient.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from domain.values import Timestamp


def stamp() -> Timestamp:
    """Read the clock at the acquisition boundary and return the instant as a Timestamp.

    Always UTC with an explicit offset, because a local-time stamp is ambiguous twice a year
    and a naive one is ambiguous always. Microsecond precision is kept: two acquisitions in
    the same second are two acquisitions, and collapsing them to one instant would make an
    ordering question unanswerable later.
    """
    now = datetime.now(timezone.utc)
    return Timestamp(now.isoformat().replace("+00:00", "Z"))


def stamp_from_epoch(seconds: float) -> Timestamp:
    """The same stamp, from a caller-supplied epoch instant.

    Exists for the acquisition path that already has the instant a transfer completed — an
    adapter that records the completion time of a download should record *that* moment, not
    the slightly later moment it got around to calling `stamp()`.

    It is not a way to fabricate a time. It takes a number a caller must already possess, and
    supplying an arbitrary one is indistinguishable from lying about when data arrived —
    which is what the no-backfill invariant checks for, not what a type can prevent.
    """
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError(f"epoch seconds must be a number, got {type(seconds).__name__}")
    moment = datetime.fromtimestamp(float(seconds), tz=timezone.utc)
    return Timestamp(moment.isoformat().replace("+00:00", "Z"))


def monotonic() -> float:
    """A monotonic reading for measuring elapsed time within one acquisition.

    Not a clock in the ADR-0004 sense: it has no epoch, cannot be converted to a Timestamp,
    and cannot be recorded as when anything happened. It exists so an adapter can implement
    the retry and timeout policy E5 §15 makes adapter-local without reaching for
    `time.time()`, which would be a second, unsanctioned wall-clock read.
    """
    return time.monotonic()


__all__ = ["monotonic", "stamp", "stamp_from_epoch"]

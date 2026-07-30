"""Invariants over Observations.

Each predicate here answers a question that a well-typed `Observation` can still get wrong.
Anything a type can enforce is enforced by the type instead — a predicate restating a
constructor check would always be true and would give a property test nothing to find.
"""

from __future__ import annotations

from domain.entities.observation import Observation
from domain.entities.protocol import Protocol
from domain.values.timestamp import Timestamp


def observation_is_wellformed(observation: Observation) -> bool:
    """The predicate TIS E4 §19 names in the epic's example execution flow.

    E5 constructs an Observation, calls this, serialises, and validates against the schema.
    What it checks beyond construction: `valid_time` is present and is a real instant
    (ADR-0004 — when the phenomenon occurred is always known), and `ingest_time` is either a
    real instant or the single permitted null. Crucially it also requires that a *known*
    ingest time is not before the valid time it accompanies: learning of a measurement before
    the measurement occurred is not a late arrival, it is a corrupt record.
    """
    if not isinstance(observation, Observation):
        return False
    if not isinstance(observation.valid_time, Timestamp):
        return False
    if observation.ingest_time is None:
        return True
    return observation.ingest_time.instant >= observation.valid_time.instant


def ingest_time_is_not_backfilled(observation: Observation, frozen_at: Timestamp) -> bool:
    """False where `ingest_time` equals the dataset freeze timestamp (ADR-0022).

    This is not a generic plausibility check. ADR-0022 was written to reject one specific
    proposed migration: backfilling every unknown `ingest_time` with the dataset freeze
    timestamp and "flagging it as imputed". A flag does not convert a fabrication into a
    measurement, and the fabricated value is recognisable precisely because every backfilled
    row would carry the same instant — the freeze.

    An observation genuinely ingested at the freeze instant would fail this check. That is
    the right trade: the freeze is a batch operation over already-acquired data, so a true
    coincidence is vanishingly unlikely, whereas a backfill produces the collision on every
    row. A false positive costs one investigation; a false negative silently launders
    fabricated provenance into the bitemporal record.
    """
    if observation.ingest_time is None:
        return True
    return observation.ingest_time.instant != frozen_at.instant


def observation_is_admissible_under(observation: Observation, protocol: Protocol) -> bool:
    """Whether the Protocol's leakage rule admits this observation (ADR-0022 §2).

    `requires_bitemporal = True` excludes observations whose `ingest_time` is unknown, which
    is what makes the leakage gate enforceable *by construction* rather than by trust: if
    availability cannot be established, the row cannot participate.

    `requires_bitemporal = False` admits them, and the resulting Evaluation must record
    `leakage_gate_applied = False` — see `leakage_gate_is_consistent_with`.
    """
    if protocol.requires_bitemporal:
        return observation.ingest_time is not None
    return True


def absence_survives_serialisation(observation: Observation) -> bool:
    """A null value and a null ingest time survive a round trip unchanged (ADR-0017, STD-04).

    Imputation rarely arrives as a deliberate decision. It arrives as a serialiser that emits
    `0` for `None`, or a reader that supplies a default for a missing key — and by the time
    the number is on a page, nothing distinguishes it from a measurement. This quantifies over
    the one boundary the domain owns: its own `to_dict` / `from_dict`.
    """
    restored = Observation.from_dict(observation.to_dict())
    return (
        (restored.value is None) == (observation.value is None)
        and (restored.ingest_time is None) == (observation.ingest_time is None)
        and restored == observation
    )

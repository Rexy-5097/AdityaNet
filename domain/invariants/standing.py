"""Invariants over supersession and protocol shape.

ADR-0024's principle — bytes are immutable, standing is not — has no field that expresses it.
It is a property of what the record *does not* do: nothing here mutates or deletes a
superseded release, and these predicates check the record's own consistency.
"""

from __future__ import annotations

from domain.entities.evidence import Supersession
from domain.entities.protocol import Protocol
from domain.values.enums import Severity, SplitStrategy


def supersession_is_wellformed(supersession: Supersession) -> bool:
    """A supersession record says something coherent about standing (ADR-0024).

    A release may not supersede itself, and the reason may not be empty. `superseding` may be
    null: an outright withdrawal with nothing to replace it is a legitimate and common
    outcome, and requiring a replacement would invite a fabricated one.
    """
    if supersession.superseding is not None:
        if supersession.superseding == supersession.superseded:
            return False
    return bool(supersession.reason) and isinstance(supersession.severity, Severity)


def retraction_fails_the_build(supersession: Supersession) -> bool:
    """A `RETRACTION` fails the build; the other two severities do not (STD-22, ADR-0024 §3).

    The asymmetry is the decision. A `CORRECTION` or `DEPRECATION` renders a notice, because
    the reader needs to know the standing changed but the page may still exist. A `RETRACTION`
    anywhere in a Claim's provenance DAG stops the build, because the alternative is
    continuing to publish work that is known to be scientifically invalid.
    """
    return supersession.fails_the_build is (supersession.severity is Severity.RETRACTION)


def bytes_are_never_replaced(supersession: Supersession) -> bool:
    """A supersession names the superseded digest and leaves it addressable (ADR-0024 §1).

    The record points *at* the old digest; it does not carry replacement bytes and has no
    field through which it could. That absence is what guarantees the audit trail survives the
    finding that justified it — a retraction that deleted its subject would destroy the
    evidence for itself.
    """
    return (
        supersession.superseded is not None
        and not hasattr(supersession, "replacement_bytes")
        and not hasattr(supersession, "content")
    )


def split_is_chronological(protocol: Protocol) -> bool:
    """The only permitted split strategy (ADR-0008, `protocol.schema.json`).

    A shuffled split would let a future minute inform a past one, and the resulting score
    would measure interpolation rather than detection — the failure mode that makes a solar
    flare benchmark look far better than it is.
    """
    return protocol.splits.strategy is SplitStrategy.CHRONOLOGICAL


def chronological_boundary_is_locatable(protocol: Protocol) -> bool:
    """`test_start` is a real instant, so the chronological boundary is locatable.

    Named without a `test_` prefix on purpose: pytest collects any callable whose name begins
    with `test_`, so a predicate called `test_period_follows_training` would be silently
    collected as a zero-argument test case and error at collection time.

    Stated separately from `split_is_chronological` because a strategy label and an actual
    boundary are different claims: a protocol can declare itself chronological and give no
    usable point at which the test period begins.
    """
    return protocol.splits.test_start is not None

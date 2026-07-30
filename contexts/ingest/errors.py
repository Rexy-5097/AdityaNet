"""Ingest's members of the failure taxonomy.

TIS §0.2 fixes five failure classes for the whole system and permits no others and no
catch-all. E5 §8 names the four Ingest raises:

    UnavailableResource   the portal or feed is unreachable
    IntegrityFailure      digest mismatch — NO PARTIAL INGEST
    ContractViolation     structure violates the spec — fail loud, never coerce
    PolicyRejection       an adapter attempted to redistribute Tier 0 bytes

Two of those already have owners and are re-exported rather than redefined.
`IntegrityFailure` belongs to the provenance kernel, which is the only thing that computes a
digest and so the only thing that can find one wrong (ADR-0005). `ContractViolation` belongs
to the domain, which is where the shape of an Observation is decided (ADR-0019). Redefining
either here would give one concept two identities, and a caller catching the wrong one would
see an abort pass through as an unhandled error.

The two defined here are the ones with no other home: an unreachable archive and a refused
operation are facts about acquisition, not about digests or shapes.
"""

from __future__ import annotations

from domain.errors import ContractViolation
from kernel.provenance.errors import IntegrityFailure


class IngestError(Exception):
    """Root of the errors Ingest itself defines.

    Exists so a caller can catch them without a bare `except`, which TIS §0.2 forbids
    universally.
    """


class UnavailableResource(IngestError):
    """An external source could not be reached (TIS §0.2, E5 §8).

    Retry policy is adapter-local (E5 §15). Exhaustion raises this, the run aborts, and
    nothing partial is written — E5 §9 states that `aborted` leaves no observations.
    """


class PolicyRejection(IngestError):
    """A gate refused the operation, and the gate is named (TIS §0.2).

    In this context the gate is almost always Tier 0 non-redistribution (ADR-0023, STD-23,
    E5 §11(iv)) or the credential boundary (STD-19, E5 §13). The gate's identity is carried
    rather than described, because a refusal nobody can attribute is a refusal nobody can
    act on.
    """

    def __init__(self, gate: str, message: str) -> None:
        self.gate = gate
        self.message = message
        super().__init__(f"{gate}: {message}")


__all__ = [
    "ContractViolation",
    "IngestError",
    "IntegrityFailure",
    "PolicyRejection",
    "UnavailableResource",
]

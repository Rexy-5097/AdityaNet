"""Invariants over identity — which entities may carry a name, and which may not.

ADR-0005 divides identity in two and TIS E4 §11(ii) states the division as a closed list.
These predicates are that rule made callable, so that "no entity carries a mutable identity
except these five" is something a test can quantify over rather than something a reviewer has
to remember.
"""

from __future__ import annotations

from domain.entities.names import PERMITTED_MUTABLE_IDENTITY, _Named
from domain.values.digest import Digest
from domain.values.identifier import Identifier


def mutable_identity_is_permitted(entity: object) -> bool:
    """True only for the five entities TIS E4 §11(ii) permits a mutable identity.

    Checked by class name against `PERMITTED_MUTABLE_IDENTITY` rather than by `isinstance`
    against a base class, and deliberately so: inheriting from `_Named` is how a *sixth*
    named entity would be added, so a check that trusted the base class would approve exactly
    the case it exists to catch.
    """
    return type(entity).__name__ in PERMITTED_MUTABLE_IDENTITY


#: Entities the contracts give a `digest` field — the releasable, independently citable
#: objects. This list is read from the contracts as merged by M2/E4/#11, not from intuition.
CONTENT_ADDRESSED = (
    "DatasetRelease",
    "LabelRelease",
    "MethodRelease",
    "EnvironmentRelease",
    "Protocol",
    "Evaluation",
)

#: Immutable entities the contracts address by *containment* rather than by their own digest,
#: each with the reason.
#:
#:   Observation      a row within a DatasetRelease, addressed through the release that
#:                    contains it. Carries `source_digest`, so provenance is a column on
#:                    every row.
#:   EvidenceBinding  a pointer *into* an artifact; `artifact_digest` addresses the bytes it
#:                    reads, which is the thing the evidence gate re-checks.
#:   Supersession     addressed through `superseded`. NOTE: ADR-0024 §2 states supersession
#:                    records are "themselves immutable and content-addressed", and
#:                    `supersession.schema.json` as merged by #11 carries no `digest` field.
#:                    That gap is real and is reported against #11 rather than repaired here
#:                    — a contract is #11's to change, and #12 may not edit one silently.
ADDRESSED_BY_CONTAINMENT = {
    "Observation": "source_digest",
    "EvidenceBinding": "artifact_digest",
    "Supersession": "superseded",
}


def immutable_is_content_addressed(entity: object) -> bool:
    """Every immutable entity is reachable by a `Digest` (ADR-0005, STD-02).

    Sequential and timestamp identifiers are forbidden for immutables: they encode when a
    thing was made rather than what it contains, and two different objects can share either.

    Two ways of satisfying that, and the distinction is drawn from the contracts rather than
    invented here. A releasable object carries its own `digest`. A row or a pointer is
    addressed through the digest it names — `ADDRESSED_BY_CONTAINMENT` records which field
    that is for each, and why.
    """
    if mutable_identity_is_permitted(entity):
        return False
    field = ADDRESSED_BY_CONTAINMENT.get(type(entity).__name__)
    if field is not None:
        return isinstance(getattr(entity, field, None), Digest)
    return isinstance(getattr(entity, "digest", None), Digest)


def named_entity_carries_no_digest(entity: _Named) -> bool:
    """A mutable name has no content address (ADR-0005).

    The converse of the rule above, and not redundant with it. Giving a name a digest would
    suggest it can be pinned, and an Evaluation that pinned a *name* rather than a *release*
    would appear reproducible while silently tracking whatever the name points at today.
    """
    return isinstance(entity.id, Identifier) and not hasattr(entity, "digest")

"""The five entities permitted a mutable identity.

ADR-0005 divides identity in two: every immutable object is addressed by the SHA-256 of its
content, and *mutable names* may carry a conventional identifier **because they are never
referenced by an Evaluation**. TIS E4 §11(ii) states the same rule as a closed list:

    Dataset · Method · Source · Instrument · LabelSource

This module is that list and nothing else. The five are grouped in one file precisely so the
list is visible in one place — a sixth named entity added elsewhere would be easy to miss,
whereas adding one here means editing the module whose docstring says there are five, and
`test_named_entities_are_exactly_the_five_permitted` fails.

Each carries an `Identifier` and a human label. They deliberately carry no digest: giving a
name a content address would suggest it can be pinned, and the whole point of the division is
that these cannot. What an Evaluation pins is a *Release*, which is a different entity.

The distinction between `Source` and `Instrument` is not cosmetic (ADR-0003): a Source is how
data was obtained, an Instrument is what measured it. One instrument's data can arrive
through two sources, and conflating them makes the acquisition path unrecoverable.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.identifier import Identifier

#: The closed list from TIS E4 §11(ii). Exported so the invariant predicate and its test read
#: from one definition rather than restating it.
PERMITTED_MUTABLE_IDENTITY = ("Dataset", "Method", "Source", "Instrument", "LabelSource")


@dataclass(frozen=True)
class _Named:
    """Shared construction for a named entity.

    Not an abstraction reached for in advance: there are five instances, which satisfies
    STD-11's requirement of two before generalising. It carries no behaviour of its own —
    only the validation every named entity performs identically — and each concrete class
    below states what it is for.
    """

    id: Identifier
    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, Identifier):
            raise ContractViolation(
                "/id", f"id must be an Identifier, got {type(self.id).__name__}"
            )
        if not isinstance(self.label, str) or not self.label:
            raise ContractViolation("/label", "label must be a non-empty string")

    def to_dict(self) -> dict[str, str]:
        return {"id": str(self.id), "label": self.label}


@dataclass(frozen=True)
class Source(_Named):
    """A channel of acquisition — how data was obtained (ADR-0003)."""


@dataclass(frozen=True)
class Instrument(_Named):
    """A physical instrument — what performed the measurement (ADR-0003)."""


@dataclass(frozen=True)
class Dataset(_Named):
    """The mutable name a sequence of DatasetReleases is published under.

    An Evaluation never references this; it references a DatasetRelease digest. That is what
    lets the name accumulate releases without any published result changing meaning.
    """


@dataclass(frozen=True)
class Method(_Named):
    """The mutable name a sequence of MethodReleases is published under.

    `Method`, never `Model` (ADR-0002): the winning method in this domain is a threshold on a
    count rate, and a vocabulary built around `Model` would structurally privilege machine
    learning over the thing that actually works.
    """


@dataclass(frozen=True)
class LabelSource(_Named):
    """The external authority a sequence of LabelReleases comes from.

    Separate from Dataset because labels are exogenous and revisable (ADR-0007), and they
    come from a different mission than the observations they label (L-09).
    """

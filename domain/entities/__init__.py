"""Entities: objects whose identity persists across changes of attribute.

WHAT IS HERE AND WHAT IS NOT
----------------------------
ADR-0002 fixes the ubiquitous language and lists the first-class entities. Three of them —
`Artifact`, `ProvenanceRecord` and `Run` — are **not** re-declared here. ADR-0026 reclassified
provenance as a shared kernel, `kernel/provenance` already implements all three, and a second
definition of one concept is exactly the drift ADR-0019 warns about. `domain/` cannot import
the kernel (ADR-0026 restricts it to the standard library), so the correct treatment is to
leave them to their owner rather than to mirror them.
`test_domain_does_not_redefine_kernel_entities` pins that.

Two identity regimes, and the split is the point (ADR-0005):

  `names.py`      Dataset · Method · Source · Instrument · LabelSource
                  Mutable identifiers, permitted **because no Evaluation references them**.

  everything else Immutable, content-addressed. What an Evaluation pins.

The entities modelled here are those the contracts define, so that every one has a schema to
round-trip against. `Mission`, `Event`, `Prediction`, `Claim` and `Limitation` appear in
ADR-0002's vocabulary but have no contract, no field list in the TIS, and no referencing
entity; modelling them now would mean inventing their fields, which STD-11 and this project's
standing rule against speculative abstraction both forbid. They are recorded as a gap in the
Issue #12 report rather than guessed at.
"""

from domain.entities.evaluation import PINNED_INPUTS, Evaluation
from domain.entities.evidence import EvidenceBinding, Supersession
from domain.entities.names import (
    PERMITTED_MUTABLE_IDENTITY,
    Dataset,
    Instrument,
    LabelSource,
    Method,
    Source,
)
from domain.entities.observation import Observation
from domain.entities.protocol import Protocol, Splits
from domain.entities.releases import (
    Blas,
    DatasetRelease,
    EnvironmentRelease,
    LabelRelease,
    MethodRelease,
    Platform,
    Table,
)

__all__ = [
    "Blas",
    "Dataset",
    "DatasetRelease",
    "EnvironmentRelease",
    "Evaluation",
    "EvidenceBinding",
    "Instrument",
    "LabelRelease",
    "LabelSource",
    "Method",
    "MethodRelease",
    "Observation",
    "PERMITTED_MUTABLE_IDENTITY",
    "PINNED_INPUTS",
    "Platform",
    "Protocol",
    "Source",
    "Splits",
    "Supersession",
    "Table",
]

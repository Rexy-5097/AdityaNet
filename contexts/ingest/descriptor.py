"""What a Source publishes about itself.

E5 §4 fixes the shape: `SourceDescriptor {source_id, authority, latency_class, granularity}`.
ADR-0003 says why a Source is a separate concept from an Instrument — a Source is a *channel*
(authority, latency class, granularity, retrieval descriptor), an Instrument is a *sensor*.
Conflating a channel with a sensor is a modelling error independent of how many channels
exist, which is what makes the separation a free seam under ADR-0025 rather than an
abstraction bought on speculation.

WHY `latency_class` IS VALIDATED RATHER THAN FREE TEXT
------------------------------------------------------
ADR-0001 lists as a binding non-goal: *"Real-time Aditya-L1 services while the archive remains
~33 days latent."* That non-goal is only checkable if a source's latency is a quantity rather
than a phrase. `~33d` and `about a month` and `slow` are all true descriptions and only one of
them can be compared to anything.

So the field takes a duration — an optional `~` for "approximately", a count, and a unit — and
exposes it in seconds. E5 §18 requires the ISSDC adapter to be registered with latency class
`~33d`, which is a claim a test can now check rather than read.

No enumeration of latency *categories* is defined here. "realtime", "near-real-time" and
"archival" are words this repository has not agreed on, and inventing a vocabulary for a
second source that does not exist is the paid abstraction ADR-0003 explicitly refuses to
authorise.

WHAT THE DESCRIPTOR MUST NOT CARRY
----------------------------------
Credentials. ADR-0003 lists credentials among a Source's properties, and STD-19 and E5 §13
confine them to the adapter. Both hold because the descriptor records *whether*
authentication is needed, never the secret — the same division `manifest.schema.json` makes
for a Tier 0 retrieval descriptor (M2/E4/#14). `requires_credentials` is the whole of what
crosses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values import Identifier

#: `~33d` — optional approximation marker, a count, and a unit. Seconds through days; a
#: latency measured in weeks is expressed in days, because two units for one duration is how
#: `~1w` and `~7d` come to look like different classes.
LATENCY_PATTERN = re.compile(r"^(~?)(\d+)([smhd])$")

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(frozen=True)
class LatencyClass:
    """How far behind the phenomenon a Source's data arrives.

    Parsed, not merely stored, so that ADR-0001's non-goal about real-time services is a
    comparison rather than a reading.
    """

    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise ContractViolation("/latency_class", "latency class must be a non-empty string")
        if LATENCY_PATTERN.match(self.text) is None:
            raise ContractViolation(
                "/latency_class",
                f"latency class {self.text!r} is not a duration such as '~33d' or '5m'. "
                f"A latency that cannot be compared cannot be checked against ADR-0001's "
                f"non-goal on real-time services.",
            )

    @property
    def seconds(self) -> int:
        match = LATENCY_PATTERN.match(self.text)
        assert match is not None  # guaranteed by __post_init__
        return int(match.group(2)) * _UNIT_SECONDS[match.group(3)]

    @property
    def is_approximate(self) -> bool:
        """True where the value is prefixed `~`.

        Recorded because ~33 days is a characterisation of a manual archive process, not a
        measurement of one, and a reader should be able to tell which they are looking at.
        """
        return self.text.startswith("~")

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class RetrievalDescriptor:
    """How to re-acquire Tier 0 bytes this repository does not hold.

    Mirrors `manifest.schema.json#/properties/retrieval` field for field, deliberately: the
    descriptor an adapter publishes and the descriptor a manifest records are the same fact,
    and two shapes for one fact is how they come to disagree (ADR-0023, STD-23).
    """

    provider: str
    locator: str
    requires_credentials: bool = False

    def __post_init__(self) -> None:
        for name in ("provider", "locator"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")
        if not isinstance(self.requires_credentials, bool):
            raise ContractViolation(
                "/requires_credentials",
                f"requires_credentials must be a bool, got "
                f"{type(self.requires_credentials).__name__}",
            )

    def to_dict(self) -> dict[str, object]:
        """The shape `manifest.schema.json` expects under `retrieval`."""
        return {
            "provider": self.provider,
            "locator": self.locator,
            "requires_credentials": self.requires_credentials,
        }


@dataclass(frozen=True)
class SourceDescriptor:
    """What a Source publishes about itself (E5 §4).

    Four fields, exactly as the TIS names them, plus the retrieval descriptor ADR-0003 lists
    among a Source's properties and ADR-0023 requires for Tier 0.
    """

    source_id: Identifier
    authority: str
    latency_class: LatencyClass
    granularity: Identifier
    retrieval: RetrievalDescriptor

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, Identifier):
            raise ContractViolation(
                "/source_id",
                f"source_id must be an Identifier, got {type(self.source_id).__name__}",
            )
        if not isinstance(self.authority, str) or not self.authority:
            raise ContractViolation(
                "/authority",
                "authority must be named — who publishes this channel is part of what the "
                "data means (ADR-0003)",
            )
        if not isinstance(self.latency_class, LatencyClass):
            raise ContractViolation(
                "/latency_class",
                f"latency_class must be a LatencyClass, got "
                f"{type(self.latency_class).__name__}",
            )
        if not isinstance(self.granularity, Identifier):
            raise ContractViolation(
                "/granularity",
                f"granularity must be an Identifier, got {type(self.granularity).__name__}. "
                f"E5 §18 registers the ISSDC channel as 'daily-archive'.",
            )
        if not isinstance(self.retrieval, RetrievalDescriptor):
            raise ContractViolation(
                "/retrieval",
                f"retrieval must be a RetrievalDescriptor, got "
                f"{type(self.retrieval).__name__}",
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": str(self.source_id),
            "authority": self.authority,
            "latency_class": str(self.latency_class),
            "granularity": str(self.granularity),
            "retrieval": self.retrieval.to_dict(),
        }


__all__ = [
    "LATENCY_PATTERN",
    "LatencyClass",
    "RetrievalDescriptor",
    "SourceDescriptor",
]

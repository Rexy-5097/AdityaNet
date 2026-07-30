"""What an acquisition produces: a referenced artifact and the provenance of getting it.

E5 §4: `acquire(selector) -> RawArtifact + AcquisitionProvenance`.

THE ARTIFACT HOLDS NO BYTES, AND THAT IS THE POINT
---------------------------------------------------
`RawArtifact` has a digest, a size, a retrieval descriptor and an optional cache path. It has
no `bytes` field and no `content` field, and `test_a_raw_artifact_cannot_carry_bytes` asserts
that it never gains one. Two separate rules land on the same design:

  ADR-0023 / STD-23 / E5 §11(iv)  Tier 0 bytes are referenced, never redistributed. Local
                                  copies are evictable caches, never the system of record.
  E5 §12                          Streaming parse; a whole-day archive must not be fully
                                  materialised.

A type that could hold the bytes would make both violations one attribute access away, and
neither would be visible in review — the object would simply be larger.

`cache_path` is the evictable copy. It is optional because a cache that has been evicted is
the normal case, not an error: what makes the artifact usable again is `retrieval`, which is
why that field is required and the path is not.

THE CLOCK READ
--------------
`AcquisitionProvenance.ingest_time` is stamped by `contexts.ingest.boundary.stamp`, the single
sanctioned clock read in the system (ADR-0004, TIS §0.4). It is required and non-null here,
because this type describes an acquisition that *just happened*. Historical rows that predate
bitemporal capture carry `ingest_time = None` on the Observation (ADR-0022) and have no
AcquisitionProvenance at all — there is no acquisition to describe, and E5 §11(ii) forbids any
code path from writing a non-null ingest_time for them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from contexts.ingest.descriptor import RetrievalDescriptor
from domain.errors import ContractViolation
from domain.values import Digest, Identifier, RunId, Timestamp


@dataclass(frozen=True)
class RawArtifact:
    """A Tier 0 artifact, identified rather than held (ADR-0023)."""

    digest: Digest
    size_bytes: int
    retrieval: RetrievalDescriptor
    #: Where an evictable local copy currently sits, if one does. Never the system of record.
    cache_path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.digest, Digest):
            raise ContractViolation(
                "/digest",
                f"digest must be a Digest, got {type(self.digest).__name__}. Only the "
                f"provenance kernel mints one (ADR-0005); this records the one it minted.",
            )
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise ContractViolation(
                "/size_bytes",
                f"size_bytes must be an integer, got {type(self.size_bytes).__name__}",
            )
        if self.size_bytes < 0:
            raise ContractViolation(
                "/size_bytes", f"size_bytes must be non-negative, got {self.size_bytes}"
            )
        if not isinstance(self.retrieval, RetrievalDescriptor):
            raise ContractViolation(
                "/retrieval",
                f"retrieval must be a RetrievalDescriptor, got "
                f"{type(self.retrieval).__name__}. Without one these bytes cannot be "
                f"re-acquired, and ADR-0023 requires that any stage can.",
            )
        if self.cache_path is not None and not isinstance(self.cache_path, Path):
            raise ContractViolation(
                "/cache_path",
                f"cache_path must be a Path or None, got {type(self.cache_path).__name__}",
            )

    @property
    def is_cached(self) -> bool:
        """Whether a local copy is currently recorded. An evicted cache is not an error."""
        return self.cache_path is not None


@dataclass(frozen=True)
class AcquisitionProvenance:
    """The record of one acquisition, for the provenance kernel to store (E5 §7).

    Carries the run that performed it, the source it came from, the digest it produced and
    the instant the system learned of it. Nothing else — and specifically no credential, no
    URL that might embed a token, and no response body (E5 §13, §14).
    """

    run_id: RunId
    source_id: Identifier
    artifact_digest: Digest
    #: The sanctioned clock read (ADR-0004). Required and non-null: this describes an
    #: acquisition that happened, so the moment is known by construction.
    ingest_time: Timestamp
    #: Instruments whose products this artifact contains, if the source states them. Empty
    #: where the channel is instrument-agnostic; a daily archive may carry several.
    instruments: tuple[Identifier, ...] = field(default=())

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, RunId):
            raise ContractViolation(
                "/run_id", f"run_id must be a RunId, got {type(self.run_id).__name__}"
            )
        if not isinstance(self.source_id, Identifier):
            raise ContractViolation(
                "/source_id",
                f"source_id must be an Identifier, got {type(self.source_id).__name__}",
            )
        if not isinstance(self.artifact_digest, Digest):
            raise ContractViolation(
                "/artifact_digest",
                f"artifact_digest must be a Digest, got "
                f"{type(self.artifact_digest).__name__}",
            )
        if not isinstance(self.ingest_time, Timestamp):
            raise ContractViolation(
                "/ingest_time",
                f"ingest_time must be a Timestamp, got {type(self.ingest_time).__name__}. "
                f"An acquisition that happened has a known moment; ADR-0022's null is for "
                f"historical rows, which have no acquisition to describe.",
            )
        if not isinstance(self.instruments, tuple):
            raise ContractViolation(
                "/instruments",
                f"instruments must be a tuple, got {type(self.instruments).__name__}",
            )
        if any(not isinstance(i, Identifier) for i in self.instruments):
            raise ContractViolation(
                "/instruments", "every instrument must be an Identifier"
            )
        if len(set(self.instruments)) != len(self.instruments):
            raise ContractViolation("/instruments", "instruments must be unique")

    def to_dict(self) -> dict[str, object]:
        """A structured record, suitable for logging (TIS §0.3) and for the kernel.

        Contains `source_id`, `instrument_id`s and the artifact digest — exactly the fields
        E5 §14 says to log — and none of the fields it says never to log.
        """
        return {
            "run_id": str(self.run_id),
            "source_id": str(self.source_id),
            "artifact_digest": str(self.artifact_digest),
            "ingest_time": str(self.ingest_time),
            "instruments": [str(i) for i in self.instruments],
        }


@dataclass(frozen=True)
class Acquisition:
    """The pair `acquire` returns (E5 §4), kept together because neither is usable alone.

    An artifact without its provenance is bytes nobody can attribute; provenance without its
    artifact is a claim about nothing.
    """

    artifact: RawArtifact
    provenance: AcquisitionProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, RawArtifact):
            raise ContractViolation(
                "/artifact",
                f"artifact must be a RawArtifact, got {type(self.artifact).__name__}",
            )
        if not isinstance(self.provenance, AcquisitionProvenance):
            raise ContractViolation(
                "/provenance",
                f"provenance must be an AcquisitionProvenance, got "
                f"{type(self.provenance).__name__}",
            )
        if self.artifact.digest != self.provenance.artifact_digest:
            raise ContractViolation(
                "",
                f"the provenance records digest {self.provenance.artifact_digest.short} "
                f"but the artifact is {self.artifact.digest.short}. A record that points at "
                f"different bytes than the artifact it accompanies is worse than no record: "
                f"it looks like attribution.",
            )


__all__ = ["Acquisition", "AcquisitionProvenance", "RawArtifact"]

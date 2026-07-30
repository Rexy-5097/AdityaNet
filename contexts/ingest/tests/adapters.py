"""In-test adapters: one that conforms, and one per rule that does not.

NOT SOURCE ADAPTERS, AND THE DISTINCTION IS THE ISSUE BOUNDARY
---------------------------------------------------------------
M3/E5/#16 delivers the ISSDC-PRADAN adapter: it reaches a real archive, holds a real session,
and retrieves real bytes. Nothing here does any of that. These are the *subjects* of the
conformance check — the smallest objects that satisfy or violate the contract, so that
`verify_conformance` can be watched accepting and refusing.

A conformance checker tested only against a conforming adapter is a checker nobody has seen
reject anything, and this repository has already shipped one gate with that defect. So each
violation below is a separate class that breaks exactly one rule and keeps the others, which
is what makes a failing assertion attributable to the rule it names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.acquisition import Acquisition, AcquisitionProvenance, RawArtifact
from contexts.ingest.credentials import Credential
from contexts.ingest.descriptor import (
    LatencyClass,
    RetrievalDescriptor,
    SourceDescriptor,
)
from domain.values import Digest, Identifier, RunId, Timestamp

RUN = RunId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
DIGEST = Digest("a" * 64)
OTHER_DIGEST = Digest("b" * 64)


def descriptor(**overrides) -> SourceDescriptor:
    """The ISSDC channel as E5 §18 describes it: latency `~33d`, granularity `daily-archive`."""
    fields = {
        "source_id": Identifier("issdc-pradan"),
        "authority": "ISSDC, Indian Space Research Organisation",
        "latency_class": LatencyClass("~33d"),
        "granularity": Identifier("daily-archive"),
        "retrieval": RetrievalDescriptor(
            provider="ISSDC PRADAN",
            locator="aditya-l1/solexs/l1/2024-03-01",
            requires_credentials=True,
        ),
    }
    fields.update(overrides)
    return SourceDescriptor(**fields)


def acquisition(**overrides) -> Acquisition:
    fields = {
        "artifact": RawArtifact(
            digest=DIGEST,
            size_bytes=4096,
            retrieval=descriptor().retrieval,
            cache_path=Path("/tmp/cache/aaaa.fits"),
        ),
        "provenance": AcquisitionProvenance(
            run_id=RUN,
            source_id=Identifier("issdc-pradan"),
            artifact_digest=DIGEST,
            ingest_time=Timestamp("2024-04-03T12:00:00Z"),
            instruments=(Identifier("solexs"),),
        ),
    }
    fields.update(overrides)
    return Acquisition(**fields)


class ConformingAdapter:
    """Satisfies every rule. The positive case, without which the checker could reject all."""

    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> Acquisition:
        return acquisition()


class AdapterWithNoDescriptor:
    """Missing half the interface E5 §4 requires."""

    def acquire(self, selector: str) -> Acquisition:
        return acquisition()


class AdapterWithNoAcquire:
    def descriptor(self) -> SourceDescriptor:
        return descriptor()


class AdapterReturningTheWrongDescriptorType:
    """Describes itself in its own vocabulary, so nothing can compare it to another channel."""

    def descriptor(self) -> dict:
        return {"source_id": "issdc-pradan", "latency": "about a month"}

    def acquire(self, selector: str) -> Acquisition:
        return acquisition()


class AdapterWithAVaryingDescriptor:
    """Declares a different latency every time it is asked, which is to declare none."""

    def __init__(self) -> None:
        self._calls = 0

    def descriptor(self) -> SourceDescriptor:
        self._calls += 1
        return descriptor(latency_class=LatencyClass(f"~{30 + self._calls}d"))

    def acquire(self, selector: str) -> Acquisition:
        return acquisition()


@dataclass(frozen=True)
class LeakyDescriptorHolder:
    """A descriptor-shaped object that also carries the session cookie."""

    source_id: Identifier
    authority: str
    session: Credential


class AdapterLeakingACredentialInItsDescriptor:
    """STD-19, E5 §13: the descriptor records *how* to acquire, never the secret."""

    def descriptor(self) -> SourceDescriptor:
        return LeakyDescriptorHolder(  # type: ignore[return-value]
            source_id=Identifier("issdc-pradan"),
            authority="ISSDC",
            session=Credential("issdc-session", "PRADAN-SESSION-abc123"),
        )

    def acquire(self, selector: str) -> Acquisition:
        return acquisition()


@dataclass(frozen=True)
class ProvenanceCarryingASecret:
    """Provenance-shaped, and would persist a secret to an artifact (E5 §13)."""

    run_id: RunId
    source_id: Identifier
    artifact_digest: Digest
    ingest_time: Timestamp
    credential: Credential


class AdapterPersistingACredentialInProvenance:
    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> Acquisition:
        provenance = ProvenanceCarryingASecret(
            run_id=RUN,
            source_id=Identifier("issdc-pradan"),
            artifact_digest=DIGEST,
            ingest_time=Timestamp("2024-04-03T12:00:00Z"),
            credential=Credential("issdc-session", "PRADAN-SESSION-abc123"),
        )
        return _unchecked_acquisition(
            RawArtifact(DIGEST, 4096, descriptor().retrieval), provenance
        )


@dataclass(frozen=True)
class ArtifactHoldingBytes:
    """Would materialise a whole-day archive and could redistribute Tier 0 (ADR-0023, E5 §12)."""

    digest: Digest
    size_bytes: int
    retrieval: RetrievalDescriptor
    cache_path: Path | None
    bytes: bytes


class AdapterHoldingRawBytes:
    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> Acquisition:
        artifact = ArtifactHoldingBytes(
            digest=DIGEST,
            size_bytes=4,
            retrieval=descriptor().retrieval,
            cache_path=None,
            bytes=b"\x00\x01\x02\x03",
        )
        return _unchecked_acquisition(artifact, acquisition().provenance)


class AdapterReturningTheWrongAcquisitionType:
    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> RawArtifact:
        return acquisition().artifact


@dataclass(frozen=True)
class ProvenanceWithoutAnIngestTime:
    run_id: RunId
    source_id: Identifier
    artifact_digest: Digest
    ingest_time: None


class AdapterOmittingTheIngestTime:
    """E5 §11(i): every newly ingested Observation carries valid_time AND ingest_time."""

    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> Acquisition:
        provenance = ProvenanceWithoutAnIngestTime(
            run_id=RUN,
            source_id=Identifier("issdc-pradan"),
            artifact_digest=DIGEST,
            ingest_time=None,
        )
        return _unchecked_acquisition(
            RawArtifact(DIGEST, 4096, descriptor().retrieval), provenance
        )


class AdapterMisattributingItsArtifact:
    """Provenance pointing at bytes other than the artifact it accompanies."""

    def descriptor(self) -> SourceDescriptor:
        return descriptor()

    def acquire(self, selector: str) -> Acquisition:
        return _unchecked_acquisition(
            RawArtifact(DIGEST, 4096, descriptor().retrieval),
            AcquisitionProvenance(
                run_id=RUN,
                source_id=Identifier("issdc-pradan"),
                artifact_digest=OTHER_DIGEST,
                ingest_time=Timestamp("2024-04-03T12:00:00Z"),
            ),
        )


def _unchecked_acquisition(artifact: object, provenance: object) -> Acquisition:
    """Build an `Acquisition` around parts its constructor would refuse.

    `Acquisition.__post_init__` rejects most of these violations outright, which is the
    correct behaviour and is tested directly. But `verify_conformance` must also reject them,
    because an adapter written before this contract existed — or one that builds its result
    some other way — can hand the checker an object the constructor never saw. Bypassing
    validation here is what lets the checker be tested rather than the constructor.
    """
    instance = object.__new__(Acquisition)
    object.__setattr__(instance, "artifact", artifact)
    object.__setattr__(instance, "provenance", provenance)
    return instance

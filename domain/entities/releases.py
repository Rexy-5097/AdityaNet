"""The four pinnable releases.

A *Release* is what an Evaluation pins. Where a name (`domain/entities/names.py`) may accrue
new versions without any published result changing meaning, a Release is immutable and
content-addressed, and that is the whole basis on which a result can be re-checked years
later (ADR-0005, ADR-0006, STD-10).

Four of the five inputs ADR-0021 pins live here: DatasetRelease, LabelRelease, MethodRelease
and EnvironmentRelease. The fifth, Protocol, is in its own module because it carries the
evaluation *procedure* rather than a snapshot of inputs.

Each carries its own `digest`. This module does not compute one and could not: ADR-0005 makes
the provenance shared kernel the only minting authority, and ADR-0026 forbids `domain/` from
importing it. The digest arrives from whichever context created the release; what the domain
enforces is that it is present and well formed, so an unpinned release cannot exist as a
value.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.digest import Digest
from domain.values.identifier import Identifier, RunId
from domain.values.timestamp import Timestamp


def _require(value: object, kind: type, pointer: str, label: str) -> None:
    if not isinstance(value, kind):
        raise ContractViolation(
            pointer, f"{label} must be a {kind.__name__}, got {type(value).__name__}"
        )


def _require_count(value: object, pointer: str, label: str, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractViolation(
            pointer, f"{label} must be an integer, got {type(value).__name__}"
        )
    if value < minimum:
        raise ContractViolation(pointer, f"{label} must be at least {minimum}, got {value}")


@dataclass(frozen=True)
class Table:
    """One canonical table inside a DatasetRelease.

    Per-table digests roll up to the release digest so that a changed byte is *locatable*
    rather than merely detectable. A single release-level digest would tell an investigator
    that something moved and nothing about where.
    """

    key: str
    name: str
    digest: Digest
    n_files: int
    bytes: int

    def __post_init__(self) -> None:
        # `^[A-Z][0-9]+$` — the contract's shape for a table key, e.g. "T1".
        if (
            not isinstance(self.key, str)
            or len(self.key) < 2
            or not self.key[0].isascii()
            or not self.key[0].isupper()
            or not self.key[1:].isdigit()
        ):
            raise ContractViolation(
                "/key", f"table key must be an upper-case letter followed by digits, got {self.key!r}"
            )
        if not isinstance(self.name, str) or not self.name:
            raise ContractViolation("/name", "table name must be a non-empty string")
        _require(self.digest, Digest, "/digest", "digest")
        _require_count(self.n_files, "/n_files", "n_files", 0)
        _require_count(self.bytes, "/bytes", "bytes", 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "digest": str(self.digest),
            "n_files": self.n_files,
            "bytes": self.bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Table:
        return cls(
            key=data["key"],                      # type: ignore[arg-type]
            name=data["name"],                    # type: ignore[arg-type]
            digest=Digest(data["digest"]),        # type: ignore[arg-type]
            n_files=data["n_files"],              # type: ignore[arg-type]
            bytes=data["bytes"],                  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class DatasetRelease:
    """An immutable, digest-addressed snapshot of canonical tables — the citable unit."""

    dataset_id: Identifier
    version: str
    digest: Digest
    tables: tuple[Table, ...]
    frozen_at: Timestamp
    n_files: int
    total_bytes: int
    #: Tier 1 deposition identifier. `None` before deposition, or where the fallback path was
    #: used. Its absence degrades citability and is published rather than hidden (ADR-0023).
    doi: str | None = None

    def __post_init__(self) -> None:
        _require(self.dataset_id, Identifier, "/dataset_id", "dataset_id")
        if not isinstance(self.version, str) or not self.version:
            raise ContractViolation("/version", "version must be a non-empty string")
        _require(self.digest, Digest, "/digest", "digest")
        _require(self.frozen_at, Timestamp, "/frozen_at", "frozen_at")
        _require_count(self.n_files, "/n_files", "n_files", 1)
        _require_count(self.total_bytes, "/total_bytes", "total_bytes", 0)

        if not isinstance(self.tables, tuple):
            raise ContractViolation(
                "/tables", f"tables must be a tuple, got {type(self.tables).__name__}"
            )
        if not self.tables:
            raise ContractViolation(
                "/tables", "a release with no tables releases nothing"
            )
        if any(not isinstance(t, Table) for t in self.tables):
            raise ContractViolation("/tables", "every table must be a Table")
        keys = [t.key for t in self.tables]
        if len(set(keys)) != len(keys):
            raise ContractViolation("/tables", f"table keys must be unique, got {keys}")
        if self.doi is not None and (not isinstance(self.doi, str) or not self.doi):
            raise ContractViolation(
                "/doi", "doi must be a non-empty string or None; an empty string would be "
                "indistinguishable from an absent deposition"
            )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "dataset_id": str(self.dataset_id),
            "version": self.version,
            "digest": str(self.digest),
            "tables": [t.to_dict() for t in self.tables],
            "frozen_at": str(self.frozen_at),
            "n_files": self.n_files,
            "total_bytes": self.total_bytes,
        }
        if self.doi is not None:
            data["doi"] = self.doi
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DatasetRelease:
        return cls(
            dataset_id=Identifier(data["dataset_id"]),   # type: ignore[arg-type]
            version=data["version"],                     # type: ignore[arg-type]
            digest=Digest(data["digest"]),               # type: ignore[arg-type]
            tables=tuple(Table.from_dict(t) for t in data["tables"]),  # type: ignore[arg-type]
            frozen_at=Timestamp(data["frozen_at"]),      # type: ignore[arg-type]
            n_files=data["n_files"],                     # type: ignore[arg-type]
            total_bytes=data["total_bytes"],             # type: ignore[arg-type]
            doi=data.get("doi"),                         # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class LabelRelease:
    """An external authority's ground truth, snapshotted at a recorded ingest time.

    `ingest_time` is NOT nullable here, unlike an Observation's. The asymmetry is deliberate
    and is the reason the two fields are not shared: a label release is created *by this
    system*, so the moment it was taken is always known. An Observation may predate bitemporal
    capture entirely (ADR-0022); a LabelRelease cannot.
    """

    label_source_id: Identifier
    authority: str
    digest: Digest
    ingest_time: Timestamp
    n_events: int
    #: The prior release this revises, or `None` for the first. A revision produces a new
    #: release; the prior one is retained and remains addressable (ADR-0007).
    supersedes_digest: Digest | None = None

    def __post_init__(self) -> None:
        _require(self.label_source_id, Identifier, "/label_source_id", "label_source_id")
        if not isinstance(self.authority, str) or not self.authority:
            raise ContractViolation(
                "/authority",
                "authority must be named — labels come from a different mission than the "
                "observations they label (L-09)",
            )
        _require(self.digest, Digest, "/digest", "digest")
        _require(self.ingest_time, Timestamp, "/ingest_time", "ingest_time")
        _require_count(self.n_events, "/n_events", "n_events", 0)
        if self.supersedes_digest is not None:
            _require(self.supersedes_digest, Digest, "/supersedes_digest", "supersedes_digest")
            if self.supersedes_digest == self.digest:
                raise ContractViolation(
                    "/supersedes_digest", "a release cannot supersede itself"
                )

    def to_dict(self) -> dict[str, object]:
        return {
            "label_source_id": str(self.label_source_id),
            "authority": self.authority,
            "digest": str(self.digest),
            "ingest_time": str(self.ingest_time),
            "n_events": self.n_events,
            "supersedes_digest": (
                None if self.supersedes_digest is None else str(self.supersedes_digest)
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> LabelRelease:
        prior = data.get("supersedes_digest")
        return cls(
            label_source_id=Identifier(data["label_source_id"]),  # type: ignore[arg-type]
            authority=data["authority"],                          # type: ignore[arg-type]
            digest=Digest(data["digest"]),                        # type: ignore[arg-type]
            ingest_time=Timestamp(data["ingest_time"]),           # type: ignore[arg-type]
            n_events=data["n_events"],                            # type: ignore[arg-type]
            supersedes_digest=None if prior is None else Digest(prior),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class MethodRelease:
    """A scoreable method, with the instruments it consumes declared machine-readably.

    `declared_instruments` is required and non-empty. ADR-0011 exists because the v1 framework
    declared exactly this metadata correctly and then never compared it against anything
    (SALVAGE-002). The comparison against a Protocol's `permitted_instruments` is
    `domain.invariants.declared_instruments_are_permitted`; keeping the declaration here and
    the comparison there is what makes the rule checkable by a property test over both.
    """

    method_id: Identifier
    digest: Digest
    artifact_digest: Digest
    declared_instruments: tuple[Identifier, ...]
    parameters: dict[str, object]
    #: The run that produced this release, or `None` for a method with no fitting step. A
    #: threshold detector legitimately has none — which is why this is nullable rather than
    #: an admission of missing provenance.
    training_provenance: RunId | None

    def __post_init__(self) -> None:
        _require(self.method_id, Identifier, "/method_id", "method_id")
        _require(self.digest, Digest, "/digest", "digest")
        _require(self.artifact_digest, Digest, "/artifact_digest", "artifact_digest")

        if not isinstance(self.declared_instruments, tuple):
            raise ContractViolation(
                "/declared_instruments",
                f"declared_instruments must be a tuple, got "
                f"{type(self.declared_instruments).__name__}",
            )
        if not self.declared_instruments:
            raise ContractViolation(
                "/declared_instruments",
                "a method must declare at least one instrument; an empty declaration would "
                "be a subset of every permitted set and so would pass ADR-0011 vacuously",
            )
        if any(not isinstance(i, Identifier) for i in self.declared_instruments):
            raise ContractViolation(
                "/declared_instruments", "every declared instrument must be an Identifier"
            )
        if len(set(self.declared_instruments)) != len(self.declared_instruments):
            raise ContractViolation(
                "/declared_instruments", "declared instruments must be unique"
            )
        if not isinstance(self.parameters, dict):
            raise ContractViolation(
                "/parameters",
                f"parameters must be a dict, got {type(self.parameters).__name__}",
            )
        if any(not isinstance(k, str) for k in self.parameters):
            raise ContractViolation("/parameters", "every parameter name must be a string")
        if self.training_provenance is not None:
            _require(self.training_provenance, RunId, "/training_provenance", "training_provenance")

    def to_dict(self) -> dict[str, object]:
        return {
            "method_id": str(self.method_id),
            "digest": str(self.digest),
            "artifact_digest": str(self.artifact_digest),
            "declared_instruments": [str(i) for i in self.declared_instruments],
            "parameters": dict(self.parameters),
            "training_provenance": (
                None if self.training_provenance is None else str(self.training_provenance)
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> MethodRelease:
        run = data.get("training_provenance")
        return cls(
            method_id=Identifier(data["method_id"]),           # type: ignore[arg-type]
            digest=Digest(data["digest"]),                     # type: ignore[arg-type]
            artifact_digest=Digest(data["artifact_digest"]),   # type: ignore[arg-type]
            declared_instruments=tuple(
                Identifier(i) for i in data["declared_instruments"]  # type: ignore[union-attr]
            ),
            parameters=dict(data["parameters"]),               # type: ignore[arg-type]
            training_provenance=None if run is None else RunId(run),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Blas:
    """BLAS/LAPACK implementation and version — pinned, because reduction order depends on it."""

    implementation: str
    version: str

    def __post_init__(self) -> None:
        for name in ("implementation", "version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")

    def to_dict(self) -> dict[str, str]:
        return {"implementation": self.implementation, "version": self.version}


@dataclass(frozen=True)
class Platform:
    """OS and CPU architecture. RECORDED, NOT PINNED (ADR-0021).

    Bit-identity across architectures cannot be guaranteed and claiming it would be an
    unsupported assertion. A platform difference is exactly what separates reproduction class
    EXACT from EQUIVALENT, which is why this is captured rather than ignored.
    """

    os: str
    arch: str

    def __post_init__(self) -> None:
        for name in ("os", "arch"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")

    def to_dict(self) -> dict[str, str]:
        return {"os": self.os, "arch": self.arch}


@dataclass(frozen=True)
class EnvironmentRelease:
    """The fifth pinned evaluation input (ADR-0021, superseding ADR-0009).

    ADR-0009 asserted an Evaluation was a pure function of four inputs. That was false:
    results also depend on library versions, BLAS implementation, thread count, reduction
    order and CPU architecture. Pinning determinism in a *standard* does not make the
    environment an *input*, and an unpinned input makes the central invariant unenforceable.
    """

    digest: Digest
    interpreter_version: str
    lockfile_digest: Digest
    blas: Blas
    #: Pinned because reduction order under multithreaded BLAS is not deterministic. Keys are
    #: set by the libraries installed, not by the contract — the one open object in the set.
    thread_counts: dict[str, int]
    hash_seed: int
    platform: Platform
    #: `None` where no container was used. ADR-0016's image is authored but unbuilt, so this
    #: is null in practice today.
    container_digest: Digest | None = None

    def __post_init__(self) -> None:
        _require(self.digest, Digest, "/digest", "digest")
        if not isinstance(self.interpreter_version, str) or not self.interpreter_version:
            raise ContractViolation(
                "/interpreter_version", "interpreter_version must be a non-empty string"
            )
        _require(self.lockfile_digest, Digest, "/lockfile_digest", "lockfile_digest")
        _require(self.blas, Blas, "/blas", "blas")
        _require(self.platform, Platform, "/platform", "platform")

        if not isinstance(self.thread_counts, dict):
            raise ContractViolation(
                "/thread_counts",
                f"thread_counts must be a dict, got {type(self.thread_counts).__name__}",
            )
        if not self.thread_counts:
            raise ContractViolation(
                "/thread_counts",
                "at least one thread count must be pinned; an empty map pins nothing while "
                "appearing to",
            )
        for name, count in self.thread_counts.items():
            if not isinstance(name, str) or not name:
                raise ContractViolation(
                    "/thread_counts", "every thread-count key must be a non-empty string"
                )
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ContractViolation(
                    f"/thread_counts/{name}", f"thread count must be an integer >= 1, got {count!r}"
                )
        if isinstance(self.hash_seed, bool) or not isinstance(self.hash_seed, int):
            raise ContractViolation(
                "/hash_seed", f"hash_seed must be an integer, got {type(self.hash_seed).__name__}"
            )
        if self.hash_seed < 0:
            raise ContractViolation(
                "/hash_seed", f"hash_seed must be non-negative, got {self.hash_seed}"
            )
        if self.container_digest is not None:
            _require(self.container_digest, Digest, "/container_digest", "container_digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "digest": str(self.digest),
            "interpreter_version": self.interpreter_version,
            "lockfile_digest": str(self.lockfile_digest),
            "blas": self.blas.to_dict(),
            "thread_counts": dict(self.thread_counts),
            "hash_seed": self.hash_seed,
            "container_digest": (
                None if self.container_digest is None else str(self.container_digest)
            ),
            "platform": self.platform.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> EnvironmentRelease:
        container = data.get("container_digest")
        blas = data["blas"]
        platform = data["platform"]
        return cls(
            digest=Digest(data["digest"]),                          # type: ignore[arg-type]
            interpreter_version=data["interpreter_version"],        # type: ignore[arg-type]
            lockfile_digest=Digest(data["lockfile_digest"]),        # type: ignore[arg-type]
            blas=Blas(blas["implementation"], blas["version"]),     # type: ignore[index]
            thread_counts=dict(data["thread_counts"]),              # type: ignore[arg-type]
            hash_seed=data["hash_seed"],                            # type: ignore[arg-type]
            platform=Platform(platform["os"], platform["arch"]),    # type: ignore[index]
            container_digest=None if container is None else Digest(container),  # type: ignore[arg-type]
        )

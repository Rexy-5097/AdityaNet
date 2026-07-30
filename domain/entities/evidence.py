"""`EvidenceBinding` and `Supersession` — what a published number must carry, and how a
release loses standing without losing its bytes.

EVIDENCE BINDING
----------------
There is deliberately **no `value` field**. A rendering component cannot be passed a number,
so a number cannot reach a page without existing in an artifact first (ADR-0012, ADR-0013).
The binding names an artifact, a JSON Pointer into it, and the digest of the exact bytes read;
the evidence gate re-reads the artifact and fails the build on drift.

That absence is the entire design. Adding a convenience `value` field "for rendering" would
reintroduce the failure the binding exists to prevent, so `test_evidence_binding_has_no_value_
field` asserts it stays absent.

`artifact` is a repository-relative path and TIS E4 §13 requires that a contract not permit a
free-form path that could escape the artifact root. The schema's `minLength: 1` does not do
that on its own, so the containment check is enforced here — absolute paths, `..` traversal,
and backslash separators are all refused.

SUPERSESSION
------------
ADR-0024: bytes are immutable, standing is not. The bytes of a superseded release never
change and are never deleted; a Supersession is a separate, immutable record that says the
release should no longer be relied upon. `superseding` is nullable for outright withdrawal
with nothing to replace it — a `RETRACTION` frequently has no replacement, and forcing one
would invite a fabricated substitute.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.digest import Digest
from domain.values.enums import Severity
from domain.values.identifier import RunId
from domain.values.timestamp import Timestamp


def _contained_relative_path(path: str, pointer: str) -> str:
    """Reject anything that is not a repository-relative path inside the artifact root.

    TIS E4 §13. Checked here rather than by pattern in the schema because the rule is about
    what a path *resolves to*, and normalisation is what reveals it: `a/../../b` contains no
    leading `..` but escapes all the same.
    """
    if not isinstance(path, str) or not path:
        raise ContractViolation(pointer, "artifact path must be a non-empty string")
    if path.startswith("/"):
        raise ContractViolation(
            pointer, f"artifact path must be repository-relative, got absolute {path!r}"
        )
    if "\\" in path:
        # A backslash is a legal character in a POSIX filename, so a path containing one is
        # ambiguous between a separator and a name. Refusing is the only unambiguous reading.
        raise ContractViolation(
            pointer, f"artifact path must use '/' separators, got {path!r}"
        )
    if "\x00" in path:
        raise ContractViolation(pointer, "artifact path must not contain a null byte")
    normalised = posixpath.normpath(path)
    if normalised == ".." or normalised.startswith("../"):
        raise ContractViolation(
            pointer,
            f"artifact path {path!r} escapes the artifact root (normalises to "
            f"{normalised!r})",
        )
    return path


def _valid_json_pointer(pointer_value: str, pointer: str) -> str:
    """RFC 6901. The empty string is the whole document and is legal."""
    if not isinstance(pointer_value, str):
        raise ContractViolation(
            pointer, f"pointer must be a string, got {type(pointer_value).__name__}"
        )
    if pointer_value == "":
        return pointer_value
    if not pointer_value.startswith("/"):
        raise ContractViolation(
            pointer,
            f"JSON Pointer must be empty or begin with '/', got {pointer_value!r}",
        )
    for token in pointer_value.split("/")[1:]:
        index = 0
        while index < len(token):
            if token[index] == "~":
                # RFC 6901 defines exactly two escapes: ~0 for '~' and ~1 for '/'. Any other
                # sequence is malformed, and guessing the intent would be coercion.
                if index + 1 >= len(token) or token[index + 1] not in "01":
                    raise ContractViolation(
                        pointer,
                        f"JSON Pointer {pointer_value!r} has an invalid escape; '~' must be "
                        f"followed by '0' or '1'",
                    )
                index += 2
                continue
            index += 1
    return pointer_value


@dataclass(frozen=True)
class EvidenceBinding:
    """A published claim bound to the artifact bytes that support it.

    Carries no value, by design — see the module docstring.
    """

    claim_id: str
    measurement_key: str
    artifact: str
    pointer: str
    artifact_digest: Digest
    run_id: RunId

    def __post_init__(self) -> None:
        for name in ("claim_id", "measurement_key"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")
        _contained_relative_path(self.artifact, "/artifact")
        _valid_json_pointer(self.pointer, "/pointer")
        if not isinstance(self.artifact_digest, Digest):
            raise ContractViolation(
                "/artifact_digest",
                f"artifact_digest must be a Digest, got "
                f"{type(self.artifact_digest).__name__}. The gate re-reads the artifact and "
                f"compares; without a digest there is nothing to compare against.",
            )
        if not isinstance(self.run_id, RunId):
            raise ContractViolation(
                "/run_id", f"run_id must be a RunId, got {type(self.run_id).__name__}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "measurement_key": self.measurement_key,
            "artifact": self.artifact,
            "pointer": self.pointer,
            "artifact_digest": str(self.artifact_digest),
            "run_id": str(self.run_id),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> EvidenceBinding:
        return cls(
            claim_id=data["claim_id"],                          # type: ignore[arg-type]
            measurement_key=data["measurement_key"],            # type: ignore[arg-type]
            artifact=data["artifact"],                          # type: ignore[arg-type]
            pointer=data["pointer"],                            # type: ignore[arg-type]
            artifact_digest=Digest(data["artifact_digest"]),    # type: ignore[arg-type]
            run_id=RunId(data["run_id"]),                       # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Supersession:
    """An immutable record that a release has lost standing (ADR-0024)."""

    superseded: Digest
    #: The replacement, or `None` for outright withdrawal with nothing to replace it.
    superseding: Digest | None
    severity: Severity
    reason: str
    effective_date: Timestamp
    discovered_by: RunId

    def __post_init__(self) -> None:
        if not isinstance(self.superseded, Digest):
            raise ContractViolation(
                "/superseded",
                f"superseded must be a Digest, got {type(self.superseded).__name__}",
            )
        if self.superseding is not None and not isinstance(self.superseding, Digest):
            raise ContractViolation(
                "/superseding",
                f"superseding must be a Digest or None, got "
                f"{type(self.superseding).__name__}",
            )
        if self.superseding is not None and self.superseding == self.superseded:
            raise ContractViolation(
                "/superseding",
                "a release cannot supersede itself; the record would assert that identical "
                "bytes both are and are not authoritative",
            )
        if not isinstance(self.severity, Severity):
            raise ContractViolation(
                "/severity",
                f"severity must be a Severity, got {type(self.severity).__name__}",
            )
        if not isinstance(self.reason, str) or not self.reason:
            raise ContractViolation(
                "/reason",
                "reason must be given; an unexplained supersession cannot be assessed by "
                "anyone who did not make it",
            )
        if not isinstance(self.effective_date, Timestamp):
            raise ContractViolation(
                "/effective_date",
                f"effective_date must be a Timestamp, got "
                f"{type(self.effective_date).__name__}",
            )
        if not isinstance(self.discovered_by, RunId):
            raise ContractViolation(
                "/discovered_by",
                f"discovered_by must be a RunId, got {type(self.discovered_by).__name__}. "
                f"The provenance of the finding is part of the finding.",
            )

    @property
    def fails_the_build(self) -> bool:
        """True for a RETRACTION (STD-22, ADR-0024 §3).

        A retraction anywhere in a Claim's provenance DAG fails the build. CORRECTION and
        DEPRECATION render a notice instead: they change what a reader should conclude, not
        whether the page may exist.
        """
        return self.severity is Severity.RETRACTION

    def to_dict(self) -> dict[str, object]:
        return {
            "superseded": str(self.superseded),
            "superseding": None if self.superseding is None else str(self.superseding),
            "severity": self.severity.value,
            "reason": self.reason,
            "effective_date": str(self.effective_date),
            "discovered_by": str(self.discovered_by),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Supersession:
        superseding = data["superseding"]
        return cls(
            superseded=Digest(data["superseded"]),               # type: ignore[arg-type]
            superseding=None if superseding is None else Digest(superseding),  # type: ignore[arg-type]
            severity=Severity(data["severity"]),
            reason=data["reason"],                               # type: ignore[arg-type]
            effective_date=Timestamp(data["effective_date"]),    # type: ignore[arg-type]
            discovered_by=RunId(data["discovered_by"]),          # type: ignore[arg-type]
        )

"""The append-only provenance store. The only code in this package that writes.

LAYOUT. Everything is content-addressed, so a name IS a digest:

    <root>/artifacts/<digest>.json    registration: digest + size
    <root>/records/<digest>.json      a ProvenanceRecord

Append-only falls out of that rather than being enforced on top of it. Identical content
hashes to an identical name, so re-writing a fact is a no-op; different content cannot reach
an existing name because the name is derived from the content. There is no update path and
no delete path, and their absence is the mechanism, not an oversight.

WRITE CONFINEMENT (TIS E3 §13). Every path is resolved and checked to lie beneath the store
root before it is opened. A digest is validated hex, so it cannot contain a separator — but
the check does not rely on that, because relying on an upstream validator for a filesystem
boundary is how directory traversal happens.

VERIFY ON READ. A record is re-digested when loaded and compared against the name it was
stored under. A store whose contents were edited in place is exactly the situation an
integrity system exists to detect, and detecting it costs one hash of a small file.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

from kernel.provenance.artifact import Artifact
from kernel.provenance.dag import ancestors as _ancestors
from kernel.provenance.dag import would_create_cycle
from kernel.provenance.digest import Digest, digest_bytes, digest_file
from kernel.provenance.errors import IntegrityFailure, ProvenanceFailure
from kernel.provenance.record import ProvenanceRecord
from kernel.provenance.run import Run

logger = logging.getLogger("kernel.provenance")

_ARTIFACTS = "artifacts"
_RECORDS = "records"


class ProvenanceStore:
    """A store rooted at a directory.

    The root is a constructor parameter rather than a module constant because tests need a
    temporary directory and production needs a real one. That is evidence, not speculative
    dependency injection: there is exactly one parameter, and it exists because two callers
    demonstrably need different values.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        (self.root / _ARTIFACTS).mkdir(parents=True, exist_ok=True)
        (self.root / _RECORDS).mkdir(parents=True, exist_ok=True)

    # ── path confinement ────────────────────────────────────────────────────────

    def _path(self, kind: str, digest: Digest) -> Path:
        candidate = (self.root / kind / f"{digest.hex}.json").resolve()
        if not candidate.is_relative_to(self.root):
            raise ProvenanceFailure(
                f"refusing to write outside the store root: {candidate}"
            )
        return candidate

    # ── artifacts ───────────────────────────────────────────────────────────────

    def put_bytes(self, data: bytes) -> Artifact:
        """Register an in-memory byte sequence."""
        return self._register(Artifact(digest=digest_bytes(data), size_bytes=len(data)))

    def put_file(self, path: Path) -> Artifact:
        """Register a file on disk, digested without being loaded into memory."""
        return self._register(
            Artifact(digest=digest_file(path), size_bytes=path.stat().st_size)
        )

    def _register(self, artifact: Artifact) -> Artifact:
        target = self._path(_ARTIFACTS, artifact.digest)
        payload = json.dumps(
            {"digest": artifact.digest.hex, "size_bytes": artifact.size_bytes},
            indent=2,
            sort_keys=True,
        )

        if target.exists():
            # Same digest, so same bytes, so same size. A disagreement means the store was
            # edited outside this code path.
            existing = json.loads(target.read_text())
            if existing["size_bytes"] != artifact.size_bytes:
                raise IntegrityFailure(
                    f"artifact {artifact.digest.short} is registered with size "
                    f"{existing['size_bytes']} but was offered as {artifact.size_bytes}"
                )
            return artifact

        target.write_text(payload)
        logger.info(
            "artifact registered",
            extra={"context": "provenance", "event": "artifact.registered",
                   "artifact_digest": artifact.digest.short},
        )
        return artifact

    def has_artifact(self, digest: Digest) -> bool:
        return self._path(_ARTIFACTS, digest).exists()

    def get_artifact(self, digest: Digest) -> Artifact:
        target = self._path(_ARTIFACTS, digest)
        if not target.exists():
            raise ProvenanceFailure(f"artifact {digest.short} is not registered")
        raw = json.loads(target.read_text())
        return Artifact(digest=Digest(raw["digest"]), size_bytes=raw["size_bytes"])

    # ── records ─────────────────────────────────────────────────────────────────

    def record(
        self, run: Run, inputs: Iterable[Digest], outputs: Iterable[Digest]
    ) -> ProvenanceRecord:
        """Record that `run` consumed `inputs` and produced `outputs`.

        Both validations below are soundness conditions, not hygiene:

        - Every input must already be registered. An unregistered input is a claim about
          bytes the store has never seen, which makes the chain unwalkable at exactly the
          point an auditor would follow it (VVMP §7, step 12).
        - The record must not close a cycle, or ancestry stops terminating.
        """
        input_tuple = tuple(inputs)
        output_tuple = tuple(outputs)

        for digest in input_tuple:
            if not self.has_artifact(digest):
                raise ProvenanceFailure(
                    f"input {digest.short} is not a registered artifact"
                )

        if would_create_cycle(input_tuple, output_tuple, self.records()):
            raise ProvenanceFailure(
                "recording these inputs and outputs would close a cycle in the "
                "provenance graph"
            )

        record = ProvenanceRecord(
            run_id=run.run_id, inputs=input_tuple, outputs=output_tuple
        )
        target = self._path(_RECORDS, record.digest)

        if not target.exists():
            target.write_text(record.to_json())
            logger.info(
                "provenance recorded",
                extra={"context": "provenance", "event": "record.written",
                       "run_id": run.run_id, "artifact_digest": record.digest.short},
            )

        return record

    def get_record(self, digest: Digest) -> ProvenanceRecord:
        target = self._path(_RECORDS, digest)
        if not target.exists():
            raise ProvenanceFailure(f"record {digest.short} does not exist")

        text = target.read_text()
        record = ProvenanceRecord.from_json(text)
        if record.digest != digest:
            raise IntegrityFailure(
                f"record stored as {digest.short} hashes to {record.digest.short}; "
                f"the store has been modified outside this package"
            )
        return record

    def records(self) -> Iterator[ProvenanceRecord]:
        """Every record in the store, verified on read.

        Sorted by filename so iteration order is deterministic. A scan is correct at any
        size and an index is an optimisation; STD-20 forbids adding one without a
        measurement showing it is needed.
        """
        for path in sorted((self.root / _RECORDS).glob("*.json")):
            if path.name.startswith("._"):
                continue
            yield self.get_record(Digest(path.stem))

    # ── traversal ───────────────────────────────────────────────────────────────

    def ancestors(self, digest: Digest) -> frozenset[Digest]:
        """Every digest reachable upstream of `digest`, exclusive of itself."""
        return _ancestors(digest, list(self.records()))

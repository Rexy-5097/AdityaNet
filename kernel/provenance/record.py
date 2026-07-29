"""ProvenanceRecord — how an Artifact came to exist.

A record states: this Run consumed these input digests and produced these output digests.
Records chained by digest form the DAG that answers the only question this kernel exists to
answer — where did a published number come from.

THE RECORD IS ITSELF CONTENT-ADDRESSED. Its digest is computed over a canonical
serialisation with sorted inputs and outputs, so that the same claim always produces the
same record identity regardless of the order a caller happened to pass things in. Without
that, two identical records would occupy two names and the store would stop being
append-only in any meaningful sense.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from kernel.provenance.digest import Digest, digest_bytes


@dataclass(frozen=True)
class ProvenanceRecord:
    """Immutable. Append-only: a recorded fact is never revised (TIS E3 §11)."""

    run_id: str
    inputs: tuple[Digest, ...]
    outputs: tuple[Digest, ...]

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("a record must name the run that produced it")
        if not self.outputs:
            raise ValueError("a record with no outputs records nothing")
        if len(set(self.outputs)) != len(self.outputs):
            raise ValueError("outputs contain a duplicate digest")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError("inputs contain a duplicate digest")

    def canonical(self) -> bytes:
        """The bytes this record is digested over.

        Sorted, separator-normalised, no whitespace. Any change to this function changes
        every record identity in existence, which is why it is defined once, here, and is
        pinned by a known-value test.
        """
        return json.dumps(
            {
                "run_id": self.run_id,
                "inputs": sorted(d.hex for d in self.inputs),
                "outputs": sorted(d.hex for d in self.outputs),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()

    @property
    def digest(self) -> Digest:
        return digest_bytes(self.canonical())

    def to_json(self) -> str:
        """Serialised form written to the store. Indented for human audit."""
        return json.dumps(
            {
                "run_id": self.run_id,
                "inputs": sorted(d.hex for d in self.inputs),
                "outputs": sorted(d.hex for d in self.outputs),
            },
            indent=2,
            sort_keys=True,
        )

    @staticmethod
    def from_json(text: str) -> "ProvenanceRecord":
        raw = json.loads(text)
        return ProvenanceRecord(
            run_id=raw["run_id"],
            inputs=tuple(Digest(h) for h in raw["inputs"]),
            outputs=tuple(Digest(h) for h in raw["outputs"]),
        )

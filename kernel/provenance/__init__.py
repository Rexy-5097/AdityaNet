"""Provenance shared kernel — the single minting authority for digests.

ADR-0026 reclassified provenance from a bounded context to a SHARED KERNEL: it is vocabulary
used by every context and has no domain behaviour of its own. Nothing here knows what a
flare, an instrument or an evaluation is, and a test enforces that.

ADR-0005 makes this package load-bearing: every immutable object in the system is identified
by the SHA-256 of its content, and this is the only code permitted to compute one. One
implementation, one place to audit.

IMPORT RULE. TIS E3 §11 states the kernel imports "no internal package, no third party".
ADR-0026's shorthand is "imports nothing", which read literally would forbid `hashlib` and
so make ADR-0005 unimplementable; the TIS wording is the precise one and is what the test
encodes. The standard library is permitted. Sibling modules within this package are
permitted — TIS E3 §5 specifies them by name.

Public interface (TIS E3 §4):

    digest_bytes / digest_file / digest_stream / digest_chunks   mint a Digest
    begin_run / Run.end                                          bracket an execution
    ProvenanceStore.put_bytes / put_file                         register an Artifact
    ProvenanceStore.record                                       record a derivation
    ProvenanceStore.ancestors                                    walk the graph upstream
"""

from kernel.provenance.artifact import Artifact
from kernel.provenance.dag import ancestors, producers, would_create_cycle
from kernel.provenance.digest import (
    CHUNK_BYTES,
    Digest,
    digest_bytes,
    digest_chunks,
    digest_file,
    digest_stream,
)
from kernel.provenance.errors import IntegrityFailure, KernelError, ProvenanceFailure
from kernel.provenance.record import ProvenanceRecord
from kernel.provenance.run import Run, RunStatus, begin_run, new_run_id
from kernel.provenance.store import ProvenanceStore

__all__ = [
    "Artifact",
    "CHUNK_BYTES",
    "Digest",
    "IntegrityFailure",
    "KernelError",
    "ProvenanceFailure",
    "ProvenanceRecord",
    "ProvenanceStore",
    "Run",
    "RunStatus",
    "ancestors",
    "begin_run",
    "digest_bytes",
    "digest_chunks",
    "digest_file",
    "digest_stream",
    "new_run_id",
    "producers",
    "would_create_cycle",
]

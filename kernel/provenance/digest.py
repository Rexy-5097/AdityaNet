"""Content addressing. The only place in the system that mints a digest.

ADR-0005: every immutable object is identified by the SHA-256 of its content. Sequential
and timestamp identifiers are forbidden for immutables, because they do not establish that
two references denote the same bytes.

STREAMING IS NOT AN OPTIMISATION HERE. Tier 0 source archives run to ~21 GB (ADR-0023), and
TIS E3 §12 forbids buffering them. `digest_file` therefore reads in fixed chunks and never
materialises a whole file. `digest_bytes` exists for in-memory values and is defined to
produce an identical result for identical content — a property the tests pin, because two
code paths producing two digests for one byte sequence would silently split the graph.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Iterable

# 64 KiB. Large enough that syscall overhead is irrelevant, small enough that peak memory is
# bounded regardless of input size. STD-20 forbids tuning this without a measurement.
CHUNK_BYTES = 64 * 1024

_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True, order=True)
class Digest:
    """A SHA-256 content digest, lower-case hex.

    Frozen and ordered so that digests can be used as dict keys, placed in sets, and sorted
    deterministically — sorting matters because a record's inputs must serialise in a stable
    order or the record's own digest would depend on insertion order.
    """

    hex: str

    def __post_init__(self) -> None:
        if len(self.hex) != 64:
            raise ValueError(f"digest must be 64 hex characters, got {len(self.hex)}")
        if not _HEX.issuperset(self.hex):
            raise ValueError("digest must be lower-case hexadecimal")

    @property
    def short(self) -> str:
        """First 12 characters. For logs only — never for identity (STD-14)."""
        return self.hex[:12]

    def __str__(self) -> str:
        return self.hex


def digest_bytes(data: bytes) -> Digest:
    """Digest an in-memory byte sequence."""
    return Digest(hashlib.sha256(data).hexdigest())


def digest_chunks(chunks: Iterable[bytes]) -> Digest:
    """Digest a stream of chunks.

    Chunk boundaries do not affect the result — SHA-256 is defined over the byte sequence,
    not over how it was delivered. A property test pins this, because a digest that varied
    with read size would make every file's identity depend on the reader.
    """
    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk)
    return Digest(hasher.hexdigest())


def digest_stream(stream: IO[bytes]) -> Digest:
    """Digest an open binary stream without materialising it."""
    hasher = hashlib.sha256()
    while True:
        chunk = stream.read(CHUNK_BYTES)
        if not chunk:
            break
        hasher.update(chunk)
    return Digest(hasher.hexdigest())


def digest_file(path: Path) -> Digest:
    """Digest a file on disk without loading it into memory."""
    with path.open("rb") as handle:
        return digest_stream(handle)

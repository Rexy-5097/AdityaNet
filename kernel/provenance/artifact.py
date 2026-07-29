"""Artifact — an immutable byte sequence, identified by its content digest.

The atom of the system: every other immutable object either is an Artifact or references
one by digest (TIS Part 1). An Artifact carries no name, no path and no media type, because
none of those are properties of the bytes — the same bytes acquired from two sources are one
Artifact, and conflating identity with location is how a content-addressed store stops being
content-addressed.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.provenance.digest import Digest


@dataclass(frozen=True)
class Artifact:
    """Immutable. Equality and hashing are by digest alone."""

    digest: Digest
    size_bytes: int

    def __post_init__(self) -> None:
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")

    def __str__(self) -> str:
        return f"{self.digest.short}({self.size_bytes}B)"

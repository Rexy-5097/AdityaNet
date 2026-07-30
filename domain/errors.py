"""The domain's single failure class.

TIS §0.2 fixes the failure taxonomy for every context and permits no others and no
catch-all. E4 §8 names this epic's member of that taxonomy: `ContractViolation`, raised when
input fails its schema or an invariant.

E4 §15 adds the requirement that makes it useful: the violation carries the JSON Pointer of
the failing field. A message reading "invalid observation" tells a caller nothing it can act
on; `/ingest_time` tells it exactly which field to look at, in the same address space the
JSON Schema uses (RFC 6901). The pointer is therefore not decoration — it is the mechanism by
which a schema failure and a domain failure describe the same defect the same way.

TIS §0.2 forbids coercion of malformed input universally (STD-13). Nothing here repairs a
value, substitutes a default, or downgrades an error to a warning.
"""

from __future__ import annotations


class DomainError(Exception):
    """Root of the domain's error hierarchy.

    Exists so that a caller can catch everything this package raises without resorting to a
    bare `except`, which TIS §0.2 forbids universally.
    """


class ContractViolation(DomainError):
    """Input fails its schema or an invariant. Abort; never coerce (STD-13).

    `pointer` is an RFC 6901 JSON Pointer naming the failing field, relative to the object
    being constructed or checked. The empty string denotes the whole document, which is
    correct for a violation that is a property of the object rather than of one field — a
    Score whose interval excludes its own value, for instance, has no single field at fault.
    """

    def __init__(self, pointer: str, message: str) -> None:
        self.pointer = pointer
        self.message = message
        super().__init__(f"{pointer or '/'}: {message}")

    def __repr__(self) -> str:
        return f"ContractViolation(pointer={self.pointer!r}, message={self.message!r})"

"""`Digest` — a content address, held but never minted.

ADR-0005 states that every immutable object is identified by the SHA-256 of its content, and
that digests are minted by the provenance shared kernel **and by nothing else**. ADR-0026
states that `domain/` imports the standard library only, which means it cannot import the
kernel.

Both hold at once because holding a digest and minting one are different operations. This
type validates the *form* of a content address — 64 lower-case hex characters — so that an
entity cannot be constructed carrying something that is not one. It computes nothing. There
is deliberately no constructor here that takes bytes: `hashlib` is standard library and would
import cleanly, so the absence of a hashing function is a decision, not a limitation, and
`test_digest_cannot_mint` pins it.

WHY THIS IS NOT A DUPLICATE OF `kernel.provenance.Digest`
---------------------------------------------------------
The kernel's `Digest` is the *output* of the minting authority and travels with the functions
that produce it. This one is the *input* vocabulary of a pure domain that is forbidden from
importing that authority. ADR-0019 warns against a shared package that launders dependency
cycles; the alternative here — letting `domain/` import `kernel/` — is precisely the
dependency edge ADR-0026 forbids. Two 64-hex validators is the smaller cost, and the boundary
test in E4 §11(i) is what keeps them from becoming one by accident.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation

HEX_LENGTH = 64
_HEX_DIGITS = frozenset("0123456789abcdef")


@dataclass(frozen=True, order=True)
class Digest:
    """A SHA-256 content address in lower-case hexadecimal.

    Frozen and ordered so digests can key a dict, enter a set, and sort deterministically.
    Sorting is load-bearing wherever a derived digest is computed over a collection of
    digests: an unstable order would make the derived identity depend on insertion order.
    """

    hex: str

    def __post_init__(self) -> None:
        if not isinstance(self.hex, str):
            raise ContractViolation("", f"digest must be a string, got {type(self.hex).__name__}")
        if len(self.hex) != HEX_LENGTH:
            raise ContractViolation(
                "", f"digest must be {HEX_LENGTH} hex characters, got {len(self.hex)}"
            )
        if not _HEX_DIGITS.issuperset(self.hex):
            # Upper-case hex is rejected rather than lowered. Two spellings of one digest
            # would compare unequal while addressing identical bytes, and coercing the input
            # would violate STD-13.
            raise ContractViolation("", "digest must be lower-case hexadecimal")

    @property
    def short(self) -> str:
        """First 12 characters, for logs only — never for identity (STD-14)."""
        return self.hex[:12]

    def __str__(self) -> str:
        return self.hex

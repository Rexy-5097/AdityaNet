"""`Identifier` and `RunId` — the two name forms the contracts admit.

ADR-0005 divides the world in two. Immutable objects are addressed by digest. *Mutable
names* — Dataset, Method, Source, Instrument, LabelSource — may carry conventional
identifiers precisely because an Evaluation never references them. These are those
identifiers, and the type exists so that the distinction is visible in a signature: a
parameter typed `Digest` cannot receive a name, and a parameter typed `Identifier` cannot
receive a digest.

The permitted shape is `^[a-z0-9][a-z0-9_-]*$`, matching `common.schema.json#/$defs/
instrument_id` exactly. Lower-case only, because a name that differs from another only by
case reads as the same name to a human and as a different one to a dict.

`RunId` is separate rather than a looser `Identifier` because a ULID is not a name: it is
minted by the kernel, it is 26 Crockford Base32 characters, and it excludes I, L, O and U so
a transcribed id cannot be misread. Accepting it as an `Identifier` would let any slug stand
where a run must be named.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation

MAX_IDENTIFIER_LENGTH = 64

_LOWER_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyz0123456789")
_IDENTIFIER_BODY = _LOWER_ALNUM | {"_", "-"}

RUN_ID_LENGTH = 26
# Crockford Base32: the full alphabet less I, L, O and U.
_CROCKFORD = frozenset("0123456789ABCDEFGHJKMNPQRSTVWXYZ")


@dataclass(frozen=True, order=True)
class Identifier:
    """A mutable name (ADR-0005). Never a substitute for a content address."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ContractViolation(
                "", f"identifier must be a string, got {type(self.value).__name__}"
            )
        if not self.value:
            raise ContractViolation("", "identifier must not be empty")
        if len(self.value) > MAX_IDENTIFIER_LENGTH:
            raise ContractViolation(
                "", f"identifier must be at most {MAX_IDENTIFIER_LENGTH} characters, "
                f"got {len(self.value)}"
            )
        if self.value[0] not in _LOWER_ALNUM:
            # A leading separator is rejected so that a name cannot sort ahead of every
            # other name by accident, and so `-x` cannot be mistaken for a command flag.
            raise ContractViolation(
                "", "identifier must begin with a lower-case letter or digit"
            )
        if not _IDENTIFIER_BODY.issuperset(self.value):
            raise ContractViolation(
                "", "identifier may contain only lower-case letters, digits, '_' and '-'"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class RunId:
    """A ULID naming one execution, minted by the kernel and validated here."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ContractViolation(
                "", f"run id must be a string, got {type(self.value).__name__}"
            )
        if len(self.value) != RUN_ID_LENGTH:
            raise ContractViolation(
                "", f"run id must be {RUN_ID_LENGTH} characters, got {len(self.value)}"
            )
        if not _CROCKFORD.issuperset(self.value):
            raise ContractViolation(
                "", "run id must be upper-case Crockford Base32 (no I, L, O or U)"
            )

    def __str__(self) -> str:
        return self.value

"""`Observation` — one measured quantity, bitemporal by construction.

Mirrors `contracts/observation.schema.json`. Two of its fields carry the architecture's most
consequential decisions, and both are enforced here by the *shape of the type* rather than by
a check a caller could skip.

`ingest_time` HAS NO DEFAULT
----------------------------
ADR-0022 makes it nullable with exactly one meaning — *unknown; this observation predates
bitemporal capture* — and states it is never fabricated, defaulted, or inferred. A dataclass
field written `ingest_time: Timestamp | None = None` would violate that in the most literal
way available: a caller who simply omitted the argument would receive `None`, which is to say
the system would *default* a provenance value. So the field is required with no default, and
`test_observation_cannot_be_constructed_without_ingest_time` pins it. Omitting it raises
`TypeError` from Python itself, which is the strongest enforcement available and costs
nothing.

This is the same reasoning the contract records: the field is `required` in JSON Schema *and*
nullable, so absence and unknown cannot be confused.

`value` IS NULLABLE AND NEVER FILLED
------------------------------------
`None` means observed to be absent. ADR-0017 and STD-04 forbid fill, interpolation,
zero-substitution and forward-fill on every path. Zero-substitution is the one worth naming
twice: zero is a valid count rate, so a zero-filled gap is indistinguishable from a real
quiet-Sun measurement, and the error is undetectable downstream (L-07).
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.digest import Digest
from domain.values.identifier import Identifier
from domain.values.numeric import finite
from domain.values.timestamp import Timestamp


@dataclass(frozen=True)
class Observation:
    """One physical measurement (ADR-0002: never called a Measurement)."""

    source_id: Identifier
    instrument_id: Identifier
    quantity: str
    unit: str
    valid_time: Timestamp
    #: No default, deliberately — see the module docstring.
    ingest_time: Timestamp | None
    value: float | None
    source_digest: Digest
    quality_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("source_id", "instrument_id"):
            if not isinstance(getattr(self, name), Identifier):
                raise ContractViolation(
                    f"/{name}",
                    f"{name} must be an Identifier, got {type(getattr(self, name)).__name__}",
                )
        for name in ("quantity", "unit"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")

        if not isinstance(self.valid_time, Timestamp):
            raise ContractViolation(
                "/valid_time",
                f"valid_time must be a Timestamp, got {type(self.valid_time).__name__}. "
                f"It is always known (ADR-0004) and so is never null.",
            )
        if self.ingest_time is not None and not isinstance(self.ingest_time, Timestamp):
            raise ContractViolation(
                "/ingest_time",
                f"ingest_time must be a Timestamp or None, got "
                f"{type(self.ingest_time).__name__}. None means exactly one thing: unknown, "
                f"predates bitemporal capture (ADR-0022).",
            )
        if self.value is not None:
            object.__setattr__(self, "value", finite(self.value, "/value", "value"))

        if not isinstance(self.source_digest, Digest):
            raise ContractViolation(
                "/source_digest",
                f"source_digest must be a Digest, got {type(self.source_digest).__name__}. "
                f"Provenance is a column, not a document.",
            )

        flags = self.quality_flags
        if not isinstance(flags, tuple):
            # A list would be mutable, and a frozen entity holding a mutable member is
            # frozen in name only.
            raise ContractViolation(
                "/quality_flags",
                f"quality_flags must be a tuple, got {type(flags).__name__}",
            )
        if any(not isinstance(f, str) or not f for f in flags):
            raise ContractViolation(
                "/quality_flags", "every quality flag must be a non-empty string"
            )
        if len(set(flags)) != len(flags):
            raise ContractViolation(
                "/quality_flags", "quality flags must be unique"
            )

    @property
    def ingest_time_is_unknown(self) -> bool:
        """True where `ingest_time` is null — the one meaning ADR-0022 assigns it."""
        return self.ingest_time is None

    @property
    def value_is_absent(self) -> bool:
        """True where the quantity was observed to be absent. Never means zero (L-07)."""
        return self.value is None

    def to_dict(self) -> dict[str, object]:
        """Serialise to exactly `observation.schema.json`'s shape.

        `quality_flags` is emitted only when non-empty: the schema gives it a default of
        `[]`, so emitting an empty list would write out a value the contract already implies.
        """
        data: dict[str, object] = {
            "source_id": str(self.source_id),
            "instrument_id": str(self.instrument_id),
            "quantity": self.quantity,
            "unit": self.unit,
            "valid_time": str(self.valid_time),
            "ingest_time": None if self.ingest_time is None else str(self.ingest_time),
            "value": self.value,
            "source_digest": str(self.source_digest),
        }
        if self.quality_flags:
            data["quality_flags"] = list(self.quality_flags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Observation:
        ingest = data["ingest_time"]
        return cls(
            source_id=Identifier(data["source_id"]),          # type: ignore[arg-type]
            instrument_id=Identifier(data["instrument_id"]),  # type: ignore[arg-type]
            quantity=data["quantity"],                        # type: ignore[arg-type]
            unit=data["unit"],                                # type: ignore[arg-type]
            valid_time=Timestamp(data["valid_time"]),         # type: ignore[arg-type]
            ingest_time=None if ingest is None else Timestamp(ingest),  # type: ignore[arg-type]
            value=data["value"],                              # type: ignore[arg-type]
            source_digest=Digest(data["source_digest"]),      # type: ignore[arg-type]
            quality_flags=tuple(data.get("quality_flags", ())),  # type: ignore[arg-type]
        )

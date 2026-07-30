"""`Protocol` — the pre-registered evaluation specification.

ADR-0008 makes a Protocol immutable and content-addressed for one reason: pre-registration is
meaningless if the protocol is editable prose. A protocol that can be adjusted after seeing a
result is a description of the result.

Three fields here decide what a downstream claim is allowed to mean.

`requires_bitemporal` (ADR-0022) selects which of two guarantees is in force. `true` excludes
observations whose `ingest_time` is unknown, so the leakage gate is enforceable *by
construction*. `false` admits them, and the resulting Evaluation must record
`leakage_gate_applied = false` so a reader can see which guarantee applied rather than
assuming the stronger one.

`tolerance` (ADR-0021) is the absolute agreement required for reproduction class EQUIVALENT —
same five inputs, different platform. A tolerance of zero demands bit-identity and so admits
only EXACT. It is required rather than defaulted because a default would silently decide how
much disagreement counts as reproduction.

`exchangeable_unit` (L-01) records what the uncertainty estimator resamples. Flares span many
minutes, so minutes are not independent and the row count is not the sample size. An interval
resampled over the wrong unit is narrower than the truth, which is the direction that flatters
a result.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.digest import Digest
from domain.values.enums import SplitStrategy
from domain.values.identifier import Identifier
from domain.values.numeric import finite
from domain.values.timestamp import Timestamp


@dataclass(frozen=True)
class Splits:
    """How a Protocol divides time.

    Only chronological splitting is permitted: a shuffled split would let a future minute
    inform a past one, and the resulting score would measure interpolation rather than
    detection.
    """

    strategy: SplitStrategy
    test_start: Timestamp
    val_fraction: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.strategy, SplitStrategy):
            raise ContractViolation(
                "/strategy",
                f"strategy must be a SplitStrategy, got {type(self.strategy).__name__}",
            )
        if not isinstance(self.test_start, Timestamp):
            raise ContractViolation(
                "/test_start",
                f"test_start must be a Timestamp, got {type(self.test_start).__name__}",
            )
        if self.val_fraction is not None:
            fraction = finite(self.val_fraction, "/val_fraction", "val_fraction")
            if not 0 <= fraction < 1:
                raise ContractViolation(
                    "/val_fraction",
                    f"val_fraction must lie in [0, 1), got {fraction}. A fraction of 1 would "
                    f"leave no training data.",
                )
            object.__setattr__(self, "val_fraction", fraction)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "strategy": self.strategy.value,
            "test_start": str(self.test_start),
        }
        if self.val_fraction is not None:
            data["val_fraction"] = self.val_fraction
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Splits:
        return cls(
            strategy=SplitStrategy(data["strategy"]),
            test_start=Timestamp(data["test_start"]),  # type: ignore[arg-type]
            val_fraction=data.get("val_fraction"),     # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Protocol:
    """An immutable, pre-registered evaluation specification (ADR-0008)."""

    protocol_id: Identifier
    digest: Digest
    task: str
    splits: Splits
    metrics: tuple[str, ...]
    uncertainty_estimator: str
    exchangeable_unit: str
    permitted_instruments: tuple[Identifier, ...]
    label_source_id: Identifier
    requires_bitemporal: bool
    tolerance: float
    operating_points: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_id, Identifier):
            raise ContractViolation(
                "/protocol_id",
                f"protocol_id must be an Identifier, got {type(self.protocol_id).__name__}",
            )
        if not isinstance(self.digest, Digest):
            raise ContractViolation(
                "/digest", f"digest must be a Digest, got {type(self.digest).__name__}"
            )
        if not isinstance(self.splits, Splits):
            raise ContractViolation(
                "/splits", f"splits must be a Splits, got {type(self.splits).__name__}"
            )
        if not isinstance(self.label_source_id, Identifier):
            raise ContractViolation(
                "/label_source_id",
                f"label_source_id must be an Identifier, got "
                f"{type(self.label_source_id).__name__}",
            )
        for name in ("task", "uncertainty_estimator", "exchangeable_unit"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"/{name}", f"{name} must be a non-empty string")

        if not isinstance(self.metrics, tuple) or not self.metrics:
            raise ContractViolation(
                "/metrics", "at least one metric must be named; a protocol scoring nothing "
                "specifies nothing"
            )
        if any(not isinstance(m, str) or not m for m in self.metrics):
            raise ContractViolation("/metrics", "every metric must be a non-empty string")
        if len(set(self.metrics)) != len(self.metrics):
            raise ContractViolation("/metrics", "metrics must be unique")

        if not isinstance(self.permitted_instruments, tuple) or not self.permitted_instruments:
            raise ContractViolation(
                "/permitted_instruments",
                "at least one instrument must be permitted; an empty set would refuse every "
                "method rather than permitting every one, and either reading would be a guess",
            )
        if any(not isinstance(i, Identifier) for i in self.permitted_instruments):
            raise ContractViolation(
                "/permitted_instruments", "every permitted instrument must be an Identifier"
            )
        if len(set(self.permitted_instruments)) != len(self.permitted_instruments):
            raise ContractViolation(
                "/permitted_instruments", "permitted instruments must be unique"
            )

        if not isinstance(self.requires_bitemporal, bool):
            raise ContractViolation(
                "/requires_bitemporal",
                f"requires_bitemporal must be a bool, got "
                f"{type(self.requires_bitemporal).__name__}. It selects which leakage "
                f"guarantee is in force (ADR-0022), so it may not be absent or truthy.",
            )
        tolerance = finite(self.tolerance, "/tolerance", "tolerance")
        if tolerance < 0:
            raise ContractViolation(
                "/tolerance", f"tolerance must be non-negative, got {tolerance}"
            )
        object.__setattr__(self, "tolerance", tolerance)

        if not isinstance(self.operating_points, tuple):
            raise ContractViolation(
                "/operating_points",
                f"operating_points must be a tuple, got "
                f"{type(self.operating_points).__name__}",
            )
        object.__setattr__(
            self,
            "operating_points",
            tuple(
                finite(p, f"/operating_points/{n}", "operating point")
                for n, p in enumerate(self.operating_points)
            ),
        )

    def permits(self, instrument: Identifier) -> bool:
        return instrument in self.permitted_instruments

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "protocol_id": str(self.protocol_id),
            "digest": str(self.digest),
            "task": self.task,
            "splits": self.splits.to_dict(),
            "metrics": list(self.metrics),
            "uncertainty_estimator": self.uncertainty_estimator,
            "exchangeable_unit": self.exchangeable_unit,
            "permitted_instruments": [str(i) for i in self.permitted_instruments],
            "label_source_id": str(self.label_source_id),
            "requires_bitemporal": self.requires_bitemporal,
            "tolerance": self.tolerance,
        }
        if self.operating_points:
            data["operating_points"] = list(self.operating_points)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Protocol:
        return cls(
            protocol_id=Identifier(data["protocol_id"]),   # type: ignore[arg-type]
            digest=Digest(data["digest"]),                 # type: ignore[arg-type]
            task=data["task"],                             # type: ignore[arg-type]
            splits=Splits.from_dict(data["splits"]),       # type: ignore[arg-type]
            metrics=tuple(data["metrics"]),                # type: ignore[arg-type]
            uncertainty_estimator=data["uncertainty_estimator"],  # type: ignore[arg-type]
            exchangeable_unit=data["exchangeable_unit"],   # type: ignore[arg-type]
            permitted_instruments=tuple(
                Identifier(i) for i in data["permitted_instruments"]  # type: ignore[union-attr]
            ),
            label_source_id=Identifier(data["label_source_id"]),  # type: ignore[arg-type]
            requires_bitemporal=data["requires_bitemporal"],      # type: ignore[arg-type]
            tolerance=data["tolerance"],                          # type: ignore[arg-type]
            operating_points=tuple(data.get("operating_points", ())),  # type: ignore[arg-type]
        )

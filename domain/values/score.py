"""`Interval` and `Score` — a number may not travel without its uncertainty.

ADR-0002 classifies both as value objects: `Uncertainty` was rejected as an entity and is an
`Interval`, and a `Score` has no identity of its own — it is a component of the Evaluation
that produced it.

`Score.interval` is required, not optional. STD-05 exists because a bare number in a
publication is the failure this platform was built to refuse, and the enforcement point is
here: if the type cannot represent a score without an interval, no code path can produce one.
The same reasoning makes `denominator` required — a rate whose denominator is unknown cannot
be weighed against another rate, so "0.87" alone is not a result.

`Interval.estimator` and `Interval.exchangeable_unit` are required for a reason specific to
this domain. Flares span many minutes, so minutes are not independent (L-01): an interval
resampled over minutes says something different from one resampled over events, and without
the unit recorded a reader cannot tell which was done.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.numeric import finite


@dataclass(frozen=True)
class Interval:
    """An uncertainty interval with the estimator and unit that produced it."""

    lower: float
    upper: float
    level: float
    estimator: str
    exchangeable_unit: str

    def __post_init__(self) -> None:
        lower = finite(self.lower, "/lower", "lower")
        upper = finite(self.upper, "/upper", "upper")
        level = finite(self.level, "/level", "level")

        if lower > upper:
            raise ContractViolation(
                "", f"interval lower {lower} exceeds upper {upper}"
            )
        if not 0 < level < 1:
            # Matches the contract's exclusiveMinimum/exclusiveMaximum. A level of 0 or 1
            # describes an interval that is either empty or certain, and neither is a
            # confidence level.
            raise ContractViolation(
                "/level", f"level must lie strictly between 0 and 1, got {level}"
            )
        if not self.estimator:
            raise ContractViolation(
                "/estimator", "estimator must be named — an interval without one is "
                "uninterpretable"
            )
        if not self.exchangeable_unit:
            raise ContractViolation(
                "/exchangeable_unit",
                "exchangeable_unit must be named — the row count is not the sample size "
                "(L-01)",
            )
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        object.__setattr__(self, "level", level)

    @property
    def width(self) -> float:
        return self.upper - self.lower

    def contains(self, value: float) -> bool:
        """Inclusive of both bounds: a point estimate equal to a bound is inside it."""
        return self.lower <= value <= self.upper

    def to_dict(self) -> dict[str, object]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "level": self.level,
            "estimator": self.estimator,
            "exchangeable_unit": self.exchangeable_unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Interval:
        return cls(
            lower=data["lower"],          # type: ignore[arg-type]
            upper=data["upper"],          # type: ignore[arg-type]
            level=data["level"],          # type: ignore[arg-type]
            estimator=data["estimator"],  # type: ignore[arg-type]
            exchangeable_unit=data["exchangeable_unit"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Score:
    """One metric, its value, its uncertainty and what it was computed over."""

    metric: str
    value: float
    interval: Interval
    denominator: int

    def __post_init__(self) -> None:
        if not self.metric:
            raise ContractViolation("/metric", "metric must be named")
        value = finite(self.value, "/value", "value")

        if not isinstance(self.interval, Interval):
            raise ContractViolation(
                "/interval",
                f"interval must be an Interval, got {type(self.interval).__name__}. A score "
                f"without its uncertainty is the figure STD-05 refuses.",
            )
        if isinstance(self.denominator, bool) or not isinstance(self.denominator, int):
            raise ContractViolation(
                "/denominator",
                f"denominator must be an integer, got {type(self.denominator).__name__}",
            )
        if self.denominator < 1:
            raise ContractViolation(
                "/denominator", f"denominator must be at least 1, got {self.denominator}"
            )
        object.__setattr__(self, "value", value)

    def to_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "value": self.value,
            "interval": self.interval.to_dict(),
            "denominator": self.denominator,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Score:
        return cls(
            metric=data["metric"],              # type: ignore[arg-type]
            value=data["value"],                # type: ignore[arg-type]
            interval=Interval.from_dict(data["interval"]),  # type: ignore[arg-type]
            denominator=data["denominator"],    # type: ignore[arg-type]
        )

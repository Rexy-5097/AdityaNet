"""`Evaluation` — five pinned inputs, a reproduction class, and scores that carry intervals.

ADR-0021 is the decision this type exists to make unforgettable:

    Evaluation = f(MethodRelease, DatasetRelease, LabelRelease, Protocol, EnvironmentRelease)

Five digests, all required, none defaulted. ADR-0009 (superseded) claimed four sufficed; that
claim was false, because results also depend on library versions, BLAS, thread counts and
reduction order. The type therefore cannot be constructed with four — the fifth is a
positional field like any other, and `test_evaluation_requires_all_five_inputs` drops each in
turn.

`reproduction_class` is required and there is no default (STD-21). A default would silently
decide what a result guarantees. `UNREPRODUCIBLE` is representable *and* constructible on
purpose: an evaluation with an unpinned input is a real thing that really happened, and the
architecture's response is to refuse to publish it, not to pretend it cannot exist. The
refusal lives in `domain.invariants.evaluation_is_publishable`, so that the rule is a
predicate a gate can call rather than an exception that erases the record.

`leakage_gate_applied` records whether the gate was enforceable, which depends on the
Protocol's `requires_bitemporal` (ADR-0022). The consistency of the two is a two-object rule
and so lives with the invariants, not here.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import ContractViolation
from domain.values.digest import Digest
from domain.values.enums import ReproductionClass
from domain.values.score import Score

#: The five inputs of ADR-0021, in the order the ADR states them. Exported so the invariant
#: and its tests enumerate them from one definition instead of three hand-written lists.
PINNED_INPUTS = (
    "method_release",
    "dataset_release",
    "label_release",
    "protocol",
    "environment_release",
)


@dataclass(frozen=True)
class Evaluation:
    """One scoring of one method under one protocol, in one pinned environment."""

    digest: Digest
    method_release: Digest
    dataset_release: Digest
    label_release: Digest
    protocol: Digest
    environment_release: Digest
    reproduction_class: ReproductionClass
    leakage_gate_applied: bool
    scores: tuple[Score, ...]

    def __post_init__(self) -> None:
        for name in ("digest", *PINNED_INPUTS):
            value = getattr(self, name)
            if not isinstance(value, Digest):
                raise ContractViolation(
                    f"/{name}",
                    f"{name} must be a Digest, got {type(value).__name__}. All five inputs "
                    f"of ADR-0021 are pinned by content address; an unpinned input makes the "
                    f"central invariant unenforceable.",
                )
        if not isinstance(self.reproduction_class, ReproductionClass):
            raise ContractViolation(
                "/reproduction_class",
                f"reproduction_class must be a ReproductionClass, got "
                f"{type(self.reproduction_class).__name__}. It is declared, never inferred "
                f"(STD-21).",
            )
        if not isinstance(self.leakage_gate_applied, bool):
            raise ContractViolation(
                "/leakage_gate_applied",
                f"leakage_gate_applied must be a bool, got "
                f"{type(self.leakage_gate_applied).__name__}. A reader must be able to see "
                f"which guarantee was in force rather than assume it (ADR-0022).",
            )
        if not isinstance(self.scores, tuple) or not self.scores:
            raise ContractViolation(
                "/scores", "an evaluation with no scores evaluates nothing"
            )
        if any(not isinstance(s, Score) for s in self.scores):
            raise ContractViolation("/scores", "every score must be a Score")
        metrics = [s.metric for s in self.scores]
        if len(set(metrics)) != len(metrics):
            raise ContractViolation(
                "/scores",
                f"each metric may be scored once; got duplicates in {sorted(metrics)}. Two "
                f"values for one metric leaves a reader to choose, which is not a result.",
            )

    @property
    def pinned(self) -> tuple[Digest, ...]:
        """The five input digests, in ADR-0021's order."""
        return tuple(getattr(self, name) for name in PINNED_INPUTS)

    def score_for(self, metric: str) -> Score | None:
        """The score for a metric, or `None` if this evaluation did not compute it.

        `None` here means *not computed*, and there is no other way to express it — there is
        no zero-score fallback, because a metric that was not computed is not a metric that
        scored zero (ADR-0017).
        """
        for score in self.scores:
            if score.metric == metric:
                return score
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "digest": str(self.digest),
            "method_release": str(self.method_release),
            "dataset_release": str(self.dataset_release),
            "label_release": str(self.label_release),
            "protocol": str(self.protocol),
            "environment_release": str(self.environment_release),
            "reproduction_class": self.reproduction_class.value,
            "leakage_gate_applied": self.leakage_gate_applied,
            "scores": [s.to_dict() for s in self.scores],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Evaluation:
        return cls(
            digest=Digest(data["digest"]),                            # type: ignore[arg-type]
            method_release=Digest(data["method_release"]),            # type: ignore[arg-type]
            dataset_release=Digest(data["dataset_release"]),          # type: ignore[arg-type]
            label_release=Digest(data["label_release"]),              # type: ignore[arg-type]
            protocol=Digest(data["protocol"]),                        # type: ignore[arg-type]
            environment_release=Digest(data["environment_release"]),  # type: ignore[arg-type]
            reproduction_class=ReproductionClass(data["reproduction_class"]),
            leakage_gate_applied=data["leakage_gate_applied"],        # type: ignore[arg-type]
            scores=tuple(Score.from_dict(s) for s in data["scores"]),  # type: ignore[union-attr]
        )

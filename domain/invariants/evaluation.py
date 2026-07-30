"""Invariants over Evaluations — the epic's highest-consequence rules.

Every predicate here is a rule that decides whether a number may be published, and each one
is a rule that a structurally valid `Evaluation` can still break.
"""

from __future__ import annotations

from domain.entities.evaluation import PINNED_INPUTS, Evaluation
from domain.entities.protocol import Protocol
from domain.entities.releases import MethodRelease
from domain.values.digest import Digest
from domain.values.enums import ReproductionClass


def evaluation_pins_five_inputs(evaluation: Evaluation) -> bool:
    """All five inputs of ADR-0021 are present and are content addresses.

    ADR-0009 (superseded) claimed four inputs sufficed. That was false: results also depend on
    library versions, BLAS implementation, thread count, reduction order and CPU architecture.
    An unpinned input makes the central invariant unenforceable, so this counts to five rather
    than to four and reads the names from `PINNED_INPUTS` so it cannot drift from the entity.
    """
    return len(PINNED_INPUTS) == 5 and all(
        isinstance(getattr(evaluation, name, None), Digest) for name in PINNED_INPUTS
    )


def evaluation_is_publishable(evaluation: Evaluation) -> bool:
    """False for `UNREPRODUCIBLE` (ADR-0021, STD-21).

    An evaluation with an unpinned input is a real event that really happened, so it remains
    representable and constructible; what it may not do is appear in published output. The
    rule is a predicate rather than a construction-time exception precisely so the record
    survives to be inspected — refusing to build the object would delete the evidence that
    something unpinned was run.
    """
    return evaluation.reproduction_class is not ReproductionClass.UNREPRODUCIBLE


def reproduction_class_is_consistent_with(
    evaluation: Evaluation, protocol: Protocol
) -> bool:
    """A zero-tolerance Protocol admits only `EXACT` (ADR-0021).

    `EQUIVALENT` means the five inputs match, the platform differs, and the scores agree
    within the Protocol's declared tolerance. Where that tolerance is zero, "agree within
    tolerance" is bit-identity, which is `EXACT` by definition — so a zero-tolerance protocol
    reporting `EQUIVALENT` is claiming a guarantee it has not defined.
    """
    if evaluation.reproduction_class is ReproductionClass.EQUIVALENT:
        return protocol.tolerance > 0
    return True


def leakage_gate_is_consistent_with(evaluation: Evaluation, protocol: Protocol) -> bool:
    """The recorded gate state matches the Protocol that governed the run (ADR-0022 §2).

    Where `requires_bitemporal` is false, the gate was not enforceable and the Evaluation must
    say so — `leakage_gate_applied = False`. Recording `True` there would claim a guarantee
    that was structurally unavailable, which is the precise failure ADR-0022 exists to
    prevent: a forecasting claim resting on data whose availability was never established.

    Where `requires_bitemporal` is true the gate is enforceable, and an Evaluation is free to
    record either — it may have been applied, or the run may have been made without it, and
    the record should not be able to hide which.
    """
    if not protocol.requires_bitemporal:
        return evaluation.leakage_gate_applied is False
    return True


def declared_instruments_are_permitted(
    method_release: MethodRelease, protocol: Protocol
) -> bool:
    """`declared_instruments ⊆ permitted_instruments` (ADR-0011).

    This is the comparison the v1 framework never performed. It declared exactly this metadata
    correctly and then never checked it against anything (SALVAGE-002), which meant a method
    could consume an instrument its protocol forbade and score normally. On mismatch the
    engine refuses to score and records a PolicyRejection naming the gate; this predicate is
    the condition that refusal tests.
    """
    return set(method_release.declared_instruments).issubset(
        set(protocol.permitted_instruments)
    )


def every_score_carries_its_interval(evaluation: Evaluation) -> bool:
    """No score without an uncertainty interval and a denominator (STD-05).

    The `Score` type cannot represent a value without an interval, so this predicate should be
    true by construction — and that is exactly why it is worth stating. It is the assertion
    that the structural guarantee has not been weakened, and it fails loudly if a future change
    makes `interval` optional "just for the summary table".
    """
    return all(
        score.interval is not None and score.denominator >= 1 for score in evaluation.scores
    )


def every_score_lies_within_its_interval(evaluation: Evaluation) -> bool:
    """The point estimate falls inside its own interval.

    Not enforced by `Score`'s constructor, because an `Interval` is valid in isolation and a
    value is valid in isolation — only together are they inconsistent. A point estimate
    outside its own confidence interval means the estimator and the metric were computed over
    different things, which is a defect that otherwise surfaces as a plausible-looking number.
    """
    return all(score.interval.contains(score.value) for score in evaluation.scores)

"""Every architectural invariant, as a callable predicate.

TIS E4 §4 makes `domain.invariants.*` part of this epic's public interface, and §16 requires a
property test for every invariant. `ALL_INVARIANTS` is what makes "every" mechanically
checkable: `test_every_invariant_has_a_property_test` reads this tuple and fails if a
predicate is exported without a test naming it. Adding an invariant and forgetting its test is
therefore a red build rather than a gap nobody notices.

Predicates return `bool` and never raise. A rule that raises cannot be quantified over — a
property test would stop at the first counterexample instead of characterising the rule — and
these are exactly the rules a gate needs to *ask about* before deciding to refuse. Field-level
validity is a different thing and is enforced by the types, which raise `ContractViolation` at
construction.
"""

from domain.invariants.evaluation import (
    declared_instruments_are_permitted,
    evaluation_is_publishable,
    evaluation_pins_five_inputs,
    every_score_carries_its_interval,
    every_score_lies_within_its_interval,
    leakage_gate_is_consistent_with,
    reproduction_class_is_consistent_with,
)
from domain.invariants.identity import (
    immutable_is_content_addressed,
    mutable_identity_is_permitted,
    named_entity_carries_no_digest,
)
from domain.invariants.observation import (
    absence_survives_serialisation,
    ingest_time_is_not_backfilled,
    observation_is_admissible_under,
    observation_is_wellformed,
)
from domain.invariants.standing import (
    bytes_are_never_replaced,
    chronological_boundary_is_locatable,
    retraction_fails_the_build,
    split_is_chronological,
    supersession_is_wellformed,
)

#: Every invariant predicate, paired with the decision it enforces. The citation is not
#: decoration: an invariant that cannot name the ADR, standard or limitation it comes from is
#: a preference, and STD-11 and this repository's rule against invented rules both forbid one.
ALL_INVARIANTS = (
    (observation_is_wellformed, "ADR-0004, TIS E4 §19"),
    (ingest_time_is_not_backfilled, "ADR-0022, ADR-0017, STD-04"),
    (observation_is_admissible_under, "ADR-0022 §2"),
    (absence_survives_serialisation, "ADR-0017, STD-04"),
    (evaluation_pins_five_inputs, "ADR-0021"),
    (evaluation_is_publishable, "ADR-0021, STD-21"),
    (reproduction_class_is_consistent_with, "ADR-0021"),
    (leakage_gate_is_consistent_with, "ADR-0022 §2"),
    (declared_instruments_are_permitted, "ADR-0011, SALVAGE-002"),
    (every_score_carries_its_interval, "STD-05"),
    (every_score_lies_within_its_interval, "STD-05"),
    (mutable_identity_is_permitted, "ADR-0005, TIS E4 §11(ii)"),
    (immutable_is_content_addressed, "ADR-0005, STD-02"),
    (named_entity_carries_no_digest, "ADR-0005"),
    (supersession_is_wellformed, "ADR-0024"),
    (retraction_fails_the_build, "ADR-0024 §3, STD-22"),
    (bytes_are_never_replaced, "ADR-0024 §1, STD-10"),
    (split_is_chronological, "ADR-0008"),
    (chronological_boundary_is_locatable, "ADR-0008"),
)

__all__ = [
    "ALL_INVARIANTS",
    "absence_survives_serialisation",
    "bytes_are_never_replaced",
    "chronological_boundary_is_locatable",
    "declared_instruments_are_permitted",
    "evaluation_is_publishable",
    "evaluation_pins_five_inputs",
    "every_score_carries_its_interval",
    "every_score_lies_within_its_interval",
    "immutable_is_content_addressed",
    "ingest_time_is_not_backfilled",
    "leakage_gate_is_consistent_with",
    "mutable_identity_is_permitted",
    "named_entity_carries_no_digest",
    "observation_is_admissible_under",
    "observation_is_wellformed",
    "reproduction_class_is_consistent_with",
    "retraction_fails_the_build",
    "split_is_chronological",
    "supersession_is_wellformed",
]

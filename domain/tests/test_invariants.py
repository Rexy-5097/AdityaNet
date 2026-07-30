"""Property tests for every invariant (TIS E4 §16).

WHAT "PROPERTY" MEANS HERE, EXACTLY
-----------------------------------
There is no `hypothesis` in this suite. The `unit` CI job installs `pytest` and nothing else,
and adding a generator library to exercise a package whose whole claim is that it needs no
infrastructure would be a poor trade. So each property is quantified the way the domain
permits: over the finite space the rule is defined on — the three reproduction classes, the
three severities, both settings of `requires_bitemporal`, both states of a nullable field, and
the full cross-product where two of those interact.

Where a rule ranges over an unbounded space (a numeric bound, a path), the test enumerates the
boundary and the classes of counterexample rather than sampling the interior. That is a
weaker guarantee than randomised generation and it is stated here rather than implied, so
nobody reads "property test" as more than it is.

EVERY INVARIANT IS COVERED, MECHANICALLY
----------------------------------------
`test_every_invariant_has_a_property_test` reads `ALL_INVARIANTS` and fails if a predicate is
exported without a test naming it. Adding an invariant and forgetting its test is a red build,
not a gap nobody notices.
"""

from __future__ import annotations

import inspect

import pytest

from domain import invariants
from domain.invariants import (
    ALL_INVARIANTS,
    absence_survives_serialisation,
    bytes_are_never_replaced,
    chronological_boundary_is_locatable,
    declared_instruments_are_permitted,
    evaluation_is_publishable,
    evaluation_pins_five_inputs,
    every_score_carries_its_interval,
    every_score_lies_within_its_interval,
    immutable_is_content_addressed,
    ingest_time_is_not_backfilled,
    leakage_gate_is_consistent_with,
    mutable_identity_is_permitted,
    named_entity_carries_no_digest,
    observation_is_admissible_under,
    observation_is_wellformed,
    reproduction_class_is_consistent_with,
    retraction_fails_the_build,
    split_is_chronological,
    supersession_is_wellformed,
)
from domain.tests import build
from domain.values import Identifier, ReproductionClass, Severity, Timestamp


# ═══════════════════════════════════════════════════════ coverage of the invariant set


def test_every_invariant_has_a_property_test():
    """The registry is the contract: an exported predicate without a test fails here."""
    source = inspect.getsource(inspect.getmodule(test_every_invariant_has_a_property_test))
    missing = [
        predicate.__name__
        for predicate, _ in ALL_INVARIANTS
        if f"def test_{predicate.__name__}" not in source
    ]
    assert not missing, f"invariants exported with no property test: {missing}"


def test_every_invariant_cites_the_decision_it_enforces():
    """An invariant that cannot name its ADR, standard or limitation is a preference."""
    for predicate, citation in ALL_INVARIANTS:
        assert citation, f"{predicate.__name__} cites nothing"
        assert any(
            token in citation for token in ("ADR-", "STD-", "TIS", "L-", "SALVAGE-")
        ), f"{predicate.__name__} cites {citation!r}, which names no decision"


def test_every_invariant_is_exported_and_returns_a_bool():
    """Predicates return bool and never raise — a rule that raises cannot be quantified over."""
    for predicate, _ in ALL_INVARIANTS:
        assert predicate.__name__ in invariants.__all__
        assert inspect.signature(predicate).return_annotation == "bool"


def test_the_registry_has_no_duplicates():
    names = [p.__name__ for p, _ in ALL_INVARIANTS]
    assert len(set(names)) == len(names)


# ═══════════════════════════════════════════════════════ observation invariants


def test_observation_is_wellformed():
    """ADR-0004, TIS E4 §19. Quantified over both states of the nullable ingest time."""
    assert observation_is_wellformed(build.observation())
    assert observation_is_wellformed(build.observation(ingest_time=None))

    # Deliberate violation: learning of a measurement before it happened is a corrupt record,
    # not a late arrival.
    assert not observation_is_wellformed(
        build.observation(
            valid_time=Timestamp("2024-03-01T00:00:00Z"),
            ingest_time=Timestamp("2024-02-28T00:00:00Z"),
        )
    )
    assert not observation_is_wellformed("not an observation")


def test_observation_is_wellformed_accepts_simultaneous_capture():
    """The boundary: ingest at the same instant as validity is legal, not off-by-one."""
    same = Timestamp("2024-03-01T00:00:00Z")
    assert observation_is_wellformed(build.observation(valid_time=same, ingest_time=same))


def test_ingest_time_is_not_backfilled():
    """ADR-0022: the rejected migration filled every unknown with the freeze timestamp."""
    freeze = Timestamp("2024-05-01T00:00:00Z")

    assert ingest_time_is_not_backfilled(build.observation(), freeze)
    # Null is not a backfill — it is the honest representation ADR-0022 mandates.
    assert ingest_time_is_not_backfilled(build.observation(ingest_time=None), freeze)

    # Deliberate violation: the fabricated value, flagged or not.
    assert not ingest_time_is_not_backfilled(build.observation(ingest_time=freeze), freeze)
    # And recognised across offsets, because the same instant written two ways is the same
    # fabrication.
    assert not ingest_time_is_not_backfilled(
        build.observation(ingest_time=Timestamp("2024-05-01T05:30:00+05:30")), freeze
    )


@pytest.mark.parametrize("requires_bitemporal", [True, False])
@pytest.mark.parametrize("ingest_known", [True, False])
def test_observation_is_admissible_under(requires_bitemporal, ingest_known):
    """ADR-0022 §2, quantified over the full 2×2 of protocol mode and ingest-time state."""
    protocol = build.protocol(requires_bitemporal=requires_bitemporal)
    observation = build.observation(
        ingest_time=Timestamp("2024-04-03T12:00:00Z") if ingest_known else None
    )
    expected = ingest_known or not requires_bitemporal
    assert observation_is_admissible_under(observation, protocol) is expected


def test_absence_survives_serialisation():
    """ADR-0017, STD-04. Both nullable fields, independently and together."""
    assert absence_survives_serialisation(build.observation())
    assert absence_survives_serialisation(build.observation(value=None))
    assert absence_survives_serialisation(build.observation(ingest_time=None))
    assert absence_survives_serialisation(
        build.observation(value=None, ingest_time=None)
    )
    # Zero must not be confused with absence on the way out and back.
    assert absence_survives_serialisation(build.observation(value=0.0))
    assert build.observation(value=0.0).to_dict()["value"] == 0.0
    assert build.observation(value=None).to_dict()["value"] is None


# ═══════════════════════════════════════════════════════ evaluation invariants


def test_evaluation_pins_five_inputs():
    """ADR-0021, which superseded ADR-0009's false four-input claim."""
    assert evaluation_pins_five_inputs(build.evaluation())

    class FourInputEvaluation:
        """The superseded model, constructed deliberately to prove the count is checked."""

        method_release = build.digest("e")
        dataset_release = build.digest("b")
        label_release = build.digest("d")
        protocol = build.digest("2")
        environment_release = None

    assert not evaluation_pins_five_inputs(FourInputEvaluation())


@pytest.mark.parametrize("reproduction_class", list(ReproductionClass))
def test_evaluation_is_publishable(reproduction_class):
    """ADR-0021, STD-21. Quantified over all three classes — the whole space."""
    evaluation = build.evaluation(reproduction_class=reproduction_class)
    expected = reproduction_class is not ReproductionClass.UNREPRODUCIBLE
    assert evaluation_is_publishable(evaluation) is expected


@pytest.mark.parametrize("reproduction_class", list(ReproductionClass))
@pytest.mark.parametrize("tolerance", [0.0, 0.001])
def test_reproduction_class_is_consistent_with(reproduction_class, tolerance):
    """ADR-0021: a zero-tolerance Protocol has not defined what EQUIVALENT would mean."""
    evaluation = build.evaluation(reproduction_class=reproduction_class)
    protocol = build.protocol(tolerance=tolerance)
    expected = not (
        reproduction_class is ReproductionClass.EQUIVALENT and tolerance == 0.0
    )
    assert reproduction_class_is_consistent_with(evaluation, protocol) is expected


@pytest.mark.parametrize("requires_bitemporal", [True, False])
@pytest.mark.parametrize("gate_applied", [True, False])
def test_leakage_gate_is_consistent_with(requires_bitemporal, gate_applied):
    """ADR-0022 §2, quantified over the full 2×2.

    The one forbidden cell is the dangerous one: a protocol that could not enforce the gate,
    paired with an evaluation claiming it was applied.
    """
    evaluation = build.evaluation(leakage_gate_applied=gate_applied)
    protocol = build.protocol(requires_bitemporal=requires_bitemporal)
    expected = requires_bitemporal or not gate_applied
    assert leakage_gate_is_consistent_with(evaluation, protocol) is expected


def test_declared_instruments_are_permitted():
    """ADR-0011 — the comparison v1 declared correctly and never performed (SALVAGE-002)."""
    protocol = build.protocol(
        permitted_instruments=(Identifier("solexs"), Identifier("hel1os"))
    )
    assert declared_instruments_are_permitted(build.method_release(), protocol)
    assert declared_instruments_are_permitted(
        build.method_release(
            declared_instruments=(Identifier("solexs"), Identifier("hel1os"))
        ),
        protocol,
    )

    # Deliberate violation: a method consuming an instrument its protocol forbids.
    assert not declared_instruments_are_permitted(
        build.method_release(declared_instruments=(Identifier("xsm"),)), protocol
    )
    # A partial overlap is still a violation — subset, not intersection.
    assert not declared_instruments_are_permitted(
        build.method_release(
            declared_instruments=(Identifier("solexs"), Identifier("xsm"))
        ),
        protocol,
    )


def test_every_score_carries_its_interval():
    """STD-05. True by construction, asserted so a future weakening goes red."""
    assert every_score_carries_its_interval(build.evaluation())
    assert every_score_carries_its_interval(
        build.evaluation(scores=(build.score(), build.score(metric="hss")))
    )


def test_every_score_lies_within_its_interval():
    """Not enforced by the constructor: each part is valid alone, only the pair is wrong."""
    assert every_score_lies_within_its_interval(build.evaluation())
    # The boundary is inside.
    assert every_score_lies_within_its_interval(
        build.evaluation(scores=(build.score(value=0.80),),)
    )
    # Deliberate violation: a point estimate outside its own confidence interval means the
    # estimator and the metric were computed over different things.
    assert not every_score_lies_within_its_interval(
        build.evaluation(scores=(build.score(value=0.99),))
    )


# ═══════════════════════════════════════════════════════ identity invariants


def test_mutable_identity_is_permitted():
    """ADR-0005, TIS E4 §11(ii). Quantified over every named entity and every other entity."""
    for named in build.named_entities():
        assert mutable_identity_is_permitted(named)

    for immutable in (
        build.observation(),
        build.dataset_release(),
        build.label_release(),
        build.method_release(),
        build.environment_release(),
        build.protocol(),
        build.evaluation(),
        build.evidence_binding(),
        build.supersession(),
    ):
        assert not mutable_identity_is_permitted(immutable)


def test_mutable_identity_is_permitted_catches_a_sixth_named_entity():
    """Deliberate violation: inheriting from `_Named` must not grant permission.

    Checked by class name rather than `isinstance`, precisely because subclassing is how a
    sixth would arrive — a check trusting the base class would approve the one case it exists
    to catch.
    """
    from domain.entities.names import _Named

    class Mission(_Named):
        """Not among the five TIS E4 §11(ii) permits."""

    assert not mutable_identity_is_permitted(Mission(Identifier("aditya-l1"), "Aditya-L1"))


def test_immutable_is_content_addressed():
    """ADR-0005, STD-02: sequential and timestamp identifiers are forbidden for immutables."""
    # Releasable objects, addressed by their own digest.
    for immutable in (
        build.dataset_release(),
        build.label_release(),
        build.method_release(),
        build.environment_release(),
        build.protocol(),
        build.evaluation(),
    ):
        assert immutable_is_content_addressed(immutable)

    # Rows and pointers, addressed through the digest they name.
    assert immutable_is_content_addressed(build.observation())
    assert immutable_is_content_addressed(build.evidence_binding())
    assert immutable_is_content_addressed(build.supersession())

    # A name is not content-addressed, and must not be.
    for named in build.named_entities():
        assert not immutable_is_content_addressed(named)


def test_every_domain_entity_is_covered_by_one_identity_regime():
    """No entity may fall between the two rules.

    An entity that is neither a permitted name, nor carries its own digest, nor is listed in
    `ADDRESSED_BY_CONTAINMENT` would silently return False and look like a violation when it
    is really an omission. This enumerates every entity the package exports and requires each
    to land in exactly one regime.
    """
    from domain.invariants.identity import ADDRESSED_BY_CONTAINMENT, CONTENT_ADDRESSED
    from domain.entities.names import PERMITTED_MUTABLE_IDENTITY

    every = (
        *build.named_entities(),
        build.observation(),
        build.dataset_release(),
        build.label_release(),
        build.method_release(),
        build.environment_release(),
        build.protocol(),
        build.evaluation(),
        build.evidence_binding(),
        build.supersession(),
    )
    for entity in every:
        name = type(entity).__name__
        regimes = [
            name in PERMITTED_MUTABLE_IDENTITY,
            name in CONTENT_ADDRESSED,
            name in ADDRESSED_BY_CONTAINMENT,
        ]
        assert sum(regimes) == 1, f"{name} falls into {sum(regimes)} identity regimes, not 1"


def test_immutable_is_content_addressed_rejects_a_sequential_identifier():
    """The deliberate violation ADR-0005 names: an integer id in place of a digest."""

    class SequentiallyIdentified:
        digest = 1234

    assert not immutable_is_content_addressed(SequentiallyIdentified())


def test_named_entity_carries_no_digest():
    """ADR-0005: an Evaluation pinning a name would track whatever it points at today."""
    for named in build.named_entities():
        assert named_entity_carries_no_digest(named)


def test_named_entity_carries_no_digest_catches_a_pinned_name():
    """Deliberate violation."""
    from domain.entities.names import _Named

    class PinnedDataset(_Named):
        digest = build.digest()

    assert not named_entity_carries_no_digest(PinnedDataset(Identifier("x"), "X"))


# ═══════════════════════════════════════════════════════ standing invariants


def test_supersession_is_wellformed():
    """ADR-0024."""
    assert supersession_is_wellformed(build.supersession())
    # A null superseding digest is an outright withdrawal, which is legitimate.
    assert supersession_is_wellformed(build.supersession(superseding=None))


def test_supersession_is_wellformed_rejects_self_supersession():
    """Deliberate violation, constructed around the constructor's own guard.

    The entity refuses this at construction, so the predicate is exercised against a stand-in
    that carries the same fields. Both layers enforce it: the type stops it being built, the
    predicate stops it being believed if it arrives from elsewhere.
    """

    class SelfSuperseding:
        superseded = build.digest("b")
        superseding = build.digest("b")
        severity = Severity.CORRECTION
        reason = "circular"

    assert not supersession_is_wellformed(SelfSuperseding())


@pytest.mark.parametrize("severity", list(Severity))
def test_retraction_fails_the_build(severity):
    """STD-22, ADR-0024 §3. Quantified over all three severities — the whole space."""
    supersession = build.supersession(severity=severity)
    assert retraction_fails_the_build(supersession)
    assert supersession.fails_the_build is (severity is Severity.RETRACTION)


def test_bytes_are_never_replaced():
    """ADR-0024 §1: the record points at the old digest and carries no replacement bytes."""
    assert bytes_are_never_replaced(build.supersession())
    assert bytes_are_never_replaced(build.supersession(superseding=None))


def test_split_is_chronological():
    """ADR-0008: a shuffled split would let a future minute inform a past one."""
    assert split_is_chronological(build.protocol())


def test_split_is_chronological_rejects_any_other_strategy():
    """Deliberate violation. The enum has one member, so the stand-in carries the other case."""

    class ShuffledSplits:
        strategy = "shuffled"

    class ShuffledProtocol:
        splits = ShuffledSplits()

    assert not split_is_chronological(ShuffledProtocol())


def test_chronological_boundary_is_locatable():
    """A strategy label and an actual boundary are different claims."""
    assert chronological_boundary_is_locatable(build.protocol())

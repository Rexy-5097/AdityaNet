"""Unit tests for the entities.

Two things are tested for every entity: that a well-formed instance round-trips through
`to_dict`/`from_dict` unchanged, and that each field's constraint actually rejects. The
second is the one that matters — a constraint nobody has watched reject is a comment.
"""

from __future__ import annotations

import dataclasses

import pytest

from domain.entities import (
    Dataset,
    DatasetRelease,
    EnvironmentRelease,
    Evaluation,
    EvidenceBinding,
    Instrument,
    LabelRelease,
    LabelSource,
    Method,
    MethodRelease,
    Observation,
    Protocol,
    Source,
    Supersession,
    Table,
)
from domain.errors import ContractViolation
from domain.tests import build
from domain.values import Digest, Identifier, ReproductionClass, RunId, Severity, Timestamp

ROUND_TRIPPABLE = [
    (Observation, build.observation),
    (DatasetRelease, build.dataset_release),
    (LabelRelease, build.label_release),
    (MethodRelease, build.method_release),
    (EnvironmentRelease, build.environment_release),
    (Protocol, build.protocol),
    (Evaluation, build.evaluation),
    (EvidenceBinding, build.evidence_binding),
    (Supersession, build.supersession),
]


@pytest.mark.parametrize("cls, make", ROUND_TRIPPABLE, ids=lambda x: getattr(x, "__name__", ""))
def test_every_contract_entity_round_trips(cls, make):
    """ADR-0019: types are hand-written and validated against the schemas.

    Round-tripping is what keeps the two honest on this side of that boundary. The
    schema-validation half is in `tests/integration/test_domain_contract_conformance.py`.
    """
    original = make()
    assert cls.from_dict(original.to_dict()) == original


@pytest.mark.parametrize("cls, make", ROUND_TRIPPABLE, ids=lambda x: getattr(x, "__name__", ""))
def test_every_contract_entity_is_frozen(cls, make):
    """A mutable release is not a release (STD-10)."""
    entity = make()
    field = dataclasses.fields(entity)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(entity, field, None)


# --------------------------------------------------------------------------- Observation


def test_observation_cannot_be_constructed_without_ingest_time():
    """ADR-0022: `ingest_time` is never defaulted.

    A field written `ingest_time: Timestamp | None = None` would default a provenance value
    for any caller who simply omitted it. There is no default, so Python itself refuses.
    """
    with pytest.raises(TypeError):
        Observation(  # type: ignore[call-arg]
            source_id=Identifier("issdc"),
            instrument_id=Identifier("solexs"),
            quantity="count_rate",
            unit="counts/s",
            valid_time=Timestamp("2024-03-01T00:00:00Z"),
            value=12.5,
            source_digest=build.digest(),
        )


def test_observation_accepts_a_null_ingest_time_with_exactly_one_meaning():
    """L-11: null means unknown — predates bitemporal capture. Nothing else."""
    unknown = build.observation(ingest_time=None)
    assert unknown.ingest_time_is_unknown
    assert unknown.to_dict()["ingest_time"] is None


def test_observation_accepts_a_null_value_meaning_observed_to_be_absent():
    absent = build.observation(value=None)
    assert absent.value_is_absent
    assert absent.to_dict()["value"] is None


def test_observation_distinguishes_absent_from_zero():
    """L-07: zero is a valid count rate, so a zero-filled gap is undetectable downstream."""
    assert build.observation(value=None) != build.observation(value=0.0)
    assert build.observation(value=0.0).value_is_absent is False


def test_observation_requires_a_valid_time():
    with pytest.raises(ContractViolation) as caught:
        build.observation(valid_time=None)
    assert caught.value.pointer == "/valid_time"


@pytest.mark.parametrize(
    "field, bad",
    [
        ("source_id", "issdc"),
        ("instrument_id", "solexs"),
        ("quantity", ""),
        ("unit", ""),
        ("ingest_time", "2024-04-03T12:00:00Z"),
        ("source_digest", "a" * 64),
    ],
)
def test_observation_rejects_raw_values_where_a_typed_one_is_required(field, bad):
    """A bare string is not an Identifier, a Timestamp or a Digest.

    This is what stops a caller passing an unvalidated string through a well-typed signature.
    """
    with pytest.raises(ContractViolation) as caught:
        build.observation(**{field: bad})
    assert caught.value.pointer == f"/{field}"


def test_observation_rejects_a_mutable_quality_flag_collection():
    """A frozen entity holding a list is frozen in name only."""
    with pytest.raises(ContractViolation):
        build.observation(quality_flags=["saturated"])


def test_observation_rejects_duplicate_quality_flags():
    with pytest.raises(ContractViolation):
        build.observation(quality_flags=("saturated", "saturated"))


def test_observation_omits_empty_quality_flags_from_its_dict():
    """The schema defaults it to `[]`; emitting one would write out an implied value."""
    assert "quality_flags" not in build.observation().to_dict()
    assert build.observation(quality_flags=("saturated",)).to_dict()["quality_flags"] == [
        "saturated"
    ]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True])
def test_observation_rejects_unserialisable_values(bad):
    with pytest.raises(ContractViolation):
        build.observation(value=bad)


# --------------------------------------------------------------------------- names


def test_the_five_named_entities_are_exactly_those_permitted():
    """TIS E4 §11(ii) is a closed list. A sixth would need this test changed deliberately."""
    from domain.entities.names import PERMITTED_MUTABLE_IDENTITY

    assert set(PERMITTED_MUTABLE_IDENTITY) == {
        "Dataset", "Method", "Source", "Instrument", "LabelSource"
    }
    assert {type(e).__name__ for e in build.named_entities()} == set(PERMITTED_MUTABLE_IDENTITY)


@pytest.mark.parametrize("cls", [Dataset, Method, Source, Instrument, LabelSource])
def test_a_named_entity_carries_no_digest(cls):
    """ADR-0005: giving a name a content address would suggest it can be pinned."""
    entity = cls(Identifier("x"), "X")
    assert not hasattr(entity, "digest")


@pytest.mark.parametrize("cls", [Dataset, Method, Source, Instrument, LabelSource])
def test_a_named_entity_rejects_a_raw_string_id(cls):
    with pytest.raises(ContractViolation) as caught:
        cls("x", "X")  # type: ignore[arg-type]
    assert caught.value.pointer == "/id"


@pytest.mark.parametrize("cls", [Dataset, Method, Source, Instrument, LabelSource])
def test_a_named_entity_requires_a_label(cls):
    with pytest.raises(ContractViolation):
        cls(Identifier("x"), "")


def test_named_entities_of_different_types_are_not_equal():
    """A Source and an Instrument sharing an id are different things (ADR-0003)."""
    assert Source(Identifier("x"), "X") != Instrument(Identifier("x"), "X")


# --------------------------------------------------------------------------- releases


def test_dataset_release_requires_at_least_one_table():
    with pytest.raises(ContractViolation) as caught:
        build.dataset_release(tables=())
    assert "releases nothing" in caught.value.message


def test_dataset_release_rejects_duplicate_table_keys():
    with pytest.raises(ContractViolation):
        build.dataset_release(tables=(build.table(), build.table()))


def test_dataset_release_permits_a_null_doi_and_publishes_the_absence():
    """ADR-0023: absent deposition degrades citability and is published, not hidden."""
    assert build.dataset_release(doi=None).to_dict().get("doi", "absent") == "absent"
    assert build.dataset_release(doi="10.5281/zenodo.1").to_dict()["doi"] == "10.5281/zenodo.1"


def test_dataset_release_rejects_an_empty_doi_string():
    """An empty string is indistinguishable from an absent deposition."""
    with pytest.raises(ContractViolation):
        build.dataset_release(doi="")


@pytest.mark.parametrize("bad_key", ["t1", "T", "1T", "TT", ""])
def test_table_rejects_a_malformed_key(bad_key):
    with pytest.raises(ContractViolation):
        build.table(key=bad_key)


def test_label_release_ingest_time_is_not_nullable():
    """Asymmetric with an Observation's, deliberately: this system created the release."""
    with pytest.raises(ContractViolation) as caught:
        build.label_release(ingest_time=None)
    assert caught.value.pointer == "/ingest_time"


def test_label_release_cannot_supersede_itself():
    with pytest.raises(ContractViolation):
        build.label_release(supersedes_digest=build.digest("d"))


def test_label_release_requires_a_named_authority():
    """L-09: labels come from a different mission than the observations they label."""
    with pytest.raises(ContractViolation) as caught:
        build.label_release(authority="")
    assert "L-09" in caught.value.message


def test_method_release_requires_at_least_one_declared_instrument():
    """An empty declaration is a subset of every permitted set — ADR-0011 would pass vacuously."""
    with pytest.raises(ContractViolation) as caught:
        build.method_release(declared_instruments=())
    assert "vacuously" in caught.value.message


def test_method_release_rejects_duplicate_declared_instruments():
    with pytest.raises(ContractViolation):
        build.method_release(
            declared_instruments=(Identifier("solexs"), Identifier("solexs"))
        )


def test_method_release_permits_null_training_provenance():
    """A threshold detector legitimately has no fitting step (ADR-0010)."""
    assert build.method_release(training_provenance=None).to_dict()["training_provenance"] is None


def test_method_release_accepts_a_training_run():
    fitted = build.method_release(training_provenance=RunId(build.RUN))
    assert fitted.to_dict()["training_provenance"] == build.RUN


def test_environment_release_requires_at_least_one_thread_count():
    """An empty map pins nothing while appearing to."""
    with pytest.raises(ContractViolation) as caught:
        build.environment_release(thread_counts={})
    assert "pins nothing" in caught.value.message


@pytest.mark.parametrize("bad", [0, -1, True, "1"])
def test_environment_release_rejects_a_nonsense_thread_count(bad):
    with pytest.raises(ContractViolation):
        build.environment_release(thread_counts={"OMP_NUM_THREADS": bad})


def test_environment_release_rejects_a_negative_hash_seed():
    with pytest.raises(ContractViolation):
        build.environment_release(hash_seed=-1)


def test_environment_release_records_platform_without_pinning_it():
    """ADR-0021: platform is recorded, not pinned. It separates EXACT from EQUIVALENT."""
    data = build.environment_release().to_dict()
    assert data["platform"] == {"os": "linux", "arch": "x86_64"}


def test_environment_release_permits_a_null_container_digest():
    """ADR-0016's image is authored but unbuilt, so this is null in practice today."""
    assert build.environment_release().to_dict()["container_digest"] is None


# --------------------------------------------------------------------------- Protocol


def test_protocol_requires_the_bitemporal_flag_to_be_a_real_bool():
    """It selects which leakage guarantee is in force, so truthiness is not enough."""
    with pytest.raises(ContractViolation) as caught:
        build.protocol(requires_bitemporal=1)
    assert "ADR-0022" in caught.value.message


def test_protocol_requires_a_non_negative_tolerance():
    with pytest.raises(ContractViolation):
        build.protocol(tolerance=-0.001)


def test_protocol_accepts_zero_tolerance():
    """Zero demands bit-identity and so admits only EXACT — legal, and consequential."""
    assert build.protocol(tolerance=0.0).tolerance == 0.0


def test_protocol_requires_at_least_one_permitted_instrument():
    with pytest.raises(ContractViolation) as caught:
        build.protocol(permitted_instruments=())
    assert "either reading would be a guess" in caught.value.message


def test_protocol_requires_at_least_one_metric():
    with pytest.raises(ContractViolation):
        build.protocol(metrics=())


def test_protocol_permits_reports_membership():
    assert build.protocol().permits(Identifier("solexs"))
    assert not build.protocol().permits(Identifier("hel1os"))


def test_splits_rejects_a_validation_fraction_of_one():
    """A fraction of 1 would leave no training data."""
    with pytest.raises(ContractViolation):
        build.protocol(splits=build.splits(val_fraction=1.0))


# --------------------------------------------------------------------------- Evaluation


@pytest.mark.parametrize(
    "missing",
    ["method_release", "dataset_release", "label_release", "protocol", "environment_release"],
)
def test_evaluation_requires_all_five_inputs(missing):
    """ADR-0021 superseded ADR-0009's four-input claim. Each of the five is dropped in turn."""
    with pytest.raises(ContractViolation) as caught:
        build.evaluation(**{missing: None})
    assert caught.value.pointer == f"/{missing}"
    assert "ADR-0021" in caught.value.message


def test_evaluation_requires_a_declared_reproduction_class():
    """STD-21: declared, never inferred."""
    with pytest.raises(ContractViolation) as caught:
        build.evaluation(reproduction_class="EXACT")
    assert "STD-21" in caught.value.message


def test_evaluation_can_represent_an_unreproducible_result():
    """It may not be published; it must still be representable, or the record is lost."""
    unpublishable = build.evaluation(reproduction_class=ReproductionClass.UNREPRODUCIBLE)
    assert unpublishable.reproduction_class is ReproductionClass.UNREPRODUCIBLE


def test_evaluation_requires_a_real_bool_for_the_leakage_gate():
    with pytest.raises(ContractViolation) as caught:
        build.evaluation(leakage_gate_applied=0)
    assert "ADR-0022" in caught.value.message


def test_evaluation_requires_at_least_one_score():
    with pytest.raises(ContractViolation):
        build.evaluation(scores=())


def test_evaluation_rejects_two_values_for_one_metric():
    """Two values for one metric leaves a reader to choose, which is not a result."""
    with pytest.raises(ContractViolation) as caught:
        build.evaluation(scores=(build.score(), build.score(value=0.42)))
    assert "once" in caught.value.message


def test_evaluation_pinned_returns_the_five_in_adr_order():
    assert build.evaluation().pinned == (
        build.digest("e"), build.digest("b"), build.digest("d"),
        build.digest("2"), build.digest("0"),
    )


def test_evaluation_score_for_returns_none_when_not_computed():
    """Not computed is not zero (ADR-0017). There is no fallback."""
    assert build.evaluation().score_for("hss") is None
    assert build.evaluation().score_for("tss") == build.score()


# --------------------------------------------------------------------------- evidence


def test_evidence_binding_has_no_value_field():
    """ADR-0012/0013: a component cannot be passed a number, so a number cannot reach a page.

    The absence is the design. A convenience `value` field "for rendering" would reintroduce
    exactly the failure the binding exists to prevent.
    """
    names = {f.name for f in dataclasses.fields(EvidenceBinding)}
    assert "value" not in names
    assert "value" not in build.evidence_binding().to_dict()


@pytest.mark.parametrize(
    "escape",
    [
        "/etc/passwd",
        "../secrets.json",
        "artifacts/../../etc/passwd",
        "..",
        "a\\b.json",
        "artifacts/\x00.json",
    ],
)
def test_evidence_binding_refuses_a_path_that_escapes_the_artifact_root(escape):
    """TIS E4 §13. `a/../../b` has no leading `..` and escapes all the same."""
    with pytest.raises(ContractViolation) as caught:
        build.evidence_binding(artifact=escape)
    assert caught.value.pointer == "/artifact"


def test_evidence_binding_accepts_a_contained_relative_path():
    assert build.evidence_binding(artifact="artifacts/a/../b.json").artifact


@pytest.mark.parametrize("pointer", ["", "/scores/0/value", "/a~0b", "/a~1b"])
def test_evidence_binding_accepts_valid_json_pointers(pointer):
    """RFC 6901: the empty string is the whole document and is legal."""
    assert build.evidence_binding(pointer=pointer).pointer == pointer


@pytest.mark.parametrize("bad", ["scores", "/a~2b", "/trailing~"])
def test_evidence_binding_rejects_malformed_json_pointers(bad):
    with pytest.raises(ContractViolation) as caught:
        build.evidence_binding(pointer=bad)
    assert caught.value.pointer == "/pointer"


def test_supersession_permits_a_null_superseding_digest():
    """An outright withdrawal with nothing to replace it is legitimate and common."""
    assert build.supersession(superseding=None).to_dict()["superseding"] is None


def test_supersession_refuses_to_supersede_itself():
    with pytest.raises(ContractViolation) as caught:
        build.supersession(superseding=build.digest("b"))
    assert "itself" in caught.value.message


def test_supersession_requires_a_reason():
    with pytest.raises(ContractViolation) as caught:
        build.supersession(reason="")
    assert "cannot be assessed" in caught.value.message


def test_supersession_requires_the_provenance_of_the_finding():
    """The provenance of the finding is part of the finding."""
    with pytest.raises(ContractViolation) as caught:
        build.supersession(discovered_by=build.RUN)
    assert caught.value.pointer == "/discovered_by"


@pytest.mark.parametrize(
    "severity, fails",
    [(Severity.RETRACTION, True), (Severity.CORRECTION, False), (Severity.DEPRECATION, False)],
)
def test_only_a_retraction_fails_the_build(severity, fails):
    """STD-22. The other two render a notice; the page may still exist."""
    assert build.supersession(severity=severity).fails_the_build is fails


def test_supersession_carries_no_replacement_bytes():
    """ADR-0024 §1: the bytes of a superseded release never change and are never deleted."""
    names = {f.name for f in dataclasses.fields(Supersession)}
    assert "content" not in names and "replacement_bytes" not in names


def test_table_and_digest_are_distinct_types_in_a_signature():
    """Recorded because both are 64-hex-adjacent and confusing them would be silent."""
    assert isinstance(build.table().digest, Digest)
    assert not isinstance(build.digest(), Table)

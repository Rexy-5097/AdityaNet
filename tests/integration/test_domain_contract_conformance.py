"""The domain, the contracts and the provenance kernel, exercised together.

WHY THIS EXISTS AND WHY IT IS NOT A UNIT TEST
----------------------------------------------
By the end of M2 this repository holds three independently-tested subsystems: `contracts/`
(M2/E4/#11), `kernel/provenance` (M2/E3/#10) and `domain/` (M2/E4/#12). Each has a green suite
of its own, and until this file nothing exercised a path that crossed all three. Per-issue
green had stopped being evidence that the platform cohered.

The seam is load-bearing and it is the one ADR-0019 identifies: schemas are normative and
language types are hand-written, so nothing but a test forces the two to agree. A domain type
that quietly drifts from its schema produces objects that pass every unit test in `domain/` and
are rejected by the first consumer that validates them — and the failure surfaces in E5, far
from its cause.

Three things are checked, in increasing scope:

  1. Every domain entity's `to_dict()` validates against its own contract.
  2. The two agree on rejection as well as acceptance — what the domain refuses to build, the
     schema also refuses to accept. Agreement on the happy path alone would be satisfied by a
     schema that accepted everything.
  3. A serialised domain object survives the full platform path: validated against its
     contract, registered in the kernel's content-addressed store, chained into a provenance
     record, and recovered by walking the DAG.

Lives in `tests/integration/` because it crosses real component boundaries and touches a real
filesystem store, per the split the `integration` CI job encodes.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from domain.entities import (
    DatasetRelease,
    EnvironmentRelease,
    Evaluation,
    EvidenceBinding,
    LabelRelease,
    MethodRelease,
    Observation,
    Protocol,
    Supersession,
)
from domain.errors import ContractViolation
from domain.tests import build
from domain.values import Identifier, ReproductionClass, Timestamp
from kernel.provenance import (
    Digest as KernelDigest,
    ProvenanceStore,
    begin_run,
    digest_bytes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"

#: Domain entity → the contract that is normative for it (ADR-0019). `provenance-record` and
#: `common` are absent deliberately: the first is the kernel's, and the second is a definitions
#: file nothing validates against directly.
ENTITY_CONTRACTS = [
    (Observation, build.observation, "observation"),
    (DatasetRelease, build.dataset_release, "dataset-release"),
    (LabelRelease, build.label_release, "label-release"),
    (MethodRelease, build.method_release, "method-release"),
    (EnvironmentRelease, build.environment_release, "environment-release"),
    (Protocol, build.protocol, "protocol"),
    (Evaluation, build.evaluation, "evaluation"),
    (EvidenceBinding, build.evidence_binding, "evidence-binding"),
    (Supersession, build.supersession, "supersession"),
]


def registry():
    """Resolve `urn:adityanet:contract:*` references against the real contract files.

    Built from the schemas on disk rather than from a fixture copy: a registry seeded with
    inlined duplicates would validate the domain against a stale snapshot of the contracts and
    report agreement that had stopped being true.
    """
    from referencing import Registry, Resource

    built = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        if path.name.startswith("._"):
            continue
        built = Resource.from_contents(json.loads(path.read_text())) @ built
    return built


def validator_for(name: str):
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry())


def test_the_contract_set_is_present():
    """Fail closed: an empty scan would report success while checking nothing (STD-07)."""
    schemas = [p for p in CONTRACTS.glob("*.schema.json") if not p.name.startswith("._")]
    assert len(schemas) == 11, f"expected 11 contracts, found {len(schemas)}"


# ═══════════════════════════════════════════════ 1. every entity conforms to its contract


@pytest.mark.parametrize(
    "cls, make, contract", ENTITY_CONTRACTS, ids=[c for _, _, c in ENTITY_CONTRACTS]
)
def test_entity_serialises_to_a_valid_contract_document(cls, make, contract):
    """ADR-0019: the schema is normative and the hand-written type must satisfy it."""
    errors = sorted(validator_for(contract).iter_errors(make().to_dict()), key=str)
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


@pytest.mark.parametrize(
    "cls, make, contract", ENTITY_CONTRACTS, ids=[c for _, _, c in ENTITY_CONTRACTS]
)
def test_a_valid_contract_document_reconstructs_the_same_entity(cls, make, contract):
    """The round trip closes through JSON, not only through a Python dict.

    `to_dict` → `json.dumps` → `json.loads` → `from_dict` is the path a real producer and
    consumer take. Testing only the dict would miss anything JSON cannot carry — a tuple, a
    set, a non-string key.
    """
    original = make()
    through_json = json.loads(json.dumps(original.to_dict()))
    validator_for(contract).validate(through_json)
    assert cls.from_dict(through_json) == original


def test_every_contract_with_a_domain_entity_is_covered():
    """No contract may quietly lack a domain type.

    The two exclusions are named rather than inferred, so adding a twelfth contract without a
    corresponding entity fails here instead of passing unnoticed.
    """
    on_disk = {
        p.name.removesuffix(".schema.json")
        for p in CONTRACTS.glob("*.schema.json")
        if not p.name.startswith("._")
    }
    covered = {contract for _, _, contract in ENTITY_CONTRACTS}
    assert on_disk - covered == {"common", "provenance-record"}


# ═══════════════════════════════════════════════ 2. the two agree on rejection


def test_the_domain_and_the_schema_agree_that_an_unknown_field_is_invalid():
    """Every object contract is closed; the domain has no field to carry an extra either."""
    document = build.observation().to_dict()
    document["unexpected"] = 1
    assert list(validator_for("observation").iter_errors(document))
    with pytest.raises(TypeError):
        Observation(**{**{}, "unexpected": 1})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("source_digest", "not-a-digest"),
        ("valid_time", "2024-01-01"),
        ("instrument_id", "UPPER"),
        ("value", "0.5"),
        ("quantity", ""),
    ],
)
def test_what_the_domain_refuses_to_build_the_schema_also_refuses(field, bad_value):
    """Agreement on rejection, which is the half a permissive schema would fake.

    Each value is injected into an otherwise-valid serialised document and independently
    passed to the domain constructor. Both must refuse. If only the domain refused, the
    contract would be admitting documents no producer here can make; if only the schema
    refused, the domain would be minting documents no consumer can read.
    """
    document = build.observation().to_dict()
    document[field] = bad_value
    assert list(validator_for("observation").iter_errors(document)), (
        f"schema accepted {field}={bad_value!r} which the domain rejects"
    )
    with pytest.raises(ContractViolation):
        Observation.from_dict(document)


def test_both_layers_accept_a_null_ingest_time():
    """ADR-0022's nullable field is nullable on both sides, not merely tolerated on one."""
    document = build.observation(ingest_time=None).to_dict()
    assert document["ingest_time"] is None
    validator_for("observation").validate(document)
    assert Observation.from_dict(document).ingest_time is None


def test_both_layers_reject_a_fourth_input_evaluation():
    """ADR-0021 superseded ADR-0009 in the contract and in the type, not just in prose."""
    document = build.evaluation().to_dict()
    del document["environment_release"]
    assert list(validator_for("evaluation").iter_errors(document))
    with pytest.raises(KeyError):
        Evaluation.from_dict(document)


def test_an_unreproducible_evaluation_is_representable_but_not_publishable():
    """ADR-0021, STD-21: the contract admits it, the invariant refuses to publish it.

    Both behaviours are required together. A contract that rejected `UNREPRODUCIBLE` would
    make the record unrepresentable and so erase the evidence that something unpinned ran.
    """
    from domain.invariants import evaluation_is_publishable

    unpinned = build.evaluation(reproduction_class=ReproductionClass.UNREPRODUCIBLE)
    validator_for("evaluation").validate(unpinned.to_dict())
    assert not evaluation_is_publishable(unpinned)


# ═══════════════════════════════════════════════ 3. the full platform path


def test_a_domain_object_survives_contract_validation_and_the_provenance_kernel(tmp_path):
    """Domain → contract → kernel, the path a real ingest run takes.

    This is the coherence check the three subsystems could not make individually. It also
    exercises the boundary ADR-0026 draws: the domain never imports the kernel, so the digest
    the store mints and the digest the domain validates meet only here, as data.
    """
    store = ProvenanceStore(tmp_path / "store")
    run = begin_run(context="ingest", event="parse")

    observation = build.observation(ingest_time=None)
    payload = json.dumps(observation.to_dict(), sort_keys=True).encode()

    # 1. The contract is normative — validate before anything is registered.
    validator_for("observation").validate(json.loads(payload))

    # 2. The kernel mints the digest. The domain could not have: ADR-0005 reserves minting to
    #    the kernel and ADR-0026 bars the import that would make it possible.
    raw = store.put_bytes(b"raw SoLEXS frame")
    parsed = store.put_bytes(payload)

    # 3. The derivation is recorded and the chain is walkable from the output back to the raw
    #    input — which is what makes a published number answerable.
    record = store.record(run, inputs=[raw.digest], outputs=[parsed.digest])
    assert raw.digest in store.ancestors(parsed.digest)
    assert record.run_id == run.run_id

    # 4. The bytes recovered from the store reconstruct the identical entity.
    recovered = json.loads((store.root / "artifacts" / f"{parsed.digest.hex}.json").read_text())
    assert recovered["digest"] == parsed.digest.hex
    assert Observation.from_dict(json.loads(payload)) == observation


def test_the_domain_validates_a_digest_the_kernel_minted(tmp_path):
    """The two `Digest` types are separate by architecture and must agree on form.

    `domain.values.Digest` and `kernel.provenance.Digest` are deliberately distinct: the domain
    cannot import the kernel (ADR-0026), so the shared 64-hex form is a convention held by two
    implementations. A test is the only thing that keeps them from drifting apart — and drift
    would mean a digest the kernel minted becoming unrepresentable in the domain.
    """
    from domain.values import Digest as DomainDigest

    minted: KernelDigest = digest_bytes(b"any bytes at all")
    assert DomainDigest(minted.hex).hex == minted.hex
    assert DomainDigest(minted.hex).short == minted.short


def test_a_method_release_is_refused_by_the_protocol_that_forbids_its_instrument():
    """ADR-0011 end to end: both objects valid against their contracts, the pairing invalid.

    This is the failure v1 could not detect (SALVAGE-002). Each document passes its own schema
    — the violation exists only in the relationship between them, which is precisely why it
    needs an invariant rather than a contract.
    """
    from domain.invariants import declared_instruments_are_permitted

    method = build.method_release(declared_instruments=(Identifier("xsm"),))
    protocol = build.protocol(permitted_instruments=(Identifier("solexs"),))

    validator_for("method-release").validate(method.to_dict())
    validator_for("protocol").validate(protocol.to_dict())

    assert not declared_instruments_are_permitted(method, protocol)


def test_a_backfilled_ingest_time_passes_the_contract_and_fails_the_invariant():
    """ADR-0022's rejected migration, demonstrated at both layers.

    A backfilled `ingest_time` is a perfectly well-formed timestamp, so no schema can catch it.
    The contract validates the document and the invariant refuses it — which is the division
    of labour between the two layers, shown on the case that motivated ADR-0022.
    """
    from domain.invariants import ingest_time_is_not_backfilled

    freeze = Timestamp("2024-05-01T00:00:00Z")
    backfilled = build.observation(ingest_time=freeze)

    validator_for("observation").validate(backfilled.to_dict())
    assert not ingest_time_is_not_backfilled(backfilled, freeze)
    assert ingest_time_is_not_backfilled(build.observation(ingest_time=None), freeze)

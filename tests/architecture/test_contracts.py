"""Contract validation.

The ten schemas are the only vocabulary that crosses a context boundary (ADR-0019), so every
one is exercised against a valid example, an invalid example, boundary conditions, a
missing-field case and an unknown-field case.

WHY UNKNOWN-FIELD REJECTION IS TESTED PER CONTRACT AND NOT ASSUMED
------------------------------------------------------------------
`additionalProperties: false` is one word in a diff and silently absent if forgotten. An open
object accepts a typo'd field name forever, and producer and consumer then disagree about a
payload while both believe they conform. Each contract is asserted closed individually.

Requires `jsonschema`. That is a third-party import, which is permitted here: `tests/` is not
a governed package under the import policy, and the alternative — hand-rolling a validator —
would mean testing the contracts against a second implementation of JSON Schema rather than
against JSON Schema.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"

DIGEST = "a" * 64
DIGEST_B = "b" * 64
RUN_ID = "01JQ8ZK9WXYZABCDEFGHJKMNPQ"
WHEN = "2026-07-30T12:00:00Z"

EXPECTED_CONTRACTS = (
    "common", "dataset-release", "environment-release", "evaluation",
    "evidence-binding", "label-release", "manifest", "method-release",
    "observation", "protocol", "provenance-record", "supersession",
)


def schema_paths() -> list[Path]:
    return sorted(p for p in CONTRACTS.glob("*.schema.json") if not p.name.startswith("._"))


def registry() -> Registry:
    """All contracts, resolvable by $id, so cross-schema $refs work.

    Built by accumulation rather than a bulk constructor: `Registry` is immutable, and the
    `@` operator returns a new registry with the resource added.
    """
    built = Registry()
    for path in schema_paths():
        schema = json.loads(path.read_text())
        built = Resource.from_contents(schema) @ built
    return built


def validator_for(name: str) -> Draft202012Validator:
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    return Draft202012Validator(schema, registry=registry())


def valid(name: str) -> dict:
    """A minimal conforming document per contract."""
    return {
        "provenance-record": {
            "run_id": RUN_ID, "inputs": [DIGEST], "outputs": [DIGEST_B],
        },
        "observation": {
            "source_id": "issdc-pradan", "instrument_id": "solexs-sdd2",
            "quantity": "count_rate", "unit": "counts/s",
            "valid_time": WHEN, "ingest_time": WHEN,
            "value": 12.5, "source_digest": DIGEST,
        },
        "dataset-release": {
            "dataset_id": "aditya-xray", "version": "r1", "digest": DIGEST,
            "frozen_at": WHEN, "n_files": 1985, "total_bytes": 596917461,
            "tables": [{"key": "T1", "name": "solexs_lc_1min",
                        "digest": DIGEST_B, "n_files": 424, "bytes": 14061207}],
        },
        "label-release": {
            "label_source_id": "noaa-swpc", "authority": "NOAA SWPC",
            "digest": DIGEST, "ingest_time": WHEN, "n_events": 581,
        },
        "protocol": {
            "protocol_id": "mx-nowcast", "digest": DIGEST, "task": "M/X nowcast",
            "splits": {"strategy": "chronological", "test_start": WHEN},
            "metrics": ["roc_auc", "pr_auc"],
            "uncertainty_estimator": "day-block bootstrap",
            "exchangeable_unit": "day",
            "permitted_instruments": ["solexs-sdd2"],
            "label_source_id": "noaa-swpc",
            "requires_bitemporal": False, "tolerance": 0.0,
        },
        "environment-release": {
            "digest": DIGEST, "interpreter_version": "3.12.12",
            "lockfile_digest": DIGEST_B,
            "blas": {"implementation": "OpenBLAS", "version": "0.3.27"},
            "thread_counts": {"OMP_NUM_THREADS": 1},
            "hash_seed": 0,
            "platform": {"os": "linux", "arch": "x86_64"},
        },
        "method-release": {
            "method_id": "threshold-rate", "digest": DIGEST,
            "artifact_digest": DIGEST_B,
            "declared_instruments": ["solexs-sdd2"],
            "parameters": {"threshold": 6.2334528172083585},
            "training_provenance": None,
        },
        "evaluation": {
            "digest": DIGEST, "method_release": DIGEST, "dataset_release": DIGEST,
            "label_release": DIGEST, "protocol": DIGEST, "environment_release": DIGEST,
            "reproduction_class": "EXACT", "leakage_gate_applied": False,
            "scores": [{"metric": "roc_auc", "value": 0.953889,
                        "interval": {"lower": 0.9396, "upper": 0.9664, "level": 0.95,
                                     "estimator": "day-block bootstrap",
                                     "exchangeable_unit": "day"},
                        "denominator": 192541}],
        },
        "evidence-binding": {
            "claim_id": "threshold-beats-models", "measurement_key": "roc_auc",
            "artifact": "registry/evaluations/abc.json",
            "pointer": "/scores/0/value", "artifact_digest": DIGEST, "run_id": RUN_ID,
        },
        "supersession": {
            "superseded": DIGEST, "superseding": DIGEST_B, "severity": "DEPRECATION",
            "reason": "superseded by bitemporal schema", "effective_date": WHEN,
            "discovered_by": RUN_ID,
        },
        # Tier 1 is the manifest's central case: a canonical release deposited externally
        # and referenced from git by digest, DOI and URL (ADR-0023, E6 §7).
        "manifest": {
            "kind": "dataset", "digest": DIGEST, "tier": 1, "recorded_at": WHEN,
            "retention": {"class": "permanent"},
            "deposition": {"provider": "Zenodo",
                           "url": "https://zenodo.org/records/1",
                           "doi": "10.5281/zenodo.1"},
        },
    }[name]


CONTRACT_NAMES = [n for n in EXPECTED_CONTRACTS if n != "common"]


# ── The corpus ──────────────────────────────────────────────────────────────────

def test_exactly_the_expected_contracts_exist():
    found = tuple(p.name.removesuffix(".schema.json") for p in schema_paths())
    assert found == EXPECTED_CONTRACTS


def test_the_object_contracts_are_the_ten_of_part_1_plus_the_tier_2_manifest():
    """TIS Part 1 specifies ten; `common` is definitions, not an object contract.

    The eleventh is `manifest`, added by M2/E4/#14 — E4 §2 lists the Tier 2 manifest format
    in this epic's scope alongside the ten, and §15 row 14 assigns it its own issue.
    """
    assert len(CONTRACT_NAMES) == 11
    assert "manifest" in CONTRACT_NAMES
    assert "common" not in CONTRACT_NAMES


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_schema_is_itself_valid_json_schema(path: Path):
    Draft202012Validator.check_schema(json.loads(path.read_text()))


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_has_stable_identifier_and_explicit_version(path: Path):
    schema = json.loads(path.read_text())
    match = re.match(r"^urn:adityanet:contract:([a-z-]+):(\d+)$", schema["$id"])
    assert match, f"malformed $id: {schema['$id']}"
    assert match.group(1) == path.name.removesuffix(".schema.json")
    assert int(match.group(2)) >= 1


def test_identifiers_are_unique():
    ids = [json.loads(p.read_text())["$id"] for p in schema_paths()]
    assert len(set(ids)) == len(ids)


# ── Valid examples ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_valid_example_validates(name: str):
    validator_for(name).validate(valid(name))


# ── Unknown fields are rejected, per contract ───────────────────────────────────

@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_unknown_field_is_rejected(name: str):
    document = {**valid(name), "unexpected_field": "x"}
    assert not validator_for(name).is_valid(document)


@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_every_object_contract_is_closed(name: str):
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    assert schema.get("additionalProperties") is False


def test_only_thread_counts_permits_extension():
    """The single sanctioned open object, and it says why: the relevant variables are set by
    the libraries installed, not by this contract."""
    env = json.loads((CONTRACTS / "environment-release.schema.json").read_text())
    threads = env["properties"]["thread_counts"]
    assert threads["additionalProperties"] == {"type": "integer", "minimum": 1}
    assert "not by this contract" in threads["description"]


# ── Missing required fields ─────────────────────────────────────────────────────

@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_every_required_field_is_actually_required(name: str):
    """Dropping any one required field must invalidate the document. A field listed as
    required but not enforced is a contract that lies."""
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    validator = validator_for(name)
    for field in schema["required"]:
        document = {k: v for k, v in valid(name).items() if k != field}
        assert not validator.is_valid(document), f"{name}: {field} is not enforced"


# ── Invalid values and boundaries ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "name,field,bad",
    [
        ("observation", "source_digest", "A" * 64),          # upper-case hex
        ("observation", "source_digest", "a" * 63),          # too short
        ("observation", "source_digest", "a" * 65),          # too long
        ("observation", "valid_time", "not-a-timestamp"),
        ("observation", "unit", ""),                          # empty
        ("observation", "instrument_id", "Solexs"),          # upper-case
        ("provenance-record", "run_id", "01JQ8ZK9WXYZABCDEFGHJKMNPI"),   # I is excluded
        ("provenance-record", "outputs", []),                # must produce something
        ("dataset-release", "n_files", 0),                   # a release with no files
        ("dataset-release", "total_bytes", -1),
        ("label-release", "n_events", -1),
        ("protocol", "tolerance", -0.1),                     # negative tolerance
        ("protocol", "permitted_instruments", []),           # would permit nothing
        ("environment-release", "hash_seed", -1),
        ("method-release", "declared_instruments", []),      # ADR-0011 needs at least one
        ("evaluation", "reproduction_class", "PROBABLY"),
        ("evaluation", "scores", []),
        ("evidence-binding", "pointer", "no-leading-slash"),
        ("supersession", "severity", "MINOR"),
    ],
)
def test_invalid_value_is_rejected(name: str, field: str, bad):
    assert not validator_for(name).is_valid({**valid(name), field: bad})


@pytest.mark.parametrize(
    "name,field,ok",
    [
        ("provenance-record", "inputs", []),        # acquisition has no upstream input
        ("dataset-release", "total_bytes", 0),      # boundary: minimum 0
        ("label-release", "n_events", 0),           # a release may legitimately have none
        ("protocol", "tolerance", 0.0),             # zero demands bit-identity
        ("environment-release", "hash_seed", 0),
    ],
)
def test_boundary_value_is_accepted(name: str, field: str, ok):
    validator_for(name).validate({**valid(name), field: ok})


@pytest.mark.parametrize("level", [0.0, 1.0, 1.5, -0.1])
def test_confidence_level_must_be_strictly_between_zero_and_one(level: float):
    document = valid("evaluation")
    document["scores"][0]["interval"]["level"] = level
    assert not validator_for("evaluation").is_valid(document)


def test_a_score_without_an_interval_is_rejected():
    """STD-05. A bare number without its uncertainty is the figure this platform refuses."""
    document = valid("evaluation")
    del document["scores"][0]["interval"]
    assert not validator_for("evaluation").is_valid(document)


def test_a_score_without_a_denominator_is_rejected():
    document = valid("evaluation")
    del document["scores"][0]["denominator"]
    assert not validator_for("evaluation").is_valid(document)


# ── Nullability carries meaning (ADR-0017, ADR-0022) ────────────────────────────

def test_observation_ingest_time_may_be_null():
    """ADR-0022: null means unknown — predates bitemporal capture. L-11 publishes it."""
    validator_for("observation").validate({**valid("observation"), "ingest_time": None})


def test_observation_ingest_time_may_not_be_omitted():
    """Absence and unknown are different. Requiring the field forces the producer to state
    which it means rather than leaving a reader to guess."""
    document = {k: v for k, v in valid("observation").items() if k != "ingest_time"}
    assert not validator_for("observation").is_valid(document)


def test_observation_value_may_be_null_but_not_omitted():
    """ADR-0017: null is observed-to-be-absent. It is never imputed and never zero-filled."""
    validator_for("observation").validate({**valid("observation"), "value": None})
    document = {k: v for k, v in valid("observation").items() if k != "value"}
    assert not validator_for("observation").is_valid(document)


def test_supersession_superseding_may_be_null_for_outright_withdrawal():
    validator_for("supersession").validate({**valid("supersession"), "superseding": None})


def test_method_release_training_provenance_may_be_null():
    """A threshold detector legitimately has no fitting step."""
    validator_for("method-release").validate(
        {**valid("method-release"), "training_provenance": None}
    )


# ── The five pinned inputs (ADR-0021) ───────────────────────────────────────────

FIVE_INPUTS = ("method_release", "dataset_release", "label_release",
               "protocol", "environment_release")


@pytest.mark.parametrize("pinned", FIVE_INPUTS)
def test_evaluation_requires_all_five_pinned_inputs(pinned: str):
    """ADR-0021 supersedes ADR-0009 precisely because four was not enough."""
    document = {k: v for k, v in valid("evaluation").items() if k != pinned}
    assert not validator_for("evaluation").is_valid(document)


@pytest.mark.parametrize("cls", ["EXACT", "EQUIVALENT", "UNREPRODUCIBLE"])
def test_the_three_reproduction_classes_are_accepted(cls: str):
    validator_for("evaluation").validate({**valid("evaluation"), "reproduction_class": cls})


@pytest.mark.parametrize("sev", ["CORRECTION", "RETRACTION", "DEPRECATION"])
def test_the_three_supersession_severities_are_accepted(sev: str):
    validator_for("supersession").validate({**valid("supersession"), "severity": sev})


def test_protocol_permits_only_chronological_splitting():
    """A shuffled split would let a future minute inform a past one."""
    document = valid("protocol")
    document["splits"]["strategy"] = "random"
    assert not validator_for("protocol").is_valid(document)


# ── No domain logic in the contracts (ADR-0026) ─────────────────────────────────

@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_no_domain_vocabulary_in_constraints(path: Path):
    """Contracts are structural. A solar term hard-coded into an enum or pattern would make
    the vocabulary domain-bound and unusable for a second instrument.

    Prose is exempt: several descriptions cite the clause that motivated a constraint, which
    is why the rule exists at all.
    """
    schema = json.loads(path.read_text())

    # $id, $schema and $ref are identifiers, not constraints. The URN namespace legitimately
    # contains the project name; excluding these is scoping the rule to what it governs — a
    # value a document is checked against — rather than exempting anything.
    def constraints(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("description", "title", "$comment", "$id", "$schema", "$ref"):
                    continue
                yield from constraints(value)
        elif isinstance(node, list):
            for value in node:
                yield from constraints(value)
        elif isinstance(node, str):
            yield node

    forbidden = ("solexs", "hel1os", "flare", "goes", "aditya")
    for text in constraints(schema):
        lowered = text.lower()
        for word in forbidden:
            assert word not in lowered, f"{path.name}: domain term {word!r} in a constraint"


# ── The gate ────────────────────────────────────────────────────────────────────

def test_the_contracts_gate_passes():
    import importlib.util
    import sys

    gate_path = REPO_ROOT / "tools" / "gates" / "contracts.py"
    spec = importlib.util.spec_from_file_location("contracts_gate", gate_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.main() == 0


# ── The additive-only diff logic (STD-09) ───────────────────────────────────────
#
# Exercised against synthetic baselines rather than against origin/main. Every contract is
# new on this branch, so the gate compares nothing when run here — a diff check that has
# only ever run against an empty baseline is a diff check nobody has seen work.


def _gate():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "contracts_gate_diff", REPO_ROOT / "tools" / "gates" / "contracts.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _diff(old: dict, new: dict) -> list[str]:
    gate = _gate()
    report = gate.Report()
    base = {"$id": "urn:adityanet:contract:t:1", "type": "object"}
    gate.compare("t.schema.json", {**base, **old}, {**base, **new}, report)
    return report.failures


BREAKING = [
    ("narrowed minLength",
     {"properties": {"a": {"type": "string", "minLength": 1}}},
     {"properties": {"a": {"type": "string", "minLength": 2}}}),
    ("narrowed minItems",
     {"properties": {"a": {"type": "array", "minItems": 0}}},
     {"properties": {"a": {"type": "array", "minItems": 1}}}),
    ("narrowed maximum",
     {"properties": {"a": {"type": "number", "maximum": 10}}},
     {"properties": {"a": {"type": "number", "maximum": 5}}}),
    ("raised minimum",
     {"properties": {"a": {"type": "integer", "minimum": 0}}},
     {"properties": {"a": {"type": "integer", "minimum": 1}}}),
    ("changed type",
     {"properties": {"a": {"type": "string"}}},
     {"properties": {"a": {"type": "number"}}}),
    ("changed pattern",
     {"properties": {"a": {"type": "string", "pattern": "^x$"}}},
     {"properties": {"a": {"type": "string", "pattern": "^y$"}}}),
    ("removed property",
     {"properties": {"a": {"type": "string"}, "b": {"type": "string"}}},
     {"properties": {"a": {"type": "string"}}}),
    ("closed an open object",
     {"properties": {"a": {"type": "object", "additionalProperties": True}}},
     {"properties": {"a": {"type": "object", "additionalProperties": False}}}),
    ("removed an enum value",
     {"properties": {"a": {"enum": ["X", "Y"]}}},
     {"properties": {"a": {"enum": ["X"]}}}),
    ("added a required field at the root",
     {"required": ["a"]},
     {"required": ["a", "b"]}),
    ("added a required field in a nested object",
     {"properties": {"s": {"type": "object", "required": ["x"]}}},
     {"properties": {"s": {"type": "object", "required": ["x", "y"]}}}),
    ("narrowed a union type",
     {"properties": {"a": {"type": ["number", "null"]}}},
     {"properties": {"a": {"type": ["number"]}}}),
]


@pytest.mark.parametrize("label,old,new", BREAKING, ids=[b[0] for b in BREAKING])
def test_breaking_change_is_rejected(label: str, old: dict, new: dict):
    assert _diff(old, new), f"{label} was not detected as breaking"


ADDITIVE = [
    ("added optional property",
     {"properties": {"a": {"type": "string"}}},
     {"properties": {"a": {"type": "string"}, "b": {"type": "string"}}}),
    ("widened maximum",
     {"properties": {"a": {"type": "number", "maximum": 5}}},
     {"properties": {"a": {"type": "number", "maximum": 10}}}),
    ("lowered minLength",
     {"properties": {"a": {"type": "string", "minLength": 2}}},
     {"properties": {"a": {"type": "string", "minLength": 1}}}),
    ("added an enum value",
     {"properties": {"a": {"enum": ["X"]}}},
     {"properties": {"a": {"enum": ["X", "Y"]}}}),
    ("removed a required field",
     {"required": ["a", "b"]},
     {"required": ["a"]}),
    ("widened a union type",
     {"properties": {"a": {"type": ["number"]}}},
     {"properties": {"a": {"type": ["number", "null"]}}}),
    ("changed a description",
     {"properties": {"a": {"type": "string", "description": "before"}}},
     {"properties": {"a": {"type": "string", "description": "after"}}}),
]


@pytest.mark.parametrize("label,old,new", ADDITIVE, ids=[a[0] for a in ADDITIVE])
def test_additive_change_is_accepted(label: str, old: dict, new: dict):
    assert not _diff(old, new), f"{label} was wrongly flagged: {_diff(old, new)}"


def test_a_major_bump_exempts_the_comparison():
    """A new major version IS the sanctioned route for a breaking change, so the
    additive-only rule does not apply across it."""
    gate = _gate()
    report = gate.Report()
    gate.compare(
        "t.schema.json",
        {"$id": "urn:adityanet:contract:t:1", "properties": {"a": {"type": "string"}}},
        {"$id": "urn:adityanet:contract:t:2", "properties": {}},
        report,
    )
    assert not report.failures
    assert report.compared == 0


def test_the_gate_does_not_claim_an_unexercised_comparison():
    """When no baseline exists the summary must say so rather than assert every change was
    additive. A gate claiming a property it did not check is the failure mode this project
    exists to refuse."""
    import io
    from contextlib import redirect_stdout

    gate = _gate()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        gate.main()
    output = buffer.getvalue()
    if "0 compared" in output or "No baseline" in output:
        assert "every change additive" not in output

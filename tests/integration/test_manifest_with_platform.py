"""The Tier 2 manifest, exercised against every component M2 has delivered.

WHY THIS IS AN INTEGRATION TEST AND NOT MORE SCHEMA TESTS
----------------------------------------------------------
`tests/architecture/test_manifest_contract.py` proves the schema accepts and refuses the right
documents. What it cannot prove is the thing the manifest exists for: that the digest written
into a manifest is *the same digest* as the bytes it claims to describe. A manifest is only
worth anything if that holds, and checking it needs four components at once —

  #10 kernel/provenance   mints the digest, and is the only thing permitted to (ADR-0005)
  #11 contracts/          says what a DatasetRelease looks like
  #12 domain/             builds one, and validates the digest's *form* without minting it
  #13 import rules        say which context is allowed to do all of the above
  #14 manifest            records where the bytes went

The central assertion is `manifest["digest"] == kernel-minted digest`. Every other guarantee
in this repository — citation, re-acquisition, supersession, evidence binding — rests on that
equality, and until this file nothing had ever checked it end to end.

SCOPE. No producer is implemented. The manifest documents here are built inline by the test,
which is what a test does; `contexts/curation/manifest` is E6/#20's to write, and
`registry/datasets/*.json` instances are E6/#21's to commit.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
GATE_PATH = REPO_ROOT / "tools" / "gates" / "imports.py"

WHEN = "2026-07-30T12:00:00Z"


def registry() -> Registry:
    built = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        if path.name.startswith("._"):
            continue
        built = Resource.from_contents(json.loads(path.read_text())) @ built
    return built


def validator_for(name: str):
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry())


def freeze_a_release(store):
    """Build a DatasetRelease, validate it, and register its bytes with the kernel.

    Stands in for what E6's `freeze` will do. It is written here rather than imported because
    Issue #14 delivers no producer — the point is to have a *real* release, contract-valid and
    kernel-registered, for the manifest to describe.
    """
    from domain.entities import DatasetRelease, Table
    from domain.values import Digest, Identifier, Timestamp

    table_bytes = b"minute,count_rate\n2024-03-01T00:00:00Z,12.5\n"
    table_artifact = store.put_bytes(table_bytes)

    release = DatasetRelease(
        dataset_id=Identifier("adityanet-v2"),
        version="r1",
        digest=Digest(table_artifact.digest.hex),
        tables=(
            Table(
                key="T1",
                name="solexs_lightcurve",
                digest=Digest(table_artifact.digest.hex),
                n_files=1,
                bytes=len(table_bytes),
            ),
        ),
        frozen_at=Timestamp(WHEN),
        n_files=1,
        total_bytes=len(table_bytes),
        doi=None,
    )
    validator_for("dataset-release").validate(release.to_dict())
    return release, table_artifact


def manifest_for(release, *, doi: str | None, url: str) -> dict:
    """The Tier 2 record that git carries in place of the ~600 MB the release contains."""
    return {
        "kind": "dataset",
        "digest": str(release.digest),
        "name": str(release.dataset_id),
        "version": release.version,
        "tier": 1,
        "recorded_at": WHEN,
        "retention": {"class": "permanent"},
        "deposition": {"provider": "Zenodo", "url": url, "doi": doi},
    }


# ═══════════════════════════════════════════ the digest is the same digest


def test_a_manifest_addresses_the_exact_bytes_the_kernel_registered(tmp_path):
    """The central claim, checked across all four components.

    The kernel mints a digest from real bytes; the domain holds it without being able to
    compute it; the contract validates the release; and the manifest records the same digest.
    If these ever diverge, every citation in the platform points at bytes nobody can verify —
    and nothing else in the repository would notice.
    """
    from kernel.provenance import Digest as KernelDigest, ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    release, artifact = freeze_a_release(store)

    manifest = manifest_for(release, doi="10.5281/zenodo.1", url="https://zenodo.org/records/1")
    validator_for("manifest").validate(manifest)

    # The manifest's digest is the kernel's digest, is the release's digest.
    assert manifest["digest"] == artifact.digest.hex == str(release.digest)

    # And it round-trips back into a kernel Digest, so the store can be asked for the bytes.
    assert store.has_artifact(KernelDigest(manifest["digest"]))
    assert store.get_artifact(KernelDigest(manifest["digest"])).digest == artifact.digest


def test_a_manifest_whose_digest_does_not_match_is_detectable(tmp_path):
    """The failure the equality above exists to catch.

    A manifest is a claim about bytes. This constructs one that is *schema-valid and false* —
    correct in every field, pointing at a digest the store has never seen — and shows the
    store refuses it. No schema could catch this, which is exactly why the check belongs here.
    """
    from kernel.provenance import Digest as KernelDigest, ProvenanceStore
    from kernel.provenance.errors import IntegrityFailure, ProvenanceFailure

    store = ProvenanceStore(tmp_path / "store")
    release, artifact = freeze_a_release(store)

    wrong = manifest_for(release, doi=None, url="https://zenodo.org/records/2")
    wrong["digest"] = "f" * 64
    validator_for("manifest").validate(wrong)          # perfectly well formed
    assert wrong["digest"] != artifact.digest.hex      # and perfectly wrong

    assert not store.has_artifact(KernelDigest(wrong["digest"]))
    with pytest.raises((ProvenanceFailure, IntegrityFailure, FileNotFoundError)):
        store.get_artifact(KernelDigest(wrong["digest"]))


def test_the_manifest_and_the_domain_agree_on_what_a_digest_is(tmp_path):
    """`common.schema.json#/$defs/digest` and `domain.values.Digest` are two implementations
    of one rule, held together only by tests. The manifest is now a third consumer of it."""
    from domain.values import Digest as DomainDigest
    from kernel.provenance import ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    _, artifact = freeze_a_release(store)

    assert DomainDigest(artifact.digest.hex).hex == artifact.digest.hex
    validator_for("manifest").validate(
        {"kind": "dataset", "digest": artifact.digest.hex, "tier": 2,
         "recorded_at": WHEN, "retention": {"class": "permanent"},
         "path": "registry/datasets/a.json"}
    )


# ═══════════════════════════════════════════ the manifest carries the whole tier story


def test_the_fallback_deposition_publishes_its_own_degradation(tmp_path):
    """ADR-0023: without Zenodo, citability degrades — and the degradation is published.

    A release deposited via the fallback is still a valid manifest and still addresses the
    right bytes. What changes is that `doi` is null, visibly, in a required field. A reader
    can tell the difference; a schema that made `doi` optional could not.
    """
    from kernel.provenance import ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    release, artifact = freeze_a_release(store)

    fallback = manifest_for(
        release, doi=None,
        url="https://github.com/Rexy-5097/AdityaNet/releases/tag/dataset-r1",
    )
    validator_for("manifest").validate(fallback)
    assert fallback["deposition"]["doi"] is None
    assert "doi" in fallback["deposition"]
    assert fallback["digest"] == artifact.digest.hex


def test_a_tier_0_reference_records_bytes_the_repository_will_never_hold(tmp_path):
    """ADR-0023, STD-23. The 21 GB archive is identified, not stored.

    The kernel registers the *digest*, not the bytes — `put_bytes` here stands for a digest
    computed over a cached copy that is evictable by design. The manifest then records how to
    re-acquire it, and the schema makes recording a deposition impossible.
    """
    from kernel.provenance import ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    cached = store.put_bytes(b"a raw SoLEXS L1 frame that this repository does not keep")

    tier0 = {
        "kind": "dataset", "digest": cached.digest.hex, "tier": 0, "recorded_at": WHEN,
        "retention": {"class": "permanent"},
        "retrieval": {"provider": "ISSDC PRADAN",
                      "locator": "aditya-l1/solexs/2024-03-01",
                      "requires_credentials": True},
    }
    validator_for("manifest").validate(tier0)

    # The same entry with a deposition is unrepresentable — redistribution cannot be recorded.
    redistributing = dict(tier0)
    redistributing["deposition"] = {
        "provider": "Zenodo", "url": "https://zenodo.org/records/3", "doi": None,
    }
    assert list(validator_for("manifest").iter_errors(redistributing))


def test_an_evidence_binding_and_a_manifest_can_name_the_same_artifact(tmp_path):
    """Why retention is on the manifest at all (E6 §11(iv), STD-24).

    An EvidenceBinding pins `artifact_digest`; a manifest records what may happen to those
    bytes. Both contracts are satisfied here by one digest, and the manifest that names the
    binding's claim cannot be marked prunable — which is the guarantee that a published claim
    never loses the bytes underneath it.
    """
    from kernel.provenance import ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    artifact = store.put_bytes(json.dumps({"scores": [{"value": 0.85}]}).encode())

    binding = {
        "claim_id": "tss-headline", "measurement_key": "detection.tss",
        "artifact": "registry/evaluations/a.json", "pointer": "/scores/0/value",
        "artifact_digest": artifact.digest.hex,
        "run_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    }
    validator_for("evidence-binding").validate(binding)

    referenced = {
        "kind": "evaluation", "digest": artifact.digest.hex, "tier": 2,
        "recorded_at": WHEN,
        "retention": {"class": "permanent", "referenced_by": [binding["claim_id"]]},
        "path": binding["artifact"],
    }
    validator_for("manifest").validate(referenced)
    assert referenced["digest"] == binding["artifact_digest"]

    # The same artifact marked prunable while a claim depends on it: refused.
    prunable = dict(referenced)
    prunable["retention"] = {
        "class": "prunable", "prune_after": WHEN, "referenced_by": [binding["claim_id"]],
    }
    assert list(validator_for("manifest").iter_errors(prunable))


# ═══════════════════════════════════════════ #13 — the rules still hold


def test_writing_manifests_needs_no_import_the_context_rules_forbid(tmp_path):
    """The manifest introduces no new dependency edge (ADR-0026, M2/E4/#13).

    A curation module that freezes a release and records its manifest needs `domain`, `kernel`
    and the stdlib — exactly what `contexts.curation`'s policy already grants. If the manifest
    had required something else, this issue would have had to widen an import rule, and that
    would be a change to the architecture rather than an addition to the contracts.
    """
    spec = importlib.util.spec_from_file_location(f"mf_gate_{tmp_path.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    gate.REPO_ROOT = tmp_path

    for dotted in ("contracts", "domain", "kernel"):
        directory = tmp_path / dotted
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("")

    curation = tmp_path / "contexts" / "curation"
    curation.mkdir(parents=True)
    (curation / "__init__.py").write_text("")
    (curation / "manifest.py").write_text(
        "import json\n"
        "from domain.entities import DatasetRelease\n"
        "from domain.values import Digest, Timestamp\n"
        "from kernel.provenance import ProvenanceStore\n"
    )

    from tools.gates.imports import POLICIES as SHIPPED

    shipped = next(p for p in SHIPPED if p.package == "contexts.curation")
    report, code = gate.run([
        gate.Policy(package="contexts.curation", allow=shipped.allow, populated=True),
        *[gate.Policy(package=n) for n in ("contracts", "domain", "kernel")],
    ])
    assert code == 0, report.violations
    assert report.modules >= 1, "the analyser scanned nothing; the verdict means nothing"


def test_the_manifest_contract_is_reachable_from_the_shared_definitions():
    """`$ref` resolution across the contract set still works with twelve schemas.

    The manifest is the first contract added since the registry was built, and a `$ref` that
    fails to resolve produces a validator that silently accepts everything under it.
    """
    schema = json.loads((CONTRACTS / "manifest.schema.json").read_text())
    assert schema["properties"]["digest"]["$ref"].startswith("urn:adityanet:contract:common:1")

    # A bad digest must actually be rejected — proof the $ref resolved rather than no-opped.
    assert list(validator_for("manifest").iter_errors({
        "kind": "dataset", "digest": "nope", "tier": 2, "recorded_at": WHEN,
        "retention": {"class": "permanent"}, "path": "a.json",
    }))

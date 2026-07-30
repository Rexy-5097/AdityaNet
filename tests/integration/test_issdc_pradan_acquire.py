"""Fixture acquire — the integration test §15 row 16 names, across the whole platform.

`| 16 | 16 | E5 | 700 | L | 15 | descriptor | — | fixture acquire |`

The adapter is exercised against every component that has to accept what it produces:

  #10 kernel/provenance   mints every digest, and is the only thing permitted to
  #11 contracts/          validates the Observation the acquisition supports
  #12 domain/             holds the digest and the times without being able to make either
  #13 context import rules  say Ingest may reach the kernel and the domain and nothing else
  #14 manifest            records the Tier 0 archive as referenced, never deposited
  #15 ingest contract     is what decides whether this adapter may feed the platform at all

THE ADAPTER SATISFIES THE CONTRACT RATHER THAN BYPASSING IT
------------------------------------------------------------
Every acquisition below goes through `verify_conformance` — #15's checker — rather than
calling `acquire` directly and inspecting the result. That is the difference between an
adapter that happens to produce the right shape and one the platform has actually accepted.
`test_the_adapter_is_admitted_by_the_contract_not_by_inspection` makes the distinction
explicit by showing the checker rejecting a near-identical adapter that breaks one rule.

The archives are fixtures, built from bytes these tests write, with the layout
`SPEC-parsers@r6` §1.1 records. Two tests use the real corpus and skip when it is absent
(STD-12, E5 §17); the guard tests for `.gz` products because five archive *directories* exist
in a clean checkout while their products do not.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from contexts.ingest import (
    Acquisition,
    PolicyRejection,
    UnavailableResource,
    assert_credential_free,
    verify_conformance,
)
from contexts.ingest.adapters.issdc_pradan import (
    GRANULARITY,
    LATENCY,
    SOURCE_ID,
    IssdcPradanAdapter,
)
from domain.entities import Observation
from domain.invariants import ingest_time_is_not_backfilled, observation_is_wellformed
from domain.values import Digest, Identifier, Timestamp
from kernel.provenance import Digest as KernelDigest, ProvenanceStore, begin_run

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
GATE_PATH = REPO_ROOT / "tools" / "gates" / "imports.py"
REAL_ARCHIVE = REPO_ROOT / "research" / "data" / "aditya_l1" / "real_l1_v1" / "solexs"

FLARE_DAY = "2024-05-14"


def real_products_present() -> bool:
    """Products, not directories — E5 §16's explicit requirement."""
    if not REAL_ARCHIVE.is_dir():
        return False
    return any(p for p in REAL_ARCHIVE.rglob("*.gz") if not p.name.startswith("._"))


real_only = pytest.mark.skipif(
    not real_products_present(), reason="real SoLEXS archive not extracted"
)


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


def build_archive(root: Path, date: str = "20240514", version: str = "1.0") -> Path:
    """A daily archive with the published layout: stem repeated, SDD1 GTI only."""
    stem = f"AL1_SLX_L1_{date}_v{version}"
    inner = root / stem / stem
    for relative, payload in {
        f"SDD1/AL1_SOLEXS_{date}_SDD1_L1.gti.gz": b"gti-sdd1",
        f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.gti.gz": b"gti-sdd2",
        f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.lc.gz": b"count-rate lightcurve",
        f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.pi.gz": b"pulse-height",
    }.items():
        target = inner / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(payload))
    return root / stem


@pytest.fixture
def acquired(tmp_path):
    """One conforming acquisition of a fixture archive, admitted by #15's checker."""
    root = tmp_path / "archive"
    build_archive(root)
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcPradanAdapter(root, store)
    return store, adapter, verify_conformance(adapter, selector=FLARE_DAY)


# ═══════════════════════════════════════════ #15 — admitted by the contract


def test_the_adapter_is_admitted_by_the_contract_not_by_inspection(acquired, tmp_path):
    """The acquisition is what #15's checker returned, not what `acquire` happened to build.

    The contrast is the point: a near-identical adapter that breaks exactly one rule — it
    reports a digest other than the one its artifact carries — is refused by the same call
    that admitted this one.
    """
    _, adapter, acquisition = acquired
    assert isinstance(acquisition, Acquisition)

    class MisreportingAdapter(IssdcPradanAdapter):
        def acquire(self, selector: str) -> Acquisition:
            return _misattribute(super().acquire(selector))

    with pytest.raises(PolicyRejection):
        verify_conformance(
            MisreportingAdapter(adapter.archive_root, ProvenanceStore(tmp_path / "s2")),
            selector=FLARE_DAY,
        )


def _misattribute(acquisition: Acquisition) -> Acquisition:
    """Rebuild an acquisition whose provenance names bytes other than its artifact.

    Constructed around the constructor's guard, because the checker must reject it too: an
    adapter can build its result some other way, and #15's job is to catch that.
    """
    instance = object.__new__(Acquisition)
    object.__setattr__(instance, "artifact", acquisition.artifact)
    object.__setattr__(
        instance,
        "provenance",
        type(acquisition.provenance)(
            run_id=acquisition.provenance.run_id,
            source_id=acquisition.provenance.source_id,
            artifact_digest=Digest("f" * 64),
            ingest_time=acquisition.provenance.ingest_time,
        ),
    )
    return instance


def test_the_registered_channel_declares_what_e5_requires(acquired):
    """E5 §18: latency class `~33d`, granularity `daily-archive`."""
    _, adapter, _ = acquired
    described = adapter.descriptor()
    assert (str(described.source_id), str(described.latency_class),
            str(described.granularity)) == (SOURCE_ID, LATENCY, GRANULARITY)


# ═══════════════════════════════════════════ #10 — every digest is the kernel's


def test_every_digest_the_adapter_reports_was_minted_by_the_kernel(acquired):
    """ADR-0005 permits nothing else to mint one.

    Each product digest is re-derived here with the kernel's own `digest_file` over the file
    on disk, and each must match what the adapter reported.
    """
    from kernel.provenance import digest_file

    _, adapter, acquisition = acquired
    archive = adapter.archive_for(FLARE_DAY)

    for product in adapter.products(FLARE_DAY):
        on_disk = digest_file(archive / product.relative_path)
        assert product.digest.hex == on_disk.hex, product.relative_path

    # And the archive identity is the kernel's digest of the canonical listing.
    from kernel.provenance import digest_chunks

    listing = adapter.manifest_bytes(adapter.products(FLARE_DAY))
    assert acquisition.artifact.digest.hex == digest_chunks([listing]).hex


def test_the_archive_identity_resolves_to_bytes_the_store_holds(acquired):
    """A digest nobody can resolve is a claim about nothing."""
    store, _, acquisition = acquired
    assert store.has_artifact(KernelDigest(str(acquisition.artifact.digest)))


def test_the_acquisition_is_recorded_in_the_provenance_dag(acquired, tmp_path):
    """The derivation chain a published number will later be walked back along."""
    store, adapter, acquisition = acquired
    run = begin_run(context="ingest", event="canonicalise")

    canonical = store.put_bytes(b"canonical minute grid for 2024-05-14")
    store.record(run,
                 inputs=[KernelDigest(str(acquisition.artifact.digest))],
                 outputs=[canonical.digest])

    ancestors = store.ancestors(canonical.digest)
    assert KernelDigest(str(acquisition.artifact.digest)) in ancestors


# ═══════════════════════════════════════════ #11 + #12 — the row it supports


def test_an_observation_built_from_the_acquisition_validates_against_its_contract(acquired):
    """The acquisition supplies the provenance column and both times; the domain and the
    contract accept the result.

    The *parse* is not performed — reading a SoLEXS `.lc` product is M3/E5/#17. What is shown
    is that everything a parser will need is present and mutually consistent.
    """
    _, _, acquisition = acquired

    observation = Observation(
        source_id=acquisition.provenance.source_id,
        instrument_id=Identifier("solexs"),
        quantity="count_rate",
        unit="counts/s",
        valid_time=Timestamp("2024-05-14T16:51:00Z"),
        ingest_time=acquisition.provenance.ingest_time,
        value=None,
        source_digest=acquisition.artifact.digest,
    )

    validator_for("observation").validate(observation.to_dict())
    assert observation_is_wellformed(observation)
    assert observation.source_digest == acquisition.artifact.digest
    assert observation.ingest_time is not None


def test_the_stamped_ingest_time_is_not_a_backfill(acquired):
    """ADR-0022: the value came from the acquisition boundary, not from a freeze timestamp."""
    _, _, acquisition = acquired
    freeze = Timestamp("2026-05-01T00:00:00Z")
    observation = Observation(
        source_id=acquisition.provenance.source_id,
        instrument_id=Identifier("solexs"),
        quantity="count_rate",
        unit="counts/s",
        valid_time=Timestamp("2024-05-14T16:51:00Z"),
        ingest_time=acquisition.provenance.ingest_time,
        value=None,
        source_digest=acquisition.artifact.digest,
    )
    assert ingest_time_is_not_backfilled(observation, freeze)


def test_the_ingest_time_is_far_later_than_the_observation(acquired):
    """The ~33-day latency, visible in the data rather than only in the descriptor.

    An archive acquired today carries observations from a date long past. The row records
    both, which is what makes "what did we know at time T?" answerable at all (ADR-0004).
    """
    _, adapter, acquisition = acquired
    observed = Timestamp("2024-05-14T16:51:00Z")
    learned = acquisition.provenance.ingest_time

    assert learned.instant > observed.instant
    elapsed = (learned.instant - observed.instant).total_seconds()
    assert elapsed > adapter.descriptor().latency_class.seconds, (
        "the fixture is acquired now, so the gap must exceed the declared ~33d latency"
    )


# ═══════════════════════════════════════════ #14 — Tier 0, referenced not deposited


def test_the_acquisition_becomes_a_valid_tier_0_manifest(acquired):
    """The adapter's retrieval descriptor is exactly what a Tier 0 manifest records."""
    _, adapter, acquisition = acquired

    manifest = {
        "kind": "dataset",
        "digest": acquisition.artifact.digest.hex,
        "name": "adityanet-solexs-daily",
        "tier": 0,
        "recorded_at": str(acquisition.provenance.ingest_time),
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
    }
    validator_for("manifest").validate(manifest)
    assert manifest["retrieval"]["requires_credentials"] is True
    assert manifest["digest"] == acquisition.artifact.digest.hex


def test_the_manifest_cannot_record_this_archive_as_deposited(acquired):
    """ADR-0023, STD-23: another organisation's raw archive is never redistributed.

    Refused at both ends — the adapter cannot hand out the bytes, and the manifest cannot say
    they were deposited.
    """
    _, _, acquisition = acquired
    assert not hasattr(acquisition.artifact, "bytes")

    redistributing = {
        "kind": "dataset", "digest": acquisition.artifact.digest.hex, "tier": 0,
        "recorded_at": str(acquisition.provenance.ingest_time),
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
        "deposition": {"provider": "Zenodo", "url": "https://zenodo.org/records/1",
                       "doi": None},
    }
    assert list(validator_for("manifest").iter_errors(redistributing))


def test_the_store_holds_the_listing_and_not_the_archive(acquired):
    """What git and the store carry is the manifest, not the data (ADR-0023, E6 §19)."""
    store, adapter, acquisition = acquired
    assert store.has_artifact(KernelDigest(str(acquisition.artifact.digest)))
    for product in adapter.products(FLARE_DAY):
        assert not store.has_artifact(KernelDigest(str(product.digest))), (
            f"{product.relative_path} was copied into the store"
        )


# ═══════════════════════════════════════════ #13 — the import rules still hold


def test_the_adapter_lives_within_the_ingest_import_rule():
    """ADR-0026: the adapter may reach `contracts`, `domain` and `kernel`, and no context."""
    from tools.gates.imports import POLICIES, run

    report, code = run(POLICIES)
    assert code == 0, report.violations

    ingest = next(p for p in POLICIES if p.package == "contexts.ingest")
    internal = ingest.allow & {"contracts", "domain", "kernel", "contexts", "apps",
                               "tools", "registry", "tests"}
    assert internal == {"contracts", "domain", "kernel"}
    assert "contexts" not in ingest.allow, "Ingest must reach no other context"
    assert ingest.populated is True


def test_an_adapter_reaching_another_context_is_rejected(tmp_path):
    """The deliberate violation, against the shipped rule."""
    spec = importlib.util.spec_from_file_location(f"a_gate_{tmp_path.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    gate.REPO_ROOT = tmp_path

    for dotted in ("contracts", "domain", "kernel", "contexts.curation"):
        directory = tmp_path / Path(*dotted.split("."))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("")
    adapter_dir = tmp_path / "contexts" / "ingest" / "adapters" / "issdc_pradan"
    adapter_dir.mkdir(parents=True)
    for level in (tmp_path / "contexts" / "ingest",
                  tmp_path / "contexts" / "ingest" / "adapters", adapter_dir):
        (level / "__init__.py").write_text("")
    (adapter_dir / "adapter.py").write_text(
        "from kernel.provenance import digest_file\n"
        "from contexts.curation.freeze import freeze\n"
    )

    from tools.gates.imports import POLICIES as SHIPPED

    shipped = next(p for p in SHIPPED if p.package == "contexts.ingest")
    report, code = gate.run([
        gate.Policy(package="contexts.ingest", allow=shipped.allow, populated=True),
        gate.Policy(package="contexts.curation", allow=shipped.allow, populated=False),
        *[gate.Policy(package=n) for n in ("contracts", "domain", "kernel")],
    ])
    assert code == 1
    assert any("contexts.curation" in v and "not permitted" in v for v in report.violations)


# ═══════════════════════════════════════════ STD-19 — nothing leaks


def test_nothing_the_adapter_produces_carries_a_credential(acquired):
    """The adapter holds no secret, so this checks the far end rather than the type."""
    _, adapter, acquisition = acquired
    assert_credential_free(adapter.descriptor(), what="the ISSDC descriptor")
    assert_credential_free(acquisition, what="the ISSDC acquisition")

    serialised = json.dumps(acquisition.provenance.to_dict(), sort_keys=True)
    for marker in ("jsessionid", "fgtserver", "oauth", "cookie", "token", "session"):
        assert marker not in serialised.lower()


# ═══════════════════════════════════════════ an unretrieved day


def test_a_day_that_was_never_retrieved_aborts_without_partial_state(tmp_path):
    """E5 §9: any failure aborts, and `aborted` leaves no observations.

    Nothing is registered with the store, because the failure happens before anything is.
    """
    root = tmp_path / "archive"
    build_archive(root, date="20240514")
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcPradanAdapter(root, store)

    before = len(list((store.root / "artifacts").glob("*.json")))
    with pytest.raises(UnavailableResource):
        adapter.acquire("2024-05-15")
    after = len(list((store.root / "artifacts").glob("*.json")))
    assert before == after == 0


# ═══════════════════════════════════════════ the real corpus (skips when absent)


@real_only
def test_the_real_flare_day_acquires_and_conforms(tmp_path):
    """The X8.7 flare of 2024-05-14, through the whole platform.

    SALVAGE-001 records v1 reproducing this event to the minute from GOES. This is the
    Aditya-L1 side of the same day, entering the platform with provenance for the first time.
    """
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcPradanAdapter(REAL_ARCHIVE, store)

    acquisition = verify_conformance(adapter, selector=FLARE_DAY)
    products = adapter.products(FLARE_DAY)

    assert len(products) == 4, [p.relative_path for p in products]
    assert acquisition.artifact.size_bytes == sum(p.size_bytes for p in products)
    assert acquisition.artifact.size_bytes > 10_000_000, "the day's archive is ~13 MB"
    assert store.has_artifact(KernelDigest(str(acquisition.artifact.digest)))

    manifest = {
        "kind": "dataset", "digest": acquisition.artifact.digest.hex, "tier": 0,
        "recorded_at": str(acquisition.provenance.ingest_time),
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
    }
    validator_for("manifest").validate(manifest)


@real_only
def test_the_real_archive_identity_is_stable_across_acquisitions(tmp_path):
    """Re-acquiring the same day does not mint a new identity.

    This is what makes a citation durable: the digest depends on the bytes ISSDC published,
    not on when this system happened to look at them.
    """
    first = IssdcPradanAdapter(REAL_ARCHIVE, ProvenanceStore(tmp_path / "s1")).acquire(FLARE_DAY)
    second = IssdcPradanAdapter(REAL_ARCHIVE, ProvenanceStore(tmp_path / "s2")).acquire(FLARE_DAY)

    assert first.artifact.digest == second.artifact.digest
    assert first.provenance.run_id != second.provenance.run_id

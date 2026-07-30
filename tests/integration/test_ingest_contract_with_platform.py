"""A complete acquisition path, across every component the platform has.

This is the first test in the repository that follows real scientific data from an
acquisition channel to a contract-valid, provenance-linked Observation. Everything before M3
built the vocabulary and the guarantees; this exercises the path they exist for.

  #10 kernel/provenance   digests the raw bytes and chains the derivation
  #11 contracts/          says what an Observation and a manifest must look like
  #12 domain/             builds the Observation, and refuses a fabricated ingest_time
  #13 context import rules  say that Ingest may do all of this and may not reach elsewhere
  #14 manifest            records where the Tier 0 bytes stay, since they are not kept here
  #15 ingest contract     the channel, the boundary stamp, and the credential confinement

Two paths are followed, and the difference between them is the whole of ADR-0022:

  a NEW acquisition        both times present, the ingest one stamped at the boundary
  a HISTORICAL row         valid_time only; ingest_time null, meaning "unknown — predates
                           bitemporal capture", with no acquisition to describe and nothing
                           anywhere that would fill it in

SCOPE. No source adapter, no instrument parser, no registry. The adapter here is the in-test
conforming one from `contexts/ingest/tests/adapters.py`; the ISSDC-PRADAN adapter is M3/E5/#16
and the SoLEXS and HEL1OS parsers are #17 and #18. The Observation is constructed directly
from bytes the test wrote, because parsing a FITS product is precisely what #17 owns.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from contexts.ingest import (
    Acquisition,
    AcquisitionProvenance,
    RawArtifact,
    RetrievalDescriptor,
    assert_credential_free,
    verify_conformance,
)
from contexts.ingest import boundary
from contexts.ingest.descriptor import LatencyClass, SourceDescriptor
from domain.entities import Observation
from domain.invariants import (
    ingest_time_is_not_backfilled,
    observation_is_admissible_under,
    observation_is_wellformed,
)
from domain.values import Digest, Identifier, RunId, Timestamp
from kernel.provenance import Digest as KernelDigest, ProvenanceStore, begin_run

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
GATE_PATH = REPO_ROOT / "tools" / "gates" / "imports.py"

#: One minute of SoLEXS-shaped light-curve data. Not a FITS product — parsing one is #17's
#: work — but real bytes, digested by the real kernel, so the digests below are genuine.
RAW_FRAME = b"# solexs l1 lightcurve\n2024-03-01T00:00:00Z,12.5\n2024-03-01T00:01:00Z,\n"


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


class IssdcShapedAdapter:
    """A channel with the ISSDC channel's declared shape, acquiring from a local file.

    It is not the ISSDC adapter (#16): it reaches no portal and holds no session. What it does
    reproduce faithfully is the *contract* — the descriptor E5 §18 specifies, a digest minted
    by the kernel, and an ingest_time stamped at the boundary.
    """

    def __init__(self, store: ProvenanceStore, source_file: Path) -> None:
        self._store = store
        self._file = source_file

    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id=Identifier("issdc-pradan"),
            authority="ISSDC, Indian Space Research Organisation",
            latency_class=LatencyClass("~33d"),
            granularity=Identifier("daily-archive"),
            retrieval=RetrievalDescriptor(
                provider="ISSDC PRADAN",
                locator="aditya-l1/solexs/l1/2024-03-01",
                requires_credentials=True,
            ),
        )

    def acquire(self, selector: str) -> Acquisition:
        run = begin_run(context="ingest", event="acquire")

        # The kernel mints the digest. Ingest could not: ADR-0005 reserves minting to it.
        artifact = self._store.put_file(self._file)

        # The one sanctioned clock read in the system (ADR-0004, TIS §0.4).
        stamped = boundary.stamp()

        return Acquisition(
            artifact=RawArtifact(
                digest=Digest(artifact.digest.hex),
                size_bytes=artifact.size_bytes,
                retrieval=self.descriptor().retrieval,
                cache_path=self._file,
            ),
            provenance=AcquisitionProvenance(
                run_id=RunId(run.run_id),
                source_id=Identifier("issdc-pradan"),
                artifact_digest=Digest(artifact.digest.hex),
                ingest_time=stamped,
                instruments=(Identifier("solexs"),),
            ),
        )


@pytest.fixture
def acquired(tmp_path):
    """Perform one conforming acquisition and return everything it produced."""
    source = tmp_path / "solexs_20240301.lc"
    source.write_bytes(RAW_FRAME)
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcShapedAdapter(store, source)
    return store, adapter, verify_conformance(adapter, selector="2024-03-01")


# ═══════════════════════════════════════════ the whole path


def test_a_new_acquisition_produces_a_contract_valid_observation_with_both_times(acquired):
    """The path M3 exists to open, end to end.

    Channel → kernel digest → boundary stamp → domain Observation → contract validation →
    provenance record. Every step is performed by the component that owns it, and the
    Observation that comes out carries both times with nothing fabricated.
    """
    store, adapter, acquisition = acquired

    # An Observation canonicalised from the acquired artifact. The parse itself is #17's;
    # what matters here is that the times and the provenance column come from the acquisition.
    observation = Observation(
        source_id=acquisition.provenance.source_id,
        instrument_id=Identifier("solexs"),
        quantity="count_rate",
        unit="counts/s",
        valid_time=Timestamp("2024-03-01T00:00:00Z"),
        ingest_time=acquisition.provenance.ingest_time,
        value=12.5,
        source_digest=acquisition.artifact.digest,
    )

    validator_for("observation").validate(observation.to_dict())
    assert observation_is_wellformed(observation)

    # E5 §11(i): every newly ingested Observation carries both times.
    assert observation.valid_time is not None
    assert observation.ingest_time is not None
    assert observation.ingest_time.instant >= observation.valid_time.instant

    # The provenance column points at the bytes the kernel actually holds.
    assert store.has_artifact(KernelDigest(str(observation.source_digest)))

    # And the derivation is recorded, so the row is answerable back to the raw frame.
    run = begin_run(context="ingest", event="parse")
    parsed = store.put_bytes(json.dumps(observation.to_dict(), sort_keys=True).encode())
    store.record(run, inputs=[KernelDigest(str(observation.source_digest))],
                 outputs=[parsed.digest])
    assert KernelDigest(str(observation.source_digest)) in store.ancestors(parsed.digest)


def test_the_digest_is_the_same_digest_at_every_layer(acquired):
    """Kernel, ingest artifact, acquisition provenance, domain Observation, manifest.

    Five representations of one content address. Each is a separate type in a separate
    component, and nothing but a test holds them to the same value.
    """
    store, adapter, acquisition = acquired
    minted = store.put_file(acquisition.artifact.cache_path)

    assert acquisition.artifact.digest.hex == minted.digest.hex
    assert acquisition.provenance.artifact_digest.hex == minted.digest.hex

    manifest = {
        "kind": "dataset",
        "digest": minted.digest.hex,
        "tier": 0,
        "recorded_at": str(acquisition.provenance.ingest_time),
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
    }
    validator_for("manifest").validate(manifest)
    assert manifest["digest"] == acquisition.artifact.digest.hex


def test_the_ingest_descriptor_is_exactly_a_manifest_retrieval_descriptor(acquired):
    """One fact, one shape (M2/E4/#14, ADR-0023).

    The descriptor an adapter publishes and the descriptor a Tier 0 manifest records are the
    same statement about how to re-acquire. If their shapes ever diverge, a manifest written
    from an adapter's descriptor stops validating — so this is checked rather than assumed.
    """
    _, adapter, _ = acquired
    published = adapter.descriptor().retrieval.to_dict()

    manifest = {
        "kind": "dataset", "digest": "a" * 64, "tier": 0,
        "recorded_at": "2024-04-03T12:00:00Z",
        "retention": {"class": "permanent"},
        "retrieval": published,
    }
    validator_for("manifest").validate(manifest)

    schema = json.loads((CONTRACTS / "manifest.schema.json").read_text())
    assert set(published) == set(schema["properties"]["retrieval"]["properties"])


def test_tier_0_bytes_are_referenced_and_the_manifest_cannot_say_otherwise(acquired):
    """ADR-0023 and STD-23, enforced at both ends of the same path.

    Ingest cannot hand out the bytes — `RawArtifact` has no field for them — and the manifest
    cannot record them as deposited. Two independent refusals of the same thing.
    """
    _, _, acquisition = acquired
    assert not hasattr(acquisition.artifact, "bytes")
    assert acquisition.artifact.retrieval is not None

    redistributing = {
        "kind": "dataset", "digest": acquisition.artifact.digest.hex, "tier": 0,
        "recorded_at": "2024-04-03T12:00:00Z",
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
        "deposition": {"provider": "Zenodo", "url": "https://zenodo.org/records/1",
                       "doi": None},
    }
    assert list(validator_for("manifest").iter_errors(redistributing))


# ═══════════════════════════════════════════ ADR-0022 — the historical path


def test_a_historical_row_carries_a_null_ingest_time_and_no_acquisition():
    """The other half of the bitemporal story, and the one that is easy to get wrong.

    A row that predates bitemporal capture has no acquisition to describe. It gets
    `ingest_time = None` — ADR-0022's single meaning — and E5 §11(ii) forbids any code path
    from writing a non-null value for it. The contract accepts it, the invariant confirms it
    was not backfilled, and there is nothing in `contexts.ingest.boundary` that would supply
    one.
    """
    historical = Observation(
        source_id=Identifier("issdc-pradan"),
        instrument_id=Identifier("solexs"),
        quantity="count_rate",
        unit="counts/s",
        valid_time=Timestamp("2023-01-15T00:00:00Z"),
        ingest_time=None,
        value=8.25,
        source_digest=Digest("c" * 64),
    )

    validator_for("observation").validate(historical.to_dict())
    assert historical.to_dict()["ingest_time"] is None
    assert observation_is_wellformed(historical)
    assert historical.ingest_time_is_unknown

    freeze = Timestamp("2024-05-01T00:00:00Z")
    assert ingest_time_is_not_backfilled(historical, freeze)

    # Stamping it would be a deliberate act, and the invariant catches the specific
    # fabrication ADR-0022 was written to reject.
    fabricated = Observation(
        source_id=historical.source_id,
        instrument_id=historical.instrument_id,
        quantity=historical.quantity,
        unit=historical.unit,
        valid_time=historical.valid_time,
        ingest_time=freeze,
        value=historical.value,
        source_digest=historical.source_digest,
    )
    validator_for("observation").validate(fabricated.to_dict())   # schema cannot see it
    assert not ingest_time_is_not_backfilled(fabricated, freeze)  # the invariant can


def test_a_bitemporal_protocol_excludes_the_historical_row_and_admits_the_acquired_one(acquired):
    """Why the distinction is load-bearing (ADR-0022 §2).

    A Protocol with `requires_bitemporal = true` excludes rows whose availability cannot be
    established. The newly acquired row survives it; the historical one does not. That is the
    leakage gate becoming enforceable by construction rather than by trust — and it only
    works because nothing filled in the missing time.
    """
    from domain.tests import build

    _, _, acquisition = acquired
    strict = build.protocol(requires_bitemporal=True)
    permissive = build.protocol(requires_bitemporal=False)

    fresh = build.observation(ingest_time=acquisition.provenance.ingest_time)
    historical = build.observation(ingest_time=None)

    assert observation_is_admissible_under(fresh, strict)
    assert not observation_is_admissible_under(historical, strict)
    assert observation_is_admissible_under(historical, permissive)


# ═══════════════════════════════════════════ #13 — the rules still hold


def test_the_ingest_context_imports_only_what_adr_0026_grants():
    """The real tree, under the shipped policy — not a fixture.

    M3/E5/#15 is the first issue to put code in a context, so this is the first time the
    ingest rule binds against anything. It asserts the policy is applied to the real package
    and that the package satisfies it.
    """
    from tools.gates.imports import POLICIES, run

    ingest = next(p for p in POLICIES if p.package == "contexts.ingest")
    assert ingest.populated is True, "the ingest policy still declares itself unpopulated"
    assert ingest.allow == frozenset({"contracts", "domain", "kernel"})

    report, code = run(POLICIES)
    assert code == 0, report.violations
    assert report.modules >= 7, f"only {report.modules} modules scanned"


def test_ingest_reaches_no_other_context(tmp_path):
    """The deliberate violation, against the shipped rule rather than a synthetic one."""
    spec = importlib.util.spec_from_file_location(f"ing_gate_{tmp_path.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    gate.REPO_ROOT = tmp_path

    for dotted in ("contracts", "domain", "kernel", "contexts.curation"):
        directory = tmp_path / Path(*dotted.split("."))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("")
    ingest_dir = tmp_path / "contexts" / "ingest"
    ingest_dir.mkdir(parents=True)
    (ingest_dir / "__init__.py").write_text("")
    (ingest_dir / "acquire.py").write_text(
        "from domain.values import Digest\n"
        "from kernel.provenance import ProvenanceStore\n"
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
    assert any(
        "contexts.curation" in v and "not permitted" in v for v in report.violations
    ), report.violations


def test_no_credential_reaches_anything_the_platform_stores(acquired):
    """The boundary holds across the whole path, checked on what was actually produced."""
    store, adapter, acquisition = acquired
    assert_credential_free(adapter.descriptor(), what="the source descriptor")
    assert_credential_free(acquisition, what="the acquisition")

    serialised = json.dumps(acquisition.provenance.to_dict(), sort_keys=True)
    for leak in ("session", "cookie", "token", "password", "credential"):
        assert leak not in serialised

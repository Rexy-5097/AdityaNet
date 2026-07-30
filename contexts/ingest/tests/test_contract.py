"""Contract conformance — the unit test §15 row 14+1 names.

`| 15 | 15 | E5 | 200 | M | 11 | contract conformance | — | credential-boundary |`

Every rule in the contract is exercised from both sides: an adapter that satisfies it, and an
adapter that breaks exactly that rule and keeps the others. The second half is the half that
matters — a checker seen only accepting is a checker nobody has watched reject anything.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from contexts.ingest import boundary
from contexts.ingest.acquisition import Acquisition, AcquisitionProvenance, RawArtifact
from contexts.ingest.contract import (
    CONFORMANCE_GATE,
    FORBIDDEN_ARTIFACT_FIELDS,
    SourceAdapter,
    verify_conformance,
    verify_descriptor,
)
from contexts.ingest.credentials import Credential
from contexts.ingest.descriptor import LatencyClass, RetrievalDescriptor, SourceDescriptor
from contexts.ingest.errors import PolicyRejection, UnavailableResource
from contexts.ingest.tests import adapters
from domain.errors import ContractViolation
from domain.values import Digest, Identifier, Timestamp

SELECTOR = "2024-03-01"


# ═══════════════════════════════════════════ the contract accepts what conforms


def test_a_conforming_adapter_passes_every_check():
    """The positive case. Without it, a checker that rejected everything would look correct."""
    acquired = verify_conformance(adapters.ConformingAdapter(), selector=SELECTOR)
    assert isinstance(acquired, Acquisition)
    assert acquired.artifact.digest == acquired.provenance.artifact_digest


def test_the_protocol_recognises_a_structurally_complete_adapter():
    assert isinstance(adapters.ConformingAdapter(), SourceAdapter)


def test_the_descriptor_check_returns_what_it_verified():
    """E5 §18's acceptance criterion is a question about the descriptor alone.

    Separating it means an adapter can be asked what it is without being asked to fetch,
    which is what lets #16 assert `~33d` / `daily-archive` without touching the archive.
    """
    described = verify_descriptor(adapters.ConformingAdapter())
    assert str(described.source_id) == "issdc-pradan"
    assert str(described.latency_class) == "~33d"
    assert str(described.granularity) == "daily-archive"


# ═══════════════════════════════════════════ E5 §4 — the interface itself


@pytest.mark.parametrize(
    "adapter",
    [adapters.AdapterWithNoDescriptor(), adapters.AdapterWithNoAcquire()],
    ids=["no-descriptor", "no-acquire"],
)
def test_an_incomplete_adapter_is_refused(adapter):
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapter, selector=SELECTOR)
    assert caught.value.gate == CONFORMANCE_GATE


def test_a_descriptor_of_the_wrong_type_is_refused():
    """A channel describing itself in its own vocabulary cannot be compared to another."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterReturningTheWrongDescriptorType(), selector=SELECTOR)
    assert "SourceDescriptor" in caught.value.message


def test_a_descriptor_that_varies_between_calls_is_refused():
    """A channel whose declared latency changes has declared no latency."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterWithAVaryingDescriptor(), selector=SELECTOR)
    assert "not constant" in caught.value.message


def test_an_acquisition_of_the_wrong_type_is_refused():
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterReturningTheWrongAcquisitionType(), selector=SELECTOR)
    assert "Acquisition" in caught.value.message


# ═══════════════════════════════════════════ STD-19 / E5 §13 — credentials never leave


def test_an_adapter_leaking_a_credential_in_its_descriptor_is_refused():
    """The descriptor records *how* to acquire, never the secret.

    Refused by the CONFORMANCE gate rather than the credential gate, and that ordering is
    the stronger result: a real `SourceDescriptor` has no field a credential could occupy
    (see the test below), so the only way to publish one is to return something that is not
    a SourceDescriptor at all — which the type check catches first. The runtime credential
    scan is the backstop for the duck-typed case, exercised on provenance below.
    """
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(
            adapters.AdapterLeakingACredentialInItsDescriptor(), selector=SELECTOR
        )
    assert caught.value.gate == CONFORMANCE_GATE
    assert "SourceDescriptor" in caught.value.message


def test_the_descriptor_type_has_no_field_a_credential_could_occupy():
    """STD-19 made structural rather than checked.

    Every `SourceDescriptor` field is either a typed domain value or a plain string that the
    constructor requires — there is no `object`-typed field, no free-form mapping, and no
    optional extras dict. A secret cannot be placed in a conforming descriptor at all, which
    is a stronger guarantee than scanning for one after the fact.
    """
    typed = {f.name: f.type for f in fields(SourceDescriptor)}
    assert set(typed) == {
        "source_id", "authority", "latency_class", "granularity", "retrieval"
    }
    for name, annotation in typed.items():
        assert "dict" not in str(annotation).lower(), f"{name} could carry arbitrary keys"
        assert "Any" not in str(annotation), f"{name} is untyped"

    # And a credential offered to any of them is refused by the constructor.
    secret = Credential("issdc-session", "PRADAN-SESSION-abc123")
    for name in typed:
        with pytest.raises(ContractViolation):
            adapters.descriptor(**{name: secret})


def test_an_adapter_persisting_a_credential_in_provenance_is_refused():
    """E5 §13: never persisted to an artifact. Provenance is persisted through E3."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(
            adapters.AdapterPersistingACredentialInProvenance(), selector=SELECTOR
        )
    assert caught.value.gate == "credential-boundary"


def test_the_conforming_descriptor_records_that_credentials_are_needed_without_carrying_one():
    """The whole of what may cross: a boolean, mirroring the Tier 0 retrieval descriptor."""
    described = verify_descriptor(adapters.ConformingAdapter())
    assert described.retrieval.requires_credentials is True
    assert "credential" not in described.to_dict()
    assert set(described.retrieval.to_dict()) == {
        "provider", "locator", "requires_credentials"
    }


# ═══════════════════════════════════════════ ADR-0023 / E5 §12 — Tier 0 is referenced


def test_an_artifact_holding_raw_bytes_is_refused():
    """ADR-0023, STD-23, E5 §11(iv), E5 §12 all land on this one refusal."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterHoldingRawBytes(), selector=SELECTOR)
    assert caught.value.gate == CONFORMANCE_GATE
    assert "referenced, never" in caught.value.message


def test_a_raw_artifact_cannot_carry_bytes():
    """The type has no such field, and this asserts it never gains one.

    An artifact that *can* hold the bytes will hold them, and a whole-day archive would be
    materialised without anyone deciding to (E5 §12).
    """
    names = {f.name for f in fields(RawArtifact)}
    assert not (names & FORBIDDEN_ARTIFACT_FIELDS), (
        f"RawArtifact gained {sorted(names & FORBIDDEN_ARTIFACT_FIELDS)}"
    )
    assert names == {"digest", "size_bytes", "retrieval", "cache_path"}


def test_an_artifact_requires_a_way_to_re_acquire_it():
    """ADR-0023: any stage must be able to re-acquire from the descriptor."""
    with pytest.raises(ContractViolation) as caught:
        RawArtifact(digest=Digest("a" * 64), size_bytes=1, retrieval=None)
    assert caught.value.pointer == "/retrieval"


def test_an_evicted_cache_is_not_an_error():
    """Local copies are evictable caches, never the system of record (ADR-0023)."""
    artifact = RawArtifact(
        digest=Digest("a" * 64), size_bytes=1, retrieval=adapters.descriptor().retrieval
    )
    assert artifact.cache_path is None
    assert artifact.is_cached is False
    assert adapters.acquisition().artifact.is_cached is True


# ═══════════════════════════════════════════ ADR-0004 / E5 §11 — both times


def test_an_adapter_omitting_the_ingest_time_is_refused():
    """E5 §11(i): every newly ingested Observation carries valid_time AND ingest_time."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterOmittingTheIngestTime(), selector=SELECTOR)
    assert "ingest_time" in caught.value.message


def test_acquisition_provenance_requires_a_non_null_ingest_time():
    """ADR-0022's null is for historical rows, which have no acquisition to describe."""
    with pytest.raises(ContractViolation) as caught:
        AcquisitionProvenance(
            run_id=adapters.RUN,
            source_id=Identifier("issdc-pradan"),
            artifact_digest=Digest("a" * 64),
            ingest_time=None,
        )
    assert caught.value.pointer == "/ingest_time"


def test_there_is_no_way_to_stamp_a_historical_row():
    """E5 §11(ii): no code path writes a non-null ingest_time for historical data.

    The boundary module exports a clock read and a monotonic reading, and nothing that takes
    a row, a dataset or a date and returns a time for it. Backfilling would require calling
    `stamp()` and attaching the result to old rows — which is a deliberate act that
    `domain.invariants.ingest_time_is_not_backfilled` detects.
    """
    exported = set(boundary.__all__)
    assert exported == {"monotonic", "stamp", "stamp_from_epoch"}
    for forbidden in ("backfill", "infer", "default_ingest_time", "for_row", "impute"):
        assert not hasattr(boundary, forbidden)


def test_a_misattributed_artifact_is_refused_by_the_checker():
    """Provenance pointing at other bytes is worse than none: it looks like attribution."""
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(adapters.AdapterMisattributingItsArtifact(), selector=SELECTOR)
    assert caught.value.gate == CONFORMANCE_GATE


def test_acquisition_refuses_mismatched_parts_at_construction():
    """The constructor enforces it too, so the checker is a second line rather than the only."""
    with pytest.raises(ContractViolation) as caught:
        Acquisition(
            artifact=adapters.acquisition().artifact,
            provenance=AcquisitionProvenance(
                run_id=adapters.RUN,
                source_id=Identifier("issdc-pradan"),
                artifact_digest=Digest("b" * 64),
                ingest_time=Timestamp("2024-04-03T12:00:00Z"),
            ),
        )
    assert "looks like attribution" in caught.value.message


# ═══════════════════════════════════════════ E5 §9 — a refusal is conformant


def test_an_adapter_that_aborts_is_not_a_conformance_failure():
    """E5 §9: `aborted` leaves no observations. Aborting is what an adapter should do.

    The original error is re-raised unchanged rather than wrapped, so the caller sees that
    the archive was unreachable rather than that conformance failed.
    """

    class UnreachableAdapter:
        def descriptor(self):
            return adapters.descriptor()

        def acquire(self, selector):
            raise UnavailableResource("PRADAN portal did not respond after 3 attempts")

    with pytest.raises(UnavailableResource):
        verify_conformance(UnreachableAdapter(), selector=SELECTOR)


# ═══════════════════════════════════════════ no registry, no dispatch, no framework


def test_the_contract_registers_nothing():
    """ADR-0003 does not authorise a source-plugin registry, dispatch layer or framework.

    ADR-0025 classifies all three as paid abstractions, forbidden until a second source
    exists. A Protocol declares what a caller may rely on and constructs nothing; this
    asserts the module never grows the thing the ADR refuses.
    """
    import contexts.ingest.contract as module

    for forbidden in ("register", "REGISTRY", "ADAPTERS", "get_adapter", "load_adapter",
                      "dispatch", "AdapterFactory", "SourceAdapterBase"):
        assert not hasattr(module, forbidden), f"contract.py grew {forbidden}"


def test_the_protocol_is_not_a_base_class():
    """A conforming adapter inherits nothing, which is what makes the seam free (ADR-0025).

    `isinstance` succeeds by structure, not by ancestry. An adapter that had to inherit
    something in order to be recognised would be an adapter the framework owns.
    """
    assert SourceAdapter not in adapters.ConformingAdapter.__mro__
    assert adapters.ConformingAdapter.__mro__ == (adapters.ConformingAdapter, object)
    assert isinstance(adapters.ConformingAdapter(), SourceAdapter)


# ═══════════════════════════════════════════ the descriptor's own rules


def test_the_latency_class_is_a_comparable_quantity():
    """ADR-0001's non-goal on real-time services is only checkable if latency is a number."""
    assert LatencyClass("~33d").seconds == 33 * 86400
    assert LatencyClass("5m").seconds == 300
    assert LatencyClass("~33d").is_approximate is True
    assert LatencyClass("5m").is_approximate is False


@pytest.mark.parametrize(
    "bad", ["about a month", "slow", "33", "d", "", "33 days", "~33w", "-5m", None]
)
def test_a_latency_that_cannot_be_compared_is_refused(bad):
    with pytest.raises(ContractViolation):
        LatencyClass(bad)


def test_the_issdc_channel_is_far_outside_anything_real_time():
    """The measurement behind ADR-0001's non-goal, stated as a test rather than as prose."""
    assert LatencyClass("~33d").seconds == 2_851_200


@pytest.mark.parametrize(
    "field, bad",
    [
        ("source_id", "issdc-pradan"),
        ("authority", ""),
        ("latency_class", "~33d"),
        ("granularity", "daily-archive"),
        ("retrieval", {"provider": "x", "locator": "y"}),
    ],
)
def test_the_descriptor_refuses_raw_values_where_a_typed_one_is_required(field, bad):
    with pytest.raises(ContractViolation) as caught:
        adapters.descriptor(**{field: bad})
    assert caught.value.pointer == f"/{field}"


def test_the_descriptor_serialises_to_the_shape_the_manifest_expects():
    """The retrieval descriptor an adapter publishes and the one a manifest records are the
    same fact; two shapes for one fact is how they come to disagree (M2/E4/#14)."""
    assert adapters.descriptor().retrieval.to_dict() == {
        "provider": "ISSDC PRADAN",
        "locator": "aditya-l1/solexs/l1/2024-03-01",
        "requires_credentials": True,
    }


@pytest.mark.parametrize("cls", [SourceDescriptor, RetrievalDescriptor, RawArtifact,
                                 AcquisitionProvenance, Acquisition])
def test_every_contract_type_is_frozen(cls):
    """A descriptor that can be edited after publication has not been published."""
    instance = {
        SourceDescriptor: adapters.descriptor(),
        RetrievalDescriptor: adapters.descriptor().retrieval,
        RawArtifact: adapters.acquisition().artifact,
        AcquisitionProvenance: adapters.acquisition().provenance,
        Acquisition: adapters.acquisition(),
    }[cls]
    first = fields(instance)[0].name
    with pytest.raises(FrozenInstanceError):
        setattr(instance, first, None)


def test_acquisition_provenance_logs_exactly_what_e5_permits():
    """E5 §14: log source_id, instrument_id, artifact_digest, counts. Never cookies or URLs."""
    record = adapters.acquisition().provenance.to_dict()
    assert set(record) == {
        "run_id", "source_id", "artifact_digest", "ingest_time", "instruments"
    }
    for forbidden in ("cookie", "session", "url", "token", "bytes", "credential"):
        assert forbidden not in record


def test_the_boundary_produces_a_utc_timestamp_the_domain_accepts():
    """The one sanctioned clock read (ADR-0004), returning a value the pure domain validates."""
    stamped = boundary.stamp()
    assert isinstance(stamped, Timestamp)
    assert stamped.is_utc
    assert str(stamped).endswith("Z")


def test_the_epoch_stamp_and_the_clock_stamp_agree_on_form():
    fixed = boundary.stamp_from_epoch(1_709_251_200)
    assert str(fixed) == "2024-03-01T00:00:00Z"
    assert fixed.is_utc


def test_monotonic_cannot_become_a_timestamp():
    """It has no epoch, so it can measure elapsed time and cannot record when."""
    first = boundary.monotonic()
    assert isinstance(first, float)
    assert boundary.monotonic() >= first
    with pytest.raises(ContractViolation):
        Timestamp(str(first))

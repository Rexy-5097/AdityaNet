"""The `SourceAdapter` contract, and the conformance check every adapter must pass.

E5 §4 fixes the interface:

    SourceAdapter:
      descriptor()        -> SourceDescriptor
      acquire(selector)   -> RawArtifact + AcquisitionProvenance

WHY A PROTOCOL AND NOT A BASE CLASS
------------------------------------
ADR-0003 is explicit about what it does *not* authorise: *"a source-plugin registry, a
dispatch layer, or a configurable adapter framework. Those are paid abstractions and remain
forbidden until a second source exists."* ADR-0025 lists "generic base classes" in the same
category.

A `typing.Protocol` is none of those. It declares what a caller may rely on; it is not
inherited from, it constructs nothing, it dispatches nothing, and deleting it would not change
one line of an adapter's behaviour. Under ADR-0025's test it is a free seam: stating what an
acquisition channel must provide would still be the correct design with exactly one source
forever, because the parser downstream has to be able to trust its input regardless of which
channel produced it.

There is no registry here. No `register()`, no adapter table, no lookup by `source_id`, no
configuration. `verify_conformance` takes an adapter a caller already holds.

WHAT CONFORMANCE MEANS
----------------------
Structural conformance — having the right methods — is the least of it, and is the part a type
checker already handles. `verify_conformance` checks the parts that decide whether the rest of
the platform can trust the adapter's output, which no type system checks:

  1. `descriptor()` returns a real `SourceDescriptor`, and returns the *same* one every time.
     A descriptor that varies between calls means the channel's latency or authority is
     whatever it happened to be when someone asked.
  2. Nothing the adapter publishes carries a credential (STD-19, E5 §13).
  3. `acquire()` returns an `Acquisition` whose provenance names the same digest as its
     artifact, with an `ingest_time` that is present and non-null (E5 §11(i), ADR-0004).
  4. The artifact carries no bytes and does carry a retrieval descriptor, so Tier 0 is
     referenced rather than redistributed (ADR-0023, STD-23, E5 §11(iv)).

The check is offered as a function rather than imposed as a base class for the same reason the
interface is a Protocol: an adapter that must inherit something in order to be checked is an
adapter the framework owns.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from contexts.ingest.acquisition import Acquisition, AcquisitionProvenance, RawArtifact
from contexts.ingest.credentials import assert_credential_free
from contexts.ingest.descriptor import SourceDescriptor
from contexts.ingest.errors import PolicyRejection
from domain.errors import ContractViolation
from domain.values import Timestamp

#: The gate named when an adapter fails conformance. One string, so a caller matching on it
#: and a test asserting it cannot drift.
CONFORMANCE_GATE = "source-adapter-conformance"

#: Fields a `RawArtifact` may never gain. Checked by name because the rule is about the type's
#: shape rather than about any particular value: an artifact that *can* hold bytes will hold
#: them, and Tier 0 redistribution becomes one attribute away (ADR-0023, E5 §12).
FORBIDDEN_ARTIFACT_FIELDS = frozenset({"bytes", "content", "data", "body", "payload", "raw"})


@runtime_checkable
class SourceAdapter(Protocol):
    """A channel of acquisition (ADR-0003).

    `runtime_checkable` so `isinstance` can report a missing method as a conformance failure
    rather than as an `AttributeError` three frames later. It checks method *presence* only,
    which is why `verify_conformance` exists and does the rest.
    """

    def descriptor(self) -> SourceDescriptor:
        """What this channel is: authority, latency class, granularity, how to retrieve.

        Must be constant for the life of the adapter. A channel whose declared latency
        changes between calls has not declared a latency.
        """
        ...

    def acquire(self, selector: str) -> Acquisition:
        """Retrieve one artifact, returning it with the provenance of retrieving it.

        `selector` names what to fetch in the channel's own terms — a date for a daily
        archive, a product identifier elsewhere. It is a plain string because interpreting it
        is the adapter's business; a structured selector type would be a framework deciding
        for adapters that do not yet exist (ADR-0003, ADR-0025).

        Raises `UnavailableResource` when the channel cannot be reached and retries are
        exhausted, `IntegrityFailure` when the retrieved bytes do not match their digest.
        Neither leaves partial state: E5 §9 states that `aborted` leaves no observations.
        """
        ...


def _fail(message: str) -> None:
    raise PolicyRejection(CONFORMANCE_GATE, message)


def verify_descriptor(adapter: object) -> SourceDescriptor:
    """Check `descriptor()` and return what it produced.

    Separated from the full check because an adapter can be asked what it is without being
    asked to fetch anything, and E5 §18's acceptance criterion — the ISSDC channel registered
    with latency class `~33d`, granularity `daily-archive` — is exactly that question.
    """
    if not hasattr(adapter, "descriptor"):
        _fail(f"{type(adapter).__name__} has no descriptor(); E5 §4 requires one")

    descriptor = adapter.descriptor()
    if not isinstance(descriptor, SourceDescriptor):
        _fail(
            f"descriptor() returned {type(descriptor).__name__}, not a SourceDescriptor. "
            f"A channel that describes itself in its own vocabulary cannot be compared to "
            f"another one."
        )

    again = adapter.descriptor()
    if again != descriptor:
        _fail(
            "descriptor() is not constant between calls. A channel whose declared latency "
            "or authority varies has declared neither."
        )

    assert_credential_free(descriptor, what="the source descriptor")
    return descriptor


def verify_acquisition(acquisition: object) -> Acquisition:
    """Check one `acquire()` result against everything the platform will assume about it."""
    if not isinstance(acquisition, Acquisition):
        _fail(
            f"acquire() returned {type(acquisition).__name__}, not an Acquisition. E5 §4 "
            f"requires a RawArtifact and its AcquisitionProvenance together."
        )

    artifact: RawArtifact = acquisition.artifact
    provenance: AcquisitionProvenance = acquisition.provenance

    # Tier 0 is referenced, never redistributed (ADR-0023, STD-23, E5 §11(iv)).
    carried = FORBIDDEN_ARTIFACT_FIELDS & set(vars(artifact))
    if carried:
        _fail(
            f"the raw artifact carries {sorted(carried)}. Tier 0 bytes are referenced, never "
            f"held: local copies are evictable caches and a whole-day archive must not be "
            f"materialised (ADR-0023, E5 §12)."
        )
    if artifact.retrieval is None:
        _fail(
            "the raw artifact has no retrieval descriptor, so these bytes cannot be "
            "re-acquired. ADR-0023 requires that any stage can."
        )

    # Both times, and the ingest one non-null (E5 §11(i), ADR-0004).
    if not isinstance(provenance.ingest_time, Timestamp):
        _fail(
            "the acquisition provenance has no ingest_time. It is stamped at this boundary "
            "and nowhere else (ADR-0004); ADR-0022's null is for historical rows, which have "
            "no acquisition to describe."
        )

    # The record must point at the artifact it accompanies. `Acquisition` enforces this at
    # construction, so reaching here means it was built some other way.
    if artifact.digest != provenance.artifact_digest:
        _fail(
            f"the provenance records {provenance.artifact_digest.short} but the artifact is "
            f"{artifact.digest.short}."
        )

    assert_credential_free(provenance, what="the acquisition provenance")
    assert_credential_free(artifact, what="the raw artifact")
    return acquisition


def verify_conformance(adapter: object, *, selector: str) -> Acquisition:
    """Run the full check against a real adapter, and return what it acquired.

    This is what M3/E5/#16 will run against the ISSDC-PRADAN adapter, and what any future
    channel will have to satisfy before its data can enter the platform. It performs a real
    acquisition — a conformance check that stubbed out the fetch would verify the parts that
    were never in doubt.
    """
    if not isinstance(adapter, SourceAdapter):
        _fail(
            f"{type(adapter).__name__} does not satisfy the SourceAdapter protocol; "
            f"E5 §4 requires descriptor() and acquire()."
        )

    verify_descriptor(adapter)

    try:
        acquired = adapter.acquire(selector)
    except (PolicyRejection, ContractViolation):
        # A refusal is conformant behaviour — an adapter that aborts rather than returning
        # something wrong is doing exactly what E5 §9 requires. Re-raised unchanged so the
        # caller sees the real reason rather than a conformance message wrapping it.
        raise

    return verify_acquisition(acquired)


__all__ = [
    "CONFORMANCE_GATE",
    "FORBIDDEN_ARTIFACT_FIELDS",
    "SourceAdapter",
    "verify_acquisition",
    "verify_conformance",
    "verify_descriptor",
]

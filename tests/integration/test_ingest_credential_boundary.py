"""The credential boundary — the integration test §15 row 15 names.

`| 15 | 15 | E5 | 200 | M | 11 | contract conformance | — | credential-boundary |`

E5 §13 makes Ingest the highest-sensitivity context in the system: it holds the only secrets.
STD-19 and E5 §11(iii) say what must never happen — a secret logged, persisted to an artifact,
or crossing a context boundary.

This is an integration test rather than a unit test because a leak is not a property of the
`Credential` type. It is a property of a *path*: the secret is fine sitting in memory and
becomes a defect the moment something writes it somewhere. So each test below follows a real
path outward — into a log record, into a provenance artifact registered with the kernel, into
a manifest, into a formatted string — and checks what arrives at the far end.

The bytes on disk are read back and searched for the secret. Not the object, not the
serialisation function's return value: the file. That is the only check that would have caught
the class of leak this is written against, where a redaction works everywhere except the one
path nobody tested.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from contexts.ingest import (
    Acquisition,
    AcquisitionProvenance,
    CREDENTIAL_BOUNDARY,
    Credential,
    PolicyRejection,
    RawArtifact,
    RetrievalDescriptor,
    assert_credential_free,
    verify_conformance,
)
from contexts.ingest.credentials import REDACTED, SECRET_FIELD_NAMES
from contexts.ingest.tests import adapters
from domain.values import Digest, Identifier, RunId, Timestamp
from kernel.provenance import ProvenanceStore, begin_run

#: A value distinctive enough that finding it anywhere is unambiguous.
SECRET = "PRADAN-SESSION-3f9c1a7e-do-not-log-me"


def a_credential() -> Credential:
    return Credential("issdc-pradan-session", SECRET)


# ═══════════════════════════════════════════ the secret does not reach a log


def test_a_credential_cannot_be_logged_through_any_common_route(tmp_path, caplog):
    """The routes a secret actually escapes by: an f-string, a %-format, a repr, a traceback.

    E5 §14 forbids logging cookies. Enforcement is on the type rather than on every call site,
    because "remember not to log this" is the instruction that fails.
    """
    secret = a_credential()
    log_file = tmp_path / "ingest.log"

    handler = logging.FileHandler(log_file)
    logger = logging.getLogger("ingest.boundary.test")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        logger.info("acquiring with %s", secret)
        logger.info(f"acquiring with {secret}")
        logger.info("acquiring with %r", secret)
        logger.info("padded: %s", f"{secret:>40}")
        logger.debug("structured: %s", {"session": str(secret)})
        try:
            raise RuntimeError(f"auth failed for {secret}")
        except RuntimeError:
            logger.exception("acquisition failed")
    finally:
        logger.removeHandler(handler)
        handler.close()

    written = log_file.read_text()
    assert SECRET not in written, "the secret reached the log file"
    assert REDACTED in written, "nothing was written; the test would pass vacuously"


def test_the_secret_is_still_readable_where_it_is_supposed_to_be():
    """Redaction that also hid the value from the adapter would make the type unusable.

    `reveal()` is the single named accessor, so `grep -rn 'reveal()' contexts/` enumerates
    every place in the repository where a secret is touched.
    """
    assert a_credential().reveal() == SECRET
    assert str(a_credential()) != SECRET
    assert repr(a_credential()) != SECRET


# ═══════════════════════════════════════════ the secret does not reach an artifact


def test_a_credential_cannot_be_serialised_into_an_artifact():
    """E5 §13: never persisted to an artifact. `json.dumps` refuses it outright."""
    with pytest.raises(TypeError):
        json.dumps({"session": a_credential()})
    assert not hasattr(Credential, "to_dict")


def test_provenance_registered_with_the_kernel_contains_no_secret(tmp_path):
    """The full path: acquire → serialise provenance → register → read the file back.

    Reading the bytes from disk is the point. A check on the dict would pass even if the
    serialiser had been changed to include the secret somewhere the dict did not show.
    """
    store = ProvenanceStore(tmp_path / "store")
    run = begin_run(context="ingest", event="acquire")

    # An adapter authenticates with a real secret and publishes provenance that must not
    # carry it.
    secret = a_credential()
    assert secret.reveal() == SECRET  # the adapter genuinely used it

    provenance = AcquisitionProvenance(
        run_id=RunId(run.run_id.value if hasattr(run.run_id, "value") else str(run.run_id)),
        source_id=Identifier("issdc-pradan"),
        artifact_digest=Digest("a" * 64),
        ingest_time=Timestamp("2024-04-03T12:00:00Z"),
        instruments=(Identifier("solexs"),),
    )
    assert_credential_free(provenance, what="the acquisition provenance")

    payload = json.dumps(provenance.to_dict(), sort_keys=True).encode()
    artifact = store.put_bytes(payload)

    on_disk = (store.root / "artifacts" / f"{artifact.digest.hex}.json").read_text()
    assert SECRET not in on_disk
    assert SECRET not in payload.decode()
    assert "issdc-pradan" in payload.decode(), "nothing was recorded; the check is vacuous"


def test_a_manifest_built_from_a_descriptor_carries_no_secret():
    """The descriptor an adapter publishes becomes a Tier 0 manifest's retrieval descriptor.

    M2/E4/#14's `manifest.schema.json` records *how* to re-acquire and has no field for a
    secret; this shows the ingest side produces exactly that shape and nothing more.
    """
    retrieval = adapters.descriptor().retrieval.to_dict()
    assert set(retrieval) == {"provider", "locator", "requires_credentials"}
    assert retrieval["requires_credentials"] is True
    assert SECRET not in json.dumps(retrieval)
    for name in SECRET_FIELD_NAMES:
        assert name not in retrieval


# ═══════════════════════════════════════════ the boundary refuses the crossing


def test_the_boundary_refuses_an_object_carrying_a_credential():
    with pytest.raises(PolicyRejection) as caught:
        assert_credential_free({"session": a_credential()}, what="a log record")
    assert caught.value.gate == CREDENTIAL_BOUNDARY
    assert SECRET not in str(caught.value), "the rejection message leaked the secret"


@pytest.mark.parametrize(
    "carrier, description",
    [
        (lambda c: c, "the credential itself"),
        (lambda c: {"session": c}, "a mapping value"),
        (lambda c: [1, {"deep": {"inner": c}}], "nested three levels down"),
        (lambda c: (c,), "inside a tuple"),
        (lambda c: {"a": [{"b": [c]}]}, "alternating mappings and sequences"),
    ],
    ids=["direct", "mapping", "nested", "tuple", "alternating"],
)
def test_a_credential_is_found_wherever_it_is_hidden(carrier, description):
    """A shallow check would pass on four of these five."""
    with pytest.raises(PolicyRejection):
        assert_credential_free(carrier(a_credential()), what=description)


def test_a_raw_string_in_a_secret_named_field_is_also_refused():
    """The backstop for the mistake of never using the type at all.

    Caught by field *name*, not by guessing what a secret looks like: a heuristic over values
    would be both wrong and unfalsifiable.
    """
    with pytest.raises(PolicyRejection):
        assert_credential_free({"cookie": "sessionid=abc123"}, what="a request record")


def test_the_boundary_permits_what_should_cross():
    """A checker that refused everything would be satisfied by every test above."""
    assert_credential_free(adapters.descriptor(), what="the source descriptor")
    assert_credential_free(adapters.acquisition(), what="an acquisition")
    assert_credential_free(
        {"source_id": "issdc-pradan", "requires_credentials": True},
        what="a manifest retrieval descriptor",
    )


def test_a_cyclic_structure_does_not_crash_the_check():
    """A leak check that raises RecursionError is a leak check that gets removed."""
    loop: dict = {"self": None}
    loop["self"] = loop
    assert_credential_free(loop, what="a cyclic record")

    loop_with_secret: dict = {"self": None, "session": a_credential()}
    loop_with_secret["self"] = loop_with_secret
    with pytest.raises(PolicyRejection):
        assert_credential_free(loop_with_secret, what="a cyclic record")


# ═══════════════════════════════════════════ conformance enforces it end to end


def test_the_conformance_check_refuses_an_adapter_that_would_leak(tmp_path):
    """The boundary is not advisory: an adapter that leaks cannot pass conformance.

    This is what #16's ISSDC adapter will be run against before its data is allowed in.
    """
    with pytest.raises(PolicyRejection) as caught:
        verify_conformance(
            adapters.AdapterPersistingACredentialInProvenance(), selector="2024-03-01"
        )
    assert caught.value.gate == CREDENTIAL_BOUNDARY


def test_a_conforming_adapter_passes_and_leaks_nothing(tmp_path):
    """The positive path, checked at the far end rather than at the type."""
    acquired: Acquisition = verify_conformance(
        adapters.ConformingAdapter(), selector="2024-03-01"
    )
    serialised = json.dumps(acquired.provenance.to_dict(), sort_keys=True)
    assert SECRET not in serialised
    for name in SECRET_FIELD_NAMES:
        assert name not in serialised


def test_an_artifact_path_is_a_cache_not_a_secret(tmp_path):
    """A cache path is recorded; it is not sensitive and must not be redacted into uselessness."""
    artifact = RawArtifact(
        digest=Digest("a" * 64),
        size_bytes=1,
        retrieval=RetrievalDescriptor("ISSDC PRADAN", "aditya-l1/solexs", True),
        cache_path=Path(tmp_path / "cache" / "frame.fits"),
    )
    assert_credential_free(artifact, what="a raw artifact")
    assert artifact.is_cached

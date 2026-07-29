"""ProvenanceStore and graph traversal.

The store is the only code in this package that writes, so every soundness property of the
provenance graph is enforced or violated here. Each invariant below has at least one test
that makes it fail.
"""

from __future__ import annotations

import json

import pytest

from kernel.provenance.dag import ancestors, producers, would_create_cycle
from kernel.provenance.digest import Digest, digest_bytes
from kernel.provenance.errors import IntegrityFailure, ProvenanceFailure
from kernel.provenance.record import ProvenanceRecord
from kernel.provenance.run import RunStatus, begin_run
from kernel.provenance.store import ProvenanceStore


@pytest.fixture()
def store(tmp_path) -> ProvenanceStore:
    return ProvenanceStore(tmp_path / "prov")


@pytest.fixture()
def run():
    return begin_run("provenance", "test")


# ── Artifact registration ───────────────────────────────────────────────────────

def test_put_bytes_registers_and_returns_an_artifact(store):
    artifact = store.put_bytes(b"hello")
    assert artifact.digest == digest_bytes(b"hello")
    assert artifact.size_bytes == 5
    assert store.has_artifact(artifact.digest)


def test_put_file_digests_without_loading(store, tmp_path):
    path = tmp_path / "f.bin"
    path.write_bytes(b"payload" * 1000)
    artifact = store.put_file(path)
    assert artifact.digest == digest_bytes(b"payload" * 1000)
    assert artifact.size_bytes == 7000


def test_registering_identical_bytes_twice_is_idempotent(store):
    first = store.put_bytes(b"same")
    second = store.put_bytes(b"same")
    assert first == second
    assert len(list((store.root / "artifacts").glob("*.json"))) == 1


def test_get_artifact_round_trips(store):
    artifact = store.put_bytes(b"round trip")
    assert store.get_artifact(artifact.digest) == artifact


def test_get_unregistered_artifact_fails(store):
    with pytest.raises(ProvenanceFailure, match="not registered"):
        store.get_artifact(digest_bytes(b"never registered"))


def test_negative_size_is_rejected():
    from kernel.provenance.artifact import Artifact
    with pytest.raises(ValueError, match="negative"):
        Artifact(digest=digest_bytes(b"x"), size_bytes=-1)


# ── Append-only ─────────────────────────────────────────────────────────────────

def test_append_only_is_structural_not_enforced(store):
    """Identical content hashes to an identical name, so rewriting is a no-op and different
    content cannot reach an existing name. There is no update path to test because there is
    no update path to write."""
    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")

    artifact = store.put_bytes(b"immutable")
    before = (store.root / "artifacts" / f"{artifact.digest.hex}.json").read_text()
    store.put_bytes(b"immutable")
    after = (store.root / "artifacts" / f"{artifact.digest.hex}.json").read_text()
    assert before == after


def test_a_tampered_artifact_registration_is_detected(store):
    """Editing the store outside this package is exactly what an integrity system exists to
    catch."""
    artifact = store.put_bytes(b"tamper target")
    path = store.root / "artifacts" / f"{artifact.digest.hex}.json"
    path.write_text(json.dumps({"digest": artifact.digest.hex, "size_bytes": 999}))

    with pytest.raises(IntegrityFailure, match="registered with size"):
        store.put_bytes(b"tamper target")


# ── Recording ───────────────────────────────────────────────────────────────────

def test_record_links_inputs_to_outputs(store, run):
    source = store.put_bytes(b"source")
    derived = digest_bytes(b"derived")

    record = store.record(run, [source.digest], [derived])
    assert record.run_id == run.run_id
    assert record.inputs == (source.digest,)
    assert record.outputs == (derived,)


def test_record_is_content_addressed_and_order_independent(store, run):
    a = store.put_bytes(b"a")
    b = store.put_bytes(b"b")
    out1, out2 = digest_bytes(b"o1"), digest_bytes(b"o2")

    first = store.record(run, [a.digest, b.digest], [out1, out2])
    second = store.record(run, [b.digest, a.digest], [out2, out1])

    assert first.digest == second.digest, "record identity depends on argument order"
    assert len(list((store.root / "records").glob("*.json"))) == 1


def test_recording_the_same_fact_twice_is_idempotent(store, run):
    source = store.put_bytes(b"s")
    out = digest_bytes(b"o")
    store.record(run, [source.digest], [out])
    store.record(run, [source.digest], [out])
    assert len(list(store.records())) == 1


def test_record_round_trips_through_the_store(store, run):
    source = store.put_bytes(b"s")
    written = store.record(run, [source.digest], [digest_bytes(b"o")])
    assert store.get_record(written.digest) == written


def test_records_iterates_everything(store, run):
    a = store.put_bytes(b"a")
    store.record(run, [a.digest], [digest_bytes(b"o1")])
    store.record(run, [a.digest], [digest_bytes(b"o2")])
    assert len(list(store.records())) == 2


# ── Deliberate violations: soundness ────────────────────────────────────────────

def test_an_unregistered_input_is_rejected(store, run):
    """An unregistered input is a claim about bytes the store has never seen, which breaks
    the audit chain at the exact step an auditor would follow (VVMP §7)."""
    with pytest.raises(ProvenanceFailure, match="not a registered artifact"):
        store.record(run, [digest_bytes(b"ghost")], [digest_bytes(b"out")])


def test_a_self_referential_record_is_rejected(store, run):
    same = store.put_bytes(b"self")
    with pytest.raises(ProvenanceFailure, match="cycle"):
        store.record(run, [same.digest], [same.digest])


def test_a_cycle_across_two_records_is_rejected(store, run):
    a = store.put_bytes(b"a")
    b_digest = digest_bytes(b"b")
    store.record(run, [a.digest], [b_digest])

    # b is now downstream of a. Registering b and claiming it produced a closes the loop.
    store.put_bytes(b"b")
    with pytest.raises(ProvenanceFailure, match="cycle"):
        store.record(run, [b_digest], [a.digest])


def test_a_longer_cycle_is_rejected(store, run):
    a = store.put_bytes(b"a")
    b, c = digest_bytes(b"b"), digest_bytes(b"c")
    store.record(run, [a.digest], [b])
    store.put_bytes(b"b")
    store.record(run, [b], [c])
    store.put_bytes(b"c")

    with pytest.raises(ProvenanceFailure, match="cycle"):
        store.record(run, [c], [a.digest])


def test_a_record_with_no_outputs_is_rejected(run):
    with pytest.raises(ValueError, match="records nothing"):
        ProvenanceRecord(run_id=run.run_id, inputs=(), outputs=())


def test_duplicate_digests_within_one_side_are_rejected(run):
    d = digest_bytes(b"d")
    with pytest.raises(ValueError, match="duplicate"):
        ProvenanceRecord(run_id=run.run_id, inputs=(), outputs=(d, d))
    with pytest.raises(ValueError, match="duplicate"):
        ProvenanceRecord(run_id=run.run_id, inputs=(d, d), outputs=(digest_bytes(b"o"),))


def test_a_record_must_name_a_run(run):
    with pytest.raises(ValueError, match="name the run"):
        ProvenanceRecord(run_id="", inputs=(), outputs=(digest_bytes(b"o"),))


def test_a_tampered_record_is_detected_on_read(store, run):
    """Verify-on-read. A store edited in place is detected for the cost of one small hash."""
    source = store.put_bytes(b"s")
    record = store.record(run, [source.digest], [digest_bytes(b"o")])
    path = store.root / "records" / f"{record.digest.hex}.json"

    forged = ProvenanceRecord(
        run_id=record.run_id, inputs=(), outputs=(digest_bytes(b"forged"),)
    )
    path.write_text(forged.to_json())

    with pytest.raises(IntegrityFailure, match="has been modified outside this package"):
        store.get_record(record.digest)


def test_a_missing_record_is_reported(store):
    with pytest.raises(ProvenanceFailure, match="does not exist"):
        store.get_record(digest_bytes(b"absent"))


# ── Write confinement (TIS E3 §13) ──────────────────────────────────────────────

def test_no_write_escapes_the_store_root(store, run):
    """Every path the store actually writes lies beneath its root.

    The fixture starts empty, so this test must first cause writes or it asserts nothing —
    the guard below is what caught it doing exactly that.
    """
    source = store.put_bytes(b"confinement")
    store.record(run, [source.digest], [digest_bytes(b"derived")])

    written = list(store.root.rglob("*.json"))
    assert len(written) >= 2, "expected an artifact and a record to compare against"
    for path in written:
        assert path.resolve().is_relative_to(store.root)


def test_path_construction_is_checked_against_the_root(store):
    """Confinement is enforced by resolving and comparing, not by trusting that a Digest
    cannot contain a separator. Relying on an upstream validator for a filesystem boundary
    is how directory traversal happens, so the check does not depend on one.
    """
    digest = digest_bytes(b"legitimate")
    resolved = store._path("artifacts", digest)
    assert resolved.is_relative_to(store.root)
    assert resolved.name == f"{digest.hex}.json"


def test_a_digest_cannot_carry_a_path_separator():
    """The second, independent line: the value object rejects anything non-hex, so a
    traversal payload cannot become a Digest in the first place."""
    for payload in ("../" * 21 + "x", "a/b", "..", "\x00" * 64):
        with pytest.raises(ValueError):
            Digest(payload)


def test_store_creates_its_own_layout(tmp_path):
    root = tmp_path / "fresh" / "nested"
    created = ProvenanceStore(root)
    assert (created.root / "artifacts").is_dir()
    assert (created.root / "records").is_dir()


# ── Graph traversal ─────────────────────────────────────────────────────────────

def test_ancestors_of_an_unknown_digest_is_empty(store):
    assert store.ancestors(digest_bytes(b"unknown")) == frozenset()


def test_ancestors_walks_one_hop(store, run):
    a = store.put_bytes(b"a")
    b = digest_bytes(b"b")
    store.record(run, [a.digest], [b])
    assert store.ancestors(b) == frozenset({a.digest})


def test_ancestors_is_transitive(store, run):
    a = store.put_bytes(b"a")
    b, c = digest_bytes(b"b"), digest_bytes(b"c")
    store.record(run, [a.digest], [b])
    store.put_bytes(b"b")
    store.record(run, [b], [c])

    assert store.ancestors(c) == frozenset({a.digest, b})


def test_ancestors_handles_a_diamond_without_duplication(store, run):
    root = store.put_bytes(b"root")
    left, right = digest_bytes(b"left"), digest_bytes(b"right")
    store.record(run, [root.digest], [left, right])
    store.put_bytes(b"left")
    store.put_bytes(b"right")
    merged = digest_bytes(b"merged")
    store.record(run, [left, right], [merged])

    assert store.ancestors(merged) == frozenset({left, right, root.digest})


def test_ancestors_excludes_the_digest_itself(store, run):
    a = store.put_bytes(b"a")
    b = digest_bytes(b"b")
    store.record(run, [a.digest], [b])
    assert b not in store.ancestors(b)


def test_ancestors_terminates_on_a_corrupted_cyclic_graph():
    """record() rejects cycles at write time. This is the second line, for a store that was
    corrupted or hand-edited — traversal must terminate rather than recurse forever."""
    a, b = digest_bytes(b"a"), digest_bytes(b"b")
    cyclic = [
        ProvenanceRecord(run_id="R" * 26, inputs=(a,), outputs=(b,)),
        ProvenanceRecord(run_id="R" * 26, inputs=(b,), outputs=(a,)),
    ]
    assert ancestors(a, cyclic) == frozenset({a, b})


def test_producers_indexes_outputs_to_records():
    a, b = digest_bytes(b"a"), digest_bytes(b"b")
    record = ProvenanceRecord(run_id="R" * 26, inputs=(a,), outputs=(b,))
    assert producers([record]) == {b: record}


def test_would_create_cycle_detects_direct_overlap():
    d = digest_bytes(b"d")
    assert would_create_cycle([d], [d], [])


def test_would_create_cycle_is_false_for_a_fresh_derivation():
    assert not would_create_cycle([digest_bytes(b"in")], [digest_bytes(b"out")], [])


# ── End-to-end: the chain an auditor walks ──────────────────────────────────────

def test_a_published_value_traces_to_its_source(store):
    """VVMP §7 in miniature: raw source -> derived -> published, walked upstream."""
    acquire = begin_run("ingest", "acquire")
    raw = store.put_bytes(b"raw archive bytes")
    canonical = digest_bytes(b"canonical table")
    store.record(acquire, [raw.digest], [canonical])
    acquire.end(RunStatus.OK)

    derive = begin_run("evidence", "derive")
    store.put_bytes(b"canonical table")
    published = digest_bytes(b"published figure")
    store.record(derive, [canonical], [published])
    derive.end(RunStatus.OK)

    assert store.ancestors(published) == frozenset({canonical, raw.digest})

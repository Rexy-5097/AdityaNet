"""Manifest validity — the unit test §15 row 14 names.

`| 14 | 14 | E4 | 250 | M | 11 | manifest validity | — | — |`

The Tier 2 manifest is what git carries in place of the bytes (ADR-0023, E6 §19), so almost
everything this schema does is a refusal: refusing to record a Tier 0 archive as deposited,
refusing to mark referenced bytes prunable, refusing a path that leaves the repository. A
refusal nobody has watched happen is a comment, so every conditional below is exercised from
both sides — the permitted shape and the shape it exists to forbid.

SCOPE. This file tests the schema and nothing else. Issue #14 delivers the contract; it
delivers no producer, no parser, no registry and no ingest logic. `registry/*/*.json`
instances belong to E6/#21, E7/#23, E8/#25 and #26, E9/#27; `contexts/curation/manifest`
belongs to E6/#20; the retention gate belongs to E6/#22.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
REGISTRY_DIR = REPO_ROOT / "registry"

DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64
WHEN = "2026-07-30T12:00:00Z"

#: The seven registry namespaces, which the `kind` enum must match exactly. Read from the
#: schema and from disk rather than restated, so a namespace added in one place and not the
#: other is a failure rather than a silent divergence.
NAMESPACE_DIRECTORIES = {
    "datasets": "dataset",
    "labels": "label",
    "methods": "method",
    "protocols": "protocol",
    "environments": "environment",
    "evaluations": "evaluation",
    "supersessions": "supersession",
}


def registry() -> Registry:
    built = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        if path.name.startswith("._"):
            continue
        built = Resource.from_contents(json.loads(path.read_text())) @ built
    return built


def validator() -> Draft202012Validator:
    schema = json.loads((CONTRACTS / "manifest.schema.json").read_text())
    return Draft202012Validator(schema, registry=registry())


def schema() -> dict:
    return json.loads((CONTRACTS / "manifest.schema.json").read_text())


def tier1(**overrides) -> dict:
    doc = {
        "kind": "dataset",
        "digest": DIGEST,
        "tier": 1,
        "recorded_at": WHEN,
        "retention": {"class": "permanent"},
        "deposition": {
            "provider": "Zenodo",
            "url": "https://zenodo.org/records/1",
            "doi": "10.5281/zenodo.1",
        },
    }
    doc.update(overrides)
    return doc


def tier0(**overrides) -> dict:
    doc = {
        "kind": "dataset",
        "digest": DIGEST,
        "tier": 0,
        "recorded_at": WHEN,
        "retention": {"class": "permanent"},
        "retrieval": {
            "provider": "ISSDC PRADAN",
            "locator": "aditya-l1/solexs/2024-03-01",
            "requires_credentials": True,
        },
    }
    doc.update(overrides)
    return doc


def tier2(**overrides) -> dict:
    doc = {
        "kind": "evaluation",
        "digest": DIGEST,
        "tier": 2,
        "recorded_at": WHEN,
        "retention": {"class": "prunable", "prune_after": WHEN},
        "path": "registry/evaluations/aaaaaaaa.json",
    }
    doc.update(overrides)
    return doc


def assert_valid(doc: dict) -> None:
    errors = sorted(validator().iter_errors(doc), key=str)
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


def assert_invalid(doc: dict) -> None:
    assert list(validator().iter_errors(doc)), f"schema accepted what it must refuse: {doc}"


# ═══════════════════════════════════════════ identity and conventions


def test_the_manifest_contract_exists_and_is_a_valid_schema():
    Draft202012Validator.check_schema(schema())


def test_the_id_follows_the_urn_convention():
    """`contracts/_common.md`: a URN, not an https:// URL — no endpoint is served."""
    assert schema()["$id"] == "urn:adityanet:contract:manifest:1"
    assert schema()["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_the_manifest_is_closed():
    """Closed by default. An unrecognised field is how two parties disagree while conforming."""
    assert schema()["additionalProperties"] is False
    assert_invalid(tier1(unexpected="x"))


@pytest.mark.parametrize("nested", ["retention", "retrieval", "deposition"])
def test_every_nested_object_is_closed_too(nested):
    """A closed top level with an open sub-object is closed in name only."""
    assert schema()["properties"][nested]["additionalProperties"] is False


def test_the_digest_definition_is_reused_not_restated():
    """One definition of a content address, so the constraint cannot drift (ADR-0005)."""
    assert schema()["properties"]["digest"]["$ref"].endswith("#/$defs/digest")
    assert schema()["properties"]["recorded_at"]["$ref"].endswith("#/$defs/timestamp")


# ═══════════════════════════════════════════ the required core


def test_a_wellformed_manifest_of_each_tier_validates():
    for doc in (tier0(), tier1(), tier2()):
        assert_valid(doc)


@pytest.mark.parametrize("field", ["kind", "digest", "tier", "recorded_at", "retention"])
def test_each_required_field_is_enforced(field):
    """Dropped individually, so the requirement is proved rather than assumed."""
    doc = tier1()
    del doc[field]
    assert_invalid(doc)


@pytest.mark.parametrize("bad", ["A" * 64, "a" * 63, "", "not-a-digest", None, 1])
def test_the_digest_must_be_a_sha256(bad):
    assert_invalid(tier1(digest=bad))


@pytest.mark.parametrize("bad", ["2026-07-30", "", "30/07/2026", None])
def test_recorded_at_must_be_a_real_timestamp(bad):
    assert_invalid(tier1(recorded_at=bad))


def test_recorded_at_is_a_fact_not_an_identifier():
    """ADR-0005 forbids timestamp identifiers for immutables.

    Two manifests recorded at the same instant with different digests are two different
    objects, and the schema must not treat the instant as distinguishing.
    """
    assert_valid(tier1(digest=DIGEST, recorded_at=WHEN))
    assert_valid(tier1(digest=OTHER_DIGEST, recorded_at=WHEN))


# ═══════════════════════════════════════════ kind matches the registry on disk


def test_kind_covers_exactly_the_seven_registry_namespaces():
    """The schema and the directory tree must not drift apart.

    A manifest whose `kind` has no directory has nowhere to be filed; a directory whose kind
    the schema rejects can never receive one. Either way an entry is silently lost.
    """
    on_disk = {
        d.name for d in REGISTRY_DIR.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_"))
    }
    assert on_disk == set(NAMESPACE_DIRECTORIES), (
        f"registry/ holds {sorted(on_disk)}, the test maps {sorted(NAMESPACE_DIRECTORIES)}"
    )
    assert set(schema()["properties"]["kind"]["enum"]) == set(NAMESPACE_DIRECTORIES.values())


@pytest.mark.parametrize("kind", sorted(NAMESPACE_DIRECTORIES.values()))
def test_every_namespace_is_an_acceptable_kind(kind):
    assert_valid(tier1(kind=kind))


@pytest.mark.parametrize("bad", ["datasets", "Dataset", "observation", "", None])
def test_an_unknown_kind_is_refused(bad):
    """Including the plural directory name — a near miss that would file entries nowhere."""
    assert_invalid(tier1(kind=bad))


# ═══════════════════════════════════════════ ADR-0023 — the three tiers


@pytest.mark.parametrize("bad", [3, -1, "1", None, True])
def test_the_tier_must_be_one_of_the_three_adr_0023_defines(bad):
    assert_invalid(tier1(tier=bad))


def test_a_tier_written_as_a_float_is_the_same_tier():
    """`1.0` is accepted, and that is correct rather than a hole.

    JSON Schema compares `enum` members by *value*, and JSON has one number type: `1.0` and
    `1` are the same number, not two spellings of it. A schema cannot distinguish them, so
    the alternative to accepting `1.0` is not rejecting it — it is pretending to reject it.
    Recorded here because the first version of this test asserted the opposite and was wrong.
    """
    assert_valid(tier1(tier=1.0))
    assert_invalid(tier1(tier=1.5))


def test_tier_0_requires_a_retrieval_descriptor():
    """ADR-0023: "Digest plus retrieval descriptor only". Any stage must be able to
    re-acquire from it, so a Tier 0 manifest without one identifies bytes nobody can get."""
    doc = tier0()
    del doc["retrieval"]
    assert_invalid(doc)


def test_tier_0_cannot_carry_a_deposition():
    """THE REDISTRIBUTION REFUSAL.

    ADR-0023 and STD-23: Tier 0 bytes are never redistributed, and E6 §11(iii) states it as an
    invariant. Making `deposition` structurally impossible on a Tier 0 entry is stronger than
    a rule someone must remember — a manifest that would republish another organisation's raw
    archive cannot be written at all.
    """
    assert_invalid(tier0(deposition={
        "provider": "Zenodo", "url": "https://zenodo.org/records/9", "doi": None,
    }))


def test_tier_0_cannot_carry_an_in_git_path():
    """The other way of redistributing: committing the bytes instead of depositing them."""
    assert_invalid(tier0(path="raw-data/solexs/frame.fits"))


def test_tier_1_requires_a_deposition():
    doc = tier1()
    del doc["deposition"]
    assert_invalid(doc)


def test_tier_1_carries_neither_a_retrieval_descriptor_nor_a_path():
    """A deposited release lives at its deposition; the other two forms are for other tiers."""
    assert_invalid(tier1(retrieval={"provider": "ISSDC", "locator": "x"}))
    assert_invalid(tier1(path="registry/datasets/a.json"))


def test_tier_2_requires_a_path_and_nothing_else():
    doc = tier2()
    del doc["path"]
    assert_invalid(doc)
    assert_invalid(tier2(deposition={
        "provider": "Zenodo", "url": "https://zenodo.org/records/9", "doi": None,
    }))


# ═══════════════════════════════════════════ deposition


def test_the_doi_is_required_as_a_field_and_nullable_in_value():
    """ADR-0023's fallback degrades citability, and the degradation is published, not hidden.

    Required-and-nullable rather than optional: omitting the field would make "no DOI" and
    "nobody recorded whether there is a DOI" the same document. The same reasoning as
    `ingest_time` (ADR-0022) applied to citability.
    """
    assert_valid(tier1(deposition={
        "provider": "GitHub release",
        "url": "https://github.com/Rexy-5097/AdityaNet/releases/tag/v1",
        "doi": None,
    }))
    doc = tier1()
    del doc["deposition"]["doi"]
    assert_invalid(doc)


@pytest.mark.parametrize(
    "bad_doi", ["", "zenodo.1", "10.x/abc", "doi:10.5281/zenodo.1", "10.5281/", 1]
)
def test_a_malformed_doi_is_refused(bad_doi):
    assert_invalid(tier1(deposition={
        "provider": "Zenodo", "url": "https://zenodo.org/records/1", "doi": bad_doi,
    }))


@pytest.mark.parametrize(
    "bad_url",
    ["http://zenodo.org/records/1", "ftp://x/y", "zenodo.org/records/1", "", "//zenodo.org"],
)
def test_a_deposition_url_must_be_https(bad_url):
    """A plaintext locator for an artifact whose purpose is verifiable integrity undermines
    the claim in transit."""
    assert_invalid(tier1(deposition={
        "provider": "Zenodo", "url": bad_url, "doi": None,
    }))


@pytest.mark.parametrize("field", ["provider", "url", "doi"])
def test_every_deposition_field_is_required(field):
    doc = tier1()
    del doc["deposition"][field]
    assert_invalid(doc)


# ═══════════════════════════════════════════ retrieval (Tier 0)


@pytest.mark.parametrize("field", ["provider", "locator"])
def test_a_retrieval_descriptor_must_name_provider_and_locator(field):
    doc = tier0()
    del doc["retrieval"][field]
    assert_invalid(doc)


def test_a_retrieval_descriptor_may_record_that_credentials_are_needed():
    """Recorded because a reader who cannot obtain one needs to know before trying.

    The credentials themselves never appear — STD-19 confines them to Ingest — and the schema
    is closed, so there is no field through which one could.
    """
    assert_valid(tier0())
    assert_valid(tier0(retrieval={"provider": "ISSDC", "locator": "x"}))
    assert "additionalProperties" in schema()["properties"]["retrieval"]
    assert schema()["properties"]["retrieval"]["additionalProperties"] is False


def test_the_retrieval_descriptor_has_no_field_for_a_secret():
    """A closed object with no credential-shaped field is how STD-19 is kept structural."""
    fields = set(schema()["properties"]["retrieval"]["properties"])
    assert fields == {"provider", "locator", "requires_credentials"}
    for forbidden in ("token", "password", "cookie", "session", "api_key", "secret"):
        assert forbidden not in fields


# ═══════════════════════════════════════════ STD-24 — retention


@pytest.mark.parametrize("bad", ["forever", "PERMANENT", "", None])
def test_the_retention_class_is_a_closed_vocabulary(bad):
    assert_invalid(tier1(retention={"class": bad}))


def test_retention_is_required_and_must_declare_a_class():
    assert_invalid(tier1(retention={}))


def test_a_permanent_entry_has_no_prune_instant():
    """A permanent artifact has no instant after which it may be pruned.

    Permitting both would let a manifest state a contradiction that a retention run would
    then have to arbitrate — and it would arbitrate it the same way every time, silently.
    """
    assert_invalid(tier2(retention={"class": "permanent", "prune_after": WHEN},
                         path="registry/evaluations/a.json"))
    assert_valid(tier2(retention={"class": "permanent"}, path="registry/evaluations/a.json"))


def test_a_prunable_entry_must_say_when():
    """STD-24 gives 90 days; a prunable entry that names no instant is unprunable in practice
    and permanent in effect, without saying so."""
    assert_invalid(tier2(retention={"class": "prunable"}))


def test_a_referenced_artifact_cannot_be_marked_prunable():
    """E6 §11(iv): an artifact referenced by an Evidence Binding is NEVER pruned.

    This is the one combination that would let a published claim lose the bytes underneath it,
    so the contract makes it unrepresentable rather than merely discouraged.
    """
    assert_invalid(tier2(retention={
        "class": "prunable", "prune_after": WHEN, "referenced_by": ["tss-headline"],
    }))
    assert_valid(tier2(retention={
        "class": "permanent", "referenced_by": ["tss-headline"],
    }, path="registry/evaluations/a.json"))


def test_referenced_by_entries_are_unique_and_non_empty():
    assert_invalid(tier2(retention={
        "class": "permanent", "referenced_by": ["a", "a"],
    }, path="x.json"))
    assert_invalid(tier2(retention={
        "class": "permanent", "referenced_by": [""],
    }, path="x.json"))


def test_a_tier_1_release_cannot_be_prunable():
    """ADR-0023 lifecycle: Tier 1 is permanent. A prunable one would make a DOI resolve to
    nothing, which is worse than never having minted it."""
    assert_invalid(tier1(retention={"class": "prunable", "prune_after": WHEN}))


# ═══════════════════════════════════════════ path containment (Tier 2)


@pytest.mark.parametrize(
    "escape",
    ["/etc/passwd", "../secrets.json", "registry/../../etc/passwd", "..", "../", "a/../../b"],
)
def test_a_tier_2_path_may_not_escape_the_repository(escape):
    """A manifest is read by tooling that will open what it names.

    `registry/../../etc/passwd` carries no leading `..` and escapes all the same, which is
    why the pattern rejects a `..` segment anywhere rather than only at the start.
    """
    assert_invalid(tier2(path=escape))


@pytest.mark.parametrize(
    "good",
    ["registry/evaluations/a.json", "artifacts/v2/x.json", "a.json", "a/b/c/d.json"],
)
def test_a_contained_tier_2_path_is_accepted(good):
    assert_valid(tier2(path=good))


def test_a_path_containing_two_dots_inside_a_name_is_not_an_escape():
    """`..` as a path segment is traversal; `..` inside a filename is not.

    Recorded because an over-broad pattern that rejected `v1..2.json` would push authors to
    rename real artifacts to satisfy a check that had misread them.
    """
    assert_valid(tier2(path="registry/evaluations/v1..2.json"))


# ═══════════════════════════════════════════ the optional name is never an identity


def test_the_name_is_optional_and_never_the_identity():
    """ADR-0005: mutable names are permitted precisely because nothing pins them.

    A manifest is valid without one — the digest is the identity — and two manifests sharing
    a name but not a digest are two different objects.
    """
    assert_valid(tier1())
    assert "name" not in schema()["required"]
    assert_valid(tier1(name="adityanet-v2", version="r1"))
    assert_valid(tier1(name="adityanet-v2", digest=OTHER_DIGEST))


@pytest.mark.parametrize("bad", ["Upper", "-leading", "has space", "a" * 65, ""])
def test_a_malformed_name_is_refused(bad):
    """Matches the identifier shape used across the contract set."""
    assert_invalid(tier1(name=bad))

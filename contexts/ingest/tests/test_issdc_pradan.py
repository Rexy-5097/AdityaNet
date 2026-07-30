"""The ISSDC-PRADAN adapter — the `descriptor` unit test §15 row 16 names.

`| 16 | 16 | E5 | 700 | L | 15 | descriptor | — | fixture acquire |`

Most of this file runs against a **fixture archive** built from bytes the test writes: an
archive with the layout `SPEC-parsers@r6` §1.1 records, so the adapter's behaviour is checked
without the 3.5 GB corpus. Tests that genuinely need the real archive are marked and skip when
it is absent, never fail (STD-12, E5 §17).

THE SKIP GUARD TESTS FOR PRODUCTS, NOT FOR A DIRECTORY
-------------------------------------------------------
E5 §16 is explicit, and names the reason: *"the legacy `isdir` guard silently disabled 188
tests."* The same trap exists in this archive for a different reason — the five v1.1 archives
carry a tracked quicklook PNG, so `AL1_SLX_L1_20241001_v1.1/` **exists in a clean checkout**
while its `.gz` products do not. A directory check would pass where the data does not exist.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from contexts.ingest import UnavailableResource, verify_conformance, verify_descriptor
from contexts.ingest.adapters.issdc_pradan import (
    ARCHIVE_STEM,
    GRANULARITY,
    LATENCY,
    PORTAL,
    SOURCE_ID,
    IssdcPradanAdapter,
)
from contexts.ingest.credentials import SECRET_FIELD_NAMES
from domain.errors import ContractViolation
from kernel.provenance import ProvenanceStore

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_ARCHIVE = REPO_ROOT / "research" / "data" / "aditya_l1" / "real_l1_v1" / "solexs"

#: The X8.7 flare of 2024-05-14, the day SALVAGE-001 records v1 reproducing to the minute.
FLARE_DAY = "2024-05-14"


def real_products_present() -> bool:
    """True only when SoLEXS `.gz` products are actually on disk.

    NOT `REAL_ARCHIVE.is_dir()`, and not a check for the archive directories either: five of
    them are present in every clean checkout because their quicklook PNGs are tracked while
    the 3.5 GB of products are not.
    """
    if not REAL_ARCHIVE.is_dir():
        return False
    return any(
        path for path in REAL_ARCHIVE.rglob("*.gz") if not path.name.startswith("._")
    )


real_only = pytest.mark.skipif(
    not real_products_present(), reason="real SoLEXS archive not extracted"
)


def build_archive(root: Path, date: str = "20240514", version: str = "1.0",
                  *, products: dict[str, bytes] | None = None) -> Path:
    """A fixture archive with the layout SPEC-parsers r6 §1.1 records.

    The stem repeats inside, SDD1 carries GTI only, SDD2 carries all science. Real gzip bytes
    so the digests the kernel mints are digests of real files.
    """
    stem = f"AL1_SLX_L1_{date}_v{version}"
    inner = root / stem / stem
    if products is None:
        products = {
            f"SDD1/AL1_SOLEXS_{date}_SDD1_L1.gti.gz": b"gti-sdd1",
            f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.gti.gz": b"gti-sdd2",
            f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.lc.gz": b"lightcurve",
            f"SDD2/AL1_SOLEXS_{date}_SDD2_L1.pi.gz": b"pulse-height",
        }
    for relative, payload in products.items():
        target = inner / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(payload))
    return root / stem


def adapter_over(root: Path, tmp_path: Path) -> IssdcPradanAdapter:
    return IssdcPradanAdapter(root, ProvenanceStore(tmp_path / "store"))


# ═══════════════════════════════════════════ the descriptor — row 16's Unit column


def test_the_channel_is_registered_with_the_declared_latency_and_granularity(tmp_path):
    """E5 §18's acceptance criterion, verbatim: latency class `~33d`, granularity
    `daily-archive`."""
    described = adapter_over(tmp_path / "archive", tmp_path).descriptor()
    assert str(described.source_id) == SOURCE_ID == "issdc-pradan"
    assert str(described.latency_class) == LATENCY == "~33d"
    assert str(described.granularity) == GRANULARITY == "daily-archive"


def test_the_descriptor_passes_the_ingest_contract_check(tmp_path):
    """#15's `verify_descriptor` is what any channel must satisfy; this one does."""
    described = verify_descriptor(adapter_over(tmp_path / "archive", tmp_path))
    assert described.authority.startswith("ISSDC")


def test_the_descriptor_needs_no_archive_to_answer(tmp_path):
    """A channel can say what it is without being asked to fetch.

    Asserted because it is what lets E5 §18's criterion be checked in a clean export, where
    the corpus is absent.
    """
    described = adapter_over(tmp_path / "does-not-exist", tmp_path).descriptor()
    assert str(described.latency_class) == "~33d"


def test_the_declared_latency_is_a_quantity_not_a_phrase(tmp_path):
    """ADR-0001's non-goal on real-time Aditya-L1 services is stated in terms of this value.

    33 days in seconds, so the non-goal is a comparison a gate could make rather than a
    sentence someone reads.
    """
    latency = adapter_over(tmp_path / "archive", tmp_path).descriptor().latency_class
    assert latency.seconds == 33 * 86_400 == 2_851_200
    assert latency.is_approximate, "~33d characterises a manual process; it is not measured"


def test_the_descriptor_is_constant_between_calls(tmp_path):
    """A channel whose declared latency varies has declared none (#15's conformance rule)."""
    adapter = adapter_over(tmp_path / "archive", tmp_path)
    assert adapter.descriptor() == adapter.descriptor()


def test_the_retrieval_descriptor_records_how_to_re_acquire_and_nothing_more(tmp_path):
    """ADR-0023: the descriptor is what lets a future reader get these bytes again."""
    retrieval = adapter_over(tmp_path / "archive", tmp_path).descriptor().retrieval
    assert retrieval.provider == "ISSDC PRADAN"
    assert PORTAL in retrieval.locator
    assert "AL1_SLX_L1" in retrieval.locator
    assert retrieval.requires_credentials is True
    assert set(retrieval.to_dict()) == {"provider", "locator", "requires_credentials"}


def test_the_locator_carries_no_session_state(tmp_path):
    """E5 §14 forbids recording URLs containing tokens.

    PRADAN's cookies are per-session and per-person; one would violate STD-19 and be useless
    within the hour besides.
    """
    locator = adapter_over(tmp_path / "archive", tmp_path).descriptor().retrieval.locator
    lowered = locator.lower()
    for marker in ("jsessionid", "fgtserver", "oauth", "cookie", "token", "="):
        assert marker not in lowered, f"the locator contains {marker!r}"


# ═══════════════════════════════════════════ STD-19 — the adapter holds no secret


def test_the_adapter_holds_no_credential(tmp_path):
    """The strongest form of STD-19 available to this channel: there is nothing to confine.

    PRADAN authentication is an interactive browser login that happens before and outside
    this code, so the adapter never possesses a secret. It cannot leak what it does not hold.
    """
    adapter = adapter_over(tmp_path / "archive", tmp_path)
    attributes = {name.strip("_").lower() for name in vars(adapter)}
    assert not (attributes & SECRET_FIELD_NAMES), f"the adapter holds {attributes}"
    assert set(vars(adapter)) == {"archive_root", "_store"}


def test_the_adapter_module_contains_no_secret_literal():
    """STD-19: no secret is committed. Checked on this module's own source."""
    import contexts.ingest.adapters.issdc_pradan.adapter as module

    source = Path(module.__file__).read_text().lower()
    for marker in ("jsessionid", "fgtserver", "oauth_token_request_state", "set-cookie"):
        assert marker not in source, f"the adapter source contains {marker!r}"


def test_the_adapter_performs_no_http(tmp_path):
    """No transport is implemented, and none is simulated.

    PRADAN requires an interactive login and warns that scripted access risks blocking, so a
    fetch here would mean inventing a transport this channel does not have — and inventing
    responses to go with it. The module imports nothing that could make a request.
    """
    import contexts.ingest.adapters.issdc_pradan.adapter as module

    source = Path(module.__file__).read_text()
    for forbidden in ("import requests", "import urllib", "import http",
                      "urlopen", "httpx", "socket"):
        assert forbidden not in source, f"the adapter reaches the network via {forbidden!r}"


# ═══════════════════════════════════════════ locating a day


def test_a_malformed_selector_is_a_contract_violation_not_an_outage(tmp_path):
    """Conflating the two would send someone looking for a network problem they do not have."""
    adapter = adapter_over(tmp_path / "archive", tmp_path)
    for bad in ("20240514", "2024-5-14", "May 14 2024", "", None, "2024-05-14T00:00:00Z"):
        with pytest.raises(ContractViolation) as caught:
            adapter.archive_for(bad)
        assert caught.value.pointer == "/selector"


def test_a_missing_archive_root_is_reported_as_unavailable(tmp_path):
    """The true statement: the data has not been retrieved. Nothing here can fetch it."""
    adapter = adapter_over(tmp_path / "never-downloaded", tmp_path)
    with pytest.raises(UnavailableResource) as caught:
        adapter.archive_for(FLARE_DAY)
    assert "manual browser session" in str(caught.value)


def test_a_day_that_was_never_retrieved_is_reported_as_unavailable(tmp_path):
    root = tmp_path / "archive"
    build_archive(root, date="20240514")
    adapter = adapter_over(root, tmp_path)
    with pytest.raises(UnavailableResource) as caught:
        adapter.archive_for("2024-05-15")
    assert "2024-05-15" in str(caught.value)


def test_a_directory_with_no_products_is_unavailable_not_empty(tmp_path):
    """THE STD-12 TRAP, reproduced exactly.

    Five v1.1 archives carry a tracked quicklook PNG, so the directory exists in a clean
    checkout while the science products do not. An `isdir` check passes here and the caller
    receives an archive with nothing in it.
    """
    root = tmp_path / "archive"
    stem = "AL1_SLX_L1_20241001_v1.1"
    png = root / stem / stem / "SDD2" / "AL1_SOLEXS_20241001_SDD2_L1_lightcurve.png"
    png.parent.mkdir(parents=True)
    png.write_bytes(b"\x89PNG\r\n\x1a\n")

    adapter = adapter_over(root, tmp_path)
    assert adapter.archive_for("2024-10-01").is_dir(), "the directory does exist"
    with pytest.raises(UnavailableResource) as caught:
        adapter.products("2024-10-01")
    assert "STD-12" in str(caught.value)


def test_both_version_variants_are_recognised(tmp_path):
    """SPEC-parsers r6: 431 archives at v1.0 and 5 at v1.1, no date carrying both."""
    root = tmp_path / "archive"
    build_archive(root, date="20240514", version="1.0")
    build_archive(root, date="20241001", version="1.1")
    adapter = adapter_over(root, tmp_path)
    assert adapter.version_of(adapter.archive_for("2024-05-14")) == "1.0"
    assert adapter.version_of(adapter.archive_for("2024-10-01")) == "1.1"


def test_two_versions_of_one_day_are_refused_rather_than_guessed(tmp_path):
    """SPEC-parsers r6 records no such date. If one appears, which is authoritative is a
    question, and picking one silently would answer it wrongly and invisibly."""
    root = tmp_path / "archive"
    build_archive(root, date="20240514", version="1.0")
    build_archive(root, date="20240514", version="1.1")
    with pytest.raises(ContractViolation) as caught:
        adapter_over(root, tmp_path).archive_for(FLARE_DAY)
    assert "authoritative" in caught.value.message


@pytest.mark.parametrize(
    "name", ["AL1_SLX_L1_20240514_v1.0", "AL1_SLX_L1_20241001_v1.1"]
)
def test_the_archive_stem_pattern_matches_the_published_layout(name):
    assert ARCHIVE_STEM.match(name) is not None


@pytest.mark.parametrize(
    "name",
    ["AL1_SLX_L1_20240514", "AL1_SLX_L2_20240514_v1.0", "HLS_20251208_000008_43178sec_lev1_V111"],
)
def test_the_archive_stem_pattern_rejects_anything_else(name):
    assert ARCHIVE_STEM.match(name) is None


# ═══════════════════════════════════════════ products and the archive identity


def test_products_are_returned_in_a_deterministic_order(tmp_path):
    """The archive digest is computed over this sequence, so filesystem ordering must not
    reach it — two machines would otherwise produce two identities for the same bytes."""
    root = tmp_path / "archive"
    build_archive(root)
    adapter = adapter_over(root, tmp_path)
    paths = [product.relative_path for product in adapter.products(FLARE_DAY)]
    assert paths == sorted(paths)
    assert len(paths) == 4


def test_appledouble_sidecars_are_excluded(tmp_path):
    """`._` files are created by macOS on non-native filesystems and are not part of what
    ISSDC published. Including them would make the digest depend on which computer looked."""
    root = tmp_path / "archive"
    archive = build_archive(root)
    inner = archive / archive.name / "SDD2"
    (inner / "._AL1_SOLEXS_20240514_SDD2_L1.lc.gz").write_bytes(b"resource fork")

    adapter = adapter_over(root, tmp_path)
    products = adapter.products(FLARE_DAY)
    assert len(products) == 4
    assert not any(p.relative_path.split("/")[-1].startswith("._") for p in products)


def test_the_quicklook_png_is_not_a_product(tmp_path):
    """A rendering of the data is not the data. Including it would make the archive identity
    depend on whether a preview image happened to be generated."""
    root = tmp_path / "archive"
    archive = build_archive(root, date="20241001", version="1.1")
    (archive / archive.name / "SDD2" / "AL1_SOLEXS_20241001_SDD2_L1_lightcurve.png").write_bytes(
        b"\x89PNG"
    )
    products = adapter_over(root, tmp_path).products("2024-10-01")
    assert all(p.relative_path.endswith(".gz") for p in products)


def test_the_archive_identity_changes_when_any_product_changes(tmp_path):
    """A rollup rather than one opaque digest: a changed byte anywhere is detected AND stays
    locatable to the product that changed (the ADR-0006 property, applied to an archive)."""
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    build_archive(root_a)
    build_archive(root_b, products={
        "SDD1/AL1_SOLEXS_20240514_SDD1_L1.gti.gz": b"gti-sdd1",
        "SDD2/AL1_SOLEXS_20240514_SDD2_L1.gti.gz": b"gti-sdd2",
        "SDD2/AL1_SOLEXS_20240514_SDD2_L1.lc.gz": b"lightcurve-CHANGED",
        "SDD2/AL1_SOLEXS_20240514_SDD2_L1.pi.gz": b"pulse-height",
    })
    first = adapter_over(root_a, tmp_path / "sa").acquire(FLARE_DAY)
    second = adapter_over(root_b, tmp_path / "sb").acquire(FLARE_DAY)
    assert first.artifact.digest != second.artifact.digest

    changed = {
        p.relative_path
        for p in adapter_over(root_a, tmp_path / "sa2").products(FLARE_DAY)
    } ^ {
        p.relative_path
        for p in adapter_over(root_b, tmp_path / "sb2").products(FLARE_DAY)
    }
    assert not changed, "the paths are identical; only one product's bytes differ"


def test_the_same_archive_yields_the_same_identity_twice(tmp_path):
    """Determinism: nothing in the identity depends on the clock, the store, or the run.

    The two acquisitions carry different run ids and different ingest times — they are
    different acquisitions of the same bytes — and the same digest. That separation is what
    makes a release citable: re-acquiring tomorrow does not produce a new identity.
    """
    root = tmp_path / "archive"
    build_archive(root)
    first = adapter_over(root, tmp_path / "s1").acquire(FLARE_DAY)
    second = adapter_over(root, tmp_path / "s2").acquire(FLARE_DAY)

    assert first.artifact.digest == second.artifact.digest
    assert first.provenance.run_id != second.provenance.run_id


def test_the_manifest_listing_is_stable_and_readable(tmp_path):
    root = tmp_path / "archive"
    build_archive(root)
    adapter = adapter_over(root, tmp_path)
    listing = adapter.manifest_bytes(adapter.products(FLARE_DAY)).decode()
    lines = listing.strip().split("\n")
    assert len(lines) == 4
    for line in lines:
        digest, size, path = line.split(" ", 2)
        assert len(digest) == 64
        assert size.isdigit()
        assert path.endswith(".gz")


# ═══════════════════════════════════════════ acquisition conforms to #15


def test_the_adapter_satisfies_the_ingest_contract(tmp_path):
    """The whole point: #16 is checked by #15's rules rather than by its own."""
    root = tmp_path / "archive"
    build_archive(root)
    acquired = verify_conformance(adapter_over(root, tmp_path), selector=FLARE_DAY)
    assert acquired.artifact.digest == acquired.provenance.artifact_digest
    assert acquired.provenance.ingest_time is not None
    assert str(acquired.provenance.source_id) == SOURCE_ID


def test_the_acquisition_holds_no_bytes(tmp_path):
    """Tier 0 is referenced, never redistributed (ADR-0023, STD-23, E5 §11(iv), §12)."""
    root = tmp_path / "archive"
    build_archive(root)
    artifact = adapter_over(root, tmp_path).acquire(FLARE_DAY).artifact
    assert not hasattr(artifact, "bytes")
    assert artifact.retrieval.provider == "ISSDC PRADAN"
    assert artifact.cache_path is not None, "the local copy is recorded as a cache"


def test_the_recorded_size_is_the_sum_of_the_products(tmp_path):
    root = tmp_path / "archive"
    build_archive(root)
    adapter = adapter_over(root, tmp_path)
    acquired = adapter.acquire(FLARE_DAY)
    assert acquired.artifact.size_bytes == sum(
        p.size_bytes for p in adapter.products(FLARE_DAY)
    )


def test_the_product_bytes_are_not_registered_with_the_store(tmp_path):
    """Only the listing is registered. Registering the products would copy Tier 0 bytes into
    the store, which ADR-0023 forbids — the store is not where the archive lives."""
    root = tmp_path / "archive"
    build_archive(root)
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcPradanAdapter(root, store)
    acquired = adapter.acquire(FLARE_DAY)

    from kernel.provenance import Digest as KernelDigest

    assert store.has_artifact(KernelDigest(str(acquired.artifact.digest)))
    for product in adapter.products(FLARE_DAY):
        assert not store.has_artifact(KernelDigest(str(product.digest)))


# ═══════════════════════════════════════════ the real archive (skips when absent)


@real_only
def test_the_real_flare_day_archive_matches_the_published_layout():
    """SPEC-parsers r6 §1.1, against the corpus: SDD1 GTI only, SDD2 all science."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        adapter = IssdcPradanAdapter(REAL_ARCHIVE, ProvenanceStore(Path(tmp) / "store"))
        products = adapter.products(FLARE_DAY)

    names = [p.relative_path for p in products]
    assert any("SDD1" in n and n.endswith(".gti.gz") for n in names)
    assert not any("SDD1" in n and n.endswith((".lc.gz", ".pi.gz")) for n in names), (
        "SPEC-parsers r6: .lc and .pi exist for SDD2 only"
    )
    for suffix in (".gti.gz", ".lc.gz", ".pi.gz"):
        assert any("SDD2" in n and n.endswith(suffix) for n in names), f"SDD2 {suffix} missing"


@real_only
def test_the_real_corpus_has_the_archive_count_the_spec_records():
    """436 archives, 436 unique dates, 0 duplicates — SPEC-parsers r6 §1.1, re-measured."""
    stems = [
        path.name for path in REAL_ARCHIVE.iterdir()
        if path.is_dir() and ARCHIVE_STEM.match(path.name)
    ]
    dates = [ARCHIVE_STEM.match(s).group(1) for s in stems]
    assert len(stems) == 436, f"the spec records 436 archives; found {len(stems)}"
    assert len(set(dates)) == 436, "a date appears twice; SPEC-parsers r6 records none"

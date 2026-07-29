"""Digest — content addressing.

ADR-0005 makes identity a function of content. Every property below exists because its
negation would break that: a digest that varied with read size, with platform, or with
process would mean two references to identical bytes could disagree about whether they are
identical, and the whole provenance graph rests on them agreeing.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from kernel.provenance.digest import (
    CHUNK_BYTES,
    Digest,
    digest_bytes,
    digest_chunks,
    digest_file,
    digest_stream,
)

# NIST FIPS 180-4 published vectors. Pinning these means a change to the hash function or
# its invocation is caught here rather than by every downstream digest silently moving.
KNOWN_VECTORS = (
    (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    (
        b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
        "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
    ),
)


# ── Digest value object ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", KNOWN_VECTORS)
def test_known_vectors(data: bytes, expected: str):
    assert digest_bytes(data).hex == expected


def test_digest_is_frozen():
    digest = digest_bytes(b"x")
    with pytest.raises(AttributeError):
        digest.hex = "0" * 64  # type: ignore[misc]


def test_digest_is_hashable_and_usable_as_a_key():
    a, b = digest_bytes(b"a"), digest_bytes(b"b")
    assert {a: 1, b: 2}[a] == 1
    assert len({a, b, digest_bytes(b"a")}) == 2


def test_digest_orders_deterministically():
    """Sorting matters: a record's inputs serialise sorted, so its own identity would
    otherwise depend on the order a caller passed them."""
    digests = [digest_bytes(bytes([n])) for n in range(20)]
    assert sorted(digests) == sorted(digests, key=lambda d: d.hex)


def test_short_is_a_prefix_and_not_identity():
    digest = digest_bytes(b"abc")
    assert digest.short == digest.hex[:12]
    assert len(digest.short) == 12


def test_str_is_the_full_hex():
    """A digest interpolated into a message must not silently truncate."""
    digest = digest_bytes(b"abc")
    assert str(digest) == digest.hex


# ── Deliberate violations: malformed digests are rejected ───────────────────────

@pytest.mark.parametrize(
    "bad",
    [
        "",
        "abc",
        "0" * 63,
        "0" * 65,
        "A" * 64,          # upper case
        "g" * 64,          # not hex
        "0" * 63 + "!",
    ],
)
def test_malformed_digest_is_rejected(bad: str):
    with pytest.raises(ValueError):
        Digest(bad)


# ── Properties ──────────────────────────────────────────────────────────────────

def test_same_bytes_give_the_same_digest_across_many_inputs():
    rng = random.Random(20260730)
    for _ in range(200):
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 300)))
        assert digest_bytes(data) == digest_bytes(bytes(data))


def test_different_bytes_give_different_digests():
    rng = random.Random(11)
    seen: dict[str, bytes] = {}
    for _ in range(500):
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 64)))
        hexed = digest_bytes(data).hex
        assert seen.setdefault(hexed, data) == data


def test_digest_is_independent_of_chunk_boundaries():
    """The property that makes streaming safe. A digest varying with read size would make
    every file's identity depend on its reader."""
    rng = random.Random(7)
    data = bytes(rng.randrange(256) for _ in range(50_000))
    expected = digest_bytes(data)

    for size in (1, 7, 512, 4096, CHUNK_BYTES, len(data), len(data) * 2):
        chunks = [data[i : i + size] for i in range(0, len(data), size)] or [b""]
        assert digest_chunks(chunks) == expected


def test_empty_input_is_digestible_and_not_special_cased():
    assert digest_chunks([]) == digest_bytes(b"")
    assert digest_chunks([b"", b""]) == digest_bytes(b"")


def test_digest_matches_hashlib_directly():
    """Guards against this module accidentally salting, encoding or double-hashing."""
    rng = random.Random(3)
    data = bytes(rng.randrange(256) for _ in range(1000))
    assert digest_bytes(data).hex == hashlib.sha256(data).hexdigest()


# ── Streaming ───────────────────────────────────────────────────────────────────

def test_digest_stream_matches_digest_bytes(tmp_path):
    data = b"provenance" * 5000
    path = tmp_path / "blob.bin"
    path.write_bytes(data)
    with path.open("rb") as handle:
        assert digest_stream(handle) == digest_bytes(data)


def test_digest_file_matches_digest_bytes(tmp_path):
    data = b"\x00\xff" * 100_000
    path = tmp_path / "blob.bin"
    path.write_bytes(data)
    assert digest_file(path) == digest_bytes(data)


def test_digest_file_does_not_materialise_the_file(tmp_path, monkeypatch):
    """TIS E3 §12 forbids buffering a whole file — Tier 0 archives run to ~21 GB.

    Asserted structurally rather than by memory measurement: `read` is observed, and no
    single call may request more than one chunk.
    """
    data = b"z" * (CHUNK_BYTES * 4 + 13)
    path = tmp_path / "big.bin"
    path.write_bytes(data)

    requested: list[int | None] = []
    real_open = type(path).open

    class Watched:
        def __init__(self, handle):
            self._handle = handle

        def read(self, size=None):
            requested.append(size)
            return self._handle.read(size)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._handle.close()
            return False

    def fake_open(self, *args, **kwargs):
        return Watched(real_open(self, *args, **kwargs))

    monkeypatch.setattr(type(path), "open", fake_open)

    assert digest_file(path) == digest_bytes(data)
    assert requested, "digest_file did not read in chunks"
    assert all(size == CHUNK_BYTES for size in requested), (
        f"digest_file requested an unbounded read: {set(requested)}"
    )
    assert len(requested) >= 5, "file was not read incrementally"


def test_digest_file_on_empty_file(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    assert digest_file(path) == digest_bytes(b"")

"""The salvage corpus.

The Engineering Plan specifies no tests for M1/E2/#8. Two of its implementation rules are
nonetheless stated as absolutes — *every migrated document must state its provenance* and
*every migrated document must have a stable identifier* — and a rule with no gate is a
preference (STD-11). These tests are the gate for exactly those two rules, plus the third
that makes salvage safe: no obsolete implementation may be copied forward.

Salvage is a standing invitation to reintroduce something that was removed for a reason. The
last test is the one that matters: every document must say which parts are ideas and which
are artifacts fitted on data now known to be unusable.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SALVAGE = REPO_ROOT / "specs" / "salvage"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)
RECOVERY_TAG = "v1-surya-final"


def meta_of(path: Path) -> dict[str, str]:
    match = FRONT_MATTER.match(path.read_text())
    assert match is not None, f"{path.name}: missing front matter"
    return dict(KEY.findall(match.group(1)))


def salvage_paths() -> list[Path]:
    return sorted(p for p in SALVAGE.glob("SALVAGE-*.md") if not p.name.startswith("._"))


# ── The corpus exists and is enumerable ─────────────────────────────────────────

def test_the_salvage_corpus_is_not_empty():
    """A scan over an empty directory passes while checking nothing."""
    assert len(salvage_paths()) >= 3


def test_numbering_is_contiguous():
    numbers = sorted(int(p.stem.split("-")[1]) for p in salvage_paths())
    assert numbers == list(range(1, len(numbers) + 1))


# ── Rule: every migrated document must have a stable identifier ─────────────────

@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_has_a_stable_identifier(path: Path):
    meta = meta_of(path)
    assert meta["id"] == path.stem
    assert re.fullmatch(r"SALVAGE-\d{3}", meta["id"])


def test_identifiers_are_unique():
    ids = [meta_of(p)["id"] for p in salvage_paths()]
    assert len(set(ids)) == len(ids)


# ── Rule: every migrated document must state its provenance ─────────────────────

@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_declares_machine_readable_provenance(path: Path):
    meta = meta_of(path)
    assert meta.get("origin") == "salvaged"
    assert meta.get("source_tag") == RECOVERY_TAG
    assert meta.get("source_paths"), "no source path declared"


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_states_provenance_in_prose_with_a_retrieval_command(path: Path):
    """Front matter is for machines. A reader must also be told, in the document, where the
    implementation went and how to get it back."""
    text = path.read_text()
    assert f"git show {RECOVERY_TAG}:" in text, "no retrieval command in the prose"
    assert "Provenance" in text


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_declares_that_it_mandates_nothing(path: Path):
    """A salvage document is not a specification. Without saying so it will eventually be
    read as one, because it sits in specs/."""
    text = path.read_text()
    assert "mandates nothing" in text
    assert "adr/" in text, "does not point at where binding decisions live"


# ── Rule: preserve design knowledge, not implementation ─────────────────────────

@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_contains_no_copied_implementation(path: Path):
    """Deliberate violation guard for the rule 'never copy obsolete code into the new
    architecture'. Fenced blocks are permitted only for shell retrieval commands."""
    fences = re.findall(r"```(\w*)\n(.*?)```", path.read_text(), re.S)
    for language, body in fences:
        assert language in ("", "sh", "bash", "console"), (
            f"{path.stem}: fenced {language!r} block — salvage carries design knowledge, "
            f"not implementation"
        )
        for line in body.splitlines():
            # The provenance fences sit inside blockquotes, so lines carry a "> " prefix.
            # Stripping it here rather than un-quoting the documents keeps the provenance
            # note visually distinct from the body, which is why it is quoted at all.
            stripped = line.strip().lstrip("> ").strip()
            if not stripped:
                continue
            assert stripped.startswith(("git ", "#")), (
                f"{path.stem}: fenced block contains non-retrieval content: {stripped[:60]}"
            )


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_states_what_must_not_be_carried_forward(path: Path):
    """The section that makes salvage safe. Every document must name the parts that are
    artifacts of unusable data rather than transferable ideas."""
    assert "What must not be carried forward" in path.read_text()


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_contrasts_v1_against_the_frozen_architecture(path: Path):
    """Salvage that only praises the old design invites its restoration wholesale."""
    assert "frozen architecture does differently" in path.read_text()


# ── The index ───────────────────────────────────────────────────────────────────

def test_index_lists_every_salvage_document():
    index = (SALVAGE / "index.md").read_text()
    for path in salvage_paths():
        assert f"[{path.stem}]({path.name})" in index, f"index omits {path.stem}"


def test_index_states_that_salvage_is_not_specification():
    index = (SALVAGE / "index.md").read_text()
    assert "not specifications" in index

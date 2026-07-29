"""The limitation clause namespace.

ADR-0013 makes each clause individually citable so that exactly one copy of every caveat
exists. Two failure modes would defeat that, and neither is visible by reading:

  1. A clause silently paraphrased on migration, producing a second and softer copy.
  2. A clause cited by a decision but absent from the namespace.

The first is caught by comparing migrated bodies against the frozen source verbatim — a
migration is only trustworthy if it can be diffed against what it migrated. The second is
caught by resolving every citation in adr/ and standards/ against the namespace.

L-11 is exempt from the verbatim check because it has no artifact source: it is authored
from ADR-0022, which postdates the report the other clauses come from. The exemption is
declared in the file's own front matter (`origin: authored`) and asserted here, so it cannot
be claimed by a clause that ought to have been migrated.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUSES = REPO_ROOT / "specs" / "limitations"
FROZEN_SOURCE = REPO_ROOT / "artifacts/v2/ml/DATASET_LIMITATIONS_FOR_ML.md"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)

EXPECTED_IDS = tuple(f"L-{n:02d}" for n in range(1, 12))


def normalised(text: str) -> str:
    """Collapse whitespace before a substring check.

    A clause is prose wrapped at 88 columns, so a required phrase may straddle a line break.
    Asserting on the raw text would make these tests fail on re-wrapping rather than on
    content, which is a test that reports the wrong thing.
    """
    return " ".join(text.split())


def meta_of(path: Path) -> dict[str, str]:
    match = FRONT_MATTER.match(path.read_text())
    assert match is not None, f"{path.name}: missing front matter"
    return dict(KEY.findall(match.group(1)))


def body_of(path: Path) -> str:
    """Everything after the blockquote provenance note — the clause proper."""
    text = FRONT_MATTER.sub("", path.read_text())
    lines = [ln for ln in text.splitlines() if not ln.startswith((">", "# "))]
    return "\n".join(lines).strip()


def clause_paths() -> list[Path]:
    return sorted(p for p in CLAUSES.glob("L-*.md") if not p.name.startswith("._"))


# ── The namespace is complete and contiguous ────────────────────────────────────

def test_all_expected_clauses_exist():
    found = tuple(p.stem for p in clause_paths())
    assert found == EXPECTED_IDS, f"expected {EXPECTED_IDS}, found {found}"


def test_no_gaps_in_clause_numbering():
    """A gap means a clause was cited, reserved, then never written."""
    numbers = sorted(int(p.stem.split("-")[1]) for p in clause_paths())
    assert numbers == list(range(1, len(numbers) + 1))


@pytest.mark.parametrize("path", clause_paths(), ids=lambda p: p.stem)
def test_front_matter_id_matches_filename(path: Path):
    assert meta_of(path)["id"] == path.stem


@pytest.mark.parametrize("path", clause_paths(), ids=lambda p: p.stem)
def test_clause_has_a_body(path: Path):
    assert len(body_of(path)) > 200, f"{path.stem} is too short to be a clause"


# ── Migrated clauses are provably verbatim ──────────────────────────────────────

@pytest.mark.parametrize(
    "path",
    [p for p in clause_paths() if meta_of(p).get("origin", "migrated") == "migrated"],
    ids=lambda p: p.stem,
)
def test_migrated_clause_is_verbatim(path: Path):
    """Every paragraph of a migrated clause must appear in the frozen source unchanged.

    This is the test that makes ADR-0013's 'exactly one copy' claim checkable. A paraphrase,
    a dropped sentence, or a softened qualifier all fail here.
    """
    source = FROZEN_SOURCE.read_text()
    for paragraph in (p.strip() for p in body_of(path).split("\n\n")):
        if not paragraph:
            continue
        assert paragraph in source, (
            f"{path.stem}: paragraph not found verbatim in {FROZEN_SOURCE.name} — "
            f"the migration altered it.\n  {paragraph[:120]}..."
        )


def test_authored_clauses_declare_their_origin():
    """A clause with no artifact source must say so, and must cite the decision it derives
    from. Otherwise 'authored' becomes a way to exempt a clause from the verbatim check."""
    authored = [p for p in clause_paths() if meta_of(p).get("origin") == "authored"]
    assert authored, "no authored clause found; the exemption path is untested"
    for path in authored:
        meta = meta_of(path)
        assert meta["source"].startswith("adr/"), (
            f"{path.stem} is authored but does not cite a governing ADR as its source"
        )
        assert "Authored, not migrated" in path.read_text()


def test_no_clause_claims_authored_origin_while_matching_the_frozen_source():
    """The inverse guard: a clause present in the frozen report may not be marked authored
    to escape the verbatim check."""
    source = FROZEN_SOURCE.read_text()
    for path in clause_paths():
        if meta_of(path).get("origin") != "authored":
            continue
        title = meta_of(path)["title"]
        assert title not in source, (
            f"{path.stem} is marked authored but its title appears in the frozen source"
        )


# ── L-11 states what ADR-0022 requires it to state ──────────────────────────────

L11_REQUIRED = (
    ("nullability meaning", "predates bitemporal capture"),
    ("never fabricated", "never fabricated"),
    ("gate unenforceable", "unenforceable"),
    ("protocol exclusion", "requires_bitemporal"),
    ("evaluation records non-application", "leakage_gate_applied"),
)


@pytest.mark.parametrize("label,needle", L11_REQUIRED, ids=[x[0] for x in L11_REQUIRED])
def test_l11_states_the_adr_0022_consequence(label: str, needle: str):
    assert needle in normalised((CLAUSES / "L-11.md").read_text()), (
        f"L-11 does not state the {label} that ADR-0022 requires it to publish"
    )


def test_l11_offers_no_unmeasured_estimate():
    """ADR-0001 and STD-20 forbid publishing a figure nobody measured. The affected-row
    count is unknowable before bitemporal capture begins, so L-11 must decline to give one."""
    text = normalised((CLAUSES / "L-11.md").read_text())
    assert "not yet determined" in text
    assert "No estimate is offered" in text


# ── Every citation into the namespace resolves ──────────────────────────────────

def test_every_clause_cited_by_the_constitution_resolves():
    """The acceptance criterion for Issue #3, now satisfiable."""
    present = {p.stem for p in clause_paths()}
    cited: dict[str, list[str]] = {}
    for root in ("adr", "standards"):
        for path in (REPO_ROOT / root).rglob("*.md"):
            # AppleDouble sidecars are recreated by the OS on this volume and are not
            # UTF-8. The links gate already skips them; this scan must agree.
            if path.name.startswith("._"):
                continue
            for clause in re.findall(r"\bL-\d{2}\b", path.read_text()):
                cited.setdefault(clause, []).append(path.name)

    unresolved = {c: sorted(set(v)) for c, v in cited.items() if c not in present}
    assert not unresolved, f"clauses cited but absent: {unresolved}"


def test_index_lists_every_clause():
    index = (CLAUSES / "index.md").read_text()
    for path in clause_paths():
        assert f"[{path.stem}]({path.name})" in index, f"index omits {path.stem}"

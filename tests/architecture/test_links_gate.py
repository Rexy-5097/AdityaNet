"""Deliberate-violation tests for the constitution link gate.

ADR-0020 / STD-07: every gate must have a test proving it FAILS when it should. A gate
verified only by "it passed on the real corpus" is indistinguishable from a gate that
returns zero unconditionally — which is precisely the failure this project has already hit,
when a skip guard silently disabled 188 tests for four days.

Each test therefore constructs a corpus that violates exactly one invariant and asserts the
gate rejects it. The final test is the important one: it proves the DEFERRAL mechanism
cannot outlive the work that closes it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

GATE_PATH = Path(__file__).resolve().parents[2] / "tools" / "gates" / "links.py"


def load_gate(root: Path):
    """Load the gate module with its directory constants re-pointed at a fixture corpus.

    The gate resolves its roots at import time from its own location, so a fresh module
    object is loaded per test and its constants rebound. This keeps the gate free of a
    dependency-injection seam it does not otherwise need (ADR-0025: no paid abstraction for
    a hypothetical case).
    """
    spec = importlib.util.spec_from_file_location(f"links_gate_{root.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    module.ADR_DIR = root / "adr"
    module.STANDARDS_DIR = root / "standards"
    module.SPECS_DIR = root / "specs"
    module.NAMESPACE_ROOTS = {
        "ADR": module.ADR_DIR,
        "STD": module.STANDARDS_DIR,
        "L": module.SPECS_DIR / "limitations",
        "CONTRA": module.SPECS_DIR / "contradictions",
    }
    return module


def write_adr(root: Path, doc_id: str, *, body: str = "", status: str = "active",
              supersedes: str = "[]", superseded_by: str = "null",
              subdir: str = "adr") -> Path:
    directory = root / subdir
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{doc_id}.md"
    path.write_text(
        f"---\n"
        f"id: {doc_id}\n"
        f"title: Fixture {doc_id}\n"
        f"status: {status}\n"
        f"supersedes: {supersedes}\n"
        f"superseded_by: {superseded_by}\n"
        f"---\n\n"
        f"# {doc_id}\n\n{body}\n"
    )
    return path


# ── The gate accepts a well-formed corpus ───────────────────────────────────────

def test_accepts_wellformed_corpus(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="See ADR-0002.")
    write_adr(tmp_path, "ADR-0002")
    assert gate.main() == 0


def test_accepts_symmetric_supersession(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0021", supersedes="[ADR-0009]")
    write_adr(tmp_path, "ADR-0009", status="superseded", superseded_by="ADR-0021",
              subdir="adr/superseded")
    assert gate.main() == 0


# ── Deliberate violations: each must FAIL ───────────────────────────────────────

def test_rejects_duplicate_id(tmp_path: Path):
    """TIS E1 §11 invariant (i): exactly one file per citable ID."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001")
    write_adr(tmp_path, "ADR-0001", subdir="adr/superseded")
    assert gate.main() == 1


def test_rejects_dangling_citation_in_materialised_namespace(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="See ADR-0099, which does not exist.")
    assert gate.main() == 1


def test_rejects_asymmetric_supersession_missing_back_reference(tmp_path: Path):
    """ADR-0021 supersedes ADR-0009; if 0009 does not say so, a reader arriving from the
    other direction sees an active decision that is not active."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0021", supersedes="[ADR-0009]")
    write_adr(tmp_path, "ADR-0009", status="superseded", superseded_by="null",
              subdir="adr/superseded")
    assert gate.main() == 1


def test_rejects_asymmetric_supersession_missing_forward_reference(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0021", supersedes="[]")
    write_adr(tmp_path, "ADR-0009", status="superseded", superseded_by="ADR-0021",
              subdir="adr/superseded")
    assert gate.main() == 1


def test_rejects_superseded_status_without_target(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0009", status="superseded", superseded_by="null")
    assert gate.main() == 1


def test_rejects_missing_front_matter(tmp_path: Path):
    gate = load_gate(tmp_path)
    (tmp_path / "adr").mkdir(parents=True)
    (tmp_path / "adr" / "ADR-0001.md").write_text("# No front matter here\n")
    assert gate.main() == 1


def test_rejects_broken_relative_link(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="See [the other one](ADR-0404.md).")
    assert gate.main() == 1


# ── Fail-closed (ADR-0020) ──────────────────────────────────────────────────────

def test_fails_closed_when_corpus_root_absent(tmp_path: Path):
    """A missing constitution is a failure, not a vacuous pass."""
    gate = load_gate(tmp_path)
    assert gate.main() == 1


def test_fails_closed_when_corpus_empty(tmp_path: Path):
    """An empty corpus must not pass. Otherwise a gate that found nothing is
    indistinguishable from a gate that verified everything."""
    gate = load_gate(tmp_path)
    (tmp_path / "adr").mkdir(parents=True)
    assert gate.main() == 1


# ── The deferral mechanism cannot outlive the work that closes it ───────────────

def test_defers_citation_while_namespace_absent(tmp_path: Path):
    """ADR-0013 requires clauses to be cited rather than restated, so ADRs cite L-nn before
    the clause files are delivered. While specs/limitations/ does not exist, the citation is
    reported as deferred rather than failing."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="Constrained by L-03.")
    assert gate.main() == 0


def test_enforces_citation_once_namespace_materialises(tmp_path: Path):
    """The moment specs/limitations/ exists, an unresolved L-nn citation becomes a hard
    failure — with no change to the gate. This is what stops the deferral becoming a
    permanent suppression."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="Constrained by L-03.")
    (tmp_path / "specs" / "limitations").mkdir(parents=True)
    assert gate.main() == 1


def test_deferred_citation_resolves_when_clause_delivered(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001", body="Constrained by L-03.")
    write_adr(tmp_path, "L-03", subdir="specs/limitations")
    assert gate.main() == 0


# ── Navigational documents are ID-exempt, NOT check-exempt ──────────────────────
#
# Issue #2 requires a README in every directory, including adr/ and standards/. Those files
# carry no citable ID and no front matter. Lifting the ID requirement for them is correct;
# lifting the citation requirement would be weakening the gate to make a test pass, so these
# tests pin the distinction.

def test_navigational_document_needs_no_front_matter(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001")
    (tmp_path / "adr" / "README.md").write_text("# adr\n\nWhat may enter this directory.\n")
    (tmp_path / "adr" / "index.md").write_text("# Index\n\n- ADR-0001\n")
    assert gate.main() == 0


def test_navigational_document_citations_are_still_checked(tmp_path: Path):
    """A README citing a decision that does not exist is the same defect as an ADR doing so."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001")
    (tmp_path / "adr" / "README.md").write_text("# adr\n\nGoverned by ADR-0099.\n")
    assert gate.main() == 1


def test_navigational_document_links_are_still_checked(tmp_path: Path):
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001")
    (tmp_path / "adr" / "README.md").write_text("# adr\n\nSee [nothing](ADR-0404.md).\n")
    assert gate.main() == 1


def test_navigational_document_is_not_indexed_as_an_id(tmp_path: Path):
    """Two READMEs in different directories must not collide as duplicate IDs."""
    gate = load_gate(tmp_path)
    write_adr(tmp_path, "ADR-0001")
    (tmp_path / "adr" / "README.md").write_text("# adr\n")
    (tmp_path / "standards").mkdir(parents=True)
    (tmp_path / "standards" / "README.md").write_text("# standards\n")
    assert gate.main() == 0


# ── The real corpus ─────────────────────────────────────────────────────────────

def test_real_constitution_passes():
    """The gate against the committed constitution. Deferred L-nn citations are expected
    until Issues #3 and #4 deliver specs/limitations/ (Defect Report DR-002, D-3)."""
    spec = importlib.util.spec_from_file_location("links_gate_real", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.main() == 0

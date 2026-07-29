"""Repository structure as an executable assertion.

Issue #2's required test: no forbidden directory names at any depth, plus the structural
guarantees the skeleton exists to provide.

SCOPE, AND WHY IT IS SCOPED
---------------------------
ADR-0019 governs the monorepo structure defined by Architecture Freeze v1.0. It does not
govern trees that predate the Freeze and are already scheduled for removal — applying a new
rule retroactively to code awaiting deletion would produce a failure nobody can act on
without doing another issue's work.

Legacy roots are therefore excluded, but on exactly the terms approved for the namespace
deferral in Issue #1 (D-3):

  1. An exclusion is permitted only for a root explicitly scheduled by a later issue.
  2. The exclusion expires by itself: once the root is gone, the entry is stale, and
     `test_scheduled_removals_have_not_already_happened` fails until it is deleted.

Without (2) an exclusion list becomes a permanent suppression file, which is the failure
mode this project has already met once — a guard that silently disabled 188 tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directory names that may never appear inside the architecture tree. Each is a dependency
# cycle waiting to happen: a package with no responsibility accumulates whatever does not
# obviously belong elsewhere, and then everything imports it.
FORBIDDEN_NAMES = frozenset({"common", "shared", "utils", "core", "misc", "legacy", "archive"})

# The roots ADR-0019 governs. A root is added here when the issue that creates it lands.
ARCHITECTURE_ROOTS = (
    "adr",
    "standards",
    "contracts",
    "domain",
    "kernel",
    "contexts",
    "registry",
    "apps",
    "specs",
    "tools",
    "tests",
)

# Roots predating the Freeze, excluded from the forbidden-name rule ONLY because a named
# issue removes or restructures them. See the module docstring for the expiry rule.
SCHEDULED_FOR_REMOVAL = {
    "research": "Issue #9 — amputation of the v1 generation",
    "web": "Issue #42 — portal re-partition into apps/portal",
}

# Directories that must exist with a README once Issue #2 has landed.
REQUIRED_TREE = (
    "adr", "adr/superseded",
    "standards",
    "contracts",
    "domain", "domain/entities", "domain/values", "domain/invariants",
    "kernel", "kernel/provenance",
    "contexts",
    "contexts/ingest", "contexts/curation", "contexts/groundtruth",
    "contexts/method", "contexts/evaluation", "contexts/evidence",
    "registry",
    "registry/datasets", "registry/labels", "registry/methods", "registry/protocols",
    "registry/environments", "registry/evaluations", "registry/supersessions",
    "apps", "apps/portal",
    "specs",
    "tools", "tools/gates", "tools/dev",
    "tests", "tests/architecture", "tests/property", "tests/integration",
)

# adr/superseded holds ADR files, not a README; its parent documents the convention.
NO_README_REQUIRED = frozenset({"adr/superseded"})


def architecture_directories() -> list[Path]:
    found: list[Path] = []
    for root in ARCHITECTURE_ROOTS:
        base = REPO_ROOT / root
        if not base.exists():
            continue
        found.append(base)
        found.extend(p for p in base.rglob("*") if p.is_dir())
    return found


# ── The required test: no forbidden directory names ─────────────────────────────

def test_no_forbidden_directory_names_in_architecture_tree():
    """ADR-0019: no common/, shared/, utils/, core/, misc/, legacy/ or archive/."""
    offenders = [
        str(d.relative_to(REPO_ROOT))
        for d in architecture_directories()
        if d.name in FORBIDDEN_NAMES
    ]
    assert not offenders, (
        f"forbidden directory name(s) in the architecture tree: {offenders}. "
        f"Shared vocabulary belongs in contracts/ (ADR-0019)."
    )


def test_forbidden_name_check_actually_inspects_directories():
    """Deliberate-violation guard for the test above.

    A test that scans an empty set passes vacuously. This asserts the scan reaches a
    meaningful population, so that a future refactor which silently empties
    ARCHITECTURE_ROOTS cannot leave the rule passing while checking nothing.
    """
    assert len(architecture_directories()) >= len(REQUIRED_TREE)


# ── The skeleton exists and is documented ───────────────────────────────────────

@pytest.mark.parametrize("relative", REQUIRED_TREE)
def test_required_directory_exists(relative: str):
    assert (REPO_ROOT / relative).is_dir(), f"missing architecture directory: {relative}"


@pytest.mark.parametrize(
    "relative", [d for d in REQUIRED_TREE if d not in NO_README_REQUIRED]
)
def test_required_directory_has_readme(relative: str):
    """Two purposes. It satisfies the acceptance criterion that every directory states its
    responsibility and its exclusions — and it is what makes the skeleton survive a clone,
    since git does not track empty directories."""
    readme = REPO_ROOT / relative / "README.md"
    assert readme.is_file(), f"{relative} has no README.md"
    text = readme.read_text()
    assert "## Responsibility" in text, f"{relative}/README.md does not state a responsibility"
    assert "## What may not enter" in text, f"{relative}/README.md does not state exclusions"


# ── Exclusions must expire ──────────────────────────────────────────────────────

@pytest.mark.parametrize("root,owner", sorted(SCHEDULED_FOR_REMOVAL.items()))
def test_scheduled_removals_have_not_already_happened(root: str, owner: str):
    """An exclusion that outlives its justification is a suppression.

    Once the owning issue removes the root, this fails until the entry is deleted from
    SCHEDULED_FOR_REMOVAL — at which point the forbidden-name rule would apply to it anyway,
    which is the correct end state.
    """
    assert (REPO_ROOT / root).exists(), (
        f"'{root}' no longer exists, so its exclusion is stale. "
        f"Remove it from SCHEDULED_FOR_REMOVAL ({owner})."
    )


def test_no_architecture_root_is_also_scheduled_for_removal():
    """A root cannot simultaneously be governed and exempt."""
    overlap = set(ARCHITECTURE_ROOTS) & set(SCHEDULED_FOR_REMOVAL)
    assert not overlap, f"root(s) both governed and excluded: {sorted(overlap)}"

"""Self-tests for the import-graph policy engine.

Issue #6's stated test is "self-test — a deliberate violation fails". A harness that has
only ever been run against compliant code is a harness nobody has seen reject anything, and
this repository has already shipped one gate that passed because it was never exercised
against a violation.

Every test below builds a fixture package on disk and asserts the analyser's verdict on it.
Fixtures rather than the real tree, because a self-test that depended on the repository's
current contents would start failing for reasons unrelated to the harness.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

GATE_PATH = Path(__file__).resolve().parents[2] / "tools" / "gates" / "imports.py"


def load_gate(root: Path):
    """Load the analyser with its repository root re-pointed at a fixture tree."""
    spec = importlib.util.spec_from_file_location(f"imports_gate_{root.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.REPO_ROOT = root
    return module


def package(root: Path, dotted: str, **modules: str) -> Path:
    """Create a package with `__init__.py` plus the named modules."""
    directory = root / Path(*dotted.split("."))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").write_text("")
    for name, body in modules.items():
        (directory / f"{name}.py").write_text(body)
    return directory


# ── The analyser accepts compliant code ─────────────────────────────────────────

def test_stdlib_only_package_passes(tmp_path):
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", digest="import hashlib\nimport sys\n")
    package(tmp_path, "kernel")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 0, report.violations
    assert report.modules == 3


def test_self_import_is_permitted(tmp_path):
    """A package may import itself; TIS E3 §5 names the kernel's sibling modules."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance",
            dag="from kernel.provenance.digest import Digest\n", digest="")
    package(tmp_path, "kernel")

    _, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 0


def test_explicitly_allowed_root_is_permitted(tmp_path):
    gate = load_gate(tmp_path)
    package(tmp_path, "contexts.evaluation", engine="import contracts\nimport domain\n")
    package(tmp_path, "contexts")
    package(tmp_path, "contracts")
    package(tmp_path, "domain")

    _, code = gate.run([
        gate.Policy(package="contexts.evaluation", allow=frozenset({"contracts", "domain"})),
        gate.Policy(package="contexts", exclude=("tests", "evaluation")),
        gate.Policy(package="contracts"),
        gate.Policy(package="domain"),
    ])
    assert code == 0


# ── Deliberate violations: each must FAIL ───────────────────────────────────────

def test_third_party_import_is_rejected(tmp_path):
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", digest="import hashlib\nimport numpy\n")
    package(tmp_path, "kernel")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 1
    assert any("numpy" in v for v in report.violations)


def test_disallowed_internal_import_is_rejected(tmp_path):
    """The kernel may not reach into a context."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", dag="from contexts.ingest import parsers\n")
    package(tmp_path, "kernel")
    package(tmp_path, "contexts")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
        gate.Policy(package="contexts"),
    ])
    assert code == 1
    assert any("contexts" in v for v in report.violations)


def test_a_relative_import_cannot_evade_the_policy(tmp_path):
    """`from . import x` is an import of the enclosing package however it is spelled. A
    policy evadable by changing import syntax would not be a policy."""
    gate = load_gate(tmp_path)
    package(tmp_path, "contexts.evaluation", engine="from . import sibling\n", sibling="")
    package(tmp_path, "contexts")

    report, code = gate.run([
        # `contexts` is deliberately NOT in `allow`, and the package root is `contexts`,
        # so a correctly-resolved relative import is permitted here...
        gate.Policy(package="contexts.evaluation"),
        gate.Policy(package="contexts", exclude=("tests", "evaluation")),
    ])
    assert code == 0, report.violations

    # ...but it IS resolved rather than ignored: a policy on a differently-rooted package
    # sees the same import as reaching `contexts`.
    assert "contexts" in gate.imported_roots(
        tmp_path / "contexts" / "evaluation" / "engine.py"
    )


def test_stdlib_can_be_forbidden_when_a_policy_says_so(tmp_path):
    """ADR-0026's literal wording is stricter than TIS E3 §11 (DR-006). The engine can
    express the strict form even though no policy uses it today."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", digest="import hashlib\n")
    package(tmp_path, "kernel")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance", allow_stdlib=False),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 1
    assert any("hashlib" in v for v in report.violations)


# ── Fail-closed ─────────────────────────────────────────────────────────────────

def test_a_policy_for_a_missing_package_is_an_error(tmp_path):
    """A renamed package must not silently disable its own policy."""
    gate = load_gate(tmp_path)
    with pytest.raises(gate.PolicyError, match="does not exist"):
        gate.run([gate.Policy(package="kernel.absent")])


def test_an_empty_policy_set_refuses_to_pass(tmp_path):
    gate = load_gate(tmp_path)
    with pytest.raises(gate.PolicyError, match="vacuously"):
        gate.run([])


def test_a_package_declared_populated_but_empty_is_a_violation(tmp_path):
    """A scan over nothing reports success while checking nothing."""
    gate = load_gate(tmp_path)
    directory = tmp_path / "kernel" / "provenance"
    directory.mkdir(parents=True)

    report, code = gate.run([gate.Policy(package="kernel.provenance", populated=True)])
    assert code == 1
    assert any("no runtime module" in v for v in report.violations)


def test_a_package_declared_unpopulated_that_gains_code_is_a_violation(tmp_path):
    """The self-expiring declaration. Once a package has code, the policy must bind."""
    gate = load_gate(tmp_path)
    package(tmp_path, "contexts.ingest", adapter="import os\n")
    package(tmp_path, "contexts")

    report, code = gate.run([
        gate.Policy(package="contexts.ingest", populated=False),
        gate.Policy(package="contexts", exclude=("tests", "ingest")),
    ])
    assert code == 1
    assert any("declared unpopulated" in v for v in report.violations)


def test_an_ungoverned_package_is_a_violation(tmp_path):
    """A new package must not be ungoverned by default."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", digest="")
    package(tmp_path, "kernel")
    package(tmp_path, "domain.entities", thing="")
    package(tmp_path, "domain")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 1
    assert any("no import policy" in v and "domain" in v for v in report.violations)


def test_a_parent_policy_covers_its_subpackages(tmp_path):
    gate = load_gate(tmp_path)
    package(tmp_path, "domain.entities", thing="import os\n")
    package(tmp_path, "domain")

    report, code = gate.run([gate.Policy(package="domain")])
    assert code == 0, report.violations


# ── Test directories are excluded from the runtime surface ──────────────────────

def test_test_modules_are_not_part_of_the_governed_surface(tmp_path):
    """A test importing pytest is not the package importing pytest; the shipped package does
    not contain it."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", digest="import hashlib\n")
    package(tmp_path, "kernel.provenance.tests", test_digest="import pytest\n")
    package(tmp_path, "kernel")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 0, report.violations


# ── Reporting (STD-07) ──────────────────────────────────────────────────────────

def test_the_report_enumerates_what_was_checked(tmp_path):
    """A report of failures alone cannot be distinguished from a gate that never ran."""
    gate = load_gate(tmp_path)
    package(tmp_path, "kernel.provenance", a="import os\n", b="import sys\nimport json\n")
    package(tmp_path, "kernel")

    report, code = gate.run([
        gate.Policy(package="kernel.provenance"),
        gate.Policy(package="kernel", exclude=("tests", "provenance")),
    ])
    assert code == 0
    assert report.modules == 4
    assert report.imports == 3
    assert report.policies == 2


# ── The real repository ─────────────────────────────────────────────────────────

def test_the_repository_satisfies_its_own_policies():
    """The harness applied to the tree it governs. This is what makes it a gate rather than
    a library."""
    spec = importlib.util.spec_from_file_location("imports_gate_real", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.main() == 0


def test_the_real_policy_set_is_not_empty():
    """Guards against a future edit emptying POLICIES and leaving the gate green."""
    spec = importlib.util.spec_from_file_location("imports_gate_policies", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert len(module.POLICIES) >= 2

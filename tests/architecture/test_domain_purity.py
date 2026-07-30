"""The domain model's purity.

The counterpart of `test_kernel_isolation.py`, delivered by M2/E4/#12 for the same reason
M2/E3/#10 delivered that one: a package whose value rests on what it *cannot* reach needs the
restriction checked, not stated.

THE PRECISE RULE. ADR-0026: "`domain/` imports stdlib only." TIS E4 §11(i) repeats it, and
§16 gives the consequence — unit tests use no fixtures and no mocks, because if a mock is
needed the code is in the wrong layer.

WHAT THIS FILE IS NOT
---------------------
It is not M2/E4/#13. That issue owns all six ADR-0026 import rules with deliberate-violation
tests across every context, and depends on #12 for exactly that reason. This file covers only
the facts #12 itself creates: that `domain/` imports nothing but the standard library and
itself, that it does not re-declare what the kernel owns, that it cannot mint a digest, and
that it cannot read a clock. The import-policy gate (`tools/gates/imports.py`) enforces the
first mechanically; this asserts it independently, so a policy edit cannot quietly widen the
rule without a second file disagreeing.

Analysed with `ast` rather than by importing, so a module with a broken import is reported as
a violation instead of crashing the run.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN = REPO_ROOT / "domain"

INTERNAL_PACKAGES = frozenset(
    {"kernel", "domain", "contexts", "contracts", "apps", "tools", "tests", "registry"}
)

STDLIB = frozenset(sys.stdlib_module_names)

#: Entities `kernel/provenance` owns. ADR-0026 made provenance a shared kernel; a second
#: declaration in `domain/` would be two definitions of one concept, which is the drift
#: ADR-0019 exists to prevent.
KERNEL_OWNED = ("Artifact", "ProvenanceRecord", "Run", "RunStatus", "ProvenanceStore")


def domain_modules() -> list[Path]:
    """Runtime modules under `domain/`, excluding its own tests."""
    return sorted(
        path
        for path in DOMAIN.rglob("*.py")
        if not path.name.startswith("._") and "tests" not in path.relative_to(DOMAIN).parts
    )


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_domain_has_modules_to_check():
    """Fail closed: a scan over an empty set reports success while checking nothing."""
    modules = domain_modules()
    assert len(modules) >= 10, f"expected the domain to be populated, found {len(modules)}"


@pytest.mark.parametrize("path", domain_modules(), ids=lambda p: p.stem)
def test_domain_module_imports_no_third_party(path: Path):
    """ADR-0026, TIS E4 §11(i). The standard library and `domain` itself, nothing else."""
    offenders = {
        root
        for root in imported_roots(path)
        if root not in STDLIB and root not in INTERNAL_PACKAGES and root != "__future__"
    }
    assert not offenders, f"{path.relative_to(REPO_ROOT)} imports third-party {offenders}"


@pytest.mark.parametrize("path", domain_modules(), ids=lambda p: p.stem)
def test_domain_module_imports_no_other_internal_package(path: Path):
    """`kernel` is the tempting one, and it is the edge ADR-0026 forbids.

    `kernel.provenance.Digest` would be the obvious import for a package full of content
    addresses. Taking it would make the pure domain depend on the shared kernel and would
    make every domain test require the kernel to be importable.
    """
    offenders = {
        root
        for root in imported_roots(path)
        if root in INTERNAL_PACKAGES and root != "domain"
    }
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} imports internal package(s) {offenders}; "
        f"ADR-0026 permits the standard library and `domain` itself"
    )


@pytest.mark.parametrize("name", KERNEL_OWNED)
def test_domain_does_not_redefine_kernel_entities(name: str):
    """ADR-0002 lists them; ADR-0026 assigns them to the kernel. One definition, one owner."""
    for path in domain_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        declared = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        }
        assert name not in declared, (
            f"{path.relative_to(REPO_ROOT)} declares {name}, which kernel/provenance owns"
        )


def test_the_domain_cannot_mint_a_digest():
    """ADR-0005: digests are minted by the shared kernel and by nothing else.

    `hashlib` is standard library, so the import policy would permit it. The absence is a
    decision, and this is where the decision is checked.
    """
    offenders = [
        path.relative_to(REPO_ROOT)
        for path in domain_modules()
        if "hashlib" in imported_roots(path)
    ]
    assert not offenders, f"{offenders} import hashlib; only the kernel may mint a digest"


def test_the_domain_cannot_read_a_clock():
    """TIS §0.4: determinism is enforced by a pinned input, not by discipline.

    `datetime` is permitted — parsing a recorded instant is not reading a clock — but the
    call that returns *now* is not. Checked by call site rather than by import, because the
    module is legitimately needed and only one of its functions is forbidden.
    """
    forbidden = {"now", "utcnow", "today", "time", "monotonic", "time_ns"}
    offenders: list[str] = []
    for path in domain_modules():
        if "time" in imported_roots(path) or "random" in imported_roots(path):
            offenders.append(f"{path.relative_to(REPO_ROOT)} imports time/random")
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in forbidden:
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT)}:{node.lineno} calls .{node.func.attr}()"
                    )
    assert not offenders, f"the domain reads a clock: {offenders}"


def test_the_domain_reads_no_environment_and_performs_no_io():
    """TIS §0.4 and E4 §2: persistence and I/O are out of scope for this epic."""
    forbidden_roots = {"os", "io", "socket", "subprocess", "pathlib", "shutil", "urllib"}
    offenders = [
        f"{path.relative_to(REPO_ROOT)} imports {sorted(imported_roots(path) & forbidden_roots)}"
        for path in domain_modules()
        if imported_roots(path) & forbidden_roots
    ]
    assert not offenders, f"the domain performs I/O: {offenders}"


def test_every_invariant_is_reachable_from_the_public_interface():
    """TIS E4 §4 makes `domain.invariants.*` part of the epic's public interface."""
    from domain import invariants

    for predicate, _ in invariants.ALL_INVARIANTS:
        assert getattr(invariants, predicate.__name__, None) is predicate


def test_the_domain_declares_an_import_policy():
    """`tools/gates/imports.py` treats a package with no policy as a failure (STD-07).

    Asserted here as well as in the gate so that removing the policy fails two files rather
    than silently un-governing the package.
    """
    from tools.gates.imports import POLICIES

    policy = next((p for p in POLICIES if p.package == "domain"), None)
    assert policy is not None, "domain has no import policy"
    assert policy.allow == frozenset(), "domain's policy permits an internal package"
    assert policy.allow_stdlib is True

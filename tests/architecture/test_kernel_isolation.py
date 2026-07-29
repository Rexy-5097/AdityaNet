"""The provenance kernel's import isolation.

ADR-0026 makes provenance a shared kernel: vocabulary used by every context, with no domain
behaviour of its own. That is only true if it cannot reach into anything.

THE PRECISE RULE. ADR-0026's shorthand is "imports nothing". Read literally that forbids
`hashlib`, which makes SHA-256 impossible, which makes ADR-0005 unimplementable. TIS E3 §11
gives the exact form and is what this test encodes:

    no internal package, no third party. The standard library is permitted.
    Sibling modules within the kernel are permitted — TIS E3 §5 names them.

Reported as DR-006, a Documentation Defect against ADR-0026's phrasing. ADRs are immutable,
so the ambiguity is resolved here rather than there.

Analysed with `ast` rather than by importing, so a module with an import that fails is
reported as a violation instead of crashing the test run.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
KERNEL = REPO_ROOT / "kernel" / "provenance"

# Every top-level directory that is a repository package. Importing any of these from the
# kernel would make the shared kernel depend on a context.
INTERNAL_PACKAGES = frozenset(
    {"kernel", "domain", "contexts", "contracts", "apps", "tools", "tests", "registry"}
)

STDLIB = frozenset(sys.stdlib_module_names)


def kernel_modules() -> list[Path]:
    """Runtime modules only.

    Test modules under the kernel legitimately import pytest: a test importing a third-party
    library is not the kernel importing it, and the shipped package does not contain them.
    Excluding them is scoping, not an exemption — the runtime surface is what ships.
    """
    return sorted(
        path
        for path in KERNEL.rglob("*.py")
        if not path.name.startswith("._") and "tests" not in path.relative_to(KERNEL).parts
    )


def imported_roots(path: Path) -> set[str]:
    """Top-level module name of every import in a file."""
    tree = ast.parse(path.read_text(), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                pytest.fail(f"{path.name}: relative import; the kernel uses absolute paths")
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def test_the_kernel_has_modules_to_check():
    """A scan over an empty set passes vacuously. This is the guard that stops a future
    refactor from leaving the rule green while checking nothing."""
    modules = kernel_modules()
    assert len(modules) >= 7, f"expected the kernel's modules, found {len(modules)}"


@pytest.mark.parametrize("path", kernel_modules(), ids=lambda p: p.name)
def test_kernel_module_imports_no_third_party(path: Path):
    """Every import resolves to the standard library or to the kernel itself."""
    offenders = sorted(
        root
        for root in imported_roots(path)
        if root not in STDLIB and root != "kernel"
    )
    assert not offenders, (
        f"kernel/provenance/{path.name} imports third-party package(s) {offenders}. "
        f"TIS E3 §11: the kernel imports no internal package and no third party."
    )


@pytest.mark.parametrize("path", kernel_modules(), ids=lambda p: p.name)
def test_kernel_module_imports_no_other_internal_package(path: Path):
    """`kernel` is permitted; every other repository package is not."""
    offenders = sorted(
        root
        for root in imported_roots(path)
        if root in INTERNAL_PACKAGES and root != "kernel"
    )
    assert not offenders, (
        f"kernel/provenance/{path.name} imports internal package(s) {offenders}. "
        f"The shared kernel may not depend on a context (ADR-0026)."
    )


@pytest.mark.parametrize("path", kernel_modules(), ids=lambda p: p.name)
def test_kernel_module_carries_no_domain_vocabulary(path: Path):
    """TIS E3 §6: no domain object may enter this kernel.

    Checked on identifiers rather than prose, so that a docstring may explain why the rule
    exists — as several do — without tripping it.
    """
    forbidden = ("solexs", "hel1os", "flare", "aditya", "goes", "evaluation", "instrument")
    tree = ast.parse(path.read_text(), filename=str(path))
    names = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    } | {
        node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)
    }

    offenders = sorted(word for word in forbidden if any(word in name for name in names))
    assert not offenders, (
        f"kernel/provenance/{path.name} names domain concept(s) {offenders}. "
        f"The shared kernel has no domain knowledge (ADR-0026)."
    )


def test_the_public_interface_is_the_one_the_tis_specifies():
    """TIS E3 §4. A kernel that quietly grew a new public operation would be a kernel whose
    contract nobody re-read."""
    sys.path.insert(0, str(REPO_ROOT))
    import kernel.provenance as provenance

    required = {
        "digest_bytes", "digest_file", "digest_stream", "digest_chunks",
        "begin_run", "Run", "RunStatus",
        "Artifact", "ProvenanceRecord", "ProvenanceStore",
        "Digest", "ancestors",
        "IntegrityFailure", "ProvenanceFailure",
    }
    exported = set(provenance.__all__)
    assert required <= exported, f"missing from the public interface: {sorted(required - exported)}"
    assert exported <= required | {"KernelError", "CHUNK_BYTES", "new_run_id",
                                   "producers", "would_create_cycle"}, (
        f"undeclared public surface: {sorted(exported - required)}"
    )

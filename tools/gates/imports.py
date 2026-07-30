#!/usr/bin/env python3
"""Import-graph policy engine.

WHAT THIS IS FOR
----------------
ADR-0026 states the dependency direction between the shared kernel and the six bounded
contexts. A dependency rule that lives only in an ADR is applied by a human reading the ADR,
which is the definition of a preference rather than a standard (STD-01, STD-11).

This module turns such a rule into a program: a policy names a package and the roots it may
import, the analyser reports every violation, and the caller exits non-zero. It carries NO
context rules of its own — those belong to the issue that encodes them. What ships here is
the mechanism and the proof that the mechanism rejects violations.

WHY `ast` AND NOT `import`
--------------------------
Importing a package to inspect its imports executes it. A module with a broken import would
then crash the analyser instead of being reported as the violation it is, and a module with
a side effect would run it. Static parsing reports what the source says, which is the thing
the rule is about.

FAIL-CLOSED (ADR-0020, STD-07)
------------------------------
Three ways this refuses to pass quietly:

  - A policy naming a package that does not exist is an error, not a skipped rule. Otherwise
    a renamed package silently disables its own policy.
  - A policy declared `populated` that contains no modules is an error. A scan over an empty
    set reports success while checking nothing, which is indistinguishable from a gate that
    never ran.
  - A package present in the tree with no policy at all is an error. Otherwise a new package
    is ungoverned by default, and the rule set silently stops covering the repository.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Top-level directories that are Python packages in the architecture tree. A directory
# listed here must have a policy; see `undeclared` below.
GOVERNED_ROOTS = ("kernel", "domain", "contexts", "contracts", "apps", "tools", "registry")

STDLIB = frozenset(sys.stdlib_module_names)


class PolicyError(Exception):
    """The policy itself is unusable — a PolicyRejection in the TIS §0.2 taxonomy."""


@dataclass(frozen=True)
class Policy:
    """What one package is permitted to import.

    `package`     dotted path relative to the repository root, e.g. "kernel.provenance".
    `allow`       top-level module roots this package may import, beyond the standard
                  library and itself. Empty means: stdlib and itself only.
    `allow_stdlib` False forbids even the standard library. No policy needs this today; it
                  exists because ADR-0026's text is stricter than TIS E3 §11 and a future
                  rule may need to express the stricter form (see DR-006).
    `populated`   whether this package is expected to contain modules. A package still being
                  built declares False; once it has code the declaration must change, and
                  `stale` reports it if it does not.
    `exclude`     path fragments whose modules are not runtime code — test directories. A
                  test importing pytest is not the package importing pytest.
    """

    package: str
    allow: frozenset[str] = frozenset()
    allow_stdlib: bool = True
    populated: bool = True
    exclude: tuple[str, ...] = ("tests",)

    @property
    def path(self) -> Path:
        return REPO_ROOT / Path(*self.package.split("."))

    @property
    def root(self) -> str:
        return self.package.split(".")[0]


@dataclass
class Report:
    """Enumerates what was checked, not only what failed (STD-07)."""

    modules: int = 0
    imports: int = 0
    policies: int = 0
    violations: list[str] = field(default_factory=list)

    def violation(self, message: str) -> None:
        self.violations.append(message)


def modules_of(policy: Policy) -> list[Path]:
    """Runtime modules governed by a policy, in a stable order."""
    if not policy.path.is_dir():
        raise PolicyError(
            f"policy names package '{policy.package}' but {policy.path} does not exist"
        )
    return sorted(
        path
        for path in policy.path.rglob("*.py")
        if not path.name.startswith("._")
        and not set(path.relative_to(policy.path).parts) & set(policy.exclude)
    )


def imported_roots(path: Path) -> set[str]:
    """Top-level module name of every import in a file.

    A relative import is resolved to the package it sits in, because `from . import x` inside
    `kernel.provenance` is an import of `kernel` however it is spelled — a policy that could
    be evaded by changing import syntax would not be a policy.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                roots.add(path.relative_to(REPO_ROOT).parts[0])
            elif node.module:
                roots.add(node.module.split(".")[0])

    return roots


def check(policy: Policy, report: Report) -> None:
    """Apply one policy, recording every violation it finds."""
    modules = modules_of(policy)
    report.policies += 1

    if policy.populated and not modules:
        report.violation(
            f"{policy.package}: declared populated but contains no runtime module. "
            f"A scan over nothing passes while checking nothing."
        )
        return

    if not policy.populated and modules:
        report.violation(
            f"{policy.package}: declared unpopulated but contains "
            f"{len(modules)} module(s). Update the policy so the rule binds."
        )
        return

    permitted = set(policy.allow) | {policy.root}

    for module in modules:
        report.modules += 1
        for root in sorted(imported_roots(module)):
            report.imports += 1
            if root in permitted:
                continue
            if root in STDLIB:
                if policy.allow_stdlib:
                    continue
                report.violation(
                    f"{module.relative_to(REPO_ROOT)}: imports stdlib '{root}', "
                    f"which {policy.package} forbids"
                )
                continue
            report.violation(
                f"{module.relative_to(REPO_ROOT)}: imports '{root}', "
                f"not permitted by the policy for {policy.package} "
                f"(allowed: {sorted(permitted) or 'itself only'})"
            )


def undeclared(policies: list[Policy]) -> list[str]:
    """Packages present in the governed roots with no policy covering them.

    Without this, adding a package silently adds an ungoverned package, and the rule set
    stops describing the repository without anyone editing it.
    """
    declared = {p.package for p in policies}
    missing: list[str] = []

    for root in GOVERNED_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for init in base.rglob("__init__.py"):
            if init.name.startswith("._"):
                continue
            package = ".".join(init.parent.relative_to(REPO_ROOT).parts)
            if "tests" in init.parent.parts:
                continue
            # A parent policy covers its subpackages.
            if any(package == d or package.startswith(f"{d}.") for d in declared):
                continue
            missing.append(package)

    return sorted(set(missing))


def run(policies: list[Policy]) -> tuple[Report, int]:
    """Apply every policy. Returns the report and a process exit code."""
    report = Report()

    if not policies:
        raise PolicyError("no policies supplied; refusing to pass vacuously")

    for policy in policies:
        check(policy, report)

    for package in undeclared(policies):
        report.violation(
            f"{package}: is a package in a governed root with no import policy. "
            f"Add one, or it is ungoverned by default."
        )

    return report, 1 if report.violations else 0


# ── The policy set in force today ───────────────────────────────────────────────
#
# Only rules that are determinable now. The six bounded-context rules of ADR-0026 belong to
# the issue that encodes them, and the context packages contain no code yet, so writing them
# here would produce rules that check nothing.
#
# kernel.provenance: TIS E3 §11 — no internal package, no third party. The standard library
# is permitted; ADR-0026's shorthand "imports nothing" would forbid hashlib and so make
# ADR-0005 unimplementable (DR-006).

POLICIES = [
    Policy(package="kernel.provenance", allow=frozenset(), allow_stdlib=True),
    # kernel/__init__.py alone — the package marker. Declared populated because it exists;
    # the gate rejected an earlier declaration of False, which is the `stale` check working.
    Policy(package="kernel", allow=frozenset(), allow_stdlib=True,
           exclude=("tests", "provenance")),
]


def main() -> int:
    try:
        report, code = run(POLICIES)
    except PolicyError as exc:
        print(f"imports: GATE FAILURE — {exc}", file=sys.stderr)
        return 1

    print(
        f"imports: checked {report.modules} module(s), {report.imports} import(s) "
        f"under {report.policies} polic(ies)"
    )

    if report.violations:
        print(f"\nimports: {len(report.violations)} violation(s)", file=sys.stderr)
        for violation in report.violations:
            print(f"  {violation}", file=sys.stderr)
        return code

    print("imports: every import is permitted by its package's policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

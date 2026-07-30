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


def imported_paths(path: Path) -> set[str]:
    """The FULL dotted path of every import in a file.

    WHY THIS EXISTS ALONGSIDE `imported_roots` (added by M2/E4/#13)
    ---------------------------------------------------------------
    `imported_roots` collapses `contexts.curation.freeze` to `contexts`. That is the right
    granularity for deciding whether an import is stdlib, third party, or internal, and it is
    what the stdlib classification below still uses.

    It is the wrong granularity for ADR-0026's fifth dependency rule — *no context imports
    another context's internals*. Every bounded context lives under one root, so at root
    granularity `contexts.evaluation` importing `contexts.method` is indistinguishable from it
    importing itself, and the rule is not merely unenforced but **inexpressible**. Issue #6
    shipped the mechanism and deferred these rules to the issue that encodes them; encoding
    them requires seeing the whole path.

    Relative imports resolve against the importing module's own package, because `from .
    import x` inside `contexts.ingest` is an import of `contexts.ingest` however it is spelled.
    A rule evadable by changing import syntax would not be a rule.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    own_package = ".".join(path.relative_to(REPO_ROOT).parent.parts)
    found: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = own_package.split(".")
                # level 1 is the current package, level 2 its parent, and so on.
                climbed = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                base = ".".join(climbed)
                found.add(f"{base}.{node.module}" if node.module else base)
            elif node.module:
                found.add(node.module)

    return found


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

    permitted = set(policy.allow)

    for module in modules:
        report.modules += 1
        for dotted in sorted(imported_paths(module)):
            report.imports += 1

            # A package may always import itself. Matched against the policy's OWN dotted
            # package rather than its top-level root — tightened by M2/E4/#13. Under the
            # previous root-granularity rule, `policy.root` for `contexts.evaluation` was
            # `contexts`, so importing `contexts.method` counted as importing itself and
            # ADR-0026's fifth dependency rule could not be stated at all.
            if dotted == policy.package or dotted.startswith(f"{policy.package}."):
                continue

            root = dotted.split(".")[0]
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
                f"{module.relative_to(REPO_ROOT)}: imports '{dotted}', "
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
# kernel.provenance: TIS E3 §11 — no internal package, no third party. The standard library
# is permitted; ADR-0026's shorthand "imports nothing" would forbid hashlib and so make
# ADR-0005 unimplementable (DR-006).
#
# THE SIX BOUNDED-CONTEXT RULES (M2/E4/#13)
# -----------------------------------------
# Issue #6 deferred these, on the grounds that the context packages contained no code and a
# rule over nothing checks nothing. That reasoning was right about *today* and wrong about
# *tomorrow*, and the difference is what these entries close.
#
# Every context declares `populated=False`. That is not a placeholder — it is a live
# assertion, and `check` above rejects a policy declaring False while modules exist. So the
# first `.py` file added to any context turns the gate red until that issue states what its
# context may import. Without these entries a new module under `contexts/` would be governed
# by nothing at all: `undeclared` finds packages by `__init__.py`, and none of these
# directories has one, so a context module would be neither policed nor reported missing.
#
# `allow` lists only what ADR-0026 grants. Third-party roots are NOT pre-granted: the ADR
# does not grant them, and a context that later needs `astropy` should add one reviewable
# line rather than inherit a blanket permission nobody voted for (STD-11).
#
# No context may import another context. That is enforced by the dotted self-match in
# `check`, not by anything listed here — `contexts` is deliberately absent from every
# `allow` below, and six deliberate-violation tests in
# `tests/architecture/test_context_imports.py` prove each one rejects.

POLICIES = [
    Policy(package="kernel.provenance", allow=frozenset(), allow_stdlib=True),
    # kernel/__init__.py alone — the package marker. Declared populated because it exists;
    # the gate rejected an earlier declaration of False, which is the `stale` check working.
    Policy(package="kernel", allow=frozenset(), allow_stdlib=True,
           exclude=("tests", "provenance")),
    # ADR-0026 and TIS E4 §11(i): `domain/` imports the standard library only. `allow` is
    # empty, so the package may import stdlib and itself and nothing else — notably not
    # `kernel`, even though `kernel.provenance.Digest` would otherwise be the obvious thing
    # to reach for. That edge is the one ADR-0026 forbids, and the gate is where the
    # temptation is answered rather than resisted.
    #
    # Declared by M2/E4/#12, which is what put modules under `domain/`. The gate treats a
    # package present in the tree with no policy as a failure, so this entry is not optional
    # bookkeeping: without it the `architecture` job goes red.
    Policy(package="domain", allow=frozenset(), allow_stdlib=True),

    # R1 — Ingest. Acquires and canonicalises. Needs the vocabulary, the domain model and
    # the kernel to register raw artifacts as it acquires them (TIS E5 §19).
    #
    # `populated` flipped to True by M3/E5/#15, the first issue to put code in a context. The
    # staleness check did its job on the way: with the modules added and the flag still False
    # the gate went red — "declared unpopulated but contains 7 module(s)" — which is exactly
    # what M2/E4/#13 built it for. The rule now binds against real code rather than a fixture.
    #
    # `astropy` granted by M3/E5/#17. The SoLEXS products are FITS, and reading FITS needs a
    # FITS reader — hand-rolling one to avoid a dependency would be a far larger risk to
    # scientific fidelity than the dependency is to the architecture. This is the path #13
    # described when it declined to pre-grant third-party roots: "a context that later needs
    # `astropy` should add one reviewable line rather than inherit a blanket permission
    # nobody voted for (STD-11)." This is that line, and it grants astropy to Ingest only.
    Policy(package="contexts.ingest", populated=True,
           allow=frozenset({"contracts", "domain", "kernel", "astropy"})),

    # R2 — Curation. Freezes observations into digest-addressed releases; the kernel is what
    # mints those digests (ADR-0005, ADR-0006).
    Policy(package="contexts.curation", populated=False,
           allow=frozenset({"contracts", "domain", "kernel"})),

    # R3 — Ground Truth. Must not import contexts.curation: its README forbids the merge, and
    # labels revise on a different cadence from the data they label (ADR-0007).
    Policy(package="contexts.groundtruth", populated=False,
           allow=frozenset({"contracts", "domain", "kernel"})),

    # R4 — Method. Must not reach test labels, and must not be imported BY evaluation — the
    # engine executes a released artifact rather than calling a method (ADR-0010, ADR-0016).
    Policy(package="contexts.method", populated=False,
           allow=frozenset({"contracts", "domain", "kernel"})),

    # R5 — Evaluation. ADR-0026 states this one narrowly and literally: "Evaluation imports
    # contracts and domain only". `kernel` is therefore absent, and that is encoded as
    # written rather than widened to what the engine will plausibly need. See AC-001 in the
    # Issue #13 report: TIS E10 §7 requires an Evaluation to carry its own digest, ADR-0005
    # reserves minting to the kernel, and those cannot both hold under this rule. The
    # contradiction is reported for resolution by ADR before M7/#30, not resolved here by
    # quietly loosening a frozen rule.
    Policy(package="contexts.evaluation", populated=False,
           allow=frozenset({"contracts", "domain"})),

    # R6 — Evidence. Reads from every context and writes to none (ADR-0026). "Reads from"
    # means reads their *artifacts*, not imports their modules, so no context root is
    # granted. The kernel is: TIS E11 §10 evaluates supersession transitively via
    # `kernel.provenance.ancestors()`. The write prohibition is not an import rule and is
    # enforced separately, by a static scan in test_context_imports.py.
    Policy(package="contexts.evidence", populated=False,
           allow=frozenset({"contracts", "domain", "kernel"})),
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

"""The six bounded-context import rules of ADR-0026, each with a deliberate violation.

TIS E4 §20 names this file. §15 row 13 states the deliverable as "6 violation tests" and
ADR-0026's own Verification clause asks for "a kernel-zero-imports test plus six
import-direction tests, each with a deliberate-violation case". The kernel-zero-imports test
already exists (`test_kernel_isolation.py`, M2/E3/#10) and `domain/` stdlib-only already
exists (`test_domain_purity.py`, M2/E4/#12). What is missing, and what this file supplies, is
the six.

THE HONEST POSITION ON EMPTY CONTEXTS
--------------------------------------
`contexts/*` contains six README files and no Python. A rule applied to no code is a rule that
has never rejected anything, and this project has already shipped one gate that passed because
it was never exercised against a violation. So none of these tests assert over the real
context tree — every one of them **builds a violating module on disk and asserts the analyser
reports it**. The verdict is about the analyser, which exists, not about code that does not.

Two further tests make the rules bind on the day code arrives rather than on the day someone
remembers them:

  - `test_a_new_module_in_an_empty_context_turns_the_gate_red` — every context declares
    `populated=False`, and the gate rejects that declaration the moment a module appears.
  - `test_every_context_directory_has_a_policy` — a seventh context added without a policy is
    a failure, because `undeclared` finds packages by `__init__.py` and these directories have
    none.

WHAT THIS FILE DOES NOT OWN
---------------------------
The forbidden-directory-name rule of ADR-0019 (`test_repository_structure.py`, M0/#2). The
kernel's zero-import rule (M2/E3/#10). The domain's stdlib-only rule (M2/E4/#12). Any actual
context implementation — E5 onwards. `contracts/manifest.schema.json` — M2/E4/#14.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "gates" / "imports.py"
CONTEXTS = REPO_ROOT / "contexts"

#: The six rules, exactly as ADR-0026 and each context's README state them. `allow` is what
#: the context may import beyond the standard library and itself; the citation is what makes
#: the entry auditable rather than assumed.
CONTEXT_RULES = [
    ("ingest", frozenset({"contracts", "domain", "kernel"}),
     "ADR-0003, ADR-0004, ADR-0017 — acquire and canonicalise"),
    ("curation", frozenset({"contracts", "domain", "kernel"}),
     "ADR-0006, ADR-0023, ADR-0024 — freeze into digest-addressed releases"),
    ("groundtruth", frozenset({"contracts", "domain", "kernel"}),
     "ADR-0007 — exogenous, revisable; must not merge into curation"),
    ("method", frozenset({"contracts", "domain", "kernel"}),
     "ADR-0010, ADR-0011, ADR-0016 — cannot reach test labels"),
    ("evaluation", frozenset({"contracts", "domain"}),
     "ADR-0026 as written: 'Evaluation imports contracts and domain only'"),
    ("evidence", frozenset({"contracts", "domain", "kernel"}),
     "ADR-0026 — read-only; TIS E11 §10 uses kernel.provenance.ancestors()"),
]

CONTEXT_NAMES = [name for name, _, _ in CONTEXT_RULES]

#: This repository's own package roots. An `allow` entry outside this set is a third-party
#: library, which ADR-0026 does not govern and does not grant by default.
INTERNAL_ROOTS = frozenset(
    {"kernel", "domain", "contexts", "contracts", "apps", "tools", "tests", "registry"}
)


def load_gate(root: Path):
    """Load the analyser with its repository root re-pointed at a fixture tree.

    The same harness `test_imports_gate.py` uses. A self-test bound to the repository's
    current contents would start failing for reasons unrelated to the rule under test.
    """
    spec = importlib.util.spec_from_file_location(f"ctx_gate_{root.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.REPO_ROOT = root
    return module


def package(root: Path, dotted: str, **modules: str) -> Path:
    directory = root / Path(*dotted.split("."))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").write_text("")
    for name, body in modules.items():
        (directory / f"{name}.py").write_text(body)
    return directory


def scaffold(root: Path) -> list[str]:
    """The packages a context may import, so a positive case has somewhere to go.

    Returns their names. They must be declared too: the analyser treats any package in a
    governed root with no policy as a violation, so an undeclared scaffold would make a
    positive test fail — and, worse, would make a negative test pass for the wrong reason.
    """
    names = ["contracts", "domain", "kernel"]
    for dotted in names:
        package(root, dotted)
    return names


def scaffold_policies(gate, names: list[str]) -> list:
    """Permissive policies for the scaffold, so the verdict is about the rule under test."""
    return [gate.Policy(package=name, allow=frozenset()) for name in names]


def policy_for(gate, name: str, allow: frozenset[str], **overrides):
    fields = {"package": f"contexts.{name}", "allow": allow, "populated": True}
    fields.update(overrides)
    return gate.Policy(**fields)


# ═══════════════════════════════════════════ the rules are present and match the ADR


def test_the_real_policy_set_covers_all_six_contexts():
    """A rule that is not in POLICIES is not enforced, whatever this file asserts."""
    from tools.gates.imports import POLICIES

    declared = {p.package: p for p in POLICIES}
    for name, allow, citation in CONTEXT_RULES:
        policy = declared.get(f"contexts.{name}")
        assert policy is not None, f"contexts.{name} has no import policy ({citation})"
        internal = policy.allow & INTERNAL_ROOTS
        assert internal == allow, (
            f"contexts.{name} permits internal {sorted(internal)}, "
            f"ADR-0026 grants {sorted(allow)}"
        )


def test_every_third_party_grant_is_named_and_is_not_a_context():
    """A context may be granted a library. It may never be granted another context.

    Comparing only the internal roots above would let a third-party grant appear unnoticed,
    so every non-internal grant is enumerated here as well. Adding one is then two deliberate
    edits — POLICIES and this list — rather than one silent widening. M3/E5/#17 granted
    `astropy` to Ingest because the SoLEXS products are FITS; ADR-0026 grants none by default
    (STD-11), which is what #13 recorded when it declined to pre-grant any.
    """
    from tools.gates.imports import GOVERNED_ROOTS, POLICIES

    granted: dict[str, set[str]] = {}
    for policy in POLICIES:
        if not policy.package.startswith("contexts."):
            continue
        third_party = policy.allow - INTERNAL_ROOTS
        assert not (third_party & set(GOVERNED_ROOTS)), (
            f"{policy.package} grants {sorted(third_party & set(GOVERNED_ROOTS))}, which is "
            f"a governed root of this repository, not a third-party library"
        )
        if third_party:
            granted[policy.package] = third_party

    assert granted == {"contexts.ingest": {"astropy"}}, (
        f"third-party grants changed: {granted}"
    )


def test_no_context_policy_grants_the_contexts_root():
    """ADR-0026 rule 5. Granting `contexts` would permit every context to import every other."""
    from tools.gates.imports import POLICIES

    for policy in POLICIES:
        if policy.package.startswith("contexts."):
            assert "contexts" not in policy.allow, (
                f"{policy.package} grants the `contexts` root, which readmits exactly the "
                f"cross-context coupling ADR-0026 forbids"
            )


def test_evaluation_is_the_one_context_without_kernel_access():
    """ADR-0026 states R5 narrowly, and it is encoded as written rather than widened.

    Recorded as AC-001 in the Issue #13 report: TIS E10 §7 requires an Evaluation to carry its
    own digest and ADR-0005 reserves minting to the kernel, so this rule and those two cannot
    all hold. Encoding the frozen text and reporting the contradiction is the correct
    handling; quietly adding `kernel` here would be weakening a gate to fit an unwritten need.
    """
    from tools.gates.imports import POLICIES

    without_kernel = {
        p.package for p in POLICIES
        if p.package.startswith("contexts.") and "kernel" not in p.allow
    }
    assert without_kernel == {"contexts.evaluation"}


def test_every_context_directory_has_a_policy():
    """A seventh context added without a policy would be governed by nothing.

    `undeclared` locates packages by `__init__.py`; no context directory has one, so this is
    the only thing standing between a new context and no rules at all.
    """
    from tools.gates.imports import POLICIES

    on_disk = {
        d.name for d in CONTEXTS.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_"))
    }
    declared = {
        p.package.split(".", 1)[1] for p in POLICIES if p.package.startswith("contexts.")
    }
    assert on_disk == declared, f"contexts without a policy: {sorted(on_disk - declared)}"
    assert on_disk == set(CONTEXT_NAMES)


def test_every_rule_cites_a_decision():
    """A rule that cannot name its ADR is a preference (STD-11)."""
    for name, _, citation in CONTEXT_RULES:
        assert "ADR-" in citation or "TIS" in citation, f"{name} cites {citation!r}"


# ═══════════════════════════════════════════ the six rules accept what they should


@pytest.mark.parametrize("name, allow, citation", CONTEXT_RULES, ids=CONTEXT_NAMES)
def test_a_context_may_import_exactly_what_its_rule_grants(tmp_path, name, allow, citation):
    """The positive half. A rule set that rejected everything would pass all six violation
    tests below and be useless, so each grant is exercised as well as each prohibition."""
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    body = "import sys\n" + "".join(f"import {root}\n" for root in sorted(allow))
    package(tmp_path, f"contexts.{name}", work=body)

    report, code = gate.run(
        [policy_for(gate, name, allow), *scaffold_policies(gate, scaffolded)]
    )
    assert code == 0, report.violations


@pytest.mark.parametrize("name, allow, citation", CONTEXT_RULES, ids=CONTEXT_NAMES)
def test_a_context_may_import_its_own_submodules(tmp_path, name, allow, citation):
    """Self-import is permitted, and is matched on the dotted package rather than the root.

    This is the case the tightening in `check` had to keep working while making
    cross-context imports visible: `contexts.ingest.parsers` is `contexts.ingest` importing
    itself, and `contexts.ingest` importing `contexts.curation` is not.
    """
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(
        tmp_path, f"contexts.{name}",
        adapters="",
        work=f"from contexts.{name}.adapters import thing\nfrom . import adapters\n",
    )

    report, code = gate.run(
        [policy_for(gate, name, allow), *scaffold_policies(gate, scaffolded)]
    )
    assert code == 0, report.violations


# ═══════════════════════════════════════════ THE SIX DELIBERATE VIOLATIONS


@pytest.mark.parametrize("name, allow, citation", CONTEXT_RULES, ids=CONTEXT_NAMES)
def test_a_context_may_not_import_another_context(tmp_path, name, allow, citation):
    """ADR-0026 rule 5 — the six deliberate-violation cases §15 row 13 requires.

    Each context is given a module importing a *different* context and the analyser must
    report it. Before M2/E4/#13 tightened the self-match from `policy.root` to the dotted
    package, every one of these passed silently: `contexts` was the root of both sides.
    """
    other = next(n for n in CONTEXT_NAMES if n != name)
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, f"contexts.{other}")
    package(tmp_path, f"contexts.{name}", work=f"import contexts.{other}.engine\n")

    report, code = gate.run([
        policy_for(gate, name, allow),
        policy_for(gate, other, allow, populated=False),
        *scaffold_policies(gate, scaffolded),
    ])
    assert code == 1, f"contexts.{name} was permitted to import contexts.{other}"
    # Asserted on the specific violation, not merely on the exit code: a non-zero exit for
    # an unrelated reason would let this test pass while the rule did nothing.
    assert any(
        f"contexts.{other}" in v and "not permitted" in v for v in report.violations
    ), report.violations


@pytest.mark.parametrize("name, allow, citation", CONTEXT_RULES, ids=CONTEXT_NAMES)
def test_the_from_form_of_a_cross_context_import_is_caught_too(tmp_path, name, allow, citation):
    """A rule evadable by changing import syntax would not be a rule."""
    other = next(n for n in CONTEXT_NAMES if n != name)
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, f"contexts.{other}")
    package(tmp_path, f"contexts.{name}", work=f"from contexts.{other}.engine import run\n")

    report, code = gate.run([
        policy_for(gate, name, allow),
        policy_for(gate, other, allow, populated=False),
        *scaffold_policies(gate, scaffolded),
    ])
    assert code == 1, report.violations
    assert any(
        f"contexts.{other}" in v and "not permitted" in v for v in report.violations
    ), report.violations


def test_evaluation_may_not_import_the_method_context(tmp_path):
    """The named case in ADR-0026's table: "never imports a method".

    The engine executes a *released artifact* through the wire format (ADR-0016). Importing
    the method context would let a first-party method bypass the interface every third-party
    method must use, and the benchmark would stop measuring the same thing for both.
    """
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, "contexts.method", detector="")
    package(tmp_path, "contexts.evaluation",
            engine="from contexts.method.detector import Threshold\n")

    report, code = gate.run([
        policy_for(gate, "evaluation", frozenset({"contracts", "domain"})),
        policy_for(gate, "method", frozenset({"contracts", "domain", "kernel"})),
        *scaffold_policies(gate, scaffolded),
    ])
    assert code == 1, "the evaluation engine was permitted to import a method"
    assert any(
        "contexts.method" in v and "not permitted" in v for v in report.violations
    ), report.violations


def test_groundtruth_may_not_import_curation(tmp_path):
    """contexts/groundtruth/README: merging into contexts/curation is forbidden.

    Labels come from a different authority on a different revision cadence; conflating them
    makes historical scores silently unreproducible (ADR-0007).
    """
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, "contexts.curation", freeze="")
    package(tmp_path, "contexts.groundtruth", events="import contexts.curation.freeze\n")

    allow = frozenset({"contracts", "domain", "kernel"})
    report, code = gate.run([
        policy_for(gate, "groundtruth", allow),
        policy_for(gate, "curation", allow),
        *scaffold_policies(gate, scaffolded),
    ])
    assert code == 1, report.violations
    assert any(
        "contexts.curation" in v and "not permitted" in v for v in report.violations
    ), report.violations


def test_evaluation_may_not_import_the_kernel(tmp_path):
    """R5 encoded as ADR-0026 writes it. See AC-001 — reported, not resolved here."""
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, "contexts.evaluation", engine="import kernel.provenance\n")

    report, code = gate.run([
        policy_for(gate, "evaluation", frozenset({"contracts", "domain"})),
        *scaffold_policies(gate, scaffolded),
    ])
    assert code == 1, report.violations
    assert any(
        "kernel" in v and "not permitted" in v for v in report.violations
    ), report.violations


@pytest.mark.parametrize("name, allow, citation", CONTEXT_RULES, ids=CONTEXT_NAMES)
def test_no_context_may_import_an_ungranted_third_party(tmp_path, name, allow, citation):
    """ADR-0026 grants no blanket third-party permission, so none is inherited.

    A context needing `astropy` adds one reviewable line to its policy. That is deliberate:
    the alternative is a permission nobody decided to give (STD-11).
    """
    gate = load_gate(tmp_path)
    scaffolded = scaffold(tmp_path)
    package(tmp_path, f"contexts.{name}", work="import astropy.io.fits\n")

    report, code = gate.run(
        [policy_for(gate, name, allow), *scaffold_policies(gate, scaffolded)]
    )
    assert code == 1, report.violations
    assert any("astropy" in v for v in report.violations), report.violations


# ═══════════════════════════════════════════ the rules bind when code arrives


@pytest.mark.parametrize("name", CONTEXT_NAMES)
def test_a_new_module_in_an_empty_context_turns_the_gate_red(tmp_path, name):
    """`populated=False` is a live assertion, not a placeholder.

    This is what makes six rules over six empty directories more than decoration: the first
    `.py` file added to any context fails the gate until that issue states what its context
    may import.
    """
    gate = load_gate(tmp_path)
    package(tmp_path, f"contexts.{name}", work="import sys\n")

    report, code = gate.run([policy_for(gate, name, frozenset(), populated=False)])
    assert code == 1, f"a module appeared in contexts.{name} and the gate stayed green"
    assert any("declared unpopulated" in v for v in report.violations), report.violations


@pytest.mark.parametrize("name", CONTEXT_NAMES)
def test_an_empty_context_declaring_itself_populated_is_a_failure(tmp_path, name):
    """The converse. A scan over nothing passes while checking nothing (STD-07)."""
    gate = load_gate(tmp_path)
    (tmp_path / "contexts" / name).mkdir(parents=True)

    report, code = gate.run([policy_for(gate, name, frozenset(), populated=True)])
    assert code == 1, report.violations
    assert any("no runtime module" in v for v in report.violations), report.violations


def test_the_six_contexts_are_currently_empty_and_declared_so():
    """States the ground truth this file rests on, so it fails if that changes silently."""
    from tools.gates.imports import POLICIES

    declared = {p.package: p for p in POLICIES}
    for name in CONTEXT_NAMES:
        modules = [
            p for p in (CONTEXTS / name).rglob("*.py") if not p.name.startswith("._")
        ]
        policy = declared[f"contexts.{name}"]
        assert policy.populated is bool(modules), (
            f"contexts.{name} has {len(modules)} module(s) and declares "
            f"populated={policy.populated}"
        )


# ═══════════════════════════════════════════ Evidence writes nothing


#: Callables and attributes by which a module mutates the world. Checked by call site rather
#: than by import, because `pathlib` is legitimately needed to *read* an artifact.
WRITE_CALLS = frozenset({
    "write_text", "write_bytes", "writelines", "write", "mkdir", "touch",
    "unlink", "rmdir", "remove", "rename", "replace", "rmtree", "makedirs",
})


def write_call_sites(source: str, filename: str = "<test>") -> list[str]:
    """Every call in `source` that mutates the filesystem.

    ADR-0026: "Evidence writes nothing." That is not an import rule — Evidence legitimately
    imports `pathlib` to read — so it cannot be expressed in the policy engine and is checked
    here instead. `open(...)` is inspected for a mode argument containing `w`, `a` or `x`,
    because `open(path)` alone is a read.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in WRITE_CALLS:
            found.append(f"{filename}:{node.lineno} .{node.func.attr}()")
        elif isinstance(node.func, ast.Name) and node.func.id == "open":
            mode = ""
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = str(keyword.value.value)
            if any(flag in mode for flag in "wax+"):
                found.append(f"{filename}:{node.lineno} open(mode={mode!r})")
    return found


def test_the_write_scan_detects_every_form_of_write():
    """The deliberate-violation case for the write rule itself.

    A scanner that has only been run over code that does not write is a scanner nobody has
    seen detect anything.
    """
    for source in (
        "from pathlib import Path\nPath('x').write_text('a')\n",
        "from pathlib import Path\nPath('x').mkdir()\n",
        "from pathlib import Path\nPath('x').unlink()\n",
        "import shutil\nshutil.rmtree('x')\n",
        "open('x', 'w')\n",
        "open('x', mode='a')\n",
        "f = open('x', 'wb')\n",
    ):
        assert write_call_sites(source), f"write not detected in: {source!r}"


def test_the_write_scan_permits_reading():
    """Evidence reads from every context. A scanner that flagged reads would be unusable."""
    for source in (
        "from pathlib import Path\nvalue = Path('x').read_text()\n",
        "open('x')\n",
        "open('x', 'r')\n",
        "open('x', mode='rb')\n",
        "import json\ndata = json.loads(open('x').read())\n",
    ):
        assert not write_call_sites(source), f"read wrongly flagged: {source!r}"


def test_evidence_context_writes_nothing():
    """ADR-0026 applied to the real tree. Vacuous today and stated so, but it binds on the
    first module Evidence gains, and E11/#42 is the issue that will add them."""
    offenders: list[str] = []
    for path in sorted((CONTEXTS / "evidence").rglob("*.py")):
        if path.name.startswith("._"):
            continue
        offenders += write_call_sites(path.read_text(), str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"contexts/evidence writes: {offenders}"


def test_the_evidence_write_rule_is_asserted_over_a_known_violation():
    """Pairs with the test above, which currently scans zero files.

    Without this, `test_evidence_context_writes_nothing` would report green over an empty
    directory — indistinguishable from a check that does not work.
    """
    violating = "from pathlib import Path\nPath('out.html').write_text('<p>1</p>')\n"
    assert write_call_sites(violating, "contexts/evidence/render.py")

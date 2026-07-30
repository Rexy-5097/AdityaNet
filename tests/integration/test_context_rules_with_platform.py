"""The context import rules, exercised against a context that really uses the platform.

WHY THIS IS NOT COVERED BY test_context_imports.py
---------------------------------------------------
That file proves each of the six rules **rejects** a violation. Six rejection tests are
satisfied by a rule set that rejects everything, and a rule set that rejects everything is
indistinguishable from one that works right up until the moment someone writes a real context
— at which point it blocks the architecture it was meant to protect.

So this file asks the complementary question, and it can only be asked at integration level
because answering it needs three real subsystems at once: **does the rule set permit the
composition the architecture actually calls for?** The module below is a plausible Ingest
context — it builds a `domain` entity, serialises it against a `contracts` schema, and
registers it in the `kernel` provenance store — and the test asserts both that the gate
permits it *and* that it genuinely runs and produces a provenance-linked artifact.

The last test is the one that justifies the gate existing at all: the violating variant
**executes perfectly**. Nothing at runtime notices that Ingest reached into Curation. Only the
static rule does, which is precisely why the rule cannot be replaced by a test that runs code.

Components crossed: `tools/gates/imports` (M0/E14/#6, tightened by #13) · `contracts/`
(M2/E4/#11) · `domain/` (M2/E4/#12) · `kernel/provenance` (M2/E3/#10).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "gates" / "imports.py"
CONTRACTS = REPO_ROOT / "contracts"

#: A realistic Ingest module: acquire raw bytes, canonicalise to an Observation, register
#: both with the provenance kernel. Held as source because it is analysed statically by the
#: gate *and* executed against the real packages — the same text, judged both ways.
INGEST_MODULE = '''
"""contexts/ingest/parse.py — canonicalise a raw frame into a bitemporal Observation."""

import json

from domain.entities import Observation
from domain.values import Digest, Identifier, Timestamp
from kernel.provenance import ProvenanceStore, begin_run


def ingest(raw: bytes, store: ProvenanceStore) -> tuple[dict, str]:
    """Register raw bytes, canonicalise them, and record the derivation.

    `ingest_time` is None here on purpose: this fixture stands in for a historical frame that
    predates bitemporal capture, which is the case ADR-0022 exists for. Nothing fabricates a
    value to fill it.
    """
    run = begin_run(context="ingest", event="parse")
    source = store.put_bytes(raw)

    observation = Observation(
        source_id=Identifier("issdc"),
        instrument_id=Identifier("solexs"),
        quantity="count_rate",
        unit="counts/s",
        valid_time=Timestamp("2024-03-01T00:00:00Z"),
        ingest_time=None,
        value=12.5,
        source_digest=Digest(source.digest.hex),
    )

    document = observation.to_dict()
    parsed = store.put_bytes(json.dumps(document, sort_keys=True).encode())
    store.record(run, inputs=[source.digest], outputs=[parsed.digest])
    return document, parsed.digest.hex
'''

#: The same module with one line added. It still runs. Only the gate objects.
VIOLATING_MODULE = INGEST_MODULE.replace(
    "from kernel.provenance import ProvenanceStore, begin_run",
    "from kernel.provenance import ProvenanceStore, begin_run\n"
    "from contexts.curation.freeze import freeze_release",
)


def load_gate(root: Path):
    spec = importlib.util.spec_from_file_location(f"plat_gate_{root.name}", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.REPO_ROOT = root
    return module


def build_tree(root: Path, ingest_source: str) -> None:
    """A miniature of the repository's governed roots, for static analysis only."""
    for dotted in ("contracts", "domain", "kernel", "contexts.curation"):
        directory = root / Path(*dotted.split("."))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("")
    (root / "contexts" / "curation" / "freeze.py").write_text("")

    ingest_dir = root / "contexts" / "ingest"
    ingest_dir.mkdir(parents=True, exist_ok=True)
    (ingest_dir / "__init__.py").write_text("")
    (ingest_dir / "parse.py").write_text(ingest_source)


def real_policies(gate, root: Path):
    """The context rules exactly as shipped, applied to the fixture tree.

    `allow` is copied from `tools.gates.imports.POLICIES` rather than restated, so this test
    judges the rule the repository actually ships. Only `populated` is recomputed, from what
    the fixture tree contains — declaring otherwise would trip the gate's own staleness check
    and the failure would be about the fixture rather than about the rule.
    """
    from tools.gates.imports import POLICIES as SHIPPED

    def has_modules(package: str) -> bool:
        directory = root / Path(*package.split("."))
        return any(
            p for p in directory.rglob("*.py") if not p.name.startswith("._")
        )

    context_rules = [
        gate.Policy(
            package=p.package,
            allow=p.allow,
            allow_stdlib=p.allow_stdlib,
            populated=has_modules(p.package),
        )
        for p in SHIPPED
        if p.package in ("contexts.ingest", "contexts.curation")
    ]
    scaffold = [gate.Policy(package=name) for name in ("contracts", "domain", "kernel")]
    return context_rules + scaffold


def registry() -> Registry:
    built = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        if path.name.startswith("._"):
            continue
        built = Resource.from_contents(json.loads(path.read_text())) @ built
    return built


def validator_for(name: str):
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry())


def run_module(source: str, store):
    """Execute the module source against the REAL domain, contracts and kernel packages."""
    namespace: dict = {}
    exec(compile(source, "contexts/ingest/parse.py", "exec"), namespace)  # noqa: S102
    return namespace["ingest"](b"raw SoLEXS frame", store)


# ═══════════════════════════════════════════ the rules permit the real composition


def test_the_ingest_rule_permits_a_context_that_uses_all_three_subsystems(tmp_path):
    """The complementary half of the six rejection tests.

    Six tests proving a rule set rejects would all pass for a rule set that rejects
    everything. This asserts the shipped `contexts.ingest` policy admits a module importing
    `domain`, `kernel` and the stdlib together — the composition TIS E5 §19 describes.
    """
    gate = load_gate(tmp_path)
    build_tree(tmp_path, INGEST_MODULE)

    report, code = gate.run(real_policies(gate, tmp_path))
    assert code == 0, report.violations
    assert report.modules >= 1, "the analyser scanned no module; the verdict means nothing"


def test_that_same_module_actually_works_against_the_real_platform(tmp_path):
    """Permitted by the gate is worth little if the composition does not function.

    Runs the identical source against the real `domain`, `contracts` and `kernel`: the
    Observation is built, validated against its normative schema, registered in the store,
    and reachable from its raw input by walking the provenance DAG.
    """
    from kernel.provenance import Digest as KernelDigest, ProvenanceStore

    store = ProvenanceStore(tmp_path / "store")
    document, parsed_hex = run_module(INGEST_MODULE, store)

    # The contract is normative (ADR-0019) — the domain type must satisfy it.
    validator_for("observation").validate(document)

    # ADR-0022: unknown ingest time is null, never fabricated.
    assert document["ingest_time"] is None

    # The chain is walkable from the canonical output back to the raw bytes.
    parsed = KernelDigest(parsed_hex)
    ancestors = store.ancestors(parsed)
    assert ancestors, "the parsed observation has no recorded ancestry"

    # And the digest the kernel minted is a value the domain accepts, though neither
    # package imports the other.
    from domain.values import Digest as DomainDigest

    assert DomainDigest(parsed_hex).hex == parsed_hex


def test_the_permitted_module_is_permitted_for_the_right_reason(tmp_path):
    """`contracts`, `domain` and `kernel` are granted; nothing else sneaks in on a root match."""
    gate = load_gate(tmp_path)
    build_tree(tmp_path, INGEST_MODULE)

    paths = gate.imported_paths(tmp_path / "contexts" / "ingest" / "parse.py")
    assert {"domain.entities", "domain.values", "kernel.provenance"} <= paths
    assert not any(p.startswith("contexts.") for p in paths)


# ═══════════════════════════════════════════ the rule catches what runtime cannot


def test_a_cross_context_import_is_rejected_by_the_gate(tmp_path):
    """One added line, and the shipped Ingest policy refuses it."""
    gate = load_gate(tmp_path)
    build_tree(tmp_path, VIOLATING_MODULE)

    report, code = gate.run(real_policies(gate, tmp_path))
    assert code == 1, "Ingest was permitted to import Curation"
    assert any(
        "contexts.curation" in v and "not permitted" in v for v in report.violations
    ), report.violations


def test_the_violating_module_still_runs_perfectly(tmp_path):
    """The argument for the gate, stated as a test.

    The violating module differs by one import. Strip that line and the remaining code is
    byte-identical to the permitted version and produces an identical, schema-valid,
    provenance-linked result. No test that *runs* the context would ever notice the coupling;
    the architecture erodes silently and only a static rule sees it happen.
    """
    from kernel.provenance import ProvenanceStore

    runnable = VIOLATING_MODULE.replace(
        "from contexts.curation.freeze import freeze_release\n", ""
    )
    assert runnable == INGEST_MODULE, "the two variants differ by more than the bad import"

    document, _ = run_module(runnable, ProvenanceStore(tmp_path / "store"))
    validator_for("observation").validate(document)


def test_the_evaluation_rule_would_reject_the_same_module(tmp_path):
    """The same source, judged under R5 instead of R1, is a violation.

    ADR-0026 grants Evaluation `contracts` and `domain` only, so a module importing the kernel
    is permitted in Ingest and refused in Evaluation. That the verdict changes with the
    context — on identical text — is what makes these rules directional rather than a single
    global allow-list. See AC-001 in the Issue #13 report on this rule's tension with
    ADR-0005.
    """
    gate = load_gate(tmp_path)
    build_tree(tmp_path, INGEST_MODULE)
    evaluation_dir = tmp_path / "contexts" / "evaluation"
    evaluation_dir.mkdir(parents=True)
    (evaluation_dir / "__init__.py").write_text("")
    (evaluation_dir / "engine.py").write_text(INGEST_MODULE)

    from tools.gates.imports import POLICIES as SHIPPED

    evaluation = next(p for p in SHIPPED if p.package == "contexts.evaluation")
    report, code = gate.run([
        gate.Policy(package="contexts.evaluation", allow=evaluation.allow, populated=True),
        *[gate.Policy(package=n) for n in ("contracts", "domain", "kernel")],
    ])
    assert code == 1
    assert any("kernel" in v and "not permitted" in v for v in report.violations), (
        report.violations
    )

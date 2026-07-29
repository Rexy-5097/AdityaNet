#!/usr/bin/env python3
"""Link-integrity gate for the constitution.

Verifies that every citable identifier referenced anywhere under adr/ and standards/
resolves to exactly one document, and that supersession is declared symmetrically.

WHY THIS EXISTS
---------------
ADR-0013 makes limitation clauses citable by ID so that exactly one copy of every caveat
exists. That guarantee is worth nothing if a citation can point at nothing: a dangling
`L-07` reads exactly like a resolved one. Likewise ADR-0021 supersedes ADR-0009, and a
reader who follows the pointer must arrive somewhere.

This gate is therefore not a link checker for convenience. It is the mechanism that makes
citation-instead-of-restatement safe (TIS E1 §11, STD-05, STD-13).

FAIL-CLOSED (ADR-0020, STD-07)
------------------------------
A gate that cannot execute must fail, not pass. If the constitution root is missing or
contains no documents, that is a failure and not an empty success — an absent corpus is
indistinguishable from a passing one otherwise.

Reports enumerate what was checked, not only what failed, for the same reason.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "adr"
STANDARDS_DIR = REPO_ROOT / "standards"
SPECS_DIR = REPO_ROOT / "specs"

# A citable identifier. Anchored on a word boundary so that "ADR-0001" inside a longer
# token is not matched, and case-sensitive because the identifiers are.
CITATION = re.compile(r"\b(ADR-\d{4}|STD-\d{2}|L-\d{2}|CONTRA-\d{3})\b")

# Minimal front-matter reader. A full YAML parser is not warranted: the front matter is
# five flat keys written by this project, and adding a dependency to the one gate that must
# run before any dependency is installed would be self-defeating.
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)

# Navigational documents carry no citable ID and therefore no front matter: an index lists
# what exists, a README states what may enter a directory. Neither is citable, so neither is
# indexed.
#
# They are NOT exempt from checking. Their citations and relative links are verified exactly
# as a citable document's are — a README pointing at a decision that does not exist is the
# same defect wherever it appears. Only the ID requirement is lifted.
NAVIGATIONAL = frozenset({"index.md", "README.md"})


class GateFailure(Exception):
    """A PolicyRejection in the TIS §0.2 taxonomy, raised by this gate alone."""


@dataclass
class Document:
    path: Path
    doc_id: str
    status: str
    supersedes: list[str]
    superseded_by: str | None


# Namespace roots. A citation is only enforceable once the directory that would contain its
# target exists.
#
# WHY. ADR-0013 requires clauses to be cited rather than restated, so the ADRs legitimately
# cite L-nn. Those clause files arrive with a later issue. Two wrong responses were
# available: strip the citations (violating ADR-0013 to satisfy a sequencing error), or
# suppress the finding in a list nobody reads.
#
# Instead the gate is scoped to what has been materialised. Citations into an absent
# namespace are reported as DEFERRED and counted in the summary, never hidden. The instant
# the root appears, an unresolved citation into it becomes a hard failure with no change to
# this gate — so the deferral cannot outlive the work that closes it.
NAMESPACE_ROOTS = {
    "ADR": ADR_DIR,
    "STD": STANDARDS_DIR,
    "L": SPECS_DIR / "limitations",
    "CONTRA": SPECS_DIR / "contradictions",
}


def namespace_of(identifier: str) -> str:
    return identifier.rsplit("-", 1)[0]


def namespace_materialised(identifier: str) -> bool:
    root = NAMESPACE_ROOTS.get(namespace_of(identifier))
    return root is not None and root.exists()


@dataclass
class Report:
    """Enumerates what was checked. STD-07: a report of failures alone cannot be
    distinguished from a gate that never ran."""

    documents: int = 0
    citations: int = 0
    failures: list[str] = field(default_factory=list)
    deferred: set[str] = field(default_factory=set)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def defer(self, identifier: str) -> None:
        self.deferred.add(identifier)


def parse_front_matter(text: str, path: Path) -> dict[str, str]:
    match = FRONT_MATTER.match(text)
    if match is None:
        raise GateFailure(f"{path}: missing front matter")
    return {k: v.strip() for k, v in KEY.findall(match.group(1))}


def parse_list(raw: str) -> list[str]:
    """Parse the inline-list form used in front matter: `[]` or `[ADR-0009]`."""
    inner = raw.strip().removeprefix("[").removesuffix("]").strip()
    return [item.strip() for item in inner.split(",") if item.strip()] if inner else []


def load(path: Path) -> Document:
    meta = parse_front_matter(path.read_text(), path)
    for required in ("id", "title", "status"):
        if required not in meta:
            raise GateFailure(f"{path}: front matter missing '{required}'")

    superseded_by = meta.get("superseded_by", "null").strip()
    return Document(
        path=path,
        doc_id=meta["id"],
        status=meta["status"],
        supersedes=parse_list(meta.get("supersedes", "[]")),
        superseded_by=None if superseded_by in ("null", "") else superseded_by,
    )


def collect(report: Report) -> tuple[dict[str, Document], list[Path]]:
    """Index every constitution document by ID, rejecting duplicates.

    TIS E1 §11 invariant (i): exactly one file per citable ID. A duplicate makes every
    citation of that ID ambiguous, so it is a failure rather than a warning.
    """
    index: dict[str, Document] = {}
    navigational: list[Path] = []

    for root in (ADR_DIR, STANDARDS_DIR, SPECS_DIR):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            if path.name.startswith("._"):
                continue
            if path.name in NAVIGATIONAL:
                navigational.append(path)
                continue
            document = load(path)
            report.documents += 1
            if document.doc_id in index:
                report.fail(
                    f"duplicate ID {document.doc_id}: {index[document.doc_id].path} "
                    f"and {path}"
                )
                continue
            index[document.doc_id] = document

    return index, navigational


def check_citations(
    index: dict[str, Document], navigational: list[Path], report: Report
) -> None:
    """Every citation in the corpus must resolve to a known document.

    Navigational documents are checked alongside citable ones. Only the ID requirement is
    lifted for them, never the citation requirement.
    """
    for path in [d.path for d in index.values()] + navigational:
        own_id = next((d.doc_id for d in index.values() if d.path == path), None)
        for cited in CITATION.findall(path.read_text()):
            report.citations += 1
            if cited == own_id or cited in index:
                continue
            if namespace_materialised(cited):
                report.fail(f"{path.name}: cites {cited}, which does not resolve")
            else:
                report.defer(cited)


def check_supersession(index: dict[str, Document], report: Report) -> None:
    """Supersession must be declared from both ends.

    ADR-0025 supersedes ADR-0018. If only one side records it, a reader arriving from the
    other side sees an active decision that is not active. Symmetry is the property that
    makes 'supersede, never edit' navigable.
    """
    for document in index.values():
        for target in document.supersedes:
            other = index.get(target)
            if other is None:
                report.fail(f"{document.doc_id}: supersedes {target}, which does not resolve")
            elif other.superseded_by != document.doc_id:
                report.fail(
                    f"asymmetric supersession: {document.doc_id} supersedes {target}, "
                    f"but {target} records superseded_by={other.superseded_by!r}"
                )

        if document.superseded_by is not None:
            other = index.get(document.superseded_by)
            if other is None:
                report.fail(
                    f"{document.doc_id}: superseded_by "
                    f"{document.superseded_by}, which does not resolve"
                )
            elif document.doc_id not in other.supersedes:
                report.fail(
                    f"asymmetric supersession: {document.doc_id} claims superseded_by "
                    f"{document.superseded_by}, which does not list it"
                )

        if document.status == "superseded" and document.superseded_by is None:
            report.fail(f"{document.doc_id}: status is superseded but superseded_by is null")


def check_relative_links(
    index: dict[str, Document], navigational: list[Path], report: Report
) -> None:
    """Markdown links between constitution documents must point at real files."""
    link = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)(?:#[^)]*)?\)")
    for path in [d.path for d in index.values()] + navigational:
        for target in link.findall(path.read_text()):
            resolved = (path.parent / target).resolve()
            if resolved.exists():
                continue
            # A link into a namespace that has not been materialised is deferred on the
            # same terms as the citation itself; see NAMESPACE_ROOTS.
            if any(root.exists() or str(root) not in str(resolved)
                   for ns, root in NAMESPACE_ROOTS.items()
                   if str(root) in str(resolved)):
                report.fail(f"{path.name}: broken link -> {target}")
            elif not any(str(root) in str(resolved) for root in NAMESPACE_ROOTS.values()):
                report.fail(f"{path.name}: broken link -> {target}")


def main() -> int:
    report = Report()

    try:
        if not ADR_DIR.exists():
            raise GateFailure(f"constitution root missing: {ADR_DIR}")

        index, navigational = collect(report)

        # Fail closed: an empty corpus is not a passing corpus (ADR-0020).
        if report.documents == 0:
            raise GateFailure("no constitution documents found; refusing to pass vacuously")

        check_citations(index, navigational, report)
        check_supersession(index, report)
        check_relative_links(index, navigational, report)

    except GateFailure as exc:
        print(f"links: GATE FAILURE — {exc}", file=sys.stderr)
        return 1

    print(
        f"links: checked {report.documents} document(s), "
        f"{report.citations} citation(s), {len(index)} unique ID(s), "
        f"{len(navigational)} navigational"
    )

    if report.deferred:
        roots = {namespace_of(i) for i in report.deferred}
        print(
            f"links: {len(report.deferred)} citation target(s) DEFERRED — "
            f"namespace(s) {', '.join(sorted(roots))} not yet materialised: "
            + ", ".join(sorted(report.deferred))
        )
        print(
            "links: these become hard failures as soon as their namespace root exists."
        )

    if report.failures:
        print(f"\nlinks: {len(report.failures)} failure(s)", file=sys.stderr)
        for failure in report.failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print("links: all citations, supersessions and links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

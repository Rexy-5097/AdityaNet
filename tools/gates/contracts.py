#!/usr/bin/env python3
"""Contract gate: schema validity, and additive-only evolution within a major version.

STD-09 and E4 invariant (iii): within a major version, contract changes are additive only.
Removals and semantic changes require a new major version.

WHY THIS IS A GATE AND NOT A REVIEW NOTE
----------------------------------------
A contract is the only vocabulary that crosses a context boundary (ADR-0019). Narrowing one
without bumping its major version breaks every producer that was conforming yesterday, and
does so silently — the producer keeps emitting what it always emitted and the consumer
starts rejecting it. Nobody reviewing a one-line schema diff reliably notices that
`minItems: 0` became `minItems: 1`.

WHAT COUNTS AS BREAKING
-----------------------
Anything that makes a previously-valid document invalid:

  - removing a property another party may be sending
  - adding a required property
  - narrowing a type, enum, pattern, or numeric bound
  - closing an object that previously accepted extensions

Adding an optional property is additive. Widening a bound is additive. Documentation is
never breaking, so `description` and `title` are ignored entirely — a gate that failed on
prose would be one people learn to bypass.

THE BASELINE
------------
The previous version of each schema on the default branch, read through git. Comparing
against the merge base rather than a stored copy means the baseline cannot drift from what
is actually published, and there is no second artifact to keep in step.

FAIL-CLOSED (ADR-0020, STD-07)
------------------------------
A schema that does not parse, a `$id` that does not match its filename, or a contracts
directory that has become empty are all failures. An empty scan reports success while
checking nothing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
BASELINE_REF = "origin/main"

ID_PATTERN = re.compile(r"^urn:adityanet:contract:([a-z-]+):(\d+)$")

# Keys that carry documentation rather than constraint. Changing one can never invalidate a
# document, so the gate ignores them outright.
PROSE_KEYS = frozenset({"description", "title", "$comment", "examples", "default"})


class GateFailure(Exception):
    """A PolicyRejection in the TIS §0.2 taxonomy."""


@dataclass
class Report:
    schemas: int = 0
    compared: int = 0
    failures: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failures.append(message)


def schema_paths() -> list[Path]:
    if not CONTRACTS.is_dir():
        raise GateFailure(f"contracts directory missing: {CONTRACTS}")
    found = sorted(
        p for p in CONTRACTS.glob("*.schema.json") if not p.name.startswith("._")
    )
    if not found:
        raise GateFailure("no contracts found; refusing to pass vacuously")
    return found


def load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise GateFailure(f"{path.name}: not valid JSON — {exc}") from exc


def check_identity(path: Path, schema: dict[str, Any], report: Report) -> None:
    """A `$id` must exist, be well formed, and name its own file.

    An identifier that disagrees with its filename is how two schemas end up believed to be
    one contract.
    """
    schema_id = schema.get("$id")
    if not schema_id:
        report.fail(f"{path.name}: no $id")
        return

    match = ID_PATTERN.match(schema_id)
    if match is None:
        report.fail(f"{path.name}: $id {schema_id!r} is not urn:adityanet:contract:<name>:<major>")
        return

    expected = path.name.removesuffix(".schema.json")
    if match.group(1) != expected:
        report.fail(f"{path.name}: $id names {match.group(1)!r}, file names {expected!r}")

    if "$schema" not in schema:
        report.fail(f"{path.name}: no $schema dialect declared")


def git_show(ref: str, relative: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{ref}:{relative}"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def walk(node: Any, trail: str = "") -> dict[str, Any]:
    """Flatten a schema to path -> constraint, dropping prose."""
    flat: dict[str, Any] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if key in PROSE_KEYS:
                continue
            here = f"{trail}/{key}"
            if isinstance(value, (dict, list)):
                flat.update(walk(value, here))
            else:
                flat[here] = value
    elif isinstance(node, list):
        for index, value in enumerate(node):
            here = f"{trail}/{index}"
            # Scalars inside lists must be captured, not recursed into. An earlier version
            # recursed unconditionally, so `enum` members, `required` names and union
            # `type` arrays were dropped from the flattened form entirely — which silently
            # disabled the enum-removal and added-required-field checks. Found by the
            # synthetic-baseline tests; the real corpus could not have shown it, because
            # every contract here is new and nothing was compared.
            if isinstance(value, (dict, list)):
                flat.update(walk(value, here))
            else:
                flat[here] = value
    return flat


# Constraints whose tightening makes a previously-valid document invalid.
_NARROWING_NUMERIC = {
    "minLength": lambda old, new: new > old,
    "minItems": lambda old, new: new > old,
    "minProperties": lambda old, new: new > old,
    "minimum": lambda old, new: new > old,
    "exclusiveMinimum": lambda old, new: new > old,
    "maxLength": lambda old, new: new < old,
    "maxItems": lambda old, new: new < old,
    "maximum": lambda old, new: new < old,
    "exclusiveMaximum": lambda old, new: new < old,
}


def required_sets(schema: Any, trail: str = "") -> dict[str, set[str]]:
    """Map each container path to the set of field names it requires."""
    found: dict[str, set[str]] = {}
    if isinstance(schema, dict):
        if isinstance(schema.get("required"), list):
            found[trail] = {r for r in schema["required"] if isinstance(r, str)}
        for key, value in schema.items():
            found.update(required_sets(value, f"{trail}/{key}"))
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            found.update(required_sets(value, f"{trail}/{index}"))
    return found


def compare(name: str, old: dict[str, Any], new: dict[str, Any], report: Report) -> None:
    """Report every change that could invalidate a previously-valid document."""
    if old.get("$id") != new.get("$id"):
        # A changed major version is the sanctioned route for a breaking change, so the
        # comparison does not apply.
        return

    report.compared += 1
    old_flat, new_flat = walk(old), walk(new)

    for pointer, was in old_flat.items():
        key = pointer.rsplit("/", 1)[-1]
        now = new_flat.get(pointer)

        if pointer not in new_flat:
            # `enum` and `required` members have dedicated checks below, which report in
            # the vocabulary of the schema rather than as a lost array index.
            if "/enum/" in pointer or "/required/" in pointer:
                continue
            if "/properties/" in pointer and pointer.count("/") >= 2:
                report.fail(f"{name}: removed {pointer} — breaking without a major bump")
            continue

        if key in _NARROWING_NUMERIC and isinstance(was, (int, float)):
            if _NARROWING_NUMERIC[key](was, now):
                report.fail(f"{name}: narrowed {pointer} from {was} to {now}")

        elif key == "type" and was != now:
            report.fail(f"{name}: changed {pointer} from {was!r} to {now!r}")

        elif key == "pattern" and was != now:
            report.fail(f"{name}: changed {pointer} — a pattern change can invalidate values")

        elif key == "additionalProperties" and was is True and now is False:
            report.fail(f"{name}: closed {pointer} — previously accepted extensions")

    # A newly-required property invalidates every document that omitted it.
    #
    # Computed from the schema tree rather than from flattened pointers: an earlier version
    # derived the container path by string-splitting a pointer, which produced "//required/"
    # at the document root and so never matched anything. Comparing name sets per container
    # is correct by construction and cannot be defeated by a path-joining slip.
    old_required, new_required = required_sets(old), required_sets(new)
    for container, now_required in new_required.items():
        added = now_required - old_required.get(container, set())
        if added and container in old_required:
            for field in sorted(added):
                report.fail(
                    f"{name}: added required field {field!r} at {container or '/'} — "
                    f"invalidates every document that omitted it"
                )

    # An enum may gain members; losing one invalidates documents using it.
    for pointer, was in old_flat.items():
        if "/enum/" in pointer and was not in new_flat.values():
            report.fail(f"{name}: removed enum value {was!r} from {pointer.split('/enum/')[0]}")


def main() -> int:
    report = Report()

    try:
        paths = schema_paths()
        for path in paths:
            schema = load(path)
            report.schemas += 1
            check_identity(path, schema, report)

            relative = path.relative_to(REPO_ROOT).as_posix()
            previous = git_show(BASELINE_REF, relative)
            if previous is None:
                continue  # new contract; nothing to compare against
            compare(path.name, json.loads(previous), schema, report)

    except GateFailure as exc:
        print(f"contracts: GATE FAILURE — {exc}", file=sys.stderr)
        return 1

    print(
        f"contracts: checked {report.schemas} schema(s), "
        f"{report.compared} compared against {BASELINE_REF}"
    )

    if report.failures:
        print(f"\ncontracts: {len(report.failures)} violation(s)", file=sys.stderr)
        for failure in report.failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    if report.compared == 0:
        # Honest reporting. Every contract is new relative to the baseline, so the
        # additive-only comparison ran against nothing. Claiming "every change is additive"
        # here would be a gate asserting a property it did not check.
        print(
            f"contracts: identifiers well formed. No baseline on {BASELINE_REF} for any "
            f"contract, so the additive-only comparison was not exercised."
        )
    else:
        print(
            "contracts: all identifiers well formed; every change additive within its major."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

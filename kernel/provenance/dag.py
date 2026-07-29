"""Provenance graph traversal.

Pure functions over an already-loaded set of records. They perform no I/O, so the traversal
logic is testable without a store and the store is testable without re-testing traversal.

WHY CYCLES ARE REJECTED RATHER THAN TOLERATED. A cycle means an artifact is among its own
ancestors, which makes "where did this come from" non-terminating and the audit chain of
VVMP §7 unwalkable. It is not a performance concern; it is a soundness concern.
"""

from __future__ import annotations

from collections.abc import Iterable

from kernel.provenance.digest import Digest
from kernel.provenance.record import ProvenanceRecord


def producers(records: Iterable[ProvenanceRecord]) -> dict[Digest, ProvenanceRecord]:
    """Index each output digest to the record that produced it.

    An output may be produced by at most one record. Two records claiming to have produced
    the same bytes is not a conflict — content addressing means they produced identical
    bytes — but the graph keeps the first, because ancestry is then stable under iteration
    order.
    """
    index: dict[Digest, ProvenanceRecord] = {}
    for record in records:
        for output in record.outputs:
            index.setdefault(output, record)
    return index


def ancestors(digest: Digest, records: Iterable[ProvenanceRecord]) -> frozenset[Digest]:
    """Every digest reachable upstream of `digest`, exclusive of itself.

    Breadth-first with an explicit visited set, so a malformed graph containing a cycle
    terminates here rather than recursing forever. `record()` rejects cycles at write time;
    this is the second line, for a store that was corrupted or hand-edited.
    """
    index = producers(records)
    seen: set[Digest] = set()
    frontier = [digest]

    while frontier:
        current = frontier.pop()
        record = index.get(current)
        if record is None:
            continue
        for parent in record.inputs:
            if parent not in seen:
                seen.add(parent)
                frontier.append(parent)

    return frozenset(seen)


def would_create_cycle(
    inputs: Iterable[Digest],
    outputs: Iterable[Digest],
    records: Iterable[ProvenanceRecord],
) -> bool:
    """True if recording these inputs and outputs would close a cycle.

    Two ways that happens: a digest appears on both sides of the same record, or an output
    is already an ancestor of one of the inputs.
    """
    input_set = set(inputs)
    output_set = set(outputs)
    if input_set & output_set:
        return True

    materialised = list(records)
    for candidate in input_set:
        upstream = ancestors(candidate, materialised)
        if output_set & (upstream | {candidate}):
            return True
    return False

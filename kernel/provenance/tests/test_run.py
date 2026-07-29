"""Run — execution identity and its two-state lifecycle.

A Run is the only object in this package that reads a clock. The tests assert what that is
allowed to buy — uniqueness and ordering — and never a specific timestamp, because a test
that pinned a timestamp would be asserting the clock rather than the code.
"""

from __future__ import annotations

import re

import pytest

from kernel.provenance.errors import ProvenanceFailure
from kernel.provenance.run import Run, RunStatus, begin_run, new_run_id

CROCKFORD = re.compile(r"\A[0-9ABCDEFGHJKMNPQRSTVWXYZ]{26}\Z")


# ── Identifier ──────────────────────────────────────────────────────────────────

def test_run_id_is_a_26_character_crockford_ulid():
    assert CROCKFORD.match(new_run_id())


def test_run_id_excludes_ambiguous_letters():
    """Crockford drops I, L, O and U so a transcribed identifier cannot be misread."""
    ids = "".join(new_run_id() for _ in range(200))
    assert not set("ILOU") & set(ids)


def test_run_ids_are_unique():
    minted = [new_run_id() for _ in range(5000)]
    assert len(set(minted)) == len(minted)


def test_run_ids_sort_lexicographically_in_creation_order():
    """The property that makes a directory listing of runs chronological without parsing
    anything. Within one millisecond the random component is incremented rather than
    redrawn, so ordering survives a fast loop."""
    minted = [new_run_id() for _ in range(5000)]
    assert minted == sorted(minted)


# ── Lifecycle ───────────────────────────────────────────────────────────────────

def test_begin_run_starts_in_the_started_state():
    run = begin_run("provenance", "test")
    assert run.status is RunStatus.STARTED
    assert not run.is_terminal
    assert run.ended_ms is None


@pytest.mark.parametrize("status", [RunStatus.OK, RunStatus.FAILED])
def test_run_ends_in_a_terminal_state(status: RunStatus):
    ended = begin_run("provenance", "test").end(status)
    assert ended.status is status
    assert ended.is_terminal
    assert ended.ended_ms is not None


def test_end_returns_a_new_run_and_does_not_mutate_the_original():
    run = begin_run("provenance", "test")
    ended = run.end(RunStatus.OK)
    assert run.status is RunStatus.STARTED
    assert ended is not run
    assert ended.run_id == run.run_id


def test_run_is_frozen():
    run = begin_run("provenance", "test")
    with pytest.raises(AttributeError):
        run.status = RunStatus.OK  # type: ignore[misc]


# ── Deliberate violations ───────────────────────────────────────────────────────

def test_a_terminal_run_cannot_be_ended_again():
    """Ending twice means a caller believes it owns a run it does not; allowing it would
    record two outcomes for one execution."""
    ended = begin_run("provenance", "test").end(RunStatus.OK)
    with pytest.raises(ProvenanceFailure, match="already ended"):
        ended.end(RunStatus.FAILED)


def test_a_run_cannot_end_in_the_started_state():
    run = begin_run("provenance", "test")
    with pytest.raises(ProvenanceFailure, match="cannot end in the started state"):
        run.end(RunStatus.STARTED)


@pytest.mark.parametrize("bad_id", ["", "short", "X" * 25, "X" * 27])
def test_malformed_run_id_is_rejected(bad_id: str):
    with pytest.raises(ValueError, match="26 characters"):
        Run(run_id=bad_id, context="c", event="e",
            status=RunStatus.STARTED, started_ms=0)


@pytest.mark.parametrize("context,event", [("", "e"), ("c", ""), ("", "")])
def test_a_run_must_name_its_context_and_event(context: str, event: str):
    """An unattributed run makes a provenance record unattributable (STD-14)."""
    with pytest.raises(ValueError, match="context and event"):
        Run(run_id=new_run_id(), context=context, event=event,
            status=RunStatus.STARTED, started_ms=0)

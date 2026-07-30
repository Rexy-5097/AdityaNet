"""The v1 recovery tag.

Issue #7 (M1/E2) exists so that Issue #9 can delete ~22,900 LOC without keeping an
`archive/` directory in the tree. That trade is only sound if recovery actually works, so
the test is not "a tag exists" but "the tag restores the code".

ISOLATION. Restoration is exercised against a throwaway index and a temporary work tree, so
a test that proves `git checkout <tag> -- <path>` works cannot itself dirty the repository
it is testing. A test that leaves the working tree modified is a test that will eventually
be run with `-x` and leave someone confused.

FAIL, DO NOT SKIP. STD-12 permits skipping when the real archive is absent. The tag is not
the archive: it is a repository ref that must travel with a clone, and a suite that skipped
when it was missing would report green in precisely the situation the tag was created to
prevent. The CI job therefore fetches tags, and absence is a failure.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TAG = "v1-surya-final"

# Paths the tag must be able to restore. Each is v1 code that Issue #9 removes, chosen to
# span the three areas named in the tag message.
RESTORABLE = (
    "research/app/main.py",
    "research/app/api/v1/api.py",
    "research/app/services/ml/policy.py",
)


def git(*args: str, **kwargs) -> subprocess.CompletedProcess[str]:
    """Run git in the repository, capturing output.

    stderr is captured rather than inherited because this repository sits on a filesystem
    that makes git emit AppleDouble index warnings on every invocation; letting them through
    would bury a real error in noise.
    """
    return subprocess.run(
        ["git", *args],
        cwd=kwargs.pop("cwd", REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        **kwargs,
    )


@pytest.fixture(scope="module")
def tag_present() -> None:
    result = git("rev-parse", "--verify", f"{TAG}^{{tag}}")
    if result.returncode != 0:
        pytest.fail(
            f"tag '{TAG}' is not present. It is a repository ref, not optional local "
            f"state: fetch tags (`git fetch --tags`) or the recovery guarantee that "
            f"justifies deleting the v1 generation does not exist here."
        )


# ── The tag itself ──────────────────────────────────────────────────────────────

def test_tag_exists(tag_present):
    assert git("rev-parse", "--verify", TAG).returncode == 0


def test_tag_is_annotated_not_lightweight(tag_present):
    """A lightweight tag carries no message, so it could not hold the retrieval command the
    acceptance criterion requires."""
    kind = git("cat-file", "-t", TAG).stdout.strip()
    assert kind == "tag", f"{TAG} is a {kind}, not an annotated tag object"


def test_tag_message_contains_the_retrieval_command(tag_present):
    """The acceptance criterion. Someone who finds this tag in five years must not have to
    work out how to use it."""
    message = git("tag", "-l", "--format=%(contents)", TAG).stdout
    assert f"git checkout {TAG} -- " in message, "no restore command in the tag message"
    assert f"git show {TAG}:" in message, "no inspection command in the tag message"


def test_tag_message_records_why_v1_was_removed(tag_present):
    """A recovery tag whose message omits why the code was abandoned invites someone to
    restore it and use it."""
    message = git("tag", "-l", "--format=%(contents)", TAG).stdout.lower()
    for required in ("synthetic", "goes", "void"):
        assert required in message, f"tag message does not mention '{required}'"


def test_tag_points_at_a_commit_where_v1_is_present(tag_present):
    """'Pre-deletion HEAD' — the whole point. A tag placed after the deletion would restore
    nothing."""
    listing = git("ls-tree", "-r", "--name-only", TAG, "research/app/services").stdout
    assert listing.strip(), "the tagged commit contains no v1 services"
    assert len(listing.splitlines()) >= 30


# ── Restoration ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", RESTORABLE)
def test_git_show_retrieves_file_content(tag_present, path: str):
    """The read-only half: inspect without touching anything."""
    result = git("show", f"{TAG}:{path}")
    assert result.returncode == 0, f"cannot read {path} at {TAG}: {result.stderr.strip()}"
    assert result.stdout.strip(), f"{path} is empty at {TAG}"


@pytest.mark.parametrize("path", RESTORABLE)
def test_checkout_restores_the_file(tag_present, tmp_path, path: str):
    """The acceptance criterion, executed.

    `GIT_INDEX_FILE` and `--work-tree` redirect the operation entirely into tmp_path, so the
    real index and working tree are untouched. Restoring only the requested path also keeps
    this fast — a full worktree checkout of the tagged commit would materialise ~4,400 files
    to prove something about one.
    """
    env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "index")}
    result = git("--work-tree", str(tmp_path), "checkout", TAG, "--", path, env=env)

    assert result.returncode == 0, f"restore failed: {result.stderr.strip()}"

    restored = tmp_path / path
    assert restored.is_file(), f"{path} was not written to the work tree"
    assert restored.read_text() == git("show", f"{TAG}:{path}").stdout


def test_restoration_leaves_the_repository_clean(tag_present, tmp_path):
    """Guards the isolation above. If this test ever fails, the previous ones were dirtying
    the tree while claiming to prove recovery."""
    before = git("status", "--porcelain").stdout

    env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "index")}
    git("--work-tree", str(tmp_path), "checkout", TAG, "--", RESTORABLE[0], env=env)

    assert git("status", "--porcelain").stdout == before


def test_a_path_absent_from_the_tag_fails_loudly(tag_present, tmp_path):
    """Deliberate violation: restoration reports failure rather than silently producing
    nothing, so a typo'd path cannot look like a successful recovery."""
    env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "index")}
    result = git(
        "--work-tree", str(tmp_path), "checkout", TAG, "--",
        "research/app/services/does_not_exist.py", env=env,
    )
    assert result.returncode != 0
    assert not (tmp_path / "research").exists()


# ── The guarantee that makes deletion safe ──────────────────────────────────────

def test_every_path_issue_9_will_delete_is_recoverable(tag_present):
    """The load-bearing assertion.

    Issue #9 removes research/app/api, research/app/main.py and research/app/services. This
    asserts every one of those tracked files is readable at the tag — so the deletion is
    reversible in full, not just for the three sampled paths above.
    """
    doomed = git(
        "ls-tree", "-r", "--name-only", TAG,
        "research/app/api", "research/app/main.py", "research/app/services",
    ).stdout.split()

    assert len(doomed) >= 40, f"expected the v1 core, found {len(doomed)} files"

    unreadable = [p for p in doomed if git("cat-file", "-e", f"{TAG}:{p}").returncode != 0]
    assert not unreadable, f"not recoverable from the tag: {unreadable}"

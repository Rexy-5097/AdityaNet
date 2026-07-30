"""Salvage provenance claims are true, not merely present.

`test_salvage_corpus.py` asserts that each document *declares* a source tag and source
paths. That is a check on the document. This is the check on the claim: every declared path
must actually exist at the declared tag.

A provenance statement nobody verified is the failure mode this whole project is built to
refuse. A salvage document naming a path that was never there — or that moved before the tag
was cut — would send a future reader to nothing, and they would have no way to tell whether
the code or the record was wrong.

Runs in the integration job because it needs the tag, which is a repository ref rather than
a file (see M1/E2/#7).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SALVAGE = REPO_ROOT / "specs" / "salvage"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def meta_of(path: Path) -> dict[str, str]:
    match = FRONT_MATTER.match(path.read_text())
    assert match is not None, f"{path.name}: missing front matter"
    return dict(KEY.findall(match.group(1)))


def salvage_paths() -> list[Path]:
    return sorted(p for p in SALVAGE.glob("SALVAGE-*.md") if not p.name.startswith("._"))


def declared_sources(path: Path) -> list[str]:
    return [s.strip() for s in meta_of(path)["source_paths"].split(",") if s.strip()]


@pytest.fixture(scope="module")
def tag_present() -> None:
    if git("rev-parse", "--verify", "v1-surya-final^{tag}").returncode != 0:
        pytest.fail(
            "tag 'v1-surya-final' is absent, so no salvage provenance claim can be "
            "verified. Fetch tags."
        )


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_every_declared_source_exists_at_the_tag(tag_present, path: Path):
    tag = meta_of(path)["source_tag"]
    for source in declared_sources(path):
        listing = git("ls-tree", "-r", "--name-only", tag, source.rstrip("/"))
        assert listing.returncode == 0 and listing.stdout.strip(), (
            f"{path.stem} claims provenance from '{source}' at {tag}, "
            f"but nothing is there. The claim is false."
        )


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_declared_line_count_matches_the_tagged_source(tag_present, path: Path):
    """The LOC figure is a measurement, so it must match. STD-20 forbids publishing a number
    nobody checked, and a salvage document is published prose."""
    meta = meta_of(path)
    declared = int(meta["source_loc"])
    tag = meta["source_tag"]

    actual = 0
    for source in declared_sources(path):
        files = git("ls-tree", "-r", "--name-only", tag, source.rstrip("/")).stdout.split()
        for tracked in files:
            if tracked.endswith(".py"):
                actual += len(git("show", f"{tag}:{tracked}").stdout.splitlines())

    assert actual == declared, (
        f"{path.stem} declares source_loc={declared} but the tagged source is "
        f"{actual} lines. A published figure must match what it measures."
    )


@pytest.mark.parametrize("path", salvage_paths(), ids=lambda p: p.stem)
def test_retrieval_commands_in_the_prose_actually_resolve(tag_present, path: Path):
    """Every `git show <tag>:<path>` printed in the document is executed. A retrieval command
    that does not work is worse than none: it looks like a guarantee."""
    commands = re.findall(r"git show (v1-surya-final):(\S+)", path.read_text())
    assert commands, f"{path.stem} prints no retrieval command"

    for tag, target in commands:
        assert git("cat-file", "-e", f"{tag}:{target}").returncode == 0, (
            f"{path.stem} prints `git show {tag}:{target}`, which fails"
        )


def test_the_salvaged_paths_are_the_ones_issue_9_deletes(tag_present):
    """Salvage must cover what is being removed. A document salvaging code that survives is
    not salvage, and code removed with nothing salvaged is knowledge lost silently."""
    doomed = set(
        git("ls-tree", "-r", "--name-only", "v1-surya-final",
            "research/app/services/ingestion", "research/app/services/backfill",
            "research/app/services/ml/features_v4/framework.py",
            "research/app/services/ml/policy.py").stdout.split()
    )
    assert doomed, "expected the salvaged v1 paths to exist at the tag"

    covered: set[str] = set()
    for path in salvage_paths():
        for source in declared_sources(path):
            covered.update(
                git("ls-tree", "-r", "--name-only", "v1-surya-final",
                    source.rstrip("/")).stdout.split()
            )

    assert doomed <= covered, f"removed but not salvaged: {sorted(doomed - covered)}"

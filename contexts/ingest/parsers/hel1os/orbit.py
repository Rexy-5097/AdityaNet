"""Orbit identity and version precedence — `SPEC-parsers@r7` §4.

§4 is titled *"Version-Selection Policy (HEL1OS) — **naive ingestion made impossible**"*, and
the reason is measured rather than hypothetical: 46 overlapping orbit pairs exist, and their
`evt.fits` SHA-256 values **differ**, so they are genuine reprocessings rather than byte
copies. Deduplicating by content hash would silently keep both.

IDENTIFICATION
--------------
`HLS_(?P<date>\\d{8})_(?P<start>\\d{6})_(?P<dur>\\d+)sec_lev1_V(?P<ver>\\d{3})`

`OBSERVED` distribution: V111 ×371, V211 ×16, V112 ×3, V311 ×1 — re-measured against the
archive by `test_the_version_distribution_matches_the_specification`, which found exactly
those counts across 391 orbits.

**The three digits are undocumented in the archive and are treated as opaque** (§8 A-1).
Nothing here decodes them into major/minor/patch, because inventing that decomposition would
make V112 > V211 or the reverse depending on a reading nobody has authority for. They compare
as one integer, which is what §4 specifies.

PRECEDENCE, DETERMINISTIC, IN ORDER
-----------------------------------
1. Higher `ver` integer wins.
2. Tie → longer `dur` wins (more coverage).
3. Tie → later header `DATE` (processing date) wins.
4. Still tied → **F-14 terminate. Never coin-flip.**

WHAT THIS MODULE DELIBERATELY DOES NOT DO
------------------------------------------
It does not merge orbits, and it offers no function that concatenates them. §4's mandatory
mechanism is a **minute-level coverage map** built *"before emitting T3/T4/T5"* — the
canonical minute tables — and §4.4 requires that *"the merge function MUST accept the
coverage map as a required argument. There is no API that concatenates orbit files
directly."*

Those tables are the write path's, M3/E5/#19 (`grid`, `write`; row 19 depends on 17, 18 and
14). Building a coverage map here would require the minute grid this issue does not own, and
shipping a merge without it would create exactly the API §4 forbids. So #18 supplies the
*rules* — identity and precedence — and `test_no_orbit_merge_api_exists` asserts that the
concatenation §4 forbids has not appeared.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from contexts.ingest.parsers import _fits
from domain.values import Identifier, Timestamp

#: §4's identification regex, verbatim.
ORBIT_STEM = re.compile(
    r"^HLS_(?P<date>\d{8})_(?P<start>\d{6})_(?P<dur>\d+)sec_lev1_V(?P<ver>\d{3})$"
)

#: The four detectors, and the two families they fall into (§2.6, §2.7).
CZT_DETECTORS = ("czt1", "czt2")
CDTE_DETECTORS = ("cdte1", "cdte2")
DETECTORS = CZT_DETECTORS + CDTE_DETECTORS


def family_of(detector: str) -> str:
    """`czt` or `cdte`. Fails on anything else rather than guessing a family.

    The family decides the PHA channel space — 341 for CZT, 511 for CdTe (§2.7 r5) — so a
    wrong family is a wrong channel space, which F-11 exists to prevent.
    """
    lowered = detector.lower()
    if lowered in CZT_DETECTORS:
        return "czt"
    if lowered in CDTE_DETECTORS:
        return "cdte"
    _fits.fail(
        "F-07", f"/{detector}",
        f"detector {detector!r} is in neither HEL1OS family; §2.6 and §2.7 name exactly "
        f"{list(DETECTORS)}",
    )


@dataclass(frozen=True)
class OrbitId:
    """One HEL1OS orbit archive, identified from its directory name (§4).

    `version` is an opaque integer. `processing_date` is the header `DATE`, supplied by a
    caller that has read the product — this module reads no file, so precedence rule 3 takes
    it as an argument rather than discovering it.
    """

    date: str
    start: str
    duration_s: int
    version: int
    processing_date: Timestamp | None = None

    @property
    def start_epoch(self) -> float:
        """Seconds since the Unix epoch for the declared start, from the stem alone.

        Derived from the directory name rather than from a header, because `overlaps` must
        be answerable before any file is opened — §4 resolves coverage across orbits, and
        opening 391 archives to compare intervals would defeat the point.
        """
        moment = datetime.strptime(f"{self.date}{self.start}", "%Y%m%d%H%M%S").replace(
            tzinfo=timezone.utc
        )
        return moment.timestamp()

    @property
    def stem(self) -> str:
        return (
            f"HLS_{self.date}_{self.start}_{self.duration_s}sec_lev1_V{self.version:03d}"
        )

    @property
    def instrument_id(self) -> Identifier:
        return Identifier("hel1os")

    def detector_id(self, detector: str) -> Identifier:
        """`hel1os-czt1`. The detector is part of the instrument identity (ADR-0003).

        HEL1OS carries four physically distinct detectors in two families with different
        channel spaces; collapsing them to `hel1os` would make a CZT row and a CdTe row
        indistinguishable, which is the confusion F-11 forbids.
        """
        family_of(detector)
        return Identifier(f"hel1os-{detector.lower()}")


def parse_stem(name: str) -> OrbitId:
    """Read an orbit identity from a directory name. F-18 on anything that is not one."""
    match = ORBIT_STEM.match(name) if isinstance(name, str) else None
    if match is None:
        _fits.fail(
            "F-18", f"/{name}",
            f"{name!r} is not a HEL1OS orbit stem; §4 identifies orbits as "
            f"HLS_<YYYYMMDD>_<HHMMSS>_<DUR>sec_lev1_V<XYZ>",
        )
    return OrbitId(
        date=match.group("date"),
        start=match.group("start"),
        duration_s=int(match.group("dur")),
        version=int(match.group("ver")),
    )


def precedence(first: OrbitId, second: OrbitId) -> OrbitId:
    """Which of two orbits wins, by §4's four rules in order.

    Returns the winner. Raises F-14 when all four are exhausted — §4 is explicit that the
    fourth outcome is termination: **"Never coin-flip."** A tie that reached rule 4 means two
    products claim the same coverage with identical version, duration and processing date,
    and nothing in the archive distinguishes them; choosing either would be a decision the
    data does not support.
    """
    if first.version != second.version:
        return first if first.version > second.version else second

    if first.duration_s != second.duration_s:
        return first if first.duration_s > second.duration_s else second

    if first.processing_date is not None and second.processing_date is not None:
        if first.processing_date.instant != second.processing_date.instant:
            return (
                first
                if first.processing_date.instant > second.processing_date.instant
                else second
            )

    _fits.fail(
        "F-14", f"/{first.stem}",
        f"version precedence is unresolved between {first.stem!r} and {second.stem!r}: "
        f"equal version V{first.version:03d}, equal duration {first.duration_s}s, and "
        f"processing dates "
        f"{'absent' if first.processing_date is None or second.processing_date is None else 'equal'}"
        f". §4 rule 4 terminates rather than choosing — never coin-flip.",
    )


def rule_applied(first: OrbitId, second: OrbitId) -> str:
    """Which of §4's rules decided, for the resolution log §4.2 requires.

    §4.2: *"log every resolution … with winner, losers, and rule invoked."* The log itself is
    written by the merge step (#19); naming the rule is part of the precedence decision and
    so belongs with it.
    """
    if first.version != second.version:
        return "rule-1-higher-version"
    if first.duration_s != second.duration_s:
        return "rule-2-longer-duration"
    if (
        first.processing_date is not None
        and second.processing_date is not None
        and first.processing_date.instant != second.processing_date.instant
    ):
        return "rule-3-later-processing-date"
    return "rule-4-terminate"


def overlaps(first: OrbitId, second: OrbitId) -> bool:
    """Whether two orbits claim any second in common.

    §4 names two classes, both `OBSERVED` in the archive and both present locally:
      Class A — identical interval, different version.
      Class B — partial overlap, different start and duration.

    Class B is why §4 says file-level selection is *insufficient*: each file covers seconds
    the other lacks. This predicate reports the overlap; it does not resolve it, because
    resolving Class B needs the minute-level coverage map that belongs to #19.

    §4 defines no overlap measure. Over the stem-declared intervals of the 391-orbit archive
    this predicate reports 50 overlapping pairs, where §4 records 46 and the Milestone VI engine
    recorded 49; the difference is recorded, not reconciled (CONTRA-007 Observation F).
    """
    first_start, second_start = first.start_epoch, second.start_epoch
    return (
        first_start < second_start + second.duration_s
        and second_start < first_start + first.duration_s
    )


__all__ = [
    "CDTE_DETECTORS",
    "CZT_DETECTORS",
    "DETECTORS",
    "ORBIT_STEM",
    "OrbitId",
    "family_of",
    "overlaps",
    "parse_stem",
    "precedence",
    "rule_applied",
]

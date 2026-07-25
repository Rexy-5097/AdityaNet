"""
app/v2/resolution/version_engine.py — Version Resolution Engine (Milestone VI).

Implements contract §4 exactly. The parser layer is FROZEN and is not imported
or modified here.

WHAT THIS ENGINE DOES: it decides, for every (minute, detector), which orbit file
OWNS that sample. That is all.

WHAT IT MUST NEVER DO (§4 / milestone constraint):
  * modify measurements
  * interpolate
  * average competing files
  * merge detector values
It selects provenance. Nothing else. No measurement value is read by this module
-- it operates purely on orbit metadata (interval, version, duration, hashes),
which is why averaging or interpolation is not merely forbidden but structurally
impossible here: the engine never holds a measurement.

WHY A COVERAGE MAP AT ALL (§4): two overlap classes exist in the real archive.
  Class A -- identical interval, different version   -> file-level selection works
  Class B -- partial overlap, different start/dur    -> file-level selection FAILS,
             because each file covers seconds the other lacks
Only a per-minute map can resolve Class B, so the map is the single authoritative
representation of orbit ownership and the merge API cannot be called without it.

`OBSERVED` (2026-07-17, real archive): 49 time-overlapping orbit pairs; version
distribution V111x371, V211x16, V112x3, V311x1; overlapping pairs' evt.fits
SHA-256 values DIFFER, so they are genuine reprocessings and content-hash dedup
would fail -- precedence is required.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping

import pandas as pd

from app.v2.models.metadata import PARSER_VERSION, FailLoud

MINUTE = pd.Timedelta(minutes=1)


# ── precedence rules, in contract order (§4) ────────────────────────────────
RULE_VERSION = "R1_higher_version"
RULE_DURATION = "R2_longer_duration"
RULE_PROCESSING_DATE = "R3_later_processing_date"
RULE_UNRESOLVED = "R4_unresolved_F14"

PRECEDENCE_ORDER = (RULE_VERSION, RULE_DURATION, RULE_PROCESSING_DATE)


@dataclass(frozen=True)
class OrbitCandidate:
    """One HEL1OS orbit product competing for ownership of minutes.

    Carries METADATA ONLY. No measurement ever enters this object -- that is the
    structural guarantee behind "selects provenance, nothing else".
    """
    orbit_id: str
    path: str
    sha256: str
    version: int                 # from filename V<XYZ>, parsed as int
    duration_s: int              # from filename <DUR>sec
    t_start_utc: pd.Timestamp
    t_stop_utc: pd.Timestamp
    detectors: tuple[str, ...]
    processing_date: str | None = None   # header DATE; ABSENT in HEL1OS (see R3)

    def claimed_minutes(self) -> pd.DatetimeIndex:
        """Minutes this orbit claims: floor(start) .. floor(stop), inclusive."""
        if self.t_stop_utc < self.t_start_utc:
            raise FailLoud("F-19", "orbit stop precedes start",
                           file=self.path, got=(str(self.t_start_utc),
                                                str(self.t_stop_utc)))
        return pd.date_range(self.t_start_utc.floor("min"),
                             self.t_stop_utc.floor("min"), freq="min", tz="UTC")


@dataclass
class Resolution:
    """One resolved conflict. §4: every resolution is logged."""
    minute_utc: str
    detector: str
    winner_orbit_id: str
    winner_sha256: str
    rule_invoked: str
    rejected: list[dict]
    n_timestamps_affected: int = 1

    def to_row(self) -> dict:
        return asdict(self)


def _compare(a: OrbitCandidate, b: OrbitCandidate) -> tuple[OrbitCandidate, str]:
    """Return (winner, rule) for two candidates, per §4 precedence.

    Order is fixed and total: version -> duration -> processing date -> F-14.
    NEVER a coin-flip, never insertion-order, never last-write-wins.
    """
    if a.version != b.version:
        return (a, RULE_VERSION) if a.version > b.version else (b, RULE_VERSION)
    if a.duration_s != b.duration_s:
        return (a, RULE_DURATION) if a.duration_s > b.duration_s else (b, RULE_DURATION)
    # R3: HEL1OS primaries carry NO `DATE` header (OBSERVED 2026-07-17), so this
    # branch has no data source in the current archive and falls through to F-14.
    # It is implemented anyway: a reprocessed product could add DATE, and the
    # contract's order must hold if it does.
    if a.processing_date is not None and b.processing_date is not None \
            and a.processing_date != b.processing_date:
        return ((a, RULE_PROCESSING_DATE) if a.processing_date > b.processing_date
                else (b, RULE_PROCESSING_DATE))
    raise FailLoud(
        "F-14",
        "version precedence unresolved after all tie-breaks (version, duration, "
        "processing date); refusing to choose arbitrarily",
        expected="a deterministic winner",
        got={"a": a.orbit_id, "b": b.orbit_id, "version": a.version,
             "duration_s": a.duration_s,
             "processing_date_a": a.processing_date,
             "processing_date_b": b.processing_date,
             "note": "HEL1OS primaries have no DATE header, so R3 cannot "
                     "resolve; this is F-14 by design, not a bug"})


def resolve_candidates(cands: list[OrbitCandidate]) -> tuple[OrbitCandidate, str]:
    """Reduce N competing candidates to one winner + the rule that decided it."""
    if not cands:
        raise FailLoud("F-14", "no candidates to resolve")
    winner, rule = cands[0], None
    for c in cands[1:]:
        winner, rule = _compare(winner, c)
    if rule is None:
        rule = RULE_VERSION           # single candidate: uncontested
    return winner, rule


class CoverageMap:
    """THE single authoritative representation of orbit ownership (§4).

    Invariant, enforced at construction and re-assertable at any time:
        every (minute, detector) has EXACTLY ONE provenance owner.
    """

    def __init__(self, owners: Mapping[tuple[pd.Timestamp, str], str],
                 resolutions: list[Resolution],
                 candidates: Mapping[str, OrbitCandidate]):
        self._owners = dict(owners)
        self.resolutions = resolutions
        self.candidates = dict(candidates)
        self.assert_unique_ownership()

    # ── queries ────────────────────────────────────────────────────────────
    def owner(self, minute: pd.Timestamp, detector: str) -> str | None:
        return self._owners.get((pd.Timestamp(minute).floor("min"),
                                 detector.upper()))

    def owns(self, orbit_id: str, minute: pd.Timestamp, detector: str) -> bool:
        return self.owner(minute, detector) == orbit_id

    def owned_minutes(self, orbit_id: str, detector: str) -> pd.DatetimeIndex:
        ms = [m for (m, d), o in self._owners.items()
              if o == orbit_id and d == detector.upper()]
        return pd.DatetimeIndex(sorted(ms), tz="UTC")

    def __len__(self) -> int:
        return len(self._owners)

    # ── invariants ─────────────────────────────────────────────────────────
    def assert_unique_ownership(self) -> None:
        """A dict cannot hold duplicate keys, so uniqueness is structural.

        This method exists to make the invariant CHECKABLE rather than merely
        true-by-construction, and to catch a future refactor that swaps the dict
        for something weaker.
        """
        for (m, d), o in self._owners.items():
            if o is None:
                raise FailLoud("F-15", "minute with no owner in the coverage map",
                               got=(str(m), d))
            if o not in self.candidates:
                raise FailLoud("F-15", "owner is not a known candidate",
                               expected="an orbit_id present in candidates", got=o)

    # ── logging (§4) ───────────────────────────────────────────────────────
    def resolution_log(self) -> dict:
        by_pair = defaultdict(lambda: {"minutes": [], "rec": None})
        for r in self.resolutions:
            key = (r.winner_orbit_id, r.detector,
                   tuple(sorted(x["orbit_id"] for x in r.rejected)), r.rule_invoked)
            by_pair[key]["minutes"].append(r.minute_utc)
            by_pair[key]["rec"] = r
        conflicts = []
        for (win, det, losers, rule), v in sorted(by_pair.items(), key=lambda x: str(x[0])):
            r = v["rec"]
            mins = sorted(v["minutes"])
            conflicts.append({
                "winner": {"orbit_id": win, "sha256": r.winner_sha256},
                "rejected_candidates": r.rejected,
                "precedence_rule_invoked": rule,
                "n_timestamps_affected": len(mins),
                "timestamps_affected": {"first": mins[0], "last": mins[-1],
                                        "all": mins if len(mins) <= 50 else
                                        mins[:25] + ["…"] + mins[-25:]},
                "detector": det,
            })
        return {
            "engine_version": PARSER_VERSION,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "contract": "PARSER_SPECIFICATION.md §4 (version-selection policy)",
            "precedence_order": list(PRECEDENCE_ORDER) + [RULE_UNRESOLVED],
            "n_candidates": len(self.candidates),
            "n_owned_minute_detector_pairs": len(self._owners),
            "n_conflicting_minute_detector_pairs": len(self.resolutions),
            "n_distinct_conflicts": len(conflicts),
            "rules_invoked": dict(sorted(
                pd.Series([r.rule_invoked for r in self.resolutions])
                .value_counts().to_dict().items())) if self.resolutions else {},
            "conflicts": conflicts,
        }

    def write_resolution_log(self, path: str) -> dict:
        log = self.resolution_log()
        with open(path, "w") as f:
            json.dump(log, f, indent=1)
        return log


def build_coverage_map(candidates: Iterable[OrbitCandidate]) -> CoverageMap:
    """§4 mandatory mechanism — build the explicit minute-level coverage map.

    Two phases, deliberately:
      1. COLLECT every claim into (minute, detector) -> [candidates].
      2. RESOLVE each contested key by precedence, logging every resolution.

    The phases are separate so that ownership can never be decided by iteration
    order. A single-pass "assign as you go" loop would silently implement
    last-write-wins -- the exact implicit overwrite §4 forbids.
    """
    cands = list(candidates)
    by_id = {c.orbit_id: c for c in cands}
    if len(by_id) != len(cands):
        dupes = [c.orbit_id for c in cands]
        raise FailLoud("F-14", "duplicate orbit_id among candidates",
                       got=[k for k in dupes if dupes.count(k) > 1][:5])

    # Phase 1 — collect claims. No decisions here.
    claims: dict[tuple[pd.Timestamp, str], list[OrbitCandidate]] = defaultdict(list)
    for c in cands:
        for m in c.claimed_minutes():
            for d in c.detectors:
                claims[(m, d.upper())].append(c)

    # Phase 2 — resolve. Every contested key is decided by the frozen order.
    owners: dict[tuple[pd.Timestamp, str], str] = {}
    resolutions: list[Resolution] = []
    for key, competing in claims.items():
        if len(competing) == 1:
            owners[key] = competing[0].orbit_id
            continue
        winner, rule = resolve_candidates(competing)
        owners[key] = winner.orbit_id
        resolutions.append(Resolution(
            minute_utc=key[0].isoformat(), detector=key[1],
            winner_orbit_id=winner.orbit_id, winner_sha256=winner.sha256,
            rule_invoked=rule,
            rejected=[{"orbit_id": c.orbit_id, "sha256": c.sha256,
                       "version": c.version, "duration_s": c.duration_s}
                      for c in competing if c.orbit_id != winner.orbit_id]))
    return CoverageMap(owners, resolutions, by_id)


# ── the merge gate (§4 point 4) ─────────────────────────────────────────────
def select_owned_rows(df: pd.DataFrame, *, orbit_id: str, detector: str,
                      coverage_map: CoverageMap,
                      time_column: str = "timestamp_utc") -> pd.DataFrame:
    """Keep only rows whose minute is OWNED by `orbit_id` for `detector`.

    §4 point 4: `coverage_map` is a REQUIRED keyword argument. There is no API in
    v2 that concatenates orbit files directly -- naive ingestion is structurally
    impossible rather than merely discouraged.

    This FILTERS rows by ownership. It does not modify, interpolate, average or
    merge any measurement: every returned value is byte-identical to its input.
    """
    if time_column not in df.columns:
        raise FailLoud("F-04", f"time column {time_column!r} absent",
                       expected=time_column, got=list(df.columns))
    if not isinstance(coverage_map, CoverageMap):
        raise FailLoud("F-14", "select_owned_rows requires a CoverageMap; "
                               "direct concatenation of orbit files is forbidden",
                       expected="CoverageMap", got=type(coverage_map).__name__)
    minutes = pd.DatetimeIndex(df[time_column]).floor("min")
    det = detector.upper()
    mask = [coverage_map.owner(m, det) == orbit_id for m in minutes]
    return df.loc[mask]


def assert_no_duplicate_minutes(df: pd.DataFrame, *,
                                time_column: str = "timestamp_utc",
                                detector_column: str | None = None) -> None:
    """F-15 post-condition — duplicate (minute, detector) output is impossible.

    §4 point 3. This is the last line of defence: even if a future caller
    bypassed the coverage map, the emitted table cannot contain a duplicated
    (minute, detector) without terminating here.
    """
    if time_column not in df.columns:
        raise FailLoud("F-04", f"time column {time_column!r} absent",
                       expected=time_column, got=list(df.columns))
    minutes = pd.DatetimeIndex(df[time_column]).floor("min")
    if detector_column is None:
        keys = pd.Index(minutes)
    else:
        if detector_column not in df.columns:
            raise FailLoud("F-04", f"detector column {detector_column!r} absent",
                           got=list(df.columns))
        keys = pd.MultiIndex.from_arrays([minutes, df[detector_column]])
    if len(keys) != len(keys.unique()):
        dup = keys[keys.duplicated()]
        raise FailLoud("F-15", "duplicate (minute, detector) in output",
                       expected=f"{len(keys.unique())} unique keys",
                       got={"n_rows": len(keys),
                            "n_duplicates": len(dup),
                            "examples": [str(x) for x in list(dup)[:5]]})

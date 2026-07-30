"""SoLEXS `.gti.gz` — good time intervals.

Implements `SPEC-parsers@r6` §2.3.

THE INCLUSIVE CONVENTION, AND WHY THE TOLERANCE IS ZERO
--------------------------------------------------------
§2.3 as amended at r1: `START`/`STOP` are **inclusive second-marks** at 1-second sampling, so

    live_time(interval) = STOP − START + 1

`OBSERVED` on 2024-05-14 SDD2: 5 intervals, `Σ(STOP−START+1) = 86395.0 s`, equal to the
declared `EXPOSURE` **with exactly zero error**. The pre-amendment exclusive reading produced
"4 gaps of ~2 s", which was an artifact of the assumption rather than a property of the data.

F-09 requires that equality to be **exact, tolerance 0 s**. §5 states why: *"the relation is
definitional, and a tolerance would re-admit the ambiguity that produced CONTRADICTION-001."*
A tolerance here would not absorb noise — there is no noise in a sum of integers — it would
absorb a convention error, which is precisely the thing that must not be absorbed.

**The convention is verified for the implementation target only** (§2.3, §8 A-8). It is not
promoted to archive truth. Milestone VIII must verify it across all 436 archives, and §2.3 is
explicit that *"any deviation is a scientific finding and MUST terminate validation (never
tolerate, never widen)"*. So this parser fails on deviation and reports the arithmetic; it
does not widen.

EXPOSURE IS A STRING IN THE ARCHIVE
-----------------------------------
§2.3 records it: HDU1 `EXPOSURE` is `'86395.0'`, a string, while the primary `TSTART`/`TSTOP`
are ISO-8601 strings. The parser converts explicitly and fails loud if the conversion does
not succeed — it does not coerce, and it does not fall back to a computed value, because a
computed fallback would make F-09 compare a number against itself.

AN EMPTY GTI IS LEGAL
---------------------
F-12 is *"the single deliberate non-terminating rule"*. `NAXIS2 == 0` means the detector was
inactive — §1.1 records SDD1 at zero rows on 2024-05-14 with empty-string `TSTART`/`TSTOP` —
and the correct response is `detector_active = False` and zero intervals, not an error.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers.solexs import _fits
from contexts.ingest.parsers.solexs.lc import unix_to_timestamp
from domain.values import Digest, Identifier, Timestamp


@dataclass(frozen=True)
class Interval:
    """One good time interval, with inclusive second-marks (§2.3 r1)."""

    start: float
    stop: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.start) and math.isfinite(self.stop)):
            _fits.fail("F-16", "/GTI", f"interval bound not finite: {self}")
        if self.start >= self.stop:
            _fits.fail(
                "F-09", "/GTI",
                f"START {self.start!r} is not less than STOP {self.stop!r}; §2.3 requires "
                f"START<STOP per row",
            )

    @property
    def live_time(self) -> float:
        """`STOP − START + 1` — the inclusive convention, amended at r1."""
        return self.stop - self.start + 1

    @property
    def start_utc(self) -> Timestamp:
        return unix_to_timestamp(self.start)

    @property
    def stop_utc(self) -> Timestamp:
        return unix_to_timestamp(self.stop)

    def covers(self, second: float) -> bool:
        """Inclusive at both ends, which is the whole content of the r1 amendment."""
        return self.start <= second <= self.stop


@dataclass(frozen=True)
class GoodTimeIntervals:
    """A parsed `.gti` product.

    `detector_active` is False exactly when the archive declared zero rows — the F-12 path.
    It is a recorded state, not an inference: nothing here decides a detector was inactive
    from the absence of something else.
    """

    detector: str
    source_path: Path
    source_digest: Digest
    intervals: tuple[Interval, ...]
    declared_exposure: float | None
    detector_active: bool

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"solexs-{self.detector.lower()}")

    @property
    def live_time(self) -> float:
        """Σ(STOP − START + 1) over all intervals."""
        return sum(interval.live_time for interval in self.intervals)

    def excluded_seconds(self, tstart: float, rows: int) -> tuple[int, ...]:
        """Day-offsets not covered by any interval.

        §2.3 `OBSERVED` on 2024-05-14 SDD2: [0, 5, 30072, 30078, 83951] — second 0 because
        data begins at 00:00:01, plus four isolated 1-second dropouts.

        Offered here so the day-assembly layer (#19) can evaluate the `NaN ⇒ GTI-excluded`
        implication that §2.1 explicitly places outside the single-file parsers.
        """
        covered = set()
        for interval in self.intervals:
            first = int(interval.start - tstart)
            last = int(interval.stop - tstart)
            covered.update(range(first, last + 1))
        return tuple(offset for offset in range(rows) if offset not in covered)


def parse(path: Path, digest: Digest) -> GoodTimeIntervals:
    """Parse one `.gti.gz` product. Every §2.3 validation, exact where the spec says exact."""
    from astropy.io import fits

    source = path.name
    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        primary = _fits.hdu(hdul, "PRIMARY", source=source).header
        gti_hdu = _fits.hdu(hdul, "GTI", source=source)
        gti = gti_hdu.header

        rows = int(_fits.keyword(gti, "NAXIS2", source=source, hdu_name="GTI"))
        detector = _detector_from_path(path, source)

        # ── F-12: the single deliberate non-terminating rule ────────────────────
        if rows == 0:
            return GoodTimeIntervals(
                detector=detector,
                source_path=path,
                source_digest=digest,
                intervals=(),
                declared_exposure=None,
                detector_active=False,
            )

        starts = _fits.column(gti_hdu, "START", source=source, hdu_name="GTI")
        stops = _fits.column(gti_hdu, "STOP", source=source, hdu_name="GTI")
        intervals = tuple(
            Interval(float(a), float(b)) for a, b in zip(starts, stops)
        )

        _validate_ordering(intervals, source)

        declared = _declared_exposure(gti, source)
        summed = sum(interval.live_time for interval in intervals)
        if summed != declared:
            # F-09, exact. §5: a tolerance would re-admit the ambiguity that produced
            # CONTRADICTION-001, and the sum of integer second-counts has no noise to absorb.
            _fits.fail(
                "F-09", f"/{source}#GTI/EXPOSURE",
                f"Σ(STOP−START+1) = {summed!r} s but EXPOSURE declares {declared!r} s. "
                f"§2.3 requires exact equality with tolerance 0 s. The inclusive convention "
                f"is verified for 2024-05-14 SDD2 only (§8 A-8); a deviation is a scientific "
                f"finding and must terminate validation, never widen the tolerance.",
            )

        _validate_within_day(primary, intervals, source)

    return GoodTimeIntervals(
        detector=detector,
        source_path=path,
        source_digest=digest,
        intervals=intervals,
        declared_exposure=declared,
        detector_active=True,
    )


def _detector_from_path(path: Path, source: str) -> str:
    """SDD1 or SDD2, from the directory the archive places the product in (§1.1).

    Read from the path because the `.gti` HDU carries no `FILTER` keyword — unlike `.lc` and
    `.pi`, which do. Verified against the archive rather than assumed, and a path that does
    not name a detector fails rather than defaulting to one.
    """
    for part in path.parts[::-1]:
        if part.upper() in ("SDD1", "SDD2"):
            return part.upper()
    _fits.fail(
        "F-18", f"/{source}",
        f"no SDD1/SDD2 directory in {path}; §1.1 places every SoLEXS product under one, and "
        f"the .gti HDU carries no FILTER keyword to fall back on",
    )


def _declared_exposure(header, source: str) -> float:
    """§2.3: HDU1 `EXPOSURE` is a **string** in the archive. Converted explicitly."""
    raw = _fits.keyword(header, "EXPOSURE", source=source, hdu_name="GTI")
    try:
        return float(raw)
    except (TypeError, ValueError):
        _fits.fail(
            "F-09", f"/{source}#GTI/EXPOSURE",
            f"EXPOSURE is {raw!r}, which is not a number. §2.3 records it as the string "
            f"'86395.0'; a value that will not convert cannot be compared against F-09.",
        )


def _validate_ordering(intervals: tuple[Interval, ...], source: str) -> None:
    """§2.3: rows sorted and non-overlapping."""
    for index in range(1, len(intervals)):
        previous, current = intervals[index - 1], intervals[index]
        if current.start <= previous.stop:
            _fits.fail(
                "F-09", f"/{source}#GTI/START[{index}]",
                f"interval {index} starts at {current.start!r}, at or before the previous "
                f"stop {previous.stop!r}. Overlapping intervals would double-count live time.",
            )


def _validate_within_day(primary, intervals: tuple[Interval, ...], source: str) -> None:
    """§2.3: all intervals within [OBS_DATE 00:00, 23:59:59].

    The primary `TSTART`/`TSTOP` are ISO-8601 strings (§2.3), so they are compared as
    instants rather than as numbers. A non-parsing value is F-05 rather than a skipped check:
    silently not checking is the failure mode this whole specification exists to prevent.
    """
    raw_start = _fits.keyword(primary, "TSTART", source=source, hdu_name="PRIMARY")
    raw_stop = _fits.keyword(primary, "TSTOP", source=source, hdu_name="PRIMARY")
    try:
        declared_start = Timestamp(str(raw_start).replace("+00:00", "Z"))
        declared_stop = Timestamp(str(raw_stop).replace("+00:00", "Z"))
    except Exception:
        _fits.fail(
            "F-05", f"/{source}#PRIMARY/TSTART",
            f"primary TSTART/TSTOP are {raw_start!r}/{raw_stop!r}; §2.3 records them as "
            f"ISO-8601 strings such as '2024-05-14T00:00:01+00:00'",
        )

    for index, interval in enumerate(intervals):
        if interval.start_utc.instant < declared_start.instant:
            _fits.fail(
                "F-09", f"/{source}#GTI/START[{index}]",
                f"interval {index} starts at {interval.start_utc} — before the declared "
                f"TSTART {declared_start}",
            )
        if interval.stop_utc.instant > declared_stop.instant:
            _fits.fail(
                "F-09", f"/{source}#GTI/STOP[{index}]",
                f"interval {index} stops at {interval.stop_utc} — after the declared "
                f"TSTOP {declared_stop}",
            )


__all__ = ["GoodTimeIntervals", "Interval", "parse"]

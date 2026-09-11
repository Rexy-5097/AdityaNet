"""HEL1OS `aux/gti{czt,cdte}{1,2}.fits` — per-detector good time intervals. §2.9.

`OBSERVED`: HDU1 `GTI_<DET>`; columns **lowercase** `tstart`, `tstop`, units undeclared;
`NAXIS2 = 1` on the sample orbit.

THE CASE DIFFERENCE IS THE POINT
--------------------------------
§2.9: *"Column-name case differs from SoLEXS (`START`/`STOP` uppercase) → all column access
MUST be case-insensitive (§8 A-2)."* `_fits.column` compares upper-cased names, so the same
helper reads both instruments without either knowing the other's spelling — and
`test_columns_are_read_case_insensitively` asserts it, because a case-sensitive lookup would
fail here as F-04 and look like a missing column rather than a spelling difference.

UNITS ARE UNDECLARED, SO THE UNIT IS NOT ASSUMED
-------------------------------------------------
§2.9 records the units as undeclared. The values `OBSERVED` on the reference orbit are
`61017.00009887` / `61017.49984764`, which are MJD — the same encoding the other HEL1OS
products use, and far outside any plausible seconds interpretation. That reading is
*checked* rather than assumed: a bound outside the plausible MJD range terminates rather than
being reinterpreted, because a GTI misread by an epoch would silently include or exclude the
whole orbit.

No `Σ(STOP−START+1) == EXPOSURE` check appears here. That is SoLEXS §2.3's rule, resting on
1-second sampling and a declared `EXPOSURE` keyword; §2.9 declares neither. Importing it
would be applying one instrument's convention to another, which F-07 forbids.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers import _fits
from contexts.ingest.parsers.hel1os.lc import mjd_to_timestamp
from contexts.ingest.parsers.hel1os.orbit import family_of
from domain.values import Digest, Identifier, Timestamp

#: The archive's HEL1OS coverage begins 2025-12-07 (MJD 61016). A bound outside a generous
#: window around the mission is not an MJD, and reinterpreting it would be a guess.
PLAUSIBLE_MJD = (50_000.0, 80_000.0)


@dataclass(frozen=True)
class Interval:
    """One good time interval, in MJD.

    No `+1` second. That is SoLEXS §2.3's inclusive-second-mark convention, verified for a
    1 s-sampled product with a declared EXPOSURE; §2.9 declares neither, so the duration here
    is the plain difference and is labelled as such.
    """

    start_mjd: float
    stop_mjd: float

    def __post_init__(self) -> None:
        for name, value in (("start", self.start_mjd), ("stop", self.stop_mjd)):
            if not math.isfinite(value):
                _fits.fail("F-16", f"/GTI/{name}", f"{name} is not finite ({value!r})")
            if not PLAUSIBLE_MJD[0] <= value <= PLAUSIBLE_MJD[1]:
                _fits.fail(
                    "F-05", f"/GTI/{name}",
                    f"{name} {value!r} is outside the plausible MJD range {PLAUSIBLE_MJD}. "
                    f"§2.9 leaves the unit undeclared; a bound that is not an MJD is not "
                    f"reinterpreted as another epoch.",
                )
        if self.start_mjd >= self.stop_mjd:
            _fits.fail("F-09", "/GTI",
                       f"start {self.start_mjd!r} is not before stop {self.stop_mjd!r}")

    @property
    def duration_s(self) -> float:
        return (self.stop_mjd - self.start_mjd) * 86_400.0

    @property
    def start_utc(self) -> Timestamp:
        return mjd_to_timestamp(self.start_mjd)

    @property
    def stop_utc(self) -> Timestamp:
        return mjd_to_timestamp(self.stop_mjd)

    def covers(self, mjd: float) -> bool:
        return self.start_mjd <= mjd <= self.stop_mjd


@dataclass(frozen=True)
class GoodTimeIntervals:
    """A parsed HEL1OS GTI product."""

    detector: str
    source_path: Path
    source_digest: Digest
    intervals: tuple[Interval, ...]
    detector_active: bool

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"hel1os-{self.detector.lower()}")

    @property
    def live_time_s(self) -> float:
        return sum(interval.duration_s for interval in self.intervals)


def parse(path: Path, digest: Digest, *, detector: str) -> GoodTimeIntervals:
    """Parse one `gti<det>.fits`. F-12 applies: zero rows is legal, not an error."""
    from astropy.io import fits

    source = path.name
    family_of(detector)
    expected = f"GTI_{detector.upper()}"

    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        table = _fits.hdu(hdul, expected, source=source)
        rows = int(_fits.keyword(table.header, "NAXIS2", source=source, hdu_name=expected))

        if rows == 0:
            # F-12, the single deliberate non-terminating rule: the detector was inactive.
            return GoodTimeIntervals(detector, path, digest, (), detector_active=False)

        starts = _fits.column(table, "tstart", source=source, hdu_name=expected)
        stops = _fits.column(table, "tstop", source=source, hdu_name=expected)
        intervals = tuple(Interval(float(a), float(b)) for a, b in zip(starts, stops))

        for index in range(1, len(intervals)):
            if intervals[index].start_mjd <= intervals[index - 1].stop_mjd:
                _fits.fail(
                    "F-09", f"/{source}#{expected}/tstart[{index}]",
                    f"interval {index} starts at or before the previous stop; overlapping "
                    f"intervals would double-count live time",
                )

    return GoodTimeIntervals(detector, path, digest, intervals, detector_active=True)


__all__ = ["GoodTimeIntervals", "Interval", "PLAUSIBLE_MJD", "parse"]

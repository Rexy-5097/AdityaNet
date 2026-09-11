"""HEL1OS `aux/hk.fits` — housekeeping. §2.8, Phase 1a's key asset.

THE PARSER PRESERVES ARCHIVE ORDER EXACTLY. IT PERFORMS NO SORTING.
--------------------------------------------------------------------
§2.8, binding at r4, and stated as a general v2 principle rather than a HEL1OS special case:

> *"The parser MUST preserve archive order exactly. It performs no sorting. The parser is a
> lossless representation of the archive — reading and transforming are separate acts, and a
> parser that silently reorders is no longer a faithful reader."*

`mjd` here is a **measurement written in telemetry-arrival order**, not a sorted index. The
r0 requirement that it be non-decreasing was **falsified by the archive** and removed at r4.
What replaced it, with the header-span comparison made precise at r7:

    mjd finite                     F-16
    mjd unique                     F-16 — a repeated timestamp is a defect, not jitter
    header-span consistency        TSTART − ε_t ≤ min(mjd) and max(mjd) ≤ TSTOP + ε_t, else F-06
    inversion statistics RECORDED  n_out_of_order and max_backward_step_s, never thresholded
    czt1temp/czt2temp finite       F-16 — exactly these two; §2.8 requires no others
    suninfov in {0, 1}             F-07

**No jitter threshold is defined.** §2.8: the magnitude is *reported*, never compared against
an invented tolerance. So `InversionStats` carries the numbers and nothing here compares them
to anything. `ε_t` is not such a tolerance: it is §5.1's allowance for float64 representation in
a comparison against a header bound, and it applies to that comparison alone (CONTRA-007
Defect B, which also records CONTRADICTION-006's earlier implementation-only ruling).

`OBSERVED` (orbit `HLS_20251208_000008`): 9,514 rows; 424 of 9,513 steps decrease; max
backward step 892.4 ms; 0 duplicates; range within the header span. Every one of those figures
is re-measured by the real-corpus tests.

WHAT IS CAPTURED — §2.8's DECISIVE COLUMNS, BY THE ARCHIVE'S OWN NAMES
----------------------------------------------------------------------
§2.8 lists the columns decisive for Phase 1a by concern: pile-up, saturation, gain/HV, thermal,
detector health, rates, pointing and time. Its detector-health line abbreviates per-detector
columns (`hotpixcnt`, `hotpixthr`, `hotpixlgcstat`, `bunpxctr`); the archive carries them only
with a detector prefix — `czt1hotpixcnt`, `czt2bunpxctr` — which is how §3 T4 names them too.
Those prefixed names are read and nothing beyond that spelling is inferred (CONTRA-007
Observation E).

Each column keeps its archive values and dtype — an integer counter stays an integer — and its
declared unit. Where §2.8 states a unit (V for the HV monitors, keV for `czt1enth`, degC for the
four temperatures, c/s for the four rates) the declaration is checked and a contradiction is
F-07. Where §2.8 states none, the declared unit is carried as the archive gives it, `None`
included, and no meaning is supplied.

`suninfov` IS A FIRST-CLASS QUALITY FLAG
-----------------------------------------
§2.8, binding: *"data outside Sun-in-FOV is not solar signal. It MUST propagate to the
canonical tables."* Those tables are #19's, so this parser's obligation is to carry the flag
faithfully per row and to refuse a value outside {0, 1} rather than coercing it to a bool.

THE `czt2enth` UNIT INCONSISTENCY IS RECORDED, NOT REPAIRED
------------------------------------------------------------
§2.8: *"`czt1enth` has unit `keV` but `czt2enth` has unit=None for the same physical
quantity — a metadata inconsistency; the parser applies the `czt1enth` unit to both and
records the assumption (§8 A-4)."* So when `czt2enth` declares no unit it takes `czt1enth`'s and
`assumptions` says so; when it declares the same unit nothing is assumed; when it declares a
different one, the two readings of one quantity disagree and the parse terminates (F-07).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers import _fits
from contexts.ingest.parsers.hel1os.lc import (
    SECONDS_PER_DAY,
    TIME_REPRESENTATION_ALLOWANCE_S,
    mjd_to_timestamp,
)
from domain.values import Digest, Identifier, Timestamp

HDU_NAME = "HLSHK"

#: §2.8's decisive columns, by concern, in the archive's spelling.
PILEUP = ("cdte1pilectr", "cdte2pilectr")
SATURATION = ("czt1satctr1", "czt2satctr1")
GAIN_HV = ("czthvmon", "cdtehvmon", "czt1enth", "czt2enth", "cdte1enerthr", "cdte2enerthr")
THERMAL = ("czt1temp", "czt2temp", "cdte1temp", "cdte2temp")
DETECTOR_HEALTH = (
    "czt1hotpix", "czt2hotpix", "czt1hotpixcnt", "czt2hotpixcnt",
    "czt1hotpixthr", "czt2hotpixthr", "czt1hotpixlgcstat", "czt2hotpixlgcstat",
    "czt1bunpxctr", "czt2bunpxctr", "fehkstat",
)
RATES = ("czt1ctr", "czt2ctr", "cdte1ctr", "cdte2ctr")
POINTING = ("sunradeg", "sundecdeg", "suninfov", "sun2yawdeg", "sun2rolldeg", "sun2pitchdeg")
TIME = (
    "l0dhobt", "l0utcyr", "l0utcmon", "l0utcdy", "l0utchr", "l0utcmin", "l0utcsc", "l0utcmsc",
)

#: Every decisive column carried in `columns`. `mjd` and `suninfov` are validated and carried
#: in their own fields.
CAPTURED = (
    PILEUP + SATURATION + GAIN_HV + THERMAL + DETECTOR_HEALTH + RATES
    + tuple(name for name in POINTING if name != "suninfov") + TIME
)

#: The units §2.8 states. A declared unit that contradicts one of these is F-07.
STATED_UNITS: dict[str, str] = {
    "czthvmon": "V", "cdtehvmon": "V", "czt1enth": "keV",
    "czt1temp": "degC", "czt2temp": "degC", "cdte1temp": "degC", "cdte2temp": "degC",
    "czt1ctr": "c/s", "czt2ctr": "c/s", "cdte1ctr": "c/s", "cdte2ctr": "c/s",
}

#: §2.8 requires exactly these finite. The CdTe temperatures are carried, NaN included.
REQUIRED_FINITE = ("czt1temp", "czt2temp")

#: §8 A-4, recorded on the product whenever it is applied.
A4_ASSUMPTION = (
    "czt2enth carries unit=None in the archive while czt1enth carries keV for the same "
    "physical quantity; the czt1enth unit is applied to both and the assumption is recorded "
    "(SPEC-parsers r7 §2.8, §8 A-4)"
)


@dataclass(frozen=True)
class InversionStats:
    """Recorded, never thresholded (§2.8 r4).

    §2.8 is explicit that no jitter threshold is defined and the magnitude is reported. So
    this type has no `is_acceptable` and no limit to compare against — adding one would be
    inventing the tolerance the amendment refused to invent.
    """

    rows: int
    steps: int
    n_out_of_order: int
    max_backward_step_s: float

    @property
    def max_backward_step_ms(self) -> float:
        return self.max_backward_step_s * 1000.0


@dataclass(frozen=True)
class Housekeeping:
    """A parsed `hk.fits`, in archive order.

    `columns` holds every §2.8 decisive column as the archive's values; `units` holds each
    column's declared unit, after A-4 where it applied.
    """

    source_path: Path
    source_digest: Digest
    mjd: tuple[float, ...]
    suninfov: tuple[int, ...]
    columns: dict[str, tuple]
    units: dict[str, str | None]
    header_tstart: float
    header_tstop: float
    inversions: InversionStats
    assumptions: tuple[str, ...] = ()

    @property
    def instrument_id(self) -> Identifier:
        return Identifier("hel1os")

    def valid_time(self, index: int) -> Timestamp:
        return mjd_to_timestamp(self.mjd[index])

    def sun_in_fov(self, index: int) -> bool:
        """The first-class quality flag §2.8 requires to propagate."""
        return self.suninfov[index] == 1


def parse(path: Path, digest: Digest) -> Housekeeping:
    """Parse one `hk.fits`. Archive order preserved exactly; nothing is sorted."""
    from astropy.io import fits

    source = path.name
    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        table = _fits.hdu(hdul, HDU_NAME, source=source)
        header = table.header

        mjd = tuple(
            float(v) for v in _fits.column(table, "mjd", source=source, hdu_name=HDU_NAME)
        )
        if not mjd:
            _fits.fail("F-17", f"/{source}#{HDU_NAME}",
                       "HLSHK has no rows; §2.8 describes an orbit-resolved series")
        for index, value in enumerate(mjd):
            if not math.isfinite(value):
                _fits.fail("F-16", f"/{source}#{HDU_NAME}/mjd[{index}]",
                           f"mjd[{index}] is not finite ({value!r})")

        # Duplicates remain F-16 (§2.8 r4): a repeated timestamp is a genuine defect, where
        # an inversion is packet-arrival jitter.
        if len(set(mjd)) != len(mjd):
            _fits.fail(
                "F-16", f"/{source}#{HDU_NAME}/mjd",
                f"{len(mjd) - len(set(mjd))} duplicate timestamp(s). §2.8 r4 removed the "
                f"non-decreasing requirement but kept this one: an inversion is jitter, a "
                f"duplicate is a defect.",
            )

        header_tstart = float(_fits.keyword(header, "TSTART", source=source,
                                            hdu_name=HDU_NAME))
        header_tstop = float(_fits.keyword(header, "TSTOP", source=source,
                                           hdu_name=HDU_NAME))
        _check_header_span(mjd, header_tstart, header_tstop, source)

        suninfov_raw = _fits.column(table, "suninfov", source=source, hdu_name=HDU_NAME)
        suninfov: list[int] = []
        for index, value in enumerate(suninfov_raw):
            flag = int(value)
            if flag not in (0, 1):
                _fits.fail(
                    "F-07", f"/{source}#{HDU_NAME}/suninfov[{index}]",
                    f"suninfov[{index}] is {value!r}; §2.8 declares it a flag in {{0, 1}} "
                    f"and it is a first-class quality flag — coercing it would decide "
                    f"whether data is solar signal on the parser's authority",
                )
            suninfov.append(flag)

        captured: dict[str, tuple] = {}
        units: dict[str, str | None] = {}
        for name in CAPTURED:
            captured[name] = tuple(
                _fits.column(table, name, source=source, hdu_name=HDU_NAME).tolist()
            )
            units[name] = _fits.declared_unit(table, name, source=source, hdu_name=HDU_NAME)
        units["suninfov"] = _fits.declared_unit(table, "suninfov", source=source,
                                                hdu_name=HDU_NAME)

    for name, stated in STATED_UNITS.items():
        if units[name] != stated:
            _fits.fail(
                "F-07", f"/{source}#{HDU_NAME}/{name}",
                f"{name} declares unit {units[name]!r}; §2.8 states {stated!r}. Reading it "
                f"under the stated unit would assume a convention the product contradicts.",
            )

    assumptions: tuple[str, ...] = ()
    if units["czt2enth"] is None:
        units["czt2enth"] = units["czt1enth"]
        assumptions = (A4_ASSUMPTION,)
    elif units["czt2enth"] != units["czt1enth"]:
        _fits.fail(
            "F-07", f"/{source}#{HDU_NAME}/czt2enth",
            f"czt2enth declares {units['czt2enth']!r} and czt1enth declares "
            f"{units['czt1enth']!r} for the same physical quantity; §8 A-4 covers an "
            f"undeclared czt2enth unit, not a contradictory one",
        )

    for name in REQUIRED_FINITE:
        for index, value in enumerate(captured[name]):
            if not math.isfinite(value):
                _fits.fail("F-16", f"/{source}#{HDU_NAME}/{name}[{index}]",
                           f"{name}[{index}] is not finite ({value!r}); §2.8 requires it")

    return Housekeeping(
        source_path=path,
        source_digest=digest,
        mjd=mjd,
        suninfov=tuple(suninfov),
        columns=captured,
        units=units,
        header_tstart=header_tstart,
        header_tstop=header_tstop,
        inversions=inversion_stats(mjd),
        assumptions=assumptions,
    )


def _check_header_span(mjd: tuple[float, ...], header_tstart: float, header_tstop: float,
                       source: str) -> None:
    """§2.8 header-span consistency as amended at r7: bounds widened by `ε_t` only (§5.1)."""
    allowance = TIME_REPRESENTATION_ALLOWANCE_S / SECONDS_PER_DAY
    earliest, latest = min(mjd), max(mjd)
    if earliest < header_tstart - allowance or latest > header_tstop + allowance:
        _fits.fail(
            "F-06", f"/{source}#{HDU_NAME}/mjd",
            f"the mjd range [{earliest!r}, {latest!r}] is not inside the header span "
            f"[{header_tstart!r}, {header_tstop!r}] widened by ε_t = "
            f"{TIME_REPRESENTATION_ALLOWANCE_S} s (§2.8 r7, §5.1)",
        )


def inversion_stats(mjd: tuple[float, ...]) -> InversionStats:
    """Count backward steps and measure the largest. Reported, never compared (§2.8 r4)."""
    backward = 0
    largest = 0.0
    for index in range(1, len(mjd)):
        step = mjd[index] - mjd[index - 1]
        if step < 0:
            backward += 1
            largest = max(largest, -step * SECONDS_PER_DAY)
    return InversionStats(
        rows=len(mjd),
        steps=max(len(mjd) - 1, 0),
        n_out_of_order=backward,
        max_backward_step_s=largest,
    )


__all__ = [
    "A4_ASSUMPTION", "CAPTURED", "DETECTOR_HEALTH", "GAIN_HV", "HDU_NAME", "Housekeeping",
    "InversionStats", "PILEUP", "POINTING", "RATES", "REQUIRED_FINITE", "SATURATION",
    "STATED_UNITS", "THERMAL", "TIME", "inversion_stats", "parse",
]

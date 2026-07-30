"""SoLEXS `.lc.gz` — the total-band count time series.

Implements `SPEC-parsers@r6` §2.1. That section is a contract, not a description: a deviation
requires a logged amendment, not a code change.

THE TWO THINGS THIS PARSER MUST GET RIGHT
------------------------------------------
**The values are counts, not a rate.** The HDU is named `RATE` and the values are counts per
1-second bin. `HDUCLAS3='COUNTS'` is what declares this, and F-07 requires the parser to use
`HDUCLAS3` and **never** `EXTNAME` to decide semantics. Reading the name would divide by a
second that was never applied and publish a number that is right by coincidence of magnitude.

**NaN is data.** §2.1, as amended at r2: *"SoLEXS `COUNTS` uses NaN as the missing-data
sentinel… NaN values represent absent measurements. Zero remains a valid physical count and
MUST NOT be treated as missing."* The binding parser behaviour is that NaN values pass
through **unchanged**, are **never** imputed, **never** converted to zero, **never** removed.

Here that maps exactly onto the domain: `Observation.value = None` means *observed to be
absent* (ADR-0017, L-07), and `0.0` means a measured zero. The mapping is
`NaN → None`, `0.0 → 0.0`, and the two are tested against each other in both directions
because collapsing them is the specific error that would be undetectable downstream.

**Finiteness of `COUNTS` is deliberately NOT validated** (§2.1, r2): NaN is data, not an
error. What *is* validated is `TIME` finiteness — F-16 — because a NaN timestamp defeats a
monotonicity test silently, all NaN comparisons being False.

WHAT THIS PARSER DOES NOT DO
----------------------------
It does not check `NaN ⇒ GTI-excluded`. §2.1 places that at the day-assembly layer, which
needs both `.lc` and `.gti`: *"enforced at the day-assembly layer (Milestone VII), not inside
the single-file `.lc` parser."* It does not aggregate to a minute grid — §3's T1 contract is
the write path's, M3/E5/#19. It reads a clock never; `ingest_time` is supplied by the
acquisition that produced the file.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from contexts.ingest.parsers.solexs import _fits
from domain.entities import Observation
from domain.values import Digest, Identifier, Timestamp

#: Unix epoch as Modified Julian Date. `MJDREFI=40587` is what the archive declares, and
#: F-05 fires on anything else — v1 defaulted 58484 and produced a ~49-year error.
MJDREFI_UNIX = 40587

#: §2.1: one row per second of a UTC day.
EXPECTED_ROWS = 86_400

#: The quantity name is the instrument's own term. `HDUCLAS3` declares COUNTS, and the unit is
#: counts accumulated in one `TIMEDEL` second — not a rate, despite `EXTNAME='RATE'` (F-07).
QUANTITY = "counts"
UNIT = "counts"


@dataclass(frozen=True)
class LightCurveHeader:
    """Every keyword §2.1 lists under "Metadata to capture", read strictly.

    Split across PRIMARY and the `RATE` extension exactly as the archive stores them —
    `OBSERVED` on the 2024-05-14 SDD2 product. Reading a keyword from the wrong header would
    require a fallback, and a fallback is the banned idiom (§5).
    """

    mission: str
    telescope: str
    instrument: str
    origin: str
    creator: str
    filename: str
    obs_date: str
    obs_id: str
    processing_date: str
    detector: str
    tstart: float
    tstop: float
    timedel: float
    numband: str
    rows: int


@dataclass(frozen=True)
class LightCurve:
    """A parsed `.lc` product: its header, and the second-by-second series.

    `counts` holds `None` where the archive holds NaN. The conversion happens once, here, so
    that no downstream consumer can encounter a raw NaN and decide for itself what it meant.
    """

    header: LightCurveHeader
    source_path: Path
    source_digest: Digest
    times: tuple[float, ...]
    counts: tuple[float | None, ...]

    @property
    def n_finite(self) -> int:
        """Seconds carrying a measurement. §2.1 `OBSERVED`: 86,395 on 2024-05-14 SDD2."""
        return sum(1 for value in self.counts if value is not None)

    @property
    def n_absent(self) -> int:
        """Seconds observed to be absent. §2.1 `OBSERVED`: 5 on 2024-05-14 SDD2."""
        return len(self.counts) - self.n_finite

    @property
    def absent_offsets(self) -> tuple[int, ...]:
        """Day-offsets of the absent seconds. §2.1 records [0, 5, 30072, 30078, 83951]."""
        return tuple(i for i, value in enumerate(self.counts) if value is None)

    @property
    def instrument_id(self) -> Identifier:
        """`solexs-sdd2`.

        The detector is part of the instrument identity, not a label on it: SDD1 and SDD2 are
        two physical SDD detectors, and §1.1 records that they carry different products —
        SDD1 supplies GTI only. Collapsing them to `solexs` would make an SDD1 row and an
        SDD2 row indistinguishable (ADR-0003: an Instrument is a sensor).
        """
        return Identifier(f"solexs-{self.header.detector.lower()}")

    def observations(self, *, source_id: Identifier, ingest_time: Timestamp | None
                     ) -> Iterator[Observation]:
        """One Observation per second, streamed (E5 §12).

        A generator, not a list: §2.2 records ~472 MB/day decompressed for the sibling `.pi`
        product and the same discipline applies here — a day must not be materialised twice.

        `ingest_time` is supplied by the acquisition, never read from a clock here. `None` is
        legitimate and means exactly what ADR-0022 says: unknown, predates bitemporal capture.
        """
        for offset, (when, value) in enumerate(zip(self.times, self.counts)):
            yield Observation(
                source_id=source_id,
                instrument_id=self.instrument_id,
                quantity=QUANTITY,
                unit=UNIT,
                valid_time=unix_to_timestamp(when),
                ingest_time=ingest_time,
                value=value,
                source_digest=self.source_digest,
                quality_flags=() if value is not None else ("no_data",),
            )
            del offset


def unix_to_timestamp(seconds: float) -> Timestamp:
    """Unix seconds UTC → a domain Timestamp.

    §2.1 establishes the epoch from the file rather than by assumption: `MJDREFI=40587`,
    `MJDREFF=0` → MJD 40587 = 1970-01-01 = the Unix epoch, with `TIMESYS='UTC'`,
    `TIMEUNIT='s'`, `TIMZERO=0`. Verified there against `TSTART=1715644800.0` =
    2024-05-14T00:00:00Z, and re-verified by this module's tests.
    """
    moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return Timestamp(moment.isoformat().replace("+00:00", "Z"))


def _validate_time_axis(times, source: str) -> None:
    """F-16 and §2.1's validation list, in the order a failure is most diagnostic.

    Finiteness first: a NaN timestamp would defeat the monotonicity check silently, because
    every comparison against NaN is False. §2.1 calls this out explicitly.
    """
    for index, value in enumerate(times):
        if not math.isfinite(value):
            _fits.fail(
                "F-16", f"/{source}#RATE/TIME[{index}]",
                f"TIME[{index}] is not finite ({value!r}). A NaN timestamp defeats the "
                f"monotonicity test silently — every comparison against NaN is False.",
            )
    for index in range(1, len(times)):
        step = times[index] - times[index - 1]
        if step != 1:
            _fits.fail(
                "F-16", f"/{source}#RATE/TIME[{index}]",
                f"TIME step at row {index} is {step!r}s, expected exactly 1s "
                f"(TIMEDEL=1, §2.1)",
            )


def parse(path: Path, digest: Digest) -> LightCurve:
    """Parse one `.lc.gz` product. Every §2.1 validation, no repair.

    `digest` is the content address the kernel minted for these exact bytes (ADR-0005). It is
    carried onto every Observation, so a published number resolves to the file it came from.
    """
    from astropy.io import fits

    source = path.name
    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        primary = _fits.hdu(hdul, "PRIMARY", source=source).header
        rate_hdu = _fits.hdu(hdul, "RATE", source=source)
        rate = rate_hdu.header

        # ── F-07: semantics come from HDUCLAS3, never from EXTNAME ──────────────
        _fits.expect(rate, "HDUCLAS1", "LIGHTCURVE", source=source, hdu_name="RATE", rule="F-07")
        _fits.expect(rate, "HDUCLAS2", "TOTAL", source=source, hdu_name="RATE", rule="F-07")
        _fits.expect(rate, "HDUCLAS3", "COUNTS", source=source, hdu_name="RATE", rule="F-07")

        # ── F-05: the epoch is read, never defaulted ────────────────────────────
        _fits.expect(rate, "MJDREFI", MJDREFI_UNIX, source=source, hdu_name="RATE", rule="F-05")
        _fits.expect(rate, "MJDREFF", 0, source=source, hdu_name="RATE", rule="F-05")
        _fits.expect(rate, "TIMESYS", "UTC", source=source, hdu_name="RATE", rule="F-05")
        _fits.expect(rate, "TIMEUNIT", "s", source=source, hdu_name="RATE", rule="F-05")
        _fits.expect(rate, "TIMZERO", 0, source=source, hdu_name="RATE", rule="F-05")

        timedel = _fits.keyword(rate, "TIMEDEL", source=source, hdu_name="RATE")
        if timedel != 1:
            _fits.fail("F-05", f"/{source}#RATE/TIMEDEL",
                       f"TIMEDEL is {timedel!r}s; §2.1 declares 1s bins")

        rows = _fits.keyword(rate, "NAXIS2", source=source, hdu_name="RATE")
        if rows != EXPECTED_ROWS:
            _fits.fail("F-17", f"/{source}#RATE/NAXIS2",
                       f"NAXIS2 is {rows}, expected {EXPECTED_ROWS} for a SoLEXS daily "
                       f"product — a truncated product must not be parsed as a whole day")

        times = [float(v) for v in _fits.column(rate_hdu, "TIME", source=source, hdu_name="RATE")]
        raw_counts = _fits.column(rate_hdu, "COUNTS", source=source, hdu_name="RATE")

        _validate_time_axis(times, source)

        tstart = float(_fits.keyword(rate, "TSTART", source=source, hdu_name="RATE"))
        if times and tstart != times[0]:
            _fits.fail("F-06", f"/{source}#RATE/TSTART",
                       f"TSTART {tstart!r} does not equal TIME[0] {times[0]!r}")

        # ── NaN passes through as "observed to be absent". Never zero, never dropped ──
        counts: list[float | None] = []
        for index, value in enumerate(raw_counts):
            number = float(value)
            if math.isnan(number):
                counts.append(None)
                continue
            if number < 0:
                # F-19 covers negative counts only, and is inherently NaN-safe because
                # `NaN < 0` is False — which is why this check follows the NaN branch.
                _fits.fail("F-19", f"/{source}#RATE/COUNTS[{index}]",
                           f"COUNTS[{index}] is {number!r}; a negative count is physically "
                           f"impossible")
            counts.append(number)

        detector = _fits.keyword(rate, "FILTER", source=source, hdu_name="RATE")
        instrument = _fits.keyword(primary, "INSTRUME", source=source, hdu_name="PRIMARY")
        if instrument != "SoLEXS":
            _fits.fail("F-07", f"/{source}#PRIMARY/INSTRUME",
                       f"INSTRUME is {instrument!r}, expected 'SoLEXS'")

        header = LightCurveHeader(
            mission=_fits.keyword(primary, "MISSION", source=source, hdu_name="PRIMARY"),
            telescope=_fits.keyword(primary, "TELESCOP", source=source, hdu_name="PRIMARY"),
            instrument=instrument,
            origin=_fits.keyword(primary, "ORIGIN", source=source, hdu_name="PRIMARY"),
            creator=_fits.keyword(primary, "CREATOR", source=source, hdu_name="PRIMARY"),
            filename=_fits.keyword(primary, "FILENAME", source=source, hdu_name="PRIMARY"),
            obs_date=str(_fits.keyword(primary, "OBS_DATE", source=source, hdu_name="PRIMARY")),
            obs_id=str(_fits.keyword(primary, "OBS_ID", source=source, hdu_name="PRIMARY")),
            processing_date=str(
                _fits.keyword(primary, "DATE", source=source, hdu_name="PRIMARY")
            ),
            detector=detector,
            tstart=tstart,
            tstop=float(_fits.keyword(rate, "TSTOP", source=source, hdu_name="RATE")),
            timedel=float(timedel),
            numband=str(_fits.keyword(rate, "NUMBAND", source=source, hdu_name="RATE")),
            rows=int(rows),
        )

    return LightCurve(
        header=header,
        source_path=path,
        source_digest=digest,
        times=tuple(times),
        counts=tuple(counts),
    )


__all__ = [
    "EXPECTED_ROWS",
    "LightCurve",
    "LightCurveHeader",
    "MJDREFI_UNIX",
    "QUANTITY",
    "UNIT",
    "parse",
    "unix_to_timestamp",
]

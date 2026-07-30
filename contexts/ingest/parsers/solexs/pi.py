"""SoLEXS `.pi.gz` — per-second spectra. The scientific core.

Implements `SPEC-parsers@r6` §2.2: OGIP Type II PHA, `DETCHANS=340`, `CHANTYPE='PI'`,
one 340-channel spectrum per second, `NAXIS2 = 86400`.

THE BINDING PROHIBITION
-----------------------
§2.2 states it as a `CRITICAL GAP`, `OBSERVED`:

> **no RMF/ARF response file exists anywhere in the archive.** SoLEXS PI-channel → keV
> conversion is therefore **impossible from archive contents alone**. **Binding rule: no v2
> artifact may state a SoLEXS energy in keV until a response file is acquired.**

`CHANNEL` is an **ordinal PI index, not energy**. This module therefore exposes channel
indices and never an energy, has no keV field, no conversion function and no calibration
constant — and `test_no_energy_is_stated_anywhere` asserts that none appears. The prohibition
is enforced by absence rather than by comment, because a comment is not a constraint.

STREAMING IS A DESIGN REQUIREMENT, NOT A PREFERENCE
----------------------------------------------------
§2.2, marked design-binding: `NAXIS1 = 5468 B × 86400` ≈ **472 MB/day decompressed**, and 436
days ≈ **206 GB**. *"The parser MUST stream day-by-day and MUST NOT hold multiple days of
`COUNTS` in memory (16 GB RAM)."*

So `parse` returns a header-and-validation result, and `spectra()` yields rows lazily from a
freshly opened file. Nothing here accumulates a day's `COUNTS`.

`CHANNEL` IS READ ONCE AND DISCARDED
------------------------------------
§2.2: *"`CHANNEL` is 235 MB/day of pure redundancy — read once, validate constant, discard."*
F-08 fires if the vector is not identical across rows, because a varying channel map voids
the assumption that a channel index means the same thing in every row. The constant map is
kept once, on the parse result.

WHAT THIS PARSER DOES NOT DO
----------------------------
No aggregation — §3's T2 contract belongs to the write path (#19). No merging with any other
channel space: F-11 forbids combining SoLEXS PI(340) with HEL1OS CZT PHA(341) or CdTe
PHA(511), and this module cannot do so because it knows nothing of HEL1OS. The cross-product
check `.pi TSTART[0] == .lc TSTART` (V-PI-3, F-06) is offered as a function taking both, since
a single-file parser cannot perform it alone.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers.solexs import _fits
from contexts.ingest.parsers.solexs.lc import LightCurve, unix_to_timestamp
from domain.values import Digest, Identifier, Timestamp

#: §2.2, `OBSERVED`. Not a configurable expectation: a product declaring a different channel
#: count is a different product, and F-11 forbids treating two channel spaces as one.
DETCHANS = 340

#: One spectrum per second of a UTC day.
EXPECTED_ROWS = 86_400


@dataclass(frozen=True)
class Spectrum:
    """One second's 340-channel spectrum.

    `counts` is per-channel counts accumulated over `exposure` seconds. Channels are ordinal
    PI indices; the class carries no energy and there is nowhere to put one.
    """

    tstart: float
    telapse: float
    spec_num: int
    exposure: float
    counts: tuple[float, ...]

    @property
    def valid_time(self) -> Timestamp:
        return unix_to_timestamp(self.tstart)

    @property
    def total_counts(self) -> float:
        return math.fsum(self.counts)


@dataclass(frozen=True)
class SpectraHeader:
    """The OGIP Type II PHA declarations §2.2 requires, read strictly."""

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
    detchans: int
    chantype: str
    poisserr: bool
    areascal: float
    corrscal: float
    rows: int


@dataclass(frozen=True)
class Spectra:
    """A validated `.pi` product. Rows are streamed, never held.

    `channel_map` is the constant ordinal channel vector, validated once (F-08) and kept once
    rather than 86,400 times.
    """

    header: SpectraHeader
    source_path: Path
    source_digest: Digest
    channel_map: tuple[int, ...]
    first_tstart: float

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"solexs-{self.header.detector.lower()}")

    def spectra(self) -> Iterator[Spectrum]:
        """Yield each second's spectrum, one at a time, from a freshly opened file.

        A generator over a re-opened file rather than a retained handle: §2.2's memory
        constraint is about a day never being materialised, and a consumer that abandons the
        iteration should not leave a 472 MB mapping alive.
        """
        from astropy.io import fits

        source = self.source_path.name
        with fits.open(self.source_path) as hdul:
            table = _fits.hdu(hdul, "SPECTRUM", source=source)
            tstarts = _fits.column(table, "TSTART", source=source, hdu_name="SPECTRUM")
            telapses = _fits.column(table, "TELAPSE", source=source, hdu_name="SPECTRUM")
            spec_nums = _fits.column(table, "SPEC_NUM", source=source, hdu_name="SPECTRUM")
            exposures = _fits.column(table, "EXPOSURE", source=source, hdu_name="SPECTRUM")
            counts = _fits.column(table, "COUNTS", source=source, hdu_name="SPECTRUM")

            for index in range(len(tstarts)):
                row = tuple(float(v) for v in counts[index])
                for channel, value in enumerate(row):
                    if value < 0:
                        _fits.fail(
                            "F-19",
                            f"/{source}#SPECTRUM/COUNTS[{index}][{channel}]",
                            f"count {value!r} is negative, which is physically impossible",
                        )
                yield Spectrum(
                    tstart=float(tstarts[index]),
                    telapse=float(telapses[index]),
                    spec_num=int(spec_nums[index]),
                    exposure=float(exposures[index]),
                    counts=row,
                )


def parse(path: Path, digest: Digest) -> Spectra:
    """Validate one `.pi.gz` product and capture its constant channel map.

    The row data is **not** read here. §2.2 makes streaming design-binding, and a `parse` that
    returned 86,400 spectra would have already violated it before any caller could choose.
    """
    from astropy.io import fits

    source = path.name
    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        primary = _fits.hdu(hdul, "PRIMARY", source=source).header
        table = _fits.hdu(hdul, "SPECTRUM", source=source)
        spectrum = table.header

        # ── OGIP Type II PHA, declared not assumed (§2.2) ───────────────────────
        _fits.expect(spectrum, "HDUCLAS1", "SPECTRUM", source=source,
                     hdu_name="SPECTRUM", rule="F-07")
        _fits.expect(spectrum, "HDUCLAS3", "COUNTS", source=source,
                     hdu_name="SPECTRUM", rule="F-07")
        _fits.expect(spectrum, "HDUCLAS4", "TYPE:II", source=source,
                     hdu_name="SPECTRUM", rule="F-07")
        _fits.expect(spectrum, "CHANTYPE", "PI", source=source,
                     hdu_name="SPECTRUM", rule="F-07")

        detchans = int(_fits.keyword(spectrum, "DETCHANS", source=source,
                                     hdu_name="SPECTRUM"))
        if detchans != DETCHANS:
            _fits.fail(
                "F-11", f"/{source}#SPECTRUM/DETCHANS",
                f"DETCHANS is {detchans}, expected {DETCHANS}. A different channel count is "
                f"a different channel space, and F-11 forbids treating two as one.",
            )

        # Channel space before row count, deliberately. A product declaring 341 channels is
        # a different channel space (F-11) whether or not it also has the right number of
        # rows, and reporting the completeness defect first would name the less specific
        # problem. Both checks run; only the order of reporting is chosen.
        channel_column = _fits.column(table, "CHANNEL", source=source, hdu_name="SPECTRUM")
        channel_map = _constant_channel_map(channel_column, detchans, source)

        rows = int(_fits.keyword(spectrum, "NAXIS2", source=source, hdu_name="SPECTRUM"))
        if rows != EXPECTED_ROWS:
            _fits.fail("F-17", f"/{source}#SPECTRUM/NAXIS2",
                       f"NAXIS2 is {rows}, expected {EXPECTED_ROWS}")

        tstarts = _fits.column(table, "TSTART", source=source, hdu_name="SPECTRUM")
        first_tstart = float(tstarts[0])

        exposures = _fits.column(table, "EXPOSURE", source=source, hdu_name="SPECTRUM")
        for index, value in enumerate(exposures):
            if float(value) < 0:
                _fits.fail("F-19", f"/{source}#SPECTRUM/EXPOSURE[{index}]",
                           f"EXPOSURE[{index}] is {float(value)!r}; a negative exposure is "
                           f"physically impossible")

        instrument = _fits.keyword(primary, "INSTRUME", source=source, hdu_name="PRIMARY")
        if instrument != "SoLEXS":
            _fits.fail("F-07", f"/{source}#PRIMARY/INSTRUME",
                       f"INSTRUME is {instrument!r}, expected 'SoLEXS'")

        header = SpectraHeader(
            mission=_fits.keyword(primary, "MISSION", source=source, hdu_name="PRIMARY"),
            telescope=_fits.keyword(primary, "TELESCOP", source=source, hdu_name="PRIMARY"),
            instrument=instrument,
            origin=_fits.keyword(primary, "ORIGIN", source=source, hdu_name="PRIMARY"),
            creator=_fits.keyword(primary, "CREATOR", source=source, hdu_name="PRIMARY"),
            filename=_fits.keyword(primary, "FILENAME", source=source, hdu_name="PRIMARY"),
            obs_date=str(_fits.keyword(primary, "OBS_DATE", source=source,
                                       hdu_name="PRIMARY")),
            obs_id=str(_fits.keyword(primary, "OBS_ID", source=source, hdu_name="PRIMARY")),
            processing_date=str(_fits.keyword(primary, "DATE", source=source,
                                              hdu_name="PRIMARY")),
            detector=_fits.keyword(spectrum, "FILTER", source=source, hdu_name="SPECTRUM"),
            detchans=detchans,
            chantype="PI",
            poisserr=bool(_fits.keyword(spectrum, "POISSERR", source=source,
                                        hdu_name="SPECTRUM")),
            areascal=float(_fits.keyword(spectrum, "AREASCAL", source=source,
                                         hdu_name="SPECTRUM")),
            corrscal=float(_fits.keyword(spectrum, "CORRSCAL", source=source,
                                         hdu_name="SPECTRUM")),
            rows=rows,
        )

    return Spectra(
        header=header,
        source_path=path,
        source_digest=digest,
        channel_map=channel_map,
        first_tstart=first_tstart,
    )


def _constant_channel_map(column, detchans: int, source: str) -> tuple[int, ...]:
    """F-08: every row's CHANNEL vector must be identical.

    Read once and discarded (§2.2 — 235 MB/day of pure redundancy). A varying map would void
    the assumption that channel *n* means the same thing in every row, which is the
    assumption every downstream spectral operation rests on.
    """
    first = tuple(int(v) for v in column[0])
    if len(first) != detchans:
        _fits.fail("F-08", f"/{source}#SPECTRUM/CHANNEL[0]",
                   f"CHANNEL vector has {len(first)} entries, DETCHANS declares {detchans}")

    for index in range(1, len(column)):
        if tuple(int(v) for v in column[index]) != first:
            _fits.fail(
                "F-08", f"/{source}#SPECTRUM/CHANNEL[{index}]",
                f"CHANNEL vector at row {index} differs from row 0. The channel map must be "
                f"constant, or a channel index does not mean the same thing in every row.",
            )
    return first


def check_epoch_agrees_with_lightcurve(spectra: Spectra, lightcurve: LightCurve) -> None:
    """V-PI-3 / F-06: `.pi TSTART[0]` must equal the `.lc` `TSTART` for the same day.

    A cross-product check, so it takes both products rather than living inside either parser
    — the same placement §2.1 uses for the `NaN ⇒ GTI-excluded` implication. Two products of
    one day disagreeing about when the day began is an ambiguous time, and §5 admits no
    ambiguous time.
    """
    if spectra.first_tstart != lightcurve.header.tstart:
        _fits.fail(
            "F-06", f"/{spectra.source_path.name}#SPECTRUM/TSTART[0]",
            f".pi TSTART[0] is {spectra.first_tstart!r} but .lc TSTART is "
            f"{lightcurve.header.tstart!r} for the same day. V-PI-3 requires equality.",
        )


__all__ = [
    "DETCHANS",
    "EXPECTED_ROWS",
    "Spectra",
    "SpectraHeader",
    "Spectrum",
    "check_epoch_agrees_with_lightcurve",
    "parse",
]

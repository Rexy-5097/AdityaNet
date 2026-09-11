"""HEL1OS `hel1os_{czt,cdte}_spectra_{det}.fits` — per-detector PHA spectra. §2.7.

TWO CHANNEL SPACES, VALIDATED AGAINST A FAMILY-SPECIFIC ALLOWLIST
------------------------------------------------------------------
§2.7 as amended at r5: HEL1OS has **two detector families with different PHA channel
spaces**, and `DETCHANS` is validated against a family allowlist, *"never a single scalar"*.

    CZT  (czt1, czt2)   DETCHANS 341   CHANTYPE PHA
    CdTe (cdte1, cdte2) DETCHANS 511   CHANTYPE PHA

An unlisted `(family, DETCHANS)` pair terminates via **F-07**, exactly as an unlisted band
terminates via F-10.

And a third space exists one module away: SoLEXS is **340 PI** channels at 1 s (§2.2).
§2.7 is explicit — *"`PI ≠ PHA` (gain-corrected vs raw pulse height) and 340 ≠ 341. No v2
code may treat these as a common channel space (F-11)."* This module cannot merge them
because it knows nothing of SoLEXS, and a test asserts the three counts stay distinct.

EPOCH RESOLUTION R-1 (§2.7, AMENDED r4 AND r7)
-----------------------------------------------
The r0 framing read the conflict between column `unit='s'` and header `TSTART`-as-MJD as an
*epoch* ambiguity. It is not. The `unit='s'` declaration is correct, and both metadata
statements are true and **compose**:

    absolute_time = header TSTART (MJD → UTC) + column TSTART (offset seconds)

Three hypotheses are evaluated in order, and **only if all fail does F-06 terminate**:

    H3  relative seconds from header TSTART   col[0] == 0 exactly, and the column span
                                              agrees with the header span within one
                                              EXPOSURE bin + ε_t (r7)
    H1  MJD days                              |col[0] − header TSTART| × 86400 ≤ 1 s
    H2  Unix seconds                          |col[0] − unix(header TSTART)| ≤ 1 s

H3 is tested first because `unit='s'` literally declares seconds. H1 and H2 are retained
because a reprocessed product could legitimately switch to an absolute epoch, and silently
misreading one would be worse than an extra branch.

**The resolved hypothesis and its residual are recorded** on the parse result, as §2.7
requires them to be recorded in T7 provenance — the recording itself is #19's, the
measurement is this parser's.

`col_span` AND THE COMPARISON PRECISION — §2.7 AS AMENDED AT r7
----------------------------------------------------------------
r4 left `col_span` undefined and stated the H3 bound exactly. r7 defines both (CONTRA-007
Defect A):

    col_span    = column TSTOP[last] − column TSTART[0]     the covered interval
    header_span = (header TSTOP − header TSTART) × 86400 s
    accept H3 iff col[0] == 0 exactly and |col_span − header_span| ≤ EXPOSURE + ε_t

`ε_t` is §5.1's time-representation allowance, 1 ms. It absorbs float64 representation and
nothing physical: on the reference orbit `(61017.49963590554 − 61017.0000988685) × 86400`
evaluates to `43160.00000007916`, 79 ns over an exact one-bin bound, and on other valid products
the excess reaches about a microsecond. A genuine disagreement is at least a further 20 s bin,
and a two-bin disagreement fails by a wide margin. The value is the contract's, not this
module's — an allowance chosen here would be the silent tolerance r7 exists to rule out.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers import _fits
from contexts.ingest.parsers.hel1os.lc import (
    MJD_UNIX_EPOCH,
    SECONDS_PER_DAY,
    TIME_REPRESENTATION_ALLOWANCE_S,
    mjd_to_timestamp,
)
from contexts.ingest.parsers.hel1os.orbit import family_of
from domain.values import Digest, Identifier, Timestamp

#: §2.7 r5's family allowlist. Never a single scalar.
DETCHANS_BY_FAMILY: dict[str, int] = {"czt": 341, "cdte": 511}

#: The three incommensurable channel spaces F-11 names, kept here so a test can assert they
#: stay distinct. SoLEXS's 340 is stated as a number, not imported: importing it would create
#: the very coupling between channel spaces the rule forbids.
INCOMMENSURABLE_CHANNEL_SPACES = {
    ("solexs", "PI"): 340,
    ("czt", "PHA"): 341,
    ("cdte", "PHA"): 511,
}

CHANTYPE = "PHA"
#: §2.7 `OBSERVED`: `HDUCLAS3='COUNT'` — singular, unlike SoLEXS's `'COUNTS'`.
HDUCLAS3 = "COUNT"


@dataclass(frozen=True)
class EpochResolution:
    """The outcome of R-1, recorded rather than assumed (§2.7)."""

    hypothesis: str
    residual_s: float
    header_tstart_mjd: float
    exposure_s: float

    def absolute_time(self, column_tstart: float) -> Timestamp:
        """Compose the resolved offset onto the header epoch."""
        if self.hypothesis == "H3":
            return mjd_to_timestamp(
                self.header_tstart_mjd + column_tstart / SECONDS_PER_DAY
            )
        if self.hypothesis == "H1":
            return mjd_to_timestamp(column_tstart)
        return mjd_to_timestamp(MJD_UNIX_EPOCH + column_tstart / SECONDS_PER_DAY)


@dataclass(frozen=True)
class Spectrum:
    """One ~20-second PHA spectrum."""

    spec_num: int
    tstart: float
    tstop: float
    exposure: float
    counts: tuple[float, ...]
    stat_err: tuple[float, ...]
    valid_time: Timestamp

    @property
    def total_counts(self) -> float:
        return math.fsum(self.counts)


@dataclass(frozen=True)
class SpectraHeader:
    detector: str
    family: str
    detchans: int
    chantype: str
    hduclas3: str
    tstart_mjd: float
    tstop_mjd: float
    rows: int


@dataclass(frozen=True)
class Spectra:
    """A validated spectra product. Rows are streamed, never held."""

    header: SpectraHeader
    source_path: Path
    source_digest: Digest
    channel_map: tuple[int, ...]
    epoch: EpochResolution

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"hel1os-{self.header.detector.lower()}")

    def spectra(self) -> Iterator[Spectrum]:
        """Yield each spectrum lazily from a freshly opened file (E5 §12)."""
        from astropy.io import fits

        source = self.source_path.name
        with fits.open(self.source_path) as hdul:
            table = _fits.hdu(hdul, "SPECTRUM", source=source)
            spec_nums = _fits.column(table, "SPEC_NUM", source=source, hdu_name="SPECTRUM")
            tstarts = _fits.column(table, "TSTART", source=source, hdu_name="SPECTRUM")
            tstops = _fits.column(table, "TSTOP", source=source, hdu_name="SPECTRUM")
            exposures = _fits.column(table, "EXPOSURE", source=source, hdu_name="SPECTRUM")
            counts = _fits.column(table, "COUNTS", source=source, hdu_name="SPECTRUM")
            errors = _fits.column(table, "STAT_ERR", source=source, hdu_name="SPECTRUM")

            for index in range(len(tstarts)):
                row = tuple(float(v) for v in counts[index])
                for channel, value in enumerate(row):
                    if value < 0:
                        _fits.fail(
                            "F-19", f"/{source}#SPECTRUM/COUNTS[{index}][{channel}]",
                            f"count {value!r} is negative, which is physically impossible",
                        )
                exposure = float(exposures[index])
                if exposure < 0:
                    _fits.fail("F-19", f"/{source}#SPECTRUM/EXPOSURE[{index}]",
                               f"EXPOSURE[{index}] is {exposure!r}")
                yield Spectrum(
                    spec_num=int(spec_nums[index]),
                    tstart=float(tstarts[index]),
                    tstop=float(tstops[index]),
                    exposure=exposure,
                    counts=row,
                    stat_err=tuple(float(v) for v in errors[index]),
                    valid_time=self.epoch.absolute_time(float(tstarts[index])),
                )


def resolve_epoch(column_tstart, column_tstop, exposures, header_tstart: float,
                  header_tstop: float, source: str) -> EpochResolution:
    """R-1, in the order §2.7 mandates. F-06 only if all three hypotheses fail."""
    first = float(column_tstart[0])
    exposure = float(exposures[0])
    header_span = (header_tstop - header_tstart) * SECONDS_PER_DAY

    # ── H3: relative seconds from the header epoch (the observed convention) ─────
    # §2.7 r7: col_span runs from the first bin's start to the last bin's end, and the one-bin
    # bound carries §5.1's ε_t — representation, never physics (CONTRA-007 Defect A).
    column_span = float(column_tstop[-1]) - first
    residual = abs(column_span - header_span)
    if first == 0.0 and residual <= exposure + TIME_REPRESENTATION_ALLOWANCE_S:
        return EpochResolution("H3", residual, header_tstart, exposure)

    # ── H1: MJD days ────────────────────────────────────────────────────────────
    h1_residual = abs(first - header_tstart) * SECONDS_PER_DAY
    if h1_residual <= 1.0:
        return EpochResolution("H1", h1_residual, header_tstart, exposure)

    # ── H2: Unix seconds ────────────────────────────────────────────────────────
    header_unix = (header_tstart - MJD_UNIX_EPOCH) * SECONDS_PER_DAY
    h2_residual = abs(first - header_unix)
    if h2_residual <= 1.0:
        return EpochResolution("H2", h2_residual, header_tstart, exposure)

    _fits.fail(
        "F-06", f"/{source}#SPECTRUM/TSTART[0]",
        f"epoch resolution R-1 failed for all three hypotheses. column TSTART[0]={first!r}, "
        f"header TSTART={header_tstart!r} MJD, column span={column_span!r}s, header "
        f"span={header_span!r}s, EXPOSURE={exposure!r}s. H3 residual={residual!r}s, "
        f"H1={h1_residual!r}s, H2={h2_residual!r}s. §5 admits no ambiguous time.",
    )


def parse(path: Path, digest: Digest, *, detector: str) -> Spectra:
    """Validate one spectra product and resolve its epoch. Row data is not read here."""
    from astropy.io import fits

    source = path.name
    family = family_of(detector)
    expected_detchans = DETCHANS_BY_FAMILY[family]

    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    with opened as hdul:
        table = _fits.hdu(hdul, "SPECTRUM", source=source)
        header = table.header

        _fits.expect(header, "CHANTYPE", CHANTYPE, source=source,
                     hdu_name="SPECTRUM", rule="F-07")
        _fits.expect(header, "HDUCLAS3", HDUCLAS3, source=source,
                     hdu_name="SPECTRUM", rule="F-07")

        detchans = int(_fits.keyword(header, "DETCHANS", source=source,
                                     hdu_name="SPECTRUM"))
        if detchans != expected_detchans:
            _fits.fail(
                "F-07", f"/{source}#SPECTRUM/DETCHANS",
                f"DETCHANS is {detchans} for family {family!r}, which the §2.7 r5 allowlist "
                f"gives as {expected_detchans}. An unlisted (family, DETCHANS) pair "
                f"terminates: {DETCHANS_BY_FAMILY}",
            )

        channel_column = _fits.column(table, "CHANNEL", source=source, hdu_name="SPECTRUM")
        channel_map = _constant_channel_map(channel_column, detchans, source)

        tstart_mjd = float(_fits.keyword(header, "TSTART", source=source,
                                         hdu_name="SPECTRUM"))
        tstop_mjd = float(_fits.keyword(header, "TSTOP", source=source,
                                        hdu_name="SPECTRUM"))
        rows = int(_fits.keyword(header, "NAXIS2", source=source, hdu_name="SPECTRUM"))

        epoch = resolve_epoch(
            _fits.column(table, "TSTART", source=source, hdu_name="SPECTRUM"),
            _fits.column(table, "TSTOP", source=source, hdu_name="SPECTRUM"),
            _fits.column(table, "EXPOSURE", source=source, hdu_name="SPECTRUM"),
            tstart_mjd, tstop_mjd, source,
        )

        built = SpectraHeader(
            detector=detector,
            family=family,
            detchans=detchans,
            chantype=CHANTYPE,
            hduclas3=HDUCLAS3,
            tstart_mjd=tstart_mjd,
            tstop_mjd=tstop_mjd,
            rows=rows,
        )

    return Spectra(
        header=built,
        source_path=path,
        source_digest=digest,
        channel_map=channel_map,
        epoch=epoch,
    )


def _constant_channel_map(column, detchans: int, source: str) -> tuple[int, ...]:
    """F-08: the CHANNEL vector must be identical across rows.

    Same rule as SoLEXS §2.2, and the reason is the same: a varying map means a channel index
    does not mean the same thing in every row. The two are checked separately in separate
    modules, because sharing the check would require sharing a channel space.
    """
    first = tuple(int(v) for v in column[0])
    if len(first) != detchans:
        _fits.fail("F-08", f"/{source}#SPECTRUM/CHANNEL[0]",
                   f"CHANNEL vector has {len(first)} entries, DETCHANS declares {detchans}")
    for index in range(1, len(column)):
        if tuple(int(v) for v in column[index]) != first:
            _fits.fail("F-08", f"/{source}#SPECTRUM/CHANNEL[{index}]",
                       f"CHANNEL vector at row {index} differs from row 0")
    return first


__all__ = [
    "CHANTYPE",
    "DETCHANS_BY_FAMILY",
    "EpochResolution",
    "HDUCLAS3",
    "INCOMMENSURABLE_CHANNEL_SPACES",
    "Spectra",
    "SpectraHeader",
    "Spectrum",
    "parse",
    "resolve_epoch",
]

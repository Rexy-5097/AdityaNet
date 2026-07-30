"""FITS fixtures with the layouts `SPEC-parsers@r6` §2.1–§2.3 record.

Real FITS files, written by astropy, carrying the headers and columns the archive carries —
built so the parsers can be exercised without the 3.5 GB corpus, and so a *violating* product
can be constructed deliberately. The archive contains no malformed product to test against,
and a fail-loud rule nobody has watched fire is a comment.

Every default here is a value `OBSERVED` in the spec, not a plausible-looking invention:
`MJDREFI=40587`, `TIMEDEL=1`, `NAXIS2=86400`, `DETCHANS=340`, `CHANTYPE='PI'`,
`HDUCLAS3='COUNTS'`, `FILTER='SDD2'`, and the 2024-05-14 epoch `TSTART=1715644800.0`.

The fixtures are deliberately **short** by default — 60 seconds rather than 86,400 — because
a test that writes a full day writes 472 MB for `.pi`. Where a test needs the real row count
it asks for it, and where it needs to prove the row-count check fires it asks for a wrong one.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from astropy.io import fits

#: 2024-05-14T00:00:00Z — the epoch §2.1 verifies `TSTART` against.
FLARE_DAY_TSTART = 1_715_644_800.0

#: §2.1 `OBSERVED` on 2024-05-14 SDD2: NaN at these day-offsets, identical to the
#: GTI-excluded set. Reproduced here so a fixture can carry the same shape at small scale.
ABSENT_OFFSETS = (0, 5, 30_072, 30_078, 83_951)


def primary(**overrides):
    """The PRIMARY header, with every keyword §2.1 lists under "Metadata to capture"."""
    header = fits.Header()
    values = {
        "MISSION": "ADITYA-L1", "TELESCOP": "AL1", "INSTRUME": "SoLEXS",
        "ORIGIN": "ISSDC", "CREATOR": "solexs_pipeline-1.4",
        "FILENAME": "AL1_SOLEXS_20240514_SDD2_L1.lc", "OBS_DATE": "2024-05-14",
        "OBS_ID": "AL1_SLX_L1_20240514", "DATE": "2024-06-16",
    }
    values.update(overrides)
    for key, value in values.items():
        if value is not None:
            header[key] = value
    return header


def write_lc(path: Path, *, rows: int = 86_400, tstart: float = FLARE_DAY_TSTART,
             counts: list[float] | None = None, times: list[float] | None = None,
             rate_overrides: dict | None = None,
             primary_overrides: dict | None = None,
             extname: str = "RATE") -> Path:
    """A `.lc` product per §2.1."""
    if times is None:
        times = [tstart + i for i in range(rows)]
    if counts is None:
        counts = [100.0 + i for i in range(rows)]

    table = fits.BinTableHDU.from_columns([
        fits.Column(name="TIME", format="D", array=np.array(times, dtype=float)),
        fits.Column(name="COUNTS", format="D", array=np.array(counts, dtype=float)),
    ], name=extname)

    header = table.header
    for key, value in {
        "HDUCLAS1": "LIGHTCURVE", "HDUCLAS2": "TOTAL", "HDUCLAS3": "COUNTS",
        "MJDREFI": 40587, "MJDREFF": 0, "TIMESYS": "UTC", "TIMEUNIT": "s",
        "TIMEDEL": 1, "TIMZERO": 0, "TSTART": tstart,
        "TSTOP": tstart + rows - 1, "FILTER": "SDD2", "NUMBAND": "4",
    }.items():
        header[key] = value
    for key, value in (rate_overrides or {}).items():
        if value is None:
            del header[key]
        else:
            header[key] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([
        fits.PrimaryHDU(header=primary(**(primary_overrides or {}))), table,
    ]).writeto(path, overwrite=True)
    return path


def write_gti(path: Path, *, intervals: list[tuple[float, float]] | None = None,
              exposure: str | float | None = None,
              tstart: str = "2024-05-14T00:00:00+00:00",
              tstop: str = "2024-05-14T23:59:59+00:00",
              gti_overrides: dict | None = None) -> Path:
    """A `.gti` product per §2.3, with `EXPOSURE` as the string the archive stores.

    `exposure` defaults to `Σ(STOP−START+1)`, the inclusive convention amended at r1, so a
    fixture is F-09-consistent unless a test deliberately makes it otherwise.
    """
    if intervals is None:
        intervals = [(FLARE_DAY_TSTART + 1, FLARE_DAY_TSTART + 86_399)]
    if exposure is None:
        exposure = str(float(sum(stop - start + 1 for start, stop in intervals)))

    starts = np.array([a for a, _ in intervals], dtype=float)
    stops = np.array([b for _, b in intervals], dtype=float)
    table = fits.BinTableHDU.from_columns([
        fits.Column(name="START", format="D", array=starts),
        fits.Column(name="STOP", format="D", array=stops),
    ], name="GTI")
    if exposure is not None:
        table.header["EXPOSURE"] = exposure
    for key, value in (gti_overrides or {}).items():
        if value is None:
            del table.header[key]
        else:
            table.header[key] = value

    head = primary(FILENAME="AL1_SOLEXS_20240514_SDD2_L1.gti")
    if tstart is not None:
        head["TSTART"] = tstart
    if tstop is not None:
        head["TSTOP"] = tstop

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(header=head), table]).writeto(path, overwrite=True)
    return path


def write_pi(path: Path, *, rows: int = 60, detchans: int = 340,
             tstart: float = FLARE_DAY_TSTART,
             channel_map: list[list[int]] | None = None,
             counts: np.ndarray | None = None,
             exposures: list[float] | None = None,
             spectrum_overrides: dict | None = None) -> Path:
    """A `.pi` product per §2.2 — OGIP Type II PHA."""
    if channel_map is None:
        channel_map = [list(range(detchans))] * rows
    if counts is None:
        counts = np.tile(np.arange(detchans, dtype=float), (rows, 1))
    if exposures is None:
        exposures = [1.0] * rows

    table = fits.BinTableHDU.from_columns([
        fits.Column(name="TSTART", format="D", unit="s",
                    array=np.array([tstart + i for i in range(rows)], dtype=float)),
        fits.Column(name="TELAPSE", format="D", unit="s",
                    array=np.ones(rows, dtype=float)),
        fits.Column(name="SPEC_NUM", format="J", array=np.arange(rows, dtype=np.int32)),
        fits.Column(name="CHANNEL", format=f"{detchans}K",
                    array=np.array(channel_map, dtype=np.int64)),
        fits.Column(name="COUNTS", format=f"{detchans}D", array=counts),
        fits.Column(name="EXPOSURE", format="D", unit="s",
                    array=np.array(exposures, dtype=float)),
    ], name="SPECTRUM")

    header = table.header
    for key, value in {
        "HDUCLAS1": "SPECTRUM", "HDUCLAS2": "TOTAL", "HDUCLAS3": "COUNTS",
        "HDUCLAS4": "TYPE:II", "CHANTYPE": "PI", "DETCHANS": detchans,
        "POISSERR": False, "AREASCAL": 1.0, "CORRSCAL": 1.0, "FILTER": "SDD2",
    }.items():
        header[key] = value
    for key, value in (spectrum_overrides or {}).items():
        if value is None:
            del header[key]
        else:
            header[key] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([
        fits.PrimaryHDU(header=primary(FILENAME="AL1_SOLEXS_20240514_SDD2_L1.pi")), table,
    ]).writeto(path, overwrite=True)
    return path


def sdd2(root: Path) -> Path:
    directory = root / "AL1_SLX_L1_20240514_v1.0" / "AL1_SLX_L1_20240514_v1.0" / "SDD2"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sdd1(root: Path) -> Path:
    directory = root / "AL1_SLX_L1_20240514_v1.0" / "AL1_SLX_L1_20240514_v1.0" / "SDD1"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def nan_at(rows: int, offsets: tuple[int, ...]) -> list[float]:
    """Counts with NaN at the given offsets — the archive's missing-data sentinel (§2.1 r2).

    Zero appears deliberately at an offset that is *not* absent, so any test asserting on
    absence also has a measured zero present to be confused with.
    """
    values = [float(i) for i in range(rows)]
    values[1] = 0.0
    for offset in offsets:
        if offset < rows:
            values[offset] = math.nan
    return values

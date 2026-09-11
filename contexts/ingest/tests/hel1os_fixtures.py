"""FITS fixtures with the layouts `SPEC-parsers@r7` §2.5–§2.9 record.

Real FITS written by astropy, carrying the headers, EXTNAMEs, column names and declared units
the archive carries — so the parsers can be exercised without the 132 GB corpus, and so a
*violating* product can be built deliberately. A fail-loud rule nobody has watched fire is a
comment.

Every default is a value `OBSERVED` in the spec or in the archive: `TSTART = 61017.0000988685`
(2025-12-08), `EXPOSURE = 20.0` s, `DETCHANS` 341 for CZT and 511 for CdTe, `CHANTYPE='PHA'`,
`HDUCLAS3='COUNT'` (singular), band EXTNAMEs of the `<DET>_LC_BAND_<lo>KEV_TO_<hi>KEV` form,
`CTR` declared `cts/sec`, lowercase `tstart`/`tstop` in the GTI products, the housekeeping
columns and units of §2.8, and `utc-isot` strings rounded to the millisecond.

Row counts are small by default. None of the real counts is validated against a fixed
expectation by any HEL1OS rule, unlike SoLEXS's F-17, so a short fixture exercises the same
code paths.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits

#: 2025-12-08T00:00:08.5Z — the reference orbit's start (§2.5, §2.7 `OBSERVED`).
TSTART_MJD = 61017.0000988685
EXPOSURE_S = 20.0
SECONDS_PER_DAY = 86_400.0

CZT_BANDS = ((20.0, 40.0), (40.0, 60.0), (60.0, 80.0), (80.0, 150.0), (18.0, 160.0))
CDTE_BANDS = ((5.0, 20.0), (20.0, 30.0), (30.0, 40.0), (40.0, 60.0), (1.8, 90.0))
BANDS = {"czt": CZT_BANDS, "cdte": CDTE_BANDS}
DETCHANS = {"czt": 341, "cdte": 511}

#: §2.8's decisive housekeeping columns: (FITS format, declared unit) as the archive carries them.
HK_COLUMNS: dict[str, tuple[str, str | None]] = {
    "cdte1pilectr": ("K", None), "cdte2pilectr": ("K", None),
    "czt1satctr1": ("K", None), "czt2satctr1": ("K", None),
    "czthvmon": ("D", "V"), "cdtehvmon": ("D", "V"),
    "czt1enth": ("D", "keV"), "czt2enth": ("D", None),
    "cdte1enerthr": ("D", None), "cdte2enerthr": ("D", None),
    "czt1temp": ("D", "degC"), "czt2temp": ("D", "degC"),
    "cdte1temp": ("D", "degC"), "cdte2temp": ("D", "degC"),
    "czt1hotpix": ("K", None), "czt2hotpix": ("K", None),
    "czt1hotpixcnt": ("K", None), "czt2hotpixcnt": ("K", None),
    "czt1hotpixthr": ("K", None), "czt2hotpixthr": ("K", None),
    "czt1hotpixlgcstat": ("K", None), "czt2hotpixlgcstat": ("K", None),
    "czt1bunpxctr": ("K", None), "czt2bunpxctr": ("K", None),
    "fehkstat": ("K", None),
    "czt1ctr": ("D", "c/s"), "czt2ctr": ("D", "c/s"),
    "cdte1ctr": ("D", "c/s"), "cdte2ctr": ("D", "c/s"),
    "sunradeg": ("D", None), "sundecdeg": ("D", None),
    "sun2yawdeg": ("D", None), "sun2rolldeg": ("D", None), "sun2pitchdeg": ("D", None),
    "l0dhobt": ("D", None),
    "l0utcyr": ("J", None), "l0utcmon": ("J", None), "l0utcdy": ("J", None),
    "l0utchr": ("J", None), "l0utcmin": ("J", None), "l0utcsc": ("J", None),
    "l0utcmsc": ("J", None),
}


def band_extname(detector: str, low: float, high: float) -> str:
    return f"{detector.upper()}_LC_BAND_{low:.2f}KEV_TO_{high:.2f}KEV"


def isot_of(mjd: float) -> str:
    """The `utc-isot` string the archive writes for an mjd: the instant to the millisecond."""
    seconds = round((mjd - 40587.0) * SECONDS_PER_DAY, 3)
    moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:23]


def write_lightcurve(path: Path, *, detector: str = "czt1", rows: int = 120,
                     bands: tuple[tuple[float, float], ...] | None = None,
                     rates: dict[tuple[float, float], list[float]] | None = None,
                     mjd: list[float] | None = None,
                     extnames: list[str] | None = None,
                     ctr_unit: str | None = "cts/sec") -> Path:
    """A `lightcurve_<det>.fits` per §2.6: five band HDUs, `MJD`/`ISOT`/`CTR`/`STAT_ERR`."""
    family = "czt" if detector.lower().startswith("czt") else "cdte"
    bands = bands if bands is not None else BANDS[family]
    if mjd is None:
        mjd = [TSTART_MJD + i / SECONDS_PER_DAY for i in range(rows)]

    hdus = [fits.PrimaryHDU()]
    for index, (low, high) in enumerate(bands):
        values = (rates or {}).get((low, high), [10.0 + i for i in range(len(mjd))])
        name = extnames[index] if extnames else band_extname(detector, low, high)
        table = fits.BinTableHDU.from_columns([
            fits.Column(name="MJD", format="D", unit="MJD", array=np.array(mjd, dtype=float)),
            fits.Column(name="ISOT", format="30A", unit="UT",
                        array=np.array(["2025-12-08T00:00:00.0"] * len(mjd))),
            fits.Column(name="CTR", format="D", unit=ctr_unit,
                        array=np.array(values, dtype=float)),
            fits.Column(name="STAT_ERR", format="D", unit="cts/sec",
                        array=np.ones(len(mjd), dtype=float)),
        ], name=name)
        table.header["TSTART"] = TSTART_MJD
        table.header["TSTOP"] = mjd[-1]
        hdus.append(table)

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList(hdus).writeto(path, overwrite=True)
    return path


def write_spectra(path: Path, *, detector: str = "czt1", rows: int = 20,
                  detchans: int | None = None, chantype: str = "PHA",
                  hduclas3: str = "COUNT", col_tstart: list[float] | None = None,
                  channel_map: list[list[int]] | None = None,
                  counts: np.ndarray | None = None,
                  header_tstart: float = TSTART_MJD,
                  header_tstop: float | None = None,
                  overrides: dict | None = None) -> Path:
    """A `hel1os_<fam>_spectra_<det>.fits` per §2.7 — Type II PHA, H3 by construction."""
    family = "czt" if detector.lower().startswith("czt") else "cdte"
    detchans = detchans if detchans is not None else DETCHANS[family]
    if col_tstart is None:
        col_tstart = [i * EXPOSURE_S for i in range(rows)]
    col_tstop = [t + EXPOSURE_S for t in col_tstart]
    if header_tstop is None:
        # One EXPOSURE bin beyond the last bin's end — the relationship §2.7's H3 admits.
        header_tstop = header_tstart + (col_tstop[-1] + EXPOSURE_S) / SECONDS_PER_DAY
    if channel_map is None:
        channel_map = [list(range(detchans))] * rows
    if counts is None:
        counts = np.tile(np.arange(detchans, dtype=float), (rows, 1))

    table = fits.BinTableHDU.from_columns([
        fits.Column(name="SPEC_NUM", format="I", array=np.arange(rows, dtype=np.int16)),
        fits.Column(name="CHANNEL", format=f"{detchans}J",
                    array=np.array(channel_map, dtype=np.int32)),
        fits.Column(name="COUNTS", format=f"{detchans}D", unit="cts", array=counts),
        fits.Column(name="STAT_ERR", format=f"{detchans}D", array=np.ones_like(counts)),
        fits.Column(name="ROWID", format="12A", array=np.array(["r"] * rows)),
        fits.Column(name="TSTART", format="D", unit="s",
                    array=np.array(col_tstart, dtype=float)),
        fits.Column(name="TSTOP", format="D", unit="s",
                    array=np.array(col_tstop, dtype=float)),
        fits.Column(name="EXPOSURE", format="D", unit="s",
                    array=np.full(rows, EXPOSURE_S)),
    ], name="SPECTRUM")

    for key, value in {"CHANTYPE": chantype, "HDUCLAS3": hduclas3, "HDUCLAS4": "TYPE:II",
                       "DETCHANS": detchans, "TSTART": header_tstart,
                       "TSTOP": header_tstop}.items():
        table.header[key] = value
    for key, value in (overrides or {}).items():
        if value is None:
            del table.header[key]
        else:
            table.header[key] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(path, overwrite=True)
    return path


def write_gti(path: Path, *, detector: str = "czt1",
              intervals: list[tuple[float, float]] | None = None) -> Path:
    """A `gti<det>.fits` per §2.9 — LOWERCASE column names, unlike SoLEXS."""
    if intervals is None:
        intervals = [(TSTART_MJD, TSTART_MJD + 0.5)]
    table = fits.BinTableHDU.from_columns([
        fits.Column(name="tstart", format="D",
                    array=np.array([a for a, _ in intervals], dtype=float)),
        fits.Column(name="tstop", format="D",
                    array=np.array([b for _, b in intervals], dtype=float)),
    ], name=f"GTI_{detector.upper()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(path, overwrite=True)
    return path


def write_hk(path: Path, *, mjd: list[float] | None = None,
             suninfov: list[int] | None = None, rows: int = 50,
             header_tstart: float | None = None,
             header_tstop: float | None = None,
             units: dict[str, str | None] | None = None,
             values: dict[str, list] | None = None,
             omit: tuple[str, ...] = ()) -> Path:
    """An `hk.fits` per §2.8 — HDU `HLSHK`, every decisive column, telemetry order preserved."""
    if mjd is None:
        mjd = [TSTART_MJD + i / SECONDS_PER_DAY for i in range(rows)]
    if suninfov is None:
        suninfov = [1] * len(mjd)

    columns = [
        fits.Column(name="mjd", format="D", array=np.array(mjd, dtype=float)),
        fits.Column(name="suninfov", format="I",
                    array=np.array(suninfov, dtype=np.int16)),
    ]
    for name, (form, unit) in HK_COLUMNS.items():
        if name in omit:
            continue
        unit = (units or {}).get(name, unit)
        dtype = np.int64 if form == "K" else (np.int32 if form == "J" else float)
        data = (values or {}).get(name, list(range(len(mjd))))
        columns.append(fits.Column(name=name, format=form, unit=unit,
                                   array=np.array(data, dtype=dtype)))

    table = fits.BinTableHDU.from_columns(columns, name="HLSHK")
    table.header["TSTART"] = header_tstart if header_tstart is not None else min(mjd)
    table.header["TSTOP"] = header_tstop if header_tstop is not None else max(mjd)

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(path, overwrite=True)
    return path


def write_events(path: Path, *, rows: int = 10,
                 detectors: tuple[str, ...] = ("cdte1", "cdte2", "czt1", "czt2"),
                 detnam: dict[str, str] | None = None,
                 energies: list[float] | None = None,
                 mjd: list[float] | None = None,
                 isot: list[str] | None = None,
                 ener_unit: str | None = "keV",
                 omit: tuple[str, ...] = (),
                 header_tstart: float = TSTART_MJD,
                 header_tstop: float = TSTART_MJD + 0.5) -> Path:
    """An `evt.fits` per §2.5 — four detector HDUs, `ener` in keV, CZT `pix`/`offsetchn`."""
    names = {"cdte1": "CDTE1-EVENTS", "cdte2": "CDTE2-EVENTS",
             "czt1": "CZT1-EVENTS", "czt2": "CZT2-EVENTS"}
    default_detnam = {"cdte1": "CdTe1", "cdte2": "CdTe2", "czt1": "CZT1", "czt2": "CZT2"}
    detnam = {**default_detnam, **(detnam or {})}
    if mjd is None:
        mjd = [TSTART_MJD + i / SECONDS_PER_DAY for i in range(rows)]
    rows = len(mjd)
    if energies is None:
        energies = [20.0 + i for i in range(rows)]
    if isot is None:
        isot = [isot_of(value) for value in mjd]

    hdus = [fits.PrimaryHDU()]
    for detector in detectors:
        columns = [
            fits.Column(name="mjd", format="D", array=np.array(mjd, dtype=float)),
            fits.Column(name="hlsobt", format="D", unit="s",
                        array=np.arange(rows, dtype=float)),
            fits.Column(name="currtemp", format="D", unit="degC",
                        array=np.full(rows, 12.0)),
            fits.Column(name="chn", format="I", array=np.arange(rows, dtype=np.int16)),
            fits.Column(name="ener", format="D", unit=ener_unit,
                        array=np.array(energies, dtype=float)),
            fits.Column(name="recnum", format="J", array=np.arange(rows, dtype=np.int32)),
            fits.Column(name="utc-isot", format="23A", array=np.array(isot)),
        ]
        if detector.startswith("czt"):
            columns += [
                fits.Column(name="pix", format="B", array=np.arange(rows, dtype=np.uint8)),
                fits.Column(name="offsetchn", format="I",
                            array=np.arange(rows, dtype=np.int16)),
            ]
        columns = [c for c in columns if c.name not in omit]
        table = fits.BinTableHDU.from_columns(columns, name=names[detector])
        table.header["DETNAM"] = detnam[detector]
        table.header["TSTART"] = header_tstart
        table.header["TSTOP"] = header_tstop
        hdus.append(table)

    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList(hdus).writeto(path, overwrite=True)
    return path

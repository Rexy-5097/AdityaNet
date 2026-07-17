"""
app/v2/parsers/hel1os_base.py — shared HEL1OS foundation (Milestone V).

HEL1OS is structurally UNLIKE SoLEXS and the contract is emphatic that the two
conventions must never be conflated:

  SoLEXS                          HEL1OS
  ------------------------------  ------------------------------------------
  Unix seconds (MJDREFI=40587)    MJD days
  units UNDECLARED                units DECLARED (cts/sec, keV, degC, V)
  UPPERCASE columns START/STOP    lowercase columns tstart/tstop  (-> F-04/A-2)
  340 PI channels                 341 PHA channels                (-> F-11)
  daily products                  orbit products (~2/day)

§2.7 declares a REAL ambiguity that must be resolved empirically, never assumed:
the spectra column `TSTART` declares unit='s' while the header `TSTART` is MJD.
Rule R-1 below tests both hypotheses against the header span and terminates
(F-06) if neither fits.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.v2.models.metadata import FailLoud
from app.v2.parsers.base import require_header

# HLS_<YYYYMMDD>_<HHMMSS>_<DUR>sec_lev1_V<XYZ>
ORBIT_ID = re.compile(
    r"HLS_(?P<date>\d{8})_(?P<start>\d{6})_(?P<dur>\d+)sec_lev1_V(?P<ver>\d{3})",
    re.I)

# §2.6 band allowlist. Edges are PARSED from EXTNAME and validated against this
# set -- never positional, because HDU order is not a contract (F-02/F-10).
BAND_EXTNAME = re.compile(
    r"^(?P<det>CZT\d|CDTE\d)_LC_BAND_(?P<lo>[\d.]+)KEV_TO_(?P<hi>[\d.]+)KEV$", re.I)

EXPECTED_BANDS_KEV: dict[str, tuple[tuple[float, float], ...]] = {
    "CZT":  ((20.0, 40.0), (40.0, 60.0), (60.0, 80.0), (80.0, 150.0), (18.0, 160.0)),
    "CDTE": ((5.0, 20.0), (20.0, 30.0), (30.0, 40.0), (40.0, 60.0), (1.8, 90.0)),
}
N_BANDS = 5

DETECTORS = ("CDTE1", "CDTE2", "CZT1", "CZT2")          # §2.5 F-03
EVENT_HDUS = tuple(f"{d}-EVENTS" for d in DETECTORS)

MJD_UNIX_EPOCH = 40587          # MJD of 1970-01-01 (spec §2.1)
_MJD_TOL_S = 1.0                # R-1 acceptance window


def orbit_id(path: str) -> dict[str, str]:
    m = ORBIT_ID.search(path)
    if not m:
        raise FailLoud("F-18", "path does not contain a HEL1OS orbit id",
                       file=path,
                       expected="HLS_<date>_<HHMMSS>_<dur>sec_lev1_V<xyz>",
                       got=path)
    return m.groupdict()


def detector_family(detnam: str) -> str:
    d = detnam.strip().upper()
    if d.startswith("CZT"):
        return "CZT"
    if d.startswith("CDTE"):
        return "CDTE"
    raise FailLoud("F-07", "unrecognised HEL1OS detector family",
                   expected="CZT{1,2} | CdTe{1,2}", got=detnam)


def mjd_to_utc(mjd: np.ndarray) -> pd.DatetimeIndex:
    """MJD days -> UTC. §2.5/§2.6: HEL1OS canonical time is `mjd`."""
    unix_s = (np.asarray(mjd, dtype=np.float64) - MJD_UNIX_EPOCH) * 86400.0
    return pd.to_datetime(unix_s, unit="s", utc=True)


def parse_band_extname(extname: str, *, file: str | None = None
                       ) -> tuple[str, float, float]:
    """Parse and ALLOWLIST-validate a band EXTNAME (§2.6, F-10).

    An unknown band is never silently ingested: if ISSDC adds or shifts a band,
    we terminate rather than mislabel its energy range.
    """
    m = BAND_EXTNAME.match(extname.strip())
    if not m:
        raise FailLoud("F-10", "band EXTNAME does not match the expected form",
                       file=file, hdu=extname,
                       expected="<DET>_LC_BAND_<lo>KEV_TO_<hi>KEV", got=extname)
    det = m.group("det").upper()
    lo, hi = float(m.group("lo")), float(m.group("hi"))
    fam = detector_family(det)
    if (lo, hi) not in EXPECTED_BANDS_KEV[fam]:
        raise FailLoud("F-10", f"band ({lo}, {hi}) keV is not on the {fam} allowlist",
                       file=file, hdu=extname,
                       expected=EXPECTED_BANDS_KEV[fam], got=(lo, hi))
    if hi <= lo:
        raise FailLoud("F-10", "band upper edge <= lower edge", file=file,
                       hdu=extname, got=(lo, hi))
    return det, lo, hi


@dataclass(frozen=True)
class EpochResolution:
    """Outcome of §2.7 rule R-1. Recorded in T7 provenance."""
    kind: str            # "mjd_days" | "unix_seconds"
    residual_s: float


def resolve_epoch_R1(col_tstart: np.ndarray, hdr_tstart_mjd: float,
                     hdr_tstop_mjd: float, *, file: str, hdu: str
                     ) -> EpochResolution:
    """§2.7 R-1 — resolve the declared TSTART ambiguity EMPIRICALLY.

    The column declares unit='s' but the header TSTART is MJD (e.g. 61017.0).
    The column's epoch is therefore undetermined from metadata alone. Test both
    hypotheses against the header span; accept the one reproducing it to <1 s.
    If neither fits -> F-06, terminate. Never guess.
    """
    col = np.asarray(col_tstart, dtype=np.float64)
    if col.size == 0 or not np.all(np.isfinite(col)):
        raise FailLoud("F-06", "R-1: TSTART column empty or non-finite",
                       file=file, hdu=hdu)

    first = float(col[0])
    hdr_first_unix = (hdr_tstart_mjd - MJD_UNIX_EPOCH) * 86400.0

    # H1: the column is MJD days (same units as the header).
    resid_mjd = abs((first - hdr_tstart_mjd) * 86400.0)
    # H2: the column is Unix seconds (as unit='s' would literally imply).
    resid_unix = abs(first - hdr_first_unix)

    if resid_mjd <= _MJD_TOL_S and resid_mjd <= resid_unix:
        return EpochResolution("mjd_days", resid_mjd)
    if resid_unix <= _MJD_TOL_S:
        return EpochResolution("unix_seconds", resid_unix)

    raise FailLoud(
        "F-06",
        "R-1: TSTART column matches NEITHER the MJD-days nor the Unix-seconds "
        "hypothesis against the header span; the epoch is undetermined",
        file=file, hdu=hdu,
        expected=f"residual <= {_MJD_TOL_S}s under one hypothesis",
        got={"residual_if_mjd_days_s": resid_mjd,
             "residual_if_unix_seconds_s": resid_unix,
             "col_tstart[0]": first, "hdr_TSTART_mjd": hdr_tstart_mjd})


def require_hel1os_primary(primary, *, file: str) -> dict[str, str]:
    """§2.5-§2.9 common primary metadata. Never defaulted."""
    instrume = str(require_header(primary.header, "INSTRUME", file=file)).strip()
    if instrume.upper() != "HEL1OS":
        raise FailLoud("F-07", "INSTRUME is not HEL1OS", file=file,
                       expected="HEL1OS", got=instrume)
    telescop = str(require_header(primary.header, "TELESCOP", file=file)).strip()
    creator = str(require_header(primary.header, "CREATOR", file=file)).strip()
    return {"instrume": instrume, "telescop": telescop, "creator": creator}

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
_MJD_TOL_S = 1.0                # R-1 acceptance window for H1/H2 (absolute epochs)

# IEEE754 slack for the MJD(days) -> seconds conversion. NOT a physical
# tolerance: at MJD ~61017 the float64 ULP is ~7e-12 d ~= 6e-7 s, so a header
# span computed from MJD carries ~1e-7 s of representation noise. 1 ms sits ~3
# orders above that noise and ~4 orders below the smallest EXPOSURE bin (20 s),
# so it can absorb the noise without admitting any physical slack. Required
# because H3's "<= one EXPOSURE bin" comparison lands exactly ON the boundary.
_FLOAT_EPS_S = 1e-3


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
    """Outcome of §2.7 rule R-1 (amended r4). Recorded in T7 provenance."""
    kind: str            # "relative_seconds" | "mjd_days" | "unix_seconds"
    residual_s: float
    origin_mjd: float | None = None      # set for relative_seconds (H3)


def resolve_epoch_R1(col_tstart: np.ndarray, hdr_tstart_mjd: float,
                     hdr_tstop_mjd: float, *, file: str, hdu: str,
                     exposure_s: float | None = None,
                     col_tstop: np.ndarray | None = None) -> EpochResolution:
    """§2.7 R-1 (amended r4) — resolve the TSTART ORIGIN empirically.

    The r0 rule framed this as an EPOCH ambiguity and enumerated only two
    absolute hypotheses; it terminated on real data (CONTRADICTION-004 Defect A).
    The unit='s' declaration was correct all along -- the unknown was the ORIGIN.
    Both metadata statements are true and COMPOSE:

        absolute_time = mjd_to_utc(header TSTART) + column TSTART seconds

    Evaluation order H3 -> H1 -> H2; terminate (F-06) only if ALL fail. H1/H2 are
    retained for future compatibility: a reprocessed product could legitimately
    switch to an absolute epoch, and silently mis-reading it would be far worse
    than carrying an extra branch.
    """
    col = np.asarray(col_tstart, dtype=np.float64)
    if col.size == 0 or not np.all(np.isfinite(col)):
        raise FailLoud("F-06", "R-1: TSTART column empty or non-finite",
                       file=file, hdu=hdu)

    first = float(col[0])
    hdr_span_s = (hdr_tstop_mjd - hdr_tstart_mjd) * 86400.0
    # §2.7 r4 "col_span" is the DATA span: start of the first bin to the END of
    # the last one. Measuring start-to-start would silently omit the final bin's
    # duration and understate the span by exactly one EXPOSURE.
    if col_tstop is not None and np.size(col_tstop):
        col_span_s = float(np.asarray(col_tstop, dtype=np.float64)[-1] - col[0])
    else:
        col_span_s = float(col[-1] - col[0])
    hdr_first_unix = (hdr_tstart_mjd - MJD_UNIX_EPOCH) * 86400.0

    # ── H3: relative seconds from the header TSTART (the observed convention).
    # Tested FIRST because unit='s' literally declares seconds.
    bin_s = float(exposure_s) if exposure_s and np.isfinite(exposure_s) else _MJD_TOL_S
    span_residual = abs(col_span_s - hdr_span_s)
    if first == 0.0 and span_residual <= max(bin_s, _MJD_TOL_S) + _FLOAT_EPS_S:
        return EpochResolution("relative_seconds", span_residual,
                               origin_mjd=hdr_tstart_mjd)

    # ── H1: MJD days (same units as the header).
    resid_mjd = abs((first - hdr_tstart_mjd) * 86400.0)
    if resid_mjd <= _MJD_TOL_S:
        return EpochResolution("mjd_days", resid_mjd)

    # ── H2: Unix seconds.
    resid_unix = abs(first - hdr_first_unix)
    if resid_unix <= _MJD_TOL_S:
        return EpochResolution("unix_seconds", resid_unix)

    raise FailLoud(
        "F-06",
        "R-1: TSTART column matches NONE of H3 (relative seconds), H1 (MJD days) "
        "or H2 (Unix seconds); the origin is undetermined",
        file=file, hdu=hdu,
        expected="one hypothesis to fit (H3 -> H1 -> H2)",
        got={"col_tstart[0]": first,
             "H3_span_residual_s": span_residual,
             "H1_residual_if_mjd_days_s": resid_mjd,
             "H2_residual_if_unix_seconds_s": resid_unix,
             "hdr_TSTART_mjd": hdr_tstart_mjd, "hdr_span_s": hdr_span_s})


def absolute_time_from_R1(col_tstart: np.ndarray, epoch: EpochResolution
                          ) -> pd.DatetimeIndex:
    """§2.7 r4 composition rule: absolute = header TSTART + column offset."""
    col = np.asarray(col_tstart, dtype=np.float64)
    if epoch.kind == "relative_seconds":
        origin_unix = (epoch.origin_mjd - MJD_UNIX_EPOCH) * 86400.0
        return pd.to_datetime(origin_unix + col, unit="s", utc=True)
    if epoch.kind == "mjd_days":
        return mjd_to_utc(col)
    if epoch.kind == "unix_seconds":
        return pd.to_datetime(col, unit="s", utc=True)
    raise FailLoud("F-06", f"unknown R-1 resolution {epoch.kind!r}")


def require_hel1os_primary(primary, *, file: str) -> dict[str, str]:
    """§2.5-§2.9 common primary metadata. Never defaulted."""
    instrume = str(require_header(primary.header, "INSTRUME", file=file)).strip()
    if instrume.upper() != "HEL1OS":
        raise FailLoud("F-07", "INSTRUME is not HEL1OS", file=file,
                       expected="HEL1OS", got=instrume)
    telescop = str(require_header(primary.header, "TELESCOP", file=file)).strip()
    creator = str(require_header(primary.header, "CREATOR", file=file)).strip()
    return {"instrume": instrume, "telescop": telescop, "creator": creator}

"""
app/v2/parsers/solexs_lc.py — SoLEXS .lc.gz parser (Milestone III).

Implements contract §2.1 exactly. No spectrum support. No downstream aggregation
(minute-binning is Milestone VII / T1).

OBSERVED schema (spec §2.1):
  HDU0 PRIMARY : MISSION, TELESCOP, INSTRUME, ORIGIN, CREATOR, FILENAME,
                 CONTENT='LIGHT CURVE', DATE, OBS_DATE, OBS_ID
  HDU1 'RATE'  : TIME (D), COUNTS (D) -- BOTH UNITS UNDECLARED
                 HDUCLAS1='LIGHTCURVE', HDUCLAS2='TOTAL', HDUCLAS3='COUNTS'
                 FILTER='SDD2', TSTART, TSTOP, TIMEDEL=1, TIMZERO=0,
                 MJDREFI=40587, MJDREFF=0, TIMESYS='UTC', TIMEUNIT='s',
                 NUMBAND='4', NAXIS2=86400

Two contract subtleties this parser exists to honour:
  * EXTNAME is 'RATE' but HDUCLAS3 is 'COUNTS'. §2.1 binds semantics to
    HDUCLAS3, NEVER to EXTNAME (F-07). The values are counts per 1-s bin.
  * MJDREFI=40587 == Unix epoch. v1 read a key named 'MJDREF' (absent here),
    defaulted to 58484, and was ~49 years wrong -> F-05 makes that impossible.

Applicable fail-loud rules: F-01, F-02, F-04, F-05, F-07, F-16, F-17, F-18, F-19.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.v2.models.metadata import (FailLoud, Instrument, ParsedProduct,
                                    Product, Provenance, TimeEpoch)
from app.v2.parsers.base import (BaseParser, REGISTRY, get_column, get_hdu,
                                 require_equal, require_header)
from app.v2.utils.fitsio import open_fits

_FNAME = re.compile(r"AL1_SOLEXS_(?P<date>\d{8})_(?P<det>SDD\d)_L1\.lc", re.I)
_ARCHIVE_VER = re.compile(r"AL1_SLX_L1_\d{8}_v(?P<ver>[\d.]+)", re.I)

EXPECTED_ROWS = 86400          # §2.1 / F-17
EXPECTED_TIMEDEL = 1           # §2.1
EXPECTED_MJDREFI = TimeEpoch.UNIX_MJDREFI   # 40587 == 1970-01-01


@dataclass(frozen=True)
class LcTable:
    """Native 1-s light curve. `counts` are COUNTS PER BIN, not a rate (§2.1)."""
    samples: pd.DataFrame          # timestamp_utc, counts
    detector: str
    obs_date: str
    timedel_s: float
    tstart_unix: float
    tstop_unix: float


class SolexsLcParser(BaseParser):
    instrument = Instrument.SOLEXS.value
    product = Product.LC.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        base = os.path.basename(path)
        m = _FNAME.search(base)
        if not m:
            raise FailLoud("F-18", "filename does not match the SoLEXS LC pattern",
                           file=path, expected="AL1_SOLEXS_<date>_<SDDn>_L1.lc[.gz]",
                           got=base)
        det, obs_date_fn = m.group("det").upper(), m.group("date")
        av = _ARCHIVE_VER.search(path)
        archive_version = f"v{av.group('ver')}" if av else None

        with open_fits(path) as hdul:
            primary = get_hdu(hdul, "PRIMARY", file=path)
            # §2.1: HDU is named 'RATE' -- by name, never by index (F-02).
            rate = get_hdu(hdul, "RATE", file=path)
            hdr = rate.header

            # ── identity / provenance (never defaulted) ─────────────────────
            instrume = str(require_header(primary.header, "INSTRUME", file=path)).strip()
            if instrume.upper() != "SOLEXS":
                raise FailLoud("F-07", "INSTRUME is not SoLEXS", file=path,
                               expected="SoLEXS", got=instrume)
            obs_date_hdr = str(require_header(primary.header, "OBS_DATE", file=path)).strip()
            if obs_date_hdr != obs_date_fn:
                raise FailLoud("F-07", "OBS_DATE disagrees with filename date",
                               file=path, expected=obs_date_fn, got=obs_date_hdr)
            creator = str(require_header(primary.header, "CREATOR", file=path))
            processing_date = str(require_header(primary.header, "DATE", file=path))
            obs_id = str(require_header(primary.header, "OBS_ID", file=path))

            # ── §2.1 F-07: semantics come from HDUCLAS3, NEVER from EXTNAME ──
            hduclas3 = str(require_header(hdr, "HDUCLAS3", file=path, hdu="RATE")).strip()
            if hduclas3.upper() != "COUNTS":
                raise FailLoud(
                    "F-07",
                    "HDUCLAS3 is not COUNTS: the RATE-named HDU no longer carries "
                    "counts-per-bin; semantics must not be inferred from EXTNAME",
                    file=path, hdu="RATE", expected="COUNTS", got=hduclas3)
            hduclas1 = str(require_header(hdr, "HDUCLAS1", file=path, hdu="RATE")).strip()
            require_equal(hduclas1.upper(), "LIGHTCURVE", "F-07",
                          "HDUCLAS1 is not LIGHTCURVE", file=path, hdu="RATE")

            # ── §2.1 F-05: epoch. The exact defect that produced v1. ─────────
            mjdrefi = int(require_header(hdr, "MJDREFI", file=path, hdu="RATE"))
            require_equal(mjdrefi, EXPECTED_MJDREFI, "F-05",
                          "MJDREFI is not the Unix epoch (40587)", file=path, hdu="RATE")
            mjdreff = float(require_header(hdr, "MJDREFF", file=path, hdu="RATE"))
            if mjdreff != 0.0:
                raise FailLoud("F-05", "MJDREFF is non-zero; epoch is not exactly Unix",
                               file=path, hdu="RATE", expected=0.0, got=mjdreff)
            timesys = str(require_header(hdr, "TIMESYS", file=path, hdu="RATE")).strip()
            require_equal(timesys.upper(), "UTC", "F-05", "TIMESYS is not UTC",
                          file=path, hdu="RATE")
            timeunit = str(require_header(hdr, "TIMEUNIT", file=path, hdu="RATE")).strip()
            require_equal(timeunit.lower(), "s", "F-05", "TIMEUNIT is not seconds",
                          file=path, hdu="RATE")
            timzero = float(require_header(hdr, "TIMZERO", file=path, hdu="RATE"))
            if timzero != 0.0:
                raise FailLoud("F-05", "TIMZERO is non-zero; TIME needs an offset "
                                       "this parser does not apply",
                               file=path, hdu="RATE", expected=0.0, got=timzero)
            timedel = float(require_header(hdr, "TIMEDEL", file=path, hdu="RATE"))
            require_equal(timedel, float(EXPECTED_TIMEDEL), "F-07",
                          "TIMEDEL is not 1 s", file=path, hdu="RATE")

            filt = str(require_header(hdr, "FILTER", file=path, hdu="RATE")).strip()
            if filt.upper() != det:
                raise FailLoud("F-07", "FILTER disagrees with the SDD directory",
                               file=path, hdu="RATE", expected=det, got=filt)

            # ── §2.1 F-17: row count is fixed for a daily product ───────────
            nrows = int(hdr["NAXIS2"])
            require_equal(nrows, EXPECTED_ROWS, "F-17",
                          "SoLEXS daily LC must have 86400 rows", file=path, hdu="RATE")

            time = np.asarray(get_column(rate, "TIME", file=path, hdu_name="RATE"),
                              dtype=np.float64)
            counts = np.asarray(get_column(rate, "COUNTS", file=path, hdu_name="RATE"),
                                dtype=np.float64)

            # ── validation (§2.1) ────────────────────────────────────────────
            # TIME must be finite: a NaN timestamp would silently defeat the F-16
            # monotonicity test below (NaN comparisons are False).
            if not np.all(np.isfinite(time)):
                raise FailLoud("F-16", "non-finite TIME value", file=path, hdu="RATE")

            # NaN COUNTS are NOT an error: OBSERVED on the real archive, NaN is the
            # missing-data sentinel and its positions coincide EXACTLY with the
            # GTI-excluded seconds (2024-05-14 SDD2: offsets [0,5,30072,30078,83951];
            # 5 NaN, 86395 finite == EXPOSURE). See CONTRADICTION-002: §2.1's clause
            # "absence is expressed via GTI, not sentinels" is factually wrong.
            # Contract §3 already mandates the matching OUTPUT convention ("Absent
            # data is NaN + q_no_data=True"), so NaN passes through UNTOUCHED here.
            # Never imputed, never filled, never dropped.
            n_nan = int(np.count_nonzero(~np.isfinite(counts)))

            # F-19 as frozen covers "Negative counts" only. NaN < 0 is False, so
            # this test is NaN-safe and needs no guard.
            if np.any(counts < 0):
                bad = int(np.argmax(counts < 0))
                raise FailLoud("F-19", f"negative COUNTS at row {bad}", file=path,
                               hdu="RATE", got=float(counts[bad]))
            d = np.diff(time)
            if np.any(d <= 0):
                raise FailLoud("F-16", "TIME not strictly increasing", file=path,
                               hdu="RATE")
            if not np.all(d == EXPECTED_TIMEDEL):
                bad = int(np.argmax(d != EXPECTED_TIMEDEL))
                raise FailLoud("F-16", f"TIME step != TIMEDEL at row {bad}",
                               file=path, hdu="RATE",
                               expected=EXPECTED_TIMEDEL, got=float(d[bad]))

            tstart = float(require_header(hdr, "TSTART", file=path, hdu="RATE"))
            tstop = float(require_header(hdr, "TSTOP", file=path, hdu="RATE"))
            if time[0] != tstart:
                raise FailLoud("F-06", "TIME[0] != TSTART", file=path, hdu="RATE",
                               expected=tstart, got=float(time[0]))
            if time[-1] != tstop:
                raise FailLoud("F-06", "TIME[-1] != TSTOP", file=path, hdu="RATE",
                               expected=tstop, got=float(time[-1]))

            # ── epoch materialisation + day-bounds cross-check (§2.1) ────────
            ts = pd.to_datetime(time, unit="s", utc=True)
            day0 = pd.Timestamp(obs_date_fn, tz="UTC")
            day1 = day0 + pd.Timedelta(days=1)
            if ts[0] < day0 or ts[-1] >= day1:
                raise FailLoud("F-06", "TIME outside its OBS_DATE day "
                                       "(epoch is not Unix seconds?)", file=path,
                               hdu="RATE", expected=f"[{day0}, {day1})",
                               got=(str(ts[0]), str(ts[-1])))

            samples = pd.DataFrame({"timestamp_utc": ts, "counts": counts})
            numband = require_header(hdr, "NUMBAND", file=path, hdu="RATE")

            prov = Provenance(
                src_file=path, src_sha256=sha256 or "", instrument=self.instrument,
                detector=det, product=self.product, archive_version=archive_version,
                obs_date=obs_date_fn, orbit_id=None, creator=creator,
                processing_date=processing_date, rows_in=nrows, rows_out=len(samples),
                time_epoch_resolution="unix_seconds",
                assumptions_applied=[
                    "A-6: NUMBAND captured as metadata, not interpreted",
                    "semantics from HDUCLAS3=COUNTS, not EXTNAME='RATE' (F-07)",
                    "epoch=unix_seconds verified via MJDREFI=40587 (F-05)",
                    "NaN COUNTS preserved as the missing-data sentinel "
                    "(CONTRADICTION-002); never imputed",
                ])
            return ParsedProduct(
                data=LcTable(samples=samples, detector=det, obs_date=obs_date_fn,
                             timedel_s=timedel, tstart_unix=tstart, tstop_unix=tstop),
                provenance=prov, detector_active=True,
                header={"nrows": nrows, "obs_id": obs_id, "numband": str(numband),
                        "hduclas3": hduclas3, "tstart": tstart, "tstop": tstop,
                        # exposed so Milestone VII can cross-check NaN <-> GTI
                        "n_nan_counts": n_nan, "n_finite_counts": nrows - n_nan})


REGISTRY.register(SolexsLcParser())

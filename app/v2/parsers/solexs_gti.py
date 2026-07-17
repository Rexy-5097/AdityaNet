"""
app/v2/parsers/solexs_gti.py — SoLEXS .gti.gz parser (Milestone II).

Implements contract §2.3 exactly. No downstream aggregation.

OBSERVED schema (frozen spec §2.3):
  HDU0 PRIMARY : MISSION, TELESCOP, INSTRUME, ORIGIN, CREATOR, FILENAME,
                 CONTENT='GOOD TIME INTERVAL', DATE, OBS_DATE, OBS_ID,
                 TSTART/TSTOP as ISO-8601 STRINGS (or '' when inactive)
  HDU1 'GTI'   : START (D), STOP (D)  -- Unix seconds, units UNDECLARED
                 EXPOSURE as a STRING (e.g. '86395.0')
                 NAXIS2 == 0 is LEGAL -> detector inactive (F-12)

Applicable fail-loud rules: F-01, F-02, F-04, F-09, F-12, F-16, F-18, F-19.
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
                                 require_header)
from app.v2.utils.fitsio import open_fits

# AL1_SOLEXS_<YYYYMMDD>_<SDDn>_L1.gti
_FNAME = re.compile(r"AL1_SOLEXS_(?P<date>\d{8})_(?P<det>SDD\d)_L1\.gti", re.I)
# AL1_SLX_L1_<YYYYMMDD>_v<ver>
_ARCHIVE_VER = re.compile(r"AL1_SLX_L1_\d{8}_v(?P<ver>[\d.]+)", re.I)

EXPOSURE_TOL_S = 1.0            # §2.3 / F-09


@dataclass(frozen=True)
class GtiTable:
    """Parsed GTI. `intervals` is empty iff detector_active is False (F-12)."""
    intervals: pd.DataFrame       # start_utc, stop_utc, duration_s
    exposure_declared_s: float | None
    exposure_summed_s: float
    detector: str
    obs_date: str


class SolexsGtiParser(BaseParser):
    instrument = Instrument.SOLEXS.value
    product = Product.GTI.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        base = os.path.basename(path)
        m = _FNAME.search(base)
        if not m:
            raise FailLoud("F-18", "filename does not match the SoLEXS GTI pattern",
                           file=path, expected="AL1_SOLEXS_<date>_<SDDn>_L1.gti[.gz]",
                           got=base)
        det, obs_date_fn = m.group("det").upper(), m.group("date")
        av = _ARCHIVE_VER.search(path)
        archive_version = f"v{av.group('ver')}" if av else None

        with open_fits(path) as hdul:
            primary = get_hdu(hdul, "PRIMARY", file=path)
            gti = get_hdu(hdul, "GTI", file=path)          # F-02 by name

            # ── mandatory primary metadata (never defaulted) ─────────────────
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

            nrows = int(gti.header["NAXIS2"])

            # ── F-12: the single deliberate non-fatal rule ───────────────────
            if nrows == 0:
                # OBSERVED on SDD1 2024-05-14: zero rows, primary TSTART=''.
                # Legal inactive detector. Emit an empty table; never synthesise.
                prov = self._prov(path, sha256, det, archive_version, obs_date_fn,
                                  creator, processing_date, obs_id, nrows, 0,
                                  ["F-12: GTI NAXIS2==0 -> detector_active=False"])
                return ParsedProduct(
                    data=GtiTable(intervals=self._empty_intervals(),
                                  exposure_declared_s=None, exposure_summed_s=0.0,
                                  detector=det, obs_date=obs_date_fn),
                    provenance=prov, detector_active=False,
                    header={"nrows": 0, "obs_id": obs_id},
                    warnings=[f"[F-12] {det} GTI has zero rows -> detector inactive"])

            start = np.asarray(get_column(gti, "START", file=path, hdu_name="GTI"),
                               dtype=np.float64)
            stop = np.asarray(get_column(gti, "STOP", file=path, hdu_name="GTI"),
                              dtype=np.float64)

            # ── validation (§2.3) ────────────────────────────────────────────
            if np.any(~np.isfinite(start)) or np.any(~np.isfinite(stop)):
                raise FailLoud("F-19", "non-finite GTI boundary", file=path)
            if np.any(stop <= start):
                bad = int(np.argmax(stop <= start))
                raise FailLoud("F-19", f"GTI row {bad} has STOP <= START", file=path,
                               expected="STOP > START", got=(start[bad], stop[bad]))
            if np.any(np.diff(start) <= 0):
                raise FailLoud("F-16", "GTI START not strictly increasing", file=path)
            if np.any(start[1:] < stop[:-1]):
                bad = int(np.argmax(start[1:] < stop[:-1]))
                raise FailLoud("F-16", f"GTI intervals overlap at row {bad}", file=path,
                               expected="non-overlapping", got=(stop[bad], start[bad + 1]))

            summed = float(np.sum(stop - start))
            # EXPOSURE is a STRING in the archive (§2.3) -> parse explicitly,
            # never coerce silently.
            exp_raw = require_header(gti.header, "EXPOSURE", file=path, hdu="GTI")
            try:
                exposure = float(str(exp_raw).strip())
            except ValueError as e:
                raise FailLoud("F-07", f"EXPOSURE not parseable as float: {exp_raw!r}",
                               file=path, hdu="GTI") from e
            if exposure < 0:
                raise FailLoud("F-19", "negative EXPOSURE", file=path, got=exposure)
            if abs(summed - exposure) > EXPOSURE_TOL_S:
                raise FailLoud("F-09", "sum(STOP-START) != EXPOSURE", file=path,
                               hdu="GTI", expected=f"{exposure} +/-{EXPOSURE_TOL_S}",
                               got=summed)

            # ── epoch: Unix seconds, verified against OBS_DATE (§2.3) ────────
            day0 = pd.Timestamp(obs_date_fn, tz="UTC")
            day1 = day0 + pd.Timedelta(days=1)
            t0 = pd.to_datetime(start, unit="s", utc=True)
            t1 = pd.to_datetime(stop, unit="s", utc=True)
            if t0.min() < day0 or t1.max() > day1:
                raise FailLoud("F-06", "GTI interval outside its OBS_DATE day "
                                       "(epoch is not Unix seconds?)", file=path,
                               expected=f"[{day0}, {day1}]",
                               got=(str(t0.min()), str(t1.max())))

            intervals = pd.DataFrame({
                "start_utc": t0, "stop_utc": t1,
                "duration_s": (stop - start).astype(np.float64)})

            prov = self._prov(path, sha256, det, archive_version, obs_date_fn,
                              creator, processing_date, obs_id, nrows, len(intervals),
                              ["epoch=unix_seconds verified against OBS_DATE"])
            return ParsedProduct(
                data=GtiTable(intervals=intervals, exposure_declared_s=exposure,
                              exposure_summed_s=summed, detector=det,
                              obs_date=obs_date_fn),
                provenance=prov, detector_active=True,
                header={"nrows": nrows, "obs_id": obs_id, "exposure_s": exposure})

    @staticmethod
    def _empty_intervals() -> pd.DataFrame:
        return pd.DataFrame({
            "start_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
            "stop_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
            "duration_s": pd.Series([], dtype="float64")})

    def _prov(self, path, sha256, det, ver, obs_date, creator, pdate, obs_id,
              rows_in, rows_out, assumptions) -> Provenance:
        return Provenance(
            src_file=path, src_sha256=sha256 or "", instrument=self.instrument,
            detector=det, product=self.product, archive_version=ver,
            obs_date=obs_date, orbit_id=None, creator=creator,
            processing_date=pdate, rows_in=rows_in, rows_out=rows_out,
            time_epoch_resolution=TimeEpoch(kind="unix_seconds",
                                            resolved_by="header_MJDREFI_convention",
                                            mjdrefi=TimeEpoch.UNIX_MJDREFI).kind,
            assumptions_applied=list(assumptions))


REGISTRY.register(SolexsGtiParser())

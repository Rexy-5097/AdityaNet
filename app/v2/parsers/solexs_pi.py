"""
app/v2/parsers/solexs_pi.py — SoLEXS .pi.gz spectra parser (Milestone IV).

Implements contract §2.2. This is the scientific core: 340 PI channels at 1-s
cadence, 86400 spectra per day. No keV conversion. No RMF assumptions.

OBSERVED schema (spec §2.2):
  HDU1 'SPECTRUM' : OGIP Type II PHA (HDUCLAS4='TYPE:II'), DETCHANS=340,
                    CHANTYPE='PI', HDUCLAS3='COUNTS', POISSERR=False,
                    AREASCAL=1.0, CORRSCAL=1.0, FILTER='SDD2'
  Columns         : TSTART (D,s), TELAPSE (D,s), SPEC_NUM (J),
                    CHANNEL (340K), COUNTS (340D), EXPOSURE (D,s)
  NAXIS2 = 86400  -> one 340-channel spectrum per second

MEMORY (§2.2, design-binding): NAXIS1=5468 B x 86400 ~= 472 MB/day decompressed;
436 days ~= 206 GB. This parser streams ONE DAY AT A TIME and never holds
multiple days of COUNTS. CHANNEL is 235 MB/day of pure redundancy (the same 340
ints repeated 86400 times) -> read once, validate constant (F-08), discard.

ENERGY (§2.2, binding): CHANNEL is an ORDINAL PI INDEX, NOT energy. No RMF/ARF
exists anywhere in the archive, so PI->keV is impossible from archive contents.
No v2 artifact may state a SoLEXS energy in keV. This parser exposes no energy
axis and computes no keV.

NaN (§2.1 r2, applies identically here): NaN COUNTS is the missing-data
sentinel; it passes through unchanged. Never imputed, zero-filled, or removed.

Applicable fail-loud rules: F-01, F-02, F-04, F-06, F-07, F-08, F-17, F-18, F-19.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.v2.models.metadata import (ChanType, FailLoud, Instrument,
                                    ParsedProduct, Product, Provenance)
from app.v2.parsers.base import (BaseParser, REGISTRY, get_column, get_hdu,
                                 require_equal, require_header)
from app.v2.utils.fitsio import open_fits

_FNAME = re.compile(r"AL1_SOLEXS_(?P<date>\d{8})_(?P<det>SDD\d)_L1\.pi", re.I)
_ARCHIVE_VER = re.compile(r"AL1_SLX_L1_\d{8}_v(?P<ver>[\d.]+)", re.I)

EXPECTED_ROWS = 86400          # §2.2 / F-17
EXPECTED_DETCHANS = 340        # §2.2 / F-07 -- NOT 341 (that is HEL1OS PHA, F-11)
EXPECTED_CHANTYPE = "PI"       # §2.2 -- gain-corrected pulse-invariant


@dataclass(frozen=True)
class PiTable:
    """Type II PHA spectra for one day.

    counts : (86400, 340) float64 -- counts per EXPOSURE seconds, per channel.
             NaN is the missing-data sentinel (§2.1 r2), preserved untouched.
    channel_index : (340,) int64 -- ORDINAL PI indices. NOT energy. No RMF exists.
    """
    tstart_unix: np.ndarray        # (86400,) float64
    telapse_s: np.ndarray          # (86400,) float64
    exposure_s: np.ndarray         # (86400,) float64
    counts: np.ndarray             # (86400, 340) float64
    channel_index: np.ndarray      # (340,) int64
    chantype: str
    detector: str
    obs_date: str

    @property
    def n_spectra(self) -> int:
        return int(self.counts.shape[0])

    @property
    def n_channels(self) -> int:
        return int(self.counts.shape[1])

    def timestamps_utc(self) -> pd.DatetimeIndex:
        return pd.to_datetime(self.tstart_unix, unit="s", utc=True)


class SolexsPiParser(BaseParser):
    instrument = Instrument.SOLEXS.value
    product = Product.PI.value

    def parse(self, path: str, *, sha256: str | None = None,
              lc_tstart: float | None = None) -> ParsedProduct:
        """Parse one day of spectra.

        lc_tstart : if supplied, §2.2 V-PI-3 is enforced -- .pi TSTART[0] must
                    equal the .lc TSTART for the same day, else F-06.
        """
        self._reject_appledouble(path)
        base = os.path.basename(path)
        m = _FNAME.search(base)
        if not m:
            raise FailLoud("F-18", "filename does not match the SoLEXS PI pattern",
                           file=path, expected="AL1_SOLEXS_<date>_<SDDn>_L1.pi[.gz]",
                           got=base)
        det, obs_date_fn = m.group("det").upper(), m.group("date")
        av = _ARCHIVE_VER.search(path)
        archive_version = f"v{av.group('ver')}" if av else None

        with open_fits(path) as hdul:
            primary = get_hdu(hdul, "PRIMARY", file=path)
            spec = get_hdu(hdul, "SPECTRUM", file=path)         # F-02 by name
            hdr = spec.header

            # ── identity (never defaulted) ───────────────────────────────────
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

            # ── §2.2 OGIP class + PI/PHA discipline (F-07, guards F-11) ─────
            hduclas1 = str(require_header(hdr, "HDUCLAS1", file=path, hdu="SPECTRUM")).strip()
            require_equal(hduclas1.upper(), "SPECTRUM", "F-07",
                          "HDUCLAS1 is not SPECTRUM", file=path, hdu="SPECTRUM")
            hduclas3 = str(require_header(hdr, "HDUCLAS3", file=path, hdu="SPECTRUM")).strip()
            require_equal(hduclas3.upper(), "COUNTS", "F-07",
                          "HDUCLAS3 is not COUNTS", file=path, hdu="SPECTRUM")
            hduclas4 = str(require_header(hdr, "HDUCLAS4", file=path, hdu="SPECTRUM")).strip()
            require_equal(hduclas4.upper(), "TYPE:II", "F-07",
                          "HDUCLAS4 is not TYPE:II (per-row spectra expected)",
                          file=path, hdu="SPECTRUM")

            chantype = str(require_header(hdr, "CHANTYPE", file=path, hdu="SPECTRUM")).strip()
            if chantype.upper() != EXPECTED_CHANTYPE:
                # PI vs PHA is not cosmetic: SoLEXS PI(340) and HEL1OS PHA(341)
                # are incommensurable channel spaces (§2.7 / F-11).
                raise FailLoud("F-07", "CHANTYPE is not PI; SoLEXS spectra must be "
                                       "gain-corrected pulse-invariant",
                               file=path, hdu="SPECTRUM",
                               expected=EXPECTED_CHANTYPE, got=chantype)

            detchans = int(require_header(hdr, "DETCHANS", file=path, hdu="SPECTRUM"))
            require_equal(detchans, EXPECTED_DETCHANS, "F-07",
                          "DETCHANS is not 340 (341 would be HEL1OS PHA -- see F-11)",
                          file=path, hdu="SPECTRUM")

            filt = str(require_header(hdr, "FILTER", file=path, hdu="SPECTRUM")).strip()
            if filt.upper() != det:
                raise FailLoud("F-07", "FILTER disagrees with the SDD directory",
                               file=path, hdu="SPECTRUM", expected=det, got=filt)

            # Scaling headers: any departure from unity would silently rescale
            # every spectrum, so they are asserted rather than applied.
            for key in ("AREASCAL", "CORRSCAL"):
                val = float(require_header(hdr, key, file=path, hdu="SPECTRUM"))
                if val != 1.0:
                    raise FailLoud("F-07", f"{key} != 1.0; this parser applies no "
                                           f"scaling and must not silently ignore it",
                                   file=path, hdu="SPECTRUM", expected=1.0, got=val)

            nrows = int(hdr["NAXIS2"])
            require_equal(nrows, EXPECTED_ROWS, "F-17",
                          "SoLEXS daily PI must have 86400 rows",
                          file=path, hdu="SPECTRUM")

            # ── columns (case-insensitive, by name) ─────────────────────────
            tstart = np.asarray(get_column(spec, "TSTART", file=path,
                                           hdu_name="SPECTRUM"), dtype=np.float64)
            telapse = np.asarray(get_column(spec, "TELAPSE", file=path,
                                            hdu_name="SPECTRUM"), dtype=np.float64)
            exposure = np.asarray(get_column(spec, "EXPOSURE", file=path,
                                             hdu_name="SPECTRUM"), dtype=np.float64)
            channel = np.asarray(get_column(spec, "CHANNEL", file=path,
                                            hdu_name="SPECTRUM"))
            counts = np.asarray(get_column(spec, "COUNTS", file=path,
                                           hdu_name="SPECTRUM"), dtype=np.float64)

            # ── shape (§2.2) ────────────────────────────────────────────────
            if counts.ndim != 2 or counts.shape != (nrows, EXPECTED_DETCHANS):
                raise FailLoud("F-07", "COUNTS is not (NAXIS2, DETCHANS)", file=path,
                               hdu="SPECTRUM",
                               expected=(nrows, EXPECTED_DETCHANS), got=counts.shape)
            if channel.ndim != 2 or channel.shape != (nrows, EXPECTED_DETCHANS):
                raise FailLoud("F-07", "CHANNEL is not (NAXIS2, DETCHANS)", file=path,
                               hdu="SPECTRUM",
                               expected=(nrows, EXPECTED_DETCHANS), got=channel.shape)

            # ── §2.2 F-08: the CHANNEL map must be constant across rows ─────
            # 235 MB/day of redundancy: validate once, then collapse to (340,).
            ch0 = channel[0].astype(np.int64)
            if not np.array_equal(channel, np.broadcast_to(ch0, channel.shape)):
                bad = int(np.argmax(np.any(channel != ch0, axis=1)))
                raise FailLoud("F-08", f"CHANNEL vector differs at row {bad}; the "
                                       f"channel map is not constant",
                               file=path, hdu="SPECTRUM")
            del channel                    # release ~235 MB immediately

            # ── time (§2.2) ─────────────────────────────────────────────────
            if not np.all(np.isfinite(tstart)):
                raise FailLoud("F-16", "non-finite TSTART", file=path, hdu="SPECTRUM")
            if np.any(np.diff(tstart) <= 0):
                raise FailLoud("F-16", "TSTART not strictly increasing", file=path,
                               hdu="SPECTRUM")
            day0 = pd.Timestamp(obs_date_fn, tz="UTC")
            day1 = day0 + pd.Timedelta(days=1)
            ts = pd.to_datetime(tstart, unit="s", utc=True)
            if ts[0] < day0 or ts[-1] >= day1:
                raise FailLoud("F-06", "TSTART outside its OBS_DATE day (epoch is "
                                       "not Unix seconds?)", file=path, hdu="SPECTRUM",
                               expected=f"[{day0}, {day1})",
                               got=(str(ts[0]), str(ts[-1])))

            # §2.2 V-PI-3: cross-product epoch agreement with the .lc
            if lc_tstart is not None and float(tstart[0]) != float(lc_tstart):
                raise FailLoud("F-06", ".pi TSTART[0] != .lc TSTART for the same day",
                               file=path, hdu="SPECTRUM",
                               expected=lc_tstart, got=float(tstart[0]))

            # ── physical sanity (§2.2 / F-19). NaN-safe: NaN<0 is False. ────
            if np.any(exposure < 0):
                raise FailLoud("F-19", "negative EXPOSURE", file=path, hdu="SPECTRUM",
                               got=float(np.nanmin(exposure)))
            if np.any(counts < 0):
                raise FailLoud("F-19", "negative COUNTS", file=path, hdu="SPECTRUM",
                               got=float(np.nanmin(counts)))

            # §2.1 r2: NaN COUNTS is the missing-data sentinel -> preserved.
            n_nan_rows = int(np.count_nonzero(~np.isfinite(counts).all(axis=1)))

            prov = Provenance(
                src_file=path, src_sha256=sha256 or "", instrument=self.instrument,
                detector=det, product=self.product, archive_version=archive_version,
                obs_date=obs_date_fn, orbit_id=None, creator=creator,
                processing_date=processing_date, rows_in=nrows, rows_out=nrows,
                time_epoch_resolution="unix_seconds",
                assumptions_applied=[
                    "§2.2: CHANNEL is an ordinal PI index; NO RMF exists in the "
                    "archive, so no keV is computed or claimed",
                    "§2.2 F-08: CHANNEL validated constant, then collapsed to (340,)",
                    "§2.1 r2: NaN COUNTS preserved as the missing-data sentinel",
                ])
            return ParsedProduct(
                data=PiTable(tstart_unix=tstart, telapse_s=telapse,
                             exposure_s=exposure, counts=counts,
                             channel_index=ch0, chantype=ChanType.PI.value,
                             detector=det, obs_date=obs_date_fn),
                provenance=prov, detector_active=True,
                header={"nrows": nrows, "detchans": detchans, "chantype": chantype,
                        "obs_id": obs_id, "n_all_nan_spectra": n_nan_rows,
                        "tstart": float(tstart[0]), "tstop": float(tstart[-1])})


REGISTRY.register(SolexsPiParser())


def stream_days(paths, *, sha256_by_path=None, lc_tstart_by_path=None):
    """Yield one parsed day at a time. NEVER holds two days simultaneously.

    §2.2 is design-binding here: a day is ~472 MB decompressed and the archive is
    ~206 GB across 436 days, so a list-returning API would be unusable on a 16 GB
    machine. This generator is the ONLY supported multi-day entry point, and it
    is a generator specifically so that no accumulation is possible inside the
    parser layer.

    The caller must not retain `PiTable.counts` across iterations. To make that
    contract observable rather than merely documented, each yielded product's
    counts array is released here after the consumer resumes: the reference held
    by this function is dropped before the next file is opened.

    Args:
        paths: iterable of .pi[.gz] paths.
        sha256_by_path: optional {path: sha256} from the 0.5.1 manifest (F-13).
        lc_tstart_by_path: optional {path: lc_tstart} to enforce §2.2 V-PI-3.

    Yields:
        ParsedProduct, one per path, in the given order.
    """
    parser = SolexsPiParser()
    sha_map = sha256_by_path or {}
    lc_map = lc_tstart_by_path or {}
    for p in paths:
        product = parser.parse(p, sha256=sha_map.get(p),
                               lc_tstart=lc_map.get(p))
        yield product
        # Drop this day before touching the next one. Without this, a consumer
        # that keeps the generator alive would leave one full day (~235 MB of
        # COUNTS) resident while the next day is being decompressed.
        del product

"""
app/v2/parsers/hel1os.py — HEL1OS parser family (Milestone V).

Implements contract §2.5–§2.9. Per the milestone brief: orbit files are NOT
merged here. Merging is Milestone VI's version-resolution engine, which is the
only place a coverage map exists (§4).

Products:
  HEL1OSLcParser       §2.6  lightcurve_{czt,cdte}{1,2}.fits  5 band HDUs
  HEL1OSGtiParser      §2.9  gti{czt,cdte}{1,2}.fits          lowercase cols
  HEL1OSHkParser       §2.8  aux/hk.fits                      Phase 1a asset
  HEL1OSSpectraParser  §2.7  hel1os_{czt,cdte}_spectra_*.fits 341 PHA + R-1
  HEL1OSEventsParser   §2.5  events/evt.fits                  4 detector HDUs
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.v2.models.metadata import (ChanType, FailLoud, Instrument,
                                    ParsedProduct, Product, Provenance)
from app.v2.parsers.base import (BaseParser, REGISTRY, get_column, get_hdu,
                                 has_column, require_equal, require_header)
from app.v2.parsers.hel1os_base import (DETECTORS, EVENT_HDUS, EXPECTED_BANDS_KEV,
                                        N_BANDS, detector_family, mjd_to_utc,
                                        orbit_id, parse_band_extname,
                                        require_hel1os_primary, resolve_epoch_R1)
from app.v2.utils.fitsio import open_fits

EXPECTED_DETCHANS_PHA = 341        # §2.7 -- NOT 340 (that is SoLEXS PI, F-11)


def _prov(path, sha256, det, product, oid, creator, rows_in, rows_out,
          epoch, assumptions) -> Provenance:
    return Provenance(
        src_file=path, src_sha256=sha256 or "",
        instrument=Instrument.HEL1OS.value, detector=det, product=product,
        archive_version=f"V{oid['ver']}", obs_date=oid["date"],
        orbit_id=f"HLS_{oid['date']}_{oid['start']}_{oid['dur']}sec_lev1_V{oid['ver']}",
        creator=creator, processing_date=None, rows_in=rows_in, rows_out=rows_out,
        time_epoch_resolution=epoch, assumptions_applied=list(assumptions))


# ── §2.6 light curves ───────────────────────────────────────────────────────
@dataclass(frozen=True)
class HelLcTable:
    """Per-band rate series for ONE detector of ONE orbit. NOT merged (M-VI)."""
    bands: dict[tuple[float, float], pd.DataFrame]   # (lo,hi)keV -> ts, ctr, err
    detector: str
    orbit: str


class HEL1OSLcParser(BaseParser):
    instrument = Instrument.HEL1OS.value
    product = Product.LIGHTCURVE.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        oid = orbit_id(path)
        with open_fits(path, memmap=True) as hdul:
            meta = require_hel1os_primary(get_hdu(hdul, "PRIMARY", file=path),
                                          file=path)
            band_hdus = [h for h in hdul if (h.name or "").upper() != "PRIMARY"]
            if len(band_hdus) != N_BANDS:
                raise FailLoud("F-10", "expected exactly 5 band HDUs", file=path,
                               expected=N_BANDS, got=len(band_hdus))
            bands, det, rows_in = {}, None, 0
            for h in band_hdus:
                d, lo, hi = parse_band_extname(h.name, file=path)   # F-10 allowlist
                detnam = str(require_header(h.header, "DETNAM", file=path,
                                            hdu=h.name)).strip().upper()
                if detnam != d:
                    raise FailLoud("F-07", "DETNAM disagrees with EXTNAME detector",
                                   file=path, hdu=h.name, expected=d, got=detnam)
                det = det or d
                if d != det:
                    raise FailLoud("F-07", "band HDUs mix detectors", file=path,
                                   hdu=h.name, expected=det, got=d)

                mjd = np.asarray(get_column(h, "MJD", file=path, hdu_name=h.name),
                                 dtype=np.float64)
                ctr = np.asarray(get_column(h, "CTR", file=path, hdu_name=h.name),
                                 dtype=np.float64)
                err = np.asarray(get_column(h, "STAT_ERR", file=path,
                                            hdu_name=h.name), dtype=np.float64)
                rows_in += len(mjd)

                # §2.6: CTR is a RATE with units DECLARED -- the OPPOSITE
                # convention from SoLEXS .lc (undeclared counts). Assert it.
                unit = next((c.unit for c in h.columns
                             if c.name.strip().upper() == "CTR"), None)
                if unit is None or str(unit).strip().lower() not in ("cts/sec", "cts/s", "counts/s"):
                    raise FailLoud("F-07", "CTR unit is not a declared rate; the "
                                           "SoLEXS counts convention must not be "
                                           "assumed here", file=path, hdu=h.name,
                                   expected="cts/sec", got=unit)
                if not np.all(np.isfinite(mjd)):
                    raise FailLoud("F-16", "non-finite MJD", file=path, hdu=h.name)
                if np.any(np.diff(mjd) <= 0):
                    raise FailLoud("F-16", "MJD not strictly increasing", file=path,
                                   hdu=h.name)
                if np.any(ctr < 0):                       # NaN-safe
                    raise FailLoud("F-19", "negative CTR", file=path, hdu=h.name,
                                   got=float(np.nanmin(ctr)))
                bands[(lo, hi)] = pd.DataFrame(
                    {"timestamp_utc": mjd_to_utc(mjd), "ctr": ctr, "stat_err": err})

            fam = detector_family(det)
            if set(bands) != set(EXPECTED_BANDS_KEV[fam]):
                raise FailLoud("F-10", f"{fam} band set incomplete", file=path,
                               expected=EXPECTED_BANDS_KEV[fam],
                               got=tuple(sorted(bands)))
            prov = _prov(path, sha256, det, self.product, oid, meta["creator"],
                         rows_in, sum(len(v) for v in bands.values()), "mjd_days",
                         ["§2.6: band edges parsed from EXTNAME and allowlisted",
                          "§2.6: CTR is a declared rate (cts/sec), not counts"])
            return ParsedProduct(
                data=HelLcTable(bands=bands, detector=det, orbit=prov.orbit_id),
                provenance=prov,
                header={"n_bands": len(bands), "detector": det})


# ── §2.9 GTI ────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class HelGtiTable:
    intervals: pd.DataFrame            # start_utc, stop_utc, duration_s
    detector: str
    orbit: str


class HEL1OSGtiParser(BaseParser):
    instrument = Instrument.HEL1OS.value
    product = Product.GTI.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        oid = orbit_id(path)
        with open_fits(path, memmap=True) as hdul:
            gti = next((h for h in hdul if (h.name or "").upper().startswith("GTI_")),
                       None)
            if gti is None:
                raise FailLoud("F-02", "no GTI_<DET> HDU", file=path,
                               expected="GTI_<DET>", got=[h.name for h in hdul])
            det = gti.name.split("_", 1)[1].upper()
            detector_family(det)
            # §2.9: columns are LOWERCASE here vs UPPERCASE in SoLEXS -> the
            # case-insensitive lookup (A-2) is what makes one code path work.
            ts = np.asarray(get_column(gti, "tstart", file=path, hdu_name=gti.name),
                            dtype=np.float64)
            te = np.asarray(get_column(gti, "tstop", file=path, hdu_name=gti.name),
                            dtype=np.float64)
            n = len(ts)
            if n == 0:                                     # F-12: legal
                return ParsedProduct(
                    data=HelGtiTable(intervals=_empty_intervals(), detector=det,
                                     orbit=f"HLS_{oid['date']}_{oid['start']}"),
                    provenance=_prov(path, sha256, det, self.product, oid, "", 0, 0,
                                     "mjd_days", ["F-12: empty GTI -> inactive"]),
                    detector_active=False,
                    warnings=[f"[F-12] {det} GTI has zero rows -> detector inactive"])
            if np.any(te <= ts):
                raise FailLoud("F-19", "GTI stop <= start", file=path, hdu=gti.name)
            if np.any(np.diff(ts) <= 0):
                raise FailLoud("F-16", "GTI tstart not strictly increasing",
                               file=path, hdu=gti.name)
            # HEL1OS GTI is MJD-days (§2.9 has no EXPOSURE header to cross-check,
            # so the SoLEXS F-09 exposure identity does NOT apply here).
            s_utc, e_utc = mjd_to_utc(ts), mjd_to_utc(te)
            intervals = pd.DataFrame({
                "start_utc": s_utc, "stop_utc": e_utc,
                "duration_s": (te - ts) * 86400.0})
            return ParsedProduct(
                data=HelGtiTable(intervals=intervals, detector=det,
                                 orbit=f"HLS_{oid['date']}_{oid['start']}"),
                provenance=_prov(path, sha256, det, self.product, oid, "", n, n,
                                 "mjd_days",
                                 ["§2.9: lowercase tstart/tstop (A-2 case-insensitive)",
                                  "§2.9: no EXPOSURE header -> SoLEXS F-09 identity "
                                  "does not apply"]),
                header={"nrows": n})


def _empty_intervals() -> pd.DataFrame:
    return pd.DataFrame({"start_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
                         "stop_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
                         "duration_s": pd.Series([], dtype="float64")})


# ── §2.8 housekeeping ───────────────────────────────────────────────────────
#: §2.8 -- the columns Phase 1a needs. suninfov is a FIRST-CLASS quality flag:
#: data outside Sun-in-FOV is not solar signal.
HK_REQUIRED = ("mjd", "czt1temp", "czt2temp", "cdte1temp", "cdte2temp",
               "czthvmon", "cdtehvmon", "cdte1pilectr", "cdte2pilectr",
               "czt1satctr1", "czt2satctr1", "czt1hotpixcnt", "czt2hotpixcnt",
               "czt1ctr", "czt2ctr", "cdte1ctr", "cdte2ctr",
               "suninfov", "sunradeg", "sundecdeg", "fehkstat",
               "czt1enth", "cdte1enerthr", "cdte2enerthr")


@dataclass(frozen=True)
class HelHkTable:
    samples: pd.DataFrame
    orbit: str
    columns_present: tuple[str, ...] = field(default=())


class HEL1OSHkParser(BaseParser):
    instrument = Instrument.HEL1OS.value
    product = Product.HK.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        oid = orbit_id(path)
        with open_fits(path, memmap=True) as hdul:
            hk = get_hdu(hdul, "HLSHK", file=path)          # F-02 by name
            n = int(hk.header["NAXIS2"])
            cols = {}
            for c in HK_REQUIRED:
                # get_column raises F-04 if absent: HK is Phase 1a's only source
                # of pile-up/saturation/HV state, so a missing column is fatal
                # rather than silently degraded.
                cols[c] = np.asarray(get_column(hk, c, file=path, hdu_name="HLSHK"))
            mjd = cols["mjd"].astype(np.float64)
            if not np.all(np.isfinite(mjd)):
                raise FailLoud("F-16", "non-finite HK mjd", file=path, hdu="HLSHK")
            if np.any(np.diff(mjd) < 0):
                raise FailLoud("F-16", "HK mjd decreasing", file=path, hdu="HLSHK")

            suninfov = cols["suninfov"].astype(np.int16)
            bad = np.setdiff1d(np.unique(suninfov), np.array([0, 1], dtype=np.int16))
            if bad.size:
                raise FailLoud("F-07", "suninfov is not boolean {0,1}", file=path,
                               hdu="HLSHK", expected="{0,1}", got=bad.tolist())

            df = pd.DataFrame({"timestamp_utc": mjd_to_utc(mjd)})
            for c in HK_REQUIRED:
                if c == "mjd":
                    continue
                df[c] = cols[c].astype(np.float64) if c != "suninfov" else suninfov.astype(bool)
            return ParsedProduct(
                data=HelHkTable(samples=df, orbit=f"HLS_{oid['date']}_{oid['start']}",
                                columns_present=tuple(HK_REQUIRED)),
                provenance=_prov(path, sha256, None, self.product, oid, "", n, len(df),
                                 "mjd_days",
                                 ["§2.8: suninfov is a first-class quality flag",
                                  "§2.8 A-4: czt2enth declares unit=None; the "
                                  "czt1enth keV unit is assumed for both"]),
                header={"nrows": n, "n_columns": len(HK_REQUIRED)})


# ── §2.7 spectra (341 PHA + R-1) ────────────────────────────────────────────
@dataclass(frozen=True)
class HelSpectraTable:
    counts: np.ndarray             # (n, 341)
    stat_err: np.ndarray
    channel_index: np.ndarray      # (341,)
    tstart: np.ndarray
    tstop: np.ndarray
    exposure_s: np.ndarray
    chantype: str
    detector: str
    orbit: str
    epoch_kind: str


class HEL1OSSpectraParser(BaseParser):
    instrument = Instrument.HEL1OS.value
    product = Product.SPECTRA.value

    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        self._reject_appledouble(path)
        oid = orbit_id(path)
        with open_fits(path, memmap=True) as hdul:
            spec = get_hdu(hdul, "SPECTRUM", file=path)
            hdr = spec.header
            det = str(require_header(hdr, "DETNAM", file=path,
                                     hdu="SPECTRUM")).strip().upper()
            detector_family(det)

            # §2.7 F-11 discipline: 341 PHA, NOT 340 PI.
            chantype = str(require_header(hdr, "CHANTYPE", file=path,
                                          hdu="SPECTRUM")).strip()
            if chantype.upper() != "PHA":
                raise FailLoud("F-07", "HEL1OS CHANTYPE is not PHA (PI would be the "
                                       "SoLEXS space -- see F-11)", file=path,
                               hdu="SPECTRUM", expected="PHA", got=chantype)
            detchans = int(require_header(hdr, "DETCHANS", file=path, hdu="SPECTRUM"))
            require_equal(detchans, EXPECTED_DETCHANS_PHA, "F-07",
                          "DETCHANS is not 341 (340 would be SoLEXS PI -- F-11)",
                          file=path, hdu="SPECTRUM")
            hduclas4 = str(require_header(hdr, "HDUCLAS4", file=path,
                                          hdu="SPECTRUM")).strip()
            require_equal(hduclas4.upper(), "TYPE:II", "F-07",
                          "HDUCLAS4 is not TYPE:II", file=path, hdu="SPECTRUM")
            # §2.7 OBSERVED: HDUCLAS3 is 'COUNT' (singular) here vs 'COUNTS'
            # (plural) in SoLEXS. Accept the HEL1OS spelling explicitly rather
            # than normalising -- the difference is a documented archive fact.
            hduclas3 = str(require_header(hdr, "HDUCLAS3", file=path,
                                          hdu="SPECTRUM")).strip()
            if hduclas3.upper() not in ("COUNT", "COUNTS"):
                raise FailLoud("F-07", "HDUCLAS3 is not COUNT/COUNTS", file=path,
                               hdu="SPECTRUM", expected="COUNT", got=hduclas3)

            n = int(hdr["NAXIS2"])
            counts = np.asarray(get_column(spec, "COUNTS", file=path,
                                           hdu_name="SPECTRUM"), dtype=np.float64)
            err = np.asarray(get_column(spec, "STAT_ERR", file=path,
                                        hdu_name="SPECTRUM"), dtype=np.float64)
            channel = np.asarray(get_column(spec, "CHANNEL", file=path,
                                            hdu_name="SPECTRUM"))
            ts = np.asarray(get_column(spec, "TSTART", file=path,
                                       hdu_name="SPECTRUM"), dtype=np.float64)
            te = np.asarray(get_column(spec, "TSTOP", file=path,
                                       hdu_name="SPECTRUM"), dtype=np.float64)
            ex = np.asarray(get_column(spec, "EXPOSURE", file=path,
                                       hdu_name="SPECTRUM"), dtype=np.float64)

            if counts.shape != (n, EXPECTED_DETCHANS_PHA):
                raise FailLoud("F-07", "COUNTS is not (NAXIS2, 341)", file=path,
                               hdu="SPECTRUM",
                               expected=(n, EXPECTED_DETCHANS_PHA), got=counts.shape)
            ch0 = channel[0].astype(np.int64)
            if not np.array_equal(channel, np.broadcast_to(ch0, channel.shape)):
                raise FailLoud("F-08", "CHANNEL vector not constant across rows",
                               file=path, hdu="SPECTRUM")
            del channel
            if np.any(ex < 0):
                raise FailLoud("F-19", "negative EXPOSURE", file=path, hdu="SPECTRUM")
            if np.any(counts < 0):
                raise FailLoud("F-19", "negative COUNTS", file=path, hdu="SPECTRUM")

            # §2.7 R-1: the declared ambiguity. Resolve, never assume.
            epoch = resolve_epoch_R1(
                ts,
                float(require_header(hdr, "TSTART", file=path, hdu="SPECTRUM")),
                float(require_header(hdr, "TSTOP", file=path, hdu="SPECTRUM")),
                file=path, hdu="SPECTRUM")

            return ParsedProduct(
                data=HelSpectraTable(counts=counts, stat_err=err, channel_index=ch0,
                                     tstart=ts, tstop=te, exposure_s=ex,
                                     chantype=ChanType.PHA.value, detector=det,
                                     orbit=f"HLS_{oid['date']}_{oid['start']}",
                                     epoch_kind=epoch.kind),
                provenance=_prov(path, sha256, det, self.product, oid, "", n, n,
                                 epoch.kind,
                                 [f"§2.7 R-1 resolved empirically: {epoch.kind} "
                                  f"(residual {epoch.residual_s:.6f}s)",
                                  "§2.7: 341 PHA channels; ordinal, incommensurable "
                                  "with SoLEXS 340 PI (F-11)"]),
                header={"nrows": n, "detchans": detchans, "chantype": chantype,
                        "epoch_kind": epoch.kind,
                        "epoch_residual_s": epoch.residual_s})


# ── §2.5 events ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class HelEventsTable:
    """Per-detector event lists. NOT ingested into canonical minute tables (§2.5)."""
    n_events: dict[str, int]
    detectors: tuple[str, ...]
    orbit: str
    _hdu_meta: dict[str, dict] = field(default_factory=dict)


class HEL1OSEventsParser(BaseParser):
    instrument = Instrument.HEL1OS.value
    product = Product.EVENTS.value

    def parse(self, path: str, *, sha256: str | None = None,
              load_columns: bool = False) -> ParsedProduct:
        """§2.5: expose an event reader, but do NOT ingest events into the
        canonical tables. Default is metadata-only: evt.fits is ~219 MB/orbit
        and 85.7 GB archive-wide, so eager column loading would be a trap.
        """
        self._reject_appledouble(path)
        oid = orbit_id(path)
        with open_fits(path, memmap=True) as hdul:
            require_hel1os_primary(get_hdu(hdul, "PRIMARY", file=path), file=path)
            names = {(h.name or "").upper() for h in hdul}
            missing = [e for e in EVENT_HDUS if e not in names]
            if missing:                                    # §2.5 F-03
                raise FailLoud("F-03", "evt.fits is missing detector HDU(s)",
                               file=path, expected=list(EVENT_HDUS), got=sorted(names))
            n_events, meta = {}, {}
            for e in EVENT_HDUS:
                h = get_hdu(hdul, e, file=path)
                det = str(require_header(h.header, "DETNAM", file=path,
                                         hdu=e)).strip().upper()
                for c in ("mjd", "hlsobt", "currtemp", "chn", "ener", "recnum"):
                    if not has_column(h, c):
                        raise FailLoud("F-04", f"event column {c!r} absent",
                                       file=path, hdu=e)
                # §2.5: CZT carries pix/offsetchn; CdTe does not. Assert the
                # family-specific schema rather than assuming a common one.
                if detector_family(det) == "CZT":
                    for c in ("pix", "offsetchn"):
                        if not has_column(h, c):
                            raise FailLoud("F-04", f"CZT event column {c!r} absent",
                                           file=path, hdu=e)
                # §2.5: `ener` must be declared in keV -- HEL1OS is calibrated,
                # unlike SoLEXS whose PI channels have no RMF.
                unit = next((c.unit for c in h.columns
                             if c.name.strip().lower() == "ener"), None)
                if unit is None or str(unit).strip().lower() != "kev":
                    raise FailLoud("F-07", "event `ener` is not declared in keV",
                                   file=path, hdu=e, expected="keV", got=unit)
                n = int(h.header["NAXIS2"])
                n_events[det] = n
                meta[det] = {"nrows": n,
                             "tstart_mjd": float(require_header(h.header, "TSTART",
                                                                file=path, hdu=e)),
                             "tstop_mjd": float(require_header(h.header, "TSTOP",
                                                               file=path, hdu=e))}
                if load_columns:
                    ev_mjd = np.asarray(get_column(h, "mjd", file=path, hdu_name=e),
                                        dtype=np.float64)
                    if np.any(np.diff(ev_mjd) < 0):
                        raise FailLoud("F-16", "event mjd decreasing", file=path,
                                       hdu=e)
                    meta[det]["mjd_first"] = float(ev_mjd[0])
                    meta[det]["mjd_last"] = float(ev_mjd[-1])
            return ParsedProduct(
                data=HelEventsTable(n_events=n_events, detectors=DETECTORS,
                                    orbit=f"HLS_{oid['date']}_{oid['start']}",
                                    _hdu_meta=meta),
                provenance=_prov(path, sha256, None, self.product, oid, "",
                                 sum(n_events.values()), 0, "mjd_days",
                                 ["§2.5: events exposed but NOT ingested into the "
                                  "canonical minute tables",
                                  "§2.5: `ener` is calibrated keV (unlike SoLEXS PI)"]),
                header={"n_events_total": sum(n_events.values()), **meta})


for _p in (HEL1OSLcParser(), HEL1OSGtiParser(), HEL1OSHkParser(),
           HEL1OSSpectraParser(), HEL1OSEventsParser()):
    REGISTRY.register(_p)

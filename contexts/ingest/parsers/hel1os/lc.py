"""HEL1OS `lightcurve_{czt,cdte}{1,2}.fits` — per-detector band light curves. §2.6.

THE OPPOSITE UNIT CONVENTION FROM SoLEXS
-----------------------------------------
§2.6: *"`CTR` is a **rate** with units **declared** — the opposite convention from SoLEXS
`.lc` (undeclared counts). The parser MUST NOT assume a shared convention across
instruments (F-07)."*

So this module reads `cts/sec` and emits a rate, while `parsers/solexs/lc.py` reads
undeclared values that `HDUCLAS3` declares to be counts and emits counts. Two instruments,
two conventions, and the only thing stopping one from being read as the other is that each
parser reads its own product's declaration. Neither imports the other.

BANDS ARE PARSED FROM `EXTNAME`, NEVER FROM POSITION
-----------------------------------------------------
§2.6, design rule: *"band edges are **parsed from `EXTNAME`** and validated against the
allowlist, never hardcoded by position — HDU order is not a contract."*

`OBSERVED` in the archive: `CZT1_LC_BAND_20.00KEV_TO_40.00KEV` and its four siblings. An
`EXTNAME` outside the allowlist is **F-10** — *"never silently accept an unknown band"* —
because a band this code has not been told about would be ingested as though it were one it
had, and a rate would be attributed to the wrong energy range.

`CTR`'s declared unit is read and must be `cts/sec` (F-07): the Observation's `cts/s` is stated
because the product declares a rate, never because this module expects one.

EACH BAND KEEPS ITS OWN TIME AXIS
---------------------------------
§2.6 records `NAXIS2 ≈ 43171` without saying whether the five bands of one detector share
timestamps. Archive-wide they often do not — every CdTe file and a few CZT files carry bands of
different lengths — so each `Band` keeps its own `MJD` column and nothing aligns them
(CONTRA-007 Observation D).

`TIME_REPRESENTATION_ALLOWANCE_S` is defined here, beside the MJD conversion every HEL1OS module
already imports, because it belongs to comparisons of MJD-derived times: `SPEC-parsers@r7` §5.1.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest.parsers import _fits
from contexts.ingest.parsers.hel1os.orbit import family_of
from domain.entities import Observation
from domain.values import Digest, Identifier, Timestamp

#: `CZT1_LC_BAND_20.00KEV_TO_40.00KEV`
BAND_EXTNAME = re.compile(
    r"^(?P<det>[A-Z0-9]+)_LC_BAND_(?P<lo>[0-9.]+)KEV_TO_(?P<hi>[0-9.]+)KEV$"
)

#: §2.6's allowlist, per family. Four science bands plus one total, per detector.
#: An unlisted band terminates via F-10; the set is not extended by observation.
BANDS_KEV: dict[str, tuple[tuple[float, float], ...]] = {
    "czt": ((20.0, 40.0), (40.0, 60.0), (60.0, 80.0), (80.0, 150.0), (18.0, 160.0)),
    "cdte": ((5.0, 20.0), (20.0, 30.0), (30.0, 40.0), (40.0, 60.0), (1.8, 90.0)),
}

#: The widest band of each family is the total, and it is the one that spans the others.
TOTAL_BAND: dict[str, tuple[float, float]] = {"czt": (18.0, 160.0), "cdte": (1.8, 90.0)}

EXPECTED_BAND_COUNT = 5

#: MJD of the Unix epoch. HEL1OS states times in MJD (§2.5, §2.6), where SoLEXS states them
#: in Unix seconds — another convention that must not be shared across instruments.
MJD_UNIX_EPOCH = 40587.0
SECONDS_PER_DAY = 86_400.0

#: `SPEC-parsers@r7` §5.1 — the time-representation allowance `ε_t`. Applied only where the
#: contract compares an MJD-derived time with a bound or with another representation of the
#: same instant (§2.5 span and V-EVT-2, §2.7 R-1 H3, §2.8 header span), never to a physical time
#: difference. It absorbs float64 representation, not physics (CONTRA-007).
TIME_REPRESENTATION_ALLOWANCE_S = 1e-3

#: §2.6 `OBSERVED`: `CTR` declares `cts/sec`. Read and checked, never assumed (F-07).
DECLARED_RATE_UNIT = "cts/sec"


def mjd_to_timestamp(mjd: float) -> Timestamp:
    """MJD → a domain Timestamp, UTC.

    `OBSERVED` (§2.5): `TSTART = 61017.0000988685` is 2025-12-08. The conversion is exact
    arithmetic on the declared epoch, not a library guess: MJD 40587 is 1970-01-01.
    """
    from datetime import datetime, timezone

    seconds = (mjd - MJD_UNIX_EPOCH) * SECONDS_PER_DAY
    moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return Timestamp(moment.isoformat().replace("+00:00", "Z"))


@dataclass(frozen=True)
class Band:
    """One energy band of one detector, with edges read from its `EXTNAME`."""

    detector: str
    low_kev: float
    high_kev: float
    extname: str
    mjd: tuple[float, ...]
    rate: tuple[float, ...]
    stat_err: tuple[float, ...]

    @property
    def is_total(self) -> bool:
        return (self.low_kev, self.high_kev) == TOTAL_BAND[family_of(self.detector)]

    @property
    def quantity(self) -> str:
        """The instrument's own term, carrying the band it belongs to.

        The energy range is part of what was measured: a rate in 20–40 keV and a rate in
        40–60 keV are different quantities, and a name that omitted the band would make them
        indistinguishable once serialised.
        """
        return f"count_rate_{self.low_kev:g}_{self.high_kev:g}_kev"


@dataclass(frozen=True)
class BandLightCurves:
    """A parsed `lightcurve_*.fits`: five bands of one detector."""

    detector: str
    source_path: Path
    source_digest: Digest
    bands: tuple[Band, ...]
    header_tstart: float
    header_tstop: float

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"hel1os-{self.detector.lower()}")

    @property
    def family(self) -> str:
        return family_of(self.detector)

    def band(self, low_kev: float, high_kev: float) -> Band:
        for candidate in self.bands:
            if (candidate.low_kev, candidate.high_kev) == (low_kev, high_kev):
                return candidate
        _fits.fail(
            "F-10", f"/{self.source_path.name}",
            f"no band {low_kev}-{high_kev} keV in {self.detector}; present: "
            f"{[(b.low_kev, b.high_kev) for b in self.bands]}",
        )

    def observations(self, *, source_id: Identifier, ingest_time: Timestamp | None,
                     ) -> Iterator[Observation]:
        """One Observation per (sample, band), streamed.

        The unit is `cts/s` — declared by the archive, not inferred — and is deliberately
        different from the SoLEXS lightcurve's `counts`. Emitting both as one unit is the
        cross-instrument mismatch F-07 exists to prevent.
        """
        for band in self.bands:
            for when, value in zip(band.mjd, band.rate):
                yield Observation(
                    source_id=source_id,
                    instrument_id=self.instrument_id,
                    quantity=band.quantity,
                    unit="cts/s",
                    valid_time=mjd_to_timestamp(when),
                    ingest_time=ingest_time,
                    value=value,
                    source_digest=self.source_digest,
                )


def parse(path: Path, digest: Digest, *, detector: str) -> BandLightCurves:
    """Parse one band-lightcurve product. Every §2.6 validation, no repair."""
    from astropy.io import fits

    source = path.name
    family = family_of(detector)
    allowed = BANDS_KEV[family]

    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    bands: list[Band] = []
    with opened as hdul:
        extensions = [hdu for hdu in hdul[1:]]
        if len(extensions) != EXPECTED_BAND_COUNT:
            _fits.fail(
                "F-10", f"/{source}",
                f"{len(extensions)} band HDUs, expected exactly {EXPECTED_BAND_COUNT} "
                f"(§2.6). Names present: {[h.name for h in extensions]}",
            )

        header_tstart = float(
            _fits.keyword(extensions[0].header, "TSTART", source=source,
                          hdu_name=extensions[0].name)
        )
        header_tstop = float(
            _fits.keyword(extensions[0].header, "TSTOP", source=source,
                          hdu_name=extensions[0].name)
        )

        for hdu in extensions:
            match = BAND_EXTNAME.match(hdu.name)
            if match is None:
                _fits.fail(
                    "F-10", f"/{source}#{hdu.name}",
                    f"EXTNAME {hdu.name!r} does not encode a band; §2.6 records the form "
                    f"<DET>_LC_BAND_<lo>KEV_TO_<hi>KEV",
                )
            low, high = float(match.group("lo")), float(match.group("hi"))
            if (low, high) not in allowed:
                _fits.fail(
                    "F-10", f"/{source}#{hdu.name}",
                    f"band {low}-{high} keV is not in the {family} allowlist "
                    f"{list(allowed)}. §2.6: never silently accept an unknown band — an "
                    f"unlisted band would attribute a rate to the wrong energy range.",
                )
            if match.group("det").lower() != detector.lower():
                _fits.fail(
                    "F-10", f"/{source}#{hdu.name}",
                    f"EXTNAME names detector {match.group('det')!r}, the file is "
                    f"{detector!r}",
                )

            ctr_unit = _fits.declared_unit(hdu, "CTR", source=source, hdu_name=hdu.name)
            if ctr_unit != DECLARED_RATE_UNIT:
                _fits.fail(
                    "F-07", f"/{source}#{hdu.name}/CTR",
                    f"CTR declares unit {ctr_unit!r}; §2.6 records a declared rate "
                    f"{DECLARED_RATE_UNIT!r}. Emitting a rate over any other declaration "
                    f"would assume a convention the product does not state.",
                )

            mjd = tuple(
                float(v) for v in _fits.column(hdu, "MJD", source=source, hdu_name=hdu.name)
            )
            rate = tuple(
                float(v) for v in _fits.column(hdu, "CTR", source=source, hdu_name=hdu.name)
            )
            stat_err = tuple(
                float(v)
                for v in _fits.column(hdu, "STAT_ERR", source=source, hdu_name=hdu.name)
            )
            _validate_band(mjd, rate, source, hdu.name)

            bands.append(
                Band(
                    detector=detector,
                    low_kev=low,
                    high_kev=high,
                    extname=hdu.name,
                    mjd=mjd,
                    rate=rate,
                    stat_err=stat_err,
                )
            )

    found = {(b.low_kev, b.high_kev) for b in bands}
    if found != set(allowed):
        _fits.fail(
            "F-10", f"/{source}",
            f"bands present {sorted(found)} do not match the {family} allowlist "
            f"{sorted(allowed)}",
        )

    return BandLightCurves(
        detector=detector,
        source_path=path,
        source_digest=digest,
        bands=tuple(bands),
        header_tstart=header_tstart,
        header_tstop=header_tstop,
    )


def _validate_band(mjd, rate, source: str, hdu_name: str) -> None:
    """§2.6: `MJD` strictly increasing, `CTR ≥ 0`.

    Strictly increasing here, unlike the housekeeping product where §2.8 r4 **removed** that
    requirement after the archive falsified it. The two are different measurements: a light
    curve is a binned series, housekeeping is telemetry in arrival order. Applying one
    product's rule to the other is how a real defect gets tolerated or a real value rejected.
    """
    for index, value in enumerate(mjd):
        if not math.isfinite(value):
            _fits.fail("F-16", f"/{source}#{hdu_name}/MJD[{index}]",
                       f"MJD[{index}] is not finite ({value!r})")
    for index in range(1, len(mjd)):
        if mjd[index] <= mjd[index - 1]:
            _fits.fail(
                "F-16", f"/{source}#{hdu_name}/MJD[{index}]",
                f"MJD is not strictly increasing at row {index}: "
                f"{mjd[index - 1]!r} then {mjd[index]!r}",
            )
    for index, value in enumerate(rate):
        if math.isnan(value):
            # §2.6 declares no missing-value sentinel for CTR, unlike SoLEXS §2.1 which
            # declares NaN. Treating a NaN here as "absent" would import another
            # instrument's convention; the spec does not authorise it, so it terminates.
            _fits.fail(
                "F-07", f"/{source}#{hdu_name}/CTR[{index}]",
                f"CTR[{index}] is NaN. §2.6 declares no missing-value sentinel for this "
                f"product; SoLEXS §2.1 declares one, and importing that convention across "
                f"instruments is exactly what F-07 forbids.",
            )
        if value < 0:
            _fits.fail("F-19", f"/{source}#{hdu_name}/CTR[{index}]",
                       f"CTR[{index}] is {value!r}; a negative rate is physically impossible")


__all__ = [
    "BANDS_KEV",
    "BAND_EXTNAME",
    "Band",
    "BandLightCurves",
    "DECLARED_RATE_UNIT",
    "EXPECTED_BAND_COUNT",
    "MJD_UNIX_EPOCH",
    "SECONDS_PER_DAY",
    "TIME_REPRESENTATION_ALLOWANCE_S",
    "TOTAL_BAND",
    "mjd_to_timestamp",
    "parse",
]

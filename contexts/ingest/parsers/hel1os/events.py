"""HEL1OS `events/evt.fits` — photon event lists. §2.5 as amended at r7.

THE SCOPE RULE IS PART OF THE SPECIFICATION
--------------------------------------------
§2.5, binding: *"**Not required for the canonical tables** — retained for Phase 1a pile-up /
gain work. The 0.5.2 parser MUST expose an event reader but MUST NOT ingest events into the
canonical minute tables."*

So this module reads events and produces no Observation. There is no `observations()` here,
and `test_the_event_reader_emits_no_observations` asserts that none appears — the canonical
tables are #19's, and an event stream that could flow into them would violate §2.5 by
default rather than by decision.

VOLUME
------
~85.7 GB across the corpus, and a single detector HDU can hold tens of millions of rows.
Everything here streams: `parse` reads headers only, and `events()` validates and yields one row
at a time from a freshly opened file.

FOUR DETECTOR HDUs, OR F-03
---------------------------
§2.5: HDU1–4 are `CDTE1-EVENTS`, `CDTE2-EVENTS`, `CZT1-EVENTS`, `CZT2-EVENTS`, each carrying
`DETNAM`. F-03 fires if any is absent, and its rationale is *"silent detector loss"* — three
detectors' worth of events is not a smaller version of four, it is a different measurement.
The columns §2.5 lists are required in every HDU (F-04), and CZT HDUs additionally carry `pix`
and `offsetchn`, which the reader exposes rather than drops.

`ener` IS ALREADY IN keV — AND THE DECLARATION IS READ
------------------------------------------------------
§2.5: *"`ener` is **already energy-calibrated in keV** (unlike SoLEXS)."* `parse` reads each
HDU's declared `ener` unit and refuses anything but `keV` (F-07): stating keV over a different
declaration is exactly the cross-instrument assumption F-07 exists to prevent.

THE ROW RULES — §2.5 AS AMENDED r7
-----------------------------------
The rows are never held, so the row-level rules run inside `events()` as each row is read:

    mjd within [TSTART − ε_t, TSTOP + ε_t]                         F-06   §2.5 r7, §5.1
    V-EVT-2  |instant(mjd) − instant(utc-isot)| ≤ ½·r_isot + ε_t    F-06   §2.5 r7
    mjd non-decreasing                                              F-16   §2.5
    ener > 0                                                        F-19   §2.5

`r_isot` is read from the string itself: the observed `YYYY-MM-DDTHH:MM:SS.sss` carries three
fractional digits, so it fixes the instant to 1 ms and a faithful string lies within 0.5 ms of
the `mjd` instant. `ε_t` (1 ms) absorbs float64 representation and nothing else.

NON-DECREASING IS ENFORCED AS WRITTEN — AND THE ARCHIVE FALSIFIES IT
--------------------------------------------------------------------
Real event HDUs step backward in `mjd` (CONTRA-008, OPEN). §2.5 has not been amended, so the
rule is enforced: a real stream terminates with F-16 at its first decrease, having yielded only
rows that passed every rule. Relaxing the rule here would be an amendment made in code, which
the contract forbids. Until the owner rules, the reader is exposed and every row rule is
exercised on real data, but a real stream does not run to completion.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from contexts.ingest.parsers import _fits
from contexts.ingest.parsers.hel1os.lc import (
    MJD_UNIX_EPOCH,
    SECONDS_PER_DAY,
    TIME_REPRESENTATION_ALLOWANCE_S,
    mjd_to_timestamp,
)
from contexts.ingest.parsers.hel1os.orbit import DETECTORS, family_of
from domain.values import Digest, Identifier, Timestamp

#: §2.5 `OBSERVED`. Keyed by detector so a caller asks by detector, not by HDU index.
EVENT_HDU = {
    "cdte1": "CDTE1-EVENTS", "cdte2": "CDTE2-EVENTS",
    "czt1": "CZT1-EVENTS", "czt2": "CZT2-EVENTS",
}

#: `DETNAM` as the archive spells it, per HDU. Case differs from the detector key, so the
#: comparison is case-insensitive — but presence and identity are still required.
DETNAM = {"cdte1": "CdTe1", "cdte2": "CdTe2", "czt1": "CZT1", "czt2": "CZT2"}

ENERGY_UNIT = "keV"
ISOT_COLUMN = "utc-isot"

#: §2.5's columns, required in every detector HDU; CZT additionally carries `pix`/`offsetchn`.
REQUIRED_COLUMNS = ("mjd", "hlsobt", "currtemp", "chn", "ener", "recnum", ISOT_COLUMN)
CZT_COLUMNS = ("pix", "offsetchn")


@dataclass(frozen=True)
class Event:
    """One photon event. Energy in keV, as the archive declares it."""

    mjd: float
    hlsobt: float
    energy_kev: float
    channel: int
    detector_temp_c: float
    recnum: int
    utc_isot: str
    pixel: int | None = None
    offset_channel: int | None = None

    @property
    def valid_time(self) -> Timestamp:
        return mjd_to_timestamp(self.mjd)


@dataclass(frozen=True)
class DetectorEvents:
    """Header facts for one detector's event HDU. Rows are streamed, never held."""

    detector: str
    extname: str
    detnam: str
    rows: int
    tstart_mjd: float
    tstop_mjd: float

    @property
    def instrument_id(self) -> Identifier:
        return Identifier(f"hel1os-{self.detector}")


@dataclass(frozen=True)
class EventList:
    """A validated `evt.fits`: all four detectors present, none read into memory."""

    source_path: Path
    source_digest: Digest
    detectors: tuple[DetectorEvents, ...]

    def detector(self, name: str) -> DetectorEvents:
        for candidate in self.detectors:
            if candidate.detector == name.lower():
                return candidate
        _fits.fail("F-03", f"/{self.source_path.name}",
                   f"no events for detector {name!r}; present: "
                   f"{[d.detector for d in self.detectors]}")

    def events(self, name: str) -> Iterator[Event]:
        """Validate and yield one detector's events lazily, row by row (§2.5 r7)."""
        from astropy.io import fits

        target = self.detector(name.lower())
        source = self.source_path.name
        where = f"/{source}#{target.extname}"
        allowance = TIME_REPRESENTATION_ALLOWANCE_S / SECONDS_PER_DAY
        earliest, latest = target.tstart_mjd - allowance, target.tstop_mjd + allowance
        czt = family_of(target.detector) == "czt"

        with fits.open(self.source_path) as hdul:
            table = _fits.hdu(hdul, target.extname, source=source)
            mjd = _fits.column(table, "mjd", source=source, hdu_name=target.extname)
            hlsobt = _fits.column(table, "hlsobt", source=source, hdu_name=target.extname)
            temp = _fits.column(table, "currtemp", source=source, hdu_name=target.extname)
            chn = _fits.column(table, "chn", source=source, hdu_name=target.extname)
            ener = _fits.column(table, "ener", source=source, hdu_name=target.extname)
            recnum = _fits.column(table, "recnum", source=source, hdu_name=target.extname)
            isot = _fits.column(table, ISOT_COLUMN, source=source, hdu_name=target.extname)
            pix = (_fits.column(table, "pix", source=source, hdu_name=target.extname)
                   if czt else None)
            offset = (_fits.column(table, "offsetchn", source=source, hdu_name=target.extname)
                      if czt else None)

            previous: float | None = None
            for index in range(len(mjd)):
                when = float(mjd[index])
                if not earliest <= when <= latest:
                    _fits.fail(
                        "F-06", f"{where}/mjd[{index}]",
                        f"mjd[{index}] = {when!r} is outside the header span "
                        f"[{target.tstart_mjd!r}, {target.tstop_mjd!r}] widened by ε_t = "
                        f"{TIME_REPRESENTATION_ALLOWANCE_S} s (§2.5 r7, §5.1)",
                    )

                stamp = str(isot[index])
                residual, bound = isot_disagreement_s(
                    when, stamp, pointer=f"{where}/{ISOT_COLUMN}[{index}]")
                if residual > bound:
                    _fits.fail(
                        "F-06", f"{where}/{ISOT_COLUMN}[{index}]",
                        f"V-EVT-2: {ISOT_COLUMN} {stamp!r} and mjd {when!r} disagree by "
                        f"{residual!r} s, beyond ½·r_isot + ε_t = {bound!r} s (§2.5 r7). Two "
                        f"representations of one instant that disagree are an ambiguous time.",
                    )

                if previous is not None and when < previous:
                    _fits.fail(
                        "F-16", f"{where}/mjd[{index}]",
                        f"mjd decreases at row {index}: {previous!r} then {when!r}. §2.5 "
                        f"requires non-decreasing mjd; the archive falsifies the rule and the "
                        f"falsification is recorded OPEN in CONTRA-008, so it is enforced as "
                        f"written.",
                    )
                previous = when

                energy = float(ener[index])
                if not energy > 0:
                    _fits.fail(
                        "F-19", f"{where}/ener[{index}]",
                        f"ener[{index}] is {energy!r}; §2.5 validates ener > 0",
                    )

                yield Event(
                    mjd=when,
                    hlsobt=float(hlsobt[index]),
                    energy_kev=energy,
                    channel=int(chn[index]),
                    detector_temp_c=float(temp[index]),
                    recnum=int(recnum[index]),
                    utc_isot=stamp,
                    pixel=int(pix[index]) if pix is not None else None,
                    offset_channel=int(offset[index]) if offset is not None else None,
                )


def isot_disagreement_s(mjd: float, isot: str, *, pointer: str) -> tuple[float, float]:
    """V-EVT-2: how far apart the two representations are, and the bound they must meet.

    The bound is `½·r_isot + ε_t` (§2.5 r7). `r_isot` is the resolution the string carries —
    10⁻ⁿ s for n fractional digits — so it is read from the value, not chosen. The column is
    named `utc-isot`; a string that declares a non-UTC offset contradicts that name and is
    refused rather than converted.
    """
    text = isot.strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        _fits.fail("F-06", pointer,
                   f"{text!r} is not an ISO-8601 instant, so V-EVT-2 cannot be evaluated; "
                   f"§5 admits no ambiguous time")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    elif parsed.utcoffset() != timedelta(0):
        _fits.fail("F-06", pointer,
                   f"{text!r} declares a non-UTC offset in a column named {ISOT_COLUMN!r}")

    fraction = text.partition(".")[2]
    digits = len(fraction) - len(fraction.lstrip("0123456789"))
    resolution = 10.0 ** -digits
    residual = abs((mjd - MJD_UNIX_EPOCH) * SECONDS_PER_DAY - parsed.timestamp())
    return residual, 0.5 * resolution + TIME_REPRESENTATION_ALLOWANCE_S


def parse(path: Path, digest: Digest) -> EventList:
    """Validate `evt.fits` headers: four detector HDUs, DETNAM, columns, `ener` unit, span."""
    from astropy.io import fits

    source = path.name
    try:
        opened = fits.open(path)
    except OSError as exc:
        _fits.fail("F-01", f"/{source}", f"not readable as FITS: {exc}")

    found: list[DetectorEvents] = []
    with opened as hdul:
        present = {hdu.name.upper() for hdu in hdul}
        missing = [
            EVENT_HDU[d] for d in DETECTORS if EVENT_HDU[d].upper() not in present
        ]
        if missing:
            _fits.fail(
                "F-03", f"/{source}",
                f"event HDU(s) {missing} absent. §2.5 requires all four detectors; three "
                f"detectors' events are a different measurement, not a smaller one.",
            )

        for detector in DETECTORS:
            extname = EVENT_HDU[detector]
            table = _fits.hdu(hdul, extname, source=source)
            header = table.header

            detnam = str(_fits.keyword(header, "DETNAM", source=source, hdu_name=extname))
            if detnam.upper() != DETNAM[detector].upper():
                _fits.fail(
                    "F-03", f"/{source}#{extname}/DETNAM",
                    f"DETNAM is {detnam!r} in HDU {extname!r}, expected "
                    f"{DETNAM[detector]!r}. A mismatch means the HDU name and the detector "
                    f"it holds disagree.",
                )

            required = REQUIRED_COLUMNS + (CZT_COLUMNS if family_of(detector) == "czt" else ())
            declared = {
                name: _fits.declared_unit(table, name, source=source, hdu_name=extname)
                for name in required
            }
            if declared["ener"] != ENERGY_UNIT:
                _fits.fail(
                    "F-07", f"/{source}#{extname}/ener",
                    f"ener declares unit {declared['ener']!r}; §2.5 records calibrated "
                    f"{ENERGY_UNIT!r}. An energy is never stated over a different declaration.",
                )

            tstart = float(_fits.keyword(header, "TSTART", source=source, hdu_name=extname))
            tstop = float(_fits.keyword(header, "TSTOP", source=source, hdu_name=extname))
            if not tstart < tstop:
                _fits.fail("F-05", f"/{source}#{extname}/TSTART",
                           f"TSTART {tstart!r} / TSTOP {tstop!r} do not bound an interval")

            found.append(DetectorEvents(
                detector=detector,
                extname=extname,
                detnam=detnam,
                rows=int(_fits.keyword(header, "NAXIS2", source=source, hdu_name=extname)),
                tstart_mjd=tstart,
                tstop_mjd=tstop,
            ))

    return EventList(source_path=path, source_digest=digest, detectors=tuple(found))


__all__ = [
    "CZT_COLUMNS", "DETNAM", "ENERGY_UNIT", "EVENT_HDU", "ISOT_COLUMN", "REQUIRED_COLUMNS",
    "DetectorEvents", "Event", "EventList", "isot_disagreement_s", "parse",
]

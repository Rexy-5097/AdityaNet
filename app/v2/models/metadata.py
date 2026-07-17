"""
app/v2/models/metadata.py — shared metadata models (Milestone I).

Implements the provenance/quality vocabulary of the FROZEN contract
`artifacts/v2/phase05/PARSER_SPECIFICATION.md` (commit 6de0eb2). No FITS access.

Contract anchors: §3 T7 provenance_manifest, §3 quality-flag convention,
§5 failure matrix.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

PARSER_VERSION = "v2-0.5.2"

# ── §5 Failure Matrix: the frozen rule identifiers ──────────────────────────
FAIL_RULES: dict[str, str] = {
    "F-01": "FITS unreadable / not FITS / gzip error",
    "F-02": "Expected HDU absent by name",
    "F-03": "evt.fits lacking any of the 4 detector HDUs",
    "F-04": "Column absent by name (case-insensitive lookup failed)",
    "F-05": "MJDREFI!=40587 or TIMESYS!=UTC or TIMEUNIT!=s (SoLEXS)",
    "F-06": "Epoch resolution R-1 failed, or .pi TSTART[0] != .lc TSTART",
    "F-07": "Declared unit contradicts assumption (HDUCLAS3 vs EXTNAME; cts/sec vs counts)",
    "F-08": ".pi CHANNEL vector not constant across rows",
    "F-09": "sum(STOP-START) != EXPOSURE +/-1s",
    "F-10": "Band EXTNAME outside the allowlist",
    "F-11": "Attempt to merge SoLEXS PI(340) with HEL1OS PHA(341)",
    "F-12": "GTI NAXIS2==0 -> NOT FATAL: detector_active=False (the one deliberate exception)",
    "F-13": "Member SHA-256 != Phase 0.5.1 manifest",
    "F-14": "Version precedence unresolved after all tie-breaks",
    "F-15": "Duplicate (timestamp, detector) in output",
    "F-16": "Timestamps non-monotonic or duplicated in input",
    "F-17": "NAXIS2 != expected (86400 for SoLEXS daily)",
    "F-18": "Unknown file type not on allowlist",
    "F-19": "Negative counts / negative EXPOSURE / live_time_s > 60",
    "F-20": "Output row count != expected minutes for the day",
}


class FailLoud(RuntimeError):
    """Terminates the run. Contract §5: no silent recovery, ever.

    Carries the frozen rule id so every termination is traceable to the contract
    rather than to an ad-hoc check.
    """

    def __init__(self, rule: str, detail: str, *, file: str | None = None,
                 hdu: str | None = None, expected: Any = None, got: Any = None):
        if rule not in FAIL_RULES:
            raise KeyError(f"unknown fail-loud rule {rule!r}; contract §5 is frozen")
        self.rule, self.detail, self.file, self.hdu = rule, detail, file, hdu
        self.expected, self.got = expected, got
        loc = " | ".join(x for x in (f"file={file}" if file else None,
                                     f"hdu={hdu}" if hdu else None) if x)
        exp = ""
        if expected is not None or got is not None:
            exp = f" | expected={expected!r} got={got!r}"
        super().__init__(f"[{rule}] {FAIL_RULES[rule]} :: {detail}{(' | ' + loc) if loc else ''}{exp}")


class Instrument(str, Enum):
    SOLEXS = "solexs"
    HEL1OS = "hel1os"


class Product(str, Enum):
    LC = "lc"
    PI = "pi"
    GTI = "gti"
    HK = "hk"
    EVENTS = "events"
    SPECTRA = "spectra"
    LIGHTCURVE = "lightcurve"


class ChanType(str, Enum):
    """§2.7 F-11: PI(340, SoLEXS) and PHA(341, HEL1OS) are incommensurable."""
    PI = "PI"
    PHA = "PHA"


@dataclass(frozen=True)
class TimeEpoch:
    """Resolved time epoch. §2 / R-1: never assumed, always resolved or F-06."""
    kind: str                      # "unix_seconds" | "mjd_days"
    resolved_by: str               # "header_MJDREFI" | "R-1_empirical" | ...
    mjdrefi: int | None = None

    UNIX_MJDREFI = 40587           # MJD 40587 == 1970-01-01 (contract §2.1)


@dataclass
class Provenance:
    """§3 T7 provenance_manifest — one row per parsed source file."""
    src_file: str
    src_sha256: str
    instrument: str
    detector: str | None
    product: str
    archive_version: str | None
    obs_date: str | None
    orbit_id: str | None
    creator: str | None
    processing_date: str | None
    rows_in: int
    rows_out: int
    time_epoch_resolution: str
    assumptions_applied: list[str] = field(default_factory=list)
    parser_version: str = PARSER_VERSION
    parsed_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedProduct:
    """Uniform parser return. Contract: absence is data (q_no_data), never a fill."""
    data: Any
    provenance: Provenance
    detector_active: bool = True      # False only via F-12 (empty GTI)
    header: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

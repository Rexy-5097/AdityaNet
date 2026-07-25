"""
app/v2/parsers/base.py — parser interfaces + safe FITS access (Milestone I).

Implements the contract's non-negotiable access rules so that individual parsers
cannot violate them by omission:

  §5 F-02  HDU lookup BY NAME, never by index.
  §5 F-04  Column lookup case-insensitive (SoLEXS 'START' vs HEL1OS 'tstart').
  §5       `header.get(K, default)` is BANNED for physically meaningful keys —
           that idiom is the direct cause of v1's thirty-sprint failure. The only
           reader exposed here raises F-02 on a missing key.
  §8 A-2   case-insensitivity is mandatory, not stylistic.

No parsing logic lives here — only the guarded primitives every parser must use.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Iterable

from app.v2.models.metadata import FailLoud, ParsedProduct

# §8 / F-18: macOS AppleDouble sidecars exist in the extracted store on this
# exFAT volume and MUST NOT be globbed as data.
APPLEDOUBLE = re.compile(r"(^|/)\._")


def is_appledouble(path: str) -> bool:
    return bool(APPLEDOUBLE.search(path))


def require_header(header, key: str, *, file: str | None = None,
                   hdu: str | None = None) -> Any:
    """Read a mandatory header key. NEVER defaults (contract §5).

    v1 wrote `header.get("MJDREF", 58484.0)` against files whose real key is
    MJDREFI -> a silent ~49-year time error -> simulation fallback. This function
    exists so that mistake is unrepresentable.
    """
    if key not in header:
        raise FailLoud("F-02", f"mandatory header key {key!r} absent",
                       file=file, hdu=hdu, expected=key, got=None)
    return header[key]


def get_hdu(hdul, name: str, *, file: str | None = None):
    """Fetch an HDU BY NAME (§5 F-02). HDU order is not a contract."""
    for h in hdul:
        if (h.name or "").strip().upper() == name.strip().upper():
            return h
    raise FailLoud("F-02", f"HDU {name!r} absent",
                   file=file, expected=name,
                   got=[h.name for h in hdul])


def get_column(hdu, name: str, *, file: str | None = None,
               hdu_name: str | None = None):
    """Fetch a column case-insensitively (§5 F-04, §8 A-2)."""
    cols = {c.name.strip().lower(): c.name for c in hdu.columns}
    key = name.strip().lower()
    if key not in cols:
        raise FailLoud("F-04", f"column {name!r} absent",
                       file=file, hdu=hdu_name or hdu.name,
                       expected=name, got=list(cols.values()))
    return hdu.data[cols[key]]


def has_column(hdu, name: str) -> bool:
    return name.strip().lower() in {c.name.strip().lower() for c in hdu.columns}


def require_equal(actual: Any, expected: Any, rule: str, detail: str, **kw) -> None:
    """Assert a frozen expectation or terminate with the contract's rule id."""
    if actual != expected:
        raise FailLoud(rule, detail, expected=expected, got=actual, **kw)


class BaseParser(ABC):
    """All parsers return a ParsedProduct with full provenance.

    Contract: parsers NEVER simulate, NEVER impute, NEVER default. A parser may
    return `detector_active=False` only through F-12 (legal empty GTI).
    """

    instrument: str
    product: str

    @abstractmethod
    def parse(self, path: str, *, sha256: str | None = None) -> ParsedProduct:
        """Parse one source file. Raises FailLoud on any contract violation."""

    @staticmethod
    def _reject_appledouble(path: str) -> None:
        if is_appledouble(path):
            raise FailLoud("F-18", "AppleDouble sidecar passed to a parser",
                           file=path)


class ParserRegistry:
    """Maps (instrument, product) -> parser. Allowlist-driven (§5 F-18)."""

    def __init__(self) -> None:
        self._reg: dict[tuple[str, str], BaseParser] = {}

    def register(self, parser: BaseParser) -> BaseParser:
        self._reg[(parser.instrument, parser.product)] = parser
        return parser

    def get(self, instrument: str, product: str) -> BaseParser:
        try:
            return self._reg[(instrument, product)]
        except KeyError:
            raise FailLoud("F-18", f"no parser registered for {instrument}/{product}")

    def known(self) -> Iterable[tuple[str, str]]:
        return self._reg.keys()


REGISTRY = ParserRegistry()

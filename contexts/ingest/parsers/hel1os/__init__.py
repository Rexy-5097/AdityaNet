"""HEL1OS parsers — `lc`, `spectra`, `hk`, `gti`, `events`, and orbit precedence (M3/E5/#18).

Each implements its section of `SPEC-parsers@r7`:

    orbit     §4    identity and version precedence. No merge API, no coverage map (#19).
    lc        §2.6  per-detector band rates; band edges parsed from EXTNAME; CTR unit read.
    spectra   §2.7  PHA spectra; 341 for CZT, 511 for CdTe; epoch resolution R-1 (r7 bound).
    hk        §2.8  housekeeping in ARCHIVE ORDER; every decisive column with its unit.
    gti       §2.9  per-detector good time intervals; lowercase column names.
    events    §2.5  photon events, row rules per r7. Exposed, and deliberately not ingestible.

Where a comparison involves an MJD-derived time it uses §5.1's time-representation allowance
`ε_t` (CONTRA-007). §2.5's non-decreasing event rule is enforced as written although the archive
falsifies it; that falsification is recorded OPEN (CONTRA-008).

TWO INSTRUMENTS, NO SHARED CONVENTIONS
--------------------------------------
Nothing here imports `parsers.solexs`, and nothing there imports this. The two instruments
disagree on almost every convention — counts vs rates, undeclared vs declared units, Unix
seconds vs MJD, PI(340) vs PHA(341)/PHA(511), uppercase vs lowercase column names — and
F-07 and F-11 exist because assuming a shared convention across them is the specific error
that has already been made once.
"""

from contexts.ingest.parsers.hel1os import events, gti, hk, lc, orbit, spectra

__all__ = ["events", "gti", "hk", "lc", "orbit", "spectra"]

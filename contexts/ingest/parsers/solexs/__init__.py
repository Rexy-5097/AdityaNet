"""SoLEXS parsers — `.lc`, `.pi` and `.gti` (M3/E5/#17).

Each implements its section of `SPEC-parsers@r6`, which is a **contract**: a deviation
requires a logged amendment, not a code change.

    lc    §2.1  total-band counts per second. NaN is data, not an error.
    pi    §2.2  340-channel PI spectra per second. Ordinal channels; keV is prohibited.
    gti   §2.3  inclusive second-marks; Σ(STOP−START+1) == EXPOSURE, exactly.

`.hk` (§2.4, v1.1 only, 5 of 436 days) is NOT implemented here: TIS E5 §5 lists this epic's
SoLEXS modules as `parsers/solexs/{lc,pi,gti}` and assigns no `.hk` module to any issue. The
gap is reported in the Issue #17 completion record rather than filled by guessing at scope.
"""

from contexts.ingest.parsers.solexs import gti, lc, pi

__all__ = ["gti", "lc", "pi"]

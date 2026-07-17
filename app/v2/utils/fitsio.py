"""
app/v2/utils/fitsio.py — guarded FITS opening (Milestone II).

Contract §5 F-01: unreadable / not-FITS / gzip errors terminate. There is no
fallback path, and by construction there is nowhere for one to live: this module
either yields an HDUList or raises FailLoud.
"""
from __future__ import annotations

import gzip
import io
from contextlib import contextmanager

from astropy.io import fits

from app.v2.models.metadata import FailLoud
from app.v2.parsers.base import is_appledouble


@contextmanager
def open_fits(path: str, *, memmap: bool = False):
    """Open a .fits or .fits.gz/.gz FITS file. F-01 on any failure.

    NOTE: no `except ... : return simulated_data()`. v1's parse_fits.py fell back
    to a random generator on exactly this code path, silently, for 30 sprints.
    """
    if is_appledouble(path):
        raise FailLoud("F-18", "AppleDouble sidecar is not data", file=path)
    hdul = None
    try:
        if path.endswith(".gz"):
            with gzip.open(path, "rb") as f:
                buf = io.BytesIO(f.read())
            hdul = fits.open(buf, memmap=False, lazy_load_hdus=False)
        else:
            hdul = fits.open(path, memmap=memmap, lazy_load_hdus=True)
        yield hdul
    except FailLoud:
        raise
    except Exception as e:                      # noqa: BLE001 - re-raised as F-01
        raise FailLoud("F-01", f"cannot read FITS: {type(e).__name__}: {e}",
                       file=path) from e
    finally:
        if hdul is not None:
            try:
                hdul.close()
            except Exception:                   # noqa: BLE001
                pass

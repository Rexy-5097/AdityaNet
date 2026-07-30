"""The ISSDC-PRADAN acquisition channel (M3/E5/#16).

Registered with latency class `~33d` and granularity `daily-archive`, per E5 §18.

The only channel that exists. It is constructed by a caller, not looked up: ADR-0003 does not
authorise a registry or a dispatch layer, and one channel does not need either.
"""

from contexts.ingest.adapters.issdc_pradan.adapter import (
    ARCHIVE_STEM,
    AUTHORITY,
    GRANULARITY,
    LATENCY,
    PORTAL,
    SOURCE_ID,
    ArchiveProduct,
    IssdcPradanAdapter,
)

__all__ = [
    "ARCHIVE_STEM",
    "AUTHORITY",
    "ArchiveProduct",
    "GRANULARITY",
    "IssdcPradanAdapter",
    "LATENCY",
    "PORTAL",
    "SOURCE_ID",
]

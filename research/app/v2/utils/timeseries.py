"""
app/v2/utils/timeseries.py — consumer utilities OUTSIDE the parser layer.

Contract §2.8 (r4) establishes a general v2 principle:

    THE PARSER IS A LOSSLESS REPRESENTATION OF THE ARCHIVE.

Reading and transforming are separate acts. A parser that silently reorders is
no longer a faithful reader. So HEL1OS housekeeping is returned in archive
(telemetry-arrival) order, inversions and all, and any consumer that needs
chronological order must invoke `chronological_sort()` EXPLICITLY.

This module is deliberately not importable from `app.v2.parsers` -- the
separation is structural, not stylistic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app.v2.models.metadata import PARSER_VERSION, FailLoud


@dataclass(frozen=True)
class SortRecord:
    """Provenance of a reordering. §2.8 r4: the utility MUST record provenance."""
    time_column: str
    n_rows: int
    n_out_of_order: int
    max_backward_step_s: float
    was_already_sorted: bool
    algorithm: str = "stable_mergesort"
    utility_version: str = PARSER_VERSION
    applied_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_row(self) -> dict:
        return asdict(self)


def inversion_stats(times, *, unit: str = "s") -> tuple[int, float]:
    """Count order inversions and the largest backward step.

    §2.8 r4: inversion statistics are RECORDED, never thresholded. There is no
    "acceptable jitter" constant here and there must never be one -- inventing
    a tolerance is the error rejected in CONTRADICTION-003.

    Args:
        times: 1-D array of timestamps.
        unit: "s" | "mjd" | "datetime" -- how to scale the backward step to seconds.

    Returns:
        (n_out_of_order, max_backward_step_s). Both zero for a sorted input.
    """
    t = np.asarray(times)
    if t.size < 2:
        return 0, 0.0
    if unit == "datetime" or np.issubdtype(t.dtype, np.datetime64):
        # pd.DatetimeIndex is tz-aware; .view/.astype on tz-aware is deprecated,
        # so go through pandas' own int64 nanosecond view.
        ns = pd.DatetimeIndex(t).asi8
        d = np.diff(ns) / 1e9
    else:
        d = np.diff(t.astype(np.float64))
        if unit == "mjd":
            d = d * 86400.0
        elif unit != "s":
            raise ValueError(f"unknown unit {unit!r}")
    back = d[d < 0]
    return int(back.size), float(-back.min()) if back.size else 0.0


def chronological_sort(df: pd.DataFrame, time_column: str, *,
                       unit: str = "datetime") -> tuple[pd.DataFrame, SortRecord]:
    """Return `df` in chronological order, plus provenance of the reordering.

    Contract §2.8 (r4) requires this utility to:
      * preserve EVERY row     -- no filtering, no dropping, no dedup
      * preserve EVERY value   -- no imputation, no rounding, no coercion
      * be DETERMINISTIC       -- stable mergesort; equal keys keep archive order
      * record provenance      -- returned as a SortRecord

    This is a REORDERING, never a repair. If two rows share a timestamp they both
    survive in their original relative order; duplicate timestamps are a parser
    concern (F-16), not this utility's to silently resolve.

    Raises:
        FailLoud F-04 if `time_column` is absent.
    """
    if time_column not in df.columns:
        raise FailLoud("F-04", f"time column {time_column!r} absent",
                       expected=time_column, got=list(df.columns))

    n_inv, max_back = inversion_stats(df[time_column].to_numpy(), unit=unit)
    already = n_inv == 0

    # kind="stable" -> mergesort: deterministic, and ties retain archive order.
    out = df.sort_values(time_column, kind="stable", ignore_index=True)

    # Post-conditions: the "lossless" claim is asserted, not asserted-by-comment.
    if len(out) != len(df):
        raise FailLoud("F-20", "chronological_sort changed the row count",
                       expected=len(df), got=len(out))
    if list(out.columns) != list(df.columns):
        raise FailLoud("F-20", "chronological_sort changed the columns",
                       expected=list(df.columns), got=list(out.columns))

    return out, SortRecord(time_column=time_column, n_rows=len(df),
                           n_out_of_order=n_inv, max_backward_step_s=max_back,
                           was_already_sorted=already)

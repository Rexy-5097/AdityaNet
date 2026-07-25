#!/usr/bin/env python3
"""Stage 2 derivation: frozen artifacts -> web-consumable JSON.

This is the only bridge between the scientific pipeline and the web platform, and
it is deliberately narrow. It reads committed artifacts, resolves each displayed
quantity to an RFC-6901 JSON pointer inside the artifact that produced it, and
emits both the page payloads and a flat measurement map that the frontend's code
generator turns into TypeScript.

The invariant this file exists to serve: a developer cannot type a measured number
into the web application. They reference a measurement; this script proves the
reference resolves; and `check.ts` later re-reads these same artifacts to confirm
the rendered HTML matches.

READ-ONLY. This script never writes to the frozen dataset or to artifacts/. It is
enforced, not merely intended: every input is opened with O_RDONLY and the input
digests are re-verified after writing.

Usage:
    python scripts/web/derive.py [--out web/src/generated/data]
"""

from __future__ import annotations

import argparse
import hashlib
import re
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

FREEZE_MANIFEST = Path("artifacts/v2/phase05/freeze_manifest.json")
BENCHMARK_RESULTS = Path("artifacts/v2/ml/benchmark_results.json")

API_VERSION = "v1"


# ─── Read-only artifact access ───────────────────────────────────────────────


def read_artifact(relative: Path) -> tuple[Any, str]:
    """Load a JSON artifact read-only and return (parsed, sha256).

    Opened with O_RDONLY so that a future edit to this script cannot accidentally
    truncate a scientific artifact. The digest is returned rather than looked up so
    that every emitted reference is provably the file that was actually read.
    """
    path = REPO_ROOT / relative
    fd = os.open(path, os.O_RDONLY)
    try:
        raw = os.read(fd, os.fstat(fd).st_size)
    finally:
        os.close(fd)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def git_commit() -> str:
    """Short commit of the working tree, for attribution on every measurement."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ─── JSON pointers (RFC 6901) ────────────────────────────────────────────────


def escape_token(token: str) -> str:
    """Escape one JSON-pointer token.

    Order matters: '~' must be escaped before '/', otherwise the '~1' produced by
    escaping a slash would itself be re-escaped into '~01'. The benchmark artifact's
    top-level keys are literally 'M/X NOWCAST', so this path is exercised on every
    run rather than being defensive code nobody executes.
    """
    return token.replace("~", "~0").replace("/", "~1")


def make_pointer(*tokens: str) -> str:
    return "".join("/" + escape_token(token) for token in tokens)


def resolve_pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC-6901 pointer, raising with the failing prefix on a miss.

    A silent None here would let a stale reference render as a blank metric, which is
    exactly the failure mode this project cannot tolerate.
    """
    if pointer == "":
        return document

    current = document
    walked: list[str] = []
    for raw_token in pointer.lstrip("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        walked.append(token)
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise KeyError(
                f"JSON pointer {pointer!r} failed at {'/'.join(walked)!r}. "
                f"The artifact shape changed, or the reference is stale."
            )
    return current


# ─── Measurement model ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Measurement:
    """One displayed quantity, bound to the artifact location that produced it.

    `precision` is the number of decimal places the value is *stored* with. Rendering
    may not exceed it: displaying 0.95 for a stored 0.9539 discards information, and
    displaying 0.95390 fabricates it.
    """

    key: str
    value: float
    precision: int
    artifact: str
    pointer: str
    sha256: str
    commit: str
    label: str
    unit: str | None = None
    n: int | None = None
    ci95: tuple[float, float] | None = None

    def to_json(self) -> dict[str, Any]:
        record = asdict(self)
        record.pop("key")
        return {k: v for k, v in record.items() if v is not None}


class MeasurementSet:
    """Collects measurements and guarantees every key is unique and resolvable."""

    def __init__(self) -> None:
        self._items: dict[str, Measurement] = {}

    def add(
        self,
        *,
        document: Any,
        artifact: Path,
        sha256: str,
        commit: str,
        tokens: tuple[str, ...],
        label: str,
        precision: int,
        unit: str | None = None,
        n: int | None = None,
        ci_tokens: tuple[str, ...] | None = None,
    ) -> Measurement:
        pointer = make_pointer(*tokens)
        value = resolve_pointer(document, pointer)
        if not isinstance(value, (int, float)):
            raise TypeError(f"{artifact}{pointer} resolved to {type(value).__name__}, not a number")

        ci95: tuple[float, float] | None = None
        if ci_tokens is not None:
            raw_ci = resolve_pointer(document, make_pointer(*ci_tokens))
            ci95 = (float(raw_ci[0]), float(raw_ci[1]))

        key = f"{artifact.as_posix()}#{pointer}"
        if key in self._items:
            raise ValueError(f"duplicate measurement key {key!r}")

        measurement = Measurement(
            key=key,
            value=float(value),
            precision=precision,
            artifact=artifact.as_posix(),
            pointer=pointer,
            sha256=sha256,
            commit=commit,
            label=label,
            unit=unit,
            n=n,
            ci95=ci95,
        )
        self._items[key] = measurement
        return measurement

    def to_json(self) -> dict[str, Any]:
        return {key: item.to_json() for key, item in sorted(self._items.items())}


# ─── Derivation ──────────────────────────────────────────────────────────────


CANONICAL_T1 = Path("artifacts/v2/phase05/canonical/T1")
PHASE05 = Path("artifacts/v2/phase05")


ML = Path("artifacts/v2/ml")

MODEL_LABELS = {
    "random": "Random",
    "majority": "Majority",
    "climatology": "Climatology",
    "persistence": "Persistence",
    "threshold_rate": "Threshold (rate)",
    "logistic": "Logistic regression",
    "random_forest": "Random forest",
    "lightgbm": "LightGBM",
}

# Trivial reference points. Distinguished from real candidates so the table can say so
# in text: persistence scores 0.98 by predicting y(t) ~ y(t-1), which measures how
# autocorrelated the label is, not how good a forecaster is.
BASELINE_MODELS = {"random", "majority", "climatology", "persistence"}


def finite(value: Any) -> float | None:
    """Coerce a float, mapping NaN and infinities to None.

    ISSUE-007: `json.dump` emits bare `NaN` unless allow_nan=False, and RFC 8259 has no
    such literal — `JSON.parse` rejects the entire document. The affected fields are
    Brier scores for models that emit hard classifications rather than probabilities:
    legitimately undefined, illegitimately encoded. Fixing it here stops the defect
    propagating into the web layer, where it would break every page that loads it.
    """
    if not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if value == value and value not in (float("inf"), float("-inf")) else None


def derive_findings() -> dict[str, Any]:
    """Benchmark table and ablation, from the ML artifacts.

    Only NUMBERS are taken from JSON. The verdicts — "statistically indistinguishable",
    "significantly worse" — stay in the prose reports and are rendered verbatim, because
    they are adjudications made under a pre-registered protocol, not properties this
    script may recompute. A site that recalculated significance could disagree with the
    paper it is publishing.
    """
    benchmark, _ = read_artifact(ML / "benchmark_results.json")
    ablation, _ = read_artifact(ML / "ablation_results.json")

    tasks = []
    for task_key in ("M/X NOWCAST", "M/X 30-MIN PREDICTION"):
        task = benchmark[task_key]
        rows = []
        for model_key, result in task["results"].items():
            minute = result.get("minute", {})
            event = result.get("event", {})
            boot = result.get("bootstrap", {})
            rows.append(
                {
                    "model": model_key,
                    "label": MODEL_LABELS.get(model_key, model_key),
                    "is_baseline": model_key in BASELINE_MODELS,
                    "roc_auc": finite(minute.get("roc_auc")),
                    "roc_auc_ci95": [finite(v) for v in boot.get("roc_auc_ci95", [])] or None,
                    "event_recall": finite(event.get("event_recall")),
                    "event_recall_ci95": [finite(v) for v in boot.get("event_recall_ci95", [])] or None,
                    "false_event_runs": event.get("false_event_runs"),
                    "n_events": event.get("n_events"),
                    "precision": finite(minute.get("precision")),
                    "brier": finite(minute.get("brier")),
                    "latency_us": finite(result.get("latency_us_per_sample")),
                }
            )
        tasks.append(
            {
                "key": task_key,
                "slug": "nowcast" if "NOWCAST" in task_key else "prediction",
                "label": "M/X nowcast" if "NOWCAST" in task_key else "M/X 30-minute prediction",
                "n_train": task["n_train"],
                "n_val": task["n_val"],
                "n_test": task["n_test"],
                "test_positive_rate": finite(task["test_positive_rate"]),
                "rows": rows,
            }
        )

    return {
        "tasks": tasks,
        "ablation": {k: finite(v) if isinstance(v, float) else v for k, v in ablation.items()},
        "meta": {k: v for k, v in benchmark["meta"].items()},
        "sources": {
            "benchmark": (ML / "benchmark_results.json").as_posix(),
            "ablation": (ML / "ablation_results.json").as_posix(),
        },
    }


def parse_report(relative: Path) -> dict[str, Any]:
    """Split a markdown report into lead plus level-2 sections, prose preserved."""
    text = (REPO_ROOT / relative).read_text()
    meta = dict(re.findall(r"<!--\s*([A-Z ]+):\s*(.*?)\s*-->", text))
    title = re.search(r"^# (.+)$", text, re.M)
    parts = re.split(r"^## (.+?)$", text, flags=re.M)
    lead = re.sub(r"<!--.*?-->", "", parts[0], flags=re.S)
    lead = re.sub(r"^# .+$", "", lead, flags=re.M).strip()
    return {
        "title": title.group(1).strip() if title else relative.stem,
        "date": meta.get("DATE", ""),
        "lead": lead,
        "sections": [
            {"heading": parts[i].strip(), "body": parts[i + 1].strip()}
            for i in range(1, len(parts) - 1, 2)
        ],
        "source": relative.as_posix(),
    }


def derive_days(out_dir: Path) -> list[dict[str, Any]]:
    """Per-day light curves from T1, plus the coverage index.

    Rates are rounded to 2 decimals and emitted as a flat array — one value per minute,
    positionally indexed. Objects with a timestamp key would quadruple the payload for
    information that is implied by position, since T1 is a complete 1440-minute grid.

    Missing minutes are emitted as `null`, never zero and never interpolated. A gap is a
    scientific statement — the instrument was not observing — and filling it would be
    fabricating an observation.
    """
    import pyarrow.parquet as pq

    directory = REPO_ROOT / CANONICAL_T1
    days_dir = REPO_ROOT / "web/public/api/v1/days"
    days_dir.mkdir(parents=True, exist_ok=True)

    index: list[dict[str, Any]] = []
    sources = sorted(p for p in directory.glob("*.parquet") if not p.name.startswith("._"))

    for path in sources:
        table = pq.read_table(path, columns=["rate_total", "live_time_s", "gti_fraction"])
        rates = table.column("rate_total").to_pylist()
        live = table.column("live_time_s").to_pylist()

        clean = [None if (v is None or v != v) else round(float(v), 2) for v in rates]
        finite_vals = [v for v in clean if v is not None]
        if not finite_vals:
            continue

        stem = path.stem
        date = f"{stem[0:4]}-{stem[4:6]}-{stem[6:8]}"
        observed = len(finite_vals)

        (days_dir / f"{date}.json").write_text(
            json.dumps(
                {
                    "date": date,
                    "minutes": len(clean),
                    "observed": observed,
                    "rate": clean,
                    "live_time_total_s": round(sum(v for v in live if v is not None), 1),
                },
                separators=(",", ":"), allow_nan=False,
            )
            + "\n"
        )
        index.append({
            "date": date,
            "peak": round(max(finite_vals), 2),
            "median": round(sorted(finite_vals)[len(finite_vals) // 2], 2),
            "observed": observed,
            "coverage": round(observed / max(len(clean), 1), 4),
        })

    return index


def derive_contradictions() -> list[dict[str, Any]]:
    """Parse the adjudication record into structured records.

    The markdown files remain the source of truth. This extracts only *structure* —
    identity, state, resolving revision, and section boundaries — and carries the prose
    through verbatim. The site never restates a ruling in its own words, so a reader is
    always looking at what the owner actually wrote.

    `declined` is surfaced deliberately: CONTRADICTION-003 records an amendment the
    owner refused, and 004/005 contain rejected alternatives. A ledger that showed only
    accepted outcomes would hide the most credible part of the record — the road not
    taken.
    """
    records: list[dict[str, Any]] = []

    for path in sorted((REPO_ROOT / PHASE05).glob("CONTRADICTION-*.md")):
        if path.name.startswith("._"):
            continue  # AppleDouble sidecar; see derive_star_timeline

        text = path.read_text()
        meta = dict(re.findall(r"<!--\s*([A-Z ]+):\s*(.*?)\s*-->", text))
        title = re.search(r"^# (CONTRADICTION-\d+)\s*—\s*(.+)$", text, re.M)
        status = re.search(r"^\*\*(Status:.*?)\*\*", text, re.M | re.S)
        revision = re.search(r"spec (r\d+)", meta.get("REASON", ""))

        # Split on level-2 headings, keeping each section's body markdown intact.
        parts = re.split(r"^## (.+?)$", text, flags=re.M)
        sections = [
            {"heading": parts[i].strip(), "body": parts[i + 1].strip()}
            for i in range(1, len(parts) - 1, 2)
        ]

        # Everything above the first heading: the framing paragraph.
        lead = re.sub(r"<!--.*?-->", "", parts[0], flags=re.S)
        lead = re.sub(r"^# .+$", "", lead, flags=re.M).strip()

        records.append(
            {
                "id": title.group(1) if title else path.stem,
                "slug": (title.group(1) if title else path.stem).lower(),
                "title": title.group(2).strip() if title else path.stem,
                "state": "OPEN" if meta.get("VERSION STATUS", "").startswith("OPEN") else "CLOSED",
                "date": meta.get("DATE", ""),
                "reason": meta.get("REASON", ""),
                "resolving_revision": revision.group(1) if revision else None,
                "status_line": status.group(1).strip() if status else "",
                "declined_amendment": "DECLINED" in text,
                "lead": lead,
                "sections": sections,
                "source": PHASE05.as_posix() + "/" + path.name,
            }
        )

    if not records:
        raise RuntimeError("no CONTRADICTION-*.md found; the adjudication record is the "
                           "credibility surface and cannot be empty")
    return records


def derive_star_timeline() -> tuple[list[list[Any]], dict[str, float]]:
    """Per-day activity for the experience layer's star.

    Reads every T1 day and reduces it to two numbers: the peak and the median count
    rate. Peak drives emission and bloom; median drives the quiescent corona.

    WHY THESE TWO. SoLEXS is a non-imaging photometer — it measures a single
    disk-integrated rate per minute and carries no spatial information whatsoever.
    Two scalars per day is therefore close to the honest information ceiling for a
    whole-star visual, and P8 forbids a representation richer than its data.

    The star itself is Domain A (artistic), so its *rendering* is unconstrained. Its
    *input* is real, and no number derived here is displayed as a measurement without
    going through the Domain B path.

    Returns the per-day rows and the global range used for normalisation. The range is
    emitted rather than baked in so the client's transform is inspectable.
    """
    import pyarrow.parquet as pq  # local import: only this function needs Arrow

    directory = REPO_ROOT / CANONICAL_T1
    rows: list[list[Any]] = []
    peaks: list[float] = []

    # Exclude AppleDouble sidecars. The project volume is not HFS+, so macOS writes
    # `._NAME` beside every file it touches — and `._20240201.parquet` glob-matches
    # `*.parquet`, then crashes Arrow with "Parquet magic bytes not found in footer".
    #
    # This is the third place the same root cause has surfaced (deployable output,
    # linting, and now data derivation). Any code in this repository that globs a data
    # directory must filter these, because the failure mode is a confusing crash inside
    # a third-party library rather than an obvious "bad file" error.
    sources = sorted(p for p in directory.glob("*.parquet") if not p.name.startswith("._"))

    for path in sources:
        table = pq.read_table(path, columns=["rate_total"])
        column = table.column("rate_total").to_pylist()
        finite = [v for v in column if v is not None and v == v]  # v == v drops NaN
        if not finite:
            continue

        peak = max(finite)
        ordered = sorted(finite)
        median = ordered[len(ordered) // 2]

        # File stem is YYYYMMDD; emit ISO so the client never re-parses a bare digit run.
        stem = path.stem
        date = f"{stem[0:4]}-{stem[4:6]}-{stem[6:8]}"
        rows.append([date, round(peak, 3), round(median, 3)])
        peaks.append(peak)

    if not rows:
        raise RuntimeError(f"no T1 parquet files found under {directory}")

    return rows, {"peak_min": min(peaks), "peak_max": max(peaks)}


def envelope(payload: Any, *, dataset_version: str, dataset_hash: str, commit: str) -> dict:
    """Every response is self-describing about which frozen dataset produced it.

    A consumer who saved this file three years from now must be able to tell what it
    is from the file alone, so provenance travels with the data rather than with the
    URL it was fetched from.
    """
    return {
        "api_version": API_VERSION,
        "dataset_version": dataset_version,
        "dataset_sha256": dataset_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "data": payload,
    }


def derive(out_dir: Path) -> None:
    commit = git_commit()

    manifest, manifest_sha = read_artifact(FREEZE_MANIFEST)
    benchmark, benchmark_sha = read_artifact(BENCHMARK_RESULTS)

    identity = manifest["identity"]
    dataset_version = manifest["dataset_version"]
    dataset_hash = identity["dataset_hash"]

    measurements = MeasurementSet()

    def from_manifest(tokens: tuple[str, ...], label: str, precision: int, **kwargs: Any):
        return measurements.add(
            document=manifest,
            artifact=FREEZE_MANIFEST,
            sha256=manifest_sha,
            commit=commit,
            tokens=tokens,
            label=label,
            precision=precision,
            **kwargs,
        )

    def from_benchmark(tokens: tuple[str, ...], label: str, precision: int, **kwargs: Any):
        return measurements.add(
            document=benchmark,
            artifact=BENCHMARK_RESULTS,
            sha256=benchmark_sha,
            commit=commit,
            tokens=tokens,
            label=label,
            precision=precision,
            **kwargs,
        )

    # Dataset scale. Every figure below is read from the freeze manifest; none is
    # a remembered number. Note that T1 (SoLEXS) and T4 (HEL1OS housekeeping) have
    # genuinely different file counts, a distinction prose routinely blurs.
    headline = [
        from_manifest(("identity", "n_parquet_files"), "Parquet files", 0),
        from_manifest(("tables", "T1", "n_files"), "SoLEXS observation days", 0),
        from_manifest(("tables", "T4", "n_files"), "HEL1OS housekeeping orbits", 0),
        from_manifest(("identity", "total_bytes"), "Dataset size", 0, unit="bytes"),
        # The headline scientific result: a threshold on the SoLEXS count rate.
        from_benchmark(
            ("M/X NOWCAST", "results", "threshold_rate", "minute", "roc_auc"),
            "Threshold nowcast ROC-AUC",
            4,
            ci_tokens=("M/X NOWCAST", "results", "threshold_rate", "bootstrap", "roc_auc_ci95"),
        ),
        from_benchmark(
            ("M/X NOWCAST", "results", "threshold_rate", "event", "event_recall"),
            "Threshold nowcast event recall",
            4,
            n=int(
                resolve_pointer(
                    benchmark, make_pointer("M/X NOWCAST", "results", "threshold_rate", "event", "n_events")
                )
            ),
            ci_tokens=("M/X NOWCAST", "results", "threshold_rate", "bootstrap", "event_recall_ci95"),
        ),
    ]

    overview = {
        "dataset": {
            "version": dataset_version,
            "hash": dataset_hash,
            "hash_short": dataset_hash[:8],
            "archive_span": identity["archive_span"],
            "specification_revision": identity["specification_revision"],
            "build_commit": identity["build_commit_short"],
            "frozen_at": manifest["frozen_at_utc"],
        },
        # The page references measurements by key; it never embeds their values.
        "headline_measurements": [m.key for m in headline],
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "overview.json").write_text(
        json.dumps(
            envelope(overview, dataset_version=dataset_version, dataset_hash=dataset_hash, commit=commit),
            indent=2,
        )
        + "\n"
    )
    (out_dir / "measurements.json").write_text(json.dumps(measurements.to_json(), indent=2) + "\n")

    # Experience layer input. Compact rows rather than objects: 424 days x 3 fields as
    # objects costs ~4x the bytes for no readability gain at this shape.
    timeline_rows, timeline_range = derive_star_timeline()
    (out_dir / "star-timeline.json").write_text(
        json.dumps(
            envelope(
                {
                    "note": (
                        "Per-day peak and median SoLEXS count rate. Drives the Domain A "
                        "star. Rendering is artistic; these inputs are measured."
                    ),
                    "source_table": "T1 solexs_lc_1min",
                    "columns": ["date", "peak_rate", "median_rate"],
                    "unit": "counts/s",
                    "range": timeline_range,
                    "days": timeline_rows,
                },
                dataset_version=dataset_version,
                dataset_hash=dataset_hash,
                commit=commit,
            ),
            separators=(",", ":"),
        )
        + "\n"
    )
    print(f"derive: star timeline {len(timeline_rows)} days, peak max {timeline_range['peak_max']:.1f} counts/s")

    # Adjudication record. Written as one file per contradiction plus an index, so a
    # detail page fetches only what it renders.
    contradictions = derive_contradictions()
    validation_dir = out_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    index = [
        {k: c[k] for k in ("id", "slug", "title", "state", "date", "reason",
                           "resolving_revision", "declined_amendment", "source")}
        for c in contradictions
    ]
    (validation_dir / "index.json").write_text(
        json.dumps(
            envelope(
                {
                    "contradictions": index,
                    "open_count": sum(1 for c in index if c["state"] == "OPEN"),
                    "closed_count": sum(1 for c in index if c["state"] == "CLOSED"),
                    "spec_revision": identity["specification_revision"],
                },
                dataset_version=dataset_version,
                dataset_hash=dataset_hash,
                commit=commit,
            ),
            indent=2,
        )
        + "\n"
    )
    for c in contradictions:
        (validation_dir / f"{c['slug']}.json").write_text(
            json.dumps(
                envelope(c, dataset_version=dataset_version, dataset_hash=dataset_hash, commit=commit),
                indent=2,
            )
            + "\n"
        )
    # Findings. The benchmark table comes from JSON; the conclusions, comparison, and
    # protocol are rendered verbatim, because they are adjudications rather than data.
    findings_dir = out_dir / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    (findings_dir / "benchmark.json").write_text(
        json.dumps(
            envelope(derive_findings(), dataset_version=dataset_version,
                     dataset_hash=dataset_hash, commit=commit),
            indent=2, allow_nan=False,
        )
        + "\n"
    )
    reports = {
        "conclusions": ML / "SCIENTIFIC_CONCLUSIONS.md",
        "comparison": ML / "MODEL_COMPARISON.md",
        "protocol": ML / "EVALUATION_PROTOCOL.md",
        "ablation": ML / "FEATURE_ABLATION_REPORT.md",
        "limitations": ML / "DATASET_LIMITATIONS_FOR_ML.md",
    }
    for name, rel in reports.items():
        (findings_dir / f"{name}.json").write_text(
            json.dumps(
                envelope(parse_report(rel), dataset_version=dataset_version,
                         dataset_hash=dataset_hash, commit=commit),
                indent=2, allow_nan=False,
            )
            + "\n"
        )
    print(f"derive: findings + {len(reports)} reports -> {findings_dir}")

    # Build surface: table inventory with per-table digests, plus the reproduction and
    # environment reports rendered verbatim.
    build_dir = out_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    tables = [
        {
            "key": key,
            "name": table["name"],
            "n_files": table["n_files"],
            "table_hash": table["table_hash"],
            "bytes": sum(f.get("bytes", 0) for f in table.get("files", [])),
        }
        for key, table in manifest["tables"].items()
    ]
    (build_dir / "index.json").write_text(
        json.dumps(
            envelope(
                {
                    "identity": identity,
                    "environment": manifest.get("environment", {}),
                    "tables": tables,
                    "frozen_at": manifest["frozen_at_utc"],
                    "sources": {
                        "manifest": FREEZE_MANIFEST.as_posix(),
                        "dataset_manifest": (PHASE05 / "DATASET_MANIFEST.md").as_posix(),
                        "reproducibility": (PHASE05 / "REPRODUCIBILITY_REPORT.md").as_posix(),
                        "lockfile": (PHASE05 / "requirements.lock").as_posix(),
                    },
                },
                dataset_version=dataset_version, dataset_hash=dataset_hash, commit=commit,
            ),
            indent=2, allow_nan=False,
        )
        + "\n"
    )
    for name, rel in {
        "reproducibility": PHASE05 / "REPRODUCIBILITY_REPORT.md",
        "manifest": PHASE05 / "DATASET_MANIFEST.md",
    }.items():
        (build_dir / f"{name}.json").write_text(
            json.dumps(envelope(parse_report(rel), dataset_version=dataset_version,
                                dataset_hash=dataset_hash, commit=commit),
                       indent=2, allow_nan=False) + "\n"
        )
    # Data surface.
    day_index = derive_days(out_dir)
    (REPO_ROOT / "web/public/api/v1/days/index.json").write_text(
        json.dumps(
            envelope(
                {
                    "days": day_index,
                    "span": [day_index[0]["date"], day_index[-1]["date"]] if day_index else None,
                    "table": "T1 solexs_lc_1min",
                    "unit": "counts/s",
                },
                dataset_version=dataset_version, dataset_hash=dataset_hash, commit=commit,
            ),
            indent=2, allow_nan=False,
        )
        + "\n"
    )
    print(f"derive: {len(day_index)} observation days -> web/public/api/v1/days")

    (out_dir / "coverage.json").write_text(
        json.dumps(
            envelope({"days": day_index, "table": "T1 solexs_lc_1min", "unit": "counts/s"},
                     dataset_version=dataset_version, dataset_hash=dataset_hash, commit=commit),
            indent=2, allow_nan=False,
        )
        + "\n"
    )

    print(f"derive: build surface ({len(tables)} tables) -> {build_dir}")

    # Pipeline surface: stage descriptions plus the quality report that records what the
    # archive actually contained.
    pipeline_dir = out_dir / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    for name, rel in {
        "profile": PHASE05 / "CANONICAL_DATASET_PROFILE.md",
        "quality": PHASE05 / "ARCHIVE_QUALITY_REPORT.md",
        "dictionary": PHASE05 / "DATA_DICTIONARY.md",
    }.items():
        (pipeline_dir / f"{name}.json").write_text(
            json.dumps(envelope(parse_report(rel), dataset_version=dataset_version,
                                dataset_hash=dataset_hash, commit=commit),
                       indent=2, allow_nan=False) + "\n"
        )
    print(f"derive: pipeline surface -> {pipeline_dir}")

    print(f"derive: {len(contradictions)} contradictions "
          f"({sum(1 for c in index if c['state'] == 'OPEN')} open) -> {validation_dir}")

    # Prove the inputs were not modified. Cheap, and it converts the read-only
    # promise into a checked property rather than a comment.
    _, manifest_sha_after = read_artifact(FREEZE_MANIFEST)
    _, benchmark_sha_after = read_artifact(BENCHMARK_RESULTS)
    if (manifest_sha, benchmark_sha) != (manifest_sha_after, benchmark_sha_after):
        print("derive: FATAL — an input artifact changed during derivation", file=sys.stderr)
        raise SystemExit(1)

    print(f"derive: {len(measurements.to_json())} measurements -> {out_dir}")
    print(f"derive: dataset {dataset_version} ({dataset_hash[:8]}) at commit {commit}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "web/src/generated/data")
    derive(parser.parse_args().out)


if __name__ == "__main__":
    main()

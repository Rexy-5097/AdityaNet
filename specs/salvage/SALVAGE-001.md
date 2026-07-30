---
id: SALVAGE-001
title: GOES ingestion and backfill — design knowledge from the v1 generation
status: active
supersedes: []
superseded_by: null
origin: salvaged
source_tag: v1-surya-final
source_paths: research/app/services/ingestion/, research/app/services/backfill/
source_loc: 1408
---

# SALVAGE-001 — GOES ingestion and backfill

> **Provenance.** Design knowledge extracted from the v1 generation before its removal by
> M1/E2/#9. The implementation is recoverable at tag `v1-surya-final`:
>
> ```
> git show v1-surya-final:research/app/services/ingestion/goes_client.py
> git show v1-surya-final:research/app/services/backfill/goes_backfill.py
> git show v1-surya-final:research/app/services/backfill/checkpoint_manager.py
> ```
>
> **This document contains no code and mandates nothing.** It records what the v1 design got
> right, so that the work of rediscovering it is not repeated. Binding decisions live in
> `adr/`. Where v1's approach and the frozen architecture differ, the frozen architecture
> wins and the difference is noted.

## Why this is the salvage worth keeping

v1's Aditya-L1 data was synthetic and its Aditya conclusions are void. **Its GOES side was
real** — the flare catalogue reproduced the May 2024 storm sequence, and `goes_full.parquet`
peaked at 8.69×10⁻⁴ W/m² at exactly 2024-05-14 16:51 UTC, the X8.7 flare, to the minute.
The ingestion path that produced that is the one part of v1 whose output was independently
verifiable, so its design is the part worth carrying forward.

## Design decisions that were right

**Archive the raw payload before any processing.** The client wrote the untouched response
to a raw archive directory *before* parsing, validating or reshaping it. Everything
downstream was therefore reconstructible from bytes the system had actually received rather
than from bytes it had already interpreted. This is the same instinct as
[ADR-0023](../../adr/ADR-0023.md) Tier 0 and [ADR-0005](../../adr/ADR-0005.md), arrived at
independently.

**Schema validation at the boundary, declared not inferred.** The wide telemetry frame was
validated against an explicit schema — timestamp non-null, satellite non-null, both flux
bands nullable, quality flag non-null, source non-null. Nullability was a *declaration*
about which fields may legitimately be absent, not a discovery about which happened to be.
The two flux bands were documented by wavelength (0.05–0.4 nm short, 0.1–0.8 nm long) at the
schema, so a reader never had to guess which band a column meant.

**Idempotent upsert as the write primitive.** Backfill wrote through conflict-update rather
than insert, so re-running a window was safe. This is what made resumption cheap: a
partially-completed range could simply be re-run.

**Checkpoint per source, not per job.** The checkpoint recorded the last successfully
processed date and a status, keyed by source name. Resumption asked the store where it got
to rather than inferring it from what happened to be present. Note the shape:
*per source*, which is the same separation [ADR-0003](../../adr/ADR-0003.md) later made
between a Source and an Instrument.

**Completed-date discovery separate from backfill.** A distinct query established which
dates were already present, so gap-filling was driven by observed state rather than by an
assumption that the previous run finished. Backfilling a range and discovering what is
missing from a range are different operations, and v1 kept them apart.

**A fallback path, explicitly labelled.** Monthly archive files were the primary source with
an operational endpoint as fallback. The two were distinct code paths with distinct names
rather than one path with a silent retry, so a record's origin remained knowable.

## What the frozen architecture does differently

| v1 | Frozen architecture | Why |
|---|---|---|
| Raw payload archived to a local directory | Tier 0 is **referenced by digest and retrieval descriptor, never redistributed** ([ADR-0023](../../adr/ADR-0023.md)) | The bytes belong to NOAA; identifying them satisfies provenance without republishing them |
| Ingestion and parsing in one service | One **Ingest** context with adapter and parser as separate module groups ([ADR-0026](../../adr/ADR-0026.md)) | Credentials must not escape the adapter |
| Records carry `timestamp` only | Every Observation carries `valid_time` **and** `ingest_time` ([ADR-0004](../../adr/ADR-0004.md)) | Without both, "what did we know at time T" is unanswerable |
| Checkpoint holds a date | Provenance holds digests ([ADR-0005](../../adr/ADR-0005.md)) | A date says a run happened; a digest says what it produced |

## What must not be carried forward

The v1 ingestion service assumed a live database and an async web framework. The frozen
architecture is batch and single-node ([ADR-0014](../../adr/ADR-0014.md)) at a volume that
does not justify either. The *design* of idempotent, checkpointed, gap-aware acquisition
transfers; the runtime it was built on does not.

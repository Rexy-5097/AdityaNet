---
id: STD-03
title: Bitemporality
status: active
verification: PROP
---

# STD-03 — Bitemporality

Every Observation and Label carries `valid_time` and `ingest_time`
([ADR-0004](../adr/ADR-0004.md)). `NULL` is permitted only with the meaning defined in
[ADR-0022](../adr/ADR-0022.md) — *unknown, predates bitemporal capture* — and is never
fabricated, defaulted, or inferred.

**Enforcement:** schema constraint; no-backfill property test.

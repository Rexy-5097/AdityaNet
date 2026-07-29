---
id: STD-14
title: Structured logging
status: active
verification: STAT, INTG
---

# STD-14 — Structured logging

Records carry `run_id`, `context`, `event`, `level`, `ts_utc`, plus digests and identifiers
where applicable. Prose logs are not observability.

**Forbidden in any record:** credentials, cookies, session tokens, raw archive bytes.

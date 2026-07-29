---
id: STD-19
title: Credentials confined to Ingest
status: active
verification: ARCH, STAT
---

# STD-19 — Credentials confined to Ingest

Secrets exist only within the Ingest context's source adapters. They are never logged, never
persisted to an artifact, and never cross a context boundary. No secret is committed.

**Enforcement:** secret scanning; architecture test on credential symbols.

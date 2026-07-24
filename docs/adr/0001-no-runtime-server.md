# ADR-0001 — No runtime server

**Status:** Accepted · 2026-07-23

## Context

The platform serves a frozen scientific dataset: `AdityaNet_v2_dataset_r1`,
sha256 `43fd0e22…`, 3,560,092 rows. Nothing changes at runtime. There is no user
state, no authentication, and no write path.

## Options

| Option | Assessment |
|---|---|
| FastAPI service | Conventional. Adds a runtime, container builds, a deploy target, cold starts, uptime risk, rate limiting, and an on-call surface |
| Serverless functions | Same coupling, less control, cold-start latency on every response |
| **Pre-generated static files** | Every possible response is enumerable at build time |

## Decision

Pre-generate every API response as an immutable file served from a CDN. The endpoint
*design* (URLs, envelope, schemas) is unchanged from the specification; only the
runtime is removed.

## Consequences

**Gained.** Zero operational surface. Responses become committed, hashed artifacts, so
"the API returned X" is a verifiable claim rather than a runtime event. A folder of
files still works in ten years; a Python service pinned to a 2026 dependency tree does not.

**Lost.** Arbitrary query parameters, server-side search, and cross-range aggregation.
Mitigated by fixed bin-level enums, a static search index, and — if genuinely needed —
one additive `/api/v1/query` endpoint beside the static layer, touching no existing URL.

**Not a shortcut.** The growth path is additive, which is what distinguishes an
architecture from a corner cut.

# ADR-0005 — three.js accepted at measured cost; effects stack retained

**Status:** Accepted · 2026-07-23

## Context

The experience layer requires GPU rendering with shader-level control. Before
committing, the real bundle cost was measured rather than estimated — a prior estimate
in this project was wrong by 4.6×.

## Evidence

Vite production build, gzipped, 2026-07-23:

| Configuration | Size |
|---|---|
| three + R3F + drei + postprocessing + React | **314.17 KB gz** |
| three + R3F + React (no drei, no postprocessing) | **292.57 KB gz** |
| **Cost of the entire effects stack** | **21.6 KB** |

My pre-registered estimate was 220–280 KB. It was wrong, on the low side.

## Decision

Accept three.js. **Retain `drei` and `postprocessing`.** Raise the `/explore` budget to
**450 KB gz**, lazy-loaded after LCP behind a static poster.

## Consequences

**The pre-committed fallback is void.** The specification said "drop `postprocessing`
if over budget." Measurement shows that recovers 7% while sacrificing bloom, tone
mapping, and the entire effects pipeline. Recording this because a fallback that
survives to the point of being needed and then proves useless is a planning failure
worth remembering.

**three.js core (~245 KB gz) is the real floor** and is irreducible without abandoning
the shader control the design requires. There is no smaller mature alternative.

**Affordable because of ADR-0002.** Evidence routes cost ~0 KB. A 450 KB island on one
opt-in route, loaded after a text-and-poster LCP, is a defensible trade only in an
architecture where the other surfaces are free.

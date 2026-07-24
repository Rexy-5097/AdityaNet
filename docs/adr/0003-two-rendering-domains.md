# ADR-0003 — Two rendering domains, enforced at build time

**Status:** Accepted · 2026-07-23

## Context

The platform must be simultaneously an immersive experience and a scientifically
honest research instrument. SoLEXS and HEL1OS are **non-imaging** instruments: they
measure counts per channel per minute, disk-integrated. The archive contains no
spatial information about the Sun.

A photorealistic Sun is therefore legitimate *atmosphere* and illegitimate *evidence*.
The honesty variable is framing, not pixel fidelity — a planetarium show is
photorealistic and nobody mistakes it for photometry.

## Decision

Two disjoint rendering domains, with membership enforced mechanically.

**Domain A — Experience.** Photorealistic rendering permitted. Never presented as
observational evidence.

**Domain B — Scientific.** Every visual encoding traceable to a committed artifact.

### Enforcement

1. Every `<canvas>` must be wrapped in `<ExperienceFrame>` or
   `<EvidenceFrame source={ArtifactRef}>`. An unwrapped canvas fails CI.
2. Domain A renders `ARTISTIC RENDERING · NOT OBSERVATIONAL DATA` **into the WebGL
   frame buffer**, not the DOM, so the marker survives screenshot and canvas export.
3. `src/experience/` and `src/scientific/` cannot import each other
   (`eslint-plugin-boundaries`, enforced from Sprint 0 before either exists).
4. Domain B shader uniforms are prefixed `uData*` and must resolve to an `ArtifactRef`;
   Domain A uses `uArt*`.
5. No bitmap solar textures. A texture derived from another mission's imagery would
   import that mission's observations into our frame.

## Consequences

The domain boundary becomes the product's most interesting interaction: approaching the
star dissolves Domain A into Domain B, and the watermark transitions as the user
crosses. The honesty mechanism and the emotional climax are the same event.

Sealing `src/experience/` also means a total failure of the GPU layer cannot affect a
single credibility surface — they cannot even name it.

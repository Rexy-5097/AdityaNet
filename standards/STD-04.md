---
id: STD-04
title: Missing is never imputed
status: active
verification: PROP, STAT
---

# STD-04 — Missing is never imputed

No fill, interpolation, zero-substitution, forward-fill or default on any path
([ADR-0017](../adr/ADR-0017.md)). Zero is a valid measurement.

**Enforcement:** static ban on fill and interpolate calls within canonicalisation;
no-imputation property test over generated inputs.

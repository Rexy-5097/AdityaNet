---
id: STD-01
title: Dependency direction
status: active
verification: ARCH
---

# STD-01 — Dependency direction

Imports follow the context map of [ADR-0026](../adr/ADR-0026.md). The provenance kernel
imports nothing. `domain/` imports the standard library only. Evaluation imports contracts
and domain only. Evidence performs no writes. No context imports another context's internals.

**Enforcement:** architecture test in CI. Each rule has a deliberate-violation case.

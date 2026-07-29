---
id: STD-13
title: Errors fail loud
status: active
verification: STAT, UNIT
---

# STD-13 — Errors fail loud

No bare `except`, no silent fallback, no default-on-error, no coercion of malformed input.
Failures use the five-class taxonomy: `ContractViolation`, `IntegrityFailure`,
`ProvenanceFailure`, `UnavailableResource`, `PolicyRejection`.

**Enforcement:** lint rule banning bare except and broad exception suppression.

# `domain/invariants`

**Invariants as callable predicates.**

## Responsibility

Every rule the architecture states as an invariant appears here as a predicate that a
property test can quantify over. A rule stated only in prose is not an invariant.

## What may not enter

- Prose-only rules.
- Predicates requiring I/O to evaluate.

## Governing decisions

[ADR-0026](../../adr/ADR-0026.md)

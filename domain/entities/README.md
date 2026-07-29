# `domain/entities`

**Entities with identity.**

## Responsibility

Objects whose identity persists across changes of attribute. Immutable entities are
identified by content digest; only names are mutable.

## What may not enter

- Mutable identity on anything an Evaluation references.
- Sequential or timestamp identifiers for immutable objects.

## Governing decisions

[ADR-0005](../../adr/ADR-0005.md)

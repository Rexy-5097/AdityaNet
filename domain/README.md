# `domain`

**The pure domain model.**

## Responsibility

Entities, value objects and invariants expressed as callable predicates. Imports the
standard library and nothing else, so that every invariant is testable with no fixtures,
no mocks and no infrastructure.

## What may not enter

- Any third-party import.
- Any I/O — filesystem, network, clock, environment.
- Persistence, serialisation transport, or framework code.

## Governing decisions

[ADR-0002](../adr/ADR-0002.md) · [ADR-0026](../adr/ADR-0026.md) · [STD-01](../standards/STD-01.md)

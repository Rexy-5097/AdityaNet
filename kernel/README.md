# `kernel`

**Shared kernel.**

## Responsibility

Vocabulary shared by every bounded context, with no domain behaviour of its own.
Currently one member: provenance.

## What may not enter

- Any bounded-context logic.
- Anything that is not shared by every context.

## Governing decisions

[ADR-0026](../adr/ADR-0026.md)

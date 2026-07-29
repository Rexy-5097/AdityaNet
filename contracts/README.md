# `contracts`

**The only cross-context vocabulary.**

## Responsibility

Normative JSON Schema for every object that crosses a context boundary. Schemas are the
source of truth; language types are hand-written and validated against them. Within a
major version, changes are additive only.

## What may not enter

- Language-specific types or generated code.
- Any schema not crossing a context boundary — that is a context's internal concern.
- Breaking changes within a major version.

## Governing decisions

[ADR-0019](../adr/ADR-0019.md) · [STD-09](../standards/STD-09.md)

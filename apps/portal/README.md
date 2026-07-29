# `apps/portal`

**The static evidence surface.**

## Responsibility

Renders published claims bound to artifacts. Static files only, for maximum durability
and minimum operational cost.

## What may not enter

- JavaScript on an evidence route.
- A numeric literal in a template.
- Any runtime dependency on an external origin.
- Content that implies currency without displaying data age.

## Governing decisions

[ADR-0015](../../adr/ADR-0015.md) · [ADR-0012](../../adr/ADR-0012.md) · [STD-17](../../standards/STD-17.md)

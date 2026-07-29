# `contexts/evidence`

**Bind published values to bytes, and render.**

## Responsibility

Evidence bindings, the consistency gate, supersession, and static rendering. Reads from
every context and writes to none.

## What may not enter

- Writes to any other context. Evidence observes; it never mutates.
- A rendered numeric literal. Components accept measurement keys, never values.
- JavaScript on an evidence route.
- A surface implying currency without displaying data age.

## Governing decisions

[ADR-0012](../../adr/ADR-0012.md) · [ADR-0015](../../adr/ADR-0015.md) · [ADR-0024](../../adr/ADR-0024.md)

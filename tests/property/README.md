# `tests/property`

**Universally-quantified assertions.**

## Responsibility

Properties that must hold over generated inputs: determinism, no imputation, no leakage,
no score without an interval.

## What may not enter

- Tests of specific known defects. Those are regression tests and live with their context.

## Governing decisions

[ADR-0017](../../adr/ADR-0017.md) · [ADR-0021](../../adr/ADR-0021.md)

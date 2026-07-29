# `contexts/evaluation`

**Score methods under a frozen protocol.**

## Responsibility

The evaluation engine, protocol and environment registries, the leakage and instrument
gates, and scoring with uncertainty. An Evaluation is a function of five pinned inputs.

## What may not enter

- Imports of contexts/method internals. The engine executes a released artifact.
- Any unpinned input, including the execution environment.
- Persisting or publishing an UNREPRODUCIBLE evaluation.
- A Score without an Interval, an estimator name and a denominator.

## Governing decisions

[ADR-0021](../../adr/ADR-0021.md) · [ADR-0022](../../adr/ADR-0022.md) · [ADR-0011](../../adr/ADR-0011.md)

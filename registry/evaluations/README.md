# `registry/evaluations`

**Evaluation results.**

## Responsibility

Evaluation results: five input digests, scores with intervals, reproduction class,
leakage-gate status.

## What may not enter

- Mutation of an existing entry.
- An entry without a resolvable digest.

## Governing decisions

[ADR-0021](../../adr/ADR-0021.md)

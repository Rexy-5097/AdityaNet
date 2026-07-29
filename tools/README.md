# `tools`

**Gates and developer tooling.**

## Responsibility

Programs that enforce or assist. Every enforcement rule in standards/ is implemented
here as a program that exits non-zero on violation.

## What may not enter

- Anything imported by a context. Tools depend on the tree; the tree never depends on tools.

## Governing decisions

[ADR-0020](../adr/ADR-0020.md)

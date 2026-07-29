# `tools/gates`

**Enforcement programs.**

## Responsibility

One program per gate. Each exits non-zero on violation, reports what it checked rather
than only what failed, and fails closed when it cannot execute.

## What may not enter

- A gate that passes when it cannot run.
- A gate without a deliberate-violation test proving it fails when it should.
- A suppression list that is not self-expiring.

## Governing decisions

[ADR-0020](../../adr/ADR-0020.md) · [STD-07](../../standards/STD-07.md)

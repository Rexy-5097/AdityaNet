# `registry/environments`

**EnvironmentRelease records.**

## Responsibility

EnvironmentRelease records: interpreter, lockfile digest, BLAS, thread counts, hash
seed; platform recorded, not pinned.

## What may not enter

- Mutation of an existing entry.
- An entry without a resolvable digest.

## Governing decisions

[ADR-0021](../../adr/ADR-0021.md)

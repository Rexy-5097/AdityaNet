# `registry/methods`

**MethodRelease manifests.**

## Responsibility

MethodRelease manifests: artifact digest, parameters, training provenance, declared
instruments.

## What may not enter

- Mutation of an existing entry.
- An entry without a resolvable digest.

## Governing decisions

[ADR-0010](../../adr/ADR-0010.md)

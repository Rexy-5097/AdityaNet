# `registry`

**Tier 2 storage. Git is the system of record.**

## Responsibility

Manifests and small derived payloads for every registered object. A manifest carries a
digest and, for Tier 1 objects, the DOI and URL where the bytes live. The bytes
themselves are not here.

## What may not enter

- Tier 0 raw source archives. Those are referenced by descriptor, never redistributed.
- Tier 1 dataset bytes. Those are deposited externally and referenced by DOI.
- Any mutable record. Every entry is immutable and content-addressed.

## Governing decisions

[ADR-0023](../adr/ADR-0023.md) · [ADR-0005](../adr/ADR-0005.md)

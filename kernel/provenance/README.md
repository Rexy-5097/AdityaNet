# `kernel/provenance`

**The single minting authority for digests.**

## Responsibility

Artifact, Digest, Run, ProvenanceRecord and DAG traversal. This is the only code
permitted to mint a digest, so that content addressing has exactly one implementation
and one place to audit.

## What may not enter

- Every import. This package imports nothing — not a sibling, not a third party.
- Any solar, instrument or evaluation vocabulary.
- Mutation of a recorded provenance entry.

## Governing decisions

[ADR-0005](../../adr/ADR-0005.md) · [ADR-0026](../../adr/ADR-0026.md)

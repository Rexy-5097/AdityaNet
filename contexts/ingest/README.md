# `contexts/ingest`

**Acquire and canonicalise.**

## Responsibility

Source adapters retrieve raw artifacts; instrument parsers canonicalise them into
bitemporal Observations. Acquisition and canonicalisation are one context with two
internal module groups; they split into separate contexts only when a second source
exists.

## What may not enter

- Credentials, cookies or session state leaving this context, in any form, including logs.
- Redistribution of Tier 0 source bytes.
- Imputation of a missing value on any path.
- Knowledge of evaluation, scoring or publication.

## Governing decisions

[ADR-0003](../../adr/ADR-0003.md) · [ADR-0004](../../adr/ADR-0004.md) · [ADR-0017](../../adr/ADR-0017.md) · [STD-19](../../standards/STD-19.md)

# `contexts/groundtruth`

**Version an exogenous, revisable authority.**

## Responsibility

LabelSource, LabelRelease and Event extraction. Deliberately separate from curation
because labels come from a different authority, on a different revision cadence, and
conflating them makes historical scores silently unreproducible.

## What may not enter

- Merging into contexts/curation.
- Mutating a released label snapshot. A revision produces a new release.
- Resolving a label release by 'latest' rather than by digest.

## Governing decisions

[ADR-0007](../../adr/ADR-0007.md)

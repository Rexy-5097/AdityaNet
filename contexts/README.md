# `contexts`

**The six bounded contexts.**

## Responsibility

Each context defends an invariant that would be lost if it were merged with another.
Contexts communicate through contracts/ alone and never import one another's internals.

## What may not enter

- A seventh context without a superseding ADR.
- A common/, shared/, utils/, core/ or misc/ package. Shared vocabulary lives in contracts/.
- Cross-context imports of internal modules.

## Governing decisions

[ADR-0026](../adr/ADR-0026.md) · [ADR-0019](../adr/ADR-0019.md)

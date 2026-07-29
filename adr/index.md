# Architecture Decision Records

Architecture Freeze v1.0. Accepted ADRs are immutable: supersede, never edit
(TIS E1 §9).

**25 active · 2 superseded · 27 total**

## Active

| ID | Title |
| --- | --- |
| [ADR-0001](ADR-0001.md) | Product vision and platform strategy |
| [ADR-0002](ADR-0002.md) | Domain model and ubiquitous language |
| [ADR-0003](ADR-0003.md) | Source is distinct from Instrument |
| [ADR-0004](ADR-0004.md) | All observations are bitemporal |
| [ADR-0005](ADR-0005.md) | Content addressing for every immutable object |
| [ADR-0006](ADR-0006.md) | Dataset releases are immutable |
| [ADR-0007](ADR-0007.md) | Ground truth is a separate versioned context |
| [ADR-0008](ADR-0008.md) | Protocols are immutable pre-registered artifacts |
| [ADR-0010](ADR-0010.md) | Method releases are immutable and retrievable |
| [ADR-0011](ADR-0011.md) | Methods declare instrument requirements; protocols permit; mismatch is rejected |
| [ADR-0012](ADR-0012.md) | Evidence binding and consistency gate |
| [ADR-0013](ADR-0013.md) | Limitations are versioned first-class clauses cited by ID |
| [ADR-0014](ADR-0014.md) | Batch, single-node. No microservices, no orchestration, no broker |
| [ADR-0015](ADR-0015.md) | Static publication; live surfaces strictly isolated |
| [ADR-0016](ADR-0016.md) | Third-party method execution is sandboxed and out-of-process |
| [ADR-0017](ADR-0017.md) | Missing data is never imputed |
| [ADR-0019](ADR-0019.md) | Monorepo with contracts as the sole shared vocabulary |
| [ADR-0020](ADR-0020.md) | Gates fail closed |
| [ADR-0021](ADR-0021.md) | Environment is a pinned evaluation input |
| [ADR-0022](ADR-0022.md) | Unknown ingest time is NULL; the leakage gate declares its own scope |
| [ADR-0023](ADR-0023.md) | Three storage tiers; raw data is referenced, not held |
| [ADR-0024](ADR-0024.md) | Bytes are immutable; standing is not |
| [ADR-0025](ADR-0025.md) | Free seams and paid abstractions |
| [ADR-0026](ADR-0026.md) | Six bounded contexts and one shared kernel |
| [ADR-0027](ADR-0027.md) | Bitemporal migration procedure |

## Superseded

Retained unedited with their original decisions, so that a reader arriving from a
citation sees what was decided and why it no longer holds.

| ID | Title | Superseded by |
| --- | --- | --- |
| [ADR-0009](superseded/ADR-0009.md) | Evaluation is a pure function of four pinned inputs | [ADR-0021](ADR-0021.md) |
| [ADR-0018](superseded/ADR-0018.md) | Abstraction requires two instances | [ADR-0025](ADR-0025.md) |

## Related

- [Engineering standards](../standards/index.md)
- [Technical Implementation Specification v1.0](../docs/tis/TIS-v1.0.md)
- [Verification & Validation Master Plan v1.0](../docs/tis/VVMP-v1.0.md)

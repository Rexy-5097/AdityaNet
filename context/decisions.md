# Architecture Decision Records — SuryaNet / AdityaNet

> **Index:** All ADRs in chronological order
> **Cross-refs:** `context/architecture.md` · `artifacts/decisions/`
> **Format:** ADR-XXXX-kebab-title.md in `artifacts/decisions/`

---

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-0001](../artifacts/decisions/ADR-0001-v4-feature-framework.md) | Version 4 feature framework: stateless features, framework-enforced isolation | Accepted | 2026-07-05 |
| [ADR-0002](../artifacts/decisions/ADR-0002-ci-foundation.md) | CI foundation: local gate runner + hosted mirror; frozen artifacts lint-exempt | Accepted | 2026-07-05 |

---

## Pre-AgentOS Decisions (Undocumented, Need Formalization)

The following architectural decisions predate AgentOS and should be written as ADRs:

| # | Decision | Context | Priority to Document |
|---|----------|---------|---------------------|
| 1 | Late fusion (per-instrument encoders, merge at embedding level) | Allows graceful degradation | High |
| 2 | Learnable missing tokens for absent instruments | Explicit "I don't have this data" representation | High |
| 3 | MC Dropout (50 passes) for uncertainty quantification | Simple, cheap, operational | Medium |
| 4 | Isotonic regression as primary calibration (not temperature scaling) | Temperature scaling breaks decision boundary at T=1.4168 on V3 | High |
| 5 | Chronological train/val/test split (no shuffling) | Temporal integrity, operational realism | High |
| 6 | 6-hour forecast horizon | Operationally actionable lead time for satellite safing | Medium |
| 7 | 14 GOES feature set | Information gap audit confirms history features dominate (removing any collapses TSS) | Medium |
| 8 | PatchTST over LSTM/CNN | Patch-based local+global temporal context, parameter efficiency | Medium |
| 9 | V1 (GOES-only) in production, V3 (multi-instrument) in research | V3 not validated on joint flare events; V1 has full 16-year training base | High |
| 10 | Stage 1 pretraining on GOES (SC24), Stage 2 fine-tune on Aditya-L1 overlap | Transfer learning to bridge SC24→SC25 and GOES→multi-instrument | High |

---

## How to Create an ADR

```bash
# Create the ADR file:
cp templates/adr.md artifacts/decisions/ADR-0001-late-fusion-architecture.md
# Edit it, then:
# 1. Add it to this index above
# 2. Bump adr_counter in .agentos/manifest.yml
```

---

*Last updated: 2026-07-03 · AgentOS onboarding*

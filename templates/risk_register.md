---
id: ART-RISK-NNNN
title: "[Project Name] Risk Register"
version: 1.0
status: active
owner: planner
created: YYYY-MM-DD
modified: YYYY-MM-DD
related_adr: None
related_standard: standards/security.md
related_checklist: None
related_workflow: master.md
related_agent: planner
---

# Risk Register: [ID]

## Active Risks Matrix

| Risk ID | Risk Description | Impact (1-5) | Likelihood (1-5) | Severity Score | Mitigation Strategy | Owner | Trigger Condition |
|---------|------------------|:------------:|:----------------:|:--------------:|---------------------|-------|-------------------|
| **RSK-001**| [e.g., VRAM memory leak] | 4 | 2 | 8 | Run performance profile | ML Lead | GPU VRAM > 90% |

> Severity Score = Impact $\times$ Likelihood. Red flag if Score $\ge$ 12.

## Mitigation Details

### RSK-[NNN]: [Risk Title]
- **Mitigation plan:** Action steps to prevent risk.
- **Contingency plan:** Actions if the trigger condition is met.

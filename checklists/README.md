# Quality Gate System — checklists/

> **Layer:** Infrastructure | **Status:** Active — Completed in Phase 6
> **Purpose:** Formal verification checkpoints in the development lifecycle.
> **Required Reading:** Read by Orchestrator and Human Leads before advancing milestones.
> **Cross-refs:** `workflows/master.md` · `standards/README.md` · `metrics/README.md`

---

## Lifecycle Pipeline Flow

AgentOS uses a linear, non-circular checkpoint sequence. Features and milestones must clear these gates in order, concluding with post-release Monitoring:

```
 Planning (SOP)
       │
       ▼
 Implementation (Code)
       │
       ▼
 [QG-001] Feature Completion Gate  ──(Feature ready)
       │
       ▼
 [QG-002] Pull Request Gate        ──(PR submission)
       │
       ▼
 [QG-003] QA Verification Gate     ──(Milestone build validation)
       │
       ▼
 [QG-005] Security Review Gate     ──(Security policy compliance)
       │
       ▼
 [QG-008] Release Gate             ──(Compatibility & notes audit)
       │
       ▼
 [QG-006] Deployment Gate          ──(Production staging checks)
       │
       ▼
 [Monitoring]                      ──(Production health and runtime metrics tracking)
```

> **Note:** `QG-007` (Bug Fix) operates as a parallel gate triggered during bug remediation. `QG-004` (Research Validation) is triggered for scientific or AI experiments before code integration.

---

## Traceability Matrix

This table maps each Quality Gate to its applicable Standards, evaluated Metrics, participating Reviewer Agents, and validating ADRs:

| Gate ID | Checklist | Standards Evaluated | Metrics Checked | Reviewer Agent | ADR |
|---------|-----------|---------------------|-----------------|----------------|-----|
| **QG-001**| [Feature Completion](./feature_completion.md) | `code_quality`, `documentation` | `quality.md` | `qa-reviewer` | ADR-0023 |
| **QG-002**| [Pull Request](./pull_request.md) | `code_quality`, `testing` | `quality.md` | Code Reviewer | ADR-0024 |
| **QG-003**| [QA Verification](./qa.md) | `testing`, `code_quality` | `quality.md` | `qa-reviewer` | ADR-0025 |
| **QG-004**| [Research Validation](./research_validation.md)| `research`, `ai_ml` | `benchmarks.md` | `science-reviewer` · `ai-reviewer` | ADR-0026 |
| **QG-005**| [Security Review](./security_review.md) | `security`, `api_design` | `quality.md` | `security-reviewer` | ADR-0023 |
| **QG-006**| [Deployment](./deployment.md) | `security`, `code_quality` | `performance.md`| `performance-reviewer` · Tech Lead | ADR-0027 |
| **QG-007**| [Bug Fix](./bug_fix.md) | `code_quality`, `testing` | `quality.md` | `qa-reviewer` | ADR-0025 |
| **QG-008**| [Release](./release.md) | `documentation` | `quality.md` | `release-reviewer` | ADR-0027 |

---

## Gate Quality Scores

Every gate evaluation produces a quality score block used for monitoring and dashboard metrics:

```text
Engineering Score      : [0 - 100]
Research Score         : [0 - 100] (N/A if non-research)
Security Score         : [0 - 100]
Documentation Score    : [0 - 100]
Release Score          : [0 - 100]
----------------------------------
Overall Quality Score  : [Average of applicable scores]
```

---

## Extension Rules

To register a new Quality Gate:
1. Assign it a unique `QG-NNN` identifier.
2. Build the checklist file defining its metadata, version, runtime, severity, automation level, and retry policy.
3. Update this Traceability Matrix and the lifecycle pipeline diagram.
4. Register the new checklist file in `.agentos/manifest.yml`.

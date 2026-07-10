# Artifact Schema Specification — templates/SCHEMA.md

> **Layer:** Infrastructure | **Status:** Active
> **Purpose:** Master schema specification and metadata rules for all AgentOS artifacts.
> **Required Reading:** Read by validator tools and agents generating reports.
> **Cross-refs:** `standards/documentation.md` · `artifacts/decisions/` · `tools/scripts/validate_agentos.py`

---

## Global Metadata Schema

Every engineering artifact produced by AgentOS must begin with a standardized Frontmatter metadata block. This makes every document machine-readable and traceable.

```markdown
---
id: [ART-XXX-NNNN]
title: [Document Title]
version: [1.0]
status: [draft | active | approved | superseded | completed]
owner: [agent-name | human-role]
created: [YYYY-MM-DD]
modified: [YYYY-MM-DD]
related_adr: [ADR-NNNN | None]
related_standard: [standard-name | None]
related_checklist: [QG-NNN | None]
related_workflow: [workflow-name | None]
related_agent: [agent-name | None]
---
```

---

## Artifact Type Registry

| Type prefix | Artifact Type | Schema Blueprint | Target Location | Archival Policy |
|-------------|---------------|------------------|-----------------|-----------------|
| **ART-ADR** | Architecture Decision Record | `decision_record.md` | `artifacts/decisions/` | Permanent (never delete) |
| **ART-EXP** | Experiment Log | `experiment_log.md` | `artifacts/experiments/` | Retain (compress at milestone) |
| **ART-BUG** | Bug Report | `bug_report.md` | `artifacts/bugs/` | Retire when bug status = RESOLVED |
| **ART-FEAT**| Feature Proposal | `feature_proposal.md`| `artifacts/features/` | Archive on release |
| **ART-ARCH**| Architecture Review | `architecture_review.md`| `artifacts/reviews/` | Permanent historical record |
| **ART-REL** | Release Notes | `release_notes.md` | `artifacts/releases/` | Permanent (never delete) |
| **ART-MEET**| Meeting Notes | `meeting_notes.md` | `artifacts/meetings/` | Archive after 6 months |
| **ART-PLAN**| Sprint Plan | `sprint_plan.md` | `artifacts/sprints/` | Archive after sprint close |
| **ART-RISK**| Risk Register | `risk_register.md` | `artifacts/risks/` | Active live document |
| **ART-INC** | Incident Report | `incident_report.md` | `artifacts/incidents/` | Permanent historical record |

---

## Validation Rules

Validator agents and scripts (`validate_agentos.py`) check every completed artifact against these rules:
1. **Frontmatter Presence:** Must parse as valid YAML frontmatter.
2. **Mandatory Keys:** Must contain all 12 keys defined in the Global Schema.
3. **Traceability check:** Referenced ADRs, Standards, and Checklists must exist within the repository.
4. **Idempotency check:** `id` must be unique across the entire directory structure.
5. **No empty sections:** Sections matching `[FILL: description]` must be replaced with actual text.

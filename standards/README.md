# Engineering Standards — Architecture

> **Layer:** Infrastructure | **Version:** 0.1.0 | **Status:** Complete
> **Primary Consumer:** Reviewer agents · All engineers
> **Cross-refs:** `agents/README.md` (trigger map) · `checklists/` (verification) · `metrics/` (targets)

---

## Standards Hierarchy

Standards are organized in four tiers. Lower tiers **reference** upper tiers — they never duplicate them.

```
TIER 1 — FOUNDATION (apply to all projects, all components)
  ├── code_quality.md      ← base of all engineering work
  ├── testing.md           ← references code_quality
  └── documentation.md     ← references code_quality

TIER 2 — CROSS-CUTTING (apply across all tiers below)
  └── security.md          ← referenced by api_design, data_engineering, ai_ml

TIER 3 — DOMAIN (apply to specific project types)
  ├── ai_ml.md             ← references testing, research, data_engineering
  └── research.md          ← references documentation, testing

TIER 4 — COMPONENT (apply to specific system components)
  ├── api_design.md        ← references code_quality, security, documentation
  ├── data_engineering.md  ← references security, testing, code_quality
  └── ui_ux.md             ← references documentation, testing
```

**Inheritance Rule:** When a Tier 4 standard covers code quality, it says "Follow `standards/code_quality.md`" — it does NOT restate the code quality rules.

---

## Quality Level Model

Every standard defines four quality levels. Projects self-select their target level.

| Level | Description | Typical Use Case |
|-------|------------|-----------------|
| **Minimum Acceptable** | System functions; no critical failures | Experiments, student projects |
| **Recommended** | Good engineering practices applied | Hackathons, internal tools, research |
| **Production Grade** | Full professional engineering standards | SaaS, APIs, deployed systems |
| **Flagship Grade** | Highest engineering rigor | Safety-critical, ISRO-class, publications |

---

## Standards Library

| Standard | Tier | Domain | Reviewer Agent |
|---------|------|--------|---------------|
| `code_quality.md` | Foundation | All | Any reviewer |
| `testing.md` | Foundation | All | `qa-reviewer` |
| `documentation.md` | Foundation | All | `docs-reviewer` |
| `security.md` | Cross-cutting | All | `security-reviewer` |
| `ai_ml.md` | Domain | AI/ML | `ai-reviewer` |
| `research.md` | Domain | Scientific | `science-reviewer` |
| `api_design.md` | Component | APIs | `security-reviewer` + `docs-reviewer` |
| `data_engineering.md` | Component | Data | `ai-reviewer` or `science-reviewer` |
| `ui_ux.md` | Component | Frontend | `ui-reviewer` |

---

## Standard Structure

Every standard file contains, in order:
1. Header (owner, consumers, budget, cross-refs)
2. Purpose + Scope
3. Guiding Principles
4. Quality Level table
5. Best Practices
6. Anti-patterns
7. Common Failure Modes
8. Acceptance Criteria (by quality level)
9. Reviewer Questions
10. Completion Criteria
11. Cross-references

---

## Adding a New Standard

1. Identify its tier in the hierarchy.
2. Create `standards/{name}.md`.
3. Add a row to the table above.
4. Register in `.agentos/manifest.yml`.
5. Update `.agentos/config.yml` trigger map if a new reviewer is needed.
6. Create an ADR if the new standard introduces a new architectural concern.
7. Bump the MINOR version in `VERSION`.

---

*Engineering Standards — The constitution that governs all AgentOS projects.*

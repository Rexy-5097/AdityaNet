# Standard: Documentation

> **Tier:** Foundation — applies to all projects and components
> **Owner:** Tech Lead / Docs Lead | **Reviewer:** `docs-reviewer`
> **Consumers:** All agents (docs review tasks) | **Max:** ~1300 tokens
> **Cross-refs:** `standards/code_quality.md` · `standards/api_design.md` · `metrics/quality.md`

---

## Purpose

Ensure that documentation is accurate, current, actionable, and written for both human engineers and AI agents — with minimal maintenance overhead.

## Scope

**Governs:** READMEs, API documentation, architecture records, runbooks, inline code comments, docstrings.
**Does NOT govern:** ADR content (→ `artifacts/decisions/`), experiment logs (→ `artifacts/experiments/`), context files (→ `context/`), engineering standards (→ `standards/`).

---

## Guiding Principles

1. **Documentation changes with code.** A PR that changes behavior without updating docs is incomplete.
2. **Write for the next engineer.** Assume they are intelligent but have zero context.
3. **Examples over descriptions.** Show a working example before explaining it.
4. **Current and compact over comprehensive and stale.** Short, accurate documentation beats long, outdated documentation.
5. **Docs are tests.** Runbooks that fail silently are bugs. Examples that don't run are lies.
6. **Never document what.** Document WHY — the code already shows what.
7. **AI-readable structure.** Use consistent headings, tables, and code blocks that agents can parse reliably.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| README | Exists + setup works | + Architecture overview | + All sections complete | + Architecture diagram + visual |
| API docs | None | Public methods documented | Full OpenAPI/docstring spec | Full spec + example collection |
| Inline comments | None | WHY comments on non-obvious | WHY comments throughout | WHY + decision rationale |
| Runbooks | None | Setup + common ops | All operational procedures | All + tested on every release |
| Architecture docs | None | Overview exists | `context/architecture.md` complete | + Component decision rationale |
| ADRs | None | Key decisions | All significant decisions | All + formal review process |
| Changelog | None | Major changes | Semantic versioning + all changes | Full changelog + migration guides |
| Doc coverage | N/A | All public APIs | 100% public API + modules | 100% + examples per function |

---

## Documentation Taxonomy

| Type | Audience | Update Trigger | Lives In |
|------|---------|---------------|---------|
| README | New engineers + agents | Feature changes, setup changes | Repository root |
| API docs | Consumers of the API | Any public interface change | Code / OpenAPI spec |
| Architecture | Architects + senior engineers | Structural design changes | `context/architecture.md` |
| Runbook | Operations engineers | Process changes, system changes | `docs/` or `context/` |
| ADR | Decision-makers, historians | Per architectural decision | `artifacts/decisions/` |
| Inline comment | Code reader | When intent is non-obvious | Source code |
| Experiment log | Researchers, AI reviewers | Per experiment run | `artifacts/experiments/` |

---

## Best Practices

- **README as the north star.** The README is the first thing engineers and agents read. Maintain it.
- **Anchor every example to the current API.** If an example can't run, it's misinformation.
- **Use consistent headers.** Agents extract information from structure; consistent headings make that reliable.
- **Link, don't duplicate.** If information exists elsewhere, link to it. Duplication creates drift.
- **Mark WIP sections.** Prefer `> ⚠️ Draft — not yet validated` over silently incomplete content.
- **Self-review documentation.** Follow a new README from scratch on every major release to catch failures.
- **Archive stale docs.** Outdated documentation is more dangerous than no documentation. Archive or delete.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| "TODO: document this later" | Later never comes; shipped as-is |
| Duplicating documentation across files | Drift; one version is always wrong |
| Over-commenting obvious code | Noise that makes reading harder; comment WHY not what |
| Narrative-only API docs (no examples) | Engineers can't use APIs they can't see demonstrated |
| Changelog omission | Agents and engineers cannot track what changed |
| Documentation that ships after the feature | Docs without context are always worse |
| Dead links | Infrastructure moves; docs don't; agents encounter broken references |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Stale README | Updated at launch, ignored after | Scheduled review in `checklists/release.md` | Review and update before every release |
| Missing API docs | Added "after" the implementation | Docs reviewer gate | Make docs a PR merge requirement |
| Broken examples | API changes without updating examples | CI doc test (doctest or smoke test) | Test examples as part of CI |
| ADR backlog | Decisions made but not recorded | `context/state.md` recent decisions table grows stale | Log decisions within 24h of making them |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | README exists · Setup instructions produce a running system · No broken links |
| Recommended | + All public APIs documented · Architecture overview exists · Changelog maintained |
| Production | + Full API spec · All operational runbooks exist and tested · All significant decisions have ADRs |
| Flagship | + 100% doc coverage · Examples tested in CI · Formal doc review on every release |

---

## Reviewer Questions

```
DOCUMENTATION REVIEW CHECKLIST
□ Does the README accurately reflect the current state of the system?
□ Are all public APIs documented with at least one working example?
□ Do all code examples actually run against the current codebase?
□ Is there a changelog entry for this change?
□ Are all relevant ADRs created and indexed in context/decisions.md?
□ Are there any dead links in the documentation?
□ Is documentation co-located with the code it describes?
□ Are there any "TODO: document" markers left in the codebase?
□ Does documentation explain WHY, not just WHAT?
□ Is the architecture document current with the latest changes?
```

---

## Completion Criteria

- [ ] Documentation meets the acceptance criteria for the project's quality level
- [ ] No broken links (verified by link checker or manual scan)
- [ ] All public API methods have documentation
- [ ] All examples run against the current codebase
- [ ] Changelog updated if applicable
- [ ] docs-reviewer has reviewed and approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Code commenting style | `standards/code_quality.md` |
| API documentation | `standards/api_design.md` |
| ADR format | `templates/decision_record.md` |
| Documentation metrics | `metrics/quality.md` |

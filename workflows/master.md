# Master Workflow — AgentOS Orchestration Reference

> **Layer:** Infrastructure | **Version:** 0.1.0 | **Status:** Complete
> **Primary Consumer:** `orchestrator` agent
> **Required Reading:** Before invoking any agent or beginning any task
> **Cross-refs:** `agents/README.md` · `.agentos/config.yml` · `checklists/` · `context/state.md`

---

## Project Lifecycle

```
 INCEPTION          PLANNING          DEVELOPMENT         MILESTONE          RELEASE
     │                  │                  │                  │                 │
  Setup             Scope &           Implement →          QA Gate         Release Gate
  context/          Milestones        Review loop          Checklist        Deploy
     │                  │                  │                  │                 │
     └──────────────────┴──────────────────┴──────────────────┴─────────────────┘
                                    CONTINUOUS IMPROVEMENT
                    (lessons/ · artifacts/ · context/state.md updates)
```

---

## Phase 0 — Inception

**Trigger:** New project begins.

**Steps:**
1. Copy AgentOS template into project repository.
2. Populate `context/vision.md` — define problem, objectives, success criteria.
3. Populate `context/architecture.md` — initial system design.
4. Populate `context/tech_stack.md` — technology choices.
5. Populate `context/state.md` — set Phase, Sprint 1, first tasks.
6. Invoke **`planner`** → produce milestone map.
7. Record first architectural decisions as ADRs in `artifacts/decisions/`.
8. Update `context/decisions.md` index.

**Exit Criteria:** All `context/` files populated. Milestone map exists. First ADRs recorded.

---

## Phase 1 — Planning

**Trigger:** New feature, new sprint, or scope change.

**Invoke:** `planner`

**Steps:**
1. Read `context/vision.md` and `context/state.md`.
2. Define scope — what is IN, what is OUT.
3. Break work into tasks (no task > 1 day of effort).
4. Identify risks and blockers.
5. Update `context/state.md` with active tasks and next milestone.
6. If task requires architecture decisions → invoke `chief-architect`.

**Exit Criteria:** Tasks defined. Scope agreed. `context/state.md` updated. No undefined architectural dependencies.

---

## Phase 2 — Implementation

**Trigger:** Planning complete. Tasks ready.

> ⚠️ **There is NO implementation agent.** The main coding session implements.
> Agents plan, review, and validate. The human engineer approves.

**Steps:**
1. Read required context files (see §Required Context Loading).
2. Implement the task.
3. After each implementation unit → determine which reviewer(s) are needed (see §Agent Trigger Map).
4. Invoke **`orchestrator`** → it routes to the correct reviewer(s).
5. Address review findings.
6. Apply the pull request checklist (`checklists/pull_request.md`).
7. Update `context/state.md`.

**Implementation Session Protocol:**
- Read: `context/vision.md`, `context/state.md`, `context/workflow.md`
- Read domain-specific: `context/architecture.md`, `context/tech_stack.md` (if touching those areas)
- Read `context/memory.md` for project-specific patterns and gotchas

---

## Phase 3 — Review

**All reviews are routed through the `orchestrator`.**

### Invocation Rules

| Rule | Specification |
|------|--------------|
| Default reviewers | 1 reviewer per task |
| Multi-reviewer | Only when task genuinely crosses domains |
| Automatic review | ❌ Never — always explicit invocation |
| Review after every commit | ❌ No — review after logical implementation units |

### Agent Trigger Map

| Change Domain | Reviewer | When Multiple |
|--------------|---------|--------------|
| ML model code, training, inference | `ai-reviewer` | + `science-reviewer` if research |
| Scientific methods, calibration, experiments | `science-reviewer` | + `ai-reviewer` if model involved |
| Auth, data handling, APIs, secrets | `security-reviewer` | + `performance-reviewer` if infra |
| Frontend, accessibility, design | `ui-reviewer` | + `docs-reviewer` if content changes |
| Critical paths, high-load, latency | `performance-reviewer` | standalone |
| Documentation, READMEs, guides | `docs-reviewer` | standalone |
| Release preparation | `release-reviewer` | + `security-reviewer` always |
| Architecture decisions | `chief-architect` | standalone |
| Planning, scope | `planner` | standalone |

### Review Output Format

Every reviewer produces:
```
## Review: [Domain] — [PASS | FAIL | CONDITIONAL PASS]

**Findings:**
- [CRITICAL] issue that blocks merge
- [MAJOR] issue that should be fixed before merge
- [MINOR] suggestion

**Confidence:** [HIGH | MEDIUM | LOW]
**Escalate to Chief Architect:** [YES if architectural conflict | NO]
```

---

## Phase 4 — Milestone Gates

> ⚠️ `qa-reviewer` and `release-reviewer` are **milestone agents** — not per-commit agents.

### Quality Gate Matrix

| Gate | Trigger | Agent | Checklist | Human Approval |
|------|---------|-------|-----------|----------------|
| Feature Complete | Feature marked done | `qa-reviewer` | `checklists/feature_completion.md` | Required |
| Pull Request | Before merging | reviewer via orchestrator | `checklists/pull_request.md` | Required |
| Bug Fix Closed | Bug marked resolved | author + `qa-reviewer` | `checklists/bug_fix.md` | Required |
| Security Review | Quarterly or on security change | `security-reviewer` | `checklists/security_review.md` | Required |
| Pre-Release | Release branch created | `release-reviewer` + `security-reviewer` | `checklists/release.md` | Required |
| Deployment | Approved for deploy | deployer | `checklists/deployment.md` | Required |
| Research Validation | Experiment complete | `science-reviewer` | `checklists/research_validation.md` | Required |

**Rule:** No gate passes automatically. Every gate requires human sign-off.

---

## Phase 5 — Release

**Trigger:** Pre-release gate passed.

**Invoke:** `release-reviewer`

**Steps:**
1. `release-reviewer` reads `checklists/release.md` — verifies all items.
2. `security-reviewer` runs final security pass.
3. `qa-reviewer` confirms QA gate was cleared.
4. `docs-reviewer` verifies documentation is current.
5. Human engineer approves the release.
6. Apply `checklists/deployment.md`.
7. Create release notes from `templates/release_notes.md` → save to `artifacts/releases/`.
8. Tag the release in version control.
9. Update `context/state.md` — advance to next phase/sprint.

**Exit Criteria:** All checklists cleared. Human approved. Release artifact in `artifacts/releases/`. Version tagged.

---

## Escalation Process

```
Problem arises during a task
        │
        ▼
Can the assigned reviewer resolve it?
   YES → continue
   NO  → escalate to orchestrator
        │
        ▼
Is it a conflict between two reviewers?
   NO  → ask human for clarification
   YES → escalate to chief-architect
        │
        ▼
Chief Architect reviews both positions
        │
        ▼
Chief Architect decides
        │
        ▼
Create ADR in artifacts/decisions/
        │
        ▼
Update context/decisions.md index
        │
        ▼
Project continues
```

**Rule:** Agents never stall. If blocked → escalate immediately.

---

## Required Context Loading

Every agent reads these files before beginning work:

| File | Always | Conditional |
|------|--------|------------|
| `context/vision.md` | ✅ | |
| `context/state.md` | ✅ | |
| `context/workflow.md` | ✅ | |
| `context/architecture.md` | | Architecture-touching tasks |
| `context/tech_stack.md` | | Dependency/infrastructure tasks |
| `context/memory.md` | | Domain-specific pattern needed |
| `context/decisions.md` | | Referencing past decisions |
| `metrics/benchmarks.md` | | AI/ML or performance tasks |
| `standards/{domain}.md` | | Domain-specific review |
| `checklists/{gate}.md` | | At milestone gates |

**Token budget per session:** Read only what the task requires. Never load all context files by default.

---

## Continuous Improvement Loop

After every significant task:

```
Task complete
     │
     ▼
Update context/state.md
     │
     ▼
Did anything surprising happen?
   YES → add to context/memory.md (gotcha or pattern)
   NO  → continue
     │
     ▼
Was a decision made?
   YES → create ADR → update context/decisions.md
   NO  → continue
     │
     ▼
Was a lesson learned?
   YES → add entry to lessons/
   NO  → continue
     │
     ▼
Did a failure reveal a process gap?
   YES → update the relevant workflow, standard, or checklist
   NO  → done
```

**Principle:** Fix the process, not just the symptom. Every recurring failure is a workflow gap.

---

## Research Workflow (Abbreviated)

For AI/ML and scientific projects, see `workflows/research.md` for the full SOP.

Summary:
1. Hypothesis → `context/memory.md` (active experiments section)
2. Design → `science-reviewer` reviews methodology
3. Execute → log to `templates/experiment_log.md` → save to `artifacts/experiments/`
4. Validate → `science-reviewer` runs `checklists/research_validation.md`
5. Document → findings in experiment log
6. Update → `context/memory.md` with discoveries; `context/state.md`

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|-------------|-------------|-----------------|
| Running all reviewers on every task | Token waste, reviewer fatigue | Trigger map — one reviewer per domain |
| Skipping milestone gates for "small" releases | Production failures | Every release uses `checklists/release.md` |
| Implementing without reading `context/state.md` | Working on wrong priority | State read is mandatory |
| Letting agents argue unresolved | Project stalls | Escalate to chief-architect immediately |
| Writing ADRs after decisions are implemented | No audit trail | ADR before or immediately after the decision |
| Updating `context/memory.md` for single-use facts | Context bloat | Only add if it's needed repeatedly |
| Skipping the continuous improvement loop | Recurring failures | Always run after significant tasks |

---

*workflows/master.md — The primary orchestration reference for AgentOS. Read by the orchestrator before every task dispatch.*

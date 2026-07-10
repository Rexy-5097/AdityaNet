# AgentOS — AI Assistant Specification & Initialization Protocol

> **Version:** 1.0.0 | **Status:** Stable | **Architecture:** Frozen
>
> This is the SINGLE canonical entrypoint for every AI coding assistant operating inside an AgentOS repository.
> Read this file FIRST. Do not begin implementation until initialization completes successfully.

---

## 1. System Philosophy

AgentOS is a **deterministic engineering operating system**. It is not a prompt library. It is not a boilerplate. It is infrastructure.

It governs how AI agents, human engineers, and deterministic tools collaborate on any engineering project — from hackathons to production SaaS systems to ISRO-scale scientific research.

**Three immutable laws govern all AgentOS operations:**

1. **WAT Separation** — Workflows (SOPs), Agents (decisions), and Tools (execution) are always kept in separate layers. They never bleed into each other.
2. **Architecture First** — Design before building. Review before shipping. Measure before optimizing. No implementation begins without a plan.
3. **Vendor Neutrality** — AgentOS works with any AI assistant. Core framework logic never depends on a specific AI provider. Vendor adapters live exclusively in `integrations/`.

---

## 2. Initialization Protocol

When you open an AgentOS repository, execute these steps **in order** before doing anything else:

```
STEP 1 → Read AGENTOS.md (this file) completely
STEP 2 → Read README.md (architecture overview)
STEP 3 → Read context/vision.md (project goals and success criteria)
STEP 4 → Read context/state.md (current project status)
STEP 5 → Read PROJECT_CONFIG.yaml (active profile and feature flags)
STEP 6 → Load runtime/policies/routing.yaml (agent routing rules)
STEP 7 → Run validation: python3 tools/scripts/validate_agentos.py
STEP 8 → Confirm health score = 100/100 before proceeding
STEP 9 → Report initialization status to the human engineer
STEP 10 → Await task assignment
```

**CRITICAL:** Do not modify any files, generate code, or begin implementation until Steps 1–9 are confirmed complete. If the validator reports warnings, surface them to the human engineer before proceeding.

---

## 3. Repository Discovery Rules

When an AI assistant is opened inside an AgentOS repository, it should discover components in this priority order:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `AGENTOS.md` | This initialization specification |
| 2 | `README.md` | Repository architecture and quick start |
| 3 | `context/vision.md` | Project goals and success criteria |
| 4 | `context/state.md` | Live project status |
| 5 | `PROJECT_CONFIG.yaml` | Active configuration and feature flags |
| 6 | `runtime/policies/routing.yaml` | Agent routing override rules |
| 7 | `context/decisions.md` | ADR index (read before architectural work) |
| 8 | `context/workflow.md` | Project-adapted master SOP |

Do **not** eagerly load entire subdirectories. AgentOS is designed for token efficiency. Load only what is needed for the current task.

---

## 4. Required Reading Order

For a **new project** (first session):
```
AGENTOS.md → README.md → context/vision.md → context/state.md
→ PROJECT_CONFIG.yaml → workflows/master.md
```

For an **ongoing project** (returning session):
```
AGENTOS.md → context/state.md → context/decisions.md (recent entries)
→ task assignment
```

For an **architectural task**:
```
AGENTOS.md → context/architecture.md → context/decisions.md
→ agents/chief-architect.md → artifacts/decisions/ (relevant ADRs)
```

For a **feature implementation**:
```
AGENTOS.md → context/state.md → workflows/feature_development.md
→ agents/planner.md → agents/{relevant-reviewer}.md
→ checklists/feature_completion.md
```

---

## 5. Context Loading Protocol

AgentOS uses a **minimal context strategy** to preserve token budgets:

**Always load (every session):**
- `AGENTOS.md` — This file
- `context/state.md` — Current project status
- `PROJECT_CONFIG.yaml` — Active feature flags

**Load on demand (when task requires it):**
- `context/vision.md` — When clarifying project goals
- `context/architecture.md` — When making architectural decisions
- `context/decisions.md` — When referencing ADRs
- `context/tech_stack.md` — When referencing technology choices
- `agents/{agent}.md` — When invoking a specific specialist
- `standards/{standard}.md` — When enforcing a specific quality rule
- `checklists/{gate}.md` — When verifying milestone gates

**Never load eagerly:**
- Entire `artifacts/decisions/` directory (56+ ADRs — expensive)
- Entire `validation/scenarios/` directory
- Entire `runtime/` directory (kernel internals)

---

## 6. Bootstrap Procedure

If this is a **fresh project setup** (PROJECT_CONFIG.yaml is missing or empty), run:

```bash
# Option 1: Interactive setup
python3 tools/scripts/bootstrap_project.py --interactive

# Option 2: Use defaults
python3 tools/scripts/bootstrap_project.py --defaults

# Option 3: Use a specific profile
python3 tools/scripts/bootstrap_project.py --profile backend --defaults

# Option 4: Load from config file
python3 tools/scripts/bootstrap_project.py --config my_project.yaml

# Option 5: Resume interrupted setup
python3 tools/scripts/bootstrap_project.py --resume

# Option 6: Verify the bootstrap system
python3 tools/scripts/bootstrap_project.py --self-test
```

Available profiles: `ai_project` | `backend` | `frontend` | `ml` | `research` | `isro` | `hackathon` | `flagship`

Bootstrap generates:
- `PROJECT_CONFIG.yaml` — Active project configuration
- `context/vision.md` — Initial project vision template
- `context/state.md` — Initial project state

---

## 7. Harness Runtime Usage

The Harness is the **task dispatcher**. It receives a task description, classifies it, routes it to the correct agent(s), and produces an execution plan.

```bash
python3 tools/scripts/harness_engine.py \
  --task "Implement JWT authentication" \
  --files "auth/jwt.py,auth/middleware.py" \
  --loop-mode Balanced
```

**Loop modes:**
- `Fast` — 1–2 iterations, quick feedback
- `Balanced` — 3–5 iterations, standard quality (default)
- `Exhaustive` — unlimited iterations until threshold met

The Harness will:
1. Classify the task domain
2. Route to appropriate specialist reviewers
3. Run the Loop Runtime
4. Produce iteration reports
5. Exit when quality threshold is satisfied

**Do not call agents directly.** Always route through the Harness.

---

## 8. Loop Runtime Usage

The Loop Runtime is the **iterative refinement engine**. It runs inside the Harness. You should not invoke it directly in most cases.

If you need direct loop control:

```bash
python3 -c "
from runtime.loop.runtime import LoopRuntime
loop = LoopRuntime('.')
results = loop.execute_loop(plan, loop_mode='Balanced')
print(results)
"
```

The Loop internally runs:
```
Iteration Controller → Reflection Engine → Improvement Planner
→ Execution Monitor → Quality Evaluator → Termination Check
```

---

## 9. Quality Gate Usage

Quality gates are **milestone verification checkpoints**. They must pass before advancing to the next project phase.

| Gate | File | When to Run |
|------|------|-------------|
| QG-001 | `checklists/feature_completion.md` | Before merging a feature |
| QG-002 | `checklists/pull_request.md` | Before submitting a PR |
| QG-003 | `checklists/qa.md` | Before QA signoff |
| QG-004 | `checklists/research_validation.md` | Before research publication |
| QG-005 | `checklists/security_review.md` | Before handling sensitive data |
| QG-006 | `checklists/deployment.md` | Before deploying to production |
| QG-007 | `checklists/bug_fix.md` | Before closing a bug |
| QG-008 | `checklists/release.md` | Before cutting a release |

**Rule:** All checklist items must be ✅ before gate is declared PASS.

---

## 10. Standards Usage

Standards define **what quality means** in each engineering domain.

| Standard | When to Apply |
|----------|--------------|
| `standards/code_quality.md` | All code changes |
| `standards/testing.md` | All feature implementations |
| `standards/documentation.md` | All documentation changes |
| `standards/security.md` | Auth, data handling, APIs |
| `standards/ai_ml.md` | Model code, AI pipelines |
| `standards/research.md` | Scientific experiments |
| `standards/api_design.md` | REST or GraphQL work |
| `standards/data_engineering.md` | Pipelines, ETL, data |
| `standards/ui_ux.md` | Frontend, interaction |

Apply the relevant standard before implementation. Reference the standard in your review comments.

---

## 11. Artifact Generation Rules

Every significant engineering decision must generate an artifact:

| Event | Artifact Type | Location |
|-------|--------------|----------|
| Architectural decision | ADR | `artifacts/decisions/ADR-XXXX-title.md` |
| Experiment completed | Experiment log | `artifacts/experiments/` |
| Incident resolved | Post-mortem | `artifacts/incidents/` |
| Release cut | Release notes | `artifacts/releases/` |
| Architecture reviewed | Review document | `artifacts/reviews/` |

Use templates from `templates/` to generate artifacts. Never skip artifact generation for significant decisions.

After creating an ADR:
1. Add it to `context/decisions.md` index
2. Bump the ADR counter in `.agentos/manifest.yml`

---

## 12. Validation Procedure

Run the validator after every significant change:

```bash
python3 tools/scripts/validate_agentos.py
```

**Expected output:** `Overall Grade: 100/100 | Final Status: PASS`

The validator checks 18 categories:
- Structural, Contract, Dependency, Token Budget, Cross-reference
- Architecture, Agent Routing, Workflow, Standards, Metrics
- Artifacts, Bootstrap, Harness, Loop, Validation Suite
- Production, Certification, Distribution

If the validator score drops below 100, surface warnings to the human engineer before proceeding.

---

## 13. Execution Lifecycle

The complete lifecycle for any engineering task:

```
1. INITIALIZE   → Load AGENTOS.md, context/state.md, PROJECT_CONFIG.yaml
2. DISCOVER     → Read context/vision.md, context/architecture.md if needed
3. PLAN         → Invoke planner agent, define scope and approach
4. ROUTE        → Harness classifies task, routes to reviewer(s)
5. IMPLEMENT    → Code changes with standards applied
6. LOOP         → Loop Runtime refines until quality threshold met
7. REVIEW       → Specialist reviewer validates quality
8. GATE         → Run appropriate quality checklist
9. ARTIFACT     → Generate ADR or artifact if needed
10. UPDATE      → Update context/state.md with progress
11. VALIDATE    → Run validate_agentos.py
12. REPORT      → Report status to human engineer
```

**Key invariants:**
- Step 1 always runs before any other step
- Steps 6–7 never skip, even for small changes
- Step 10 runs at the end of every session
- Step 11 always confirms 100/100 before declaring DONE

---

## 14. Shutdown Rules

At the end of every working session:

```
✅ Update context/state.md with completed tasks and current status
✅ Commit or stage all changes
✅ Run validator: python3 tools/scripts/validate_agentos.py
✅ Confirm 100/100 score
✅ Report session summary to human engineer
✅ List open tasks for next session
```

**Never leave a session with:**
- Uncommitted changes to context/state.md
- Validator score below 100
- Incomplete quality gates
- Unlogged architectural decisions

---

## Quick Reference

```
Bootstrap:  python3 tools/scripts/bootstrap_project.py --defaults
Validate:   python3 tools/scripts/validate_agentos.py
Harness:    python3 tools/scripts/harness_engine.py --task "..." --loop-mode Balanced
Suite:      python3 validation/runner/execute_suite.py
Make:       make bootstrap | make validate | make health | make test | make examples
```

---

*AgentOS v1.0.0 — Engineering infrastructure built for decades, not deadlines.*

# Agents — WAT Layer 2

> **Layer:** Infrastructure | **Status:** Active — Completed in Phase 4
> **Purpose:** Agent Contracts, Lifecycles, and Capabilities registry.
> **Required Reading:** Read by developers and agents to understand roles and interfaces.
> **Cross-refs:** `agents/CAPABILITIES.md` · `agents/TESTS.md` · `workflows/master.md`

---

## Purpose

Agents are **specialist decision-makers and reviewers** — not implementation workers.

The main coding session implements. Agents plan, route, review, validate, and decide.

---

## Core Principles

### Agents are explicitly invoked
Agents never run automatically. The orchestrator or human engineer invokes them when their domain is relevant.

### One task, one reviewer (by default)
Most tasks need exactly one reviewer. The orchestrator prevents redundant reviews. Only genuinely cross-domain changes require multiple reviewers.

### Agents do not argue
When two reviewers disagree, the **Chief Architect** makes the final call. The decision is logged as an ADR. The project continues.

### Agents are narrow
Each agent has a clearly defined domain. If a task doesn't touch that domain, the agent is not invoked.

---

## Agent Dependency & Authority Graph

This diagram shows how authority, rules, and outcomes flow within AgentOS:

```
        Human Engineer (L4 Authority)
              │
              ▼
        orchestrator (L1 Coordination)
              │
              ├───────▶ chief-architect (L3 Authority)
              │               │
              │               ▼
              │         creates ADRs (artifacts/decisions/)
              │
              ▼
      Specialist Reviewers (L2 Domain Reviewers)
     (planner · ai · science · security · performance · ui · qa · docs · release)
              │
              ├───────▶ reads: Standards (standards/)
              ├───────▶ reads: Metrics (metrics/)
              ├───────▶ executes: Checklists (checklists/)
              ▼
      outputs: Review Reports (artifacts/releases/ · artifacts/experiments/)
```

---

## Agent Roster

| Agent | File | Domain | When to Invoke |
|-------|------|--------|---------------|
| `orchestrator` | `orchestrator.md` | Routing and coordination | Start of any non-trivial task |
| `chief-architect` | `chief-architect.md` | Architecture and conflict resolution | Architectural decisions, reviewer conflicts |
| `planner` | `planner.md` | Scope, milestones, task breakdown | New features, project planning |
| `ai-reviewer` | `ai-reviewer.md` | ML models, AI systems, inference | Model code, training pipelines, AI behavior |
| `science-reviewer` | `science-reviewer.md` | Scientific validity, reproducibility | Experiments, calibration, research methods |
| `security-reviewer` | `security-reviewer.md` | Security, threat models | Auth, data handling, APIs, infrastructure |
| `performance-reviewer` | `performance-reviewer.md` | Performance, scalability | Critical paths, high-load components |
| `ui-reviewer` | `ui-reviewer.md` | UI/UX, accessibility | Frontend, interaction design, design systems |
| `qa-reviewer` | `qa-reviewer.md` | Quality assurance | Feature completion, pre-release milestones |
| `docs-reviewer` | `docs-reviewer.md` | Documentation completeness | Documentation changes, pre-release |
| `release-reviewer` | `release-reviewer.md` | Release readiness | Release preparation only |

---

## Dynamic Routing & Test Cases

Agent routing is governed by two core supporting structures:
1. **[CAPABILITIES.md](./CAPABILITIES.md):** The Orchestrator's routing table mapping file scopes to agent permissions.
2. **[TESTS.md](./TESTS.md):** Formal input/output test cases to verify the routing engine statically.

---

## Agent Lifecycle

Every agent in this directory operates according to a strict 7-stage lifecycle state machine:
1. **Idle:** Waiting for task invocation.
2. **Invoked:** Initialized with user task and git diff file list.
3. **Loading Context:** Loads target context files (defined in the agent's contract).
4. **Reviewing:** Runs its internal evaluation against the standards.
5. **Decision:** Generates binary YES/NO checks and decides Pass/Fail status.
6. **Output:** Formats and writes the output report.
7. **Completed:** Yields control back to the Orchestrator or human.

---

*Agent specification directory. All contracts are active and versioned.*

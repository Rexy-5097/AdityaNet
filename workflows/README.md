# Workflows — WAT Layer 1

> **Layer:** Infrastructure | **Status:** Placeholders — Populated in Phase 2

---

## Purpose

Workflows are **Standard Operating Procedures (SOPs)** — human-readable documents that define:
- The objective of a type of work
- The expected input and output
- The step-by-step execution order
- Agent invocation points
- Edge cases and failure handling
- Exit criteria

---

## WAT Philosophy

```
WORKFLOWS  ──→  define what to do and in what order
    ↓
AGENTS     ──→  decide, coordinate, and invoke tools
    ↓
TOOLS      ──→  execute deterministically
```

Workflows do NOT execute code. Agents follow workflows and invoke tools.

---

## Available Workflows

| Workflow | Trigger | Typical Duration |
|---------|---------|-----------------|
| `master.md` | Start of any significant work | Continuous |
| `feature_development.md` | New feature request | Hours to days |
| `bug_fix.md` | Bug report or regression | Minutes to hours |
| `research.md` | Experiment or investigation | Hours to weeks |
| `release.md` | Approaching a release | Days |
| `incident_response.md` | Production incident | Minutes to hours |

---

## How to Use Workflows

1. Identify what kind of work is starting.
2. Read the appropriate workflow before beginning.
3. Follow the steps in order.
4. Invoke agents at the designated review points.
5. Use checklists from `checklists/` at milestone gates.
6. Log decisions to `artifacts/decisions/`.

---

## How to Add a New Workflow

1. Copy the closest existing workflow as a starting point.
2. Name it descriptively: `{domain}_workflow.md`.
3. Define: objective, inputs, outputs, steps, agent triggers, edge cases, exit criteria.
4. Add it to the table above.
5. Register it in `.agentos/manifest.yml`.

---

*Phase 2 will populate all workflow files in this directory.*

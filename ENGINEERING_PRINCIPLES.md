# Engineering Principles

> **Layer:** Infrastructure | **Version:** 0.1.0 | **Status:** Authoritative
> This document is the philosophical foundation of AgentOS.
> All agents, workflows, standards, and checklists derive from these principles.

---

## 1. Architecture First

Design before implementing. Implementation without architecture produces systems that cannot be maintained, scaled, or reasoned about.

Before writing code:
- Define the system boundaries
- Map the data flow
- Identify the failure modes
- Record the decision

---

## 2. Separation of Concerns

Each component, file, agent, and workflow should have exactly one clearly defined responsibility.

When a component does two things, it should become two components.

Applied throughout this repository:
- `workflows/` defines process; `agents/` makes decisions; `tools/` executes
- `standards/` defines quality; `checklists/` verifies it
- `templates/` provides structure; `artifacts/` accumulates instances
- `context/` provides live project state; `artifacts/` stores history

---

## 3. Evidence over Consensus

Engineering decisions must be based on evidence — measurements, experiments, data — not on the preferences of the loudest voice or the consensus of the group.

When reviewing:
- Ask: "What is the evidence?"
- Ask: "What would falsify this claim?"
- Reject decisions made purely from intuition when evidence is obtainable

---

## 4. Measure Before Optimizing

Optimization without measurement is guessing.

Before claiming a system is slow, measure it.
Before claiming an optimization is an improvement, measure both before and after.
Define success criteria in `metrics/` before beginning performance work.

---

## 5. Incremental Development

Build one thing at a time. Review it. Improve it. Then build the next thing.

A partially-complete well-reviewed system is more valuable than a complete unreviewed system.

Applied in this repository: each phase of AgentOS development is reviewed and approved before the next phase begins.

---

## 6. Minimize Context Surface

In AI-assisted engineering, every token loaded into context has a cost.

Write documentation for agents, not for archives. Keep `context/` files compact. Use indices that point to detail rather than embedding all detail in every file.

If information can be derived, don't store it. If information must be stored, store it once.

---

## 7. Human Owns Final Decisions

AI agents plan, review, validate, and recommend. Humans decide.

No agent should have automatic authority to merge, deploy, or ship. Every milestone gate requires human approval.

This is not a limitation — it is a feature. Accountability requires human ownership.

---

## 8. Explicit over Automatic

Agents are invoked explicitly, not automatically. Workflows are triggered intentionally, not by side effects. Tools are called deliberately, not implicitly.

When a system acts automatically, failures become hard to trace. When a system acts explicitly, every action has a clear cause.

---

## 9. Reusable Infrastructure

Build things once and reuse them everywhere. Standards, checklists, templates, and agent specifications should be project-agnostic.

When you find yourself writing the same standard twice for two different projects, extract it into AgentOS.

---

## 10. Documentation as Code

Documentation has the same lifecycle as code:
- It is written when features are built
- It is reviewed before merging
- It is updated when behavior changes
- It is deleted when features are removed

Documentation that lags code is worse than no documentation, because it misleads.

---

## 11. Continuous Improvement

When a failure occurs:
1. Find the root cause
2. Fix the process, not just the symptom
3. Verify the fix
4. Update the workflow to prevent recurrence
5. Add the lesson to `lessons/`

A system that repeats the same failure has not learned.

---

## 12. Vendor Neutrality

Engineering infrastructure should not be locked to a specific AI provider, cloud platform, or tool vendor.

AgentOS integrates with specific tools through the `integrations/` directory. Everything outside `integrations/` is vendor-neutral.

This ensures AgentOS remains useful as AI tools evolve.

---

## 13. Narrow Agent Responsibilities

An agent that does everything is an agent that can be replaced by nothing.

Each specialist agent in AgentOS has a precisely defined domain, a list of what it does NOT do, and an explicit escalation path. This makes agents reliable, predictable, and replaceable.

---

## Principle Hierarchy

When principles conflict:

```
Human Owns Final Decisions          (always overrides)
      ↓
Architecture First
      ↓
Separation of Concerns
      ↓
Evidence over Consensus
      ↓
All other principles (equal weight)
```

---

## 14. Architecture Freeze

Upon reaching v1.0.0, the core design principles and folder structures are frozen. No new agents, workflows, engines, or standards categories may be added without documented production failure evidence from flagship project usage. Modifications require a new major version release.

---

*AgentOS Engineering Principles — The philosophical foundation of this repository.*

# Lessons

> **Layer:** Infrastructure → Project-owned over time
> **Purpose:** The repository learns. So does the team.

---

## Why Lessons Exist

Decisions are captured in `artifacts/decisions/` — but decisions record *what was decided*.

Lessons capture *what was learned* — from failures, from discoveries, from patterns that repeat.

Without lessons, a team:
- Repeats the same mistakes on every project
- Re-discovers the same best practices from scratch
- Loses institutional knowledge when engineers move on

With lessons, the repository becomes smarter over time.

---

## What Belongs Here

| Category | Examples |
|---------|---------|
| Engineering lessons | "Premature abstraction cost us 2 days" |
| Scientific lessons | "This dataset has class imbalance that requires stratified splits" |
| Recurring mistakes | "Forgetting to validate model outputs before training" |
| Discovered best practices | "Always profile before optimizing the data loader" |
| Architecture insights | "Services that share a database become tightly coupled faster than expected" |
| Process improvements | "Daily state updates halved agent context setup time" |

---

## How to Add a Lesson

1. Create a file: `lessons/{YYYY-MM-DD}-{brief-slug}.md`
2. Use this format:

```markdown
# Lesson: [Brief Title]

**Date:** YYYY-MM-DD
**Category:** [Engineering | Scientific | Process | Architecture]
**Severity:** [Minor | Significant | Critical]

## What Happened
[Brief description of the situation]

## What We Learned
[The insight — what to do or avoid next time]

## How to Apply This
[Concrete guidance for future work]

## Related
[Links to ADRs, experiments, or standards this lesson informs]
```

3. Add a row to the index below.
4. If the lesson reveals a gap in the standards or checklists, update them.

---

## Lesson Index

| Date | Title | Category | Severity |
|------|-------|---------|---------|
| *(none yet)* | | | |

---

## Rules

- Lessons are never deleted — they are the institutional memory of the project.
- A lesson that improves a standard should update that standard immediately.
- Lessons are written for future engineers and agents, not to assign blame.

---

*Lessons accumulate here over the project lifetime. The more lessons this directory contains, the smarter the system becomes.*

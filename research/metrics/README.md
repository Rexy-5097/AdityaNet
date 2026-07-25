# Metrics Layer

> **Layer:** Infrastructure | **Status:** Active — Completed in Phase 3
> **Purpose:** Measurable engineering targets — not subjective reviews.
> **Cross-refs:** `standards/README.md` · `checklists/README.md` · `workflows/master.md`

---

## Why Metrics Exist

Engineering reviews without measurable baselines produce opinions, not findings.

The `metrics/` directory defines the **measurable targets** that agents and humans compare work against.

Before optimizing: define the target.
Before reviewing: know the baseline.
After implementing: measure the delta.

---

## Metrics Categories

| File | Domain | Key Metrics Covered | Target Consumer |
|------|--------|---------------------|-----------------|
| [performance.md](file:///Users/soumyadebtripathy/WorkFlow/agentos-template/metrics/performance.md) | System Performance | Latency (P50/P95/P99), throughput, availability, cold start, CPU/GPU, memory | `performance-reviewer` |
| [quality.md](file:///Users/soumyadebtripathy/WorkFlow/agentos-template/metrics/quality.md) | Code & Process Quality | Test coverage (line/branch/mutation), cyclomatic complexity, MTTR, MTTD, defect escape rate | `qa-reviewer` |
| [benchmarks.md](file:///Users/soumyadebtripathy/WorkFlow/agentos-template/metrics/benchmarks.md) | AI/ML & Research | Accuracy, precision, recall, F1, LLM evaluation (MMLU, GSM8K, RAG), statistical power, reproducibility | `ai-reviewer` · `science-reviewer` |

---

## How Agents Use Metrics

1. **Required Loading:** When triggered for performance, QA, or AI tasks, the orchestrator directs the reviewer to load the corresponding metrics file.
2. **Objective Analysis:** Reviewers extract target and acceptable range values directly from the tables.
3. **Automated Verification:** The agent compares automated test outputs or system benchmarks against the ranges.
4. **Binary Pass/Fail:** If any critical metric falls in the failure threshold, the reviewer issues a conditional pass or a fail.

---

## Customizing Metrics (Per Project)

When deploying this template:
1. Populate the **Project Targets** section in the respective metric files with your system's baselines and goals.
2. Ensure you have automated scripts under `tools/scripts/` to measure these metrics (e.g. running a load test, checking test coverage, or calculating model accuracy).
3. The default target values in these files are the **Production Grade** standards. Adjust them if your project runs at a different target level (Minimum, Recommended, or Flagship).

---

*Metrics define what success looks like. Checklists verify that it was achieved.*

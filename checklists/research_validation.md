# Quality Gate: QG-004 Research Validation

> **Gate ID:** QG-004 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `science-reviewer` | **Participating Agents:** `ai-reviewer`
> **Estimated Runtime:** 30 min | **Gate Severity:** Recommended
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 2 retries, escalates to chief-architect)
> **Required Context:** `metrics/benchmarks.md` · `standards/research.md` · `standards/ai_ml.md` · `artifacts/experiments/`

---

## Purpose

Validate scientific experiment logs, model accuracy scores, statistical reproducibility, and data splits before mathematical/algorithmic logic is accepted.

## Entry Criteria

- Experiment execution finishes and logs are recorded.
- Expected hypothesis was logged in `context/memory.md` prior to data run.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Hypothesis Logged**| Match timestamps in git log | Pre-logged state in history | YES |
| **Statistical Power**| Compute power analysis | Power score ≥ 0.80 | YES |
| **Reproducibility Run**| Run clean-room execution | Container logs output PASS | YES |
| **Data Split Split** | Review split documentation | Test dataset held out explicitly | YES (0% leakage) |
| **Baseline Mapped** | Compare against baseline | Model score > baseline score | YES |

---

## Exit Decision Model

- **PASS:** Hypothesis matches, no data leakage, reproducibility runs pass, baseline exceeded. Quality score = 100.
- **PASS WITH WARNINGS:** Model outperforms baseline but reproducibility correlation is between 0.95 and 0.99. Score = 80-99.
- **FAIL:** Data leakage detected, model underperforms baseline, or irreproducible execution. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Archive the experiment as "FAILED" in `artifacts/experiments/`. Rerun only after fixing data parameters.
- **Divergence:** If `science-reviewer` and `ai-reviewer` disagree on validation, escalate to `chief-architect`.

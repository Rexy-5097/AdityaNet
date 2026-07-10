# Quality Gate: QG-001 Feature Completion

> **Gate ID:** QG-001 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `qa-reviewer` | **Participating Agents:** `docs-reviewer`
> **Estimated Runtime:** 5 min | **Gate Severity:** Mandatory
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 3 retries, escalates to chief-architect)
> **Required Context:** `context/state.md` · `standards/code_quality.md` · `metrics/quality.md`

---

## Purpose

Verify that a newly developed feature is functionally complete, tested, documented, and adheres to core standards before PR merge checks begin.

## Entry Criteria

- Backlog issue is assigned and in `IN_PROGRESS` or `IN_REVIEW`.
- Code changes pass basic local compiler/interpreter tests.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Unit Tests Exist** | Check file modifications | Link to test file path | YES (at least 1 new test) |
| **Linters Pass** | Run luff/eslint in CI | Log output file showing zero errors | YES |
| **Complexity Checked** | Compute cyclomatic complexity | Radon/Sonar report ≤ level limit | YES |
| **Docstrings Present** | Scan new public methods | Code block reference | YES (100% public APIs) |
| **State Updated** | Check `context/state.md` | Task marked `IN_REVIEW` | YES |

---

## Exit Decision Model

- **PASS:** All items are YES. Quality score = 100.
- **PASS WITH WARNINGS:** Complexity is slightly over target but under max limit, or linter has minor formatting warnings. Score = 80-99.
- **FAIL:** Missing tests, missing linter pass, or undocumented public APIs. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Return list of failing lines/files to the author. Rerun is allowed immediately.
- **Retry Exceeded:** If 3 consecutive failures occur, lock the task and escalate to `chief-architect`.

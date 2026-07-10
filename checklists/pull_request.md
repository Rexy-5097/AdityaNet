# Quality Gate: QG-002 Pull Request Review

> **Gate ID:** QG-002 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** Code Reviewer (Agent/Human) | **Participating Agents:** `orchestrator`
> **Estimated Runtime:** 15 min | **Gate Severity:** Mandatory
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 2 retries, escalates to chief-architect)
> **Required Context:** `context/state.md` · `standards/code_quality.md` · `standards/testing.md` · `metrics/quality.md`

---

## Purpose

Verify code changes before merging into the main repository branch. Prevents syntax degradation, regression, and undocumented architectural drift.

## Entry Criteria

- `QG-001` (Feature Completion) status is PASS.
- Pull request branch created and CI builds compile.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Branch Divergence** | Check git merge status | Git status output "no conflict" | YES |
| **Standards Met** | Verify against code_quality.md | Review checkbook results | YES |
| **No Dead Code** | Code review scan | Diff inspection for commented blocks | YES |
| **Test Quality** | Verify assertions are meaningful | Test code file path review | YES |
| **Changelog Current**| Scan `CHANGELOG.md` | New lines under Unreleased/Unpublished | YES |

---

## Exit Decision Model

- **PASS:** No conflicts, standards met, assertions pass, changelog updated. Quality score = 100.
- **PASS WITH WARNINGS:** Assertions valid but coverage didn't increase, or minor structural comments resolved post-merge. Score = 80-99.
- **FAIL:** Merge conflicts, hardcoded variables, missing test assertions, or undocumented changes. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Reject PR and assign back to author with findings list.
- **Disagreement:** If author disagrees with reviewer findings, escalate to `chief-architect` to resolve.

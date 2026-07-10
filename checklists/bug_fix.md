# Quality Gate: QG-007 Bug Fix

> **Gate ID:** QG-007 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `qa-reviewer` | **Participating Agents:** `security-reviewer` (if security bug)
> **Estimated Runtime:** 5 min | **Gate Severity:** Mandatory
> **Automation Level:** Automatic | **Retry Policy:** Allowed (Max 3 retries, escalates to chief-architect)
> **Required Context:** `context/state.md` · `standards/testing.md` · `metrics/quality.md`

---

## Purpose

Validate that a reported defect has been successfully resolved, that a regression test exists, and that no new bugs were introduced.

## Entry Criteria

- Bug is assigned, fixed, and task is set to `IN_REVIEW`.
- Clean compilation in test environment.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Regression Test** | Verify test existence | Path to test verifying bug case | YES (at least 1 test) |
| **Defect Resolved** | Execute regression test | Log showing test PASS | YES |
| **No Regression** | Run full test suite | Execution report showing 0 failed | YES |
| **Clean Linting** | Run code linter | Zero errors in modified files | YES |
| **State Updated** | Check `context/state.md` | Bug status marked `RESOLVED` | YES |

---

## Exit Decision Model

- **PASS:** Regression test passes, full suite passes, state updated. Quality score = 100.
- **PASS WITH WARNINGS:** Regression test passes, but other tests have minor linter/formatting warnings. Score = 80-99.
- **FAIL:** Regression test fails, suite failures, or missing regression test file. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Return bug task to the developer. Rerun allowed immediately.
- **Reopen Bug:** If bug reopens > 2 times, flag task as `CRITICAL_REOPEN` and escalate to `chief-architect` for design audit.

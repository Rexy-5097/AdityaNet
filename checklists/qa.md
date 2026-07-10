# Quality Gate: QG-003 QA Verification

> **Gate ID:** QG-003 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `qa-reviewer` | **Participating Agents:** `performance-reviewer`
> **Estimated Runtime:** 10 min | **Gate Severity:** Mandatory
> **Automation Level:** Automatic | **Retry Policy:** Allowed (Max 3 retries, escalates to chief-architect)
> **Required Context:** `metrics/quality.md` · `standards/testing.md`

---

## Purpose

Enforce validation of test coverage, regression checks, and flaky test verification on milestone candidate builds.

## Entry Criteria

- `QG-002` (Pull Request) status is PASS.
- Test runner completes execution in build environment.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Unit Test Coverage** | Check code coverage output | Line coverage ratio ≥ 80% (production) | YES |
| **Branch Coverage** | Check code coverage output | Branch coverage ratio ≥ 70% | YES |
| **No Flaky Tests** | Run flaky verification (3 runs) | Test logs showing consistent PASS | YES |
| **Zero Failure Run** | Inspect final run summary | Log output showing "0 failed" | YES |
| **Regression Checked**| Match resolved bug IDs | Verified unit tests exist for each ID | YES |

---

## Exit Decision Model

- **PASS:** All coverage thresholds met, 0 failures, 0 flakiness. Quality score = 100.
- **PASS WITH WARNINGS:** Line coverage within 5% of target, or flaky tests quarantined under chief-architect sign-off. Score = 80-99.
- **FAIL:** Coverage below limits, execution fails, or unquarantined flakiness. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Block the build, publish test logs, and notify development leads.
- **Retry Policy:** Developers can rerun up to 3 times after adding regression tests or fixing flakiness. If still failing, escalate.

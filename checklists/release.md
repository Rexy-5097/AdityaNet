# Quality Gate: QG-008 Release Readiness

> **Gate ID:** QG-008 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `release-reviewer` | **Participating Agents:** `docs-reviewer` · `security-reviewer`
> **Estimated Runtime:** 15 min | **Gate Severity:** Mandatory
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 2 retries, escalates to chief-architect)
> **Required Context:** `context/state.md` · `context/decisions.md` · `VERSION_POLICY.md` · `standards/documentation.md` · `metrics/quality.md`

---

## Purpose

Enforce semantic versioning rules, compile changelog entries, verify all prior QG gates have passed, and audit release notes before packaging.

## Entry Criteria

- Release candidate branch generated.
- All active milestone feature tasks have marked `DONE` in `context/state.md`.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Gate Signs** | Audit prior QG checklists | QG-001, QG-002, QG-003, QG-005 signs all PASS | YES |
| **Semantic Version**| Verify target version string | Matches `VERSION_POLICY.md` rules | YES |
| **Changelog Match** | Compare git log vs CHANGELOG | Changelog lists all changes | YES |
| **Doc Cleanliness** | Check documentation site | Docs index compiled; no broken links | YES |
| **Zero Critical Bugs**| Scan issue tracker | 0 open Critical/Major bugs | YES |

---

## Exit Decision Model

- **PASS:** All prior gates pass, version valid, changelog matches, 0 open bugs. Quality score = 100.
- **PASS WITH WARNINGS:** Prior gates pass, but changelog contains minor formatting issues. Score = 80-99.
- **FAIL:** Outstanding gate failures, version policy breach, or open critical/major bugs. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Block the release. Do not tag branch. Assign blocking issues to product/tech leads.
- **Waiver:** If an open major bug is waived for release, it requires written authorization from `chief-architect` logged as a temporary ADR.

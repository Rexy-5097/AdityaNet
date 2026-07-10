# Quality Gate: QG-006 Deployment

> **Gate ID:** QG-006 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** Human Deployment Lead | **Participating Agents:** `performance-reviewer` · `security-reviewer`
> **Estimated Runtime:** 30 min | **Gate Severity:** Mandatory
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 2 retries, escalates to chief-architect)
> **Required Context:** `metrics/performance.md` · `standards/security.md`

---

## Purpose

Verify staging environment tests, resource boundaries, rollback mechanisms, and credentials before deploying the build candidate to production.

## Entry Criteria

- `QG-008` (Release Gate) status is PASS.
- Build successfully deployed and tested in Staging environment.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **Staging Tests** | Run E2E test suite in staging | Execution report showing 0 failed | YES |
| **Rollback Verified**| Run rollback dry-run test | Script success status | YES |
| **Secrets Injected** | Check environment vault configuration| Secrets injected via runtime container (no env keys)| YES |
| **CWV budgets** | Run Lighthouse on staging | LCP < 2.5s, CLS < 0.1, INP < 200ms | YES |
| **Infrastructure** | Check CPU/RAM footprint | Usage < 80% under load test | YES |

---

## Exit Decision Model

- **PASS:** All staging tests pass, rollback checks pass, performance limits met. Quality score = 100.
- **PASS WITH WARNINGS:** Infrastructure usage slightly over budget but within threshold under load test. Score = 80-99.
- **FAIL:** Failed staging tests, failed rollback script, exposed secrets, or severe performance lag. Score < 80.

---

## Escalation Paths

- **Gate Failure:** Roll back the staging build, halt deployment pipeline, and alert Tech Lead.
- **Post-Deploy Monitoring:** On success, transition to production monitoring rules. If monitoring alerts trigger, invoke rollback immediately.

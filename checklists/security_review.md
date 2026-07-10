# Quality Gate: QG-005 Security Review

> **Gate ID:** QG-005 | **Version:** 1.0 (Compatible AgentOS 1.x)
> **Owner:** `security-reviewer` | **Participating Agents:** `docs-reviewer`
> **Estimated Runtime:** 15 min | **Gate Severity:** Mandatory
> **Automation Level:** Semi-automatic | **Retry Policy:** Allowed (Max 2 retries, escalates to chief-architect)
> **Required Context:** `standards/security.md` · `standards/api_design.md` · `metrics/quality.md`

---

## Purpose

Enforce security standards. Scans for committed secrets, credentials leakage, authorization omissions, and dependency vulnerabilities.

## Entry Criteria

- Target build compiles successfully.
- Dependency lockfile is pinned and scanned by vulnerability checkers.

---

## Verification Checklist

| Requirement | Verification Method | Evidence Required | Pass Condition |
|-------------|---------------------|-------------------|----------------|
| **No Secrets in Code**| Scan with trufflehog/gitguardian | CI scan output showing 0 alerts | YES (0 secrets) |
| **Dependency CVEs** | Run pip-audit/npm-audit | Scan log output showing 0 Critical/High | YES |
| **Auth Implemented** | Trace API routers | Every route protected by token check | YES |
| **Sanitized Input** | Review SQL/DB queries | All variables parameterized/escaped | YES |
| **CORS Policy** | Scan configuration | Specific allowed origins (no wildcard `*`) | YES |

---

## Exit Decision Model

- **PASS:** 0 secrets, 0 Critical CVEs, inputs parameterized, auth validated. Quality score = 100.
- **PASS WITH WARNINGS:** Zero Critical CVEs but Medium/Low vulnerabilities exist with approved mitigation schedule. Score = 80-99.
- **FAIL:** committed secret, Critical CVE present, unparameterized database query, or unprotected route. Score < 80.

---

## Escalation Paths

- **Secret Committed:** Revoke the credential immediately, rotate the token, rewrite git history, and fail the gate.
- **Rules Conflict:** If security constraints break functional requirements, escalate to `chief-architect` to design secure mitigation.

# Standard: Security

> **Tier:** Cross-cutting — referenced by api_design, data_engineering, ai_ml
> **Owner:** Security Lead / Tech Lead | **Reviewer:** `security-reviewer`
> **Consumers:** All agents (security-touching tasks) | **Max:** ~1500 tokens
> **Cross-refs:** `standards/code_quality.md` · `standards/api_design.md` · `standards/data_engineering.md` · `checklists/security_review.md`

---

## Purpose

Ensure that security is a design constraint — applied before implementation, not bolted on after. Protect system integrity, user data, and infrastructure against both external threats and insider error.

## Scope

**Governs:** Authentication, authorization, input validation, secret management, dependency security, data protection, infrastructure hardening, API security.
**Does NOT govern:** Business logic correctness (→ `standards/testing.md`), API design conventions (→ `standards/api_design.md`), data schema (→ `standards/data_engineering.md`).

---

## Guiding Principles

1. **Least privilege.** Every component gets the minimum permissions it needs — nothing more.
2. **Defense in depth.** Security at every layer; assume the layer above you has already failed.
3. **Never trust input.** Validate and sanitize all input at every system boundary.
4. **Secrets never in code.** No secrets in source files, logs, or commit history — ever.
5. **Fail securely.** On error, deny access. Never fail open.
6. **Assume breach.** Design systems that limit blast radius when (not if) compromise occurs.
7. **Security is a PR requirement.** Security reviews are not a post-ship event.

---

## Threat Model Categories

| Category | Threats | Required Mitigations |
|---------|---------|---------------------|
| Authentication | Credential theft, brute force, session hijacking | MFA, secure tokens, session expiry |
| Authorization | Privilege escalation, IDOR, broken access control | RBAC/ABAC, per-request permission checks |
| Input | SQL injection, XSS, command injection, path traversal | Parameterized queries, input validation, output encoding |
| Secrets | Hardcoded credentials, leaked env vars, insecure storage | Vault/secrets manager, env var injection, scan in CI |
| Dependencies | Known CVEs, supply chain attacks | Dependency scanning in CI, lockfile pinning |
| Data | Unauthorized access, data leakage, insufficient encryption | Encryption at rest and in transit, access logs |
| Infrastructure | Exposed services, overprivileged roles, unpatched systems | Network policies, IAM least privilege, patch policy |

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Secrets management | No hardcoded secrets | Env vars + .gitignore | Secrets vault (Vault/SOPS) | Vault + rotation + audit log |
| Input validation | Basic type checking | Validation on all inputs | Schema validation + sanitization | + Fuzzing in CI |
| Authentication | Basic auth implemented | JWT/OAuth2 | MFA enforced | MFA + hardware keys + SSO |
| Authorization | Role check exists | RBAC implemented | Per-endpoint permission check | ABAC + audit trail |
| Dependency scanning | None | Manual quarterly | Automated in CI | Automated + SLA for CVE response |
| Threat model | None | Key threats identified | Documented threat model | Formal threat model + penetration test |
| Encryption | HTTPS enforced | TLS 1.2+ | TLS 1.3 + at-rest encryption | E2E encryption + key management |
| Security review | None | Internal review | External review | Third-party audit + bug bounty |

---

## Best Practices

- **Parameterize every database query.** Never concatenate user input into SQL.
- **Validate at the boundary.** Input entering the system must be validated on the way in; before any processing.
- **Log security events.** All auth failures, permission denials, and suspicious patterns must be logged with context.
- **Pin dependency versions.** Floating dependencies allow silent supply chain attacks.
- **Rotate secrets on suspicion.** Never wait to confirm a compromise — rotate immediately.
- **Audit privileged operations.** Every admin action, permission change, and data export must be logged.
- **Scan before merge.** Automated secret detection and dependency scanning runs on every PR.
- **Principle of least privilege for services.** Database users have only the permissions their service needs.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Hardcoded credentials | Committed to version history; permanent exposure |
| Auth checks only at the route level | Internal service calls bypass checks |
| Catching and logging exceptions with secret values | Secrets leak into log aggregators |
| Using MD5 or SHA1 for passwords | Trivially reversible with GPU-based attacks |
| Storing secrets in environment variables in production | Process memory exposure; env var leakage |
| Trusting client-supplied user IDs | Allows IDOR (Insecure Direct Object Reference) |
| Disabling TLS verification in production | Defeats transport security entirely |
| Security "after launch" | Retrofit is 10× harder than design-time |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Secrets in git | Developer commits .env or config | Secret scanning in CI (pre-commit hooks) | Rotate all exposed secrets; rewrite git history |
| Authorization bypass | Permission checks added to routes but not service layer | Security review; penetration test | Add checks at all layers; full audit |
| Dependency CVE | No automated scanning | Dependency scanner alert | Upgrade affected package; test regression |
| Session fixation | Session token not rotated on login | Security code review | Regenerate token on every privilege change |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | No hardcoded secrets · Input validation exists · HTTPS enforced |
| Recommended | + RBAC implemented · Dependency scanner active · All auth failures logged |
| Production | + Threat model documented · TLS 1.3 · Secrets vault · External security review |
| Flagship | + Penetration test passed · Bug bounty active · Formal compliance audit · CVE SLA |

---

## Reviewer Questions

```
SECURITY REVIEW CHECKLIST
□ Are there any hardcoded credentials, tokens, or API keys in the code?
□ Is input validated at every system boundary before processing?
□ Are all database queries parameterized (no string concatenation)?
□ Are authentication and authorization checked per-request, not just at the route?
□ Is the dependency scanner configured and finding no unresolved CVEs?
□ Are secrets stored in a vault or secrets manager, not environment variables?
□ Are privileged operations logged with sufficient context?
□ Is TLS enforced on all external connections?
□ Are session tokens rotated on authentication state changes?
□ Has a threat model been documented for this component?
```

---

## Completion Criteria

- [ ] No secrets in source code or version history
- [ ] All acceptance criteria for the project's quality level are met
- [ ] Dependency scanner shows no unresolved critical or high CVEs
- [ ] Security review checklist complete
- [ ] `security-reviewer` has reviewed and approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| API authentication design | `standards/api_design.md` |
| Data handling and encryption | `standards/data_engineering.md` |
| Security checklist (verification) | `checklists/security_review.md` |
| Security incident response | `workflows/incident_response.md` |

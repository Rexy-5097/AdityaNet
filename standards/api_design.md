# Standard: API Design

> **Tier:** Component — applies to services that expose APIs
> **Owner:** Tech Lead | **Reviewer:** `security-reviewer` + `docs-reviewer`
> **Consumers:** All agents (API-touching tasks) | **Max:** ~1500 tokens
> **Cross-refs:** `standards/code_quality.md` · `standards/security.md` · `standards/documentation.md` · `standards/testing.md`

---

## Purpose

Ensure that APIs are consistent, versioned, secure, and useful — as contracts that can be depended on by consumers today and maintained without breakage tomorrow.

## Scope

**Governs:** REST API design, GraphQL schema design, gRPC service design, API versioning, error response format, rate limiting, authentication design.
**Does NOT govern:** Authentication implementation security details (→ `standards/security.md`), API documentation format (→ `standards/documentation.md`), backend data models (→ `standards/data_engineering.md`).

---

## Guiding Principles

1. **APIs are contracts.** Breaking changes require versioning — not "we'll notify consumers."
2. **Design first, implement second.** Write the OpenAPI/schema spec before the code.
3. **Fail fast and clearly.** A bad request should return a specific error immediately — not silently succeed.
4. **Idempotency is safety.** Design mutations to be safely retried.
5. **Be consistent.** Inconsistent naming, casing, or error formats make APIs unpredictable.
6. **Least surface.** Every endpoint is a maintenance obligation. Expose only what is needed.
7. **Version explicitly.** URL path versioning (`/api/v1/`) is the simplest convention that prevents confusion.

---

## API Contract Obligations

| Obligation | Description | Enforcement |
|-----------|------------|------------|
| Backward compatibility | Adding fields is allowed; removing or renaming is a breaking change | API reviewer gate |
| Versioning | Breaking changes → new major version (`v1` → `v2`) | Pre-release gate |
| Error format consistency | All errors use the same response schema | Linting / tests |
| Deprecation notice | Deprecated endpoints announced N days before removal | Changelog + header |
| Response schema stability | Existing fields do not change type | Schema validation in tests |

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Versioning | No versioning | URL version prefix | + Deprecation process | + Long-term support commitments |
| Error format | Ad-hoc | Consistent schema | RFC 7807 (Problem Details) | RFC 7807 + correlation IDs |
| Auth | API key | JWT / OAuth2 | OAuth2 + scopes + PKCE | + Token rotation + audit trail |
| Documentation | None | Endpoints documented | Full OpenAPI spec | OpenAPI spec + example collection + SDK |
| Rate limiting | None | Basic rate limits | Per-route rate limits | Tiered limits + circuit breakers |
| Idempotency | None | Idempotency keys on mutations | Enforced + tested | Enforced + client retry guidance |
| Input validation | Type checking | Schema validation | Schema + sanitization | + Fuzzing in CI |
| Testing | Manual | Happy path automated | Contract tests | Contract tests + consumer-driven |

---

## Standard Error Response Format (RFC 7807)

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "User with ID 'abc123' does not exist.",
  "instance": "/api/v1/users/abc123",
  "correlation_id": "req-xyz-789"
}
```

Use this format at all quality levels ≥ Recommended.

---

## HTTP Status Code Policy

| Status | Use For |
|--------|---------|
| 200 | Successful GET, PUT (with body) |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE or PUT (no body) |
| 400 | Client error — bad request, validation failure |
| 401 | Authentication required or failed |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict (duplicate, state conflict) |
| 422 | Validation passed but semantically invalid |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error (never reveal internals) |

---

## Best Practices

- **Nouns in paths, verbs in HTTP methods.** `GET /users/{id}`, not `GET /getUser/{id}`.
- **Plural resource names.** `/users`, `/orders`, `/experiments`.
- **Use query parameters for filtering, sorting, pagination.** Never encode filter logic in path segments.
- **Paginate all list endpoints.** Return `next`, `previous`, and `total` where applicable.
- **Never expose internal IDs in responses.** Use opaque tokens or UUIDs.
- **Log all 5xx errors with full context** (request ID, user ID, stack trace — never expose to client).
- **Design for retry.** Document which endpoints are idempotent; implement idempotency keys on POST.
- **CORS policy is explicit.** Never use wildcard `*` in production.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Changing field names without versioning | Silently breaks all existing consumers |
| 200 OK with error in body | Clients cannot detect failure without reading body |
| Raw database errors in API response | Leaks schema; enables SQL injection reconnaissance |
| Inconsistent casing (`userId` vs `user_id`) | Consumers need special-case handling; error-prone |
| Endpoints that do multiple unrelated things | Hard to document, test, and authorize separately |
| Removing endpoints without deprecation period | Breaking change with no warning |
| No rate limiting | Enables DoS; abusive clients degrade service for all |
| Boolean "success" field instead of status codes | Bypasses HTTP contract; confuses clients |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Accidental breaking change | Field removed/renamed without version bump | Contract tests fail in CI | Version the API; communicate to consumers |
| Error format inconsistency | Different devs implement error handling separately | Code review; API testing | Centralize error handler; update existing endpoints |
| Missing rate limits | Rate limiting "added later" | Load testing reveals DoS surface | Add rate limiting at API gateway level |
| Auth bypass | Authorization at route level only | Security review | Add per-resource authorization checks |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | API responds correctly · No raw errors exposed to client · Basic auth implemented |
| Recommended | + URL versioning · Consistent error format · All endpoints documented |
| Production | + Full OpenAPI spec · Rate limiting · Contract tests · OAuth2 · RFC 7807 errors |
| Flagship | + Consumer-driven contract tests · SDK generated · Deprecation policy · LTS commitment |

---

## Reviewer Questions

```
API DESIGN REVIEW CHECKLIST
□ Does every breaking change increment the API version?
□ Do all error responses use the standard error schema?
□ Are HTTP status codes used correctly (no 200 for errors)?
□ Are all inputs validated at the API boundary before processing?
□ Is authentication required and working on all protected endpoints?
□ Are authorization checks performed per-resource, not just per-route?
□ Is rate limiting configured on all public endpoints?
□ Are all list endpoints paginated?
□ Does the OpenAPI/schema specification match the implementation?
□ Are idempotency semantics documented for all mutation endpoints?
```

---

## Completion Criteria

- [ ] All acceptance criteria for the project's quality level are met
- [ ] No breaking changes introduced without version bump
- [ ] All endpoints follow the standard error format
- [ ] Security review complete (`standards/security.md`)
- [ ] Documentation complete (`standards/documentation.md`)
- [ ] `security-reviewer` and `docs-reviewer` have approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Authentication implementation | `standards/security.md` |
| API documentation requirements | `standards/documentation.md` |
| Input validation | `standards/security.md` §Input |
| Testing contract coverage | `standards/testing.md` |

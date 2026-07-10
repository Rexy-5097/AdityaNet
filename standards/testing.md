# Standard: Testing

> **Tier:** Foundation — applies to all projects and components
> **Owner:** QA Lead / Tech Lead | **Reviewer:** `qa-reviewer`
> **Consumers:** All agents (QA gate tasks) | **Max:** ~1400 tokens
> **Cross-refs:** `standards/code_quality.md` · `metrics/quality.md` · `checklists/qa.md`

---

## Purpose

Ensure that software behaves correctly under both expected and unexpected conditions, that regressions are caught automatically, and that tests serve as executable documentation.

## Scope

**Governs:** Unit tests, integration tests, system tests, regression tests, performance tests, research validation tests.
**Does NOT govern:** Test infrastructure (→ `standards/code_quality.md`), QA process (→ `checklists/qa.md`), research methodology (→ `standards/research.md`).

---

## Guiding Principles

1. **Test behavior, not implementation.** Tests should survive refactoring.
2. **Every bug gets a regression test.** A bug without a test will return.
3. **Fast tests, slow tests, separated.** Unit tests run in seconds; integration tests run in minutes. Never mix.
4. **Tests are documentation.** A test communicates what the system should do.
5. **Flaky tests are bugs.** A test that sometimes passes and sometimes fails is worse than no test.
6. **Test the boundaries.** Happy paths prove it works; edge cases prove it's safe.
7. **Test coverage is a floor, not a ceiling.** High coverage with poor assertions is worthless.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Unit test coverage | Core happy paths | ≥ 60% line coverage | ≥ 80% line coverage | ≥ 90% + branch coverage |
| Integration tests | Minimal | Key workflows covered | All integration points | All + contract tests |
| Regression tests | None required | Per major bug | Per bug (all severity) | Per bug + automated patrol |
| Property / fuzz tests | None | Encouraged | Key functions | Critical functions required |
| Performance tests | None | Manual benchmarks | Automated in CI | Budget enforcement in CI |
| Test execution time | No limit | Unit < 60s | Unit < 30s | Unit < 10s |
| Flaky test tolerance | Tolerated (document) | Zero tolerance | Zero tolerance | Zero tolerance + patrol |
| Test documentation | None | Test names are self-documenting | + docstrings on complex tests | + test design document |

---

## Test Taxonomy

| Type | Scope | Speed | Isolation | Runs When |
|------|-------|-------|-----------|---------|
| Unit | Single function/class | < 1ms each | Full mocking | Every commit |
| Integration | Multiple components | < 5s each | Partial mocking | Every PR |
| System / E2E | Full stack | Minutes | None | Pre-release |
| Performance | Latency/throughput | Varies | Staging environment | Pre-release |
| Regression | Specific bug scenario | Matches bug type | Matches bug type | Every commit |

---

## Best Practices

- **Arrange-Act-Assert.** Structure every test: set up state → execute → assert outcome.
- **One assertion per test** (or one logical concept). Multiple failures mask each other.
- **Name tests as statements:** `test_returns_404_when_user_not_found`, not `test_user`.
- **Use factory functions or fixtures** for test data; avoid magic values inline.
- **Prefer deterministic data.** Randomized test data hides reproduction steps.
- **Mock at the boundary**, not deep inside. Mock external APIs and databases; not internal functions.
- **Run the full test suite before every PR merge** — never skip on "it should be fine."
- **Coverage ≠ quality.** Assert meaningful expectations, not just that code runs.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Testing implementation (not behavior) | Tests break on refactor; discourages improvement |
| Shared mutable state between tests | One test contaminates another; order dependency |
| Sleeping (`time.sleep`) in tests | Flaky by design; use event-driven waits or mocks |
| Testing third-party libraries | Maintenance cost with no project benefit |
| Giant test functions | Hard to read; impossible to isolate failure |
| Commented-out tests | Broken tests hidden from CI; delete or fix |
| 100% coverage as the goal | Leads to assertion-free tests that prove nothing |
| Skipping integration tests "for speed" | Bugs in component interaction reach production |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Coverage collapse | Tests deleted or skipped under deadline | CI coverage gate | Restore coverage; add regression tests |
| Test suite slowdown | Integration tests in unit test suite | CI timing metrics | Separate suites; run appropriately |
| Flaky tests ignored | No policy for flaky test resolution | CI flakiness tracking | Quarantine + fix within sprint |
| Testing only happy paths | Developers write tests for code they wrote | Code review checklist | Add boundary test requirement to PR checklist |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | CI passes · Core happy paths tested · No failing tests |
| Recommended | + ≥ 60% coverage · Integration tests exist · Test names are self-documenting |
| Production | + ≥ 80% coverage · All bugs have regression tests · Zero flaky tests · Perf tests in CI |
| Flagship | + ≥ 90% coverage · Branch coverage tracked · Property tests on critical functions · Test design document |

---

## Reviewer Questions

```
TESTING REVIEW CHECKLIST
□ Does test coverage meet the project's quality level target?
□ Are tests named as behavioral statements (not test_function_name)?
□ Is each test independent — no shared mutable state?
□ Are unit tests separated from integration tests?
□ Does every fixed bug have a corresponding regression test?
□ Are time.sleep() calls absent from tests?
□ Are assertions meaningful (not just asserting the code ran)?
□ Do tests cover boundary conditions and error paths, not just happy paths?
□ Does the full test suite run in under the time limit for this quality level?
□ Are there any commented-out or skipped tests? If so, why?
```

---

## Completion Criteria

- [ ] Test suite passes with zero failures and zero errors
- [ ] Coverage meets the target for the project's quality level
- [ ] All tests are categorized by type (unit / integration / system / regression)
- [ ] No flaky tests in the suite
- [ ] Every bug fixed in this cycle has a regression test
- [ ] Test execution time is within the limit for this quality level

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Code testability | `standards/code_quality.md` |
| Research validation | `standards/research.md` |
| QA process | `checklists/qa.md` |
| Performance benchmarks | `metrics/performance.md` |
| Quality metrics | `metrics/quality.md` |

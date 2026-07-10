# Metrics: Quality

> **Owner:** Tech Lead | **Consumers:** `qa-reviewer` · All engineers
> **Update Frequency:** Per sprint · Trended over time
> **Max Size:** ~800 tokens | **Cross-refs:** `standards/code_quality.md` · `standards/testing.md` · `standards/documentation.md` · `metrics/performance.md`

---

## Purpose

Define measurable quality targets for engineering hygiene. Quality metrics prevent subjective opinions about code health from replacing objective measurement.

**Rule:** Measure trends, not just snapshots. A metric that is worsening week-over-week is a signal regardless of its absolute value.

---

## Test Coverage

| Metric | Definition | Minimum | Recommended | Production | Flagship | Method |
|--------|-----------|---------|-------------|------------|---------|--------|
| Line coverage | % of lines executed by tests | > 40% | > 60% | > 80% | > 90% | pytest-cov / Istanbul |
| Branch coverage | % of branches taken by tests | > 30% | > 50% | > 70% | > 85% | pytest-cov / Istanbul |
| Mutation score | % of injected bugs caught by tests | N/A | N/A | > 60% | > 80% | mutmut / Stryker |
| Integration coverage | % of API endpoints with integration tests | > 50% | > 80% | 100% | 100% | Manual audit |

---

## Code Complexity

| Metric | Definition | Maximum Acceptable | Recommended | Method |
|--------|-----------|-------------------|-------------|--------|
| Cyclomatic complexity | Number of independent paths | 15 | ≤ 10 (≤ 7 for production) | radon / SonarQube |
| Cognitive complexity | Human-perceived difficulty | 20 | ≤ 15 | SonarQube |
| Function length | Lines of code per function | 100 | ≤ 50 (≤ 30 for production) | radon / cloc |
| File length | Lines of code per file | 500 | ≤ 300 | cloc |
| Coupling (afferent) | Number of modules that import this one | N/A | Track trend | Dependency analysis |

---

## Bug Metrics

| Metric | Definition | Minimum | Recommended | Production | Method |
|--------|-----------|---------|-------------|------------|--------|
| Defect escape rate | Bugs found in production / total bugs found | < 30% | < 15% | < 5% | Issue tracker |
| Bug regression rate | % of closed bugs that reopen | < 20% | < 10% | < 5% | Issue tracker |
| Mean time to detect (MTTD) | Time from introduction to detection | < 2 sprints | < 1 sprint | < 24h | Issue tracker + monitoring |
| Mean time to resolve (MTTR) | Time from detection to fix deployed | < 2 weeks | < 1 week | < 24h (critical) | Issue tracker |
| Open critical bugs | Count of critical-severity open bugs | ≤ 5 | 0 | 0 | Issue tracker |

---

## Technical Debt

| Metric | Definition | Target | Method | Frequency |
|--------|-----------|--------|--------|----------|
| Debt items logged | Items in `context/state.md` debt table | 100% of known items logged | Manual + CI audit | Every sprint |
| Debt with SLA | % of logged debt items with resolution timeline | > 50% | > 80% | Manual | Every sprint |
| Debt resolved per sprint | Debt items closed this sprint | ≥ 1 per sprint | ≥ 2 per sprint | Issue tracker | Per sprint |
| Tech debt ratio | (Debt remediation time) / (feature dev time) | < 40% | < 20% | Estimation tool | Quarterly |

---

## Documentation Coverage

| Metric | Definition | Minimum | Recommended | Production | Method |
|--------|-----------|---------|-------------|------------|--------|
| Public API coverage | % of public API methods with docstrings | > 50% | > 80% | 100% | pydoc-markdown / TypeDoc |
| README currency | Days since last README update | < 60 days | < 30 days | Updated per release | Git log |
| ADR coverage | % of significant decisions with ADR | > 50% | > 80% | 100% | Manual audit |
| Stale documentation | Doc pages not updated in > 6 months | < 30% | < 10% | 0% | Docs tool / git log |

---

## Maintainability Index

| Metric | Definition | Target | Method |
|--------|-----------|--------|--------|
| Maintainability Index (MI) | Composite: volume + complexity + lines | > 65 | radon |
| Code churn rate | % of lines changed per sprint | Track trend | git diff stats |
| Duplicate code | % of codebase that is duplicated | < 5% | SonarQube / PMD |
| Dependency staleness | % of dependencies more than 2 major versions behind | < 20% | pip-audit / dependabot |

---

## Quality Gate Summary

| Gate | Triggers When | Metrics Checked |
|------|-------------|----------------|
| Per-PR | Every pull request | Linting · coverage · complexity |
| Feature complete | Feature marked done | All test coverage · doc coverage · open bugs |
| Pre-release | Release branch created | All metrics · bug regression rate · debt logged |
| Quarterly | Every 3 months | Trend analysis · debt ratio · dependency staleness |

---

## Project Targets (Fill In Per Project)

| Metric | Project Target | Set By | Date |
|--------|--------------|--------|------|
| Line coverage | [%] | | |
| Cyclomatic complexity max | | | |
| Defect escape rate | [%] | | |
| MTTR (critical) | [hours] | | |

---

*Trend direction matters as much as absolute value. A metric worsening for 3 sprints is a signal.*

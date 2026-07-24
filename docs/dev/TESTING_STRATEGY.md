# Testing strategy

## Gates

Four were specified. **Three exist**, because a gate with zero tests is not a gate —
it is a slow no-op that trains people to ignore CI.

| Gate | Command | Contents |
|---|---|---|
| `verify` | `pnpm verify` | Token drift · `astro check` · `tsc --noEmit` · ESLint (incl. architecture boundaries) |
| `test` | `pnpm test` | Vitest unit tests |
| `budget` | `pnpm budget` | Contrast floors · route JS budgets · dist hygiene |
| `e2e` | *arrives in Sprint 6* | Persona journeys, once a journey exists |

## Coverage philosophy

Coverage follows **consequence**, not uniformity. A blanket percentage across the
codebase would be cargo-culted.

| Area | Target | Why |
|---|---|---|
| `scripts/lib`, `src/lib/science` | **100% branch** | Pure functions where a wrong branch produces a *plausible but incorrect* result — a silent scientific error |
| Everything else | No numeric target | Errors are visible; tests follow behaviour, not lines |

Sprint 0's only unit tests cover WCAG contrast maths — 8 tests. They exist because if
that maths is wrong, the accessibility gate passes silently and every contrast claim
in the specification becomes false.

## What is deliberately not tested

**GPU pixel output.** Brittle and driver-dependent. Instead the *data → uniform*
mapping is unit-tested and the deterministic Tier-0 poster is visually regressed —
testing the property that matters rather than the rendering that varies.

**Component markup snapshots.** They break on every legitimate refactor, train
reflexive `-u`, and assert nothing about behaviour.

## Planned, by sprint

| Sprint | Addition |
|---|---|
| 1 | **Evidence consistency** — parse built HTML, re-read source artifacts, assert every rendered number matches. Error budget: zero, permanently |
| 1 | Negative tests: corrupt an artifact → CI fails; hand-type a number → lint fails; stale JSON pointer → codegen fails |
| 4 | Assert no model metric renders without a confidence interval |
| 5b | Shader compilation in headless GL; determinism; domain audit |
| 6 | E2E persona journeys; `e2e` gate created |
| 8 | Visual regression (10 baselines), axe, Lighthouse CI |

# Standard: Code Quality

> **Tier:** Foundation — applies to all projects and components
> **Owner:** Chief Architect | **Reviewer:** Any reviewer agent
> **Consumers:** All agents | **Max:** ~1400 tokens
> **Cross-refs:** `standards/testing.md` · `standards/documentation.md` · `metrics/quality.md`

---

## Purpose

Define what "well-written code" means in this system — consistently, measurably, and without ambiguity.

## Scope

**Governs:** All source code written for or added to the project.
**Does NOT govern:** Test code style (→ `standards/testing.md`), API contracts (→ `standards/api_design.md`), UI logic (→ `standards/ui_ux.md`).

---

## Guiding Principles

1. **Readable over clever.** Code is read 10× more than written. Optimize for the reader.
2. **Explicit over implicit.** Never make the reader guess intent.
3. **Single responsibility.** Functions do one thing. Modules own one domain.
4. **Fail loudly.** Raise errors; never silently swallow them.
5. **Testable by design.** Untestable code is a design failure, not a testing failure.
6. **No premature abstraction.** Abstractions earn their existence through proven reuse.
7. **Debt is intentional.** Every shortcut is logged; none is hidden.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Linting | No errors | Enforced in CI | Enforced + zero warnings | Enforced + custom rules |
| Function length | ≤ 100 lines | ≤ 50 lines | ≤ 30 lines | ≤ 20 lines |
| Cyclomatic complexity | ≤ 15 | ≤ 10 | ≤ 7 | ≤ 5 |
| Nesting depth | ≤ 5 | ≤ 4 | ≤ 3 | ≤ 3 |
| Magic numbers | Allowed | Named constants | Zero magic numbers | Zero + justified |
| Dead code | Removed before merge | Removed before merge | CI gate | CI gate + audit |
| Naming | Descriptive | Consistent + descriptive | Reviewed by peers | Reviewed + glossary |
| Error handling | Basic try/except | Typed exceptions | Exhaustive + logged | Exhaustive + traced |
| Technical debt | Allowed undocumented | Logged in state.md | Logged + scheduled | Logged + SLA |

---

## Best Practices

- **Name variables for what they hold**, not how they're used (`user_email`, not `data`).
- **Name functions for what they do** — verbs for actions, nouns for queries (`fetch_user_record`, `is_valid_token`).
- **Guard clauses first.** Handle error cases at the top; happy path runs straight through.
- **No comments for what.** Comment WHY, not what. The code shows what.
- **Delete unused code.** Version control is the history; dead code is a hazard.
- **Prefer composition over inheritance.** Inheritance couples; composition adapts.
- **Limit function arguments.** > 4 arguments → consider a data class or configuration object.
- **Consistent error types.** One error hierarchy per module; don't mix exception types.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Functions that do multiple things | Impossible to test in isolation; hard to name |
| Boolean flags as function arguments | Creates hidden branching; split into two functions |
| Returning `None` on error | Caller must always null-check; use typed exceptions |
| Strings as error codes | Untyped; breaks on typos; use enums or typed exceptions |
| Mutable default arguments (Python) | Shared state across calls; causes subtle bugs |
| God objects / god functions | Single point of failure; impossible to test |
| Premature optimization | Obscures intent; fix only after profiling proves the need |
| Copy-paste code | Bugs fix in one place, live in 10; extract a function |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Complexity creep | Features added to existing functions | Complexity metrics in CI | Refactor before next feature |
| Silent failures | Exceptions caught and ignored | Code review; log scanning | Add explicit error handling + logging |
| Naming entropy | No glossary; each dev uses different terms | Review findings accumulate | Establish glossary in `context/memory.md` |
| Debt accumulation | No logging policy; shortcuts undocumented | `context/state.md` debt table grows | Schedule debt sprint; log immediately when taken |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | CI passes · No syntax errors · No linting errors · Dead code removed |
| Recommended | + Complexity ≤ 10 · Named constants · Typed exceptions · Descriptive naming |
| Production | + Complexity ≤ 7 · Functions ≤ 30 lines · Zero undocumented shortcuts · Peer reviewed |
| Flagship | + Complexity ≤ 5 · Custom linting rules · All debt logged with SLA · Glossary current |

---

## Reviewer Questions

```
CODE QUALITY REVIEW CHECKLIST
□ Does every function have a single, nameable responsibility?
□ Is cyclomatic complexity within the target level?
□ Are all exceptions typed and handled explicitly?
□ Are there any magic numbers or unexplained constants?
□ Is there any dead code, commented-out blocks, or unused imports?
□ Are variable and function names self-documenting?
□ Is technical debt logged in context/state.md or artifacts/?
□ Does the code fail loudly (raises errors) rather than silently (returns None)?
□ Are there no function arguments > 4? If so, is there a data class?
□ Does the code pass linting with zero warnings?
```

---

## Completion Criteria

- [ ] All acceptance criteria for the project's quality level are met
- [ ] Linting passes in CI with zero violations
- [ ] All technical debt is logged
- [ ] No function violates the complexity or length limit for this level
- [ ] Code reviewed by at least one other engineer or reviewer agent

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Test code quality | `standards/testing.md` |
| Documentation standards | `standards/documentation.md` |
| API design rules | `standards/api_design.md` |
| Quality metrics | `metrics/quality.md` |

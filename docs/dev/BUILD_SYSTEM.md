# Build system

## Pipeline

```
tokens/*.json ──generate.ts──> src/generated/tokens.css ──┐
                                                          ├──astro build──> dist/
src/pages, src/layouts, src/styles ───────────────────────┘        │
                                                       postbuild.ts (strip OS metadata)
```

## Commands

| Command | Purpose |
|---|---|
| `pnpm generate` | Regenerate design tokens from `tokens/*.json` |
| `pnpm dev` | Astro dev server |
| `pnpm build` | Static build + output hygiene pass |
| `pnpm verify` | Token drift · `astro check` · `tsc` · ESLint |
| `pnpm test` | Vitest |
| `pnpm budget` | Contrast floors · route JS budgets · dist hygiene |

## Tooling artifacts

Five, each with a stated justification. The specification budgets four; the fifth
(`postbuild.ts`) is justified in its own file header.

| Artifact | Responsibility |
|---|---|
| `scripts/generate.ts` | Code generation. `--check` mode fails CI on drift |
| `scripts/check.ts` | Invariant and budget enforcement. Never mutates |
| `scripts/postbuild.ts` | Strips OS metadata from deployable output |
| `scripts/lib/contrast.ts` | WCAG maths. Extracted only because it has two consumers |
| ESLint custom rules | *None yet.* Boundaries are declarative config |

## Design tokens

`tokens/*.json` is the single source of truth. Tailwind v4 is CSS-first, so the
generated `@theme` block *is* both the CSS custom properties and the Tailwind scale —
there is no `tailwind.config.ts`. Generated output is committed and CI-verified, so a
reviewer sees the consequence of a token change, not merely its cause.

Three token tiers are specified; **tier 3 (component tokens) does not exist yet**
because no component needs one. It arrives with its first consumer.

## Why generated code is committed

Generation is deterministic and CI diffs it. A reader of the repository can see the
resolved values without running a toolchain, and a pull request shows the real effect
of a token edit.

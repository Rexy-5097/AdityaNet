# AdityaNet Web Platform

The web platform for AdityaNet — an independent research project over the public
Aditya-L1 X-ray archive.

> **AdityaNet is not affiliated with, endorsed by, or operated by ISRO or any space
> agency.** It is built on publicly available Aditya-L1 archive data from ISSDC.

## What this is

A static, read-only platform publishing a provenance-tracked canonical dataset derived
from SoLEXS and HEL1OS Level-1 products, the record of how that dataset was validated,
and an honest account of what can and cannot be concluded from it — including the
project's headline finding, which is negative: **machine learning provides no
operational benefit over a threshold detector for the evaluated tasks.**

## Quick start

```bash
pnpm install
pnpm generate     # design tokens -> src/generated/tokens.css
pnpm dev
```

## Commands

| Command | Purpose |
|---|---|
| `pnpm verify` | Token drift · `astro check` · `tsc --noEmit` · ESLint |
| `pnpm test` | Unit tests |
| `pnpm build` | Static build + output hygiene |
| `pnpm budget` | Contrast floors · route JS budgets · dist hygiene |

All three gates must pass before merge. There is no admin bypass, including for the
sole maintainer — a solo project with a bypass has no gates, only suggestions.

## Architecture in one paragraph

There is no runtime server. Every response is enumerable at build time, so the build
emits a plain directory hostable anywhere, indefinitely. Astro renders the shell and
the evidence surfaces at **0 KB of JavaScript**; React islands appear only where
interactivity is real. That is what makes a 450 KB immersive WebGL experience
affordable on one opt-in route — cheap pages pay for the expensive one.

## The two rules that shape the code

**Every number cites its source.** A developer cannot type a measured value into this
application. They write an artifact reference; code generation resolves it; a lint rule
rejects numeric literals in markup; and a test re-reads the original artifact from disk
and asserts the rendered string matches. That test's error budget is zero, permanently.

**Two rendering domains, enforced at build time.** Domain A (experience) may be
photorealistic and is watermarked *into the WebGL frame buffer* so the marker survives
screenshotting. Domain B (scientific) requires every visual encoding to trace to a
committed artifact. The two directories cannot import each other.

## Documentation

| | |
|---|---|
| [Product specification](../docs/web/PRODUCT_SPECIFICATION.md) | Frozen governing document |
| [Experience architecture](../docs/web/SPEC_AMENDMENT_02_EXPERIENCE.md) | Sections 18–19, supersedes on the presentation layer |
| [Architecture decisions](../docs/adr/) | ADRs with evidence |
| [Build system](../docs/dev/BUILD_SYSTEM.md) · [Testing](../docs/dev/TESTING_STRATEGY.md) | Developer docs |
| [Performance](../docs/performance/) | Measured baselines |
| [Engineering notes](../docs/blog/) | Write-ups of interesting problems |

## Project status

**Sprint 0 complete.** Foundation only: no product surfaces yet. The placeholder page
carries no measured statistics by design — the mechanism that makes a number safe to
display is built in Sprint 1, and until it exists, "every number cites its source" is
enforced by there being no numbers.

## Licence

MIT.

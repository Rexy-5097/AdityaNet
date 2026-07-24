# Architecture Decision Records

Each ADR records one decision, the evidence behind it, and what it costs. A decision
reversed later is not deleted — it is marked `Superseded` and the replacement links
back to it, because the reasoning that failed is more instructive than the one that held.

| # | Decision | Status |
|---|---|---|
| [0001](0001-no-runtime-server.md) | No runtime server; static generation | Accepted |
| [0002](0002-astro-over-nextjs.md) | Astro over Next.js | Accepted |
| [0003](0003-two-rendering-domains.md) | Two rendering domains, build-enforced | Accepted |
| [0004](0004-generated-design-tokens.md) | Design tokens as generated artifacts | Accepted |
| [0005](0005-threejs-budget.md) | three.js accepted at measured cost | Accepted |

**Format.** Context / Options considered / Decision / Consequences / Evidence.
Numbers in ADRs are measurements, never estimates. If a number is an estimate it says so.

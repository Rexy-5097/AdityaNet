# ADR-0002 — Astro over Next.js

**Status:** Accepted · 2026-07-23 · **Supersedes the Next.js choice in Parts 1–3**

## Context

Sprint 0 was first implemented on Next.js 16 App Router with `output: 'export'`. The
budget gate then measured the shipped payload for a page containing **zero interactive
components**.

## Evidence

| Framework | Initial JS (zero client components) | Inline scripts |
|---|---|---|
| Next.js 16 App Router | **184.2 KB gz** (9 chunks) | Yes — RSC payload |
| Astro 5/7 | **0 bytes** (no `<script>` tag) | None |

Verified as production React (no dev-only warning strings present); the largest chunk
is `react-dom` at 71 KB gz containing `hydrateRoot`. The App Router always hydrates,
so this is a floor, not a configuration mistake.

**Every route budget in the specification sat below that floor** — `/validation` at
60 KB, `/build` at 80 KB, `/findings` at 160 KB. The budgets were not ambitious; they
were unachievable.

## Options

| Option | Assessment |
|---|---|
| Raise all budgets to ~185 KB | Makes §11.6 fiction. Forfeits the argument that the credibility surface should be the fastest page |
| **Astro + React islands** | Evidence surfaces cost ~0; the immersive island pays for itself |
| Vite SPA | Loses HTML-first delivery, citability, and no-JS reachability |

## Decision

Astro for the shell and evidence surfaces; React islands where interactivity is real.

## Consequences

**Gained.** Evidence routes at 0 KB — which is what makes a 450 KB immersive island on
`/explore` affordable. A strict `script-src 'self'` CSP became achievable, because
removing the RSC payload removed the inline scripts that had forced `'unsafe-inline'`.
Astro's mandatory `client:*` directive enforces the client-boundary rule as a language
feature rather than a custom lint rule.

**Lost.** No WebGL context persisting across route changes. Accepted: the immersive
experience lives at a single route (`/explore`), so cross-route persistence is not
required — and a cinematic transition between two reading surfaces would have been
motion without meaning.

## Lesson recorded

The framework was chosen by convention and validated by measurement only afterwards.
The measurement should have come first. This is why `scripts/check.ts` measures
transfer size from built HTML rather than trusting any bundler's reported total.

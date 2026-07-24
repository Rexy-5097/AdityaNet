# ADR-0004 — Design tokens as generated artifacts

**Status:** Accepted · 2026-07-23

## Context

Token values must reach three consumers: CSS custom properties, the Tailwind scale,
and build-time validation. Hand-syncing them is a guaranteed drift source.

## Options

| Option | Assessment |
|---|---|
| Hand-written CSS + `tailwind.config.ts` | Two sources of truth that silently diverge |
| Tailwind v3 config as the source | Couples design tokens to one framework's config format |
| **JSON source → generated CSS** | One source; Tailwind v4 reads `@theme` directly |

## Decision

`tokens/*.json` is the source of truth. `scripts/generate.ts` emits
`src/generated/tokens.css`, whose `@theme` block is *simultaneously* the CSS custom
properties and the Tailwind configuration. There is deliberately no `tailwind.config.ts`.

`generate --check` regenerates in memory and diffs against disk; CI fails on drift, so
a hand-edited generated file cannot land.

## Consequences

**Gained.** One artifact instead of two. Token resolution throws on an unknown
primitive, so a typo fails the build rather than emitting an empty custom property that
would render transparent and pass review.

**Cost.** A build step between editing a colour and seeing it. Acceptable: `pnpm generate`
runs in under 100 ms.

**Deferred.** `generated/tokens.ts` is specified but not emitted — nothing consumes it
yet, and dead generated code is worse than a missing convenience. It ships with its
first consumer.

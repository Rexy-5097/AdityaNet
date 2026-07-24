# PERF-0000 — Sprint 0 baseline

**Date:** 2026-07-23 · **Commit:** Sprint 0 · **Machine:** Apple Silicon, Node 25.5.0, pnpm 10.28.2

All figures are gzipped transfer size measured from built HTML by
`scripts/check.ts`, which parses `<script src>` and sums the referenced assets.
Bundler-reported totals are deliberately not used: they over-count chunks no route
loads, and this project migrated frameworks precisely because a reported number was
taken on faith.

## 1. Framework selection

| Framework | Initial JS (zero interactive components) | Scripts | Inline scripts |
|---|---|---|---|
| Next.js 16 App Router (`output: 'export'`) | **184.2 KB gz** | 9 | Yes (RSC payload) |
| **Astro 7** | **0.0 KB gz** | 0 | None |

Next chunk breakdown: 71.0 / 40.5 / 39.5 / 12.9 / 10.6 / 6.1 / 4.2 / 2.5 / 1.5 KB gz.
The 71 KB chunk is `react-dom` (`hydrateRoot`, `createRoot`). Confirmed production
build — no dev-only React warning strings present. → ADR-0002.

## 2. Experience layer (spike, not shipped)

| Configuration | Size |
|---|---|
| three + R3F + drei + postprocessing + React | **314.17 KB gz** |
| three + R3F + React only | **292.57 KB gz** |
| Effects stack delta | **21.6 KB** |

Estimate was 220–280 KB. **Wrong, low.** three.js core ~245 KB gz is the floor.
The pre-committed "drop postprocessing" fallback is void — 7% saved for the whole
effects pipeline. → ADR-0005.

## 3. Shipped route budgets

| Route | JS (gz) | Budget | Headroom |
|---|---|---|---|
| `/` | **0.0 KB** | 15 KB | 100% |

Total transfer for `/`: **4.9 KB gz** (HTML 0.9 KB + CSS 4.0 KB), plus fonts fetched
on demand by `unicode-range`.

## 4. Build

| Metric | Value |
|---|---|
| Clean build (Astro, 1 route) | **~5 s wall**, 396 ms reported |
| Clean build (Next, 2 routes, for comparison) | ~4 s wall, 11 s first run |
| Pages emitted | 1 |

**Marginal build-time-per-page is not yet measurable** with a single route. It is
required before Sprint 6 generates ~500 date pages; if extrapolated build time exceeds
10 minutes the specification's R5 fallback triggers (limit `generateStaticParams` to
scientifically notable dates, client-render the rest).

## 5. Accessibility — contrast

Measured by `scripts/check.ts` against `--color-base` `#0A0C0E`:

| Token | Measured | Floor | Spec originally claimed |
|---|---|---|---|
| `--color-fg` | **16.36:1** | 7:1 | 16.1:1 |
| `--color-fg-muted` | **8.13:1** | 7:1 | 7.4:1 |
| `--color-accent` | **7.11:1** | 4.5:1 | 6.8:1 |
| `--color-focus` | **10.49:1** | 4.5:1 | 10.2:1 |
| `--color-pass` | **7.71:1** | 4.5:1 | 7.1:1 |
| `--color-open` | **7.76:1** | 4.5:1 | 8.4:1 ← **overstated** |
| `--color-fail` | **5.84:1** | 4.5:1 | 5.4:1 |
| `--color-info` | **6.37:1** | 4.5:1 | 6.2:1 |

All clear their floors. **Eight of nine hand-computed figures in the specification
disagreed with measurement**, and one was overstated. The specification has been
corrected to these values. In a platform whose first principle is that every number
cites its source, this was the correct class of bug to find early.

## 6. Asset hygiene

| Defect | Before | After |
|---|---|---|
| Font files emitted | 28 (Cyrillic, Greek, Vietnamese) | **5** (Latin) |
| OS metadata files in `dist/` | **61** | **0** |

The AppleDouble files would have been deployed publicly. They carry resource forks and
extended attributes including originating path — a small but real information leak,
invisible in code review. Now removed by `scripts/postbuild.ts` and asserted absent by
`scripts/check.ts`.

## 7. Not yet measured

Lighthouse (needs a deployed URL) · frame timings (no GPU code exists) · marginal
build cost per page · real-device LCP. Each is scheduled to the sprint that first
makes it measurable. **No performance claim in this document is an estimate.**

# Architecture

AdityaNet is a **fully static site** — no runtime server, no database, no user input. Every
response is a file produced at build time. This document explains how the pieces fit and,
more importantly, *why* the system is shaped this way. Decisions are recorded formally as
ADRs under [`adr/`](adr/); this is the narrative overview.

## System overview

```mermaid
flowchart TB
    subgraph Inputs["Build inputs (committed)"]
        ART["artifacts/v2/**.json<br/>benchmark · manifests · ablation"]
        GEN["web/src/generated/data/**.json<br/>derived, typed views"]
        TOK["web/tokens/*.json<br/>design-token source"]
    end
    subgraph Build["web/ — build pipeline"]
        G["generate.ts<br/>tokens to CSS + Tailwind"]
        A["astro build<br/>18 routes"]
        P["postbuild.ts<br/>CSP hashes · vercel.json · render.yaml"]
    end
    subgraph Verify["CI gates (scripts/check.ts)"]
        C1["contrast floors"]
        C2["route JS budgets"]
        C3["evidence consistency"]
        C4["banned lexicon · measurement literals"]
    end
    OUT["dist/ — static output"]
    TOK --> G --> A
    GEN --> A
    ART --> A
    A --> P --> OUT
    ART -. re-read .-> C3
    OUT --> C1 & C2 & C3 & C4
    OUT --> HOST["Static host / CDN"]
```

## The evidence‑integrity pipeline

This is the core mechanism and the reason the platform can claim its numbers are checkable.

1. **Scientific artifacts are the single source of truth.** Frozen JSON under `artifacts/`
   and derived, typed views under `web/src/generated/data/`. These are committed and never
   edited by hand.
2. **A pointer registry** (`measurements.json`) maps a stable key to `{ artifact, JSON
   pointer, precision, unit }`. It says *where* to read a value, never the value itself.
3. **Astro renders at build time**, reading each value through its pointer and stamping the
   rendered element with `data-measurement-key` and `data-measurement-value`.
4. **`pnpm budget` closes the loop.** It scans the built HTML, and for every measurement it
   re‑reads the artifact from disk and asserts the rendered text equals the source, at the
   declared precision. Any drift fails the build.

```mermaid
sequenceDiagram
    participant Art as artifact.json
    participant Reg as measurements.json
    participant Page as Astro page
    participant HTML as dist/**.html
    participant Gate as pnpm budget
    Page->>Reg: key
    Reg-->>Page: artifact + pointer + precision
    Page->>Art: read value (build time)
    Art-->>Page: value
    Page->>HTML: render + data-measurement-key/value
    Gate->>HTML: extract rendered value
    Gate->>Art: re-read pointer from disk
    Gate-->>Gate: assert equal, else FAIL
```

The consequence: a wrong number cannot ship. Either the artifact is wrong (a scientific
matter, tracked separately) or the build fails.

## Why static

See [ADR‑0001](adr/0001-no-runtime-server.md). The site *is* evidence, and evidence should
be cacheable, independently hostable, and free of moving parts. A static bundle can be
served from any CDN indefinitely, mirrored, and archived. There is no server to exploit, no
runtime to keep alive, and no request that isn't enumerable in advance.

## Why Astro, and the island boundary

See [ADR‑0002](adr/0002-astro-over-nextjs.md). The decisive factor was a measurement: a
zero‑interaction page shipped **184 KB gz JS** under the Next App Router (React hydrates
everything) versus **0 bytes** under Astro's islands model. The project's evidence‑route
budgets were simply unachievable on the Next floor.

JavaScript is therefore spent only where interaction is genuine:

| Route | Island | Why it hydrates |
| --- | --- | --- |
| `/` | Landing scene (React + R3F + GSAP) | Scroll‑scrubbed video + WebGL compositing. |
| `/data` | Light curve (uPlot) | Interactive per‑day time series. |
| everything else | none | Static HTML; CSS‑only scroll choreography. |

ESLint import boundaries enforce the layering — evidence components cannot import
experience code, and vice versa — so the separation cannot erode by accident.

## Two rendering domains

See [ADR‑0003](adr/0003-two-rendering-domains.md). Content is split at the architecture
level into two registers that must never be confused:

- **Artistic (Domain A)** — illustrative footage (public‑domain NASA/SVS). Always
  watermarked `ILLUSTRATIVE · NASA / SVS · NOT ADITYA‑L1 DATA`. May be beautiful; claims
  nothing.
- **Measured (Domain B)** — traceable values. Carries no decorative post‑processing,
  because effects on a measurement would misrepresent its provenance.

## Component relationships

```mermaid
flowchart TB
    BL["BaseLayout.astro<br/>header · progress rail · view transitions"] --> HdR["Header (shell)"]
    BL --> AMB["AmbientBackdrop<br/>footage + watermark"]
    BL --> PG["page content"]
    PG --> PH["PageHeader / Section (shell)"]
    PG --> KF["KeyFacts (shell)"]
    PG --> MC["MetricCard (evidence)"]
    PG --> CB["CompareBars (editorial)"]
    PG --> LM["LearnMore (editorial)"]
    MC --> MJ["measurements.json"]
    CB --> BM["benchmark_results.json"]
    LandingIsland["V2Experience (experience)"] --> TL["derive(t) timeline (pure)"]
    LandingIsland --> CAM["camera subsystem (pure)"]
```

The `experience/v2` core — the `derive(t)` timeline and the camera subsystem — is pure and
unit‑tested (no roll, static shots provably static, monotonic certainty). Rendering reads
these; they never reach into rendering.

## Design tokens

See [ADR‑0004](adr/0004-generated-design-tokens.md). Colour and type live in
`web/tokens/*.json` and are emitted by `generate.ts` to both CSS custom properties and
Tailwind config. CI checks the generated files are current, so the two representations
cannot drift. Contrast floors (AAA, ≥ 7:1 body) are asserted against these same tokens.

## Further reading

- [`methodology.md`](methodology.md) — the science and evaluation protocol.
- [`deployment.md`](deployment.md) — hosting, CSP synchronisation, the failure modes solved.
- [`reproducibility.md`](reproducibility.md) — reproducing the dataset and the result.
- [`design-system.md`](design-system.md) — the visual language and editorial split.
- [`adr/`](adr/) — the formal decision records.

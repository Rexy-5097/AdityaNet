<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Governing product specification for AdityaNet Web Platform v1.0. -->
<!-- DATE: 2026-07-23 -->

# AdityaNet Web Platform v1.0 — Product Specification

**Status: FROZEN.** This is the governing document for the AdityaNet web platform.
Implementation follows it exactly unless objective engineering evidence shows a
decision is flawed. Changes require: stop -> explain -> propose alternatives ->
approval -> amend this document.

---

## ⚠ READING ORDER — REVISIONS SUPERSEDE

Parts 1-3 were written first and describe decisions that Part 4 Section 16 later
**reversed after a full-specification review**. Part 4 is authoritative wherever
they disagree. The reversals a reader must know before trusting Parts 1-3:

| Ref | Parts 1-3 said | Superseded by Part 4 §16 |
|---|---|---|
| R-A | Six surfaces incl. a Pipeline page | **Five surfaces**; Pipeline -> `/build#architecture` |
| R-B | Three font families (Sans/Mono/Serif) | **Two**: IBM Plex Sans + Mono |
| R-C | Binary encoding for light curves | **JSON** for light curves; binary for spectra only |
| R-D | 12 component variants specified upfront | **One variant each**; more on second real use |
| R-E | 36 visual-regression baselines | **10** |
| R-F | Search + command palette in v1 | **Deferred to S9+**; no search index generated |
| R-G | Density toggle (comfortable/compact) | **Cut** |
| R-H | Python types generated from OpenAPI | **Validate-only**; derive.py writes plain dicts |
| R-I | Custom client-error beacon | **Cut for v1.0** |
| R-J | WebGL SunHero in v1.0 | **Static SVG in S2**; WebGL deferred to S9 (open decision) |
| R-K | 7 bespoke tooling artifacts | **4**: generate.ts, check.ts, derive.py, 2 lint rules |

Part 3's own review additionally superseded Parts 1-2 on:

| Ref | Superseded |
|---|---|
| §9.0 | No FastAPI runtime. Endpoint *design* survives; the *server* does not. All responses are pre-generated static files. |
| R1 | `<ScientificChart>` abstraction deferred until a third chart exists. |
| R2 | Seven test levels collapsed to four CI gates. |
| R4 | uint16 overflow guard added as fail-loud rule **F-21**. |
| R6 | Four branded types reduced to one (`ChannelIdx`). |

---

## 📖 EXPERIENCE BIBLE

`EXPERIENCE_BIBLE.md` is the **creative constitution**. It governs intent — vision,
registers, narrative, motion, and honesty rules. This document and Amendment 02 govern
construction. Where the Bible conflicts with an implementation decision, the Bible wins,
and a principle is amended there before it is implemented here.

It introduces a **third register**: Schematic (S), between Artistic (A) and Measured (B).
P8 previously recognised only two, which wrongly collapsed "illustrative engineering
visualisation" into "fabricated engineering geometry". They are different claims.

---

## ⚠ AMENDMENT 02 — EXPERIENCE ARCHITECTURE (Sections 18-19)

`SPEC_AMENDMENT_02_EXPERIENCE.md` is **normative and supersedes this document** on:
P8 (representational fidelity, now domain-scoped), motion law L2, §7.6 visual
prohibitions, §11.6 budgets, §9.4 framework (Astro, not Next), and §3.3 surfaces
(adds `/explore`). Sections 9-13 (the scientific architecture) are unchanged.

Read it before trusting Parts 1-4 on anything concerning the presentation layer.

---

## Table of contents

- **Part 1** — Sections 1-4: Product Vision, Personas, Information Architecture, Page Specifications
- **Part 2** — Sections 5-8: Design System, Component Library, Visual Language, Interaction Design
- **Part 3** — Sections 9-13: Data Architecture, API Specification, Frontend Architecture, Quality Standards, Deployment
- **Part 4** — Sections 14-17: Future Roadmap, Master Implementation Roadmap, Critical Design Review, Final Verdict

---

Research complete. Three findings from the tooling that directly shape the spec:

- **`ui-ux-pro-max` → typography:** the "Dashboard Data" pairing (**Fira Code + Fira Sans**, Mono+Sans) is its top recommendation for analytics/data-viz — which matches our need for tabular numeric alignment.
- **`ui-ux-pro-max` → charts:** line charts grade **AA**, but heatmaps only **B** ("pattern overlay for colorblind, numerical value on hover, legend with scale ticks"). It also surfaced "Streaming Area Chart" for live monitoring — which we explicitly *don't* have, confirming we avoid that entire pattern.
- **21st.dev → honest limitation:** its catalog is SaaS/marketing-oriented. Four dark themes, two loosely-relevant dashboard components, nothing scientific. **Conclusion: 21st.dev is for generic primitives only; every scientific component we build ourselves.** I'd rather state that than pretend the tool covers more than it does.

Delivering **Part 1 — Sections 1–4** (Product & Experience Foundation). I'll stop there and continue on your confirmation.

---

# ADITYANET WEB PLATFORM v1.0 — PRODUCT SPECIFICATION
## Part 1 of 4 · Sections 1–4

---

# SECTION 1 — PRODUCT VISION

## 1.1 Why AdityaNet exists

Aditya-L1's SoLEXS and HEL1OS payloads produce public archive data that is **technically accessible but practically unusable** to most researchers. The raw products are Level-1 FITS with undocumented conventions: inclusive GTI endpoints, three mutually incommensurable channel spaces, a light curve that is band-limited rather than total, spectra whose time column is an offset rather than an epoch, and housekeeping written in telemetry-arrival order. Every one of those facts was discovered by this project through measurement, and each one silently corrupts an analysis that assumes otherwise.

AdityaNet exists to publish **the corrected, provenance-tracked, reproducible form of that archive**, together with an honest account of what can and cannot be concluded from it.

## 1.2 What problem it solves

| Problem | AdityaNet's answer |
|---|---|
| Raw archive requires undocumented domain knowledge | Canonical dataset with a documented, versioned contract |
| No way to verify an analysis is correct | Every row traces to a source file + SHA-256; 6 contradictions publicly adjudicated |
| Published results rarely reproducible | Byte-identical rebuild from raw FITS, demonstrated 12/12 |
| ML claims in space weather often unfalsifiable | Event-level evaluation with CIs; the negative result published |

## 1.3 Who it serves

Six personas, specified in Section 2. In priority order of *design weight*: **Reviewer** and **ISRO Scientist** (they decide whether it's credible), then **Researcher** and **ML Engineer** (they use it), then **Open-source Contributor** and **Recruiter** (they extend/evaluate it).

## 1.4 What makes it different

Not the ML — the ML result is *negative*. The differentiators are:

1. **A public contradiction ledger.** Six times, execution falsified the specification; each was documented, adjudicated, and folded into a versioned contract (r0→r6). No project shows this.
2. **Provenance to the byte.** 5,199 provenance records; zero orphan rows.
3. **A published negative result.** "ML adds no operational value; use a threshold" — stated confidently, with paired significance tests.
4. **It found its own worst bug.** v1 ran 30 sprints on synthetic data. The project caught it, proved it forensically, and voided its own prior conclusions.

## 1.5 Mission statement

> **AdityaNet is an independent research platform that makes the Aditya-L1 X-ray archive usable, verifiable, and honest — publishing not only what was found, but the evidence that makes it checkable.**

## 1.6 Design philosophy

**The interface is an instrument, not an advertisement.** Its job is to let a skeptical expert verify a claim in as few steps as possible. Aesthetic quality serves legibility and trust; it never generates them.

## 1.7 Core principles (binding, testable)

| # | Principle | Enforcement |
|---|---|---|
| **P1** | **Every number cites its source.** No statistic renders without an artifact reference. | `<MetricCard>` requires a `source` prop; CI test asserts displayed values equal committed JSON |
| **P2** | **Nothing implies live operations.** | Banned lexicon (§7.6); every temporal view carries an `ARCHIVE · AS OF` stamp |
| **P3** | **Uncertainty travels with the estimate.** | Any model metric renders with its CI or is not rendered |
| **P4** | **Limitations are content, not footnotes.** | Limitations are a first-class surface, linked from Findings |
| **P5** | **No decoration without function.** | Every animation/3D element must encode data or aid navigation |
| **P6** | **Absence is shown, never filled.** | Gaps render as gaps; no interpolation in any chart |
| **P7** | **The platform is read-only.** | No auth, no writes, no user accounts |

---

# SECTION 2 — USER PERSONAS

### 2.1 Researcher (solar physicist)
**Goals.** Determine whether the canonical data is usable for their own work; extract a specific date range.
**Pain points.** Undocumented FITS conventions; not knowing whether someone else's "cleaned" dataset silently altered values.
**Journey.** Overview → **Data** → picks 2024-05-14 → inspects light curve, spectrum, GTI, provenance → Build → downloads.
**Entry.** Overview or a deep link to a date. **Exit.** Build (dataset download) or the repo.
**Trust signals.** The X8.7 peak resolving at 16:49 UTC against GOES 16:51; per-row `src_sha256`; the explicit "no RMF → no keV" statement where a naive platform would have invented an energy axis.

### 2.2 Reviewer (referee / senior scientist)
**Goals.** Answer "is this rigorous?" in under 15 minutes.
**Pain points.** Projects that present conclusions without method; unreproducible pipelines.
**Journey.** **Validation** → opens CONTRADICTION-001 → reads Evidence→Decision→Spec-diff→Result → **Findings** → **Build** (reproduce).
**Entry.** Validation. **Exit.** Build.
**Trust signals.** A contradiction where the project ruled *against its own convenience*; the r5 amendment where the owner **declined** the implementer's proposal to encode statistics into the contract; byte-identical rebuild evidence.

### 2.3 ISRO Scientist (domain authority)
**Goals.** Verify a third party analyzed their mission's data correctly.
**Pain points.** Outsiders overclaiming; physically wrong handling presented confidently.
**Journey.** **Data** (verify a known event) → **Validation** (check instrument handling) → **Findings/Limitations**.
**Entry.** Data. **Exit.** Limitations — and this is the persona-defining detail: *they are convinced by the limitations page, not the results page.*
**Trust signals.** Inclusive GTI convention; CZT 341 / CdTe 511 kept separate; the RMF gap named as a blocker rather than papered over; A-14 (GTI excess) published as **unexplained**.

### 2.4 ML Engineer
**Goals.** Find out what model won and whether the evaluation is sound.
**Pain points.** Leaky splits; minute-level metrics on autocorrelated data; AUC without CIs.
**Journey.** **Findings → Evaluation** → checks split/leakage → sees threshold recommended → **Build/API** to rerun.
**Entry.** Findings. **Exit.** API or repo.
**Trust signals.** 581 events not 564,160 minutes; autocorrelation 0.64 @ 8h justifying the chronological split; paired day-block bootstrap; the confidence to publish LightGBM being *significantly worse* at prediction.

### 2.5 Recruiter / hiring manager
**Goals.** Assess capability in ~90 seconds.
**Pain points.** Cannot evaluate domain depth; every project claims "AI-powered."
**Journey.** **Overview** — one scroll — then either bookmark or leave.
**Entry & Exit.** Overview.
**Trust signals.** The arc: *caught our own synthetic-data bug → rebuilt from real archive → tested ML honestly → reported it doesn't win.* Numbers with denominators. Absence of hype vocabulary.

### 2.6 Open-source contributor
**Goals.** Run it locally; extend it.
**Pain points.** Missing lockfiles; "works on my machine"; undocumented data deps.
**Journey.** **Build** → clone → lockfile → one-command rebuild → hashes match.
**Entry & Exit.** Build → GitHub.
**Trust signals.** Pinned `requirements.lock` with SHA; the documented numpy-pin incident; 188/188 tests; exact reproduce steps.

### 2.7 Cross-persona finding

**Five of six personas are converted by *checkability*, not by visual polish.** The IA must therefore surface *evidence* at the top level and treat aesthetics as the carrier, not the payload. This single observation drives Section 3.

---

# SECTION 3 — INFORMATION ARCHITECTURE

## 3.1 Method

I challenged each candidate page against three tests: **(1)** does a named persona's journey require it? **(2)** does it contain content no other page owns? **(3)** can it be honest? Anything failing any test was merged or cut.

## 3.2 Pages challenged and cut

| Candidate | Verdict | Reason |
|---|---|---|
| Mission Dashboard / Mission Control | **CUT** | Fails test 3. There is no live mission. "Mission health" of a frozen archive is theater. Its one honest feature (replay a historical date) belongs to **Data**. |
| Archive Explorer *vs* Scientific Analytics | **MERGED → Data** | ~70% content overlap (both browse observations, spectra, light curves). Two shallow pages instead of one deep one is a padding tell. |
| Research (papers/DOI) | **MERGED → Build** | Fails test 2 today: no paper exists. A "coming soon" DOI is a credibility leak. Real downloads live in Build; a Paper section appears **only when a paper exists**. |
| API + Documentation | **MERGED → Build** | Same persona (contributor/reviewer), same task (run it). Swagger is a panel, not a page. |
| Scientific Findings *vs* Evaluation | **MERGED → Findings** | The ML result *is* a scientific finding. Splitting them implies ML is a separate concern from science — the opposite of this project's thesis. |
| Login / accounts | **CUT** | Read-only public open-science platform. A login wall contradicts reproducibility and adds infrastructure for zero benefit. |

## 3.3 Final hierarchy — 6 surfaces

```
AdityaNet
├── 1. Overview          entry for all; the honest story in one scroll
├── 2. Validation        the contradiction ledger + spec evolution   ◄ credibility engine
├── 3. Data              archive browse + replay + all scientific viewers
├── 4. Findings          scientific results + ML evaluation + limitations
│      └── /limitations  (deep-linkable sub-route, own URL)
├── 5. Pipeline          interactive architecture; nodes → real artifacts
└── 6. Build             reproduce · API · downloads · hashes · tests
```

**Nav order is deliberate.** Validation sits at position 2 — before the data and before the results. That ordering is itself an argument: *here is why you should believe anything that follows.* Most platforms bury methodology; putting it second is the strongest available signal that the evidence is the product.

## 3.4 Why exactly six

Fewer than five cannot separate the personas' distinct jobs (verify / use / evaluate / reproduce). More than seven and each surface becomes shallow — the breadth tell. Six maps 1:1 onto the six persona entry points, with Overview absorbing the recruiter.

## 3.5 Navigation structure

- **Persistent top bar:** wordmark · 6 links · dataset-version chip (`r1 · 43fd0e22`) · GitHub · theme toggle.
- **The version chip is global and always visible.** Every page's content is relative to a dataset version; showing it constantly makes that unambiguous and pre-empts the "which data is this?" question.
- **No mega-menus, no dropdowns.** Six items fit; hiding them behind interaction would be complexity for its own sake.
- **Breadcrumbs** only on Data (date context) and Validation (contradiction context) — the two surfaces with drill-down.
- **Command palette (⌘K)** is the power-user path: jump to date, contradiction, endpoint, metric. It is *additive* — every destination is reachable without it.

---

# SECTION 4 — PAGE SPECIFICATIONS

> Common to all pages: dark theme; `ARCHIVE · AS OF <date>` stamp on any temporal view; every statistic via `<MetricCard>` with a source link; `prefers-reduced-motion` honored; skip-to-content link; `<main>` landmark.

---

## 4.1 OVERVIEW (`/`)

**Purpose.** Convert a cold visitor into a persona-appropriate destination within 90 seconds, using only true statements.

**User story.** *As a recruiter, I want to understand the depth of this work in one scroll, so I can decide whether to look deeper.*

**Information hierarchy.**
1. **Identity block** — "AdityaNet · Aditya-L1 X-Ray Archive Research Platform" + one-sentence scope + explicit **"Independent research project. Not affiliated with ISRO."**
2. **The arc** (4 steps, the story): Synthetic data detected → Real archive activated → Validated → ML tested honestly.
3. **Headline metrics** (6 cards, all with denominators): 424 / 436 SoLEXS days · 389 / 391 HEL1OS orbits · 581 independent M/X events · 3,560,092 canonical rows · 5,199 provenance records · 6 contradictions resolved.
4. **The finding**, stated plainly: *Threshold detection recommended. ML provides no operational benefit for the evaluated tasks.*
5. **Four persona doors** — "Verify the method" / "Explore the data" / "Read the findings" / "Reproduce it."
6. **Sun visualization** — see Animations.

**Components.** `<IdentityBlock>`, `<ArcTimeline>`, `<MetricCard>×6`, `<FindingStatement>`, `<PersonaDoor>×4`, `<SunHero>`, `<DatasetVersionChip>`.

**Interactions.** Metric cards → hover reveals source artifact + SHA prefix; click → deep-links to the surface that owns it. Persona doors → route. Sun → click a date-band to jump into Data at that date.

**Animations.** **One** WebGL element: a slowly rotating solar sphere whose surface luminance encodes **real archive activity** (daily max `rate_total`, normalized) across the 424 covered days, with a visible ring of gaps where coverage is missing. It is *functional* — it is the date entry point and it visualizes coverage. Rotation 0.05 rad/s; disabled under `prefers-reduced-motion` (static render). No particles, no lens flares, no starfield parallax.

**Loading.** Skeletons matched to final layout (no spinner). Metric values stream from a single pre-rendered JSON — effectively instant since the page is statically generated. Sun mesh loads after first paint; canvas reserves its box to prevent CLS.

**Empty.** Not applicable — Overview is statically generated from committed artifacts. If the artifact is missing at *build* time, the build **fails** rather than shipping a page with blanks (P1).

**Error.** WebGL unsupported/blocked → static SVG solar disc with the same coverage ring, no functionality lost (the date band remains clickable).

**Responsive.** ≥1280px: two-column (narrative left, Sun right). 768–1279: single column, Sun above metrics, metrics 2×3. <768: single column, Sun 320px, metrics 1×6, arc becomes vertical stepper.

**Accessibility.** Sun canvas has `role="img"` + descriptive `aria-label` and an adjacent visually-hidden data table of coverage by month (the canvas is never the only path to the information). Metric cards are `<article>` with `<dl>` semantics. Contrast ≥ 7:1 for body (AAA), ≥ 4.5:1 minimum for all text.

**Performance.** LCP < 1.5s. Sun bundle lazy-loaded, ≤ 120KB gz, excluded from the critical path. Total page JS ≤ 180KB gz.

**Data sources.** `freeze_manifest.json`, `CANONICAL_DATASET_PROFILE.md` (parsed), `benchmark_results.json`, contradiction docs (count only), `scientific_validation.json`. Daily activity series pre-computed at build time into `overview_activity.json` (424 floats — trivial payload).

**API.** `GET /api/v1/overview` (also inlined at build time; the endpoint exists for API parity, not for the page's own rendering).

**Why it deserves to exist.** It is the only surface serving the recruiter, and the entry point for all others. Without it, five personas have no front door.

---

## 4.2 VALIDATION (`/validation`, `/validation/[id]`)

**Purpose.** Prove the pipeline's correctness by exposing the full adjudication history — the credibility engine.

**User story.** *As a reviewer, I want to see how a discovered defect was proven, decided, and folded into the specification, so I can judge whether the process is rigorous.*

**Information hierarchy.**
1. **Validation status board** — parser · archive · GTI · provenance · canonical · version-resolution, each PASS with its evidence link and test count (188/188).
2. **Contradiction ledger** — 6 entries, each: ID · title · severity · status · spec revision it produced.
3. **Open scientific questions** — CONTRADICTION-003 (resolved→finding), **A-14** (open, unexplained). Displayed as *open*, not hidden.
4. **Specification evolution** — r0 → r6 timeline; each revision links to the contradiction that forced it.

**Detail route `/validation/[id]`** renders the five-act structure:
`Timeline → Evidence (measured values) → Decision (owner ruling, incl. rejected alternatives) → Spec Diff (r_n → r_n+1) → Result (what changed in the data)`

**Components.** `<ValidationStatusBoard>`, `<ContradictionLedger>`, `<ContradictionDetail>` → {`<ContradictionTimeline>`, `<EvidenceBlock>`, `<DecisionBlock>`, `<SpecDiff>`, `<ResultBlock>`}, `<SpecRevisionTimeline>`, `<OpenQuestionCard>`.

**Interactions.** Ledger row → detail (client-side route, preserves scroll). Spec diff → toggle unified/split. Evidence block → expand raw measured values. Deep-linkable anchors per act (`/validation/001#decision`).

**Animations.** Timeline nodes stagger-fade on mount (60ms interval, 200ms duration) to establish reading order. Spec diff line-highlight on expand. Nothing else. All suppressed under reduced-motion.

**Loading.** Statically generated — no runtime loading. Route transitions use React `Suspense` with a skeleton matching the five-act layout.

**Empty.** "No open questions" is a legitimate state and renders as an affirmative statement, not a blank.

**Error.** A missing contradiction ID → 404 with a link back to the ledger listing all valid IDs.

**Responsive.** ≥1024: two-column (sticky act-navigator left, content right). <1024: single column, act navigator becomes a sticky horizontal tab strip.

**Accessibility.** The five acts are `<section>`s with `aria-labelledby`. Timeline is an ordered list, not divs. Diff uses `<ins>`/`<del>` with text markers (`+`/`−`) so it is not color-dependent. Severity uses icon + text, never color alone.

**Performance.** Pure static content. LCP < 1.0s. Zero client JS beyond routing and the diff toggle.

**Data sources.** `CONTRADICTION-001…006.md`, `PARSER_SPECIFICATION.md` (§10 revision history), `MILESTONE_VIII_VALIDATION_REPORT.md`, test counts from CI output. Parsed at build time into structured JSON — **the markdown remains the source of truth**; the site never restates a decision in its own words.

**API.** `GET /api/v1/validation/contradictions`, `GET /api/v1/validation/contradictions/{id}`, `GET /api/v1/validation/spec-revisions`.

**Why it deserves to exist.** It is the single most differentiating surface. It converts the reviewer and the ISRO scientist. No comparable platform exposes its own adjudication record.

---

## 4.3 DATA (`/data`, `/data/[date]`)

**Purpose.** Let a scientist inspect any observation day at full fidelity, with provenance attached.

**User story.** *As a solar physicist, I want to open 2024-05-14 and see the light curve, spectrum, GTI, and provenance together, so I can judge whether this dataset is trustworthy for my work.*

**Information hierarchy.**
1. **Coverage selector** — calendar heatmap, 2024-02 → 2026-06, cell = day, encoding daily max rate; **gaps rendered as gaps** (distinct hatch, never zero).
2. **Day header** — date · `ARCHIVE · AS OF` · detector · archive version · live-time · GTI fraction · quality flags.
3. **Light curve** (T1) — primary panel, minute resolution, GTI-excluded regions visibly broken.
4. **Spectrum** (T2) — 340 PI channels × time heatmap + a single-minute channel profile on selection.
5. **GTI strip** (T6) — interval bar aligned to the light-curve x-axis.
6. **Provenance** (T7) — source files, SHA-256, parser version, assumptions applied.
7. **FITS header** — raw header of the source product, collapsed.

**Components.** `<CoverageCalendar>`, `<DayHeader>`, `<LightCurveViewer>`, `<SpectrumViewer>`, `<GtiStrip>`, `<ProvenanceExplorer>`, `<FitsHeaderViewer>`, `<TimeAxisSync>` (shared x-axis controller).

**Interactions.** Brush-zoom on the light curve → **synchronously** zooms spectrum + GTI (single shared time axis; this synchronization is the core scientific affordance). Click a minute → spectrum profile for that minute. Hover → crosshair with exact value + timestamp. Keyboard: `←/→` step a day, `+/−` zoom, `0` reset.

**Animations.** Zoom transitions 150ms ease-out on the axis only — data marks never animate position (a moving data point is a lie about the measurement). Panel cross-fade on date change, 120ms.

**Loading.** Per-panel skeletons; the light curve loads first (smallest payload) and the spectrum streams after. A determinate progress indicator for the spectrum (it is the heavy fetch).

**Empty.** Day exists but detector inactive → explicit "SDD1: no science products (GTI-only, F-12 inactive)". Day not in dataset → "Not in dataset" with the reason (F-19 GTI defect / acquisition gap) and a link to the Archive Quality record. **A missing day always explains itself.**

**Error.** Fetch failure → panel-scoped error with retry; other panels stay usable. Never a full-page error for a partial failure.

**Responsive.** ≥1440: 3-row stack, full-width panels, calendar in a left rail. 1024–1439: calendar collapses to a date picker + month strip. <1024: panels become vertically stacked cards, spectrum heatmap switches to a channel-group summary (5 bands) with a "view full spectrum on desktop" note — **honest degradation rather than an unreadable 340-row heatmap on a phone.**

**Accessibility.** Every chart has a `<table>` fallback (toggle: "View as data"). Heatmap ships with a **numeric-on-hover readout and a legend with scale ticks** — directly per the `ui-ux-pro-max` accessibility note (heatmaps grade **B**; these mitigations are mandatory, not optional). Colormap is **viridis** (perceptually uniform, colorblind-safe). Full keyboard operation of zoom/pan.

**Performance.** **The hard constraint:** T2 is 340 floats × 1,440 min/day. Never ship raw. Server pre-aggregates to ≤ 60 time bins × 340 channels for the default view (~20k floats ≈ 80KB), refining on zoom. Light curve decimated via **LTTB** to ≤ 2,000 points. Panel render < 500ms after data arrival. Charts on `<canvas>` (ECharts), not SVG — 1,440 SVG nodes would jank.

**Data sources.** T1, T2, T6, T7 parquet (pre-aggregated at build time per day into JSON), `canonical_build_stats.json` for coverage.

**API.** `GET /api/v1/days`, `/api/v1/days/{date}/lightcurve`, `/{date}/spectrum?bins=&channels=`, `/{date}/gti`, `/{date}/provenance`, `/{date}/fits-header`.

**Why it deserves to exist.** It is the product for the researcher and the verification instrument for the ISRO scientist. Without it, the dataset is an abstract claim.

---

## 4.4 FINDINGS (`/findings`, `/findings/limitations`)

**Purpose.** Present the scientific conclusions and the ML evaluation — including the negative result — with full uncertainty.

**User story.** *As an ML engineer, I want to see the benchmark, the split, and the significance tests, so I can judge whether "ML doesn't help" is a sound conclusion or a weak baseline.*

**Information hierarchy.**
1. **Headline conclusion** — threshold recommended; ML no operational benefit. Stated first, without hedging.
2. **Scientific findings F-1 … F-7** — each with evidence, status, and the artifact link.
3. **ML benchmark table** — 8 models × 2 tasks, every metric with CI.
4. **Significance** — paired day-block bootstrap deltas; explicit "statistically indistinguishable" labels where CIs span zero.
5. **Evaluation protocol** — split, autocorrelation justification (0.997 @ 1min → 0.64 @ 8h), event-level rationale (581 not 564,160).
6. **Feature ablation** — T2 spectral null (+0.0033), T4 exclusion rationale.
7. **Limitations** → dedicated sub-route.

**Components.** `<ConclusionStatement>`, `<FindingCard>×7`, `<BenchmarkTable>`, `<RocCurve>`, `<PrCurve>`, `<CIBar>`, `<SignificanceVerdict>`, `<ProtocolPanel>`, `<AblationTable>`, `<LimitationCard>`.

**Interactions.** Benchmark row → expands full metric set + confusion matrix. Model toggle on ROC/PR overlays curves. Hover a CI bar → exact interval. Task switch (nowcast ↔ prediction) preserves the selected models.

**Animations.** ROC curve draws once on scroll-into-view (400ms, path-length), because the *shape* is the information and drawing directs the eye along it. Never loops. Suppressed under reduced-motion (renders complete).

**Loading.** Static. Charts hydrate from inlined JSON.

**Empty.** Not applicable.

**Error.** Chart render failure → falls back to the numeric table, which is always present in the DOM anyway (it's the a11y fallback).

**Responsive.** ≥1280: table + charts side-by-side. <1280: stacked; the benchmark table scrolls horizontally **inside its own container** (never the page body).

**Accessibility.** Benchmark table uses `<caption>`, `<th scope>`, and row headers. Curves have data-table equivalents. "Statistically indistinguishable" is rendered as **text**, never implied by overlapping colors alone. CI bars carry numeric labels.

**Performance.** All data < 100KB. LCP < 1.2s.

**Data sources.** `benchmark_results.json`, `benchmark_predictions.json` (for curve regeneration), `ablation_results.json`, `SCIENTIFIC_FINDINGS.md`, `EVALUATION_PROTOCOL.md`, `DATASET_LIMITATIONS_FOR_ML.md`.

**API.** `GET /api/v1/findings`, `/api/v1/evaluation`, `/api/v1/evaluation/curves?task=&model=`, `/api/v1/limitations`.

**Why it deserves to exist.** It is where the project's scientific output lives. Splitting "findings" from "evaluation" would imply ML is separate from the science; merging them enacts the thesis that a negative ML result *is* a finding.

---

## 4.5 PIPELINE (`/pipeline`)

**Purpose.** Make the system's architecture inspectable — every stage links to the real code and artifacts it produced.

**User story.** *As a contributor, I want to understand how raw FITS becomes a canonical table, so I know where to make a change.*

**Information hierarchy.** Linear flow, each node expandable:
`ISSDC Archive → Extraction → Parsers → Validation → Version Resolution → Canonical Builders → Frozen Dataset → Evaluation`

Each node: what it does · fail-loud rules enforced · code link · artifact produced · key measured numbers (e.g. Version Resolution: 1,065,572 owned pairs, 48,604 conflicts, R1 47,328 / R2 1,276 / R3 0 / F-14 0).

**Components.** `<PipelineDiagram>` (SVG), `<PipelineNode>`, `<NodeDetailPanel>`, `<RuleBadge>` (F-01…F-20).

**Interactions.** Click node → side panel. Hover → highlights the node's inputs/outputs. Rule badge → tooltip with the rule's exact text.

**Animations.** On scroll-into-view, the flow path draws once (stroke-dashoffset, 600ms) to establish direction. **No perpetual pulsing** — a permanently animating diagram implies live flow, violating P2.

**Loading.** Static SVG, inline. No loading state.

**Empty / Error.** Not applicable (static content).

**Responsive.** ≥1024: horizontal flow. <1024: vertical flow, detail panel becomes a bottom sheet.

**Accessibility.** The diagram is an ordered list of stages in the DOM, visually positioned; screen readers get a coherent sequence. Each node is a `<button>` with `aria-expanded`. Full keyboard traversal.

**Performance.** Inline SVG ≤ 20KB. Negligible JS.

**Data sources.** `ROADMAP.md`, `PARSER_SPECIFICATION.md`, `version_resolution_log.json`, `canonical_build_stats.json`, GitHub source links.

**API.** None — fully static.

**Why it deserves to exist.** It is the map that makes Validation and Build navigable, and it is the contributor's orientation page. It earns its place only because every node links to something real; a decorative diagram would fail P5.

---

## 4.6 BUILD (`/build`)

**Purpose.** Enable independent reproduction and programmatic access.

**User story.** *As a contributor, I want to rebuild the dataset and get the same hash, so I can trust and extend it.*

**Information hierarchy.**
1. **Reproduce** — exact commands, environment pins, expected wall time (extraction 6.8 min; build 93.75 min).
2. **Verify** — `dataset_hash 43fd0e22…`, per-table hashes, the reproducibility result (byte-identical 12/12).
3. **Environment** — Python 3.12.12, numpy 1.26.4 (with the pin incident noted), lockfile SHA.
4. **API** — embedded OpenAPI explorer.
5. **Downloads** — canonical tables, manifest, reports.
6. **Tests** — 188/188, what each suite guarantees.

**Components.** `<CommandBlock>` (copy button), `<HashTable>`, `<EnvironmentPanel>`, `<ApiExplorer>` (embedded Swagger), `<DownloadTable>`, `<TestSummary>`.

**Interactions.** Copy-to-clipboard on every command. API explorer: try-it-out against live endpoints. Hash click → copy full SHA.

**Animations.** Copy confirmation only (150ms check-mark). Nothing else.

**Loading.** Static except the API explorer, which lazy-loads its bundle on first scroll into view (it is heavy and most visitors never reach it).

**Empty.** Downloads unavailable (hosting limits) → explicit instructions to rebuild locally rather than a dead button.

**Error.** API explorer failing to reach the backend → inline notice with the static OpenAPI spec still browsable.

**Responsive.** Command blocks scroll horizontally within their container; hash table collapses to a definition list < 768px.

**Accessibility.** Command blocks are `<pre><code>` with an accessible copy button label ("Copy command: git clone…"). Swagger UI is third-party — we ship a documented a11y caveat and provide the raw spec as an accessible alternative.

**Performance.** Swagger bundle (~400KB) strictly lazy and out of the initial bundle.

**Data sources.** `DATASET_MANIFEST.md`, `REPRODUCIBILITY_REPORT.md`, `freeze_manifest.json`, `requirements.lock`, OpenAPI spec, CI test output.

**API.** `GET /api/v1/dataset/manifest`, `GET /api/v1/openapi.json`.

**Why it deserves to exist.** Reproducibility is a headline claim; a claim without an executable path is marketing. This page is where the claim becomes checkable.

---

## 4.7 Page-to-persona coverage matrix

| Page | Researcher | Reviewer | ISRO | ML Eng | Recruiter | Contributor |
|---|---|---|---|---|---|---|
| Overview | ○ | ○ | ○ | ○ | **●** | ○ |
| Validation | ○ | **●** | **●** | ○ | — | ○ |
| Data | **●** | ○ | **●** | ○ | — | — |
| Findings | ○ | **●** | ○ | **●** | ○ | — |
| Pipeline | — | ○ | ○ | ○ | — | **●** |
| Build | **●** | **●** | — | ○ | ○ | **●** |

● primary · ○ secondary — every persona has a primary surface; no surface lacks a primary persona. **No orphan pages.**

---

**End of Part 1 (Sections 1–4).**

Next, on your confirmation, **Part 2 — Sections 5–8**: Design System (tokens, type scale, grid, color with contrast ratios, elevation, motion), Component Library (full props/states/a11y/performance per component), Visual Language (defining "mission-grade without impersonation"), and Interaction Design (keyboard model, search, progressive disclosure, scientific storytelling).

Say **continue** and I'll proceed.

---

# ADITYANET WEB PLATFORM v1.0 — PRODUCT SPECIFICATION
## Part 2 of 4 · Sections 5–8

---

# SECTION 5 — DESIGN SYSTEM

## 5.0 The governing idea

Most design systems organize tokens by *appearance* (colors, sizes). This one organizes them by **epistemic role**: what kind of knowledge a piece of the interface represents. Three roles exist, and they never mix:

| Role | Meaning | Type | Color namespace |
|---|---|---|---|
| **Interface** | Controls the user operates | Sans | UI palette |
| **Measurement** | Values produced by the pipeline | Mono, tabular | Data palette (disjoint) |
| **Argument** | Human reasoning and adjudication | Serif | Prose (neutral only) |

**Why this exists.** In a platform whose entire value is "you can tell what is measured and what is asserted," the type and color systems should make that distinction *pre-attentively* — before the user reads a word. A number rendered in mono tabular type on the data palette is a measurement; the same number in sans is a UI label. This is an information-design decision, not a stylistic one, and it is the reason the system does not look like a generic SaaS dashboard.

---

## 5.1 Typography

### 5.1.1 The recommendation received, and the deviation

`ui-ux-pro-max` returned **"Dashboard Data" — Fira Code + Fira Sans (Mono + Sans)** as the top pairing for analytics and data visualization. I adopt the **structural** recommendation (mono + sans for tabular density) and **substitute the families**, for three reasons:

1. **We need a serif and Fira has none.** Validation renders long-form adjudication prose. IBM Plex is a superfamily — Sans, Mono, **Serif**, and Condensed — with shared metrics, vertical rhythm, and a common design axis. Mixing Fira Sans with an unrelated serif would break optical harmony; Plex gives one type system across all three epistemic roles.
2. **Fira Code's ligatures are actively harmful here.** Programming ligatures render `->`, `!=`, `>=`, `==` as glyphs. We display SHA-256 hashes, statistical intervals (`[-0.0445, -0.0004]`), and comparison operators as *data*. A ligature silently alters the visual identity of a measured string. Disqualifying.
3. **Plex was commissioned for technical documentation** and ships true tabular lining figures in Sans, which we require for metric alignment.

### 5.1.2 Families

```
--font-sans:  "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
--font-mono:  "IBM Plex Mono", ui-monospace, "SF Mono", monospace;
--font-serif: "IBM Plex Serif", ui-serif, Georgia, serif;
```

Weights shipped: Sans 400/500/600, Mono 400/500, Serif 400/600. **Six files, all subset to Latin + the scientific glyph set** (× ≈ ± − ° μ σ Δ α ≤ ≥ ∞ †). Variable fonts are *not* used — static subsets are smaller for a fixed weight set and avoid the FOUT-with-variable-axis flash. Total font payload ≤ 145KB woff2.

**`font-display: swap`** with a metrics-matched fallback (`size-adjust`) so text is readable immediately and does not reflow.

### 5.1.3 Two scales, not one

The skill's data-density guidance (12–14px, tight leading) is correct for tables and wrong for a 900-word adjudication document. A single scale cannot serve both. So:

**Interface scale** — base 13px, ratio 1.2 (minor third, tight — dense UI needs small steps so adjacent sizes are distinguishable without large jumps):

| Token | px | Line height | Use |
|---|---|---|---|
| `--text-2xs` | 10 | 14 | Axis ticks, table micro-labels |
| `--text-xs` | 11 | 16 | Metadata, source refs, badges |
| `--text-sm` | 12 | 18 | Table cells, dense values |
| `--text-base` | 13 | 20 | UI body, controls |
| `--text-md` | 15 | 22 | Card titles, panel headings |
| `--text-lg` | 18 | 26 | Section headings |
| `--text-xl` | 24 | 32 | Page titles |
| `--text-2xl` | 32 | 40 | Overview headline |
| `--text-metric` | 28 | 32 | Metric card values (mono, tabular) |
| `--text-metric-lg` | 40 | 44 | Overview headline metrics |

**Document scale** — base 17px, ratio 1.25, measure capped at **68ch**:

| Token | px | Line height |
|---|---|---|
| `--doc-body` | 17 | 28 |
| `--doc-h3` | 19 | 28 |
| `--doc-h2` | 23 | 32 |
| `--doc-h1` | 29 | 38 |

**Why 68ch.** Below ~45ch the eye returns too often; above ~75ch it loses the line on return sweep. 68 sits in the safe band with room for inline code spans, which are wider than prose.

### 5.1.4 Numeric rendering — a hard rule

Every number produced by the pipeline renders with:

```css
font-family: var(--font-mono);
font-variant-numeric: tabular-nums lining-nums slashed-zero;
```

**Why `slashed-zero`:** we display hexadecimal hashes where `0` and `O` must be unambiguous.
**Why `tabular-nums`:** in a benchmark table, `0.954` and `0.9605` must have their decimal points on the same vertical axis or the reader cannot compare magnitudes by scanning. This is not aesthetics — it is the difference between a table you can read and one you must parse.

**Precision discipline.** Displayed precision is a *property of the artifact*, not a rendering choice. `formatQuantity()` takes precision from the data contract. A value stored as `0.9536` never renders as `0.95` (silently discards information) or `0.95360` (fabricates it).

---

## 5.2 Color system

### 5.2.1 The disjointness rule

**UI color and data color are separate namespaces with no shared values.** No interface element may use a data color; no chart series may use a UI color.

**Why.** Two failure modes this prevents: (a) a user mistaking a chart series for a link or a status; (b) a theme change silently altering the meaning of a published figure. Under this rule, the accent color can be changed tomorrow and every scientific figure remains byte-identical in meaning.

### 5.2.2 UI palette — dark (default)

| Token | Hex | Role | Contrast vs `--bg-base` |
|---|---|---|---|
| `--bg-base` | `#0A0C0E` | Page ground | — |
| `--bg-surface` | `#121518` | Panels, cards | — |
| `--bg-raised` | `#1A1E22` | Popovers, hovered rows | — |
| `--bg-sunken` | `#06080A` | Chart plot areas, code blocks | — |
| `--fg-primary` | `#E8EBED` | Body text | **16.36:1 (AAA)** |
| `--fg-secondary` | `#A0A8AF` | Labels, captions | **8.13:1 (AAA)** |
| `--fg-tertiary` | `#6B747C` | Disabled, axis ticks | **3.6:1 — non-text only** |
| `--border-subtle` | `#1E2328` | Table rules, dividers | — |
| `--border-default` | `#2A3138` | Card borders | — |
| `--border-strong` | `#3D454D` | Focused/active borders | — |
| `--accent` | `#4A9EFF` | Interactive affordance **only** | **7.11:1** |
| `--accent-hover` | `#6BB1FF` | — | 9.30:1 |
| `--focus-ring` | `#7FC4FF` | Keyboard focus | 10.49:1 |

**Why `#0A0C0E` and not pure black.** Pure `#000` against light text produces halation (visual smearing) for many readers, and offers no room for a *sunken* layer beneath surfaces. A near-black with a slight cool cast gives four distinguishable luminance layers while keeping chart plot areas the darkest region — so data is always the brightest thing on screen.

**Why a single blue accent.** One accent means *"interactive"* is learnable in one exposure. Multiple accents force the user to build a color→meaning map. Blue specifically because (a) it is the least likely hue to be confused with a physical measurement (solar/thermal data reads as yellow-red), and (b) it is furthest from the status colors below.


> **CORRECTION 2026-07-23 (Sprint 0).** The contrast ratios in this section were originally hand-computed and eight of nine disagreed with measurement; `--status-open` was overstated (8.4:1 claimed, 7.76:1 actual). All values above are now the output of `web/scripts/check.ts`, which enforces them on every build. See `docs/performance/PERF-0000-baseline.md`.

### 5.2.3 Status palette — deliberately quiet

| Token | Hex | Meaning | Contrast |
|---|---|---|---|
| `--status-pass` | `#3FB950` | Verified / PASS | 7.71:1 |
| `--status-open` | `#D29922` | Open question / unresolved | 7.76:1 |
| `--status-fail` | `#F85149` | FAIL / contradiction | 5.84:1 |
| `--status-info` | `#8B949E` | Neutral annotation | 6.37:1 |

**Why muted and not saturated.** Saturated red/green on a dark ground reads as an *alarm* — an operational-status signal. This platform has no live state; nothing is alarming. These desaturated values read as *classification*, which is what they are. This is a direct expression of P2 (nothing implies live operations).

**Status is never color-alone.** Every status renders as `[icon][TEXT LABEL]` — `✓ PASS`, `! OPEN`, `✕ FAIL`. Color is redundant reinforcement. This satisfies WCAG 1.4.1 and, more importantly, survives grayscale printing into a paper.

### 5.2.4 Data palette — Okabe–Ito

Categorical series use the **Okabe–Ito colorblind-safe qualitative palette** (Okabe & Ito, 2008), the de facto standard in scientific publishing:

```
--data-1: #E69F00  orange
--data-2: #56B4E9  sky blue
--data-3: #009E73  bluish green
--data-4: #F0E442  yellow
--data-5: #0072B2  blue
--data-6: #D55E00  vermillion
--data-7: #CC79A7  reddish purple
```

**Why this and not a bespoke palette.** It is peer-reviewed, safe under deuteranopia/protanopia/tritanopia, and — critically — **recognizable to scientists**, who have seen it in journals for fifteen years. Inventing our own palette would be a purely aesthetic choice with a real accessibility cost. Timelessness over trend.

**Hard cap: 6 series.** `ui-ux-pro-max` flagged ">6 series (visual noise)" as a line-chart contraindication. Enforced in code — `<ScientificChart>` throws in development if given more than 6 series, and offers small-multiples instead.

**Redundant encoding, mandatory.** Per the skill's line-chart note ("differentiate by line style not color alone"), series 1–6 map to fixed dash patterns: `solid, dash-6-3, dot-2-2, dash-10-4, dash-2-2-6-2, dash-14-4`. A figure screenshotted in grayscale remains readable.

### 5.2.5 Sequential colormap

**Viridis**, for every intensity encoding (spectrum heatmap, coverage calendar, solar activity).

**Why viridis and not a "prettier" map.** It is perceptually uniform — equal steps in data produce equal *perceived* steps in color — and monotonic in luminance, so it degrades correctly to grayscale. Jet/rainbow maps create false boundaries at the cyan/yellow transitions, which in a spectrogram would fabricate spectral features that are not in the data. **Using jet here would be a scientific error, not a taste error.**

Divergent data (residuals, Δ-metrics) uses **RdBu**, symmetric about zero, zero pinned to the neutral midpoint.

### 5.2.6 Light theme

Fully specified, not an afterthought — **because reviewers screenshot figures into papers and slides, which are light-background media.** All tokens invert with recomputed contrast; the data palette and viridis are unchanged (they are luminance-safe on both). Toggle persists in `localStorage`, defaults to `prefers-color-scheme`.

---

## 5.3 Spacing, grid, layout

**Base unit 4px.** Scale: `0, 1(4), 2(8), 3(12), 4(16), 5(20), 6(24), 8(32), 10(40), 12(48), 16(64), 20(80), 24(96)`.

**Why 4 and not 8.** Dense data UI needs sub-8px increments — a table cell needs 6px vertical padding, and rounding to 8 makes rows 25% taller, which costs visible rows. 4px is the smallest unit that still constrains.

**Grid.** 12 columns, `--gutter: 24px`, max content width **1440px**, document max width **68ch**.

**Why 1440 and not full-bleed.** Beyond ~1440px, a synchronized light-curve/spectrum stack becomes so wide that the vertical eye-travel between panels exceeds comfortable saccade distance — the user stops perceiving the panels as time-aligned. The alignment *is* the feature; capping width protects it.

**Density modes.** `comfortable` (default) and `compact` (table row height 32→24px), user-togglable, persisted. **Why:** the researcher scanning 400 days and the recruiter reading six cards have opposite density needs, and one default cannot serve both.

---

## 5.4 Elevation — luminance, not shadow

**Rule: elevation is expressed by background luminance step + border, never by drop shadow.**

| Level | Background | Border | Use |
|---|---|---|---|
| 0 | `--bg-base` | none | Page |
| 1 | `--bg-surface` | `--border-subtle` | Cards, panels |
| 2 | `--bg-raised` | `--border-default` | Popovers, dropdowns |
| 3 | `--bg-raised` | `--border-strong` + `0 8px 24px rgba(0,0,0,.6)` | Modals only |

**Why.** On a `#0A0C0E` ground a drop shadow is physically invisible — there is no lighter surface for it to darken. Systems that ship shadows into dark mode are porting a light-mode metaphor that does not survive the transport. Luminance steps are the honest depth cue in a dark UI. Shadow appears at exactly one level (modal) where it must communicate *"this blocks the page."*

**Border radius:** `--radius-sm: 3px`, `--radius-md: 5px`, `--radius-lg: 8px`. Charts and data tables use **`0`**.

**Why square charts.** A rounded corner on a plot area implies the data is clipped by decoration. Scientific figures have square frames — every journal, every plotting library. Rounding them is the single clearest "web designer touched this" tell.

---

## 5.5 Motion

| Token | Value | Use |
|---|---|---|
| `--dur-instant` | 80ms | Hover, focus |
| `--dur-fast` | 150ms | Toggles, tooltips, copy confirm |
| `--dur-base` | 250ms | Panel transitions, disclosure |
| `--dur-slow` | 400ms | Curve draw-on, timeline stagger |
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrances |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Position changes |

### Three motion laws

**L1 — Data marks never animate position.** A point may fade in; it may never *slide* to its value. An animated data point asserts intermediate values that were never measured. This is the most important motion rule in the system and it is what separates scientific software from dashboard software.

**L2 — No animation loops.** Every animation runs once, on a discrete trigger. A perpetual pulse or flow-animation implies ongoing process — a live-telemetry claim (P2 violation). This is why the pipeline diagram draws once and stops.

**L3 — Reduced motion is a hard gate, not a degradation.** `prefers-reduced-motion: reduce` sets all durations to `1ms` globally and renders every draw-on animation in its completed state. No information is delivered only through motion.

---

## 5.6 Charts — scientific visualization principles

Binding rules for every chart in the platform:

1. **Y-axis truncation must be declared.** A non-zero-origin axis renders a break glyph (`⌇`) at the axis root. Silent truncation exaggerates effect size — the most common chart lie.
2. **Gaps are gaps.** Missing data breaks the line. No interpolation, no `connectNulls`. (P6)
3. **Uncertainty is drawn.** Any estimate with a CI renders the CI. A bare point estimate for a model metric is a bug.
4. **No 3D, no dual y-axes, no pie charts.** 3D distorts area judgment; dual axes let the author manufacture any correlation by rescaling; pie charts defeat magnitude comparison. None have a legitimate use here.
5. **Every chart has a `<caption>`, units on axes, and a data-table fallback.**
6. **Canvas rendering** (ECharts) above 500 points; SVG below. 1,440 SVG nodes per light curve would jank on scroll.
7. **Decimation is declared.** When LTTB downsampling is active, the chart footer states `decimated 1440 → 2000 pts (LTTB)`. The user always knows whether they are looking at all the data.

---

## 5.7 Accessibility rules (system-wide)

| Rule | Target |
|---|---|
| Body text contrast | **≥ 7:1 (AAA)** |
| Large text / UI components | ≥ 4.5:1 |
| Focus indicator | 2px `--focus-ring`, 2px offset, **never removed** |
| Color-alone encoding | **Prohibited** — always icon or text redundant |
| Keyboard | 100% of functionality, including all chart zoom/pan |
| Touch targets | ≥ 44×44px |
| Motion | `prefers-reduced-motion` honored globally |
| Charts | data-table equivalent always in DOM (visually hidden until toggled) |
| Headings | strict `h1→h6` order, no skips |
| Landmarks | `header/nav/main/footer` on every page |

**Why AAA for body text.** This is long-form technical reading, often for extended sessions, frequently by people over 40 in variable lighting. AA (4.5:1) is a legal floor; AAA is the correct engineering target for a reading instrument.

---

## 5.8 Token architecture

Three tiers, one direction of dependency:

```
Tier 1 — Primitive   --blue-500: #4A9EFF        (raw values, never used in components)
Tier 2 — Semantic    --accent: var(--blue-500)  (role names, themed)
Tier 3 — Component   --metric-card-bg: var(--bg-surface)
```

**Why three tiers.** Components reference Tier 3 or Tier 2 only. This makes theming a Tier-2 operation — one file changes and the whole system re-themes with zero component edits. A component that references `--blue-500` directly is a lint error.

Delivered as CSS custom properties on `:root` + `[data-theme]`, with a **generated** Tailwind config and **generated** TypeScript types (`ColorToken`, `SpaceToken`). Single source: `tokens/*.json`. **Why generated:** hand-syncing tokens between CSS, Tailwind, and TS is a guaranteed drift source; one generator eliminates the class of bug.

---

# SECTION 6 — COMPONENT LIBRARY

## 6.0 Foundational contracts

Every component in the system builds on three types. These are the spine of the platform.

```ts
/** Where a displayed value came from. P1 is enforced through this type. */
interface ArtifactRef {
  artifact: string;        // repo-relative, e.g. "artifacts/v2/ml/benchmark_results.json"
  pointer?: string;        // RFC-6901 JSON pointer, e.g. "/nowcast/threshold/roc_auc"
  sha256?: string;         // artifact digest at build time
  commit: string;          // git SHA the artifact was read from
  href?: string;           // resolved GitHub permalink
}

/** A measured quantity. Uncertainty travels with it. */
interface Quantity {
  value: number;
  ci95?: readonly [number, number];
  unit?: string;
  n?: number;              // denominator — "424" is meaningless without "/436"
  precision: number;       // significant digits AS STORED; rendering may not exceed
}

/** P3 enforced in the type system: a model metric cannot exist without a CI. */
type ModelMetric = Quantity & { ci95: readonly [number, number] };
```

**Why `ModelMetric` is a distinct type.** P3 says "uncertainty travels with the estimate." A convention would be violated within a month. A type makes `<BenchmarkTable>` *uncompilable* if given a model metric without an interval. **The scientific principle is enforced by the compiler, not by discipline.**

---

## 6.1 `<SourceRef>` — the keystone

**Responsibility.** Render a compact, verifiable pointer from an on-screen value to the committed artifact that produced it. Every other data component composes this.

**Data contract.** `{ ref: ArtifactRef; variant?: 'inline'|'footnote'|'badge'; }`

**Variants.**
- `inline` — superscript numeral, expands on hover/focus into a popover with artifact path, pointer, SHA-7, and a permalink.
- `footnote` — full path + SHA in `--text-xs` mono beneath a block.
- `badge` — a `⛭` glyph for space-constrained contexts (table cells).

**States.** rest · hover (popover, 200ms delay) · focus (popover, immediate) · unresolved (build-time failure — see below).

**Accessibility.** `<button aria-describedby>` opening a popover with `role="dialog"`, focus-trapped, `Esc` to close. The full reference is *also* present as visually-hidden text so screen-reader users are never required to open a popover to learn provenance. Never a `title` attribute (keyboard-inaccessible, no touch support).

**Performance.** Zero runtime cost at rest — the popover is not mounted until first interaction. Refs are resolved at *build* time into a static map; no client-side lookup.

**Reuse strategy.** Required prop on `<MetricCard>`, `<BenchmarkTable>` rows, chart captions, and `<EvidenceBlock>`. **It is impossible to render a pipeline-derived number in this system without composing `<SourceRef>`.**

**Future extensibility.** `ArtifactRef.pointer` already supports JSON-pointer depth, so a future per-cell drill-down needs no interface change. Adding a `doi` field later is additive.

> **Enforcement.** A build-time codemod scans for numeric literals in JSX outside the `formatQuantity()` path and fails CI. This is the mechanism by which P1 stops being a promise.

---

## 6.2 `<MetricCard>`

**Responsibility.** Present one measured quantity with its denominator, uncertainty, and source. Nothing else.

**Data contract.**
```ts
{
  label: string;
  quantity: Quantity;
  source: ArtifactRef;           // REQUIRED — no default, no optional
  trend?: never;                 // deliberately impossible
  context?: string;              // e.g. "of 436 archive days"
  href?: string;                 // deep link to the owning surface
}
```

**Why `trend?: never`.** Every dashboard component library ships a trend arrow. A trend on a *frozen* dataset is meaningless — nothing changes. Typing it as `never` makes the wrong thing unbuildable rather than merely discouraged. **This one line is the clearest statement of what this platform is not.**

**Variants.** `default` (32px value) · `headline` (40px, Overview only) · `compact` (inline, 18px, for panel headers) · `ratio` (renders `424 / 436` with the denominator at 60% size and `--fg-secondary`).

**States.** rest · hover (border → `--border-strong`, source ref revealed) · focus-visible · linked (cursor pointer + affordance chevron) · **`unsourced` → throws in dev, fails build in CI.**

**Accessibility.** `<article>` with `<dl>/<dt>/<dd>`. `aria-label` includes the full quantity with unit and CI spoken naturally: *"Event recall, 0.927, 95% confidence interval 0.875 to 0.976."* Not a link unless `href` is present — non-interactive cards must not appear focusable.

**Performance.** Pure server component; zero client JS unless `href` is set. Renders in the static payload.

**Reuse strategy.** Used on all six surfaces. It is the only sanctioned way to display a single number at display size.

**Future extensibility.** When a second dataset version exists, a `comparison?: { quantity, version }` prop renders a *versioned delta with its own CI* — the honest form of a "trend," available only when two frozen versions genuinely exist.

---

## 6.3 `<TimeAxisController>` — headless

**Responsibility.** Own the shared time domain for Data's synchronized panels. Renders nothing.

**Why it exists as a component.** The single most valuable scientific affordance in the platform is that the light curve, spectrum, and GTI strip share one x-axis exactly. If each panel owned its own zoom state, they would drift out of sync under floating-point accumulation and async data arrival — and a *silently misaligned* spectrum against a light curve is a scientific falsehood rendered as a picture. Centralizing the domain makes desynchronization structurally impossible.

**Data contract.**
```ts
{
  domain: [Date, Date];              // full day extent
  view: [Date, Date];                // current zoom
  setView(next: [Date, Date]): void;
  cursor: Date | null;               // shared crosshair
  selection: Date | null;            // selected minute → drives spectrum profile
  gaps: Array<[Date, Date]>;         // non-GTI regions, shared by all panels
}
```

**States.** full · zoomed · brushing · cursor-active · selection-active.

**Accessibility.** Exposes keyboard handlers panels bind to: `←/→` pan 5%, `Shift+←/→` pan 25%, `+/−` zoom, `0` reset, `Home/End` jump to extent. Announces domain changes via a polite live region: *"View: 14:20 to 15:40 UTC."*

**Performance.** Zustand store with transient updates — cursor movement at 60Hz must **not** re-render React. Panels subscribe via `useStore.subscribe` and write directly to canvas. Domain changes (rare) go through React; cursor changes (constant) do not.

**Reuse strategy.** Any future time-aligned panel (HEL1OS CZT/CdTe spectra, GOES overlay) joins by consuming this context — zero changes to existing panels.

**Future extensibility.** `domain` is not day-limited; a future multi-day view requires only a different initial domain.

---

## 6.4 `<ScientificChart>` — the base primitive

**Responsibility.** Enforce §5.6 for every chart. Owns axes, gap handling, decimation disclosure, caption, legend, data-table fallback, and export. Chart *types* compose it.

**Data contract.**
```ts
{
  series: Series[];                  // max 6 — throws in dev beyond
  xAxis: AxisSpec;                   // { label, unit, type, zeroOrigin }
  yAxis: AxisSpec;
  caption: string;                   // REQUIRED
  source: ArtifactRef;               // REQUIRED
  decimation?: { from: number; to: number; method: 'LTTB' };
  gaps?: Array<[number, number]>;
}
```

**Variants.** `line` · `step` · `scatter` · `heatmap` · `interval` · `curve` (ROC/PR) · `errorbar`.

**States.** loading (skeleton at final dimensions — reserved box, zero CLS) · ready · empty (renders axes with an explicit reason) · error (falls back to the table, which already exists in the DOM) · exporting.

**Accessibility.** `role="img"` + `aria-label` summarizing shape and range. A "View as data" toggle exposes the `<table>` that is *always* in the DOM (visually hidden) — so screen-reader users and the error fallback share one code path, guaranteeing the fallback is never stale.

**Performance constraints.** Canvas above 500 points. `ResizeObserver` throttled to 100ms. Chart bundle lazy-loaded per route. **Budget: ≤ 16ms per frame during brush-zoom; ≤ 500ms initial render after data arrival.**

**Reuse strategy.** No chart in the platform is constructed directly against ECharts. Every chart composes this. **Why:** it makes the scientific rules structural — a developer cannot accidentally ship a chart with a truncated axis and no break glyph, because they never touch the axis config directly.

**Future extensibility.** ECharts sits behind an adapter interface. Swapping the renderer (e.g. to a WebGL backend for full-resolution spectra) is one file.

---

## 6.5 `<LightCurveViewer>`

**Responsibility.** Render T1 `rate_total` at minute resolution for one day, with GTI-excluded regions broken, background level marked, and detected M/X events annotated.

**Data contract.** `{ date: string; detector: 'SDD1'|'SDD2'; series: {t: number[]; rate: Float32Array; live_time: Float32Array}; gti: Interval[]; events?: FlareEvent[]; }`

**Variants.** `full` (Data page, 320px) · `strip` (80px, no annotations, for the coverage rail) · `comparison` (two detectors overlaid — solid/dashed per §5.2.4).

**States.** loading · ready · `no-science-products` (detector inactive — renders the GTI strip alone with the F-12 explanation) · `all-nan` (live_time = 0 across the day — states the reason, does not render an empty box).

**Accessibility.** Data table gives per-minute rate with quality flags, paginated at 60 rows. Keyboard cursor stepping announces value + time.

**Performance.** LTTB to ≤ 2,000 points; footer declares it. `Float32Array` transferred as binary, never JSON floats — **4 bytes vs ~18 bytes per value; for 1,440 minutes that is 5.7KB vs 26KB, and it matters far more when zoomed views request finer data.**

**Reuse strategy.** The `strip` variant makes it the row renderer inside a future multi-day browser at zero extra cost.

**Future extensibility.** `series` is an array of channels, not a single vector — a GOES overlay (§14) becomes a second series with no interface change. This was designed in now specifically so the planned GOES cross-validation requires no redesign.

---

## 6.6 `<SpectrumViewer>`

**Responsibility.** Render T2 as a channel × time heatmap, plus a single-minute channel profile on selection.

**Data contract.**
```ts
{
  date: string;
  channelSpace: 'SOLEXS_PI_340' | 'HEL1OS_CZT_PHA_341' | 'HEL1OS_CDTE_PHA_511';
  bins: { t: number[]; channels: number[]; values: Float32Array };  // row-major
  selection: Date | null;
}
```

**Why `channelSpace` is a required discriminant.** The three spaces are physically incommensurable (F-11). Making it a required literal union means a component *cannot* be handed a mixed-space array without a type error, and the axis label is derived from it — so a CZT spectrum can never be mislabeled as SoLEXS PI. **The most dangerous scientific error available in this dataset is made a compile error.**

**Variants.** `heatmap` (default) · `profile` (single-minute line, channel vs counts) · `bands` (5 aggregated bands — the mobile and low-bandwidth degradation).

**States.** loading (determinate progress — this is the heavy fetch) · ready · `no-spectra` · `reduced` (mobile band view, with an explicit "full 340-channel view available on wider screens" note).

**Accessibility.** Per the skill's heatmap guidance (**grade B**, mitigations mandatory): numeric readout on hover **and** on keyboard focus; legend with labeled scale ticks; viridis for colorblind safety. Keyboard navigates the matrix cell-by-cell with `aria-live` announcement of `channel, time, value`. The data-table fallback presents band aggregates, not 340×1440 cells — an unusable table is not an accessible one.

**Performance constraints — the platform's hardest.** Raw is 340 × 1,440 = **489,600 floats/day (1.9MB as Float32, ~9MB as JSON)**. Never shipped. Server pre-aggregates to **≤ 60 time bins × 340 channels ≈ 20,400 floats ≈ 80KB**, refining on zoom (request finer bins only for the visible window). Rendered to an `OffscreenCanvas` in a worker as an ImageBitmap; the main thread only composites. **Budget: ≤ 100KB per view, ≤ 300ms to first paint.**

**Reuse strategy.** Channel-space-agnostic by construction — the same component serves all three instruments.

**Future extensibility.** When an RMF is acquired (§14), a `calibration?: RMFRef` prop switches the y-axis from ordinal channel to keV. **The axis label is already derived rather than hardcoded, so this is an additive change with no restructuring.** This is the concrete meaning of "future improvements fit without redesign."

---

## 6.7 `<CoverageCalendar>`

**Responsibility.** Show data availability and daily activity across 2024-02-01 → 2026-06-17; serve as the primary date selector.

**Data contract.** `{ range: [string, string]; days: Map<string, {available: boolean; maxRate?: number; reason?: GapReason}>; selected?: string; onSelect(d): void }`

**Variants.** `year` (full range, month columns) · `month` (single month, larger cells) · `rail` (vertical compact, sidebar).

**States.** ready · `gap` cell (diagonal hatch + `reason`) · selected · hovered · out-of-range.

**Why a hatch and not a color.** A gray cell for "no data" competes with the low end of viridis — the user cannot distinguish *"quiet day"* from *"no observation."* Those are radically different scientific statements. A **texture** is orthogonal to the color scale and unambiguous at any zoom. (P6, made visual.)

**Accessibility.** A grid with roving tabindex; arrow keys navigate by day, `PgUp/PgDn` by month. Each cell announces `date, availability, activity level, reason if absent`. Never color-only — activity is also in the cell's `aria-label`.

**Performance.** ~866 cells → single SVG, ≤ 30KB, no per-cell React nodes (rendered as one path set with delegated pointer events). Reason: 866 React elements with handlers costs ~40ms of hydration for zero benefit.

**Future extensibility.** `days` is keyed by date with an open value shape — adding per-detector coverage layers or a GOES-availability overlay requires no signature change.

---

## 6.8 Validation narrative components

### `<ContradictionTimeline>`
**Responsibility.** Render the chronological sequence of a contradiction's discovery and resolution as an ordered, navigable structure.
**Data contract.** `{ id: string; events: Array<{ ts: string; actor: 'spec'|'implementation'|'owner'; kind: 'assumption'|'observation'|'measurement'|'ruling'; body: string; ref?: ArtifactRef }> }`
**Why `actor` is typed.** The scientific value of this record is that it distinguishes *what the spec assumed*, *what execution observed*, and *what the owner ruled*. Encoding actor as data (not as prose formatting) lets the UI make that distinction visually consistent across all six contradictions and makes it machine-queryable via the API.
**States.** collapsed (summary) · expanded · focused-event (deep-linked).
**A11y.** `<ol>`; each event `<li>` with a heading; actor rendered as text label, not color.
**Performance.** Static; ≤ 5KB per contradiction.
**Reuse.** Also renders the r0→r6 spec-revision timeline with a different actor set.

### `<EvidenceBlock>`
**Responsibility.** Present the *measured* values that falsified an assumption — never a paraphrase.
**Data contract.** `{ claim: string; measurements: Array<{ label: string; quantity: Quantity; source: ArtifactRef }>; verdict: 'supports'|'falsifies' }`
**Why measurements are structured, not markdown.** If evidence were prose, the site would be restating numbers by hand and P1 would be unenforceable. Structured measurement + `ArtifactRef` means the evidence rendered on screen is the evidence in the artifact, checked by CI.
**Variants.** `inline` · `expanded` (with raw value dump).
**A11y.** `<figure>` + `<figcaption>`; verdict as text.
**Extensibility.** `verdict` is a union — adding `'inconclusive'` for a future open question is additive.

### `<DecisionBlock>`
**Responsibility.** Render the owner's ruling **including rejected alternatives**.
**Data contract.** `{ ruling: string; rationale: string; rejected: Array<{ proposal: string; reason: string }>; revision: string }`
**Why `rejected` is a required array.** The r5 amendment — where the owner declined the implementer's proposal to encode statistics into the contract — is among the strongest credibility signals the project has. A component that only shows what was decided would discard it. **Making rejection a first-class field means the interface cannot hide the road not taken.**

### `<SpecDiff>`
**Responsibility.** Show the exact contract text before and after a revision.
**Variants.** `unified` (default) · `split` (≥1024px only).
**A11y.** `<ins>`/`<del>` with `+`/`−` text markers — never color-only. Line numbers in `aria-label`.
**Performance.** Diff computed at **build** time, shipped as tokens. Shipping a diff library to the client for static content would be ~40KB for zero benefit.

---

## 6.9 `<BenchmarkTable>` + `<CIBar>`

**Responsibility.** Present 8 models × 2 tasks with full uncertainty, and make "statistically indistinguishable" *unmissable*.

**Data contract.**
```ts
{
  task: 'nowcast' | 'prediction';
  rows: Array<{
    model: string;
    rocAuc: ModelMetric;              // CI structurally required
    eventRecall: ModelMetric;
    falseRuns: Quantity;
    precision?: Quantity;
    brier?: Quantity;
    latencyUs?: Quantity;
    verdict: 'baseline' | 'indistinguishable' | 'significantly-better' | 'significantly-worse';
  }>;
  paired?: { model: string; delta: ModelMetric; verdict: string };
  source: ArtifactRef;
}
```

**Why `verdict` is data, not computed in the view.** The adjudication (LightGBM at −0.0229 [−0.0445, −0.0004] is *significantly worse*) is a scientific conclusion recorded in `benchmark_results.json` under a pre-registered protocol. If the UI recomputed it, the site could disagree with the paper. The view renders the recorded verdict and nothing else.

**`<CIBar>`.** Horizontal interval with a point marker, numeric label always rendered as text, and a zero/reference line where a paired delta is shown. **Overlapping intervals are additionally labeled in text** — "indistinguishable" is never left to be inferred from visual overlap, because visual overlap is exactly what readers misjudge.

**States.** collapsed (headline metrics) · expanded row (confusion matrix, all metrics) · sorted · task-switched (selection preserved).

**A11y.** `<caption>`, `<th scope="col">`, `<th scope="row">`. Verdict as text in its own column. Sortable headers are buttons with `aria-sort`. **Horizontal overflow scrolls inside the table container — the page body never scrolls sideways.**

**Performance.** 16 rows; trivially static. Confusion matrices lazy-render on row expand.

**Extensibility.** `rows` is open — a future model appended to the artifact appears automatically. `task` union extends to `'onset-latency'` (§14) with no structural change, which matters because Conclusion 5 names onset latency as the next primary metric.

---

## 6.10 `<ProvenanceExplorer>`

**Responsibility.** Trace any canonical row back to its source file, digest, parser version, and applied assumptions.

**Data contract.** `{ scope: {date, detector, table}; records: Array<{ sourceFile, sha256, archiveVersion, parserVersion, assumptions: string[], rowCount, resolutionRule?: 'R1'|'R2'|'R3' }> }`

**Variants.** `summary` (counts + versions) · `detailed` (per source file) · `chain` (raw FITS → parsed → resolved → canonical, as a directed path).

**States.** ready · `multi-version` (highlights where version resolution applied, with the winning rule) · `conflict` (shows both candidates and which won — 48,604 such conflicts exist and the interface must be able to show one).

**A11y.** Definition list per record; SHA-256 in mono with `slashed-zero`, copy button, and a screen-reader-friendly truncation (`aria-label` gives the full digest, visible text shows 7 chars).

**Performance.** Fetched on demand per day; ≤ 20KB.

**Reuse.** Embedded in Data (per day) and Build (per table).

**Extensibility.** `assumptions` is a string array keyed to rule IDs (F-01…F-20) — new fail-loud rules appear without a schema change.

---

## 6.11 `<SunHero>`

**Responsibility.** Visualize archive coverage and daily activity across 424 days on a spherical projection, and act as the coarse date entry point.

**Why it is permitted under P5.** It encodes two real variables (coverage presence, daily max rate) and is interactive (selects a date). If either were removed it would become decoration and must then be deleted. **This is the only WebGL element in the platform, and it exists on exactly one page.**

**Data contract.** `{ days: Array<{date: string; available: boolean; activity: number}>; onSelect(date): void }` — 424 records, ~8KB.

**Variants.** `webgl` · `static` (SVG fallback, identical information, identical interactivity).

**States.** loading · ready · reduced-motion (no rotation, full interactivity) · unsupported (static SVG).

**A11y.** `role="img"` with a descriptive label; an adjacent visually-hidden `<table>` of monthly coverage. **The canvas is never the sole path to the information** — the same date selection is reachable via the Data page calendar.

**Performance.** ≤ 120KB gz, lazy-loaded after LCP, excluded from the critical path. Single sphere mesh, one shader, one texture built from the 424 activity values. Frame budget 16ms; **pauses rendering entirely when off-screen** (`IntersectionObserver`) and on `document.hidden`. No post-processing, no bloom, no particles.

**Extensibility.** Deliberately none. It is a leaf component with a locked scope, because this is the single element most likely to accrete decorative features under future temptation.

---

## 6.12 Secondary components

| Component | Responsibility | Key constraint |
|---|---|---|
| `<GtiStrip>` | T6 intervals aligned to shared time axis | Renders inclusive endpoints per r2; tooltip states the convention explicitly |
| `<DataTable>` | Generic sortable/virtualized table | Virtualizes above 100 rows; sticky header; tabular-nums enforced |
| `<CommandBlock>` | Copyable shell command | Never auto-runs; copy label names the command |
| `<StatusBadge>` | PASS/OPEN/FAIL | Icon + text mandatory; color redundant |
| `<RuleBadge>` | F-01…F-20 reference | Tooltip carries the rule's verbatim text from the spec |
| `<PipelineDiagram>` | Architecture flow | Draws once (L2); DOM order is an `<ol>` of stages |
| `<DocRenderer>` | Long-form markdown | Serif, 68ch, auto heading anchors, no raw HTML |
| `<ApiExplorer>` | OpenAPI browse + try | Lazy (~400KB); raw spec always available as fallback |
| `<DatasetVersionChip>` | Global version + hash | Present in the header on every page, always |
| `<CommandPalette>` | ⌘K navigation | Purely additive; every destination reachable without it |
| `<Disclosure>` | Progressive detail | `aria-expanded`; content in DOM when open only |
| `<EmptyState>` | Absence with a reason | **`reason` is a required prop** — an empty state without an explanation is a bug |

---

# SECTION 7 — VISUAL LANGUAGE

## 7.1 Defining the four target adjectives operationally

| Adjective | Operational definition | Concrete rule |
|---|---|---|
| **Professional** | Nothing is ambiguous about what a thing is or does | One accent color; one meaning per color; no icon without a label |
| **Scientific** | Values, units, denominators, and uncertainty are always present | No bare numbers; no bare percentages; CIs mandatory on estimates |
| **Credible** | Every claim is one click from its evidence | `<SourceRef>` compulsory; contradictions public; limitations a first-class surface |
| **Mission-grade** | High information density, legible under time pressure, degrades safely | Compact mode; keyboard-complete; every failure state names its cause |

## 7.2 The affiliation firewall

This is the highest-risk area in the entire product. The platform must look like serious research software **without any visual claim of institutional affiliation.**

**Prohibited absolutely:**
- ISRO, NASA, ESA logos, wordmarks, insignia, or derivative marks
- Mission-patch-style circular emblems (the visual idiom of official mission branding)
- Official mission photography, ISRO imagery, or agency press assets
- Government-style seals, badges, or "authorized" iconography
- Institutional color schemes recognizable as agency branding
- The word "official," "operational," "authorized," "certified", or "mission control" in any form

**Required, on every page:**
- Footer: **"AdityaNet is an independent research project. Not affiliated with, endorsed by, or operated by ISRO or any space agency. Built on publicly available Aditya-L1 archive data from ISSDC."**
- Overview identity block carries the independence statement **above the fold**, not in a footer.
- Any reference to Aditya-L1 is phrased as a *data source*, never as a partnership.

**Why this is stricter than legally necessary.** The credibility strategy is total honesty. A visual near-miss on official branding would poison the one asset the project has. **The cost of under-claiming is zero; the cost of over-claiming is the entire project.**

## 7.3 Banned lexicon (enforced by lint)

A CI check greps the rendered content for these terms:

`live` · `real-time` · `realtime` · `streaming` · `monitoring` · `alert` · `now` (as a temporal claim) · `current conditions` · `mission control` · `operational status` · `AI-powered` · `intelligent` · `smart` · `revolutionary` · `cutting-edge` · `state-of-the-art` · `seamless` · `powerful` · `robust` (as marketing) · `predicts the future`

**Approved replacements:** `archived`, `as of <date>`, `historical`, `reprocessed`, `detected in archive`, `evaluated`, `measured`.

**Why a lint rule and not a style guide.** Marketing vocabulary re-enters a codebase through copy edits months later, when no one remembers the rule. A failing build remembers.

## 7.4 Wordmark and identity

**Wordmark:** `AdityaNet` set in IBM Plex Sans 600, `-0.02em` tracking, with `Net` in `--fg-secondary` — a typographic distinction, not a logo.

**Why no logo.** A custom mark for an independent research project is the single most reliable portfolio tell — it signals that brand identity was prioritized over content. Wordmark-only is what actual research software does (Astropy, TOPCAT, HEASoft, SunPy). **The absence of a logo is itself a credibility signal.**

**Favicon:** the wordmark's `A` in Plex Sans on `--bg-base`. No emblem, no sun icon.

## 7.5 Imagery policy

**There is no photography anywhere in this platform.** No stock space imagery, no rendered spacecraft, no solar photography from other missions.

**Why.** Every image on this site must be *generated from the archive*. A photograph of the Sun taken by SDO on a page about Aditya-L1 SoLEXS data is a category error dressed as illustration — the visitor cannot tell which pixels are data. The only visual content is: charts derived from T1–T7, the coverage visualization, and the pipeline diagram. **If it isn't measured, it isn't shown.**

## 7.6 What "not Dribbble" means concretely

| Rejected | Why |
|---|---|
| Glassmorphism / frosted panels | Reduces text contrast for a decorative effect; fails P5 and AAA |
| Gradient text and gradient borders | Non-semantic color; breaks the disjointness rule |
| Animated gradient backgrounds | Perpetual motion → implies live state (L2) |
| Rounded chart corners | Implies decorative clipping of data |
| Hero video / parallax scrolling | Zero information, high cost, motion-sickness risk |
| Bento-grid layouts | Optimizes for screenshot appeal, not scanning; forces arbitrary card sizes |
| Emoji in UI | Renders differently per platform; unprofessional in a scientific register |
| Neon glow / cyberpunk accents | Signals "space aesthetic," which is exactly the impersonation risk |
| Dark-mode-only | Excludes light-media use (papers, slides, printing) |
| Number count-up animations | **Animates a measured value through false intermediate states — violates L1 and P1** |

---

# SECTION 8 — INTERACTION DESIGN

## 8.1 Scrolling

**Native scroll only.** No scroll-jacking, no snap points, no scroll-linked camera moves.

**Why.** Scroll-linked animation makes reading speed a function of the designer's timing curve rather than the reader's comprehension. For a document a reviewer needs to read carefully, that is hostile.

**Permitted scroll behavior:** `IntersectionObserver`-triggered one-shot reveals (ROC curve draw, pipeline path draw), sticky panel headers, sticky table headers, and `scroll-margin-top` on anchors so deep links land below the sticky header.

## 8.2 Hover

Hover reveals **detail**, never **function**. Every hover-revealed affordance is also reachable by keyboard focus and is visible on touch devices (where hover does not exist).

| Element | Hover response |
|---|---|
| MetricCard | Border strengthens; `<SourceRef>` fades in (80ms) |
| Chart | Crosshair + exact value + timestamp readout |
| Heatmap cell | Numeric value + channel + time (per skill's mandatory heatmap mitigation) |
| Calendar cell | Date, activity, availability, gap reason |
| Table row | Background → `--bg-raised` |
| SourceRef | Popover after 200ms delay |

**Why the 200ms popover delay.** Instant popovers fire during incidental cursor transit across a dense page, creating flicker. 200ms is below conscious perception for intentional hover and above the duration of a pass-through.

## 8.3 Keyboard model

**Global**

| Key | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Command palette |
| `g` then `o/v/d/f/p/b` | Go to Overview / Validation / Data / Findings / Pipeline / Build |
| `/` | Focus search |
| `?` | Keyboard shortcut reference |
| `Esc` | Close popover/modal/palette |
| `Tab` / `Shift+Tab` | Focus traversal |

**Why `g`-prefixed sequences.** They do not collide with browser or OS shortcuts, they are learnable, and they are the established convention in developer tools (Gmail, GitHub, Linear). Using an established convention beats inventing one.

**Data page**

| Key | Action |
|---|---|
| `←/→` | Previous/next day |
| `Shift+←/→` | Pan view 25% |
| `+/−` | Zoom time axis |
| `0` | Reset zoom |
| `Home/End` | Jump to day start/end |
| `↑/↓` | Move channel selection (spectrum) |
| `Enter` | Select minute → spectrum profile |
| `t` | Toggle "view as data" |

**Findings page:** `1`–`8` toggle model series on ROC/PR; `n`/`p` switch task.

**Every shortcut has a discoverable equivalent in the UI.** Shortcuts accelerate; they never gate.

## 8.4 Search

**Scope:** dates, contradiction IDs and titles, findings, fail-loud rules (F-01…F-20), API endpoints, metric names, glossary terms.

**Implementation:** a **build-time static index** (~40KB), queried client-side with a small trigram matcher. **Why not a search service:** the corpus is small, fixed, and public. Running Algolia/Elasticsearch for ~2,000 documents would be infrastructure theater — the exact enterprise-theater smell this spec is meant to avoid.

**Behavior:** results grouped by surface, keyboard-navigable, `Enter` navigates, each result shows its surface and a matched-context snippet. Empty query shows recent + suggested entry points. **No results** → shows the searchable scope, so the user learns what the index covers rather than guessing.

## 8.5 Filtering

Filters exist on exactly three surfaces: Data (date range, detector, quality), Findings (task, model), Validation (severity, status).

**Rules:**
- Filter state lives in the **URL** (`?detector=SDD1&from=2024-05-01`). **Why:** a reviewer must be able to send a colleague a link to exactly what they are looking at. Any state not in the URL is state that cannot be cited.
- Active filters render as removable chips with the result count.
- Zero results state the *reason* and offer the nearest non-empty filter.
- No filter ever silently excludes data — the count of excluded records is always displayed.

## 8.6 Progressive disclosure

Three levels, consistent across all surfaces:

**L1 — Claim.** The headline statement or number. *"ML provides no operational benefit."*
**L2 — Evidence.** The measurements supporting it. *"Threshold 0.954 AUC / 15 false runs vs RF 0.966 / 61 false runs; paired Δ +0.0076 [+0.0032, +0.0123]."*
**L3 — Artifact.** The committed file, pointer, and commit SHA.

**Rule: L1 → L3 is reachable in at most two interactions from anywhere.** This is the platform's core UX metric and it is testable — an automated test asserts that every rendered claim has a path of length ≤ 2 to its artifact.

**Anti-pattern explicitly rejected:** hiding L2 behind a modal. Modals break the reading flow and cannot be linked. Evidence expands **in place**, via `<Disclosure>`, and every disclosure has its own anchor.

## 8.7 Micro-interactions (exhaustive)

The complete list. Anything not here does not exist.

| Interaction | Response | Duration |
|---|---|---|
| Button press | Background shift, no scale transform | 80ms |
| Copy to clipboard | Icon → checkmark, label announces "Copied" | 150ms, 1.5s hold |
| Disclosure toggle | Height auto-transition + chevron rotate | 250ms |
| Tab switch | Indicator slides, content cross-fades | 150ms |
| Chart brush | Live selection rectangle, no easing (must track the pointer exactly) | 0ms |
| Zoom commit | Axis interpolates; **data marks do not translate** (L1) | 150ms |
| Route change | Content fades; header/nav persist | 120ms |
| Toast | Slide up 8px + fade | 200ms |
| Focus | Ring appears immediately | 0ms |

**Why button press has no scale transform.** A scaling button is the canonical "designed" micro-interaction and it degrades legibility of the label mid-press. It is decoration in the shape of feedback.

## 8.8 Scientific storytelling

The platform tells one story, but only where the story is *true*, and always in the same structure:

> **Claim → Evidence → Method → Limitation**

Applied literally on each surface: Overview (arc → metrics → finding → limitation link) · Validation (assumption → measurement → ruling → what remains open) · Findings (conclusion → benchmark → protocol → limitations) · Data (value → provenance → parser assumptions → coverage gaps).

**The two structural rules that make this honest:**

1. **The limitation is never optional and never last-in-tab-order.** Every claim surface links to its limitations at the same visual weight as its evidence.
2. **Negative results are presented in the same visual treatment as positive ones.** The spectral null (+0.0033) gets the same card size, the same chart, and the same prominence as the nowcast result. **A design that visually de-emphasizes an inconvenient finding is a dishonest design**, regardless of what the text says.

---

# SELF-REVIEW — Part 2

Reviewing Sections 5–8 as a hostile Staff Engineer looking specifically for student-project tells and unforced errors.

### Confirmed problems and corrections

**1. Three font families is one too many to defend on payload alone.**
The semantic argument (serif = argument, sans = interface, mono = measurement) is genuinely good, but Plex Serif is used on *one* surface. **Correction:** Serif is loaded **only on the Validation detail route**, via a route-scoped `@font-face` — not in the global bundle. If measured usage after Sprint 5 shows it does not improve the reading experience, it is cut and the system falls back to two families. Flagged for review at implementation, not defended indefinitely.

**2. `<SunHero>` remains the highest-risk element in the product.**
It is justified on paper (encodes coverage + activity, is interactive). But it is *also* the element a student project would build first and love most. **Correction — a kill criterion, committed now:** if, at Sprint 4 review, the static SVG fallback conveys the same information at equal clarity, **the WebGL version is deleted.** The fallback must be built first, and the WebGL version must earn its 120KB against it. A feature with a pre-committed kill criterion is an engineering decision; one without is an indulgence.

**3. "Command palette" risks being cargo-culted from Linear.**
Justified only because the corpus is genuinely navigable (866 dates, 6 contradictions, 20 rules, ~15 endpoints). **Correction:** deferred to Sprint 8+, explicitly *after* all six surfaces work without it. If it ships before the content does, it is theater.

**4. The banned-lexicon lint could produce false positives** ("now" appears legitimately in prose; "monitoring" appears in quoted source material). **Correction:** the rule operates on *rendered user-facing copy* with an explicit allowlist for quoted archive documentation, and blocks only on the high-signal terms (`real-time`, `live`, `AI-powered`, `mission control`, `official`). The rest are warnings. A lint rule everyone disables is worse than no lint rule.

**5. Two type scales invites inconsistency.** Mitigated by making them non-overlapping token namespaces (`--text-*` vs `--doc-*`) and lint-forbidding `--doc-*` outside `<DocRenderer>`.

**6. I specified `precision` on `Quantity` but not a rounding policy for derived display** (e.g. a percentage computed from a ratio). **Correction:** derived values are computed **at build time into the artifact**, never in the view. The frontend performs no arithmetic on measurements. This closes a real P1 hole — a number computed in JSX has no `ArtifactRef`.

### Remaining tells I am accepting, with reasons

- **Dark default.** A tell in the wrong hands, but correct here: luminance-encoded scientific imagery reads better on dark grounds, and this is the convention of DS9, TOPCAT, and every spectrogram tool. Mitigated by shipping a *complete* light theme, which is what distinguishes a considered choice from an aesthetic default.
- **Density toggle.** Slightly more surface than strictly needed, but justified by the genuinely opposed needs of the recruiter and the researcher — two personas, one screen.

### Verdict on Part 2

The design system's load-bearing idea — **epistemic role determines type, color, and motion** — is defensible in front of any reviewer, and the enforcement mechanisms (`source` required, `trend?: never`, `ModelMetric` requiring a CI, `channelSpace` as a required discriminant, build-time arithmetic) convert stated principles into compiler errors. That conversion is the difference between a design document and a design system.

---

**End of Part 2 (Sections 5–8).**

Next: **Part 3 — Sections 9–13** (Data Architecture, API Specification, Frontend Architecture, Quality Standards, Deployment), then **Part 4 — Sections 14–17** (Roadmap, Master Implementation Plan, Critical Design Review, Final Verdict). Implementation Mode begins only after Part 4 is complete, as you specified.

Say **continue** for Part 3.

---

# ADITYANET WEB PLATFORM v1.0 — PRODUCT SPECIFICATION
## Part 3 of 4 · Sections 9–13

---

# SECTION 9 — DATA ARCHITECTURE

## 9.0 The decision that determines everything else

Before choosing a data-loading strategy I asked one question: **how much of this platform's content is actually dynamic?**

| Content | Changes at runtime? |
|---|---|
| Canonical tables T1–T7 | No — frozen, hash `43fd0e22…` |
| Validation record (6 contradictions, r0→r6) | No — historical |
| Benchmark results, ablations, CIs | No — test set opened once |
| Provenance (5,199 records) | No |
| Coverage (424/436 days, 389/391 orbits) | No |
| User state | **None exists** — read-only, no auth |

**Nothing is dynamic. Every possible response is enumerable and pre-computable.**

### Architectural conclusion: there is no runtime server.

> ### ▲ REVISION TO PART 1
> Part 1 §4 specified `GET /api/v1/...` endpoints implying a FastAPI runtime. **The endpoint design survives unchanged; the runtime does not.** Every one of those URLs is served as a pre-generated, immutable JSON document from a CDN. This is a strong-reason revision under your instruction, justified below.

**Why this?** The API's entire response space is finite and known at build time. Pre-computing it converts an availability problem into a file-copy problem.

**Why not the simpler alternative?** A server *is* the conventional choice, but here it is not simpler — it is strictly more complex for identical output. A FastAPI service would add: a second language runtime in CI, container builds, a deploy target, cold-start latency, uptime risk, health checks, rate limiting, an ops on-call surface, and recurring cost — **to serve bytes that are byte-identical on every request forever.** The simpler alternative is the static one.

**What future problem does it solve?** Longevity. A research artifact should still work in ten years. A folder of files on any static host will. A Python service pinned to a 2026 dependency tree will not. It also makes the API *itself* reproducible: every response is a committed, hashed artifact, so "the API returned X" is a verifiable claim rather than a runtime event.

**What complexity does it intentionally avoid?** Servers, containers, orchestration, database, cache layer, connection pooling, autoscaling, secrets management, and the entire observability stack those require.

**What we give up, stated honestly:**
- Arbitrary query parameters (`?bins=137`). Mitigated by a fixed enum of bin levels plus shipping full-resolution data for local rebinning (§9.3).
- Server-side search. Mitigated by a 40KB static index (§8.4).
- Server-side aggregation across arbitrary date ranges. **Accepted** — deferred to §14 as a genuine future need with a defined escape hatch (§9.7).

---

## 9.1 The data pipeline: three stages, one direction

```
STAGE 1 — SCIENCE (local, authoritative, ~94 min)
  raw FITS → parsers → version resolution → canonical parquet
  output: AdityaNet_v2_dataset_r1   sha256 43fd0e22…   597 MB
  ↓  READ-ONLY BOUNDARY  ────────────────────────────────────
STAGE 2 — DERIVATION (local, deterministic, ~6 min)
  scripts/web/derive.py  reads frozen parquet + artifacts/
  output: web-artifacts-r1/         sha256 <pinned>     ~150 MB
  ↓  PUBLISHED AS A HASHED RELEASE ASSET ────────────────────
STAGE 3 — PRESENTATION (CI, ~5 min)
  Next.js static export consumes web-artifacts-r1
  output: out/                      immutable, CDN-hosted
```

**The read-only boundary is enforced, not asserted.** `derive.py` opens the dataset directory with `os.open(..., O_RDONLY)` and the CI job mounts it read-only; a write attempt raises. A test asserts the dataset hash is unchanged after derivation runs. This is the mechanized form of your constraint *"ML/web code MUST NOT modify raw measurements, canonical tables, or provenance."*

**Why Stage 2 exists as a separate stage.** CI cannot run Stage 1 — it requires the 30GB raw archive and 94 minutes. But CI *must* be able to rebuild the site deterministically. Splitting derivation out and publishing its output as a **hash-pinned release asset** gives CI a reproducible input without the archive.

**The pin is the traceability link:**

```json
// web/artifacts.lock.json  — committed
{
  "dataset_version": "r1",
  "dataset_sha256": "43fd0e228b28ae6bc7e468c3acf68722768bd62b73798eb6631e9e6233b71ed9",
  "web_artifacts_sha256": "<sha256 of web-artifacts-r1.tar.zst>",
  "derive_script_sha256": "<sha256 of derive.py>",
  "generated_at": "2026-07-23T00:00:00Z",
  "source_commit": "<git sha>"
}
```

CI downloads the asset, **verifies all three hashes, and fails the build on any mismatch.** A deployed site therefore *cannot* be serving data that does not descend from the frozen dataset. Evidence traceability becomes a property of the build, not of documentation.

---

## 9.2 Artifact layout

```
web-artifacts-r1/
├── meta/
│   ├── manifest.json              # version, hashes, counts, generated_at
│   ├── coverage.json              # 866 days: available, maxRate, gapReason
│   └── search-index.json          # ~40 KB static trigram index
├── overview.json                  # 6 headline metrics + arc + activity[424]
├── validation/
│   ├── index.json                 # ledger: 6 contradictions + status board
│   ├── contradiction-{001..006}.json   # timeline/evidence/decision/diff/result
│   └── spec-revisions.json        # r0 → r6
├── findings/
│   ├── index.json                 # F-1..F-7 + headline conclusion
│   ├── benchmark.json             # 8 models × 2 tasks, all ModelMetric
│   ├── ablation.json
│   ├── curves-{task}.json         # ROC/PR points per model
│   └── limitations.json
├── pipeline.json
├── build.json                     # repro commands, hashes, env, tests
├── measurements.json              # ← flat map: "artifact#pointer" → Quantity
└── days/{YYYY-MM-DD}/
    ├── meta.json                  # header, detector, quality, ~2 KB
    ├── lightcurve.bin             # uint32 counts + float32 livetime, ~6 KB gz
    ├── spectrum-l0.bin            # 60 × C uint16 overview tile, ~10 KB gz
    ├── spectrum-full.bin          # 1440 × C uint16 full res, ~200 KB gz (est.)
    ├── gti.json                   # ~2 KB
    └── provenance.json            # ~20 KB
```

### Why binary for time series, JSON for everything else

| Payload | Format | Reason |
|---|---|---|
| Light curve, spectra | Binary typed arrays | Counts are **non-negative integers**. `uint16`/`uint32` + gzip beats JSON floats by ~4× and parses with zero allocation into a `TypedArray` |
| Metadata, findings, provenance | JSON | Human-inspectable, diffable, directly `curl`-able. Small enough that binary saves nothing meaningful |

**Why not Parquet or Arrow in the browser?** Both would require a WASM reader (`parquet-wasm` ≈ 700KB, `arrow-js` ≈ 200KB) to decode payloads that a 20-line `DataView` loop handles natively. That is a large bundle cost to avoid writing a header parser. **Rejected as an unnecessary abstraction.**

**Binary format** (fixed 32-byte header, little-endian):
```
magic "ADNB" | version u16 | dtype u8 | ndim u8 | shape u32[2] | scale f32 | offset f32 | reserved
```
The header is versioned so a future format change is detectable rather than silently misparsed.

---

## 9.3 Solving the spectrum problem without a server

**The constraint.** T2 is 340 channels × 1,440 minutes = **489,600 values/day**. As JSON floats that is ~9MB — unshippable. This single number drove the entire loading strategy.

**The insight that makes it static.** T2 values are **photon counts** — non-negative integers, small in magnitude, and heavily zero-weighted in high channels. As `uint16` the day is 956KB raw; gzip on sparse small integers should compress to roughly **200KB**.

**Two-request progressive refinement:**

1. **`spectrum-l0.bin`** — 60 × 340 uint16 overview tile, ~10KB gz. Renders immediately, satisfying the ≤300ms first-paint budget.
2. **`spectrum-full.bin`** — 1440 × 340 uint16, ~200KB gz, fetched in the background. On arrival it replaces the tile. **From that point every zoom, pan, and rebin is computed locally in a worker with zero further network traffic.**

**Why this beats a binning API.** A server-binned endpoint issues a request per zoom level — 5–10 round-trips during exploration, each 100–300ms, making the interaction feel networked. Local rebinning after one 200KB fetch is instantaneous at every zoom. **Better UX and no server.**

**Why not just ship full resolution immediately?** 200KB before first paint blows the LCP budget on slow connections. The 10KB tile costs almost nothing and removes the wait entirely.

> **⚠ Pre-committed falsification.** The 200KB figure is an *estimate*, not a measurement. **Sprint 6 measures it on the ten highest-count days.** If the p95 exceeds **400KB gz**, this design is wrong and the fallback (already specified) is: reduce `spectrum-full` to 720 time bins (2-min resolution, halving payload) and add a `spectrum-l3` tile fetched only on deep zoom. Stating the falsification condition now prevents rationalizing a bad measurement later.

---

## 9.4 Rendering boundaries — RSC vs Client Components

Next.js App Router with **`output: 'export'`** (fully static export; no Node runtime in production).

### Why static export rather than SSR/ISR

- **Why this?** Nothing is dynamic. Export produces a portable `out/` directory hostable on any static host, forever.
- **Why not the simpler-looking alternative (a Node server on Vercel)?** It looks simpler because it is the default, but it adds a runtime that must stay alive, patched, and funded to serve unchanging bytes. It also creates vendor coupling: ISR, middleware, and route handlers are platform features, and adopting them makes the site unhostable elsewhere.
- **Future problem solved:** archival longevity and zero vendor lock-in.
- **Complexity avoided:** server runtime, cold starts, platform-specific features, deployment rollback semantics.

### The boundary rule

**Server Components are the default. A component becomes a Client Component only if it requires one of exactly four things:** browser event handlers, browser-only APIs (`canvas`, `WebGL`, `ResizeObserver`, `IntersectionObserver`), React state/effects, or the shared time-axis store.

| Zone | Type | Rationale |
|---|---|---|
| All page shells, layouts, nav | Server | Zero JS shipped |
| `<MetricCard>` (non-linked), `<StatusBadge>`, `<EvidenceBlock>`, `<DecisionBlock>`, `<SpecDiff>`, `<DocRenderer>`, `<CommandBlock>` (text) | **Server** | Pure rendering of build-time data |
| `<SourceRef>` popover, `<Disclosure>`, `<CommandBlock>` copy | Client, leaf-only | Interaction is a leaf; the surrounding content stays server-rendered |
| `<ScientificChart>` and all derivatives, `<CoverageCalendar>`, `<SunHero>`, `<TimeAxisController>` | Client | Canvas/WebGL/state |

**Enforced, not conventional:** an ESLint rule (`adityanet/no-unjustified-client`) requires every `'use client'` file to carry a `// client-reason: <one of four>` comment matching the enum. Missing or invalid reason → build fails. **This is the mechanism that stops the whole app from drifting client-side over eighteen months**, which is the single most common way a Next.js codebase degrades.

**Client-boundary placement rule:** `'use client'` goes on the *smallest* component that needs it, never on a page or layout. A page-level boundary makes the entire subtree client-rendered. Enforced by a lint rule forbidding `'use client'` in `app/**/page.tsx` and `app/**/layout.tsx`.

---

## 9.5 Data loading boundaries

Four loading tiers, chosen by payload size and access pattern — **not by page**:

| Tier | Mechanism | Applies to | Budget |
|---|---|---|---|
| **T-A: Inlined at build** | Imported into RSC, rendered to HTML | All metrics, findings, validation content, page copy | Any single page's inlined data ≤ **30KB** |
| **T-B: Static fetch on route** | `fetch()` of a `.json` in a client component | Coverage map, curves, search index | ≤ **60KB** each |
| **T-C: Static fetch on demand** | Fetched on user action | Day meta, GTI, provenance, `spectrum-l0` | ≤ **30KB** each |
| **T-D: Background binary** | Fetched after paint, decoded in a worker | `lightcurve.bin`, `spectrum-full.bin` | ≤ **400KB**, never blocks paint |

**The rule that keeps this honest:** *tier is a function of size, not of convenience.* A lint-enforced manifest (`data-tiers.json`) declares every artifact's tier and max size; **a CI check measures each generated artifact and fails if it exceeds its declared tier budget.** A file that grows past its budget breaks the build rather than quietly degrading the page.

- **Why this?** Payload discipline decays invisibly. Attaching a measured budget to every artifact makes regression a build failure.
- **Why not just review PRs carefully?** Because 200KB of drift arrives 5KB at a time over a year, and no reviewer catches that.
- **Complexity avoided:** a runtime performance-monitoring apparatus, by moving the check to build time where it is deterministic and free.

---

## 9.6 Caching

Everything is immutable, so caching is trivial — **if URLs are content-addressed.**

| Asset class | URL pattern | `Cache-Control` |
|---|---|---|
| Data artifacts | `/api/v1/datasets/r1/**` | `public, max-age=31536000, immutable` |
| JS/CSS/fonts | `/_next/static/**` (hashed) | `public, max-age=31536000, immutable` |
| HTML | `/**/*.html` | `public, max-age=0, must-revalidate` |
| `manifest.json` | `/api/v1/manifest.json` | `public, max-age=300` |

**Why data can be `immutable` forever:** the dataset version `r1` is *in the path*. `r2` will occupy different URLs. A given URL's bytes can never change, so there is no invalidation problem — the hardest problem in caching is designed out of existence by the URL scheme.

**No service worker.** It would add an update-lifecycle bug class (stale shell, skip-waiting races) for marginal benefit over `immutable` CDN caching on a site users visit a handful of times. **Rejected.**

---

## 9.7 Versioned datasets — and the escape hatch

Two independent version axes, both in the path:

```
/api/v1 / datasets / r1 / days/2024-05-14/lightcurve.bin
   ↑              ↑
   contract       content
```

- **Contract version (`v1`)** — the response *shape*. Bumped only on a breaking schema change.
- **Dataset version (`r1`)** — the *content*. Bumped when the canonical dataset is rebuilt.

They are orthogonal: `v1` can serve `r1` and `r2` simultaneously; `v2` can serve `r1`. **Why it matters:** a citation of a specific result must remain resolvable forever. Coupling the two would break every prior link on a data rebuild.

**Frontend implication.** `<DatasetVersionChip>` (already global per §5) becomes a *selector* the moment a second version exists. Every data-loading hook takes `version` from a single React context. **There is no other place in the codebase where a version string appears** — enforced by a lint rule banning literal `/r\d+/` outside `lib/dataset-version.ts`.

### The escape hatch (honest limits)

If a future need genuinely exceeds static serving — arbitrary multi-year aggregation, or user-supplied query — the boundary is already drawn: **add a single stateless compute endpoint at `/api/v1/query`, leaving every existing URL untouched.** The static layer is not a design that must be replaced to grow; it is a cache tier that a compute tier would sit beside. That is the difference between a shortcut and an architecture.

---

## 9.8 Evidence traceability — mechanized

This is the mechanism that makes P1 real. **Developers never write measured numbers. They write references.**

**Stage 2 emits `measurements.json`:**
```json
{
  "artifacts/v2/ml/benchmark_results.json#/nowcast/threshold/roc_auc": {
    "value": 0.954, "ci95": [0.940, 0.966], "precision": 3,
    "commit": "9efad0c", "sha256": "…"
  }
}
```

**Codegen emits `measurements.generated.ts`** — a frozen, fully-typed const map with a `M` accessor:

```tsx
import { M } from '@/generated/measurements';

<MetricCard
  label="Event recall"
  quantity={M['artifacts/v2/ml/benchmark_results.json#/nowcast/threshold/eventRecall']}
  source={M.ref(...)}
/>
```

**Four enforcement layers:**

| # | Mechanism | Catches |
|---|---|---|
| **E1** | Codegen fails if any referenced JSON pointer does not resolve in the artifact | Stale or typo'd references |
| **E2** | ESLint `adityanet/no-measurement-literals` — bans numeric literals in JSX text, and bans object literals structurally matching `Quantity` outside generated code | Hand-typed numbers |
| **E3** | TS: `MetricCard.source` is required; `ModelMetric` requires `ci95`; `trend?: never` | Unsourced or uncertainty-free display |
| **E4** | **Evidence-consistency test** — parses the built HTML, extracts every `data-measurement-id`, re-reads the *original* artifact from disk, and asserts the rendered string equals `formatQuantity(artifactValue)` | Any drift between site and science, including via the generator |

**E4 is the one that matters.** E1–E3 trust the generator. E4 trusts nothing — it closes the loop from rendered pixels back to the committed artifact. **If it passes, the statement "every number on this site comes from a committed artifact" is a tested property of the build, not a claim in a README.**

- **Why not just be careful?** Because the failure is silent and the cost is the project's entire credibility.
- **Complexity avoided:** a CMS, a database of facts, or a runtime provenance service. The artifacts *are* the database; codegen is the only machinery.

---

# SECTION 10 — API SPECIFICATION

## 10.1 OpenAPI-first, in both languages

**The OpenAPI 3.1 document is the single source of truth**, hand-authored at `web/openapi.yaml`. Everything else is generated from it:

```
                 openapi.yaml   ← the ONLY hand-written contract
                  /         \
   datamodel-code-generator   openapi-typescript
          ↓                          ↓
  derive/schemas.py  (Pydantic)   web/src/generated/api.ts  (TS)
          ↓                          ↓
   Stage 2 writes JSON  ────→   Stage 3 reads JSON
                       both sides typed from one spec
```

**Why OpenAPI-first rather than generating the spec from code?** Code-first generation makes the contract a *side effect* of the implementation — the schema changes silently whenever someone edits a model. Here the Python producer and the TypeScript consumer are in different languages; only a language-neutral contract can bind them. Spec-first makes a breaking change a **deliberate edit to a reviewed file**, visible in the diff.

**Enforced:**
- **A1** — Stage 2 validates every emitted JSON against the spec (Pydantic model round-trip). A non-conforming file fails derivation.
- **A2** — CI re-validates all shipped artifacts against the spec independently of the generator.
- **A3** — Generated types are committed; CI regenerates and fails on any diff. Hand-editing generated code is impossible to land.
- **A4** — `oasdiff` runs on every PR touching the spec; a breaking change without a `v`-bump fails the build.

**Why commit generated code?** So a reader of the repository can see the types without running a toolchain, and so the diff reviewer sees the *consequence* of a spec change, not just its cause.

## 10.2 URL design

```
BASE: https://<host>/api/v1

  GET /manifest.json                              # contract + available dataset versions
  GET /datasets/{ver}/meta/manifest.json
  GET /datasets/{ver}/meta/coverage.json
  GET /datasets/{ver}/overview.json
  GET /datasets/{ver}/validation/index.json
  GET /datasets/{ver}/validation/{id}.json        # id: contradiction-001 … 006
  GET /datasets/{ver}/validation/spec-revisions.json
  GET /datasets/{ver}/findings/index.json
  GET /datasets/{ver}/findings/benchmark.json
  GET /datasets/{ver}/findings/ablation.json
  GET /datasets/{ver}/findings/curves-{task}.json # task: nowcast | prediction
  GET /datasets/{ver}/findings/limitations.json
  GET /datasets/{ver}/pipeline.json
  GET /datasets/{ver}/build.json
  GET /datasets/{ver}/days/index.json             # paginated: days/index-{n}.json
  GET /datasets/{ver}/days/{date}/meta.json
  GET /datasets/{ver}/days/{date}/gti.json
  GET /datasets/{ver}/days/{date}/provenance.json
  GET /datasets/{ver}/days/{date}/lightcurve.bin
  GET /datasets/{ver}/days/{date}/spectrum-l0.bin
  GET /datasets/{ver}/days/{date}/spectrum-full.bin
  GET /openapi.yaml
```

**Every path is a real file.** No rewriting, no routing layer. `.json`/`.bin` extensions are deliberate: the URL states its own content type, works with `curl -O`, and survives a host that doesn't set `Content-Type` correctly.

**Why extensions rather than clean REST URLs?** Clean URLs (`/days/2024-05-14/lightcurve`) require server-side content negotiation. Extensions make the resource self-describing and directly downloadable — which for a scientific dataset is the more important property.

## 10.3 Response schemas

**Every response is an envelope.** Bare arrays and bare scalars are prohibited at the top level.

```ts
interface Envelope<T> {
  api_version: "v1";
  dataset_version: string;      // "r1"
  dataset_sha256: string;
  generated_at: string;         // RFC 3339
  source_commit: string;
  data: T;
  links?: { self: string; next?: string; prev?: string; related?: Record<string,string> };
}
```

**Why an envelope?** A bare array cannot be extended without a breaking change, and — more importantly here — **every response must be self-describing about which frozen dataset produced it.** A consumer who saved a response file three years ago must be able to tell what it is from the file alone. The envelope makes provenance travel with the data.

**Why not JSON:API or HAL?** Both impose substantial ceremony (`type`/`id`/`attributes` nesting, link relation vocabularies) designed for large mutable graphs with client-driven navigation. We have ~15 resource types, all read-only. **Adopting a hypermedia standard here is ceremony without benefit** — the exact enterprise-theater smell this spec forbids.

Core payload types (abbreviated; full schemas live in `openapi.yaml`):

```yaml
Quantity:      { value: number, ci95?: [number,number], unit?: string,
                 n?: integer, precision: integer }        # required: value, precision
ModelMetric:   allOf: [Quantity, required: [ci95]]        # P3 in the schema itself
ArtifactRef:   { artifact, pointer?, sha256?, commit, href? }   # required: artifact, commit
BenchmarkRow:  { model, roc_auc: ModelMetric, event_recall: ModelMetric,
                 false_runs: Quantity, verdict: enum[baseline, indistinguishable,
                 significantly-better, significantly-worse] }
DayMeta:       { date, detector, archive_version, live_time_s, gti_fraction,
                 quality_flags[], channel_space: enum[SOLEXS_PI_340,
                 HEL1OS_CZT_PHA_341, HEL1OS_CDTE_PHA_511] }
```

**`ModelMetric` requiring `ci95` in the OpenAPI schema means P3 is enforced in three independent places** — the schema, the Pydantic model, and the TS type — all generated from one line. That is what "convert principles into mechanisms" looks like in practice.

## 10.4 Error handling

Static hosting yields only transport errors, and pretending otherwise would be theater. The honest set:

| Status | Cause | Client behavior |
|---|---|---|
| `200` | Success | — |
| `304` | Conditional revalidation | Use cache |
| `404` | Resource absent | Domain-specific empty state naming the reason (§4) |
| `5xx` | CDN failure | Retry ×2, exponential backoff (250ms, 1s), then panel-scoped error with retry control |

**404 is a legitimate scientific answer**, not an error: a date with no observation genuinely has no light curve. The client distinguishes *"absent because not observed"* (from `coverage.json`, which enumerates every gap and its reason) from *"absent unexpectedly"* — and only the latter renders as a fault. **The coverage manifest is what lets a 404 be interpreted rather than guessed at.**

No RFC-7807 problem details: with no server there is no server-authored error body to standardize.

## 10.5 Versioning strategy

| Change | Action |
|---|---|
| New optional field | In-place, no bump (additive) |
| New endpoint | In-place, no bump |
| New dataset build | New `dataset_version`; `v1` unchanged; old version stays online |
| Field removed / renamed / type changed / required added | **`v2`; `v1` frozen and kept online indefinitely** |

**Deprecation policy: none — old versions are never removed.** They are static files with negligible storage cost. **Why:** the reason to delete an API version is maintenance burden, and immutable files have none. Permanence is nearly free here, and permanence is precisely what a citable research artifact requires.

Enforced by **A4** (`oasdiff` breaking-change detection in CI).

## 10.6 Pagination, streaming, rate limits — deliberate non-features

**Pagination.** Only `days/index.json` is large enough to warrant it (866 entries). Split into fixed pages of 200 with `links.next`. Cursor pagination is unnecessary — the collection is immutable, so offsets can never skip or duplicate. **Offset pagination's only real flaw does not exist here.**

**Streaming.** Not implemented. The largest payload is ~200KB, well under the threshold where streaming helps; progressive refinement (§9.3) already delivers the perceptual benefit. Adding SSE/chunked transfer would be **premature optimization for a problem measurement shows we do not have.**

**Rate limits.** Not implemented. The CDN absorbs abusive traffic natively, all content is public and immutable, and there is no origin to protect. **A rate limiter here would exist only to look serious** — and would be the clearest possible instance of enterprise theater in an architecture document.

---

# SECTION 11 — FRONTEND ARCHITECTURE

## 11.1 Folder structure

```
web/
├── openapi.yaml                    # the contract (hand-written)
├── artifacts.lock.json             # dataset + artifact hash pins
├── data-tiers.json                 # per-artifact size budgets
├── tokens/*.json                   # design tokens (source of truth)
├── scripts/
│   ├── gen-types.ts                # openapi.yaml → generated/api.ts
│   ├── gen-tokens.ts               # tokens/ → CSS vars + tailwind + TS
│   ├── gen-measurements.ts         # measurements.json → generated/measurements.ts
│   └── check-budgets.ts            # artifact + bundle budget enforcement
└── src/
    ├── app/                        # routes ONLY — no logic, no components
    │   ├── layout.tsx  page.tsx
    │   ├── validation/[id]/page.tsx
    │   ├── data/[date]/page.tsx
    │   ├── findings/limitations/page.tsx
    │   ├── pipeline/  build/
    │   └── (error handling) error.tsx  not-found.tsx
    ├── generated/                  # ← NEVER hand-edited; CI verifies
    │   ├── api.ts  measurements.ts  tokens.ts
    ├── components/
    │   ├── primitives/             # Button, Badge, Disclosure, Table…
    │   ├── evidence/               # SourceRef, MetricCard, EvidenceBlock…
    │   ├── charts/                 # ScientificChart + derivatives
    │   ├── scientific/             # LightCurveViewer, SpectrumViewer, GtiStrip…
    │   ├── narrative/              # ContradictionTimeline, DecisionBlock, SpecDiff
    │   └── shell/                  # Nav, Footer, VersionChip, CommandPalette
    ├── lib/
    │   ├── data/                   # fetchers, binary decode, tier enforcement
    │   ├── format/                 # formatQuantity, formatSha, formatInterval
    │   ├── science/                # lttb, rebin, gti, decimation  ← pure, 100% covered
    │   └── dataset-version.ts      # the ONLY place a version literal exists
    ├── hooks/
    ├── stores/                     # time-axis (Zustand) — the only store
    ├── styles/
    └── test/
```

**Why `app/` contains no components.** Routes are a Next.js concern; components are a product concern. Keeping them separate means a framework migration touches one directory. **Enforced** by a lint rule: files in `app/**` may only import from `components/`, `lib/`, and `generated/`, and may not define a component longer than a page composition.

**Why `generated/` is committed but write-protected.** A pre-commit hook and a CI check regenerate and diff. Any manual edit fails the build.

## 11.2 Architecture constraints as lint rules

The dependency graph is enforced, not documented. Using `eslint-plugin-boundaries`:

```
app        → components, lib, generated
components/scientific → components/charts, components/primitives, lib, generated
components/charts     → components/primitives, lib, generated
components/primitives → lib/format, generated/tokens        ← nothing else
lib/science           → (nothing)                            ← pure functions only
generated             → (nothing)
```

| Rule | Prevents |
|---|---|
| `primitives` cannot import `lib/data` | Primitives becoming data-aware and unreusable |
| `lib/science` cannot import anything | Scientific logic entangling with React; keeps it 100%-testable |
| No file may import `generated/*` and hand-construct a `Quantity` | Bypassing the measurement pipeline |
| No `'use client'` in `page.tsx`/`layout.tsx` | Whole-subtree client rendering |
| Every `'use client'` needs `// client-reason:` from a 4-value enum | Unjustified client drift |
| No `/r\d+/` literal outside `dataset-version.ts` | Version strings scattering |
| No `--doc-*` token outside `DocRenderer` | Type-scale mixing |
| No numeric literal in JSX text | Unsourced numbers (E2) |

**Why lint rules rather than a code-review checklist?** A checklist is applied by a human at 5pm on a Friday eighteen months from now. A lint rule is applied identically forever. **Every principle in this document that could be violated silently has been converted into a rule that fails the build.**

## 11.3 State management

Three kinds of state, three mechanisms, no overlap:

| Kind | Mechanism | Why |
|---|---|---|
| **Server/artifact data** | RSC props (inlined) or plain `fetch` + `use()` | Immutable — caching, invalidation, and refetching are all no-ops. A data-fetching library would manage a lifecycle that does not exist |
| **URL state** (date, filters, task, theme-independent view) | `searchParams` / route params | Citability (§8.5). Anything not in the URL cannot be linked |
| **Ephemeral view state** (time axis, cursor, hover) | One Zustand store, transient updates | 60Hz cursor updates must bypass React |

**Why no TanStack Query / SWR?** Their value is cache invalidation, background refetch, request dedup, and stale-while-revalidate — **every one of which is meaningless against immutable, `max-age=31536000` resources.** Adding one would ship ~13KB and a mental model to solve problems this architecture does not have.

**Why no Redux/Jotai/Context for global state?** There is exactly one piece of shared mutable state in the entire application: the time axis. One store, ~40 lines.

**Why Zustand and not `useState` lifted to a provider?** Because a Context provider re-renders every consumer on cursor movement. Zustand's `subscribe` lets chart canvases read cursor updates without a React render — the specific technical reason, not a preference.

## 11.4 Type safety

**`strict: true`** plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noFallthroughCasesInSwitch`.

**Why `noUncheckedIndexedAccess` specifically:** we index heavily into typed arrays and measurement maps. Without it, `spectrum[i]` types as `number` even when out of bounds — the exact bug class that silently renders `NaN` or `undefined` as a scientific value.

**Zero `any`.** ESLint error, no exceptions. Third-party gaps get an explicit local `.d.ts` with a comment.

**Branded types for identifiers**, preventing structurally-identical strings from being interchanged:

```ts
type IsoDate     = string & { readonly __brand: 'IsoDate' };
type Sha256      = string & { readonly __brand: 'Sha256' };
type DatasetVer  = string & { readonly __brand: 'DatasetVersion' };
type ChannelIdx  = number & { readonly __brand: 'ChannelIndex' };
```

**Why brand `ChannelIndex`:** channel indices from three incommensurable spaces (340 / 341 / 511) are all `number`. Branding, combined with the required `channelSpace` discriminant (§6.6), makes cross-space contamination a compile error. **This is the highest-consequence type in the codebase** — it guards the exact scientific error (F-11) that the dataset makes easiest to commit.

## 11.5 Testing hierarchy

Seven levels, fastest and cheapest first. **Levels L0–L3 run on every save; L0–L5 on every PR; all seven on `main`.**

| L | Level | Tool | Scope | Gate |
|---|---|---|---|---|
| **L0** | Type check | `tsc --noEmit` | Whole repo | Zero errors |
| **L1** | Contract | Pydantic + `openapi-typescript` diff | Every artifact vs spec; generated code vs committed | Zero drift |
| **L2** | **Evidence consistency** | Custom (E4) | Built HTML vs source artifacts | **Zero mismatches** |
| **L3** | Unit | Vitest | `lib/science`, `lib/format`, binary decode | **100% branch on `lib/science`**; 90% on `lib/format` |
| **L4** | Component | RTL + `jest-axe` | All components, all states | Zero a11y violations; every documented state has a test |
| **L5** | Visual regression | Playwright screenshots | 6 surfaces × 3 breakpoints × 2 themes = 36 | Zero unreviewed diffs |
| **L6** | E2E persona journeys | Playwright | 6 journeys from §2 | All pass |
| **L7** | Budgets | `check-budgets.ts` + Lighthouse CI | Bundles, artifacts, LCP/CLS/INP | No budget exceeded |

**Why L2 sits above unit tests in importance.** It is the only test that verifies the platform's central claim. A unit test proves `formatQuantity` is correct; **L2 proves the site is not lying.** It is the test that would be written by someone who understood what this product is for.

**Why 100% branch coverage on `lib/science` and nowhere else.** LTTB decimation, rebinning, and GTI interval logic are pure functions where a wrong branch produces a *plausible-looking but incorrect chart* — a silent scientific error. Everywhere else, an error is visible. Coverage targets should follow consequence, not uniformity. **A blanket 90% target across the codebase would be cargo-culted; this is not.**

**L6 journeys are the six persona paths verbatim from §2**, each asserting its trust signals are reachable — e.g. *Reviewer*: land on `/validation` → open CONTRADICTION-001 → assert Evidence, Decision, **and the rejected-alternatives block** are present → reach `/build` in ≤ 3 clicks.

**Explicitly not tested:** the WebGL sphere's pixel output (brittle, GPU-dependent). Instead its *data mapping* is unit-tested and its static SVG fallback is visually regressed — testing the property that matters, not the rendering that varies.

## 11.6 Performance, bundles, lazy loading

### Budgets (CI-enforced, per route)

| Route | JS (gz) | Initial data | LCP | CLS | INP |
|---|---|---|---|---|---|
| `/` | 180KB | 30KB | 1.5s | 0.02 | 200ms |
| `/validation`, `/validation/[id]` | **60KB** | 25KB | 1.0s | 0.01 | 100ms |
| `/data/[date]` | 220KB | 40KB + T-D | 2.0s | 0.05 | 200ms |
| `/findings` | 160KB | 60KB | 1.2s | 0.02 | 150ms |
| `/pipeline` | 70KB | 20KB | 1.0s | 0.01 | 100ms |
| `/build` | 80KB (+400KB lazy) | 20KB | 1.2s | 0.02 | 150ms |

Measured on **Moto G Power / 4G throttled**, not a MacBook on fibre. Budgets measured on a laptop are budgets that do not exist.

**`/validation` at 60KB is the important number.** The credibility surface must be the fastest page on the site, because a reviewer's patience is the scarcest resource the project has. It is achievable because Validation is 100% Server Components — its only client JS is the disclosure toggle and the diff view mode.

### Splitting strategy

| Chunk | Load | Size |
|---|---|---|
| Framework (React, Next runtime) | Initial, shared | ~45KB |
| Shell (nav, tokens, primitives) | Initial, shared | ~25KB |
| ECharts core + line/heatmap only | Route: `/data`, `/findings` | ~95KB |
| WebGL (three.js subset) | `/` only, after LCP, `IntersectionObserver` | ~120KB |
| Swagger UI | `/build`, on scroll into view | ~400KB |
| Web worker (binary decode, rebin) | `/data`, on demand | ~8KB |

**ECharts is imported per-component**, never as the full bundle (`echarts/core` + explicit chart/component registration). Full ECharts is ~1MB; our subset is ~95KB. A lint rule bans `import * from 'echarts'`.

**three.js is imported as a hand-picked module subset**, not the umbrella package — and if §Part-2's `<SunHero>` kill criterion fires, this chunk disappears entirely.

### Why no runtime performance library

No virtual-DOM profiler, no analytics-driven perf SDK. **Performance is verified at build time against a fixed device profile.** Runtime perf monitoring is for applications whose payloads vary with user data. Ours are identical for every user, so a build-time measurement is not an approximation of production — **it is production.**

---

# SECTION 12 — QUALITY STANDARDS

## 12.1 Lighthouse and Core Web Vitals

| Metric | Target | Gate |
|---|---|---|
| Performance | ≥ 95 | ≥ 90 fails PR |
| Accessibility | **100** | < 100 fails PR |
| Best Practices | ≥ 95 | — |
| SEO | ≥ 95 | — |
| LCP / CLS / INP | Per §11.6 | Exceeded → fail |

**Accessibility must be exactly 100 and nothing less.** It is the one Lighthouse category that is a near-objective checklist rather than a heuristic score, and a research platform that excludes screen-reader users has failed at its stated purpose of making the archive *accessible*.

## 12.2 WCAG conformance

**Target: WCAG 2.2 Level AA in full, with AAA on contrast (1.4.6) and AAA on reading-flow (2.4.10 section headings).**

**Why AA and not full AAA?** Full AAA requires, among other things, sign-language interpretation for media and a Level-AAA reading level (lower secondary education) for all prose. This platform's content is *inherently* graduate-level — a day-block bootstrap CI cannot be rewritten at a reading level of 14 without ceasing to be true. **Claiming AAA would be dishonest, and honesty outranks the badge.** We exceed AA precisely where it benefits our actual users (contrast, structure, keyboard) and state plainly where we do not.

**Published accessibility statement** at `/build#accessibility` listing conformance level, known exceptions (Swagger UI, third-party), and the mitigation for each. **A named exception is more credible than a blanket claim.**

Automated: `jest-axe` at L4, `@axe-core/playwright` at L5–L6, zero violations gate. Manual, once per surface before release: VoiceOver + Safari, NVDA + Firefox, keyboard-only traversal, 200% zoom, 400% reflow.

## 12.3 Error budgets — reframed honestly

Classical SRE error budgets assume a service you operate. We operate no service; the CDN's availability is not ours to spend. Applying an SLO framework to someone else's uptime would be theater. The honest budgets:

| Budget | Allowance | Action on breach |
|---|---|---|
| **Build failures on `main`** | **0** | Revert immediately; `main` is always deployable |
| **Evidence-consistency (L2) failures** | **0, ever** | Blocks release unconditionally. Not negotiable, not waivable |
| **Client JS exceptions** | ≤ 0.1% of sessions | Investigate; the site must remain usable without JS for all text content |
| **Broken internal links** | 0 | Link-check in CI |
| **Broken artifact refs** | 0 | Caught by E1 at codegen |
| **a11y violations** | 0 | Blocks PR |
| **Budget overruns (§11.6)** | 0 | Blocks PR; raising a budget requires a written justification in the PR body |

**The L2 budget of zero-forever is the project's most important quality commitment.** Every other budget is engineering hygiene; this one is the product's integrity.

## 12.4 Visual regression

36 baseline screenshots (6 surfaces × 3 breakpoints × 2 themes), plus per-component stories for the 20 named components in every documented state.

**Determinism requirements** — without these, visual regression becomes a flaky test everyone learns to approve blindly, which is worse than not having it:
- All timestamps stubbed to a fixed instant
- `prefers-reduced-motion: reduce` forced (removes all animation timing variance)
- Fonts loaded from local files, never network
- WebGL canvas masked (GPU-dependent); its SVG fallback is captured instead
- Single pinned browser build, single OS image

Diffs are reviewed by a human and approved explicitly. **Auto-approval is prohibited** — an auto-approved visual baseline is a screenshot archive, not a test.

## 12.5 Snapshot testing — scoped narrowly

Snapshots are used for exactly two things: **generated artifacts** (a change to `derive.py` shows its full effect on output) and **`formatQuantity` output** across the value matrix (integers, sub-unit, CIs, units, denominators, negative deltas, scientific notation).

**Not used for component markup.** Markup snapshots break on every legitimate refactor, train the team to run `-u` reflexively, and assert nothing about behavior. **A test everyone updates without reading is worse than no test** — it consumes CI time and manufactures false confidence.

## 12.6 Definition of Done

A change is done when: L0–L7 pass · a11y verified for new interactive surfaces · every new number flows through `M[...]` · every new `'use client'` carries a valid reason · budgets unchanged or justified in writing · the OpenAPI spec updated if any response shape changed · docs updated in the same PR.

---

# SECTION 13 — DEPLOYMENT

## 13.1 Hosting

**Cloudflare Pages.** Static `out/` directory, global CDN, unlimited bandwidth on the free tier, and — critically — **no compute.**

- **Why this?** Zero cost, zero ops, global edge, immutable-asset caching, and full deploy history with instant rollback (a rollback is repointing to a previous immutable deployment, not a rebuild).
- **Why not Vercel?** Excellent for Next.js *with* a runtime. We deliberately have none, so we would be paying vendor coupling for features we forbid (§9.4).
- **Why not S3 + CloudFront?** More configuration (bucket policy, OAI, invalidations, cert) for equivalent output.
- **Why not GitHub Pages?** 1GB site limit and a 100GB/month soft bandwidth cap; ~150MB of artifacts plus growth makes that a future migration.
- **Portability is preserved regardless:** because the build output is a plain directory with no platform features, migrating hosts is a copy operation. Vendor lock-in is architecturally impossible.

**Capacity check.** ~150MB total, ~3,000 files (500 dates × 5 + ~520 HTML + assets), against Cloudflare Pages' 20,000-file / 25MB-per-file limits. **Headroom: ~6×.** A future r2 doubling this remains within limits; beyond that, artifacts move to R2 object storage with the same URL scheme — a hosting change, not an architecture change.

**Custom domain, HTTPS enforced, HSTS.** Security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy: strict-origin-when-cross-origin`) set via `_headers`. CSP is strict: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'`. **No external origins are permitted at all** — no CDN fonts, no analytics scripts, no third-party anything. A site that loads nothing from elsewhere cannot leak its visitors elsewhere.

## 13.2 Artifact generation and publication

**Stage 2 runs locally** (it needs the 597MB frozen dataset), producing `web-artifacts-r1.tar.zst` published as a **GitHub Release asset** with its SHA-256 recorded in `artifacts.lock.json`.

- **Why a release asset rather than Git LFS?** LFS bandwidth is metered and quota-limited, and every `git clone` would pull 150MB. A release asset is fetched only by CI and by contributors who want it.
- **Why not commit it?** 150MB of generated binaries in git history is permanent, unreviewable, and would make the repository hostile to clone forever.
- **Why not generate it in CI?** CI cannot: Stage 1 needs a 30GB raw archive and 94 minutes.
- **What this preserves:** the derivation is still fully reproducible — `derive.py` is committed and hash-pinned, so anyone with the frozen dataset regenerates a byte-identical asset and can verify the pin.

## 13.3 CI/CD

```
PR:
  1. install (pnpm, frozen lockfile)
  2. codegen → assert no diff in generated/          [A3]
  3. tsc --noEmit                                    [L0]
  4. eslint (incl. all architecture + evidence rules)
  5. download web-artifacts, verify 3 hashes         [§9.1]
  6. validate artifacts vs openapi.yaml              [A2/L1]
  7. oasdiff breaking-change check                   [A4]
  8. vitest (unit + coverage gates)                  [L3]
  9. build (next build --export)
 10. EVIDENCE CONSISTENCY on built HTML              [L2]  ← hard gate
 11. check-budgets (artifacts + bundles)             [L7]
 12. playwright: component a11y, visual, E2E         [L4–L6]
 13. lighthouse-ci on 6 surfaces                     [L7]
 14. link check
 15. deploy preview → comment URL on PR

main: same pipeline → production deploy (immutable, instant rollback)
```

**Target wall time: ≤ 12 minutes.** Steps 3–8 run in parallel; the artifact download is cached by hash across runs. **Why a hard time target:** a pipeline slower than ~15 minutes gets bypassed, and a bypassed gate is not a gate.

**Branch protection:** all checks required, no force-push to `main`, no admin bypass. **Including for the sole maintainer** — a solo project with an admin bypass has no gates, only suggestions.

**Renovate** for dependency updates, grouped weekly, auto-merged only when the full pipeline including L2 and visual regression passes. **Python dependencies stay pinned to `requirements.lock`** with no auto-update: the numpy 1.26.4 → 2.4.6 incident (which silently occurred twice in this project) is exactly why the science-side environment is frozen and the web-side is not.

## 13.4 Monitoring — sized to a read-only static platform

| Concern | Tool | Why |
|---|---|---|
| Traffic | **Cloudflare Web Analytics** | Cookieless, no PII, no client script beyond a 2KB beacon, GDPR-clean by construction |
| Uptime | Cloudflare status + a single external HTTP check on `/` | Availability is the CDN's; our only concern is "is the deployment live" |
| Client errors | **Custom 1KB beacon** → Cloudflare Worker → log | See below |
| Build health | GitHub Actions notifications | The only thing we actually control |

**Why a custom error beacon instead of Sentry.** Sentry's browser SDK is ~25KB gzipped and its default configuration captures URLs, breadcrumbs, and optionally session replay. For a public research site, **collecting visitor interaction traces is both unnecessary and a privacy cost we should not impose.** A 1KB beacon sending `{message, filename, lineno, colno, userAgent-family, route}` — no user identifier, no session, no replay, no cookies — answers the only real question ("is something broken for real users?") at 1/25th the bundle cost and near-zero privacy exposure.

**Explicitly not deployed:** APM, distributed tracing, RUM SDKs, session replay, feature flags, A/B testing, heatmaps.

**Why not.** Tracing requires distributed services (we have none). RUM measures variance in payload and server latency (ours are constant, and measured at build time). Feature flags require a runtime config service. **Each of these would be infrastructure adopted to look professional rather than to answer a question we have** — the precise failure mode this specification exists to prevent.

## 13.5 Analytics ethics

No cookies. No fingerprinting. No third-party scripts (structurally impossible under the CSP in §13.1). No cross-site tracking. Aggregate page counts and referrers only. **A `/privacy` page states this in full, and the CSP is the enforcement** — the claim is verifiable by reading the response headers, not by trusting the page.

---

# HOSTILE STAFF ENGINEER REVIEW — Part 3

Reviewing my own architecture for overengineering, unnecessary abstraction, premature optimization, hidden scalability assumptions, maintainability risk, and implementation risk.

---

## Valid criticisms — architecture revised

### ▸ R1. `<ScientificChart>` is an abstraction built before its second use case. **Revised.**
I specified a base primitive with seven variants wrapping an adapter over ECharts — a framework, designed up front, on zero implementations. This is the classic premature-abstraction failure, and it usually calcifies around the *first* chart's needs while claiming generality.

**Revision:** Build `<LightCurveViewer>` concretely in Sprint 6, directly against ECharts. Build `<RocCurve>` concretely in Sprint 7. **Extract `<ScientificChart>` only after the third chart exists**, from observed commonality. The scientific *rules* (§5.6) ship immediately as a lint rule and a shared `chartDefaults()` config object — **the rules do not require the abstraction.** The ECharts adapter interface is deleted from the spec: it exists to enable a renderer swap nobody has requested, and a direct ECharts dependency is easier to replace than a wrong abstraction over it.

### ▸ R2. Seven test levels is process theater at solo scale. **Revised.**
L0–L7 with distinct tooling is a structure for a team with a QA function. A solo maintainer will run some and let the rest rot, and rotted tests are worse than absent ones.

**Revision:** collapse to **four gates** — `verify` (L0+L1+lint+L2), `test` (L3+L4), `e2e` (L5+L6), `budget` (L7). Four `pnpm` scripts, one CI job each. The *coverage* is unchanged; the *ceremony* is quartered. L2 remains a standalone unconditional gate because it is the integrity check.

### ▸ R3. Ten enforcement lint rules is more custom tooling than the app has features. **Revised.**
Custom ESLint rules are real code with real maintenance cost, and I specified ten before writing a component.

**Revision:** **Two custom rules only** — `no-measurement-literals` (E2) and `no-unjustified-client`. These guard the two properties that cannot be caught any other way and whose violation is silent. Everything else moves to `eslint-plugin-boundaries` config (declarative, zero custom code) or to a **single ~60-line `scripts/check-invariants.ts`** that greps for the remaining patterns (version literals, `--doc-*` misuse, `import * from 'echarts'`). A grep script is honest about what it is; a custom AST rule for the same job is over-machined.

### ▸ R4. The binary format is a hidden assumption about count magnitude. **Revised.**
`uint16` caps at 65,535. During the X8.7 flare of 2024-05-14, a bright low channel could plausibly exceed that in a 1-minute bin — and `uint16` overflow would **silently wrap a flare peak to a small number**, producing a scientifically wrong figure with no error. This is the most dangerous defect in Part 3 as originally written.

**Revision:** `derive.py` computes the global max per table and **fails loudly** if it exceeds the dtype range, promoting to `uint32` and recording the chosen dtype in the file header. The decoder reads dtype from the header rather than assuming. **A unit test asserts the encoder raises on overflow.** Added as fail-loud rule **F-21**, consistent with the project's existing convention.

### ▸ R5. `output: 'export'` with ~520 static pages has an unstated build-time assumption. **Accepted with a measurement gate.**
I asserted a 3–6 minute build without measuring. If per-page overhead is worse than assumed, r2 (potentially 2× the days) could push CI past the 12-minute target.

**Revision:** Sprint 3 measures build time at 50 and 500 generated pages and records the per-page cost in the repo. If extrapolated r2 build exceeds 10 minutes, `/data/[date]` becomes a single client-routed page with `generateStaticParams` limited to the ~30 scientifically notable dates (the ones likely to be cited), and other dates render client-side. **Deep-linkability is preserved either way; only pre-rendering coverage changes.** Decision deferred to data, with the trigger defined now.

### ▸ R6. Four branded types where one earns its keep. **Revised.**
`ChannelIdx` prevents a real, high-consequence scientific error (F-11 cross-space contamination). `IsoDate`, `Sha256`, and `DatasetVer` prevent string mix-ups that are (a) unlikely and (b) immediately visible when they occur.

**Revision:** keep `ChannelIdx`. Drop the other three — branding costs a cast at every boundary and the benefit is not there. **Justify each brand by the consequence of the error it prevents, not by symmetry.**

### ▸ R7. The 21-item artifact layout ships files no page consumes at v1. **Revised.**
`search-index.json` supports a command palette explicitly deferred past Sprint 8 (Part 2 self-review). Generating and shipping it now is dead weight and a maintenance obligation.

**Revision:** `derive.py` emits only what a shipped surface consumes. Search index generation lands in the sprint that ships search. **The derivation script is not a place to speculate.**

---

## Criticisms I considered and reject, with reasons

**"No server is a shortcut that will need replacing."** No — §9.7 defines the exact escape hatch, and it is *additive*: a `/api/v1/query` compute endpoint sits beside the static layer without touching one existing URL. A design with a defined, non-destructive growth path is not a shortcut.

**"OpenAPI-first is heavy for ~15 endpoints."** The weight is one YAML file. It buys a Python↔TypeScript contract that no other mechanism provides for two languages, plus automated breaking-change detection. **The alternative is hand-syncing schemas across languages, which fails silently.**

**"Evidence-consistency testing is exotic."** It is the only test that verifies the platform's central claim. If a single test survives budget pressure, it is this one.

**"Committing generated code is bad practice."** Only when generation is non-deterministic or the diff is unreviewable. Ours is deterministic, CI-verified, and the diff is the *precise consequence* of a spec change — which is the most useful thing a reviewer can see.

**"Two font scales, three families, density modes, dual themes — too much surface."** Flagged in Part 2 with a Sprint-5 kill criterion on the serif. The review mechanism exists; re-litigating it here would be churn.

---

## Post-revision architecture summary

| Property | State after revision |
|---|---|
| Runtime services | **Zero** |
| Databases / caches / queues | **Zero** |
| Custom lint rules | **2** (down from 10) |
| CI gates | **4** (down from 7 levels) |
| Branded types | **1** (down from 4) |
| Premature abstractions | **0** (`ScientificChart` deferred to third use) |
| Silent-failure modes closed | uint16 overflow (F-21), stale refs (E1), hand-typed numbers (E2/E4), client drift, cross-channel-space contamination |
| Unmeasured assumptions | **2**, each with a written falsification trigger (spectrum payload size; build time at scale) |

**Verdict on Part 3.** After revision, the architecture has no component that exists without a stated measurable benefit, no abstraction that precedes its second use case, and every scientific principle from Parts 1–2 converted into a compiler error, a codegen failure, or a build gate. The two remaining unmeasured assumptions are named, bounded, and have pre-committed fallbacks — which is the honest treatment of an estimate in a document written before implementation.

---

**End of Part 3 (Sections 9–13).**

Next: **Part 4 — Sections 14–17** (Future Roadmap, Master Implementation Roadmap with vertical-slice phases, Critical Design Review across the whole specification, and Final Verdict). Implementation Mode begins after Part 4, as you specified.

Say **continue** for Part 4.

---

# ADITYANET WEB PLATFORM v1.0 — PRODUCT SPECIFICATION
## Part 4 of 4 · Sections 14–17 · **Final**

---

# SECTION 14 — FUTURE ROADMAP

## 14.0 The governing test

A future extension is "designed for" only if it satisfies all three:

1. **No existing URL changes.** Prior citations keep resolving.
2. **No existing component signature changes.** Only additive props.
3. **No existing artifact is mutated.** New data arrives as a new file or a new dataset version.

Anything failing these is not an extension — it is a rewrite, and I say so explicitly below rather than claiming false readiness.

---

## 14.1 RMF acquisition → calibrated energy axis

**What it is.** With an instrument response file, ordinal PI channels become physical keV, unlocking spectral fitting and severity characterisation.

| | |
|---|---|
| **What changes** | New artifact `calibration/rmf-{instrument}-{ver}.json` (channel→energy edges, response matrix ref). `<SpectrumViewer>` gains `calibration?: CalibrationRef`. New dataset version `r2`. |
| **What does not change** | Every `r1` URL. `<SpectrumViewer>`'s existing props. The `channelSpace` discriminant. The binary format. |
| **The seam that makes it work** | §6.6 already derives the spectrum axis label from `channelSpace` rather than hardcoding it, and §9.7 already puts dataset version in the path. The y-axis becomes a function of `calibration ?? channelSpace` — a one-line change in one component. |
| **New surface content** | A calibration section on Build; a Validation entry if the RMF contradicts a prior assumption (likely, and it should be recorded like any other). |
| **Honest caveat** | Calibrated spectra invite *fitting*, which is a scientific capability, not a frontend one. The web platform would display fits computed in Stage 1; it must never fit in the browser. |

**Sequencing note.** RMF is pursued **after** publish and open-source, per the corrected ordering established earlier in this project. It is not a frontend dependency, and nothing in this specification waits on it.

---

## 14.2 Additional HEL1OS coverage

**What it is.** Extending beyond the current 389 / 391 orbits and the 171-day SoLEXS overlap.

| | |
|---|---|
| **What changes** | `coverage.json` gains entries. `days/{date}/` directories appear. Dataset version bumps if canonical tables are rebuilt. |
| **What does not change** | **Nothing in the frontend.** |
| **The seam** | `coverage.json` is keyed by date with an open value shape (§6.7), and `days/index.json` is generated by enumeration. `<CoverageCalendar>` renders whatever it is given. `<SpectrumViewer>` already accepts `HEL1OS_CZT_PHA_341` and `HEL1OS_CDTE_PHA_511`. |

**This is the cleanest extension in the roadmap** — new data appears with zero code changes, which is the correct outcome for "more of the same kind of data" and is the strongest evidence that the data architecture is right.

---

## 14.3 GOES cross-instrument validation

**What it is.** Overlaying GOES XRS flux against SoLEXS rate to independently validate detection, and to quantify the cross-instrument agreement the project has not yet measured.

| | |
|---|---|
| **What changes** | New artifact `days/{date}/goes.json`. `<LightCurveViewer>` receives a second series. A new Findings section: cross-instrument agreement, with its own CIs. |
| **What does not change** | `<LightCurveViewer>`'s signature — §6.5 defined `series` as an **array** specifically for this. |
| **The seam** | Multi-series was designed in, and §5.2.4's redundant dash-pattern encoding already handles two series distinguishably in grayscale. |
| **Scientific care required** | GOES is a **different instrument, different band, different calibration.** The overlay must render on a **secondary axis that is explicitly labelled as non-commensurable**, or — better, and the recommended form — as **two stacked panels sharing the time axis**, never as two lines on one y-axis. §5.6 rule 4 bans dual y-axes precisely because they manufacture apparent correlation. **The one place this project would be most tempted to break its own charting rule is exactly where the rule matters most.** |

---

## 14.4 Onset-latency metric

**What it is.** Conclusion 5 of the ML work identified onset latency — not steady-state recall — as the operationally meaningful open problem, because persistence trivially saturates recall at 1.000 with zero false runs.

| | |
|---|---|
| **What changes** | `benchmark.json` gains an `onset_latency` block. `<BenchmarkTable>`'s `task` union extends to `'onset-latency'`. A distribution chart (latency histogram with CI). |
| **What does not change** | The table component, the envelope, the API version (additive field). |
| **The seam** | §6.9 typed `task` as an extensible union and `rows` as an open array for this exact reason. |

This is the highest-scientific-value future item, because it is the metric the project's own conclusions say should be primary.

---

## 14.5 Future datasets and future models

**Datasets.** `r2`, `r3` coexist with `r1` at parallel URLs. `<DatasetVersionChip>` becomes a selector — the only UI change, and one already anticipated in §5 and §9.7. Old versions stay online permanently (§10.5).

**Models.** A model appended to `benchmark.json` appears in the table automatically, with its `verdict` recorded by the pre-registered protocol, not computed in the view (§6.9). **A new model cannot enter the site without a CI, because `ModelMetric` requires `ci95` in the schema, the Pydantic validator, and the TypeScript type.** P3 holds for work not yet done.

---

## 14.6 What is *not* designed for — stated plainly

| Capability | Why it would require rework |
|---|---|
| **User accounts, saved views, annotations** | Requires a mutable store, auth, and privacy handling. Genuine rewrite. Deliberately excluded (§3.2). |
| **Arbitrary multi-year server-side aggregation** | Exceeds static enumeration. Escape hatch defined (§9.7): one additive `/api/v1/query` endpoint beside the static layer. Not free, but not destructive. |
| **Live or near-real-time ingest** | Would violate P2 and the entire honesty framing. **Not a future item. It is out of scope by principle, permanently.** |
| **In-browser spectral fitting** | Science belongs in Stage 1. The browser displays; it does not compute results. |

---

# SECTION 15 — MASTER IMPLEMENTATION ROADMAP

## 15.0 Principles

1. **Every sprint ends deployable.** Not "buildable" — deployed, at a URL, honest about what it contains.
2. **Vertical slices.** Each sprint delivers data → API → component → page → test → deploy for one thing.
3. **Abstraction is extracted, never anticipated.** A shared component requires **two real uses**, not two imagined ones.
4. **New surfaces are dark-launched.** A route exists and is deployed before it enters navigation; entering navigation is the acceptance event.
5. **A sprint that cannot state a measurable success metric is not scoped.**

## 15.1 Scope tiers

| Tier | Contents | Rationale |
|---|---|---|
| **MVP** (S0–S5) | Shell, Overview, Validation, Findings, Build | The four surfaces that make the *science* checkable. **The platform is credible without the Data browser.** |
| **v1.0** (S6–S8) | Data surface, light theme, quality hardening | The researcher's instrument, plus the polish that makes it professional |
| **Future** (S9+) | WebGL, search, command palette, RMF, GOES, onset latency, r2 | Genuine enhancements, none load-bearing |

**Why Data is not MVP.** It is the largest engineering lift in the project (coverage calendar, synchronized time axis, 490k-value spectra, worker decoding) and the *only* surface whose absence does not weaken a single credibility claim. Shipping S0–S5 first means the project is publicly defensible ~40% into the build. **Sequencing the hardest work after the credibility work is the single most important decision in this roadmap.**

---

## SPRINT 0 — Foundation

**Objective.** A deployed, empty, correctly-configured application with the full CI pipeline green.

**Deliverables.** Next.js App Router + `output: 'export'` · TypeScript strict + `noUncheckedIndexedAccess` · `tokens/*.json` + `scripts/generate.ts` (tokens only) · Tailwind from generated tokens · IBM Plex Sans + Mono subset, self-hosted · `eslint-plugin-boundaries` config · CI: 4 gates · Cloudflare Pages deploy · `_headers` with strict CSP · one page stating what the project is, with the independence statement.

**Dependencies.** None.

**Acceptance.** `pnpm verify && pnpm test && pnpm budget` green · deployed URL live over HTTPS · CSP blocks all external origins (verified by attempting an external fetch) · Lighthouse a11y = 100 on the single page.

**Success metrics.** CI wall time **< 4 min** · initial JS **< 40KB gz** · **build-time-per-page measured and recorded** (feeds the R5 decision from Part 3).

**Risks.** *Static export blocks a needed feature* — mitigated by having verified in §9.4 that we use none. *Font subsetting breaks glyphs* — mitigated by a rendering test over the scientific glyph set.

**Rollback.** Repo is empty of product code; revert is `git reset`.

**Complexity.** Low. **~3 days.**

---

## SPRINT 1 — The evidence spine

**Objective.** Prove the platform's central mechanism end-to-end on a single number: **a value cannot appear on screen unless it exists in a committed artifact.**

**Deliverables.**
- `openapi.yaml` v0 (envelope, `Quantity`, `ModelMetric`, `ArtifactRef`, `overview.json`)
- `scripts/generate.ts` extended: OpenAPI → `generated/api.ts`
- `scripts/web/derive.py` v0 — reads `freeze_manifest.json` + `benchmark_results.json`, emits `overview.json` + `measurements.json`; opens dataset `O_RDONLY`
- `artifacts.lock.json` with all three hashes; CI verifies
- `generated/measurements.ts` codegen with **E1** (unresolvable pointer → fail)
- `<SourceRef>`, `<MetricCard>` (Server Component, `source` required, `trend?: never`)
- **`scripts/check.ts` with the L2 evidence-consistency test**
- ESLint rule `no-measurement-literals` (**E2**)
- A page rendering **six real metrics**: 424/436 days · 389/391 orbits · 581 events · 3,560,092 rows · 5,199 provenance records · 6 contradictions

**Dependencies.** S0.

**Acceptance.** **L2 passes: every rendered number equals its artifact value, verified by re-reading the artifact from disk** · deliberately corrupting one artifact value **fails CI** (negative test, committed) · a hand-typed number in JSX fails lint (negative test, committed) · a stale JSON pointer fails codegen (negative test, committed).

**Success metrics.** 6/6 metrics traced · **3/3 negative tests fail correctly** · zero numeric literals in JSX.

**Risks.** *L2 proves harder than expected* — this is the sprint's entire purpose; if it cannot be built, the honesty guarantee is aspirational and the whole specification must be reconsidered. **Placing it in Sprint 1 is deliberate: it is the assumption most expensive to discover late.**

**Rollback.** Revert to S0 deployment. No user-facing surface lost.

**Complexity.** **High** — the hardest conceptual work in the project, and correctly placed first. **~5 days.**

---

## SPRINT 2 — App shell and Overview

**Objective.** A complete, honest front door.

**Deliverables.** Persistent header (wordmark, nav, `<DatasetVersionChip>`, GitHub, theme toggle stub) · footer with the full independence statement · `<IdentityBlock>` with independence above the fold · `<ArcTimeline>` (synthetic→real→validated→ML-tested) · six `<MetricCard>`s · `<FindingStatement>` · four `<PersonaDoor>`s · **static SVG coverage visualization** (424 days, gaps hatched, clickable date bands — no WebGL) · responsive 3 breakpoints · banned-lexicon check in `scripts/check.ts`.

**Dependencies.** S1.

**Acceptance.** All numbers via `M[...]` · independence statement present above the fold and in the footer on every route · banned-lexicon check green · keyboard-complete · Lighthouse a11y 100, perf ≥ 95 · **coverage SVG conveys availability and activity without color-alone encoding.**

**Success metrics.** JS **< 120KB gz** · LCP **< 1.5s on Moto G Power / 4G** · CLS **< 0.02**.

**Risks.** *Overview becomes a marketing page.* Mitigated by the banned-lexicon gate and the rule that every headline number carries a denominator.

**Rollback.** Revert to S1's single page.

**Complexity.** Medium. **~4 days.**

---

## SPRINT 3 — Validation ★ highest-value sprint

**Objective.** Ship the credibility engine: the six-contradiction public adjudication record.

**Deliverables.** `derive.py` parses `CONTRADICTION-001…006.md`, `PARSER_SPECIFICATION.md` §10, `MILESTONE_VIII_VALIDATION_REPORT.md` → structured JSON · OpenAPI extended · `<ValidationStatusBoard>` (188/188 tests, 6 PASS states) · `<ContradictionLedger>` · `/validation/[id]` five-act route: `<ContradictionTimeline>` → `<EvidenceBlock>` → `<DecisionBlock>` (**with `rejected` alternatives**) → `<SpecDiff>` (build-time diff) → `<ResultBlock>` · `<SpecRevisionTimeline>` r0→r6 · `<OpenQuestionCard>` for A-14 · `<Disclosure>` · `<DocRenderer>`.

**Dependencies.** S1 (evidence spine), S2 (shell).

**Acceptance.** All 6 contradictions render all five acts · **the r5 rejected-alternative is visible without expanding anything** · A-14 renders as **OPEN**, not hidden · spec diff uses `<ins>`/`<del>` with `+`/`−` text markers · every act is deep-linkable · **markdown remains the source of truth — the site never restates a decision in its own words** (verified by a test asserting rendered decision text is a substring of the source `.md`).

**Success metrics.** JS **< 60KB gz** (the strictest budget in the platform — the reviewer's page must be the fastest) · LCP **< 1.0s** · **Reviewer E2E journey: landing → full evidence for CONTRADICTION-001 in ≤ 2 clicks.**

**Risks.** *Markdown parsing is brittle across six differently-formatted documents.* **Mitigated by adding explicit YAML front-matter blocks to the six source documents** — a small, honest edit to the science repo that makes the record machine-readable, benefiting the API as much as the site. *Structuring loses nuance* — mitigated by always linking the full source document alongside the structured view.

**Rollback.** Remove `/validation` from nav; route remains deployed but unlinked.

**Complexity.** Medium-High. **~5 days.**

---

## SPRINT 4 — Findings

**Objective.** Publish the scientific conclusions, including the negative result, with full uncertainty.

**Deliverables.** `derive.py` emits `findings/index.json`, `benchmark.json`, `ablation.json`, `curves-{task}.json`, `limitations.json` · `<BenchmarkTable>` (8 models × 2 tasks) · `<CIBar>` with numeric labels and text "indistinguishable" verdicts · **`<RocCurve>` built concretely against ECharts — no `<ScientificChart>` abstraction (Part 3 R1)** · `chartDefaults()` shared config encoding §5.6 rules · `<ProtocolPanel>` (split, autocorrelation 0.997→0.643, 581 events not 564,160) · `<AblationTable>` · `/findings/limitations`.

**Dependencies.** S1, S2.

**Acceptance.** **Every model metric renders with its CI — enforced by `ModelMetric` typing, verified by a test that no metric renders without an interval** · LightGBM prediction shows `−0.0229 [−0.0445, −0.0004]` labelled **"significantly worse"** in text · spectral null (+0.0033) rendered at **identical visual weight** to positive findings (verified in visual regression) · limitations reachable from every findings claim · benchmark table scrolls horizontally inside its container, never the page body.

**Success metrics.** JS < 160KB gz · LCP < 1.2s · **ML-Engineer E2E: landing → split rationale + autocorrelation justification in ≤ 3 clicks.**

**Risks.** *The negative result gets visually softened.* Mitigated by the equal-weight visual-regression assertion — a design that de-emphasizes an inconvenient finding is dishonest regardless of its text.

**Rollback.** Unlink from nav.

**Complexity.** Medium. **~4 days.**

---

## SPRINT 5 — Build ▸ **MVP COMPLETE**

**Objective.** Make reproduction executable, and close the MVP.

**Deliverables.** `build.json` (commands, wall times 6.8 min / 93.75 min, env pins, `requirements.lock` SHA, 188/188) · `<CommandBlock>` with copy · `<HashTable>` (`43fd0e22…` + per-table) · `<EnvironmentPanel>` incl. the documented numpy-pin incident · `<DownloadTable>` · `<TestSummary>` · **`#architecture` section absorbing the former Pipeline page (Part 4 revision R-A)** · lazy `<ApiExplorer>` · published `openapi.yaml` · `/privacy` · `#accessibility` statement.

**Dependencies.** S1, S2.

**Acceptance.** A clean-machine follow of the reproduce steps yields the recorded hash (**executed once, manually, and recorded**) · Swagger loads only on scroll into view · raw spec available if Swagger fails · every fail-loud rule F-01…F-21 documented in the architecture section.

**Success metrics.** JS < 80KB gz initial (+400KB lazy) · **all six persona E2E journeys pass** · **zero surfaces without a primary persona.**

**Risks.** *Downloads exceed host limits.* Mitigated by linking GitHub Release assets rather than self-hosting the 597MB dataset.

**Rollback.** Unlink from nav.

**Complexity.** Low-Medium. **~3 days.**

> ### ▣ MVP GATE — the project is publicly defensible here
> Four surfaces, every number traced, the adjudication record public, the negative result published, reproduction executable. **If the project stopped at Sprint 5, it would still be more credible than the overwhelming majority of research platforms.** Everything after this is capability, not credibility.

---

## SPRINT 6 — Data I: coverage, light curve, GTI

**Objective.** Browse real observations. No spectra yet.

**Deliverables.** `derive.py` emits `coverage.json`, `days/{date}/meta.json`, `lightcurve.json` (**JSON, not binary — Part 4 revision R-C**), `gti.json`, `provenance.json` · `<CoverageCalendar>` (single SVG, ~866 cells, hatched gaps with reasons) · `<LightCurveViewer>` on canvas with LTTB + declared decimation · `<GtiStrip>` (inclusive endpoints per r2, convention stated in tooltip) · `<ProvenanceExplorer>` (**one variant — Part 4 revision R-D**) · `<DayHeader>` · `<EmptyState>` with required `reason` · `/data/[date]` static pages · URL-encoded filters.

**Dependencies.** S0 (build-time measurement), S2.

**Acceptance.** **2024-05-14 renders the X8.7 flare peak at 16:49 UTC** (against GOES 16:51) · gaps break the line, never interpolate · a day with no science products states the F-12 reason · every chart has a working "view as data" table · `←/→` steps days from the keyboard.

**Success metrics.** JS < 180KB gz · LCP < 1.8s · day switch **< 300ms** · **build time for ~500 date pages recorded; if > 10 min, R5 fallback triggers.**

**Risks.** *866-cell calendar hydration cost* — mitigated by single-SVG rendering with delegated events (no per-cell React node). *Static page count blows build time* — R5 trigger and fallback pre-defined in Part 3.

**Rollback.** Unlink `/data`; MVP surfaces unaffected.

**Complexity.** High. **~6 days.**

---

## SPRINT 7 — Data II: spectra and time-axis synchronization

**Objective.** The platform's hardest technical problem: 489,600 values/day, no server.

**Deliverables.** Binary format v1 (**spectrum only**) with dtype in header and **F-21 overflow guard** · `derive.py` emits `spectrum-l0.bin` (60×C) and `spectrum-full.bin` (1440×C), **failing loudly on dtype overflow** · Web Worker: decode + rebin · `<SpectrumViewer>` (viridis, heatmap + profile, hover **and keyboard** numeric readout, legend with scale ticks) · `<TimeAxisController>` (Zustand, transient cursor updates) · brush-zoom synchronizing light curve + spectrum + GTI · `ChannelIdx` branded type + required `channelSpace` discriminant · mobile 5-band degradation with an honest note.

**Dependencies.** S6.

**Acceptance.** **Payload measured on the ten highest-count days; p95 `spectrum-full` ≤ 400KB gz or the pre-committed fallback ships** · brush-zoom keeps all three panels aligned to the minute (asserted in an E2E test comparing rendered domains) · **a synthetic overflow input makes `derive.py` fail, not wrap** (negative test) · a CZT array passed to a SoLEXS-typed viewer is a **compile error** (negative test via `tsd`) · keyboard cell navigation announces channel, time, value.

**Success metrics.** `spectrum-l0` first paint **< 300ms** · zoom after full load **< 16ms/frame, zero network** · JS < 220KB gz.

**Risks.** *Payload exceeds budget* — falsification and fallback pre-committed (§9.3). *Worker complexity* — mitigated by keeping the worker to two pure functions (`decode`, `rebin`) already unit-tested at 100% branch coverage in `lib/science`. *Axis desync* — structurally prevented by the single shared store, and asserted in E2E.

**Rollback.** Ship `spectrum-l0` only at fixed zoom levels; light curve and GTI remain fully functional. **The sprint degrades rather than fails.**

**Complexity.** **Highest in the project.** **~7 days.**

---

## SPRINT 8 — Quality hardening ▸ **v1.0 COMPLETE**

**Objective.** Make it professional across themes, devices, and assistive technology.

**Deliverables.** Complete light theme (all tokens recomputed; viridis and Okabe–Ito unchanged) · manual a11y passes (VoiceOver/Safari, NVDA/Firefox, keyboard-only, 200% zoom, 400% reflow) · **10 visual-regression baselines (5 surfaces × 2 breakpoints, dark; light spot-checked) — Part 4 revision R-E** · Lighthouse CI on all 5 surfaces · budget enforcement wired to CI · link check · Cloudflare Web Analytics · README + CONTRIBUTING · accessibility statement finalized with named exceptions.

**Dependencies.** S2–S7.

**Acceptance.** Lighthouse a11y **100 on all 5 surfaces** · perf ≥ 95 on all · zero axe violations · **every budget met on Moto G Power / 4G** · all four CI gates green · every documented component state has a test.

**Success metrics.** CI wall time **< 12 min** · zero budget overruns · **v1.0 tagged and released.**

**Risks.** *Light theme breaks chart legibility* — mitigated because the data palette and viridis are luminance-safe on both grounds by construction.

**Rollback.** Light theme is a token swap; revert to dark-only without touching components.

**Complexity.** Medium. **~4 days.**

---

## 15.2 Summary

| Sprint | Deliverable | Tier | Days | Cumulative |
|---|---|---|---|---|
| S0 | Foundation | MVP | 3 | 3 |
| S1 | **Evidence spine** | MVP | 5 | 8 |
| S2 | Shell + Overview | MVP | 4 | 12 |
| S3 | **Validation** | MVP | 5 | 17 |
| S4 | Findings | MVP | 4 | 21 |
| S5 | Build ▸ **MVP** | MVP | 3 | **24** |
| S6 | Data I | v1.0 | 6 | 30 |
| S7 | Data II | v1.0 | 7 | 37 |
| S8 | Quality ▸ **v1.0** | v1.0 | 4 | **41** |

**~41 focused days to v1.0; ~24 to a publicly defensible platform.** Future work (S9+): WebGL coverage sphere, search, command palette, GOES overlay, onset-latency metric, RMF, dataset r2 — **none blocking, none load-bearing.**

---

# SECTION 16 — CRITICAL DESIGN REVIEW (Parts 1–4)

Reviewing the complete specification with no deference to earlier decisions.

## 16.1 Revisions — accepted and applied

### ▸ R-A. The Pipeline page does not earn a top-level slot. **CUT.**
Part 1 justified six surfaces by mapping them to six personas. Reviewing the whole document, **Pipeline's primary persona is the contributor — and so is Build's.** One persona, two primary surfaces, is exactly the redundancy Part 1's own test was meant to catch. Pipeline's content (architecture flow, F-01…F-21, code links) is orientation material for someone who is already reproducing the build.

**Applied:** Pipeline becomes `/build#architecture`. **Five surfaces.** No content lost, one fewer route, one fewer nav item, one fewer page to maintain forever. *I failed my own test in Part 1 and it took reading Parts 1–3 together to see it.*

### ▸ R-B. IBM Plex Serif on one route is not defensible. **CUT.**
Part 2 gave it a Sprint-5 kill criterion. Reviewing end-to-end: it serves one route, adds a third family, and its "serif = argument" semantics are already carried by layout, the 68ch measure, and `<DocRenderer>`. **Two families: Plex Sans + Plex Mono.** The epistemic type system survives — interface vs. measurement is the distinction that actually does work; argument was decoration wearing a rationale.

### ▸ R-C. Binary encoding for light curves is premature optimization. **REVISED.**
1,440 points as JSON is ~26KB, ~6KB gzipped. The binary version saves perhaps 2KB while requiring a header parser, a dtype guard, and a decode path. **Light curves ship as JSON. Binary is used for spectra only**, where it saves ~4× on a 200KB payload and is genuinely load-bearing. This also removes binary decoding from Sprint 6 entirely, de-risking the sprint.

### ▸ R-D. Component variants specified before any use. **REVISED.**
`<ProvenanceExplorer>` had three variants, `<LightCurveViewer>` three, `<CoverageCalendar>` three, `<SpectrumViewer>` three — twelve variants, zero implementations. **Each ships with exactly one variant. A second appears when a second real use exists.** The variant lists in §6 are downgraded from specification to *anticipated extension points*, explicitly non-binding.

### ▸ R-E. 36 visual-regression baselines is unmaintainable solo. **REVISED.**
36 baselines × every legitimate design change = a review burden that will be discharged by bulk-approving diffs, which converts the test into a screenshot archive. **10 baselines** (5 surfaces × 2 breakpoints, dark theme; light spot-checked manually per release). Component-level stories cover state coverage more cheaply and more stably.

### ▸ R-F. Search and command palette are not v1 features. **DEFERRED.**
The searchable corpus is 6 contradictions (all listed on one page), ~500 dates (a calendar), 21 rules (one page), 15 endpoints (one spec). **Every destination is reachable in ≤ 3 clicks without search.** Shipping a search index and a trigram matcher for a corpus that fits on five pages is tooling in search of a problem. Both move to S9+, and `search-index.json` is removed from `derive.py` (Part 3 R7).

### ▸ R-G. Density toggle is unearned. **CUT.**
Justified in Part 2 by "recruiter vs researcher have opposite needs." Reviewing the whole spec: the recruiter reads Overview (six cards, low density) and the researcher reads Data (charts, density-irrelevant). **The two personas already use different surfaces.** A global toggle solves a conflict that the information architecture already resolved. Cut; the default is tuned per surface.

### ▸ R-H. Python type generation from OpenAPI is one generator too many. **REVISED.**
Part 3 specified `datamodel-code-generator` → Pydantic models → `derive.py`. But `derive.py` **writes** JSON; it does not consume it. Generating producer types buys little over **validating the output against the spec**, which CI does anyway (A2). **`derive.py` writes plain dicts and validates against `openapi.yaml` before writing.** One generator removed, identical guarantees, one less toolchain to keep alive.

### ▸ R-I. Custom client-error beacon is unjustified at v1. **CUT.**
Most surfaces ship < 100KB of JS and several ship almost none. **Cut for v1.0.** If a real defect is reported that logging would have caught, add it then. Building telemetry for hypothetical errors on a five-page static site is exactly the reflex this document exists to resist.

### ▸ R-J. The `<SunHero>` WebGL element should not be in v1.0. **RE-SEQUENCED — your call.**
Reviewing the whole specification, it is the only element that: costs 120KB (≈ two entire surfaces' budgets), requires a fallback that must be built anyway, cannot be visually regression-tested, and carries zero credibility weight for five of six personas.

**Recommendation:** ship the static SVG coverage visualization in Sprint 2 (it conveys the same two variables and is *also* clickable), and add the WebGL sphere in **S9** once the platform is complete — where it is a genuine enhancement rather than a risk on the critical path.

**This walks back your original "full WebGL animations" request, so I want to be explicit rather than quiet about it.** I am not deleting it; I am sequencing it last. If you want it in v1.0, it slots into Sprint 8 with a +2-day cost and the §6.11 constraints (encodes real data, one page, kill criterion, no post-processing) unchanged. **That is a scope call, and it is yours to make.**

### ▸ R-K. Custom tooling was accumulating. **CONSOLIDATED.**
Across Parts 1–3 I had specified `gen-types`, `gen-tokens`, `gen-measurements`, `check-budgets`, `check-invariants`, plus two ESLint rules and `derive.py` — **seven artifacts of bespoke tooling before one component existed.**

**Consolidated to four:**
| Artifact | Contents |
|---|---|
| `scripts/generate.ts` | tokens → CSS/Tailwind/TS · OpenAPI → TS · measurements → TS |
| `scripts/check.ts` | evidence consistency (L2) · budgets · invariants · banned lexicon |
| `scripts/web/derive.py` | Stage 2 derivation + spec validation |
| 2 ESLint rules | `no-measurement-literals` · `no-unjustified-client` |

## 16.2 Criticisms considered and rejected

**"Five surfaces is still too many for a solo project."** No. Each maps to a distinct persona job (convert / verify / use / evaluate / reproduce), and §4.7's matrix — recomputed after cutting Pipeline — still shows every surface with a primary persona and every persona with a primary surface.

**"The evidence-consistency test is over-engineering."** It is the least optional thing in the document. Everything else here is craft; this is the product's integrity, mechanized.

**"Two dataset-version axes are premature with one version."** The URL scheme cannot be retrofitted without breaking every citation. **Getting URLs right on day one costs nothing; getting them wrong is permanent.** The *selector UI* is correctly deferred.

**"WCAG AAA contrast is perfectionism."** It costs one token-value decision and benefits every user in every session. Free correctness is not perfectionism.

**"41 days is optimistic for a solo developer."** Probably — and the MVP gate is why the estimate's accuracy does not matter much. If S6–S7 take double, the platform has been publicly defensible since day 24.

## 16.3 Post-review state

| Metric | Part 1–3 | After Part 4 review |
|---|---|---|
| Top-level surfaces | 6 | **5** |
| Font families | 3 | **2** |
| Custom tooling artifacts | 7 | **4** |
| Custom lint rules | 10 → 2 | **2** |
| CI gates | 7 → 4 | **4** |
| Component variants specified upfront | 12 | **0** |
| Visual-regression baselines | 36 | **10** |
| Binary formats | 2 uses | **1** (spectra only) |
| Codegen pipelines | 4 | **3** |
| Runtime services | 0 | **0** |
| v1.0 features not required by a persona | 3 (search, palette, density) | **0** |
| Premature abstractions | 1 (`ScientificChart`) | **0** |

---

# SECTION 17 — FINAL VERDICT

## 17.1 The five-reviewer test

**NASA Earthdata — ✅ Approve.** Data provenance to source file and SHA-256; documented instrument conventions (inclusive GTI, three channel spaces); gaps rendered as gaps; no interpolation; viridis rather than a rainbow map; explicit statement that no RMF means no keV. They would ask for a DOI and a formal citation block — **added to Sprint 5 acceptance as a `CITATION.cff` and a citation panel on Build.**

**Palantir — ✅ Approve, with one push-back.** Information density, keyboard completeness, provenance as a first-class object, and URL-encoded state for shareability all match how their analysts work. They would push back on the absence of cross-day analysis. **Answer: §9.7's escape hatch is designed, not improvised — and building it before a user needs it would be speculative.**

**Linear — ✅ Approve.** Five surfaces, no dropdowns, no modals for content, `g`-prefixed navigation, native scroll, motion that is fast and one-shot. They would question cutting the command palette; **the answer is that their corpus is thousands of issues and ours fits on five pages.** Adopting a pattern without its precondition is cargo-culting.

**Apple HIG — ⚠️ Approve with reservations.** Typography, spacing, restraint, and accessibility all conform. They would object that the interface is *dense and expert-oriented* — and they would be right. **It is deliberate:** the primary users are researchers reading benchmark tables, not consumers. Where density conflicts with clarity (mobile spectra), we degrade honestly rather than compress illegibly.

**OpenAI — ✅ Approve, and would likely single out the negative result.** The platform's headline is *"ML provides no operational benefit; use a threshold."* Publishing `−0.0229 [−0.0445, −0.0004]` as *significantly worse* — at the same visual weight as a positive finding, enforced by a visual-regression assertion — is the rarest thing in this specification.

**Verdict: approved by all five, with two documented reservations, both of which are deliberate trade-offs I can defend in a room.**

## 17.2 Decisions I would defend under hostile questioning

1. **No runtime server.** Every response is enumerable; a server would add cost, risk, and mortality to serve unchanging bytes.
2. **The evidence-consistency test.** The only test that verifies the platform's central claim, closing the loop from rendered pixels to committed artifact.
3. **`trend?: never`.** One line that makes the wrong thing unbuildable rather than merely discouraged.
4. **`ModelMetric` requiring `ci95` in schema, validator, and type.** A scientific principle enforced by three compilers.
5. **Required `channelSpace` discriminant + branded `ChannelIdx`.** The dataset's most dangerous error (F-11) made a compile error.
6. **Validation at nav position 2.** Method before results is an argument made by information architecture.
7. **Data deferred past the MVP gate.** The hardest work sequenced after the credibility work.
8. **Okabe–Ito and viridis.** Peer-reviewed, colorblind-safe, grayscale-correct, and recognizable to the audience. Inventing a palette would trade accessibility for taste.
9. **No photography.** Every image is generated from the archive, so the visitor always knows which pixels are data.
10. **The affiliation firewall.** Under-claiming costs nothing; over-claiming costs the project.

## 17.3 The one thing I would change if forced to change one thing

**Cut the light theme from v1.0.** It is the largest remaining piece of work whose absence would harm no persona's *stated* journey. I keep it because reviewers screenshot figures into papers and slides, which are light-background media — but it is the honest answer to "what is least load-bearing," and it is a token swap, so deferring it costs nothing structurally.

---

# EXECUTIVE SUMMARY

## Why this architecture exists

AdityaNet's scientific state is frozen: a canonical dataset of 3,560,092 rows across 1,985 files, hash `43fd0e22…`, with 5,199 provenance records, six publicly adjudicated contradictions, and a benchmark whose headline conclusion is negative — **a threshold on the SoLEXS count rate matches or beats every learned model, and spectral resolution does not improve detection.**

Nothing about that changes at runtime. The architecture takes that fact seriously rather than working around it: **there is no server, no database, no cache, and no runtime state.** Every possible API response is pre-computed at build time, hash-pinned to the frozen dataset, and served as an immutable file. The application is a folder that will still work in ten years on any static host.

The interface is organized around one idea — **epistemic role** — which determines typography, color, and motion. A measurement looks like a measurement; an interface control looks like a control; and the two never share a color space, so a chart series can never be mistaken for a link and a theme change can never alter the meaning of a published figure.

## Why it is scientifically credible

Because credibility is enforced by the build rather than promised in a README.

- A developer **cannot type a number into this application.** They write an artifact reference; codegen resolves it; a lint rule rejects literals; and a test re-reads the original artifact from disk and asserts the rendered string matches. That test's error budget is **zero, forever.**
- A model metric **cannot render without a confidence interval** — required in the OpenAPI schema, the validator, and the TypeScript type.
- A spectrum **cannot be mislabelled across the three incommensurable channel spaces** — the discriminant is required and the index is branded, so the dataset's most dangerous error is a compile error.
- A count value **cannot silently overflow its encoding** — the derivation fails loudly (F-21) rather than wrapping a flare peak.
- Marketing vocabulary and false liveness claims **fail CI.**
- The negative result renders at the same visual weight as every positive one, asserted in visual regression.

The credibility surface — the six-contradiction adjudication record, including the alternatives the owner *rejected* — sits at navigation position two, before the data and before the results, and carries the strictest performance budget in the platform.

## Why it is maintainable

The complete inventory of things that must be kept alive: **one Next.js static export, three codegen steps, two check scripts, two ESLint rules, one Python derivation script, and one hand-written OpenAPI file.**

There is no service to operate, no schema to migrate, no cache to invalidate, no secret to rotate, no dependency on a cloud vendor's proprietary features, and no runtime that can wake anyone at night. Old API versions are never deleted because immutable files cost nothing to keep — so every citation resolves forever.

Every design principle that could be violated silently was converted into a compiler error, a codegen failure, or a build gate, because a principle enforced by developer discipline has a half-life of about six months. Every principle enforced by CI has none.

## Why it is right for a solo engineer building a long-lived research platform

Because the plan is honest about the constraint. It ships a **publicly defensible platform at day 24** — Overview, Validation, Findings, and Build, every number traced — and sequences the hardest engineering (synchronized time axes, 489,600 values per day with no server) *after* the work that establishes credibility. If the schedule slips, what slips is capability, not integrity.

The final review deleted a page, a font family, twelve unbuilt component variants, a search index, a density toggle, a telemetry beacon, three custom tools, and twenty-six screenshot baselines — **not to make the platform smaller, but because a solo maintainer's real budget is attention, and every unused abstraction spends it forever.** Abstraction is extracted from two real uses, never anticipated from two imagined ones.

What remains is a platform with **zero runtime services, zero premature abstractions, and zero v1.0 features that no persona requires** — where the most sophisticated engineering in the codebase exists for exactly one purpose: to make it structurally impossible for the website to say something the science does not.

---

**◼ END OF SPECIFICATION — Parts 1–4 complete.**

**Ready to enter Implementation Mode on your word.** Two open decisions I need from you first:

1. **`<SunHero>` WebGL (R-J)** — ship the static SVG in Sprint 2 and add WebGL in S9 as recommended, or pull it into v1.0 at +2 days?
2. **Commit this specification** to `docs/web/PRODUCT_SPECIFICATION.md` as a governing document before Sprint 0?

Say **Implementation Mode** and I'll begin with **Sprint 0 — Foundation**.
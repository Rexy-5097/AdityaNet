# Engineering Journal

The working record of AdityaNet's web platform: what broke, what the evidence said,
what was decided, and what it cost. Entries are append-only. A decision later reversed
stays, because the reasoning that failed is more instructive than the one that held.

---

## 2026-07-23 · Sprint 0 · The framework floor

**Problem discovered.** A page with zero interactive components shipped 184.2 KB gz of
JavaScript under Next.js 16 App Router with `output: 'export'`.

**Evidence.** `scripts/check.ts` parsed the built HTML and gzipped each referenced
asset: 9 chunks, largest 71.0 KB (`react-dom`, containing `hydrateRoot`). Confirmed a
production build by grepping for React's dev-only warning strings — none present. The
App Router hydrates unconditionally, so this is a floor, not a misconfiguration.

Astro, same content: **0 bytes, no `<script>` tag at all.**

**Root cause.** The framework was chosen by convention. The architecture document had
already concluded, correctly, that the platform needs no runtime server — and then a
framework built around a server-plus-hydration model was adopted anyway, without
measuring what that model costs when you use none of it.

**User impact.** Every route budget in the specification sat *below* the Next floor:
`/validation` at 60 KB, `/build` at 80 KB, `/findings` at 160 KB. They were not
ambitious targets, they were arithmetic that could not be satisfied. The argument that
the credibility surface should be the fastest page on the site was unachievable.

**Decision.** Migrate to Astro with React islands. → ADR-0002.

**Tradeoffs.** Lost: a WebGL context persisting across route changes. Accepted, because
the immersive experience lives at a single route, and a cinematic transition between
two reading surfaces would be motion without meaning. Gained, beyond the payload: a
strict `script-src 'self'` CSP became achievable, since removing the RSC payload
removed the inline scripts that had forced `'unsafe-inline'`.

**Performance impact.** `/` went from 184.2 KB to 0.0 KB gz of JavaScript.

**Follow-up.** None outstanding. Migration completed within the same sprint, before any
product code existed — which is the cheapest moment this decision was ever available.

---

## 2026-07-23 · Sprint 0 · Two estimates, both wrong, both low

**Problem discovered.** A pre-registered estimate for the three.js bundle (220–280 KB
gz) was wrong. Measured: **314.17 KB**.

**Evidence.** Vite production build. three + R3F + drei + postprocessing + React =
314.17 KB gz. Stripping drei *and* postprocessing = 292.57 KB gz.

**The consequential finding.** The entire effects stack costs **21.6 KB** — about 7%.
The specification's pre-committed fallback, "drop `postprocessing` if over budget,"
would have sacrificed bloom, tone mapping, and the whole post pipeline to recover
almost nothing. three.js core (~245 KB) is the real floor and is irreducible.

**Root cause.** Two estimates in one sprint, both about framework baselines, both low.
That is not bad luck, it is a bias: framework baselines are invisible in the source
tree, so whoever reads only their own code systematically underestimates them.

**Decision.** Accept three.js. Retain drei and postprocessing. Raise `/` to 450 KB gz
lazy, post-LCP. Void the fallback explicitly rather than leaving a plan that would fail
when invoked. → ADR-0005.

**Follow-up.** The correction is mechanical, not a resolution to be careful:
`check.ts` measures transfer size from built HTML and never asks the bundler.

---

## 2026-07-23 · Sprint 0 · Operating-system metadata in the deployable output

**Problem discovered.** 61 macOS AppleDouble files (`._*`) inside `dist/`.

**Evidence.** `find dist -name '._*' | wc -l` → 61, after a clean build.

**Root cause.** The project volume is not HFS+, so macOS writes sidecar files beside
every file it touches — including files Astro creates *during* the build. They were not
copied in from `public/`; they were generated in place.

**User impact.** They would have been uploaded to a public CDN. AppleDouble files carry
resource forks and extended attributes, which can include the originating path and
quarantine provenance. A small but genuine information leak.

**Engineering impact.** Invisible in code review. Nothing in the source tree mentions
these files, so no amount of reading the repository would have surfaced them.

**Decision.** `scripts/postbuild.ts` strips them; `check.ts` asserts the directory is
clean afterwards. Belt and braces, because a silent failure in the remover would
otherwise restore the leak.

**Tradeoffs.** A fifth bespoke tooling artifact against a budget of four. Justified in
the file header: the alternatives were a non-portable shell one-liner in `package.json`,
or making a validator mutate the thing it validates.

**Follow-up.** None. Also fixed alongside: Fontsource's unsuffixed entrypoints were
emitting 28 font files (Cyrillic, Greek, Vietnamese) for an English-language platform.
Latin-only imports reduced this to 5.

---

## 2026-07-23 · Sprint 0 · The specification's own numbers were wrong

**Problem discovered.** Eight of nine contrast ratios stated in specification §5.2.2
disagreed with measurement.

**Evidence.** `scripts/check.ts`, computing WCAG 2.2 relative luminance against
`--color-base` `#0A0C0E`:

| Token | Claimed | Measured |
|---|---|---|
| `--color-fg` | 16.1:1 | 16.36:1 |
| `--color-fg-muted` | 7.4:1 | 8.13:1 |
| `--color-accent` | 6.8:1 | 7.11:1 |
| `--color-pass` | 7.1:1 | 7.71:1 |
| **`--color-open`** | **8.4:1** | **7.76:1** — overstated |
| `--color-fail` | 5.4:1 | 5.84:1 |

**Root cause.** The figures were computed by hand while writing the specification and
never verified.

**User impact.** None — all values clear their accessibility floors. The impact is to
credibility, not to users.

**Engineering impact.** In a document whose first principle is *every number cites its
source*, nine unsourced numbers is the sharpest possible demonstration of why that
principle exists. It was found in Sprint 0 by the gate built to enforce it.

**Decision.** Amend the specification to the measured values, with a dated correction
note. Measured values take precedence over estimated ones — confirmed by the owner as
a standing rule.

**Follow-up.** None. `check.ts` now enforces these on every build, so they cannot drift
again.

---

## 2026-07-23 · Sprint 1 · A frozen scientific artifact is not valid JSON

**Problem discovered.** `JSON.parse` refused `artifacts/v2/ml/benchmark_results.json`
outright.

**Evidence.**
```
Unexpected token 'N', ..." "brier": NaN, "... is not valid JSON
```

**Root cause.** Python's `json.dump` emits bare `NaN`, `Infinity`, and `-Infinity`
unless `allow_nan=False`. These are a Python extension; RFC 8259 has no such literals.
`json.load` accepts them back, so the defect is completely invisible from the pipeline
side. The affected fields are `brier` scores for models that emit hard classifications
rather than calibrated probabilities — legitimately undefined, encoded illegitimately.

**User impact.** None yet. Potentially severe: the OpenAPI-described API we intend to
serve would emit documents that any standards-compliant client rejects.

**Engineering impact.** Any non-Python consumer of these artifacts fails on load — not
degrades, fails. That includes the browser, and it would have included every downstream
researcher who tried to read our published API with a conforming parser.

**Decision.** Narrow, documented tolerance at the boundary: `parseScientificJson`
replaces bare `NaN`/`Infinity` in numeric positions with `null` before parsing. It
cannot mask a value mismatch, because a field that was `NaN` was never a number this
platform could display. Strings containing "NaN" are unaffected — the surrounding
punctuation is required to match.

**Tradeoffs.** Tolerance at the boundary is not endorsement. The correct fix is at
source (`allow_nan=False`, emit `null`), which requires regenerating ML artifacts.
Logged as **ISSUE-007**, not silently absorbed.

**Follow-up.** Fix at source on the next ML artifact regeneration.

**Lesson.** A serialisation defect that round-trips within one language is invisible
until a second language reads it. Cross-language consumption is a test, not a chore.

---

## 2026-07-23 · Sprint 1 · Prose had drifted from the data

**Problem discovered.** Written descriptions of the dataset were wrong in two places.

**Evidence.** `freeze_manifest.json` gives T1 = **424** files, T4 = **389**, T3 and T5 =
**373**. Project prose had been saying "389/391 HEL1OS orbits" as though one figure
covered the HEL1OS tables. Separately, `benchmark_results.json` gives nowcast test
`n_events` = **82**; the evaluation protocol document had estimated 155.

**Root cause.** Numbers recalled from memory and repeated across documents without
re-reading the artifact.

**User impact.** None — these appeared in internal documents, not on the site.

**Engineering impact.** This is precisely the failure the platform is built to prevent,
occurring in the platform's own documentation. It is the strongest available argument
for the `MetricCard` API taking a key rather than a value.

**Decision.** Every figure on `/` now resolves through a JSON pointer. The
`no-measurement-literals` gate (Sprint 2) extends this to prose.

**Follow-up.** Audit remaining prose in `docs/` against artifacts. Logged as
**ISSUE-008**.

---

## 2026-07-23 · Sprint 1 · `as const satisfies` made optional fields unreachable

**Problem discovered.** `astro check` reported 2 errors: `Property 'n' does not exist on
type '{ ... } | ... 4 more ... | { ... }'`.

**Evidence.** The generated registry was emitted as
`export const M = { ... } as const satisfies Record<MeasurementKey, Measurement>`.
`as const` narrows each entry to a literal object type, so `M[key]` over a key union
yields a *union of literal types*. Optional properties absent from some members are
therefore not accessible on the union.

**Root cause.** `as const satisfies` was applied because it is the current idiom, not
because the literal value types were needed. They bought nothing: the guarantee lives
in the `MeasurementKey` union, not in the values.

**Decision.** Emit `Readonly<Record<MeasurementKey, Measurement>>`.

**Tradeoffs.** Loses literal value types at call sites. Nothing depends on them.

**Lesson.** The type checker caught a cargo-culted idiom before it reached a component.
Precision that no consumer uses is not precision, it is friction.

---

## 2026-07-23 · Sprint 2 · The literal gate's first catch was a false positive

**Problem discovered.** `no-measurement-literals` flagged `"256"` in `SourceRef.astro`
on its first run — from the screen-reader label `SHA-256`.

**Evidence.** `measurement literal: src/components/evidence/SourceRef.astro has "256"
in template text.`

**Root cause.** The heuristic — flag any decimal, or any integer of three or more
digits, appearing in template text — cannot distinguish a datum from a digit bound
into an identifier.

**Decision.** Strip standards identifiers (`SHA|RFC|ISO|WCAG|UTF|ES|HTTP|AES|CSP`
followed by digits) before scanning. A standards name is a named constant: no
uncertainty, no denominator, no artifact to cite.

**Rejected alternative.** Raising the threshold to four digits. It would have silenced
this warning and simultaneously let every genuine three-digit measurement through —
581 events, 424 days, 340 channels. That is the wrong direction: a gate tuned by
loosening it until it stops complaining is not a gate.

**Verification.** After the fix, a deliberately inserted `"The archive contains 581 M/X
events."` in `findings.astro` was caught. Restored immediately.

**Tradeoffs.** The scan is source-text, not AST. Less precise than the ESLint rule the
specification calls for, but Astro template text nodes are awkward to reach through the
parser, and a half-working plugin that silently stops matching is worse than a blunt
check that visibly does. Logged as **ISSUE-009**.

**Performance impact.** None; the scan runs in the existing budget gate.

---

## 2026-07-23 · Sprint 3 · A colour token silently painted body text invisible

**Problem discovered.** Paragraphs on `/` rendered in the background colour. Not
low-contrast — `rgb(10, 12, 14)` on `rgb(10, 12, 14)`.

**Evidence.** Reading computed styles in a live browser:
`getComputedStyle(p).color` returned `rgb(10, 12, 14)`, which is `--color-canvas`.

**Root cause.** A semantic colour role was named `base`. Tailwind v4 derives utilities
from token names, and `--color-base` and `--text-base` both generate `text-base`. The
colour wins. Every `text-base` in the codebase — a *font-size* utility — became a
colour declaration.

**User impact.** Body copy invisible on the entry surface and on all five planned
surfaces. Severe, and it shipped through a full green build.

**Engineering impact.** Nothing failed. No error, no warning, no failing test, no type
error. The build passed, the screenshot looked plausible because the layout was intact,
and only the words were gone. This is the most dangerous defect class the project has
hit: silent, total, and invisible to every automated check that existed.

**Decision.** Rename the role `base` -> `canvas`, and add a build gate asserting that no
colour role shares a name with a font-size utility — checked against both our type scale
and Tailwind's built-in names.

**Verification.** Reintroducing `"base"` fails the build:
`token collision: colour role(s) "base" share a name with a font-size utility.`

**Tradeoffs.** The rename touched three files. Trivial next to the alternative, which was
a landmine that would fire again on the next colour role named after a size.

**Lesson.** In a token system that generates utilities by name, the token namespace is a
*shared* namespace. Collisions there do not error — they resolve, silently and wrongly.

---

## 2026-07-23 · Sprint 3 · The performance budget measured around the payload

**Problem discovered.** After shipping a ~300 KB WebGL island, the budget gate reported
`route / 0.0 KB gz JS (budget 450 KB, 0 scripts)`.

**Evidence.** Chunks on disk: `StarExperience` 240.7 KB gz, `client` 56.1 KB gz,
`scheduler` 4.5 KB gz. Gate output: 2.0 KB, then 0.0 KB.

**Root cause.** Two independent gaps. The gate counted only `<script src>` tags, and (a)
Astro's island bootstrap is an *inline* script, (b) island chunks are referenced through
`<astro-island component-url renderer-url>` attributes and then import further chunks —
none of which is a classic script tag.

**User impact.** None directly. The impact is that the budget could have been blown by
any margin without anyone noticing.

**Engineering impact.** A gate that reports a reassuring number is worse than no gate.
It was introduced in Sprint 0 specifically to prevent silent payload growth and would
have permitted exactly that.

**Decision.** Measure the transitive import closure: seed from every `/_astro/*.js` path
mentioned anywhere in the markup, then walk each chunk's imports recursively, and count
inline script bodies as payload.

**Performance impact.** Reported cost for `/` went 0.0 KB -> **291.9 KB gz** against a
450 KB budget. The number was always true; only the measurement was wrong.

**Lesson.** Verify a measurement against a case where the answer is known and large.
"Zero" was never plausible for a page carrying three.js.

---

## 2026-07-23 · Sprint 3 · Islands broke the strict CSP; hashes restored it

**Problem discovered.** `index.html: 2 inline <script> tag(s). These require
script-src 'unsafe-inline', which the CSP in public/_headers forbids.`

**Root cause.** Astro bootstraps client islands with inline `<script type="module">`.
Sprint 0's policy is `script-src 'self'` with no exceptions, so the island would have
been blocked in production while working perfectly in dev.

**Decision.** Compute the SHA-256 of each inline script at build time and inject
`'sha256-...'` into the deployed header. A static site cannot mint a per-request nonce
and does not need one: the scripts are fixed, so their hashes are too.

**Rejected.** `'unsafe-inline'` — permits *any* inline script, which is the injection
vector the policy exists to close. Astro's `security.csp` — emits a `<meta http-equiv>`
tag, which cannot express `frame-ancestors` and would sit alongside our header policy,
where the browser enforces the intersection and the header still blocks the scripts.

**Follow-up defect, same sprint.** The first implementation used `String.replace`, which
is non-global. The first occurrence of the placeholder token in `_headers` was inside an
explanatory comment, so the comment was patched and the live directive left untouched —
while the script reported success. Fixed with `replaceAll` and by removing the token from
prose. **A build step that reports success without verifying its own output is a lie with
a progress bar.**

---

## 2026-07-23 · Sprint 3 · The interaction shipped dead

**Problem discovered.** The star did not respond to dragging at all — the headline
interactive claim of the sprint.

**Evidence.** `getComputedStyle(container).cursor` returned `auto`. The orbit hook sets
`cursor: grab` when it binds listeners, so `auto` proved they had never bound.

**Root cause.** The container div renders only after quality-tier detection resolves. The
hook's `useEffect` ran on mount, when `ref.current` was still `null`, and its dependency
was the ref *object* — whose identity is stable — so it never re-ran when the node
finally attached.

**User impact.** Total loss of the sprint's only interaction.

**Engineering impact.** It built, type-checked, passed 30 unit tests, passed every gate,
and screenshotted correctly. Static analysis cannot see this: the code is valid, the
lifecycle is wrong.

**Decision.** Replace the `RefObject` + effect pattern with a callback ref, which fires
exactly when the node arrives and again with `null` when it leaves.

**Lesson.** "It renders" and "it works" are different claims requiring different
evidence. Interaction has to be exercised in a browser; a screenshot only proves paint.

---

## 2026-07-23 · Sprint 3 · Sidecar files corrupted data derivation

**Problem discovered.** `pyarrow.lib.ArrowInvalid: Could not open Parquet input source
'._20240201.parquet': Parquet magic bytes not found in footer.`

**Root cause.** The same AppleDouble sidecars from Sprint 0, third distinct
manifestation. `._20240201.parquet` glob-matches `*.parquet`.

**Engineering impact.** Notable because the failure surfaces as a confusing crash deep
inside a third-party library rather than an obvious "bad file". Any code in this
repository that globs a data directory must filter these.

**Decision.** Filter in `derive_star_timeline`, with a comment naming the pattern so the
next occurrence is recognised immediately.

---

## 2026-07-23 · Sprint 3.6 · My visual verification method was invalid for several iterations

**Problem discovered.** Screenshots taken to verify shader changes were showing the
static poster SVG, not the WebGL canvas. I bisected three shader changes against an
image that could not respond to any of them.

**Evidence.** `document.hidden === true` in the automated browser pane. Sprint 3 added a
GPU-pause optimisation — `frameloop={running ? "always" : "never"}` where
`running = onScreen && !document.hidden` — so the renderer correctly halted. The poster
sits underneath the canvas by design, so the page still looked plausible: a soft orange
disc where a star should be.

Confirmed by hiding the poster: the canvas rendered **nothing**.

**Root cause.** A correct optimisation interacting with a headless-ish verification
environment. Neither component is wrong; the combination silently invalidated the
measurement.

**Engineering impact.** Worse than a wrong result — a *confidently* wrong one. I reported
"significant regression, granulation gone" and ran two bisection builds against an image
that was never going to change. Had I not hidden the poster, I would have reverted three
correct changes.

**Resolution.** Override `document.hidden` at runtime before verifying, and re-trigger the
IntersectionObserver. Recorded as a standing rule: **before trusting a screenshot of the
experience layer, confirm the canvas is the thing being photographed.** The cheap check is
to hide the poster.

**Lesson.** The Sprint 3 lesson was "it renders" and "it works" need different evidence.
This is the next one along: *"I can see it"* and *"I am looking at it"* are also different
claims. A fallback that is designed to be invisible when it substitutes will, by
construction, be invisible when it substitutes wrongly.

**Follow-up.** FPS remains UNVERIFIED for this pass — rAF is throttled in a hidden
document regardless of the override, so the frame-timing harness cannot run here.

---

## 2026-07-23 · Sprint 3.7 · The raymarched corona failed its own gate and was reverted

**Problem discovered.** The hybrid raymarched corona shipped in Sprint 3.6 costs ~33 ms
per frame — three times the entire rest of the scene.

**Evidence.** Clean A/B at an identical 1843x1548 buffer, same session:

| Configuration | Median frame | FPS |
|---|---|---|
| With raymarched corona | 50.0 ms | **20.0** |
| Without raymarched corona | 16.7 ms | **59.9** |

**Root cause — and a research finding I mis-transferred.** Sprint 3.6 justified the
raymarch by citing a published comparison showing raymarching is "more than twice as
fast as shell texturing". That comparison is about *shell texturing* — dozens of thin
offset layers used for fur and grass, which is blend-bound. Our case is 2-4 large
transparent spheres, which is nothing like it.

Meanwhile the march evaluates two fbm calls per step at 3 and 2 octaves: 5 gradient-noise
evaluations x 16 steps = **80 noise evaluations per pixel**, over a large screen area.
That is vastly more ALU than four shell draws. The published finding was real; my
transfer of it to this problem was not.

**Decision.** Reverted. The Sprint 3.6 brief made change 4 explicitly conditional — "only
if FPS remains at or above the Sprint 3.5 baseline" — so the gate did exactly what it was
written to do. The four-shell corona is restored.

**What survived.** The other four Sprint 3.6 changes are unaffected and measured green:
scale separation, measured limb darkening, domain warping, and prominence ordering. The
attribution test above ran with the new photosphere and hit 59.9 FPS, so the photosphere
work carries no meaningful cost.

**Lesson.** A benchmark result transfers only with its workload. "Raymarching beats
shells" was true for the geometry it was measured on and false for mine, and the only way
that surfaces is a measurement on the actual scene. Pre-committing the condition is what
made this cheap to discover and cheap to undo.

---

## 2026-07-23 · Sprint 3.8 · "Feels laggy" was one full-resolution bloom pass

**Problem discovered.** The hero was pinned at exactly 30 FPS.

**Evidence.** Frame time median 33.3 ms, p95 33.9, max 34.1 — a 0.8 ms spread at exactly
2x vsync. Zero long tasks, 27 draw calls, stable 26 MB heap.

**Root cause.** The vsync cliff. The frame took marginally over 16.67 ms, missed its
window, and displayed on the next one — 17 ms of work costing 33 ms of latency. Bisection
at a fixed 2.85 Mpx buffer showed the bloom pass alone accounted for ~16.6 ms, running its
mipmap chain at full buffer resolution.

**Decision.** `resolutionScale={0.5}` on the bloom, plus one fewer corona shell. Median
33.3 -> 16.7 ms; **30 -> 60 FPS**; bundle unchanged.

**What the profile ruled out immediately.** Zero long tasks eliminated React re-renders,
hydration, event handlers, observer callbacks, layout thrashing, and GC in a single
measurement — every one of which would otherwise have been a plausible suspect worth
hours. Measuring first is what made this a short sprint.

**Lesson.** A frame-time distribution that is *too tight* is diagnostic. Real variable
load is noisy; a 0.8 ms spread locked at a multiple of the refresh interval means the
renderer is falling off a cliff, not grinding. The fix is almost always to get under the
threshold, not to optimise broadly — and being 1 ms over costs the same as being 15 ms
over.

---

## 2026-07-23 · M1 · The Crossing prototype — three registers proven, motion unmeasurable

**Built.** An isolated R3F prototype of the Crossing (`prototype/crossing/`), driven by a
single scrubbable t. Not integrated; the frozen renderer untouched.

**What validated.** The three registers are visually distinct without explanatory text —
the primary M1 criterion. Artistic (granulated star + soft corona), Schematic (wireframe +
sensor grid + `SCHEMATIC · NOT TO SCALE`), Measured (the real value 112.98 from 2024-05-14,
enormous and monospace). The timeline is a pure function, proven in Node to keep certainty
monotonic and to sequence the watermark artistic → schematic → measured with no reversal.
Bundle 320 KB gz, in line with the frozen island.

**What did not.** Motion quality — whether the crossing *feels* inevitable — could not be
observed, because the verification browser pane throttles requestAnimationFrame to zero
frames when backgrounded. Frame timing likewise unmeasurable. This is the one thing M1 most
needed to test, and the environment cannot deliver it.

**Three defects found and fixed.** `flat` is a reserved GLSL keyword and silently broke
shader compilation; the corona was a hard polygon (replaced with a fresnel shell); the
watermark flipped to MEASURED too late (re-gated to collapse completion).

**Lesson — and it recurs.** A frame-driven animation cannot be validated in a pane that
starves the frame loop. Stills validate composition and register distinctness; they cannot
validate *motion*. The honest report says so rather than inventing a frame number, and hands
the felt-experience judgement to a real browser. This is the third time the rAF-throttle has
shaped a sprint (Sprint 3.6, 3.8, now M1); the standing mitigation — hide the poster, pump
via resize, override document.hidden — recovers stills but never motion.

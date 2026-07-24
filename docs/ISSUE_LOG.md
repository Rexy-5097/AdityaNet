# Issue Log

Every issue found during development, open or closed. Resolved entries stay, with
resolution notes — a log that only shows open problems hides how the system got here.

**Categories:** Architecture · Performance · Graphics · Accessibility · Security ·
Developer Experience · Scientific Integrity · Testing · Infrastructure

| Status | Count |
|---|---|
| Open | 10 |
| Resolved | 15 |

---

## Resolved (recent)

### ISSUE-027 · Developer Experience · **High** · Resolved (M1 cinematic build)

**Symptom:** the M1 Crossing prototype (`prototype/crossing`) rendered a blank page;
console showed a cascade of `Invalid hook call` errors, which read as a duplicate-React
bug. Hours were lost chasing `@react-three/drei`, `vite.config` dedupe, and clean
reinstalls on that theory.

**Actual root causes (two, independent):**
1. **The real crash was a plain `ReferenceError`.** An earlier edit added the payload
   caption JSX and wired `onActive={setActivePayload}` / read `activePayload`, but never
   declared `const [activePayload, setActivePayload] = useState(-1)`. The undefined
   reference threw inside `<Crossing>` on every render → blank root. `npm ls` confirmed a
   single deduped React 19.2.8, so the duplicate-React theory was wrong.
2. **The `Invalid hook call` noise was an HMR artifact.** `main.jsx` had no HMR guard, so
   Vite hot-reloads called `createRoot()` twice on the same `#root` ("container already
   passed to createRoot"), and the two competing roots emitted misleading hook errors.

**Fix:** declared the missing `useState`; added a `container._reactRoot ??= createRoot(...)`
guard so HMR reuses one root. Also hardened two latent bugs found in review: `Spacecraft`
now reports the active payload only on change (was `setState` every frame), and
`Photon.jsx` reads `s.craftFade` instead of the removed `s.wireframe` field (was NaN opacity).

**Lesson:** a `ReferenceError` thrown during render and an HMR double-root both surface as
`Invalid hook call`. Read the *first* error and confirm the React-dedupe theory with
`npm ls react` before acting on it — don't let a familiar-looking message steer the fix.

---

## Open

### ISSUE-026 · Scientific Integrity · **Owner-approved exception, tracked**
**Real SDO/NASA solar imagery in the hero.** The owner chose real solar imagery over the
procedural star, accepting the honesty tradeoff. Bounded by a hard rule: the image is
always watermarked `ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA`. Formal record:
`docs/web/P8-EXCEPTION-01-real-solar-imagery.md`.
*Standing risk:* any implementation that drops the attribution watermark is a regression
and must fail review. Disclose first to any scientific reviewer.
*Owner:* accepted 2026-07-23.


### ISSUE-007 · Scientific Integrity · **High**
**Frozen ML artifacts are not valid JSON.**
`artifacts/v2/ml/benchmark_results.json` contains bare `NaN` from Python's
`json.dump` default (`allow_nan=True`). `JSON.parse` rejects the whole document, as
would any RFC-8259 consumer — including the OpenAPI-described API we intend to publish.

*Impact:* any non-Python reader fails on load. Currently mitigated by a narrow,
documented tolerance in `check.ts` (`parseScientificJson`).
*Fix:* regenerate with `allow_nan=False`, emitting `null`.
*Owner:* next ML artifact regeneration. Blocked on not wanting to disturb a frozen
artifact mid-sprint.

### ISSUE-008 · Scientific Integrity · Medium
**Prose in `docs/` has not been audited against artifacts.**
Two errors already found (HEL1OS file counts conflated at "389/391"; nowcast test
events stated as 155 versus an actual 82). Others are likely.
*Fix:* audit every figure in `docs/` against a JSON pointer.
*Owner:* Sprint 6.

### ISSUE-009 · Testing · Low
**`no-measurement-literals` is a source scan, not an AST rule.**
The specification calls for a custom ESLint rule. Implemented as a text scan in
`check.ts` because Astro template text nodes are awkward to reach through
`astro-eslint-parser`.
*Impact:* less precise; already produced one false positive (`SHA-256`), fixed by
stripping standards identifiers. No editor integration.
*Fix:* revisit if false positives become frequent enough to matter.

### ISSUE-010 · Infrastructure · **Blocking**
**No deployment.** Cloudflare Pages requires the owner's account. Blocks the
"deployed URL live over HTTPS" acceptance criterion and all Lighthouse verification.
*Blocked since:* Sprint 0. Now three sprints.
*Owner:* project owner.

### ISSUE-011 · Testing · Medium
**Lighthouse, axe, and visual regression not running.** Accessibility is currently
verified by contrast maths and manual reasoning, not by tooling.
*Depends on:* ISSUE-010.
*Owner:* Sprint 11, or earlier once deployment exists.

### ISSUE-012 · Developer Experience · Low
**`formatValue` is duplicated** between `src/lib/format/quantity.ts` and
`scripts/check.ts`.
*Rationale:* deliberate. A verifier that imports the code it audits verifies nothing —
both would share a bug and agree. Duplication is the point.
*Risk:* the two could drift, and the gate would then be checking the wrong format.
*Fix:* a shared golden-case fixture both must satisfy. Not deduplication.
*Owner:* Sprint 5.

### ISSUE-013 · Architecture · Low
**`openapi.yaml` not yet authored.** `derive.py` emits an envelope that nothing
validates.
*Rationale:* deferred deliberately. Two generated JSON files and no HTTP surface do not
justify a specification; writing one now would be an aspirational document.
*Owner:* Sprint 4, when `/validation` emits real endpoints.

### ISSUE-014 · Testing · Medium
**Marginal build-time-per-page is still unmeasured.** Six routes build in ~1 s, but
fixed overhead dominates at this scale, so the per-page cost cannot be extrapolated.
*Why it matters:* Sprint 8 generates roughly 500 date pages. If build time exceeds
10 minutes, the specification's R5 fallback triggers.
*Owner:* Sprint 8.

---

### ISSUE-021 · Graphics · Low
**No bloom / post-processing yet.** The star holds emission near 1.0 to avoid ACES
roll-off desaturation. Genuine over-range glow needs a bloom pass.
*Owner:* Sprint 6.

### ISSUE-022 · Accessibility · Medium
**The star has no keyboard equivalent.** It is `role="img"` and outside the tab order, so
no user is trapped, but ORBIT is pointer-only.
*Fix:* arrow-key orbit when the five-verb model lands.
*Owner:* Sprint 6.

### ISSUE-023 · Testing · **High**
**Experience-layer screenshots can silently photograph the poster instead of the canvas.**
`document.hidden` is true in the automated browser pane, so the Sprint 3 GPU-pause
correctly sets `frameloop="never"` and the static poster shows through unchanged.
*Impact:* invalidated several verification cycles in Sprint 3.5/3.6.
*Workaround:* override `document.hidden`, re-trigger the observer, and confirm by hiding
the poster before trusting any screenshot.
*Fix:* a `?forcerender=1` debug flag that bypasses the pause.
*Owner:* next experience-layer sprint.

### ISSUE-024 · Performance · Medium
**Composite FPS after the Sprint 3.7 revert is confirmed only by attribution, not
end-to-end.** The browser pane throttles rAF to 33.3 ms (exactly 2x vsync) when
backgrounded, so the final composite could not be sampled cleanly.
*Confidence:* high — the post-revert configuration is Sprint 3.5's corona (measured
59.9 FPS) plus the Sprint 3.6 photosphere (measured 59.9 FPS in the attribution test).
*Fix:* one confirmation in a foreground browser.

### ISSUE-024-ORIG · Performance · Resolved by revert
**Sprint 3.6 FPS is unverified.** rAF is throttled in a hidden document regardless of the
`document.hidden` override, so the frame-timing harness cannot complete in this pane.
*Last valid measurement:* Sprint 3.5, 59.9 FPS / p95 17.2 ms at 1544x1013.
*Blocks:* the third renderer-freeze acceptance condition.
*Owner:* re-measure in a foreground browser.

---

## Resolved

### ISSUE-025 · Performance · **High** · Resolved Sprint 3.7
**Raymarched corona cost ~33 ms/frame**, dropping the hero from 59.9 to 20.0 FPS.
*Resolution:* reverted per its pre-committed condition; four-shell corona restored.
A published "raymarching beats shell texturing" result was mis-transferred from a
fur/grass workload to large transparent spheres.

### ISSUE-023 · Testing · **High** · Resolved Sprint 3.7
**Screenshots silently photographed the poster instead of the canvas.**
*Resolution:* `?forcerender=1` debug flag bypasses the GPU pause, so verification no
longer depends on runtime hacking.

### ISSUE-001 · Performance · **Critical** · Resolved Sprint 0
**Next.js App Router shipped 184.2 KB gz for a page with zero interactivity.**
Every route budget in the specification sat below the framework floor.
*Resolution:* migrated to Astro. `/` measured at **0.0 KB gz**. → ADR-0002,
Engineering Journal 2026-07-23.

### ISSUE-002 · Security · Medium · Resolved Sprint 0
**CSP required `script-src 'unsafe-inline'`.** Next streams the RSC payload through
inline `<script>` tags, and static export cannot mint a per-request nonce.
*Resolution:* dissolved by ISSUE-001. Astro emits no inline scripts, so the policy is
now `script-src 'self'` with no exception. `check.ts` fails the build if an inline
script reappears, protecting the policy from silent regression.

### ISSUE-003 · Security · Medium · Resolved Sprint 0
**61 AppleDouble files would have been deployed to a public CDN.**
Created during the build itself on a non-HFS+ volume. Carry resource forks and
extended attributes including originating path.
*Resolution:* `scripts/postbuild.ts` strips them; `check.ts` asserts absence.
Verified: 61 → 0.

### ISSUE-004 · Performance · Low · Resolved Sprint 0
**28 font files emitted** — Cyrillic, Greek, Vietnamese — for an English-language
platform. Fontsource's unsuffixed entrypoints pull every published subset.
*Resolution:* Latin-only imports. 28 → 5 files.

### ISSUE-005 · Scientific Integrity · Medium · Resolved Sprint 0
**Eight of nine contrast ratios in specification §5.2.2 disagreed with measurement**;
`--color-open` was overstated at 8.4:1 versus 7.76:1 actual.
*Resolution:* specification amended to measured values with a dated correction note.
`check.ts` now enforces them on every build.

### ISSUE-006 · Developer Experience · Low · Resolved Sprint 1
**`as const satisfies` made optional fields unreachable** through the measurement key
union — `astro check` reported 2 errors on `measurement.n`.
*Resolution:* emit `Readonly<Record<MeasurementKey, Measurement>>`. The guarantee lives
in the key union; literal value types bought nothing.

### ISSUE-015 · Testing · Low · Resolved Sprint 2
**`no-measurement-literals` false-positived on `SHA-256`** on its first run.
*Resolution:* strip standards identifiers before scanning. Rejected the alternative of
raising the digit threshold to four, which would have silenced the warning while
letting every genuine three-digit measurement through.

### ISSUE-016 · Accessibility · **Critical** · Resolved Sprint 3
**Colour token `base` collided with Tailwind's `text-base` font-size utility**, painting
all body copy in the background colour. Invisible to every automated check.
*Resolution:* renamed `base` -> `canvas`; added a token-collision gate with a passing
negative test.

### ISSUE-017 · Performance · **High** · Resolved Sprint 3
**Budget gate under-reported the experience island by ~150x** (2.0 KB reported against
~292 KB actual) because it counted only `<script src>` tags.
*Resolution:* measure the transitive import closure plus inline script bodies.
`/` now reports 291.9 KB gz against its 450 KB budget.

### ISSUE-018 · Security · **High** · Resolved Sprint 3
**Astro island bootstrap requires inline scripts**, which `script-src 'self'` blocks.
*Resolution:* build-time SHA-256 hashes injected into the deployed header. Strict policy
preserved; `'unsafe-inline'` never reintroduced.

### ISSUE-019 · Graphics · **High** · Resolved Sprint 3
**ORBIT listeners never bound.** The container mounts after tier detection, but the hook's
effect keyed on a stable ref object and never re-ran.
*Resolution:* callback ref. Verified live: `grab` -> `grabbing` -> `grab`.

### ISSUE-020 · Infrastructure · Medium · Resolved Sprint 3
**AppleDouble sidecars crashed Arrow during derivation** — `._*.parquet` glob-matches
`*.parquet`. Third manifestation of the same root cause.
*Resolution:* filtered at the glob, with the pattern named in a comment.

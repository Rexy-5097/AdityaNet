# EN-001 — Build-time evidence traceability

*Engineering Note · Sprint 1–2 · Status: implemented, 6 measurements under enforcement*

A technique for making it **structurally impossible** for a website to display a number
that does not exist in a committed artifact. Not a convention, not a review checklist —
a property the build verifies and fails on.

---

## The problem

Any site that publishes measurements has a silent failure mode: a number gets typed in,
or copied from an older draft, or survives a change to the underlying analysis. Nothing
crashes. Tests pass. The page renders. It is simply wrong, and it stays wrong until a
reader who happens to know the real value notices.

For a scientific platform this is the failure that matters most, because the entire
value proposition is that the numbers are checkable.

The obvious mitigations are weak. Code review does not catch a plausible-looking
decimal. A unit test asserting `expect(render()).toContain("0.9539")` just moves the
hand-typed literal into the test file. Importing values from JSON is better, but the
JSON can drift from the artifact that produced it, and nothing notices.

## The shape of the solution

Four steps, each of which fails loudly:

```
committed artifact ──(1)──> measurements.json ──(2)──> generated TypeScript
                                                              │
                                                             (3)
                                                              ▼
                                                        rendered HTML
                                                              │
      artifact re-read from disk ◄────────(4)─────────────────┘
```

**1. Derivation resolves pointers, not values.** A Python script names each quantity by
artifact path plus an RFC-6901 JSON pointer. If a pointer does not resolve, derivation
raises with the failing prefix — a stale reference cannot become a blank metric.

```python
raise KeyError(
    f"JSON pointer {pointer!r} failed at {'/'.join(walked)!r}. "
    f"The artifact shape changed, or the reference is stale."
)
```

**2. Code generation makes keys a type.** The registry is emitted as TypeScript with a
union of every valid key:

```ts
export type MeasurementKey =
  | "artifacts/v2/ml/benchmark_results.json#/M~1X NOWCAST/.../roc_auc"
  | ...;
```

An unknown or stale key is now a *compile* error rather than a runtime `undefined`.

**3. The component API refuses values.** This is the load-bearing design decision:

```ts
interface Props {
  metric: MeasurementKey;   // there is no `value` prop
}
```

A caller physically cannot pass a number. Not "should not" — cannot. The type system
has no way to express it.

**4. The gate re-reads the artifact.** After the build, a checker parses the emitted
HTML, extracts each rendered measurement, opens the **original scientific artifact**
from disk, resolves the recorded pointer, formats it, and compares strings.

Critically, it does not read `measurements.json` for values, and it does not read the
generated TypeScript. Both are outputs of the same generator that produced the page, so
agreeing with them would prove only self-consistency. Going back to the artifact closes
the loop from rendered pixels to committed science.

## Two details that are easy to get wrong

**RFC-6901 escaping order.** Pointer tokens escape `~` as `~0` and `/` as `~1`. When
escaping you must handle `~` *first*; when decoding you must handle `~1` first.
Reversing either order corrupts the token. This is not defensive trivia here — the
benchmark artifact's top-level keys are literally `M/X NOWCAST`, so the path executes
on every run:

```ts
const token = rawToken.replace(/~1/g, "/").replace(/~0/g, "~");
```

**Deliberate duplication.** The formatting function exists twice: once in the app, once
in the checker. That looks like a defect and is not. A verifier that imports the code it
audits verifies nothing — both sides would share a bug and agree with each other. The
mitigation for drift is a shared golden-case fixture, not deduplication.

## Proving the gate can fail

A gate that has never failed is indistinguishable from a gate that cannot. Three
negative tests, run deliberately and reverted:

| Injected fault | Result |
|---|---|
| Edit `0.9539` → `0.9999` in built HTML | `renders "0.9999" ... but the artifact says "0.9539"` |
| Typo a JSON pointer in the deriver | `KeyError: pointer '/identity/n_parquet_FILES_TYPO' failed` |
| Type `"581 M/X events"` into page prose | `measurement literal: ... has "581" in template text` |

The third covers what the first cannot: a number typed into prose never passes through
the component, so the consistency gate would never see it. That required a separate
source scan.

## What it caught

Within two sprints, on six measurements:

- **A frozen artifact was not valid JSON.** Python's `json.dump` emits bare `NaN`;
  `JSON.parse` rejects the document entirely. Invisible from Python, fatal to every
  other consumer — including the API we intend to publish.
- **The project's own prose was wrong.** Written descriptions said "389/391 HEL1OS
  orbits", conflating three tables with genuinely different file counts (424 / 389 /
  373), and stated 155 test events where the artifact says 82.

Both were found by machinery built to catch exactly this, in the documentation of the
project that built it.

## Cost

One Python script (~250 lines), one generator target (~60 lines), one checker function
(~90 lines), and one source scan (~40 lines). No runtime dependency, no service, no
database. The generated registry adds nothing to the client bundle — the routes it
serves measure **0.0 KB gz of JavaScript**.

## When this is worth it

When a wrong number is expensive and silent. Scientific publishing, financial
reporting, regulatory disclosure, benchmark results. If your numbers are decorative,
this is over-engineering. If a reader could reasonably act on them, the alternative is
trusting that nobody ever mistypes a decimal.

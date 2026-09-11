---
id: CONTRA-008
title: §2.5's non-decreasing event rule is falsified by every event HDU in the archive
status: active
state: OPEN
resolving_revision: null
supersedes: []
superseded_by: null
source: null
source_date: 2026-09-12
origin: authored
---

> **Authored, not migrated**, and **OPEN**: it records a falsification and a proposed amendment
> that has **not** been applied. The parser enforces §2.5 as written until the owner rules.
> Cite it by ID; do not restate it ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRA-008 — §2.5's non-decreasing event rule is falsified by every event HDU

**Status: OPEN 2026-09-12.** Raised by M3/E5 Issue #18, which implemented §2.5's row rules and
ran them against the whole corpus.

**The rule (§2.5, unamended since r0):** *"Validation: … `mjd` non-decreasing …"*

**`OBSERVED`, archive-wide (391 orbits, 1,564 detector HDUs, 1,352,158,522 rows):**

| Measurement | Result |
|---|---|
| HDUs containing at least one backward step | **1,564 of 1,564 (100%)** |
| Orbits affected | **391 of 391** |
| Backward steps, total | **37,912,843** |
| Backward steps per HDU | min 4 · median 23,216 · max 229,417 |
| Largest backward step | min 0.2 ms · median 6.13 s · **max 1,156.36 s** |
| Consecutive rows sharing a timestamp | 1,265,162,302 of 1,352,156,958 steps (93.6%) |

**Enforced as written, no real event stream completes.** The reader terminates at F-16 on the
first decrease of every HDU in the archive, having yielded only rows that satisfied every other
§2.5 rule. That is the behaviour #18 ships, because weakening a frozen rule in code is the one
thing the contract forbids: *"a deviation requires a logged amendment, not a code change."*

## Why this was not seen before

The Milestone V parser implemented the same check, but only under `load_columns=True`, and the
Milestone VII build never set it: `evt.fits` is 85.7 GB and events are deliberately outside the
canonical tables, so the rows were never read. **The rule had never been executed against the
archive.** This is the same pattern as CONTRADICTION-001, -003, -004 A and -005 A — a property
asserted from a single reading and never checked against the population — with one difference:
here the property was never checked at all.

## What the measurement says about the data

The three facts that bear on the ruling, and nothing beyond them:

1. **The rows are not a sorted index.** 93.6% of consecutive rows share a timestamp, and the
   backward steps are frequent (median 23,216 per HDU) rather than isolated.
2. **The backward steps are large.** A median largest-step of 6.13 s and a maximum of 1,156 s are
   not sub-second packet jitter; they are far beyond the scale §2.8 r4 recorded for housekeeping
   telemetry (max 892.4 ms on the reference orbit).
3. **Every other §2.5 rule holds on every row**: all four detector HDUs present, `DETNAM` correct,
   `ener > 0` on all 1.35 billion rows, `mjd` inside the header span to within one float64 step
   (CONTRA-007 Defect C), and `utc-isot` agreeing with `mjd` to within half the millisecond it
   carries.

**No mechanism is asserted here.** Whether event rows are written per detector packet, per
telemetry frame, or in some other archive order is not established by this measurement, and this
record does not guess.

## Proposed amendment (NOT applied — the owner's ruling is required)

The shape that already exists in the contract for exactly this situation is §2.8 r4, where the
owner removed HK's non-decreasing requirement, **declined** a proposal to sort inside the parser,
and required the parser to remain a lossless reader while recording inversion statistics.

1. **§2.5** — remove `mjd` non-decreasing for event lists. Replace it with: `mjd` finite; `mjd`
   within the header span (already r7); **inversion statistics recorded, never thresholded**, as
   §2.8 requires for housekeeping.
2. **The parser MUST NOT sort.** §2.8 r4's general v2 principle holds: reading and transforming
   are separate acts, and a consumer needing chronological order invokes the documented
   out-of-parser utility.
3. **§8** — a new assumption scoping what the inversion statistics do and do not establish,
   matching A-12's treatment of housekeeping jitter.
4. **No statistic enters the contract.** The measurements stay in this record.

**My recommendation is amendment**, on the reasoning that the alternative disposition — treating
this as an archive defect, as CONTRADICTION-005 Defect C treated 12 SoLEXS days — would discard
the event streams of **all 391 orbits**, which is not an archive defect but a convention the
contract never established. §2.5 already calls `mjd` the canonical representation of three
redundant ones and offers `utc-isot` as its cross-check; ordering was assumed, not measured.

**But this is the owner's call, not mine,** and for the same reason CONTRADICTION-006 Defect B
was: it turns on whether a backward step in an event list is telemetry or corruption. The r4
housekeeping ruling answers that question one way for a different product, and a 1,156 s step is
large enough that the answer should not be inherited without a decision.

## Until it is ruled

- §2.5 stands as written; the parser enforces it and fails closed (F-16).
- The event reader is exposed and every other row rule is exercised on real data.
- `tests/integration/test_hel1os_parse_with_platform.py` pins the falsification: it asserts that a
  real stream yields valid rows and then terminates at F-16, so the day the rule changes, the test
  changes with it.
- No canonical table is affected: §2.5 keeps events out of T1–T7, and the write path (M3/E5/#19)
  does not read them.

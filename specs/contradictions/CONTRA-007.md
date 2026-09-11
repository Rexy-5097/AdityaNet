---
id: CONTRA-007
title: HEL1OS time comparisons are undecidable at float64 resolution
status: active
state: CLOSED
resolving_revision: r7
supersedes: []
superseded_by: null
source: null
source_date: 2026-09-12
origin: authored
---

> **Authored, not migrated.** CONTRA-001 … CONTRA-006 are carried verbatim from
> `artifacts/v2/phase05/`. This record has no such source: it was raised by the governed
> re-implementation of the HEL1OS parsers (M3/E5 Issue #18) and its archive-wide verification.
> Cite it by ID; do not restate it ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRA-007 — HEL1OS time comparisons are undecidable at float64 resolution

**Status: CLOSED 2026-09-12 — resolved by [SPEC-parsers](../parsers/SPEC-parsers.md) r7 §5.1.**

**Defects A, B and C are one defect in three places:** the contract compares times derived from
MJD values without saying at what precision, and the values it compares are IEEE-754 float64.
Implemented exactly as written, three checks reject valid archive products by margins of one or
two representable steps. r7 adds `ε_t = 1 ms` (§5.1) and defines the comparisons; it changes no
physical rule and no statistic enters the contract.

**Observations D, E and F are not falsifications** and carry no amendment. They are recorded
because #18's implementation had to resolve each of them, and an unrecorded resolution is an
invented convention.

## How the defect reached a governed implementation

**CONTRADICTION-006 Defect A ruled on the same numerical problem for §2.8 and fixed it in code
only** — *"The specification text is unchanged — the epsilon exists solely to prevent IEEE754
boundary artifacts"* — and the Milestone V parsers applied the same `_FLOAT_EPS_S = 1e-3` to
§2.7 R-1 without the contract ever recording it. #18 was written from the contract text, as the
contract requires, and therefore reproduced the rejections that ruling had already resolved.

**An implementation-only fix to a contract defect does not survive a re-implementation.** That
is the reason r7 moves the value into the text rather than repeating the code fix, and it is the
one generalisation this record makes.

## DEFECT A — §2.7 R-1 H3 rejects 647 of 1,564 spectra products

**The rule (r4):** accept H3 iff `col[0] == 0` exactly **and** `abs(col_span − header_span) ≤ one
EXPOSURE bin`. `col_span` is not defined anywhere in the contract.

**`OBSERVED`, archive-wide (391 orbits, 1,564 spectra products):**

| | Products |
|---|---|
| Resolve to H3 | 917 |
| Terminate at F-06 | **647** |
| Terminate for any other reason | 0 |

Every one of the 647 is H3 in shape: `col TSTART[0] == 0.0` exactly, a uniform 20 s `EXPOSURE`,
and a span that agrees with the header to **between 6.4×10⁻⁷ s and 1.36×10⁻⁶ s past the one-bin
bound** — at most about **two representable float64 steps** of an MJD value at this epoch
(≈ 6.3×10⁻⁷ s each). The specification's own reference orbit is one of the products that fails:
`(61017.49963590554 − 61017.0000988685) × 86400` evaluates to `43160.00000007916`, 79 ns over an
exact bound, while §2.7 records that orbit as resolving to H3.

**Two readings of `col_span` were available**, and they disagree on that reference orbit:
`TSTART[last] − TSTART[0]` is two bins short of the header span, `TSTOP[last] − TSTART[0]` is one.
Only the second reproduces the contract's own recorded verdict, and it is the one the Milestone V
parser used.

### Amendment (APPLIED as r7)
1. **§2.7** — define `col_span = column TSTOP[last] − column TSTART[0]` and `header_span`, and
   state the H3 bound as `≤ one EXPOSURE bin + ε_t`.
2. **§5.1** — define `ε_t`, its scope and what it is not.

## DEFECT B — §2.8 header-span consistency rejects 94 of 391 housekeeping products

**The rule (r4):** *"the global `mjd` range lies within the header `TSTART`/`TSTOP`"* — no
precision, no rule id.

**`OBSERVED`, archive-wide:** 94 of 391 products terminate. **Every violation is exactly one
representable float64 step** (6.286×10⁻⁷ s): a boundary timestamp equals its header bound to
physical precision and differs from it by one step. None exceeds 1 µs; none is within four orders
of magnitude of a physically meaningful excursion, which would be seconds.

This is the identical measurement CONTRADICTION-006 Defect A recorded (60 orbits above `TSTOP`,
40 below `TSTART`, all ~6×10⁻⁷ s). The count differs because that ruling measured the legacy
build's orbit set; the property is the same.

### Amendment (APPLIED as r7)
**§2.8** — state header-span consistency as `TSTART − ε_t ≤ min(mjd)` and `max(mjd) ≤ TSTOP + ε_t`,
and assign it **F-06**, the id the Milestone V parser already raised.

## DEFECT C — §2.5's span check has the same defect, and V-EVT-2 has no rule at all

**The rules (r0):** *"`mjd` within `[TSTART,TSTOP]`"*, and *"`utc-isot` is a cross-check
(V-EVT-2)"* — named, with no comparison and no tolerance.

**`OBSERVED`, archive-wide (1,564 detector HDUs, 1,352,158,522 event rows):**

| Measurement | Result |
|---|---|
| HDUs whose `min(mjd)` falls below header `TSTART` | 182 — **all exactly one float64 step** (6.29×10⁻⁷ s) |
| HDUs whose `max(mjd)` rises above header `TSTOP` | 270 — **all exactly one float64 step** |
| HDUs exceeding either bound by ≥ 1 ms | **0** |
| `utc-isot` strings that fail to parse | **0** |
| `instant(mjd) − instant(utc-isot)` | **within ±0.5000 ms, every row** |
| Rows with `ener ≤ 0` | **0** |

`utc-isot` is the `mjd` instant **rounded to the millisecond it carries**: the agreement is
exactly half the string's own resolution, in both directions, across every row of the corpus.
That is a measurement of the product, so the rule follows the value rather than a chosen number.

### Amendment (APPLIED as r7)
**§2.5** — the span check gains `ε_t` and **F-06**; V-EVT-2 becomes
`|instant(mjd) − instant(utc-isot)| ≤ ½·r_isot + ε_t`, where `r_isot` is the resolution the string
itself carries, with **F-06** for a violation or an unparseable string.

## OBSERVATION D — the five bands of one detector need not share a time axis

§2.6 records `NAXIS2 ≈ 43171` and does not say whether a detector's five band HDUs are sampled
together. **They frequently are not:** of 1,564 light-curve products, **794 carry bands of unequal
length** — every CdTe product (782 of 782) and 12 CZT products. On the reference orbit CdTe1's
bands hold 43,154 / 43,171 / 43,163 / 43,133 / 43,171 samples.

A consumer assuming one axis per detector would misalign up to 38 samples. **No amendment:** §2.6
neither states nor denies a shared axis, and the parser keeps each band's own `MJD` column, which
is the only reading the measurement supports. Recorded so the property is pinned by a test rather
than rediscovered.

## OBSERVATION E — §2.8's detector-health names are abbreviations

§2.8 lists `czt{1,2}hotpix`, `hotpixcnt`, `hotpixthr`, `hotpixlgcstat`, `bunpxctr`. **The archive
carries no unprefixed column of those names.** All 391 orbits carry an identical 62-column
`HLSHK` table in which they appear as `czt1hotpixcnt`, `czt2hotpixthr`, `czt1bunpxctr` and so on —
which is also how §3 T4 names them (`czt1hotpixcnt`, `czt2hotpixcnt`).

**No amendment:** the prefixed spelling is what both the archive and §3 carry, so §2.8's
abbreviation resolves without ambiguity. The reading is recorded rather than left implicit.
`czt1enth` declares `keV` and `czt2enth` declares no unit in **391 of 391** orbits, exactly as
§2.8 and §8 A-4 describe.

## OBSERVATION F — three different counts of overlapping orbit pairs

§4 records **46** time-overlapping orbit pairs; the Milestone VI version-resolution engine
recorded **49**; #18's `overlaps` predicate, applied to the stem-declared interval
(`start`, `start + dur`) of all 391 orbits, reports **50**.

§4 defines no overlap measure, and the three numbers are consistent with three different ones.
**No amendment, and nothing is reconciled here:** #18 detects overlap and resolves precedence;
the authority on coverage is the minute-level map §4 assigns to the write path (M3/E5/#19), which
will produce the only count that governs ingestion.

## OBSERVATION G — housekeeping inversions are far larger archive-wide than on the reference orbit

§2.8 records the reference orbit's telemetry jitter — 424 of 9,513 steps decreasing, **max backward
step 892.4 ms** — and A-12 obliges Milestone VIII to report the distribution across all 391 orbits.
Parsing every product for #18 produced that measurement as a by-product:

| `max_backward_step_s` across the 389 housekeeping products that parse | Value |
|---|---|
| median | **0.0 s** (most orbits have no inversion at all) |
| maximum | **1,153.4 s** |

**No amendment, and no threshold.** §2.8 is explicit that the magnitude is reported and never
compared against an invented tolerance, so the parser records `n_out_of_order` and
`max_backward_step_s` and compares them to nothing. The figure is recorded here because it is
evidence for A-12, and because "sub-second packet-arrival jitter" — the reading the reference
orbit supports — does not describe a 1,153 s step. Whether that is jitter, a telemetry gap, or
something else is a Milestone VIII scientific question, and this record asserts no mechanism.

## What is NOT affected

Nothing physical. `ε_t` never touches a physical time difference: §2.8's inversion statistics
remain unthresholded, §2.6's `MJD` stays strictly increasing, GTI durations are unchanged, and
F-09's exact SoLEXS identity is untouched. The 20 fail-loud rule ids are unchanged. SoLEXS
parsing is unchanged in behaviour.

**Duplicate HK timestamps remain F-16.** Two orbits (`HLS_20260201_120005_43198sec_lev1_V111`,
`HLS_20260202_000005_43183sec_lev1_V111`) terminate on duplicate `mjd`, exactly as
CONTRADICTION-006 Defect B was ruled, and exactly the two the V&V plan lists as known archive
defects. No amendment; they are archive-quality findings.

**The §2.5 non-decreasing rule is NOT amended here.** Its archive-wide falsification is a separate
question with a separate answer, recorded OPEN in [CONTRA-008](CONTRA-008.md).

## Measurements, and where they live

Every number above is a measurement of the archive, recorded here and **not** in the contract —
the discipline CONTRADICTION-005 Defect B established: *measurements belong in the profile and the
contradiction record; invariants belong in the contract.* r7 encodes one value, `ε_t`, and states
its derivation without importing a statistic.

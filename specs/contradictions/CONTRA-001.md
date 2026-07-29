---
id: CONTRA-001
title: Frozen contract rule F-09 rejects valid archive data
status: active
state: CLOSED
resolving_revision: r1
supersedes: []
superseded_by: null
source: artifacts/v2/phase05/CONTRADICTION-001.md
source_date: 2026-07-17
---

> Carried verbatim from `artifacts/v2/phase05/CONTRADICTION-001.md`. The ruling below is the text the owner
> wrote; it is never summarised ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRADICTION-001 — Frozen contract rule F-09 rejects valid archive data

**Status: CLOSED 2026-07-17 — owner approved the §6 amendment; applied as PARSER_SPECIFICATION.md r1 (§10 Revision History). Milestone II now passes 32/32 with the xfail marker removed. See COMPLIANCE_M2.md.**

Raised under the Phase 0.5.2 implementation rule: *"If the implementation contradicts the specification, STOP, document the contradiction, explain why, and wait for approval"* and *"No design changes are permitted unless implementation proves the contract impossible to satisfy."*

---

## 1. The contradiction

**Frozen contract** (`PARSER_SPECIFICATION.md` @ `6de0eb2`, §2.3 and §5 F-09):

> `Σ(STOP−START)` ≈ `EXPOSURE` (±1 s) → else F-09

**Result on the mandated D1 validation file** `AL1_SOLEXS_20240514_SDD2_L1.gti.gz`:

| Quantity | Value |
|---|---|
| `Σ(STOP−START)` (the frozen formula) | **86390.0 s** |
| Declared `EXPOSURE` | **86395.0 s** |
| Discrepancy | **−5.0 s** vs a ±1.0 s tolerance → **F-09 terminates** |

The parser correctly refuses to parse the reference file of the reference day. **Satisfying the contract literally makes the archive unparseable.** This meets the "impossible to satisfy" bar exactly.

## 2. Why — the data is right and the contract is wrong

The GTI endpoints are **inclusive** at 1-second granularity. Evidence, three independent lines:

**(a) Exact arithmetic match.** With 5 intervals:
| Hypothesis | Formula | Result | Error vs EXPOSURE |
|---|---|---|---|
| A — exclusive (frozen rule) | `Σ(STOP−START)` | 86390.0 | **−5.0 s** |
| B — inclusive | `Σ(STOP−START+1)` | **86395.0** | **0.0 s** |

The −5.0 s error equals the interval count exactly: one lost second per interval — the signature of an off-by-one endpoint convention, not of corrupt data.

**(b) Independent coverage cross-check.** Marking each second of 2024-05-14 as covered under the inclusive rule yields **86,395 of 86,400 s covered — equal to the declared EXPOSURE exactly.**

**(c) The excluded seconds are physically coherent.** Day-offsets `[0, 5, 30072, 30078, 83951]`: second 0 (the day's data begins 00:00:01, matching the primary header `TSTART='2024-05-14T00:00:01+00:00'`) plus four isolated 1-second dropouts. Under my frozen exclusive reading these would be four *2-second* gaps — which is precisely the error I made when drafting §6 (see §4).

**Conclusion:** `Σ(STOP−START+1) == EXPOSURE` holds with **zero** error. The archive is internally consistent. The frozen rule encodes an arithmetic convention I inferred without computing it.

## 3. Root cause of the specification defect

When drafting §2.3 I read the GTI rows and the `EXPOSURE='86395.0'` header, and asserted the standard OGIP exclusive convention **without summing the intervals**. Structure-only discovery captured the schema correctly but did not test the *arithmetic relationship between two fields* — a gap in the discovery method, not in the data.

This is a milder relative of the v1 failure: an unverified assumption promoted to a rule. The difference is that the fail-loud architecture caught it on the first real file rather than thirty sprints later — F-09 did its job, by rejecting the file rather than silently mis-computing live time.

## 4. The contract is also internally inconsistent (found while investigating)

- **§5 F-09** implies live time = 86390 s (exclusive).
- **§6 D1 acceptance** already states *"live time ≈ 86395 s"* (inclusive).

The two sections contradict each other, and the real data adjudicates for **§6**. Additionally §6's *"GTI gaps ≈ 4×2 s"* is wrong for the same reason: the truth is **5 excluded seconds** — 4 single-second dropouts plus second 0.

## 5. Downstream impact if left unamended

`Σ(STOP−START)` understates live time by **1 s per GTI interval**. This propagates into §3 `T1.live_time_s`, `gti_fraction`, and every `rate_total = counts_total/live_time_s`. On a minute containing several GTI boundaries the rate error is ~1–2%, biased **high** (live time too small). Small, systematic, and exactly the class of silent error this project exists to eliminate.

## 6. Proposed amendment (NOT applied — requires approval)

1. **§2.3** — declare the convention explicitly: *SoLEXS GTI `START`/`STOP` are **inclusive** second-marks at 1-s sampling; live time of an interval = `STOP − START + 1`.*
2. **§5 F-09** — restate as: *`Σ(STOP−START+1) != EXPOSURE` (exact equality; tolerance 0 s) → F-09.* Tightening from ±1 s to exact is justified because the relationship is now known to be definitional, not approximate. **A tolerance would re-admit the very ambiguity that produced this defect.**
3. **§3 T1/T2** — `live_time_s` computed under the inclusive rule.
4. **§6 D1** — replace *"GTI gaps ≈ 4×2 s"* with *"5 excluded seconds at day-offsets [0, 5, 30072, 30078, 83951]; live time exactly 86395 s"*.
5. **§8** — record new assumption **A-8**: *the inclusive convention is verified on 2024-05-14 SDD2 only.* Milestone VIII MUST verify exact equality across **all 436 SoLEXS days**; any day failing exact equality is a genuine archive finding and must be reported, not tolerated.

## 7. State of the work

Milestone II code is complete and passes **29/30** tests, including every fail-loud path (F-01, F-02, F-04, F-06, F-07, F-09, F-12, F-16, F-18, F-19) and the real SDD1 empty-GTI F-12 case. The single failing test is the real SDD2 D1 file, marked `xfail(strict=True)` referencing this document — **strict**, so that if the contract is amended and the test starts passing, the marker itself fails and forces its own removal. Nothing has been weakened: `EXPOSURE_TOL_S` remains 1.0 s and F-09 remains exactly as frozen.

**RESOLVED.** All 5 proposed changes were approved and applied verbatim. F-09 was *tightened* (±1 s → exact), never weakened. The obligation from §6.5 is carried forward: **Milestone VIII must verify `Σ(STOP−START+1) == EXPOSURE` across all 436 SoLEXS archives and TERMINATE on any deviation** (spec §8 A-8).

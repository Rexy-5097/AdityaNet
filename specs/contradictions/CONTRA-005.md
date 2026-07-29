---
id: CONTRA-005
title: the archive-wide build falsifies three frozen rules
status: active
state: CLOSED
resolving_revision: r5
supersedes: []
superseded_by: null
source: artifacts/v2/phase05/CONTRADICTION-005.md
source_date: 2026-07-17
---

> Carried verbatim from `artifacts/v2/phase05/CONTRADICTION-005.md`. The ruling below is the text the owner
> wrote; it is never summarised ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRADICTION-005 — the archive-wide build falsifies three frozen rules

**Status: CLOSED 2026-07-17 — the owner ruled the three defects independent and adjudicated them separately. Applied as PARSER_SPECIFICATION.md r5 (§10). Milestone VII rebuilt; 188/188 tests pass.**

**Defect A: APPROVED in full.** §2.7 now validates `DETCHANS` against a family allowlist (CZT 341, CdTe 511, both PHA); §3 T5 carries `detchans` explicitly and never merges CZT/CdTe arrays; F-11 restated over three incommensurable spaces. **A-13** added.

**Defect B: PARTIALLY APPROVED — the owner's ruling is narrower than my proposal, and better.** The equality is replaced by the **logical implication `NaN(COUNTS) ⇒ GTI-excluded`**: a NaN inside GTI-good time remains F-09; a GTI-excluded second is **permitted** to hold a finite count. My proposal to record the measured statistics in the contract was **DECLINED** — no archive statistics, no percentages, no median excess. **A-9 recorded as discharged at M-VII; A-14 created.**

*Why the owner was right:* the implication is the **strong half** of the bijection — it forbids the dangerous direction while asserting nothing the archive supports. Encoding the excess statistics would have written an unvalidated observation into the contract: the same refusal as CONTRADICTION-003. **Measurements belong in the profile and this record; invariants belong in the contract.**

**Defect C: no amendment.** F-19 unchanged. Recorded as an archive-quality finding for Milestone VIII.

The first archive-wide build ran to completion and **reported its own failure rather than hiding it**: SoLEXS 353/436 built, **HEL1OS 0/391 built**, 474 products skipped, every skip logged with its rule id. The build driver catches per-product terminations and records them as data (builders and parsers still fail loud); this is what surfaced all three defects at once.

| Rule | Skips | Defect |
|---|---|---|
| **F-07** | **391** | **A** — §2.7's `DETCHANS=341` is wrong for CdTe |
| **F-09** | **71** | **B** — the r2 NaN⟺GTI bijection does not hold archive-wide |
| **F-19** | **12** | **C** — GTI intervals with `STOP <= START` |

---

## DEFECT A — §2.7 asserts one HEL1OS channel space; the archive has two

**The rule (§2.7):** `DETCHANS=341`, enforced by the M-V parser and the T5 builder.

**`OBSERVED`:** HEL1OS has **two distinct PHA channel spaces**:

| Detector family | `DETCHANS` | `CHANTYPE` |
|---|---|---|
| **CZT** (CZT1, CZT2) | **341** | PHA |
| **CdTe** (CdTe1, CdTe2) | **511** | PHA |

Every one of the 391 orbits contains CdTe spectra, so **every orbit terminates** and **T3/T4/T5 are empty archive-wide**.

**Root cause — mine, and the fourth instance of one pattern.** I wrote §2.7 after inspecting exactly one file (`hel1os_czt_spectra_czt2.fits`) and generalised its `DETCHANS` to all HEL1OS spectra. CONTRADICTION-001 (GTI convention), -003 (LC/spectrum relation), -004 Defect A (R-1 hypotheses) and now -005 A share a single root: **asserting a property from a single reading without checking it across the population.** The A-8/A-9/A-11/A-12 scoping discipline exists precisely because of this pattern; §2.7's `DETCHANS` was never given a scoping assumption, and that omission is what let it through.

**Consequence for F-11.** The contract treats channel-space separation as binary (SoLEXS PI 340 vs HEL1OS PHA 341). There are **three** incommensurable spaces: **SoLEXS PI 340**, **HEL1OS CZT PHA 341**, **HEL1OS CdTe PHA 511**. F-11's intent is unchanged and strengthened; its arithmetic is incomplete.

### Proposed amendment (NOT applied)
1. **§2.7** — replace the scalar `DETCHANS=341` with a per-family allowlist: **CZT → 341, CdTe → 511**, both `CHANTYPE='PHA'`; an unlisted `(family, DETCHANS)` pair terminates via **F-07**, exactly as an unlisted band terminates via F-10.
2. **§3 T5** — `hel1os_spec_1min` must carry a `detchans` column and **must not** stack CZT and CdTe spectra into one array column; the channel space is a property of the detector family.
3. **§5 F-11** — restate over **three** spaces rather than two.
4. **§8** — new assumption **A-13**: the per-family channel counts are **VERIFIED on a sample of 8 orbits**; Milestone VIII must verify across all 391; any deviation terminates validation.

---

## DEFECT B — A-9 discharged early, and **VIOLATED**

**The rule (§2.1 r2, owner-approved):** *`NaN(COUNTS)` set MUST equal the GTI-excluded second set exactly; mismatch → F-09.* Scoped by **A-9** to the reference archive, with Milestone VIII obliged to verify all 436 and **terminate on any violation**.

**The T1 builder runs this check per day, so A-9's obligation was discharged at M-VII rather than M-VIII.** The archive-wide result:

| Relationship | Days |
|---|---|
| `NaN == GTI-excluded` — **the r2 bijection holds** | **344** |
| `NaN ⊂ GTI-excluded` — **strict subset; bijection FAILS** | **70** |
| `NaN ⊃ GTI-excluded` | **0** |
| Neither | **0** |
| **`NaN ⊆ GTI-excluded`** | **414 / 414 (100%)** |

(414 days checked; 22 unparseable — 12 by Defect C, 10 by F-01.)

**Excess GTI-excluded seconds carrying finite counts:** min 2, **median 758**, max 43,199, **total 266,919**.

**`OBSERVED`:** the bijection is **false archive-wide** (70/414 = 17% violate it). The relationship that *does* hold on every single day is the **one-directional** `NaN ⊆ GTI-excluded`: every NaN second is GTI-excluded, but a GTI-excluded second may carry a finite count.

**This is exactly the outcome A-9 was written to catch**, and the reference day was unrepresentative: 2024-05-14 happens to sit in the 83% where the sets coincide.

**Note the direction matters.** `NaN ⊆ GTI-excluded` is still a strong, useful invariant — it forbids the dangerous case (a NaN inside good time, i.e. missing data silently treated as observed). What it does not support is *equality*, which the r2 rule asserts.

**`HYPOTHESIS` (not for the contract):** GTI may exclude seconds for reasons beyond data absence — the excess is large (median 758 s/day, max 43,199 s ≈ half a day) and looks structured rather than incidental. **Establishing why is a scientific-validation question, not a parser one**, and belongs with CONTRADICTION-003 in Milestone VIII. **No mechanism is asserted here.**

### Proposed amendment (NOT applied)
1. **§2.1 r2 / §7** — replace the bijection with the measured, one-directional invariant: **`NaN(COUNTS) ⊆ GTI-excluded` (F-09 on any NaN inside good time)**. Do **not** replace it with a tolerance and do **not** encode the excess statistics.
2. **§8 A-9** — mark **DISCHARGED at M-VII** and **VIOLATED**: record 344 equal / 70 strict-subset / 0 violations of the subset direction. Replace with **A-14**: *the excess of GTI-excluded seconds over NaN seconds is unexplained; owner Milestone VIII (with CONTRADICTION-003).*
3. **§3 T1** — `live_time_s` continues to come from GTI and `n_seconds_present` from finite counts. **They are already carried independently and neither is derived from the other**, so no builder change follows from this defect.

---

## DEFECT C — 12 SoLEXS days have `STOP <= START` in GTI

**`OBSERVED`:** 12 of 436 archives terminate at F-19 (`GTI row N has STOP <= START`), e.g. `AL1_SLX_L1_20240422_v1.0` row 2. A further 10 terminate at F-01 (unreadable/gzip).

**No amendment proposed.** F-19 is behaving exactly as designed: a GTI interval that ends before it starts is not a convention question, it is an archive defect. These 22 days are **correctly excluded and individually logged**. Milestone VIII should report them as an archive-quality finding.

---

## What is NOT affected

SoLEXS **T1/T2 built cleanly for 353 archives**, and every invariant held on them: NaN⟺GTI (on those days), finite-only aggregation, `live_time_s` == `EXPOSURE`, 1440 rows/day, no duplicate minutes, complete provenance. **T6: 2,130 GTI intervals. T7: 1,556 provenance rows.** The Version Resolution Engine ran correctly (1,065,572 owned pairs, 48,604 conflicts resolved) — its output is simply unused because no HEL1OS product survived Defect A.

**186/186 unit tests pass**, including the D1 acceptance criterion: T1's `rate_total` peaks at **2024-05-14 16:49 UTC**, within the frozen ±2 min of the GOES X8.7 at 16:51 — **the project's first genuine Aditya-L1 observation.**

## State of the work

Milestone VII is **paused with the code committed and every rule terminating exactly as frozen**. Nothing weakened: `DETCHANS` is still 341, the bijection is still equality, F-19 still fires. The build's own statistics are the evidence.

**RESOLVED.** All three defects closed by r5. Defect C required no amendment.

**Milestone VIII is now the final validation milestone.** It shall discharge **A-8, A-11, A-12, A-13, A-14** and resolve **CONTRADICTION-003** through archive-wide scientific validation. A-9 is already discharged (here).

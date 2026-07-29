---
id: CONTRA-006
title: two §2.8 HK checks falsified by the archive-wide rebuild
status: active
state: CLOSED
resolving_revision: null
supersedes: []
superseded_by: null
source: artifacts/v2/phase05/CONTRADICTION-006.md
source_date: 2026-07-17
---

> Carried verbatim from `artifacts/v2/phase05/CONTRADICTION-006.md`. The ruling below is the text the owner
> wrote; it is never summarised ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRADICTION-006 — two §2.8 HK checks falsified by the archive-wide rebuild

**Status: CLOSED 2026-07-17.**

**Defect A: APPROVED as an implementation-only fix.** The observed failures are numerical representation artifacts (all ~6.3×10⁻⁷ s — the float64 ULP of MJD at ~61000), not physically out-of-span telemetry. The HK header-span check now applies the SAME documented `_FLOAT_EPS_S` (1 ms) already employed by §2.7 R-1. **The specification text is unchanged** — the epsilon exists solely to prevent IEEE754 boundary artifacts and is not a physical tolerance, documented as such at the check site. Verified: a previously-rejected ULP orbit parses; no spec edit was made.

**Defect B: NOT APPROVED — §2.8 unchanged, working as designed.** Duplicate HK timestamps remain archive-quality defects; F-16 continues to terminate; parser behaviour unmodified. The 2 affected orbits (`HLS_20260201_120005_43198sec_V111`: 2 duplicate values; one further orbit: 1) are **recorded as archive findings** for Milestone VIII, alongside the 12 SoLEXS `STOP≤START` days and 10 unreadable files.

My disposition-(i) recommendation was upheld. 188/188 tests pass; the duplicate orbit verifiably still terminates with F-16.

Raised under: *"Do not revisit parser implementation unless a new parser-level contradiction is proven."* Two are proven. Both are the **same root-cause pattern as CONTRADICTION-001/-003/-004A/-005A**: a §2.8 property asserted from orbit `20251208` (the one M-V orbit) without checking the population. A-12 already anticipated that HK properties need archive-wide verification; these two checks are further HK properties that also don't hold as written.

**r5 rebuild result:** SoLEXS **424/436** (was 353 — Defect A/B fixes recovered 71), HEL1OS **295/391**. New skips: **F-06 × 94**, **F-16 × 2**. Both are in the §2.8 HK parser.

---

## DEFECT A — §2.8 header-span check rejects 94 orbits on float-ULP noise

**The rule (§2.8 r4):** *header-span consistency — the global `mjd` range lies within the header `TSTART`/`TSTOP`.* Implemented as `mjd.min() < TSTART or mjd.max() > TSTOP → F-06`.

**`OBSERVED`, archive-wide (391 orbits):**

| | Orbits | Overshoot magnitude |
|---|---|---|
| `mjd.max() > TSTOP` | **60** | **all 6.28×10⁻⁷ s** |
| `mjd.min() < TSTART` | **40** | **all ≈ 6×10⁻⁷ s** |
| overshoot ≥ 1 s | **0** | — |

Every single violation is **~0.6 microseconds** — the **float64 ULP of an MJD value at ~61000** (`2⁻⁵² × 61000 d × 86400 s/d ≈ 6×10⁻⁷ s`). There is **no orbit whose HK data is genuinely outside its header span**; there are only orbits where a boundary timestamp equals the header bound to physical precision but differs by one representable float step.

**This is not a data anomaly — it is my check testing float representation instead of data validity.** The header `TSTART`/`TSTOP` are themselves MJD floats carrying the same ULP, so "within the header span" cannot be checked more tightly than that ULP. A strict inequality below the ULP scale is meaningless.

**Precedent already in the codebase.** §2.7 R-1 (r4) hit the identical issue — an MJD→seconds comparison landing exactly on a boundary — and it is handled by a documented `_FLOAT_EPS_S = 1e-3` (1 ms, ~1600× the ULP, ~4 orders below the smallest real excursion). The §2.8 header-span check should use the same mechanism.

**Why this is an implementation-faithfulness fix, not a weakening.** The contract's intent — "the `mjd` range lies within the header span" — is *satisfied* by all 391 orbits at physical precision. A real out-of-span excursion would be seconds (a wrong day, a wrong epoch), not sub-microsecond. A 1 ms tolerance absorbs representation noise while still catching every physically meaningful violation.

### Proposed amendment (NOT applied)
1. **§2.8 validation** — clarify header-span consistency as: *`min(mjd) ≥ TSTART − ε` and `max(mjd) ≤ TSTOP + ε`, with `ε = 1 ms` (the documented MJD-float-ULP slack, shared with §2.7 R-1). A violation beyond `ε` → F-06.* This is numerical slack, **not** a physical tolerance and **not** a jitter allowance.
2. No statistic is encoded; the ULP magnitude is stated once as the justification for `ε`.

---

## DEFECT B — 2 orbits have duplicate HK `mjd` timestamps

**The rule (§2.8 r4):** *`mjd` MUST be … **unique** (duplicates remain F-16 — a repeated timestamp is a genuine defect).*

**`OBSERVED`, archive-wide:** exactly **2 orbits** contain duplicate HK `mjd`:
- `HLS_20260201_120005_43198sec_V111` — 63,298 rows, **2** duplicated values (e.g. `61072.99604…` appears twice, rows 10584 & 10660).
- one further orbit — **1** duplicated value.

389 of 391 orbits have fully unique HK `mjd`.

**This one is genuinely a contract question, and I do not think the answer is obvious.** Two defensible readings:

- **(i) Working as designed — no amendment.** §2.8 r4 explicitly calls a duplicate timestamp "a genuine defect", owner-approved. Under that wording these 2 orbits are archive defects, correctly terminated and logged — the same disposition as Defect C's 12 SoLEXS `STOP≤START` days. Recovers nothing, discards 2 orbits, records an archive-quality finding.
- **(ii) Telemetry reality — amend.** §2.8 also establishes that HK `mjd` is *"a measurement, not an index"*, written in arrival order with jitter (A-12). Two packets sharing a millisecond-precision timestamp is consistent with that framing rather than with corruption. Under this reading a duplicate HK `mjd` is not a defect and should not terminate; uniqueness would be dropped for HK (while remaining in force for the 1-second-cadence LC/PI/spectra, where a duplicate genuinely is a defect).

**I record both and recommend (i)** — no amendment — for three reasons: it is the smaller change; it matches the owner's explicit r4 wording; and 2 orbits of 391 is a negligible loss that does not justify weakening a uniqueness guarantee that is correct everywhere else. But this is the owner's call, not mine, because it turns on whether a duplicate HK timestamp is "a defect" or "telemetry" — a question the r4 text answers one way and the r4 rationale gestures at the other.

**Whichever way it is ruled, no statistic enters the contract.** If (ii), duplicates are simply permitted for HK; the *count* stays in the profile.

---

## What is NOT affected

The r5 rebuild is otherwise clean: SoLEXS 424 archives (T1/T2), HEL1OS 295 orbits (T3/T4/T5 all built — the CdTe/CZT `DETCHANS` allowlist works, and **R-1 resolved `relative_seconds` on all 1,180 spectra products**). Defects A and B here concern only the two §2.8 HK validation predicates; every other invariant held. **188/188 unit tests pass** (the M-VII suite already tracks the r5 implication rule).

## State of the work

Milestone VII is **paused with the code committed and both HK checks terminating exactly as frozen**. Nothing weakened: the header-span check still uses strict inequality; the uniqueness check still fires on duplicates. The rebuild's own skip log is the evidence.

**Awaiting approval:** Defect A amendment (float ε on the header-span check); Defect B ruling (recommend disposition (i), no amendment). Once ruled, I will apply, do the final clean rebuild, and generate `CANONICAL_DATASET_PROFILE.md` + `MILESTONE_VII_COMPLIANCE.md` against the final dataset.

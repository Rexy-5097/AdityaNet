---
id: CONTRA-002
title: §2.1's missing-value clause is factually false
status: active
state: CLOSED
resolving_revision: r2
supersedes: []
superseded_by: null
source: artifacts/v2/phase05/CONTRADICTION-002.md
source_date: 2026-07-17
---

> Carried verbatim from `artifacts/v2/phase05/CONTRADICTION-002.md`. The ruling below is the text the owner
> wrote; it is never summarised ([ADR-0013](../../adr/ADR-0013.md)).

# CONTRADICTION-002 — §2.1's missing-value clause is factually false

**Status: CLOSED 2026-07-17 — owner approved the §5 amendment; applied as PARSER_SPECIFICATION.md r2 (§10 Revision History). Milestone III re-verified 63/63 with zero deviations. See COMPLIANCE_M3.md.**

Raised under: *"If the implementation contradicts the specification, STOP, document the contradiction, explain why, and wait for approval."*

---

## 1. Two distinct defects — one mine, one the contract's

**(A) My implementation defect — already fixed, no approval required.** The Milestone III parser raised **F-19 on non-finite COUNTS**. Frozen F-19 covers *"Negative counts / negative EXPOSURE / live_time_s > 60"* — **NaN is not negative**, and §2.1's validation list never mentions finiteness. I invented an unspecified check, and it terminated on the valid D1 reference file. Fixed: NaN now passes through untouched; the negative-count test is inherently NaN-safe (`NaN < 0` is `False`). TIME finiteness is retained under **F-16**, where a NaN timestamp genuinely belongs — it would otherwise silently defeat the monotonicity test, since all NaN comparisons are `False`.

**(B) The contract defect — requires approval.** Contract §2.1 states:

> **Missing values:** no NULL convention declared; absence is expressed via GTI, **not sentinels**.

This is **`OBSERVED` false.** The real archive uses **NaN in `COUNTS` as a missing-data sentinel.**

## 2. Evidence — an exact bijection

Measured on the mandated D1 file `AL1_SOLEXS_20240514_SDD2_L1.lc.gz` against its GTI sibling:

| Quantity | Value |
|---|---|
| Rows | 86,400 |
| NaN `COUNTS` | **5** — at day-offsets `[0, 5, 30072, 30078, 83951]` |
| GTI-excluded seconds (inclusive rule, r1) | **5** — at day-offsets `[0, 5, 30072, 30078, 83951]` |
| **NaN set == GTI-excluded set** | **True** |
| NaN *inside* GTI (unexplained) | **0** |
| Finite *outside* GTI (unexplained) | **0** |
| Finite `COUNTS` | **86,395 == `EXPOSURE`** |
| Finite-count statistics | min 64, median 275, max 29,568 |

`NaN ⟺ GTI-excluded`, exactly and in both directions. The two products encode the same absence **redundantly and consistently**.

**This independently confirms the r1 amendment.** Under the pre-r1 *exclusive* convention, GTI would have excluded ~10 seconds and could never have matched the 5 NaNs. Two mutually confirming lines of evidence from different files now support the inclusive rule — a stronger position than r1 rested on.

## 3. Why the contract is satisfiable anyway (and M-III proceeded)

§2.1's validation list does **not** require a finiteness check. A literal implementation passes NaN straight through and parses the file successfully. The false clause is *descriptive*, not *prescriptive* — unlike CONTRADICTION-001, which made a frozen rule arithmetically impossible. So M-III completed honestly at 63/63, with the fix at (A).

**But it becomes prescriptive at Milestone VII.** §3 T1 requires `counts_total` = "Σ over GTI-good seconds in minute". A naive `sum()` over a minute containing a NaN yields **NaN for the entire minute** — silently destroying 1,439 good seconds of data per affected minute. The contract gives no instruction here, and §2.1 actively misleads an implementer into believing no sentinel exists.

## 4. Fortunate alignment worth noting

Contract §3's **output** convention already reads: *"Never impute; never fill. Absent data is `NaN` + `q_no_data=True`."* The archive's **input** convention is identical. Input and output already agree; only §2.1's description of the input is wrong.

## 5. Proposed amendment (NOT applied — requires approval)

1. **§2.1 Missing values** — replace the false clause with: *`COUNTS` uses **NaN as a missing-data sentinel**. `OBSERVED` on 2024-05-14 SDD2: the NaN set equals the GTI-excluded set exactly (5 s, offsets [0,5,30072,30078,83951]); finite count == `EXPOSURE` == 86,395. NaN MUST pass through the parser untouched — never imputed, filled, or dropped. Zero remains a physically valid count and MUST NOT be treated as missing.*
2. **§2.1 validation** — add: *TIME must be finite (F-16 — a NaN timestamp defeats the monotonicity test). `COUNTS` finiteness is **not** validated at parser level; NaN is data.*
3. **New validation rule (§7) — the strong one.** Add a cross-product integrity check: **`NaN(COUNTS)` set MUST equal the GTI-excluded set exactly**; deviation → **F-09** (GTI inconsistent). This is a materially stronger test than either product yields alone: it validates the light curve against the GTI *and* re-verifies the inclusive convention on every single day. Recommend Milestone VIII run it across all 436 archives alongside the A-8 exposure check.
4. **§3 T1/T2** — mandate NaN-aware aggregation: `counts_total = Σ` over **finite** seconds within the minute (`np.nansum` semantics); `n_seconds_present` counts finite seconds; a minute with zero finite seconds → `counts_total = NaN`, `q_no_data = True`. **Never** let one NaN void a whole minute.
5. **§8** — new assumption **A-9**: *the NaN⟺GTI bijection is VERIFIED on 2024-05-14 SDD2 only* (1 of 436). Milestone VIII must verify archive-wide; any deviation is a scientific finding that TERMINATES validation. Same scoping discipline as A-8.

## 6. Recommendation (ACCEPTED)

Approve. The amendment is descriptive-correction plus a **strengthening**: it adds an integrity rule (§5.3) that the contract lacked, and it closes a silent data-destruction path at T1 (§5.4) before any code depends on it. As with r1, nothing is weakened.

## 7. Resolution

All five proposed changes were **approved and applied verbatim** as spec **r2**: the §2.1 missing-value description replaced; parser behaviour made binding (pass through unchanged; never impute, zero-fill, or remove); the **NaN⟺GTI cross-product rule** added as a REQUIRED archive-consistency check (mismatch → F-09) at the day-assembly layer; the **§3 aggregation contract** added (finite-only aggregation; one NaN must never invalidate a minute; empty minute → `counts_total=NaN`, `q_no_data=True`); and **A-9** recorded, scoping the invariant to the reference archive with a Milestone VIII archive-wide obligation that TERMINATES on any violation.

**Nothing weakened.** The 20 fail-loud rule ids are untouched — r2 adds a new *application* of F-09, not a new rule. Superseded implementation notes were removed from the code, which now cites the contract clause (§2.1 r2) rather than this document.

## 8. State of the work

**Milestone III COMPLETE and re-verified against r2: 63/63 tests pass, 0 xfail, 0 skip, zero deviations.** Real D1 file: 86,400 rows, `TSTART=1715644800.0`, `TSTOP=1715731199.0`, `TIMEDEL=1`, `NUMBAND='4'`, `HDUCLAS3='COUNTS'`, span 00:00:00–23:59:59 UTC, strictly 1-s monotonic. Test `test_real_20240514_nan_positions_equal_gti_excluded_seconds` encodes the now-contractual §2.1 r2 invariant and passes. **Milestone IV authorised.**

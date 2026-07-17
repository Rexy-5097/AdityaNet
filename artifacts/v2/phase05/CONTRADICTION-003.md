<!-- VERSION STATUS: CURRENT — OPEN, non-blocking for M-IV/V/VI, BLOCKING for M-VIII -->
<!-- REASON: Contract §7 spectrum-integrity rule falsified by the real archive. -->
<!-- DATE: 2026-07-17 -->

# CONTRADICTION-003 — §7's spectrum-integrity tolerance is falsified

**Status: OPEN, advance notice. Does NOT block Milestones IV–VII (no implemented behaviour depends on it). BLOCKS Milestone VIII, whose validation protocol asserts it. Raised now rather than at M-VIII because the evidence is already in hand and the fix affects what M-VII must record.**

Milestone IV is **COMPLETE and COMPLIANT** (93/93 tests, zero deviations) — this defect lies in §7's *validation plan*, not in §2.2's parser contract.

---

## 1. The claim

Contract §7 (Scientific Sanity Checks):

> | **Spectrum integrity** | T2 channel-sum vs T1 `counts_total`; T5 vs T3 band sums | **≤ 0.1 %** (SoLEXS) |

## 2. Measured on the D1 reference day (2024-05-14 SDD2)

| Quantity | Value |
|---|---|
| `Σ(340 channels)` vs `.lc COUNTS`, mean abs diff | **569.6 counts** |
| `.lc COUNTS` median | **275 counts** |
| Exact matches | **0 / 86,395** |
| `spec_sum > lc` | **100.0 %** of seconds |
| Ratio `spec_sum / lc` | **median 2.60** (p01 1.13, p99 4.34) |
| `Σ(340)` median vs `.lc` median | **725 vs 275** |

**The discrepancy is ~160%, against a stated tolerance of 0.1%.** The relationship is not noisy — it is systematic and one-directional.

## 3. Interpretation

`LOGICALLY IMPLIED`: **the `.lc` is not the sum over all 340 PI channels.** It is a *band-limited* light curve. Supporting `OBSERVED` evidence: the `.lc` `RATE` HDU carries **`NUMBAND = '4'`** — the SoLEXS pipeline defines four bands — while exposing only `TIME` and `COUNTS`, with no band identification.

A search for the contiguous channel range best reproducing the `.lc` found **[40:170]** at mean abs diff 38.3 — far better than the full-band 569.6, but still only **16/86,395 exact matches**. `HYPOTHESIS`: the `.lc` band is defined by an energy interval mapped through a response the archive does not contain (see §2.2: **no RMF/ARF exists anywhere in the archive**), so it cannot be reconstructed from channel indices alone. This is consistent with, and downstream of, the already-recorded RMF gap.

**Root cause of the §7 defect:** the same class as CONTRADICTION-001 — I asserted a relationship between two fields from their names and OGIP conventions (`HDUCLAS2='TOTAL'`) **without computing it**. `HDUCLAS2='TOTAL'` means "not background-subtracted", not "all channels"; I over-read it.

## 4. Why nothing is blocked yet

No implemented behaviour depends on §7. The M-IV parser neither sums channels nor cross-references the `.lc`. §7 is Milestone VIII's validation protocol, and §3's T1/T2 (Milestone VII) do not require the two to reconcile.

**But it changes what M-VII should record**: if T1 `counts_total` (from `.lc`) and T2 `counts` (340 channels) are *not* commensurable, that must be stated in the schema, or a downstream consumer will reasonably assume `sum(T2.counts) == T1.counts_total` and be wrong by ~2.6×.

## 5. Proposed amendment (NOT applied — requires approval)

1. **§7 Spectrum integrity** — replace the falsified row with two honest checks:
   - *T2 internal consistency*: per-second `Σ(340 channels)` finite ⟺ `.lc COUNTS` finite (the NaN⟺NaN structural check, which **does** hold — verified three-way at M-IV).
   - *T2 vs T1 relationship*: **NOT a tolerance check.** Record the measured ratio `Σ(340)/counts_total` per day as a **reported diagnostic**; flag any day whose median ratio departs from the archive-wide median by >20% as an instrument-configuration change worth investigating. **No pass/fail threshold**, because the correct value is unknown without an RMF.
2. **§3 T1/T2** — add a binding schema note: *`T1.counts_total` (from `.lc`) is **band-limited** and is **NOT** `Σ(T2.counts)`; the observed ratio is ≈2.6 on the reference day. Consumers MUST NOT treat them as interchangeable.*
3. **§2.1** — record that `NUMBAND='4'` and the band definition are **not recoverable from the archive** (no RMF), promoting A-6 from "captured, not interpreted" to an explicit acquisition dependency.
4. **§8** — new assumption **A-10**: *the `.lc`-vs-spectrum ratio (median 2.60) is VERIFIED on the reference day only.* Milestone VIII must report the distribution across all 436 archives; a **bimodal or drifting** ratio would indicate a band or gain change and is a scientific finding.
5. **0.5.3 acquisition** — the RMF/ARF request already ranked #2 should additionally request the **`.lc` band definition**; without it the `.lc` cannot be related to the spectra at all.

## 6. Recommendation

Approve. As with r1/r2 this **strengthens**: it replaces a fabricated tolerance with a measured diagnostic, and it closes a real misuse path (`sum(T2) == T1`) before any consumer depends on it. It also converts an unexplained 2.6× discrepancy into a tracked, archive-wide observable.

**Deliberately NOT proposed:** widening the 0.1% tolerance to fit the data. The relationship is not approximately-true-with-slop; it is a different quantity. A loosened tolerance would be exactly the "make it work" failure the implementation philosophy forbids.

## 7. State of the work

**Milestone IV COMPLETE: 93/93 tests, 0 xfail, 0 skip, zero deviations.** Real D1 `.pi`: (86400, 340), `CHANTYPE='PI'`, `DETCHANS=340`, exposure 1.0 s/spectrum, channel map constant `0..339` (validated then collapsed, F-08), 5 all-NaN spectra at **[0, 5, 30072, 30078, 83951]** — a **three-way** agreement with the `.lc` NaN set and the GTI-excluded set. V-PI-3 (`.pi TSTART[0]` == `.lc TSTART`) passes. Parse: 0.5 s, **2.10 GB peak RSS** — confirming §2.2's streaming mandate is a real constraint, not a stylistic one. **Milestone V not started.**

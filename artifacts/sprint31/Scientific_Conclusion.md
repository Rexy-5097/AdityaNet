<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 7 — the eight pre-set scientific questions, answered from Phase 5 measurements only. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Scientific Conclusion (Phase 7)

Every answer below states evidence first, from `artifacts/sprint31/analysis.json` and the Phase 1–2 records, then the answer with its label.

**Q1. Does Aditya-L1 add measurable information beyond GOES?**
Evidence: F2 (with Aditya features) beats F1 (GOES-only features) on the S2 span — ΔTSS +0.0844 mean, significant 3/5 seeds. But F2 is statistically indistinguishable from F0 (GOES-only, 16-year training) on the same span (0/5 seeds significant, mean −0.0046), and the F2−F1 margin decomposes as (F2−F0) + (F0−F1) = (−0.005) + (+0.089): nearly all of it is the comparator's span-transfer collapse. F1 and F2 differ in BOTH features and training era (pre-registered arms table), so the passing primary endpoint cannot isolate the instrument. Secondary hints cut both ways: F2's ROC-AUC exceeds F0's in all seeds (0.7685 vs 0.7368, point estimates) and its pre-onset episode recall exceeds F0's significantly in 5/5 seeds (+0.39..+0.46) — but the Phase 2 flare-response check found no SoLEXS spectral response at the strongest GOES peaks, and Sprint 27 measured conditional mutual information 0.0.
**Answer: AMBIGUOUS — a 17-feature GOES-only arm trained on the same Stage-2 boundaries (identical era, no Aditya features) would resolve it: if that control matches F2, the gain is training-era match; if F2 exceeds it, the gain is instrument information.**

**Q2. Which engineered features contributed most?**
Evidence: no per-feature ablation was pre-registered or run; the only feature-level measurements are structural (correlation, distribution, flare response).
**Answer: AMBIGUOUS — a pre-registered leave-one-group-out ablation (SoLEXS hardness/variability/activity vs HEL1OS fluence/ratio groups) would resolve it.** The correlation record permits one negative attribution (Q3) but no positive one.

**Q3. Which features were ineffective?**
Evidence: `nonthermal_thermal_ratio` is structurally near-duplicate of GOES `log_long_flux` (r = −0.940, because HEL1OS band0 is nearly constant) — its incremental content is bounded near zero by construction; `d_ntr_15m` correlates 0.458 with `goes_dT_iso_15m`.
**Answer: SUPPORTED BY EVIDENCE for `nonthermal_thermal_ratio` being structurally redundant; AMBIGUOUS for all others (same ablation gap as Q2).**

**Q4. Did physics engineering overcome the bottlenecks identified in Sprint 27?**
Evidence: the three fixable bottlenecks are measurably fixed — channel duplication eliminated (12/22 raw inputs at r 0.85–0.99 → engineered set max cross-instrument |r| 0.045 except the flagged ratio), normalization applied (all features scaled, verified), masks now consumed (per-timestep channels are model inputs 33–36; the dataset_v3.py:110-111 scalar collapse is gone; zero-fill eliminated — no feature ingests a fake zero). The fourth, deepest bottleneck — whether the instruments carry conditional information at all — shows no improvement: F2 ≈ F0 at window level, and SoLEXS showed no co-temporal response at the two strongest GOES peaks in s2_val (Phase 2 finding 7).
**Answer: SUPPORTED BY EVIDENCE for the engineering bottlenecks (duplication, normalization, mask handling); NOT SUPPORTED for the information bottleneck — the fair test did not show the instruments adding window-level skill beyond GOES.**

**Q5. Is the primary limitation features, architecture, or available instrument information?**
Evidence: features are now verified correct, deduplicated, physically grounded (Phase 1–2) — yet window TSS did not exceed the GOES-only ceiling, arguing against "features" as the remaining limitation. Architecture is untested at this data quality (F3 pending). Instrument information: Sprint 27's CMI-zero audit, the flare-response null, and F2 ≈ F0 all point that way — but the training-era confound and the un-run F3 keep two alternatives alive.
**Answer: AMBIGUOUS — the era-matched GOES-only control (Q1 gap) plus the F3 fusion arm would jointly resolve it; the current weight of evidence leans toward available instrument information (or the 18-month data volume) over features.**

**Q6. What operator benefit was gained?**
Evidence: `Operator_Report.md` table — pre-onset episode recall 0.8111 (F2 mean) vs 0.3704 (F0), significant in 5/5 seeds; episode recall +0.30; cost: false episodes 37.2/month vs 3.7, yellow duty 0.319 vs 0.218; Operator Utility (V_max = TSS) unchanged (0.4022 vs 0.4068, n.s.).
**Answer: SUPPORTED BY EVIDENCE — a large, seed-consistent pre-onset warning gain, purchased at ~10× the false-alarm load, with zero net change in peak cost-loss value.**

**Q7. Is any improvement operationally meaningful for satellite operators?**
Evidence: equal V_max means the improvement is a repositioning along the ROC surface, not added value at the current thresholds; whether 81%-vs-37% pre-onset coverage justifies 37-vs-3.7 false episodes/month depends on the operator's cost/loss ratio, which is not measured anywhere in this repository.
**Answer: AMBIGUOUS — an episode-level cost-loss policy analysis with an operator-supplied C/L ratio (new pre-registration; the Path C parallel track) would resolve it.**

**Q8. Is further Aditya-L1 feature engineering scientifically justified?**
Evidence: the pre-registered feature-engineering hypothesis received its fair test — 15 physics-grounded, verified-correct features spanning every mechanism Sprint 27 named (hardness, variability, activity memory, Neupert fluence, nonthermal ratio); the result did not lift window skill above the GOES-only baseline, and the remaining pre-registered questions are architectural (F3) and attributional (era control), not feature-space questions. No unexplored feature mechanism with Sprint 27 evidentiary support exists (`02_FEATURE_PIPELINE_V4.md` "Explicitly absent" section).
**Answer: NOT SUPPORTED — further feature engineering is not the indicated next step; the open questions are the F3 fusion test (mandated by Case A) and the training-era control, after which the instrument question closes.**

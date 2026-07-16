<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 — capability checkpoint and recall-versus-false-episodes trade-off analysis. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Operating Point Analysis

**The trade-off curve does not intersect the deployment region (episode recall ≥ 0.80 AND false episodes per month ≤ 5.0) at any tested threshold: the minimum observed false-episode rate while holding mean episode recall at or above the 0.80 floor is 14.27 per month (five-seed mean curve, threshold 0.225, mean recall 0.8018) — 2.9 times the pre-registered budget. Under the pre-registered Component 3 definition this classifies the detector `SIGNAL-LIMITED`; that term is scoped strictly to its frozen definition ("cannot reach the deployment criterion at any threshold operating point") and does not assert that the SoLEXS+HEL1OS signal itself is insufficient, which remains untested.** Data: `artifacts/sprint33_nowcast/analysis.json` (five-seed aggregate and per-seed curves), all derived from the frozen sealed test predictions with no model re-inference.

## Capability-confirmation checkpoint (frozen contract quality gate 3)

`OBSERVED`: three-seed mean validation window ROC-AUC 0.8915 ± 0.0025 (seeds 42/43/44: 0.8931, 0.8886, 0.8927) ≥ the 0.87 gate — **PASS**, reproducing the single-seed feasibility value of 0.8980 within the measured seed-noise band. The escalation seeds continued the pattern (seed 45: 0.8857, seed 46: 0.8991), so the capability replication now rests on five seeds.

## The five-seed mean trade-off curve near the decision boundaries (OBSERVED)

| Threshold | Mean episode recall | Mean false episodes/month |
|-----------|---------------------|----------------------------|
| 0.150 | 0.8589 | 20.15 |
| 0.185 | 0.8258 | 15.80 |
| 0.225 | 0.8018 | **14.27** ← minimum at the recall floor |
| 0.235 | 0.7964 | 13.70 (below the floor) |
| 0.295 (sweep end) | ≈ 0.79 | ≈ 11.9 |

**Sweep-range caveat (corrected wording):** the curve was swept over thresholds 0.005–0.295. Within that range no point achieves false episodes per month ≤ 5.0 at any recall; the earlier phrasing "maximum recall at the budget is 0.0" is supported **only within the swept range** — beyond threshold 0.295 recall is already below the 0.80 floor and unmeasured, so points with ≤ 5.0 false episodes at some sub-floor recall may exist. The deployment-region conclusion is unaffected: every point with recall ≥ 0.80 lies at thresholds ≤ 0.225, fully inside the sweep, all at ≥ 14.27 false episodes per month.

## Properties of the operating points (OBSERVED)

The per-seed validation-selected thresholds differ (0.030–0.110) because each seed's calibrated probability scale differs, yet all five land at 0.90–0.93 test episode recall with stability ≤ 0.0175 — the selection protocol is robust. The large across-seed false-episode spread at matched recall (22.44–50.92 per month, std 11.17) is the sprint's most notable secondary finding: seeds that are nearly identical in window-level separability (ROC-AUC 0.896–0.904) differ by 2.3× in false-episode production, suggesting the false episodes arise from borderline probability mass whose episode structure is seed-sensitive — directly relevant to any future cross-seed-ensemble policy, and one of the questions Experiment A's attribution will inform.

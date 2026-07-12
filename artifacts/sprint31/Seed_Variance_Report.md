<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 5 — across-seed variance and escalation record for F2. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Seed Variance Report (F2)

**The escalation rule fired on the narrowest margin yet measured: the three pre-registered seeds' test True Skill Scores (0.3935 / 0.4088 / 0.3962) span 0.0153 against the 0.015 trigger, and the decision was taken automatically by `scripts/sprint31/auto_escalate.py` with no metric revealed before Phase 5 (OBSERVED). The final five-seed picture: F2 TSS 0.4022 ± 0.0151, range 0.0380 — roughly half the seed noise of the F1 pipeline on the V1 span (std 0.0276, range 0.0640, Sprint 30), but the paired ΔTSS against F1 varies by a factor of three across seeds (+0.042 to +0.125, std 0.0352), which is why only 3 of 5 seeds clear the significance half of the primary criterion.**

## Escalation record

| Step | Event |
|------|-------|
| 1 | Seeds 42/43/44 trained; evaluations sealed |
| 2 | `auto_escalate.py` reads sealed TSS values, computes range 0.0153 > 0.015, prints only "ESCALATION TRIGGERED", exit 42 |
| 3 | Seeds 45/46 trained under the identical frozen protocol inside the same chain — no manual intervention |
| 4 | Phase 5 unsealing with the pre-declared 5-seed majority criterion (≥ 3 of 5; committed `30d4f23` before ANY Sprint 31 result existed) |

## Across-seed statistics (OBSERVED / DERIVED)

| Quantity | Value | Label |
|----------|-------|-------|
| F2 TSS per seed (42/43/44/45/46) | 0.3935 / 0.4088 / 0.3962 / 0.3873 / 0.4254 | OBSERVED |
| F2 TSS mean ± std (ddof=1) | 0.4022 ± 0.0151 | DERIVED |
| F2 TSS range (5 seeds) | 0.0380 | DERIVED |
| Paired ΔTSS (F2−F1) per seed | +0.0551 / +0.0914 / +0.1083 / +0.0419 / +0.1251 | OBSERVED |
| ΔTSS (F2−F1) mean ± std; Cohen's d | +0.0844 ± 0.0352; +2.40 | DERIVED |
| Paired ΔTSS (F2−F0) per seed | −0.0134 / +0.0020 / −0.0106 / −0.0195 / +0.0185 | OBSERVED |
| ΔTSS (F2−F0) mean ± std; Cohen's d | −0.0046 ± 0.0151; −0.30 | DERIVED |
| F2 best-epoch validation TSS per seed | 0.4350 / 0.4860 / 0.4159 / 0.4557 / 0.4602 (std 0.026) | OBSERVED |
| F1-on-S2 TSS per seed (comparator) | 0.3384 / 0.3174 / 0.2879 / 0.3455 / 0.3002 (std 0.024) | OBSERVED |

Within-run and across-seed uncertainty reported separately, never pooled (plan §2). The S2 span's single-run bootstrap CIs are wide (± ≈ 0.07 half-width at 90 blocks vs ± ≈ 0.035 at 628 blocks on the V1 span) — the shorter span, not the model, drives this.

## Observations

1. The ΔTSS(F2−F1) seed spread (0.0352) exceeds the ΔTSS(F2−F0) spread (0.0151) because BOTH arms contribute seed noise to the former while F0 is fixed. Seed pairing (same-seed F2 vs F1) does not cancel it — the two trainings share nothing but the integer seed.
2. The borderline seeds (42, 45) are the two where F1-on-S2 happened to land its best values (0.3384, 0.3455) — the primary-endpoint significance pattern tracks the comparator's seed luck as much as F2's, reinforcing the decomposition in `Statistical_Analysis.md`.
3. Cross-sprint constant: every trained configuration in this program (F1 on V1 span, F1 on S2, F2 on S2) shows across-seed TSS ranges of 0.024–0.064, always above the 0.015 trigger — escalation to 5 seeds should be treated as the default budget for any future arm (carried to `Version4_Status_Report.md`).

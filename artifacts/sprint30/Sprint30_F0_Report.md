<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 3 — F0 arm execution record. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — F0 Report (GOES-14 baseline, frozen V1 reference)

**F0 was executed exactly as pre-registered in `artifacts/sprint29/experiments/F0.json`: `"training": "NONE (frozen checkpoint)"` — the arm is the single frozen V1 Baseline checkpoint, re-evaluated once through the frozen Sprint 24 harness with results sealed until Phase 5. Its policy-operating-point True Skill Score of 0.3940129618 (OBSERVED this session) reproduces the pre-registered reference value 0.3940 to the fourth decimal, which is simultaneously the reproducibility gate for the whole experiment.**

## Protocol note — one flag, resolved conservatively

The Sprint 30 brief's Phase 3 wording ("Run F0 … Seeds 42, 43, 44 … for each seed record: training history…") conflicts with the immutable contract `F0.json`, which pre-registers F0 as an untrained frozen reference. The contract governs (the brief's own top rule: "Run F0 exactly as specified in F0.json" and "Do not alter any scientific protocol"). The seeds 42/43/44 are the pre-registered **F1** training seeds; F0 carries no seed distribution. Training three fresh F0 baselines would have replaced the pre-registered arm with a different one after registration. Consequence for reporting: F0 statistics are a single point with a within-run block-bootstrap confidence interval; across-seed mean ± standard deviation applies to F1 only (see `Seed_Variance_Report.md`).

## The frozen checkpoint (OBSERVED — trained this session, Sprint 26A)

| Field | Value |
|-------|-------|
| Checkpoint path | `artifacts/sprint26a/runs/Baseline/best.pt` |
| Configuration | V1 PatchTST, 14 GOES features, 822,401 trainable parameters |
| Seed | 42 |
| Training history | 11 epochs, val TSS 0.5680 → 0.6053; best epoch 8 (val TSS 0.6053); early stop at epoch 11 (patience 3) |
| Protocol | Sprint 25 frozen protocol (AdamW lr 1e-4, weight decay 1e-4, FocalLoss γ=2.0 α=0.25, WeightedRandomSampler, clip 1.0, batch 64, 5000 steps/epoch, cosine T_max=20) |
| Training runtime | 2,294 s (38.2 min), MPS |
| Determinism evidence | An independent seed-42 rerun in Sprint 26A produced an identical trajectory (Sprint 26A determinism record) |

## Sprint 30 re-evaluation (OBSERVED — `scripts/sprint30/eval_run.py`, sealed until Phase 5)

Evaluation: frozen Sprint 24 `UnifiedEvaluator` (`scripts/sprint24/eval_framework.py`, fingerprint-verified in Phase 0), isotonic calibration fit on validation only, deployed clean policy thresholds yellow 0.14 / red 0.95 applied to calibrated test probabilities. Runtime 607 s. Calibrated validation/test probability arrays archived in `artifacts/sprint30/runs/F0/` for the Phase 5 paired analysis.

| Metric (policy operating point, test span 2023-01-01..2026-06-14) | Value | 95% CI (block bootstrap) |
|--------|-------|--------------------------|
| True Skill Score | 0.3940 | [0.3559, 0.4298] |
| ROC-AUC | 0.7521 | — |
| PR-AUC | 0.4680 | — |
| Precision / Recall (window) | 0.3988 / 0.7236 | — |
| Expected Calibration Error (test) | 0.0685 | — |
| Brier (test) | 0.1560 | — |
| Episode recall | 0.7301 | — |
| Pre-onset episode recall | 0.6192 | — |
| False episodes / month | 3.16 | — |
| Median lead time | 1,451 min | — |
| Yellow duty cycle | 0.4210 | — |

Validation-side records (selection side, never test): swept-threshold validation TSS 0.6042; validation calibration ECE 7.5×10⁻¹⁸ (fit-set value — isotonic is fit on this same split, so near-zero by construction and reported only for completeness), validation Brier 0.0330.

**Reproducibility check (DERIVED):** re-evaluated policy TSS 0.3940129618 vs the pre-registered reference 0.3940 (`F0.json:reference_result`, from `artifacts/sprint26a/runs/Baseline/eval.json`) — match. The frozen harness, calibration path, and policy thresholds reproduce exactly; stopping-rule trigger (b) "baseline reproduction failure" did NOT fire.

Full machine-readable record: `artifacts/sprint30/runs/F0/eval.json`; complete metric table including HSS, MCC, valswept operating point, and paired-vs-persistence/climatology comparisons therein.

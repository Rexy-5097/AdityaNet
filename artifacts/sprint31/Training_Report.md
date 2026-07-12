<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 3 — F2 training record, 5 seeds after automatic escalation. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Training Report (F2, 32 features + 4 disclosure channels)

**F2 — V1 PatchTST at input width 36 (867,457 parameters), Sprint 25 frozen protocol unchanged, dataset_v4.1.0-s2 Stage-2 boundaries — trained at pre-registered seeds 42/43/44; the automatic escalation check then fired (across-seed test TSS range exceeded 0.015, decided by `scripts/sprint31/auto_escalate.py` without any metric reaching stdout) and seeds 45/46 trained with zero manual intervention. All five runs early-stopped at epoch 4 with best validation TSS at epoch 1 — immediate overfitting on the 786,298-row Stage-2 training split, handled by the protocol's own patience rule, no intervention (OBSERVED).**

| Seed | Epochs | Best epoch | Best val TSS | Val trajectory | Runtime | Checkpoint |
|------|--------|-----------|--------------|----------------|---------|------------|
| 42 | 4 | 1 | 0.4350 | 0.435 → 0.370 → 0.351 → 0.309 | 12.9 min | `artifacts/sprint31/runs/F2_s42/best.pt` |
| 43 | 4 | 1 | 0.4860 | 0.486 → 0.407 → 0.335 → 0.341 | 13.0 min | `artifacts/sprint31/runs/F2_s43/best.pt` |
| 44 | 4 | 1 | 0.4159 | 0.416 → 0.389 → 0.339 → 0.380 | 13.6 min | `artifacts/sprint31/runs/F2_s44/best.pt` |
| 45 | 4 | 1 | 0.4557 | 0.456 → 0.377 → 0.364 → 0.385 | 13.7 min | `artifacts/sprint31/runs/F2_s45/best.pt` |
| 46 | 4 | 1 | 0.4602 | 0.460 → 0.398 → 0.331 → 0.374 | 13.9 min | `artifacts/sprint31/runs/F2_s46/best.pt` |

Protocol (unchanged, `artifacts/sprint25/02_retraining_protocol.md`): AdamW lr 1e-4, weight decay 1e-4, CosineAnnealingLR T_max 20, FocalLoss γ 2.0 α 0.25, WeightedRandomSampler, gradient clip 1.0, batch 64, 5,000 steps/epoch, 2,000 validation steps, patience 3 on validation TSS, isotonic calibration on validation only. Driver: `scripts/sprint31/train_driver.py` (verified path-only copy of the Sprint 30 driver). Sealed evaluation: `scripts/sprint31/eval_s2.py` — the frozen Sprint 24 `UnifiedEvaluator` instantiated on the S2 test span per the pre-registered modification in `04_FAIR_ADITYA_EXPERIMENT.md`, no test metric printed before Phase 5.

**Observations (labeled):**
- OBSERVED: the epoch-1-peak pattern is universal across seeds. The Stage-2 split provides ~18 months of data at a 31.35% positive-window rate; one epoch of 320,000 weighted samples already saturates the extractable validation skill, after which memorization degrades transfer to the 2025-06..2025-12 validation half-year.
- OBSERVED: no prediction collapse (stopping trigger (a) never fired); all runs healthy; MPS wall time ~13 min/run — half the F1 runtime despite 2.1× input width, because early stopping cut every run to 4 epochs.
- DERIVED: F2's validation-side seed spread (0.416–0.486, std 0.026) is five times F1's validation spread on its own split — consistent with the small-data regime; the pre-registered escalation to 5 seeds was therefore the expected path (its trigger was confirmed automatically post-hoc on sealed test values).
- NOT PROVEN: whether longer training with more S2-era data would change the ranking — no such arm is pre-registered.

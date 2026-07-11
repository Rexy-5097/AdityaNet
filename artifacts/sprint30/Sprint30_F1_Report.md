<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 4 — F1 arm execution record (5 seeds after pre-registered escalation). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — F1 Report (GOES-physics, 17 features)

**F1 — the frozen V1 protocol on 17 features (the 14 KEEP set plus `goes_T_iso`, `goes_EM`, `goes_dT_iso_15m`) over `dataset_v4.0.0` — was trained at the three pre-registered seeds 42/43/44 and, after the pre-registered escalation rule fired (across-seed TSS range 0.0426 > 0.015), at seeds 45/46 as well. No seed was rerun, no hyperparameter was touched, and no test metric was inspected before Phase 5. Headline (unsealed in Phase 5): F1 test True Skill Score 0.3629 ± 0.0276 across 5 seeds versus F0's 0.3940 — the paired ΔTSS is negative in 4 of 5 seeds (OBSERVED).**

## Configuration (per `artifacts/sprint29/experiments/F1.json` — no deviations)

V1 PatchTST with `n_features=17` (828,545 trainable parameters vs the 14-feature model's 822,401 — the difference is the patch-embedding width, the contract's only allowed change); Sprint 25 frozen protocol (AdamW lr 1e-4, weight decay 1e-4, CosineAnnealingLR T_max=20, FocalLoss γ=2.0 α=0.25, WeightedRandomSampler, gradient clip 1.0, batch 64, 5,000 steps/epoch, 2,000 validation steps, patience 3 on validation TSS, isotonic calibration fit on validation only); dataset `artifacts/research_v4/dataset_v4.0.0/` (frozen split boundaries verified byte-identical — see `Dataset_Validation_Report.md`). Driver: `scripts/sprint30/train_driver.py`; evaluation: `scripts/sprint30/eval_run.py` through the frozen Sprint 24 harness, sealed.

**Attribution caveat (pre-registered design property):** F1 differs from F0 by the three physics features AND the V4 preprocessing (train-only robust scaling of all 17 inputs) jointly — `F1.json` specifies the V4 pipeline, F0 is the frozen raw-feature model. Any F1-vs-F0 delta is attributable to that bundle, not to the physics features in isolation.

## Per-seed training records (OBSERVED — `artifacts/sprint30/runs/F1_s*/history.json`, `run_meta.json`)

| Seed | Epochs run | Best epoch | Best val TSS | Early-stop trigger | Runtime | Checkpoint |
|------|-----------|-----------|--------------|--------------------|---------|------------|
| 42 | 7 | 4 | 0.6138 | patience 3 at epoch 7 | 24.9 min | `artifacts/sprint30/runs/F1_s42/best.pt` |
| 43 | 6 | 3 | 0.6142 | patience 3 at epoch 6 | 24.1 min | `artifacts/sprint30/runs/F1_s43/best.pt` |
| 44 | 6 | 3 | 0.6199 | patience 3 at epoch 6 | 23.8 min | `artifacts/sprint30/runs/F1_s44/best.pt` |
| 45 | 11 | 8 | 0.6140 | patience 3 at epoch 11 | 41.0 min | `artifacts/sprint30/runs/F1_s45/best.pt` |
| 46 | 4 | 1 | 0.6044 | patience 3 at epoch 4 | 14.0 min | `artifacts/sprint30/runs/F1_s46/best.pt` |

All five runs converged without prediction collapse (stopping-rule trigger (a) did not fire). Validation-side calibration: isotonic, fit-set ECE ≈ 10⁻¹⁷ (by construction), validation Brier 0.0324–0.0336 across seeds. Every seed's best validation TSS (0.6044–0.6199) is at or above F0's 0.6053 — the validation picture favored F1 before the sealed test evaluation reversed it (see `Statistical_Analysis.md` on this regime-transfer pattern).

## Per-seed test metrics (OBSERVED — unsealed at Phase 5; policy operating point, frozen harness)

| Seed | TSS | 95% CI | ROC-AUC | PR-AUC | ECE | Episode recall | Pre-onset recall | False ep/mo | Duty cycle | Median lead (min) |
|------|-----|--------|---------|--------|-----|----------------|------------------|-------------|-----------|--------------------|
| 42 | 0.3851 | [0.3501, 0.4194] | 0.7571 | 0.5037 | 0.0736 | 0.7808 | 0.7205 | 16.76 | 0.3815 | 678 |
| 43 | 0.3543 | [0.3194, 0.3865] | 0.7458 | 0.4899 | 0.0791 | 0.8068 | 0.7507 | 16.66 | 0.4013 | 626 |
| 44 | 0.3426 | [0.3072, 0.3761] | 0.7438 | 0.4831 | 0.0818 | 0.7877 | 0.7164 | 14.78 | 0.4051 | 635 |
| 45 | 0.3983 | [—] | 0.7672 | 0.5149 | 0.0657 | 0.8452 | 0.8260 | 20.40 | 0.4110 | 890 |
| 46 | 0.3343 | [—] | 0.7264 | 0.4281 | 0.0905 | 0.8397 | 0.7808 | 16.13 | 0.4696 | 696 |
| **mean ± std** | **0.3629 ± 0.0276** | | 0.7481 | 0.4839 | 0.0781 | 0.8120 | 0.7589 | 16.94 | 0.4137 | 705 |

(F0 reference row for reading: TSS 0.3940, ROC-AUC 0.7521, PR-AUC 0.4680, ECE 0.0685, episode recall 0.7301, pre-onset recall 0.6192, false episodes/month 3.16, duty cycle 0.4210, median lead 1,451 min.) Per-seed CIs for seeds 45/46 are in `artifacts/sprint30/runs/F1_s4*/eval.json`; the paired deltas with CIs are in `Statistical_Analysis.md`.

## Escalation record

After seeds 42/43/44, the across-seed TSS range was 0.0426 > the pre-registered 0.015 trigger (`F1.json:seed_escalation_rule`), so seeds 45/46 were trained under the identical protocol **before any verdict** (commit `89a688d` pre-declares the 5-seed majority criterion before those seeds ran). Seed 45 produced F1's best result (TSS 0.3983, the only positive paired delta, +0.0043); seed 46 its worst (0.3343). Final 5-seed range: 0.0640. No seed was rerun; disappointing results were recorded and the protocol continued, per the governing integrity rules.

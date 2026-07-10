<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 pre-registered retraining protocol, exact values from repository evidence. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Pre-Registered Retraining Protocol (Baseline B0)

**Conclusion:** The protocol baseline is the frozen Version 1 training configuration reproduced exactly, plus one addition — five random seeds — to establish the seed variance that does not yet exist. Every hyperparameter below is the value actually used to train the deployed checkpoint, cited to its source file and line; the only parameter not derivable from repository evidence is the seed *count*, which is marked and registered as a pre-registration decision. A reviewer can replicate B0 from this document alone.

This baseline is deliberately identical to the frozen configuration so that the ablation matrix (`03_experiment_matrix.csv`) isolates single interventions against a known reference. No parameter here is chosen from general machine-learning knowledge; where the repository is silent, the text says `NOT PROVEN`.

## Model (unchanged, frozen architecture)

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Architecture | PatchTST with CLS token | `app/services/ml/model.py`; `PROJECT_STATUS.md` model inventory |
| Sequence length | 360 minutes | `app/services/ml/config.py` FORECAST_HORIZON_MINUTES=360; `PROJECT_STATUS.md` |
| Input features | 14 GOES features | `artifacts/feature_columns.json` |
| Patch length / stride | 16 / 8 (44 patches + CLS = 45 tokens) | `PROJECT_STATUS.md` model inventory |
| Encoder | 4 layers, 8 heads, embed 128, feed-forward 512 | `PROJECT_STATUS.md` model inventory |
| Dropout | 0.2 | `PROJECT_STATUS.md` model inventory |
| Trainable parameters | 822,401 | `artifacts/sprint24/...` Step 1 verification this session (total 828,161 incl. positional-encoding buffer) |

The architecture is held fixed in Sprint 25 by design; this campaign tests training procedure, not architecture.

## Optimization

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Optimizer | AdamW | `app/services/ml/trainer.py:158-160` |
| Learning rate | 1e-4 | `app/services/ml/trainer.py:114`; `scripts/train_patchtst.py:222` (default) |
| Weight decay | 1e-4 | `app/services/ml/trainer.py:114,158-160` |
| AdamW betas / eps | PyTorch defaults (0.9, 0.999) / 1e-8 | `app/services/ml/trainer.py:158-160` passes neither → framework defaults; exact frozen-run override is `NOT PROVEN` beyond the framework default |
| Gradient clipping | max norm 1.0 | `app/services/ml/trainer.py:115,183` |
| Learning-rate schedule | CosineAnnealingLR, T_max = max_epochs | `app/services/ml/trainer.py:161-162` |
| Warmup steps | 0 (no warmup scheduler present) | `app/services/ml/trainer.py` contains no warmup — absence is the evidence |

## Loss and sampling

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Loss function | Focal Loss | `app/services/ml/trainer.py:40-71,155-156` |
| Focal gamma | 2.0 | `app/services/ml/trainer.py:54-56,156` |
| Focal alpha | 0.25 (clamp range [0.25, 0.75]) | `app/services/ml/trainer.py:57-59,155-156` |
| Loss reduction | mean | `app/services/ml/trainer.py:54` |
| Sampler | WeightedRandomSampler, weight_pos=1/n_pos, weight_neg=1/n_neg (balances to ~0.50) | `app/services/ml/dataset.py:116-140` |

## Training loop

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Batch size | 64 | `scripts/train_patchtst.py:26,219` ("use 64 if memory allows"); note the argparse *default* is 32 and the frozen run's exact batch size is `NOT PROVEN` (`artifacts/training_history.json` does not record it) — 64 registered as the documented intended value |
| Steps per epoch | 5000 (cap) | `scripts/train_patchtst.py:223` (default) |
| Validation steps | 2000 | `scripts/train_patchtst.py:224` (default) |
| Maximum epochs | 20 | `scripts/train_patchtst.py:220` (default) |
| Early stopping criterion | validation True Skill Score | `app/services/ml/trainer.py:272,285,330-337` |
| Early stopping patience | 3 | `app/services/ml/trainer.py:112,115,272` |
| Number of seeds | **5** | Multi-seed is required by `artifacts/sprint24/08_final_verdict.md` and the single-seed limitation in `artifacts/sprint23_5/VERSION3_LIMITATIONS.md`; the specific count 5 is `NOT PROVEN` from repository evidence and is registered as a pre-registration decision to obtain a five-point variance estimate |
| Seed values | 42, 43, 44, 45, 46 | seed 42 matches the frozen run (`artifacts/sprint14c/test_results_model_D_seed_42.json`); 43-46 are consecutive registered additions |
| Device | Apple M4, Metal Performance Shaders (MPS); CPU fallback on out-of-memory | `app/services/ml/trainer.py:284-297`; `artifacts/project_status/project_status.json` (mps_available true, cuda_available false) |

## Checkpoint selection

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Selection metric | best validation True Skill Score | `app/services/ml/trainer.py:285,330-337` |
| Decision threshold | best_threshold via find_best_threshold(metric="tss") on the validation sample | `app/services/ml/trainer.py:237` |
| Saved contents | epoch, val_tss, best_threshold, model, optimizer, scheduler state | `app/services/ml/trainer.py:248-256` |

## Calibration

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Method | Isotonic Regression fit on validation predictions | `scripts/calibrate_model.py:191-202`; frozen `artifacts/calibrator.pkl` (method="isotonic", verified this session) |
| Selection | winner by validation Brier score | `scripts/calibrate_model.py:222-262` |
| Test data in calibration | none (validation only) | `scripts/calibrate_model.py:144` comment; `artifacts/operator_trust_audit.json` |

## Operator-policy generation

| Parameter | Exact value | Evidence |
|-----------|-------------|----------|
| Procedure | Validation-only episode-level cost-loss threshold selection, promoted through the Sprint 23 provenance-gated policy pipeline | `app/services/ml/policy.py`; `scripts/sprint23/promote_sprint56_policy.py`; `artifacts/sprint23/Policy_Architecture.md` |
| Evaluation harness | the frozen Sprint 24 `UnifiedEvaluator` (`scripts/sprint24/eval_framework.py`), block bootstrap block length 2,880 windows | `artifacts/sprint24/01_evaluation_framework.md` |
| Baselines held fixed | persistence True Skill Score 0.3018, climatology True Skill Score 0.0000 from Sprint 24 | `artifacts/sprint24/results_abc.json` |
| Test data in policy selection | none — thresholds swept on validation predictions only | `scripts/refine_thresholds.py` isolation pattern; Sprint 23 leakage guard `app/services/ml/policy.py` |

## Fixed evaluation contract (applies to B0 and every ablation)

All models are scored through the **same** frozen Sprint 24 harness with the identical episode construction (60-minute merge gap, onset = start + 360 minutes), the identical moving-block bootstrap (2,880-window blocks, 1,000 replicates; episode blocks of 10; seed 20260704), and the identical persistence and climatology baselines. No model gets a bespoke evaluation. Metrics are computed on the frozen test split (`artifacts/research/test.parquet`, 1,806,313 windows) exactly once per model, after all training and all validation-only selection are complete.

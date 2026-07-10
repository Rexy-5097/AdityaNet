<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26B E2 execution report (single-seed, exploratory). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 26B — E2 Execution Report

> Exploratory result only. Sprint 26B confirmation required before scientific conclusions.

**Conclusion:** E2 (uncapped steps per epoch = 80,646, seed 42, all other hyperparameters at the protocol baseline) completed successfully and produced a test policy True Skill Score of **0.3770**, which is **below** the retrained Baseline's 0.3940. Training on the full dataset each epoch caused clear overfitting to the quiet-sun Solar Cycle 24 training distribution: validation True Skill Score peaked at epoch 2 (0.5718) and then declined every subsequent epoch while the training loss continued to fall, so the best checkpoint (epoch 2, validation True Skill Score 0.5718) sits well under Baseline's 0.6053. Every value below is `OBSERVED` (measured this session) unless marked `NOT PROVEN`.

## Execution

- Started from scratch (no prior E2 checkpoint existed — confirmed this session). Seed 42, steps_per_epoch 80,646, max_epochs 20, patience 3, AdamW learning rate 1e-4, weight decay 1e-4, CosineAnnealingLR T_max = max_epochs, Focal Loss gamma 2.0 alpha 0.25, WeightedRandomSampler, isotonic calibration — all `OBSERVED` from `artifacts/sprint26b/runs/E2/run_meta.json`, exactly per `artifacts/sprint25/03_experiment_matrix.csv`.
- Checkpoint path: `artifacts/sprint26b/runs/E2/best.pt` (`OBSERVED`).
- No hardware failure; no out-of-memory; no Metal Performance Shaders crash.

## Training metrics (`OBSERVED`)

| Metric | Value |
|--------|-------|
| Best validation True Skill Score | 0.5718 at epoch 2 |
| Early stopping | stopped at epoch 5 (patience 3 from the epoch-2 peak) |
| Total epochs run | 5 |
| Training wall time | 238.6 minutes (~4.0 hours) |
| Per-epoch time | ~2,836–2,903 seconds (~47–48 minutes) |
| Peak memory | 0.015 GB (`torch.mps.current_allocated_memory`; under-reports true unified memory — process resident set was ~2.0 GB) |
| MPS / CPU utilization percentage | `NOT PROVEN` — not instrumented this session |

### Loss curve and validation trajectory (`OBSERVED`)

| Epoch | Validation True Skill Score | Training loss |
|-------|-----------------------------:|--------------:|
| 1 | 0.5635 | 0.034387 |
| 2 | **0.5718 (peak)** | 0.030602 |
| 3 | 0.5299 | 0.027457 |
| 4 | 0.5154 | 0.025836 |
| 5 | 0.4388 | 0.024977 |

**Stability note (`OBSERVED`):** the training loss decreased monotonically every epoch (0.0344 → 0.0250) while validation True Skill Score rose only through epoch 2 and then fell every epoch thereafter. This divergence — loss down, validation skill down — is the signature of overfitting. Because each uncapped epoch performs the full ~80,646 optimizer steps over the 5.16-million-window Solar Cycle 24 training set (positive rate 0.62%), the model fit the majority-negative quiet-sun distribution more tightly than the capped Baseline did, and that tighter fit did not transfer to the validation regime. No prediction collapse (all-positive or all-negative) occurred.

## Evaluation results (frozen Sprint 24 framework, `OBSERVED`)

Evaluated only through `scripts/sprint24/eval_framework.py`; source `artifacts/sprint26b/runs/E2/eval.json`. Deployed policy thresholds (yellow 0.14, red 0.95) applied to isotonic-calibrated test probabilities.

| Metric | E2 | Baseline (reference) |
|--------|---:|---------------------:|
| Test policy True Skill Score | 0.3770 | 0.3940 |
| True Skill Score advantage over persistence | +0.0752 | +0.0923 |
| ROC-AUC | 0.7493 | 0.7521 |
| PR-AUC | 0.4791 | 0.4680 |
| Expected Calibration Error | 0.0643 | 0.0685 |
| Brier score | 0.1541 | 0.1548 |
| Heidke Skill Score | 0.2835 | 0.3106 |
| Matthews Correlation Coefficient | 0.3198 | 0.3349 |
| Precision | 0.3809 | 0.3959 |
| Recall | 0.7409 | 0.7300 |
| F1 | 0.5031 | 0.5061 |
| Episode Recall | 0.7562 | 0.7301 |
| Pre-onset Episode Recall | 0.7000 | 0.6192 |
| False Episodes per Month | 3.018 | 3.163 |
| Yellow Duty Cycle | 0.4514 | 0.4210 |
| Validation-swept single-threshold test True Skill Score | 0.1920 | 0.0207 |

**Reading the evaluation (`OBSERVED`, single-seed):** on the primary endpoint (test policy True Skill Score / advantage over persistence) E2 is below Baseline by 0.0170. E2 does show the highest Pre-onset Episode Recall (0.7000) and Episode Recall (0.7562) of any configuration and a marginally better Expected Calibration Error and Brier score, but it also has the highest Yellow Duty Cycle (0.4514) and lower Precision, and the higher false-positive rate at the operating point pulls its True Skill Score below Baseline. The primary endpoint, not the secondary episode metrics, governs the decision (`artifacts/sprint26a/GO_NO_GO_DECISION.md` logic; `artifacts/sprint25/04_success_criteria.md`).

> Exploratory result only. Sprint 26B confirmation required before scientific conclusions.

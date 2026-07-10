<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26A single-seed screening results (exploratory). -->
<!-- SUPERSEDED BY: Sprint 26B confirmation campaign (not yet run) -->
<!-- DATE: 2026-07-04 -->

# Sprint 26A — Screening Results (Single Seed, Exploratory)

> Exploratory result only. Requires confirmation in Sprint 26B.

**Conclusion:** Six of the seven pre-registered configurations were trained and evaluated on seed 42 through the frozen Sprint 24 evaluation framework this session; the seventh, E2 (uncapped steps per epoch), did not complete because its full-data epochs at the measured Metal Performance Shaders throughput exceeded the available compute window, so its metrics are `NOT PROVEN`. Among the six completed, no single-variable ablation exceeded the retrained Baseline on test True Skill Score: Baseline reached 0.3940, E3 (patience 8) produced the identical checkpoint (0.3940), E6 (Platt calibration) essentially tied at 0.3934 with a higher ROC-AUC, and E1, E4, and E5 fell below Baseline. Every value is labelled `OBSERVED` (measured this session) or `NOT PROVEN`.

## Runs in execution order

### Baseline — `OBSERVED`
Full protocol, seed 42. Checkpoint `artifacts/sprint26a/runs/Baseline/best.pt`.
- Best validation True Skill Score: 0.6053 at epoch 8 (frozen reference 0.5936). Early-stopped at epoch 11 (patience 3). Training time 38.2 minutes. Peak memory 0.014 GB (`torch.mps.current_allocated_memory`; see compute report caveat).
- Test policy metrics: True Skill Score 0.3940, ROC-AUC 0.7521, PR-AUC 0.4680, Expected Calibration Error 0.0685, Brier 0.1548 (`OBSERVED`, from `artifacts/sprint26a/runs/Baseline/eval.json`), Heidke Skill Score 0.3106, Matthews Correlation Coefficient 0.3349, Precision 0.3959, Recall 0.7300, Episode Recall 0.7301, Pre-onset Recall 0.6192, False Episodes per Month 3.395, Yellow Duty Cycle 0.4210.
- Training stability: validation True Skill Score trajectory 0.568 / 0.5705 / 0.5753 / 0.5677 / 0.5878 / 0.5839 / 0.5706 / 0.6053 / 0.5715 / 0.5708 / 0.5617 — mildly noisy, single clear peak at epoch 8. Loss decreased monotonically 0.0437 → 0.0320.

### E1 — regime-inclusive training data — `OBSERVED`
Training set = 2010–2019 plus 2020 through 2022-06-30 (6,468,471 windows, positive rate 1.02%); validation = 2022-07-01 through 2022-12-31 (261,600 windows, positive rate 11.38%); test unchanged. Split `artifacts/sprint26a/e1_split_meta.json`, no test leakage. Checkpoint `artifacts/sprint26a/runs/E1/best.pt`.
- Best validation True Skill Score: 0.4400 at epoch 1 (on the harder 2022-H2 validation set — not comparable to Baseline's validation set). Early-stopped at epoch 4. Training time 13.2 minutes.
- Test policy metrics: True Skill Score 0.3840, ROC-AUC 0.7514, PR-AUC 0.4792, Expected Calibration Error 0.0827, Brier 0.1479, Pre-onset Recall 0.6055, False Episodes per Month `see eval.json`, Yellow Duty Cycle 0.4142 (`OBSERVED`).
- Training stability: peaked immediately (epoch 1) then declined on the harder validation regime; loss decreased 0.0496 → 0.0415.

### E2 — uncapped steps per epoch (80,646) — `NOT PROVEN`
Defined in `artifacts/sprint25/03_experiment_matrix.csv`. Not completed this session: at the measured throughput (~16–20 optimizer steps per second under sustained thermal load), one uncapped epoch is ~70–84 minutes and the run would require an estimated 5–8 hours, which exceeded the session's compute window. No checkpoint, no evaluation, no metrics. All E2 values are `NOT PROVEN`. This is the single most important gap in the screening (see `05_SPRINT26A_SUMMARY.md`).

### E3 — early-stopping patience 8 — `OBSERVED`
Full protocol with patience 8. Checkpoint `artifacts/sprint26a/runs/E3/best.pt`.
- Best validation True Skill Score: 0.6053 at epoch 8 — **the identical checkpoint as Baseline** (patience 8 explored epochs 9–16 and found no better model; the epoch-8 peak was already global within the extended window). Early-stopped at epoch 16. Training time 63.9 minutes.
- Test policy metrics: True Skill Score 0.3940, ROC-AUC 0.7521, PR-AUC 0.4680, Expected Calibration Error 0.0685 — identical to Baseline, as expected from the identical checkpoint (`OBSERVED`).
- Training stability: same trajectory as Baseline through epoch 8, then 0.5715 / 0.5708 / 0.5617 / … / 0.5894 (epoch 14) / … without exceeding 0.6053.

### E4 — cosine annealing horizon T_max = 10 — `OBSERVED`
Full protocol with T_max = 10 (aligned to realized run length; baseline T_max = max_epochs = 20). This numeric value is a documented pre-registration interpretation of the descriptive matrix entry "T_max aligned to realized epochs." Checkpoint `artifacts/sprint26a/runs/E4/best.pt`.
- Best validation True Skill Score: 0.6003 at epoch 3 (converged faster than Baseline). Early-stopped at epoch 6. Training time 30.0 minutes.
- Test policy metrics: True Skill Score 0.3798, ROC-AUC 0.7504, PR-AUC 0.4780, Expected Calibration Error 0.0734, Pre-onset Recall 0.6466 (highest among completed runs), Yellow Duty Cycle 0.4307 (`OBSERVED`).
- Training stability: reached 0.6003 by epoch 3 (faster learning-rate decay), then declined; loss 0.0437 → 0.0352.

### E5 — Focal Loss alpha 0.50 — `OBSERVED` (from interrupted training)
Full protocol with alpha 0.50 (baseline 0.25). Training was **interrupted at epoch 4** when the session's long-running jobs were stopped; the best checkpoint saved to that point was epoch 3 (validation True Skill Score 0.58) and was evaluated. This is therefore a partial run: `NOT PROVEN` that the natural early-stopping checkpoint would differ. Checkpoint `artifacts/sprint26a/runs/E5/best.pt` (epoch 3).
- Test policy metrics (epoch-3 checkpoint): True Skill Score 0.3793, ROC-AUC 0.7506, PR-AUC 0.4674, Expected Calibration Error 0.0804, Pre-onset Recall 0.6466 (`OBSERVED` for this checkpoint).
- Training stability (epochs 1–4): 0.569 / 0.5745 / 0.58 / 0.5703; loss higher than Baseline (0.0542 → 0.0441) from the increased positive weighting, as expected. No prediction collapse observed.

### E6 — Platt scaling calibration — `OBSERVED`
Baseline checkpoint (training identical to Baseline; only the calibration family differs), Platt scaling instead of isotonic. Checkpoint `artifacts/sprint26a/runs/E6/best.pt` (= Baseline checkpoint).
- Test policy metrics: True Skill Score 0.3934, ROC-AUC 0.7559 (highest among all runs), PR-AUC 0.4907 (highest), Expected Calibration Error 0.0900 (worst — Platt is less well-calibrated here than isotonic), Pre-onset Recall 0.6479, Yellow Duty Cycle 0.4449 (`OBSERVED`).
- Training stability: not applicable (no training; calibration-only variant).

## Metrics not captured this session

- **MPS utilization and CPU utilization percentages:** `NOT PROVEN` — not instrumented this session. Wall-clock training time and `torch.mps.current_allocated_memory` peak were captured; percentage utilization was not.
- **Confidence intervals and significance:** the frozen Sprint 24 evaluator computes block-bootstrap intervals as a byproduct, but per the single-seed exploratory design of Sprint 26A they are **not used** for any screening conclusion and are not reported here as evidence.

> Exploratory result only. Requires confirmation in Sprint 26B.

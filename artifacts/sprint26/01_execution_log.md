<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26 execution log — faithful record of every run and the feasibility blocker. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 26 — Execution Log

**Status: PAUSED at a protocol-scope decision (pause condition 3).** Phase 1 passed cleanly and the training pipeline was built and validated to reproduce the frozen Version 1 baseline faithfully, but the measured training throughput on this machine (~256 seconds per epoch, versus the 4.6 seconds per epoch implied by the frozen `artifacts/training_history.json`) makes the full pre-registered campaign of 35 runs a 13-to-40-hour compute effort, and five-way parallelism thrashed on the external-SSD input/output. Reducing the campaign is forbidden by the frozen protocol, so how to proceed is a decision only the user can make. Every claim below is labelled `OBSERVED`, `INFERRED`, or `NOT PROVEN`.

## Phase 1 — Baseline verification: PASS

`OBSERVED` — All eleven fingerprints matched their Sprint 23 / `benchmark_manifest.json` records (`artifacts/sprint26/phase1_fingerprints.json`, this session): Version 3 Stage 2 and Stage 1 checkpoints, the Sprint 14c train/validation/test parquets, `app/services/ml/model_v3.py`, `artifacts/feature_columns_v3.json`, the deployed operator policy `operator_policy_v2.0.0` (nine startup provenance checks all PASS), the isotonic calibrator, the frozen Sprint 24 evaluation harness (`UnifiedEvaluator`, block length 2,880, seed 20260704), and the Version 1 reference checkpoint (epoch 3, best threshold 0.336667, 828,161 parameters). No mismatch; no hard stop triggered.

## Pipeline construction and validation

`OBSERVED` — A faithful parameterized training driver (`scripts/sprint26/train_driver.py`) was written that reuses the frozen `FocalLoss`, `PatchTST`, and dataset code unchanged and reimplements only the training loop, so the three variables the stock `app/services/ml/trainer.py` hardcodes — focal alpha (0.25), focal gamma (2.0), and cosine `T_max` (max_epochs) — become protocol parameters. This was necessary because ablations E4 (T_max) and E5 (alpha) cannot otherwise be run; it is not a protocol deviation but the vehicle for executing the protocol.

`OBSERVED` — First smoke run used `shuffle=False` for the validation loader and produced validation True Skill Score 0.0 at epochs 1 and 2. Root cause: the frozen trainer uses `shuffle=True` for validation (`app/services/ml/dataset.py:166-169` documents that shuffling distributes positive examples and `shuffle=False` is only for final ordered test evaluation); with a 2,000-batch cap and no shuffle, the driver evaluated only the earliest ~8% of the validation set. Fixed by matching the frozen behavior (`shuffle=True`).

`OBSERVED` — After the fix, a reduced-step diagnostic (800 steps per epoch, seed 42) reproduced the frozen baseline: validation True Skill Score 0.5767 at epoch 1 and 0.5907 by epoch 4, against the frozen 0.5667 at epoch 1 and 0.5936 best. `INFERRED` — the pipeline faithfully reproduces the frozen model; the earlier True Skill Score 0.0 was a validation-sampling bug, not a training defect.

## Phase 2 — Baseline reproduction (B0): PARTIAL

`OBSERVED` — Five-way parallel launch of B0 seeds 42–46 at full protocol (5,000 steps per epoch) produced no completed epoch in nine minutes; five processes each reading the 138 MB training parquet and building 289 MB feature arrays concurrently on the external "T7 Shield" SSD thrashed on input/output. The batch was terminated; no partial checkpoints were kept.

`OBSERVED` — One clean sequential B0 run (seed 42, `--num-workers 2`) at full protocol reproduced the frozen baseline: validation True Skill Score 0.568 (epoch 1), 0.5705 (epoch 2), 0.5753 (epoch 3), against the frozen 0.5667 / 0.4998 / 0.5936. Measured epoch time 255–259 seconds for 5,000 steps (~28 optimizer steps per second at batch 64). This run was still training at the time of this log (steadily improving, not yet early-stopped).

`OBSERVED` — Version 3 integrity was re-verified after the terminated batch: all frozen artifacts byte-identical (Stage 2 checkpoint, test parquet, `model_v3.py`, Version 1 checkpoint). Nothing was harmed.

## The feasibility blocker (evidence)

`OBSERVED` — Measured training throughput is ~256 seconds per epoch at 5,000 steps. `OBSERVED` — the frozen `artifacts/training_history.json` records 4.6 seconds per epoch. This is a ~55× discrepancy that the Sprint 25 compute budget (`artifacts/sprint25/05_compute_budget.md`, which estimated ~21 seconds per training run from the frozen log) did not anticipate.

`INFERRED` — At ~256 seconds per epoch and 4-to-6 early-stopped epochs plus ~120 seconds of data loading, one training run costs ~15–25 minutes; evaluation (validation inference, test inference over 1.8 million windows, calibration, and block bootstrap) adds ~5–7 minutes. The full campaign of 35 runs (7 configurations × 5 seeds) therefore costs an estimated 13–17 hours sequentially, and up to 40 hours if some configurations (notably E2, uncapped at 80,646 steps per epoch) run their full epoch budget. Five-way parallelism, the obvious mitigation, thrashed on external-SSD input/output (`OBSERVED` above).

`NOT PROVEN` — Whether a machine with faster local storage or a CUDA GPU would bring the campaign within a single-session budget; no such hardware was available this session.

## Why this is a scope decision, not a silent adjustment

The frozen Sprint 25 protocol states, and this sprint's brief re-states, that the campaign runs exactly as written: no deviation, no additions, no removals, all five seeds, all six ablations. The available responses to the throughput constraint — proceed over many hours or days, authorize a reduced protocol (fewer seeds, fewer steps, or fewer configurations), or move to faster hardware — all either deviate from the frozen protocol or require resources beyond this session. Choosing among them is a decision genuinely outside the protocol's scope, which the brief designates as pause condition 3 ("ask once and end the turn"). See `artifacts/sprint26/BLOCKER_REPORT.md`.

## Runs table

| Run | Config | Seed | Steps/epoch | Outcome | Evidence |
|-----|--------|------|-------------|---------|----------|
| smoke_B0_s42 (discarded) | B0, pre-fix | 42 | 5000 | validation True Skill Score 0.0 — validation-shuffle bug, fixed | `OBSERVED` |
| diag (discarded) | B0, post-fix | 42 | 800 | validation True Skill Score 0.5907 — reproduction confirmed | `OBSERVED` |
| B0 parallel ×5 (terminated) | B0 | 42–46 | 5000 | no epoch in 9 min — external-SSD input/output thrash | `OBSERVED` |
| B0_s42 | B0 | 42 | 5000 | reproducing (0.568/0.5705/0.5753), ~256 s/epoch, training at log time | `OBSERVED` |
| E1–E6 × 5 seeds | ablations | 42–46 | per matrix | NOT RUN — blocked on the scope decision | `NOT PROVEN` |

No run produced a scientific result that was discarded; the two discarded runs were a bugged pipeline test and a reduced-step diagnostic, both superseded, both logged here.

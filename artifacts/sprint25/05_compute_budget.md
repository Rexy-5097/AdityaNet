<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 compute budget derived from repository training and evaluation logs. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Compute Budget

**Conclusion:** The campaign is small — an estimated **7 to 10 hours of Metal Performance Shaders wall time**, dominated by evaluation (about 9 minutes per run) rather than training (frozen Version 1 trained in 21.3 seconds). Thirty-five training runs (five seeds × seven configurations) produce about 35 checkpoints and stay under 2 gigabytes of storage and 8 gigabytes of peak unified memory. Every figure below is derived from a repository log, not a general assumption; the anchor for a single-stage Version 1 retrain is `artifacts/training_history.json`, with the multi-stage Version 3 log (`artifacts/sprint14c/experiment.log`) cited as corroboration for the longer, uncapped case.

## Per-run training time (from `artifacts/training_history.json`, read this session)

The frozen Version 1 checkpoint trained in **21.3 seconds total** over 3 early-stopped epochs (epoch 1: 12.0 s, epoch 2: 4.6 s, epoch 3: 4.7 s), step-capped at 5,000 steps per epoch (`scripts/train_patchtst.py:223`) at batch 64. Steady-state is about 4.6 seconds per capped epoch ≈ 1,087 optimizer steps per second on the Apple M4 Metal Performance Shaders device (`artifacts/project_status/project_status.json`: mps_available true, cuda_available false).

| Configuration class | Per-seed training time | Basis |
|---------------------|------------------------|-------|
| Step-capped configs (B0, E1, E3, E4, E5, E6) | ~21 s (3-epoch early stop) to ~92 s (worst case 20 epochs × 4.6 s) | `artifacts/training_history.json` per-epoch times; E3 patience 8 may run more epochs |
| Uncapped config (E2, full 80,646 steps/epoch = 16× the cap) | ~74 s/epoch → ~6 min (early-stopped ~5 epochs) to ~25 min (worst case 20 epochs) | 16 × 4.6 s/epoch, extrapolated from the capped per-step rate |

E1 (regime-inclusive data, ~6.7 million training windows versus 5.16 million) keeps the 5,000-step cap, so its per-epoch time stays ≈ the baseline; only the sampled fraction of data changes, not the step count.

Corroboration from `artifacts/sprint14c/experiment.log`: the Version 3 Stage 2 fine-tune ran with many restarts between 00:07 and 15:59 on 2026-06-21 — consistent with uncapped multi-stage training being far longer than the capped single-stage Version 1 run, which is why Sprint 25 (single-stage Version 1) budgets from the Version 1 log, not the Version 3 log.

## Per-run evaluation time (from this session's Sprint 24 measurements)

| Step | Time | Basis |
|------|------|-------|
| Validation inference (1,568,399 windows) | 196 s | `artifacts/sprint24/val_inference_manifest.json` wall_seconds this session |
| Test inference (1,806,313 windows) | ~226 s | 196 s scaled by window count (1.806M / 1.568M) |
| Calibration fit + validation-only policy sweep | ~10 s | `scripts/calibrate_model.py`, numpy sweeps |
| Harness evaluation + block bootstrap (all metrics) | ~120 s | `artifacts/sprint24/results_abc.json` method C took 66 s incl. AUC bootstrap; full suite ~120 s |
| **Per-run evaluation subtotal** | **~9 minutes** | sum |

## Aggregate budget

| Quantity | Estimate | Derivation |
|----------|----------|------------|
| Number of training runs | 35 (5 seeds × 7 configs) | `03_experiment_matrix.csv` |
| Hard run ceiling | 40 (5 documented reruns) | `04_success_criteria.md` stopping rules |
| Total training time | ~1.3 hours | ~30 capped runs at ~60 s + 5 uncapped (E2) at ~10 min |
| Total evaluation time | ~5.3 hours | 35 runs × 9 min |
| **Total Metal Performance Shaders wall time** | **~7 hours (budget 10 hours with overhead)** | training + evaluation + overhead |
| Peak unified memory | ≤ 8 GB | Sprint 24 measured ≤ 8 GB at batch 512 inference; training batch 64 activations ~83 MB + 822k-parameter model |
| Storage — checkpoints | ~350 MB | 35 × 9.96 MB (frozen checkpoint size) |
| Storage — prediction arrays | ~470 MB | 35 × (validation 6.3 MB + test 7.2 MB float32) |
| Storage — logs, manifests, policies | < 100 MB | text/JSON |
| **Total storage** | **~1.0 GB (budget 2 GB)** | sum |
| Checkpoint count | ~35 best (+ up to 5 baseline "last") | one best checkpoint per run |
| Expected calendar duration | 2–3 days | ~7–10 h compute plus pre-registered analysis (`07_preregistered_analysis_plan.md`) |

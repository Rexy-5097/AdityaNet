<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Pre-implementation verification of the diagnostic against frozen pre-reg 48cbaad. -->
<!-- DATE: 2026-07-12 -->

# Verification Report — implementation vs frozen pre-registration 48cbaad

**Result: NO CONTRADICTION. All items CONFIRMED. The frozen spec is byte-identical to its committed state (SHA-256 `e140360c…`, verified `git cat-file 48cbaad:… == working copy`), and the implementation matches it.**

| Spec item | Frozen requirement | Implementation | Status |
|-----------|--------------------|----------------|--------|
| Hypotheses | H1 size, H2 regime, H3 reg, H4 exposure, H5 architecture, H6 ceiling, H7 base-rate | All 7 have arms/knobs in `train_driver_diag.py` + `run_battery.sh`; H5 conditional | CONFIRMED |
| H1/H2 separation | size-matched-V1 (786K, V1 regime) vs S2; low-base-rate-S2 removes base-rate confound | `--match-count 786298` on V1 (SMV1 ×3); `--base-rate 0.006` on S2 (SCR_baserate) | CONFIRMED |
| Arms — GOES track | full-V1 (reuse F1) + size-matched-V1 ×3 + S2-GOES 25/50/100 ×3 | F1 reused; SMV1_d42/43/44; S2G_f25/f5/f100 ×(42/43/44) | CONFIRMED |
| Arms — Aditya track | S2-Aditya 25/100 ×2 | S2A_f025/f10 ×(42/43) | CONFIRMED |
| Arms — screening | strong-reg, reduced-steps, natural-prior, low-base-rate (1 seed) | SCR_reg/steps/natural/baserate (seed 42) | CONFIRMED |
| Primary endpoint | peak validation ROC-AUC vs training-data fraction | driver selects/records peak val ROC-AUC; PRIMARY selection = val ROC-AUC | CONFIRMED |
| Minimum effect | +0.03 peak val ROC-AUC 25%→100%, monotone; grounded ~4σ of seed std 0.007 | analysis will apply this fixed threshold | CONFIRMED |
| Secondary endpoints | peak epoch vs fraction; train-vs-val ROC divergence; Δ under reg/steps/prior; ECE separation; test-tracks-val | all logged per epoch; test-tracks-val via multi-epoch test eval at analysis | CONFIRMED |
| Epoch outputs | train/val loss, train/val ROC-AUC, train/val PR-AUC, train/val TSS, Brier, ECE, reliability, confusion, pos/neg rate | all present in `history.json` (smoke-verified) | CONFIRMED |
| Threshold-independent primary | ROC-AUC/PR-AUC/Brier primary; TSS secondary | driver selects on val ROC-AUC (not TSS) | CONFIRMED |
| Seeds | 42/43/44 primary + size-matched draws; 42 screening | as specified in battery | CONFIRMED |
| Statistical test | 3-seed mean±std curves; frozen block bootstrap 2880/1000/200 seed 20260704 for test claims | analysis uses frozen harness unchanged | CONFIRMED |
| Epochs / patience | 15 / 8 | driver defaults 15 / 8 | CONFIRMED |
| Leakage | subsamples from train windows only; val/test untouched | window-index subset on TRAIN dataset only; val/test loaders separate | CONFIRMED |
| Reproducibility | subsample seed + index set hashed/saved | `train_indices.npy` + SHA-256 in run_meta | CONFIRMED |
| Failure/stopping | non-monotone→escalate; no param adjusted to results; no rerun | arms fixed at launch; decision rules fixed in spec | CONFIRMED |
| Frozen artifacts | V3/harness/v4-goes-final untouched | provenance baseline INTACT (V3 ckpt, s2_test, harness SHA all match) | CONFIRMED |

**Implementation refinement (traceable, not a deviation):** "training-data fraction" is implemented as a random subset of WINDOW indices (training examples), not rows — subsetting rows would corrupt the 360-minute windows. This faithfully realizes the spec's "subsamples draw from train windows only" (Datasets/Leakage section). Every window remains intact (reads 360 contiguous rows); only the count of training examples changes. The selected index set is seeded and hashed for exact reproducibility.

**No CONTRADICTION exists. Proceeding to execution.**

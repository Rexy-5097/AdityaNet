<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Diagnostic implementation decisions, each traced to a frozen pre-reg section. -->
<!-- DATE: 2026-07-12 -->

# Implementation Report — every decision traced to frozen pre-reg 48cbaad

Code committed **before** results. Battery: `scripts/sprint33_diag/run_battery.sh`; driver: `scripts/sprint33_diag/train_driver_diag.py`.

| Decision | Pre-reg section | Isolation / held constant |
|----------|-----------------|---------------------------|
| Window-index subsetting for data fractions | "Datasets/Leakage: subsamples draw from train windows only" | Only the count of training windows varies; each window intact; val/test untouched |
| `--match-count 786298` for size-matched-V1 | "Design — arms: size-matched-V1 (786K rows, 3 draws)" | V1 dataset, V1 features (17 GOES, identical list to S2), V1 scaling; only row/window count matched to S2 — regime differs by construction (the intended H1/H2 variable) |
| `--base-rate 0.006` low-base-rate-S2 | "H7 arm: low-base-rate-S2 downsample" | S2 regime + S2 features held; only positive-window prevalence lowered to V1's rate; negatives all kept |
| `--dropout 0.4 --weight-decay 1e-3` (SCR_reg) | "H3 arm: strong-reg" | Everything else at frozen protocol; only regularization changed |
| `--steps-per-epoch 1250` (SCR_steps) | "H4 arm: reduced-steps" | Only gradient steps/epoch changed |
| `--sampler-mode natural` (SCR_natural) | "H7 arm: natural-prior-sampler" | WeightedRandomSampler replaced by shuffle (natural 31% prior); nothing else changed |
| Reuse F1 as full-V1 baseline | "Design: reuse existing F1 (zero cost)" | F1 frozen artifact read-only; not retrained |
| PRIMARY model selection = validation ROC-AUC | "Endpoints: threshold-independent metrics are the primary decision criteria" | Checkpoint saved on best val ROC-AUC, not TSS |
| max_epochs 15 / patience 8 | "Shared: max_epochs 15, patience 8" | Raised from the 4-epoch truncation to observe the full curve |
| Full per-epoch metric suite | "Epoch-level outputs" | All 14 fields logged incl. train-side ranking metrics (overfitting shown, not assumed) |
| Frozen Sprint-24 harness for test scoring | "Statistics: frozen block bootstrap unchanged" | Harness SHA verified unchanged; used at analysis only |
| `num_workers=0` on the one-shot eval; guarded loaders | Systems review (prior MPS spawn-hang fix) | Determinism/repro |

**Not done (documented as unnecessary per constraints):** LSTM/TCN built upfront — deferred to a conditional single GRU arm per the spec ("H5 conditional; pre-weakened by V1-trains-fine evidence"). Building two net-new architectures speculatively for a hypothesis already weakened by OBSERVED evidence was excluded by the systems-validity review folded into the frozen spec.

**No experiment outside the pre-registration was introduced. No implementation decision was adjusted based on early results (the smoke run was discarded, not read for tuning).**

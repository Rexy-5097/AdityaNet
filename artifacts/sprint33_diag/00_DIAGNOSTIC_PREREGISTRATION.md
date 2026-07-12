<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Forecast Reliability Diagnostic — frozen pre-registration for the epoch-1-collapse causal experiment. Immutable on execution. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Forecast Reliability Diagnostic — FROZEN Pre-Registration

**Objective.** Determine the cause of the universal Stage-2 epoch-1 validation collapse (`OBSERVED`: on every S2-trained forecaster, training loss falls monotonically while validation ROC-AUC also falls monotonically — ADIF_s42 0.791→0.667, EMG_s42 0.828→0.730, F2_s42 0.783→0.688; the identical PatchTST does NOT collapse on the V1 span, F1_s42 val ROC-AUC ~0.87 flat, TSS rising to epoch 4), and thereby whether the S2 forecasting ceilings (Aditya-only ≈0.36 TSS, GOES ≈0.44) are genuine data-limited ceilings or artifacts — before any corrective modeling or the nowcaster.

## Hypotheses (7) with nulls and falsification paths

| H | Statement | Confirming observation | Rejecting observation | Arm |
|---|-----------|------------------------|-----------------------|-----|
| H1 | Dataset **size** (raw rows) insufficient | Peak val ROC-AUC rises ≥0.03 across S2 25→100%; size-matched-V1 collapses | Flat curve AND size-matched-V1 trains fine | S2 data-scaling + size-matched-V1 |
| H2 | Temporal **distribution shift** (S2 regime ≠ S1) | size-matched-V1 (786K, V1 regime) trains fine while S2 (786K) collapses | size-matched-V1 also collapses | **size-matched-V1 control** |
| H3 | **Under-regularization** | strong-reg (dropout 0.4, wd 1e-3) raises peak or delays peak epoch | no change vs baseline | strong-reg S2 |
| H4 | **Excessive steps/epoch** (320K samples ≈40% of S2/epoch) | reduced-steps (1250) delays peak epoch, peak ≥ baseline | peak epoch unchanged | reduced-steps S2 |
| H5 | **Architecture** cannot represent S2 | alt-architecture trains fine while PatchTST collapses on same S2 | alt-architecture also collapses | **conditional** GRU/LSTM (triggered only if H1–H4,H7 all null) — partially pre-rejected: same PatchTST succeeds on V1 `OBSERVED` |
| H6 | **True data ceiling** | NO arm raises peak val ROC-AUC | any arm raises peak | residual of all arms |
| H7 | **Base-rate / prior** (S2 31% vs V1 0.6%; sampler forces 50/50) | natural-prior sampler delays collapse; and/or low-base-rate-S2 downsample trains fine | both unchanged | natural-prior-sampler S2 + low-base-rate-S2 downsample |

Every hypothesis terminates in a concrete decision (see Decision Matrix). H1 and H2 are separated by the size-matched-V1 control (same size, different regime); the residual base-rate confound between them is removed by the low-base-rate-S2 downsample (same regime, V1 base rate), which stays inside the S2 distribution.

## Causal graph (each branch terminates in a decision)

- **H1 true** → more S2 data lifts the ceiling → *acquire/augment data; retrain forecasters at max data.* **H1 false** → size not the limiter → evaluate H2/H7.
- **H2 true** (size-matched-V1 fine, S2 collapses, low-base-rate-S2 still collapses) → SC25-max regime is intrinsically shift-limited → *regime-adaptation / domain-robust training; report a regime-conditioned operational ceiling (a deployment-critical finding: a model trained on solar-max won't generalize across cycle phase).* **H2 false** → not regime.
- **H3 true** → *adopt stronger regularization; retrain forecasters.* **false** → not regularization.
- **H4 true** → *rescale steps/epoch to dataset size; retrain.* **false** → not exposure.
- **H7 true** → *set sampler to natural prior / re-tune the imbalance handling; retrain.* **false** → not the prior.
- **H5 (conditional) true** → *switch base architecture.* **false** → architecture-independent.
- **H6 true** (all arms flat) → *0.36/0.44 are the real data-limited ceilings; STOP optimizing the forecaster; pivot effort to the nowcaster and publish the honest ceiling.* **false** → adopt the winning lever.

## Design — arms

Two feature tracks. **GOES track** (V1 has only GOES features → this track carries the H1/H2 size-vs-regime separation): reuse existing F1 as the full-V1 baseline (zero cost); **size-matched-V1** (random 786K-row V1 subsample, 3 independent draws); **S2-GOES** (EMG features) at 25/50/100% (3 seeds). **Aditya track** (the deliverable's ceiling): **S2-Aditya** at 25/100% (2 seeds). **S2 screening arms** (1 seed, 100% S2): strong-reg (H3), reduced-steps=1250 (H4), natural-prior-sampler (H7), low-base-rate-S2 downsample to 0.6% positive (H7/H2 separation). **Conditional** GRU arm (H5) runs only if all above null.

Shared: max_epochs 15, patience 8 (to observe the full curve, not truncate at 4); frozen Sprint-24 harness for all test scoring; everything else at the frozen protocol; one variable off baseline per arm.

## Epoch-level outputs (logged every epoch, every arm)

train loss, val loss, **train ROC-AUC, val ROC-AUC** (primary), **train PR-AUC, val PR-AUC** (primary), **Brier** (primary), train TSS, val TSS (secondary), ECE, reliability-diagram bins, confusion matrix, positive-prediction rate, negative-prediction rate. Train-side ranking metrics are mandatory so overfitting (train↑/val↓ divergence) is demonstrated, not assumed. **Threshold-independent metrics (ROC-AUC, PR-AUC, Brier) are the primary decision criteria; TSS/threshold metrics are secondary.**

## Endpoints, effect size, statistics

- **Primary endpoint:** peak validation ROC-AUC as a function of training-data fraction (the learning curve), per track. **Minimum effect to declare "data-limited":** peak val ROC-AUC rises ≥ **0.03** from 25%→100%, monotone. Justification (`DERIVED`): the measured S2 across-seed ROC-AUC std is ≈0.007 (feasibility ADIF 0.7506/0.7413/0.7547), so +0.03 ≈ 4σ — distinguishable from seed noise at 3 seeds; effects < 0.015 are explicitly **underpowered** (stated Type-II caveat: a null means "no large data effect," not "provably zero").
- **Primary-endpoint replication:** 3 seeds on the S2-GOES fractions and 3 independent draws for size-matched-V1 (bounds subsample-selection variance); screening arms single-seed.
- **Secondary endpoints:** peak epoch vs fraction; train-vs-val ROC-AUC divergence (overfit fingerprint); Δpeak and Δpeak-epoch under strong-reg / reduced-steps / natural-prior / low-base-rate; ECE-vs-performance separation; test-tracks-validation confirmation (evaluate ≥2 epoch checkpoints of the 100% arm on S2 test).
- **Statistical tests:** learning-curve shape at 3 seeds (mean ± std bands); any test-set quantitative claim uses the frozen moving-block bootstrap unchanged (2880-window blocks, 1000/200 reps, seed 20260704) — the only valid procedure for the 359/360-min-autocorrelated windows.

## Datasets, leakage, seeds, compute

- **Leakage:** data-fraction subsamples draw from **train windows only**; validation/test unchanged and untouched. size-matched-V1 draws from V1 train only. Each subsample written with a provenance manifest recording seed + selected indices → reproducible from scratch.
- **Seeds:** 42/43/44 (primary fractions + size-matched-V1 draws); 42 (screening). 
- **Compute (calibrated to measured ~3.25 min/epoch on 786K-row S2, ~13 min/4-epoch):** size-matched-V1 3×~49 min ≈ 2.5 h; S2-GOES 25/50/100 ×3 ≈ 4.3 h; S2-Aditya 25/100 ×2 ≈ 2.1 h; screening ×4 ≈ 2.7 h; total ≈ **11–12 h → two overnight MPS batches** (or one ~8 h night by trimming Aditya to 1 seed and dropping the 50% GOES point). Full-V1 baseline reuses F1 (0 h). LSTM/TCN deferred (net-new architecture engineering; H5 pre-weakened) → conditional, not in base budget.

## Quality gates, reproducibility, guardrails

Frozen harness SHA unchanged; V3 / Study-A / `v4-goes-final` artifacts fingerprint-verified pre and post (read-only); all diagnostic outputs isolated under `artifacts/sprint33_diag/`; subsample manifests; `num_workers=0` on eval loaders (the prior MPS spawn-hang fix); deterministic seeds; analysis script committed before results are read. New architecture code (if the conditional arm triggers) requires its own unit tests + parameter-budget check before use.

## Success / failure / decision rules

- **Success (of the diagnostic):** it maps to exactly one Decision-Matrix row — i.e. identifies the cause or confirms H6 — regardless of which cause wins. A clean H6 null is a successful, publishable result.
- **Failure (of the diagnostic):** non-monotone/incoherent curves across all arms fitting no row → escalate to a full optimization audit (log gradients/weights).
- **No parameter is adjusted in response to results.** Arms are fixed at launch; the decision rules are fixed here.

## Deliverables

Diagnostic report with per-epoch learning curves (train vs val, all primary metrics), the resolved hypothesis table (each moved to CONFIRMED / REJECTED with its evidence), the Study-A symmetry check, the Study-B ceiling determination, and the single mapped next experiment.

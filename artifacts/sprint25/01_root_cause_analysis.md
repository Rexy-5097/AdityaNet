<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 root-cause analysis, evidence-classified from repository artifacts only. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Root Cause Analysis

**Conclusion:** Of the sixteen hypotheses, exactly two are `SUPPORTED` by repository evidence (distribution shift, threshold instability), five are `PARTIALLY SUPPORTED` (class imbalance handling, calibration quality, learning-rate schedule, early stopping, and — as a structural fact only — training objective mismatch), seven are `NOT PROVEN` (loss design, optimizer, warmup, weight decay, regularization, seed variance, label quality), and two are `CONTRADICTED` as differential causes (window construction, episode construction). The two supported causes are both operating-point / distribution problems, not discrimination problems — which is why Sprint 25 proposes a training-procedure campaign rather than an architecture change.

## Part A — Sprint 24 findings: fact separated from interpretation

Every number below is from this session's computation (`artifacts/sprint24/results_abc.json`, `artifacts/sprint24/results_d.json`), reproduced through the frozen harness (`scripts/sprint24/eval_framework.py`); Step 1 fingerprint verification passed 18/18.

| # | FACT (what the data shows) | INTERPRETATION (not carried forward as fact) |
|---|----------------------------|----------------------------------------------|
| F1 | Method C (V1 + clean policy) window True Skill Score 0.3811 [0.3434, 0.4168] vs Method A (causal persistence) 0.3018 [0.2637, 0.3391]; paired ΔTrue Skill Score +0.0794 [0.0538, 0.1062], p ≈ 0.001, stable across block sizes 1,440/2,880/5,760 | The model has "real skill beyond persistence" — an interpretation of a modest, significant margin |
| F2 | Method C ROC-AUC 0.7482 [0.7309, 0.7669] vs Method A 0.6509 [0.6328, 0.6685], non-overlapping | "Discrimination is intact / the architecture works" — interpretation |
| F3 | Method C pre-onset episode recall 0.6041 [0.5575, 0.6548] vs Method A 0.3082 [0.2671, 0.3507], Δ +0.2959 | "The model genuinely anticipates flares" — interpretation |
| F4 | Heidke Skill Score: Method C 0.2989 vs Method A 0.3018, Δ −0.0029 [−0.0243, +0.0202], p = 0.82 | "Tie on Heidke Skill Score" — this is itself a fact (not significant); any claim of superiority here is unsupported |
| F5 | Window precision: Method C 0.3957 vs Method A 0.4638, Δ −0.0681 (significant, adverse) | "The model trades precision for recall" — interpretation |
| F6 | Method D (raw threshold 0.335, validation True Skill Score 0.5689) yields test True Skill Score 0.2150 [0.1804, 0.2512]; Method D − Method A ΔTrue Skill Score −0.0868 [−0.1296, −0.0451] | "Distribution shift causes the collapse" — interpretation; the measured fact is only that the validation-optimal threshold fails on test |
| F7 | Only the calibrated policy (Method C) clears persistence; the raw-threshold model (Method D) does not | "Calibration is load-bearing" — interpretation |
| F8 | Method C yellow duty cycle 0.4150 (594.6 alert-minutes/day); 376 alert episodes averaging 33.5 h; false episodes/month 3.43; 94 RED episodes (0.93% of windows) | "Operator-hostile duty cycle" — interpretation (`05_operator_analysis.md`) |
| F9 | Climatology (fixed probability 0.040710) never crosses the yellow threshold 0.14: True Skill Score 0.0000, ROC-AUC 0.5000, PR-AUC 0.2320 | No-skill floor — definitional, not interpretive |
| F10 | 730 label episodes over 41.42 months; framework reproducible (independent rerun byte-identical) | — |

**Not computed in Sprint 24 (so unavailable as a fact):** Expected Calibration Error was not among the harness metrics (the framework computed ROC-AUC, PR-AUC, True Skill Score, Heidke Skill Score, Matthews Correlation Coefficient, precision, recall/POD, F1, FAR, POFD, and the episode suite — not calibration error). Any Expected Calibration Error figure comes from a frozen Version 3 artifact, not this comparison.

## Part B — Hypothesis classification (repository evidence only)

| # | Hypothesis | Classification | Evidence |
|---|-----------|----------------|----------|
| H1 | Distribution shift between training and test solar cycles | **SUPPORTED** | Training positive rate 0.62% (Solar Cycle 24) vs test 23.20% (Solar Cycle 25) — `PROJECT_STATUS.md` dataset inventory, `artifacts/research_dataset_report.json`. The *effect* is measured: Method D's validation-optimal threshold (validation True Skill Score 0.5689) collapses to test True Skill Score 0.2150, below persistence (`artifacts/sprint24/results_d.json`, `06_statistical_tests.md`) |
| H2 | Class imbalance handling | **PARTIALLY SUPPORTED** | Handling exists and is known-sensitive: `app/services/ml/trainer.py:40-59,147-156` uses FocalLoss with alpha clamped to [0.25, 0.75] set to 0.25, plus a WeightedRandomSampler balancing to ~0.50 (`app/services/ml/dataset.py:136-140`); the trainer docstring records that an unclamped alpha=0.9938 caused all-positive collapse. Evidence that imbalance *matters*; no experiment shows current handling is a performance ceiling |
| H3 | Threshold instability across evaluation windows | **SUPPORTED** | Method D: the single validation-optimal raw threshold does not transfer to the test regime (`artifacts/sprint24/results_d.json`); block-bootstrap True Skill Score confidence-interval width ≈ 0.07 at the deployed operating point (`artifacts/sprint24/04_bootstrap_analysis.md`) |
| H4 | Probability calibration quality | **PARTIALLY SUPPORTED** | Calibrated Method C beats persistence while raw-threshold Method D does not (F7) — calibration matters for clearing the floor. But calibration *quality* (Expected Calibration Error, monthly stability) was not measured in Sprint 24; the only anchor is a frozen pooled figure in `artifacts/calibration/calibration_report.json`, not a Sprint 24 result |
| H5 | Training objective mismatch (differentiable loss ≠ selection metric) | **PARTIALLY SUPPORTED** (structural fact only) | Fact: training minimizes FocalLoss while checkpoint selection and early stopping use validation True Skill Score (`app/services/ml/trainer.py:155-156,237,272,285`). The mismatch exists; its causal contribution to the modest margin is untested — that part is NOT PROVEN |
| H6 | Loss function design (gamma, focal form) | **NOT PROVEN** | FocalLoss gamma=2.0 is fixed (`app/services/ml/trainer.py:54-56`); no ablation varies it; no evidence it limits performance |
| H7 | Optimizer choice | **NOT PROVEN** | AdamW is used (`app/services/ml/trainer.py:158-160`); no comparison to any alternative exists |
| H8 | Learning-rate schedule | **PARTIALLY SUPPORTED** | CosineAnnealingLR with T_max=max_epochs (default 20) — `app/services/ml/trainer.py:161-162`, `scripts/train_patchtst.py:220`. But training early-stopped at 3 epochs (`artifacts/training_history.json`: lr 1e-4 → 7.5e-5 → 2.5e-5), so the cosine cycle was configured for 20 epochs and only ~15% traversed — a real schedule/epoch-budget mismatch; performance impact not isolated |
| H9 | Warmup configuration | **NOT PROVEN** | No warmup scheduler exists in `app/services/ml/trainer.py`; absence is a fact but no evidence links it to the gap |
| H10 | Weight decay | **NOT PROVEN** | weight_decay=1e-4 fixed (`app/services/ml/trainer.py:114,158-160`); no sensitivity evidence |
| H11 | Early stopping criterion | **PARTIALLY SUPPORTED** | patience=3 on validation True Skill Score (`app/services/ml/trainer.py:112,272`); training stopped at 3 epochs with validation True Skill Score oscillating 0.5667 → 0.4998 → 0.5936 (`artifacts/training_history.json`) — a noisy signal under which patience=3 is fragile; that more epochs would help is NOT PROVEN |
| H12 | Regularization | **NOT PROVEN** | Dropout 0.2 (`PROJECT_STATUS.md` model inventory) and weight decay 1e-4 fixed; no ablation |
| H13 | Seed variance | **NOT PROVEN** | Only seed 42 exists (`artifacts/sprint14c/test_results_model_D_seed_42.json`; `artifacts/sprint23_5/VERSION3_LIMITATIONS.md` limitation on single-seed evidence). No variance data exists to classify — the definitive NOT PROVEN, and the reason multi-seed is in the protocol baseline |
| H14 | Window construction | **CONTRADICTED** (as a differential cause) | Sprint 24 Step 1 verified `labels.npy ≡ target_6hr_binary[360:]` by array equality this session; the 360-minute window equals the 6-hour forecast horizon by definition (`app/services/ml/config.py`). Construction is verified correct and identical across methods, so it cannot explain the model-vs-persistence gap |
| H15 | Label quality | **NOT PROVEN** | No label-audit artifact exists in the repository (`artifacts/sprint23_5/VERSION4_RESEARCH_PROGRAM.md` assumption A13 is UNVALIDATED) |
| H16 | Episode construction | **CONTRADICTED** (as a differential cause) | Episode construction is a measurement-layer choice applied identically to all four methods and unit-tested (`tests/test_eval_framework.py`, 10 passing); it cannot differentially cause the model's under- or over-performance versus persistence |

## Part C — What this implies for Sprint 25 scope

The two `SUPPORTED` causes (H1 distribution shift, H3 threshold instability) and the calibration-adjacent `PARTIALLY SUPPORTED` causes (H4, and the operating-point interactions in H8/H11) all sit in the training-distribution and operating-point layer, downstream of a discrimination capability that Sprint 24 showed is intact (F2). No `SUPPORTED` evidence implicates the architecture itself. This is the evidentiary basis for a controlled training-procedure campaign (Sprint 25) before any architecture redesign.

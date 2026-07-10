<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 pre-registered success criteria and binding stopping rules, locked before training. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Pre-Registered Success Criteria

**Conclusion:** The primary endpoint is a paired True Skill Score advantage over causal persistence of at least **+0.1062** (the current margin's upper 95% confidence bound), so any declared success is provably beyond the Sprint 24 margin's uncertainty rather than within its noise. Eight secondary endpoints are each pinned to the Sprint 24 Method C 95% upper confidence bound where one exists, and to "must not regress" where Sprint 24 did not measure the quantity. Two endpoints (Expected Calibration Error, Red Alert Utility) were not computed in Sprint 24; their baselines are therefore `NOT PROVEN` from Sprint 24 and are defined relative to the baseline B0 measured within this campaign. These targets are locked before any training run and cannot be relaxed after results are seen.

All Sprint 24 anchor values are from this session's `artifacts/sprint24/results_abc.json` and `artifacts/sprint24/results_d.json`.

## Primary endpoint

| Endpoint | Sprint 24 anchor | Minimum required for success | Justification |
|----------|------------------|------------------------------|---------------|
| Paired True Skill Score advantage over causal persistence | Method C − Method A = +0.0794, 95% CI [+0.0538, +0.1062] | Retrained model's paired ΔTrue Skill Score(model − persistence) **≥ +0.1062**, with the paired 95% confidence-interval lower bound **> +0.0538** | +0.1062 is the current margin's upper 95% bound; requiring the new point estimate to reach it, and the new lower bound to exceed the current lower bound, guarantees the improvement is statistically distinguishable from the Sprint 24 result, not aspirational |

## Secondary endpoints

| Endpoint | Sprint 24 Method C anchor (95% CI) | Minimum required | Justification |
|----------|-----------------------------------|------------------|---------------|
| Episode Recall | 0.7205 [0.6767, 0.7685] | ≥ 0.7685 | Current upper 95% bound |
| Pre-onset Episode Recall | 0.6041 [0.5575, 0.6548] | ≥ 0.6548 | Current upper 95% bound; the operationally decisive metric (`artifacts/sprint24/03_episode_metrics.md`) |
| ROC-AUC | 0.7482 [0.7309, 0.7669] | ≥ 0.7669 | Current upper 95% bound |
| PR-AUC | 0.4747 [0.4364, 0.5150] | ≥ 0.5150 | Current upper 95% bound |
| Expected Calibration Error | `NOT PROVEN` — not computed in Sprint 24 | ≤ baseline B0's Expected Calibration Error measured this campaign, on the Sprint 24 harness | Sprint 24 did not compute Expected Calibration Error; the only requirement definable without leakage is no regression versus the B0 baseline measured under identical conditions. The frozen pooled figure 0.0876 (`artifacts/calibration/calibration_report.json`) is a non-Sprint-24 reference, not a target |
| False Episodes per Month | 3.43 | ≤ 3.43 (must not regress) | Current Method C value; a specific lower achievable target is `NOT PROVEN` from Sprint 24 |
| Yellow Duty Cycle | 0.4150 | ≤ 0.4150 (must not regress); lower strongly preferred and reported | `artifacts/sprint24/05_operator_analysis.md` flagged 0.4150 as operator-hostile; no Sprint 24 evidence establishes a specific achievable lower floor → `NOT PROVEN` for a numeric improvement target |
| Red Alert Utility | `NOT PROVEN` — Sprint 24 counted 94 RED episodes but did not compute RED-tier precision | RED-tier episode precision ≥ YELLOW-tier episode precision (Method C 0.6223) | For the RED tier to be "useful" it must be at least as trustworthy as YELLOW; the YELLOW-tier episode precision 0.6223 is the only Sprint 24 anchor available |

## Definition of a successful configuration

A configuration counts as successful only if it meets the **primary endpoint** AND at least **five of the eight secondary endpoints**, and does so in **at least three of the five seeds**. A configuration meeting the primary endpoint in fewer than three seeds is reported as inconclusive, not successful.

## Stopping Rules (binding — cannot be relaxed after results are seen)

**Campaign-failure threshold.** If, after all registered runs complete, **no configuration** meets the primary endpoint (paired ΔTrue Skill Score over persistence ≥ +0.1062 with 95% lower bound > +0.0538) in at least three of five seeds, the training-improvement campaign is declared **FAILED**, and the recommendation escalates to architecture redesign (Decision Option C of `artifacts/sprint24/07_decision_report.md`). A margin that improves on Sprint 24 but does not reach +0.1062 is reported honestly as "insufficient improvement," not reclassified as success.

**Maximum number of runs.** Seven configurations (B0 plus E1 through E6) × five seeds = **35 training runs**. A hard ceiling of **40 runs** permits up to five documented reruns (for example, out-of-memory retries). **No configuration outside the pre-registered matrix (`03_experiment_matrix.csv`) may be added after any result is seen**, and no seed beyond the five registered may be added to a configuration to change its three-of-five outcome.

**Immediate-termination triggers.** Any one of the following halts the run (and, for c/e, the whole campaign) immediately:
- (a) **Prediction collapse** — a run producing all-positive or all-negative predictions (the alpha-sensitivity failure documented in `app/services/ml/trainer.py:8-11`). The run is logged as failed; the loss/alpha is **not** tuned mid-campaign to rescue it.
- (b) **Baseline reimplementation failure** — if B0's validation True Skill Score does not land within the frozen run's 0.5936 ± 2 seed standard deviations, halt and repair the pipeline before interpreting any ablation, because the discrepancy indicates a broken reimplementation rather than a scientific finding.
- (c) **Test-set access during selection** — any read of `artifacts/research/test.parquet` or the archived test prediction arrays during training, calibration, or threshold/policy selection is an integrity violation and halts the campaign.
- (d) **Reproducibility failure** — an identical seed producing non-identical results on rerun beyond the documented Metal Performance Shaders tolerance of 9.76e-4 (`scientific_validation_report.md` §3) halts the campaign pending investigation.
- (e) **Frozen Version 3 modification** — any detected change to a frozen Version 3 artifact (checkpoints, datasets, calibrator, policy) halts the campaign.

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 window-level baseline comparison, all numbers computed this session. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Window-Level Baseline Comparison

**Conclusion:** The V1 model with the Sprint 23 clean policy (Method C) beats causal persistence (Method A) on window-level True Skill Score by +0.0794 (0.3811 versus 0.3018), on ROC-AUC by a non-overlapping margin (0.7482 versus 0.6509), and on recall by +0.2439 — all statistically significant. It does **not** beat persistence on Heidke Skill Score (difference −0.0029, not significant) and is significantly **less** precise (0.3957 versus 0.4638). Climatology (Method B) is a no-skill floor. The validation-swept-threshold model (Method D) is the sprint's cautionary result: its raw threshold, optimal on validation (validation True Skill Score 0.5689), collapses to test True Skill Score 0.2150 — **below persistence** — demonstrating that operating-point transfer across the Solar Cycle 24→25 regime shift fails, and that only the calibrated policy rescues the model above the persistence floor.

Every number in this document was produced this session by `scripts/sprint24/run_evaluation_abc.py` and `scripts/sprint24/run_method_d.py`, recorded in `artifacts/sprint24/results_abc.json` and `artifacts/sprint24/results_d.json`, through the single `UnifiedEvaluator` class (`scripts/sprint24/eval_framework.py`). Test set: 1,806,313 windows; 730 label episodes; 41.42 months; test positive rate 0.2320; validation-era climatology rate 0.040710.

## Window-level metrics (all four methods, identical framework)

| Metric | A persistence (causal) | B climatology | C V1 + clean policy | D V1 + val-swept θ | A′ literal (non-causal) |
|--------|-----------------------:|--------------:|--------------------:|-------------------:|------------------------:|
| ROC-AUC | 0.6509 | 0.5000 | **0.7482** | 0.7485 | 0.9988 |
| PR-AUC | 0.3395 | 0.2320 | **0.4747** | 0.4950 | 0.9966 |
| True Skill Score (TSS) | 0.3018 | 0.0000 | **0.3811** | 0.2150 | 0.9975 |
| TSS 95% block-bootstrap CI | [0.2637, 0.3391] | [0, 0] | [0.3434, 0.4168] | [0.1804, 0.2512] | [0.9974, 0.9976] |
| Heidke Skill Score (HSS) | 0.3018 | 0.0000 | 0.2989 | 0.1182 | 0.9975 |
| Matthews Corr. Coef. (MCC) | 0.3018 | 0.0000 | 0.3265 | 0.2181 | 0.9975 |
| Precision | 0.4638 | 0.0000 | 0.3957 | 0.2813 | 0.9981 |
| Recall / POD | 0.4638 | 0.0000 | 0.7077 | 0.9422 | 0.9981 |
| F1 | 0.4638 | 0.0000 | 0.5076 | 0.4333 | 0.9981 |
| False Alarm Ratio (FAR) | 0.5362 | 0.0000 | 0.6043 | 0.7187 | 0.0019 |
| POFD | 0.1620 | 0.0000 | 0.3266 | 0.7272 | 0.0006 |

Confusion matrices (this session): A = {tp 194,394, fp 224,756, fn 224,756, tn 1,162,407}; C = {tp 296,637, fp 453,027, fn 122,513, tn 934,136}.

## Reading the table

- **C beats A on discrimination and skill, not on precision.** ROC-AUC 0.7482 [0.7309, 0.7669] versus 0.6509 [0.6328, 0.6685] — the confidence intervals do not overlap, so the model ranks flare risk materially better than "a flare just happened." The True Skill Score advantage (+0.0794) comes entirely from recall (+0.2439): C catches far more flare windows, at the cost of precision (−0.0681). This is a recall-for-precision trade, not a uniform dominance.

- **HSS is a genuine tie.** For persistence, TSS = HSS = MCC = 0.3018 exactly (a property of the symmetric confusion structure of a binary persistence predictor). C's HSS is 0.2989 — fractionally *below* persistence and not significantly different (see `06_statistical_tests.md`). Any claim that C beats persistence on Heidke Skill Score is **NOT PROVEN**.

- **B (climatology) never alerts.** Its fixed probability 0.040710 is below the yellow threshold 0.14, so under the deployed policy it emits zero alerts — the honest consequence of a constant-probability forecaster. Its ROC-AUC is 0.5000 (no ranking information) and PR-AUC 0.2320 (exactly the test positive rate, the no-skill line). B is the floor every other method must clear.

- **D is the distribution-shift casualty.** The threshold that maximizes validation True Skill Score (raw 0.335, validation TSS 0.5689) yields test True Skill Score 0.2150 — significantly *below* persistence's 0.3018 (paired delta −0.0868, CI [−0.1296, −0.0451]). At that raw threshold the model alarms on 77.7% of test windows because Solar Cycle 25 shifted the score distribution upward relative to the 2020–2022 validation era. This directly measures the Solar Cycle 24→25 threshold-transfer failure that the frozen documentation flagged qualitatively.

- **A′ (literal "last-window label") is non-causal and excluded from the verdict.** Defining the prediction as the previous window's label (parquet row i+359) uses information up to 359 minutes *after* the decision time; its near-perfect scores (True Skill Score 0.9975) are an artifact of that look-ahead, not skill. It is reported only to show why the causal persistence definition (Method A) is the correct baseline.

## Why Method A is the fair persistence baseline

With window i's label defined as the flare indicator over the 360 minutes following parquet row i+360, the *causal* persistence forecaster available at decision time is "did an M/X flare occur in the trailing 360 minutes," which equals `target_6hr_binary[row i]` — fully observable, no look-ahead. This is Method A (True Skill Score 0.3018). The literal reading of "last-window label" (Method A′) instead reaches forward across the horizon and is not a realizable forecaster; using it as the baseline would set an impossible 0.9975 bar and is therefore rejected with its reasoning recorded.

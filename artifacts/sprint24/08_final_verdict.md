<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 final verdict on whether AdityaNet beats persistence. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Final Verdict

## Scientific Questions Answered

1. **Does the V1 model beat causal persistence?** Yes on the operationally decisive metrics, with statistical significance under block bootstrap, but by a modest margin and not on every metric. Window True Skill Score 0.3811 versus 0.3018 (paired Δ +0.0794, 95% CI [+0.0538, +0.1062], p ≈ 0.001); ROC-AUC 0.7482 versus 0.6509 (non-overlapping intervals); episode recall 0.7205 versus 0.5575; pre-onset episode recall 0.6041 versus 0.3082 (Δ +0.2959). Computed this session in `artifacts/sprint24/results_abc.json`.
2. **Does it beat climatology?** Yes, trivially — climatology (fixed probability 0.040710) never crosses the alert threshold and is a pure no-skill floor (ROC-AUC 0.5000, True Skill Score 0.0000).
3. **Does the validation-optimal threshold transfer to the test regime?** No. The raw threshold maximizing validation True Skill Score (0.335, validation True Skill Score 0.5689) yields test True Skill Score 0.2150 — significantly *below* persistence (Δ −0.0868, CI [−0.1296, −0.0451]). This measures the Solar Cycle 24→25 operating-point transfer failure directly.
4. **Is calibration load-bearing for beating persistence?** Yes. Only the calibrated policy (Method C) clears the persistence floor; the raw-threshold model (Method D) does not.

## Questions Still Unanswered

1. **Is the +0.0794 True Skill Score margin the architecture's ceiling or a fixable procedure artifact?** NOT PROVEN — a single trained model at fixed operating points cannot decide it; resolved by the multi-seed, distribution-shift-aware retrain in the recommendation.
2. **Does the model beat persistence on Heidke Skill Score?** NOT PROVEN — Δ −0.0029, CI [−0.0243, +0.0202], p = 0.82 (a tie).
3. **What is the true deployed duty cycle with MC-Dropout suppression and RED confirmation active?** NOT computed this sprint — Method C used deterministic thresholds only, so its 41.5% alert time and 3.43 false episodes/month are upper bounds.
4. **Do SoLEXS/HEL1OS add value?** Out of scope this sprint; remains unproven per `artifacts/sprint23_5/VERSION3_OPEN_RESEARCH.md`.

## Does AdityaNet Beat Persistence?

**Yes — on True Skill Score, ROC-AUC discrimination, episode recall, and pre-onset (before-flare-onset) episode recall, all statistically significant under a block bootstrap that respects the autocorrelation of the data — but the margin is modest (+0.0794 True Skill Score, about 26% relative), it is a statistical tie on Heidke Skill Score, and the model is significantly less precise than persistence at the window level.** It is a real, directional, defensible advantage concentrated in recall and early warning, not a decisive one.

## Evidence

- Window True Skill Score: C 0.3811 [0.3434, 0.4168] vs A 0.3018 [0.2637, 0.3391]; paired Δ +0.0794 [+0.0538, +0.1062], p ≈ 0.001, stable across block lengths 1,440 / 2,880 / 5,760 windows (`04_bootstrap_analysis.md`).
- ROC-AUC: C 0.7482 [0.7309, 0.7669] vs A 0.6509 [0.6328, 0.6685] — non-overlapping.
- Pre-onset episode recall: C 0.6041 [0.5575, 0.6548] vs A 0.3082 [0.2671, 0.3507]; Δ +0.2959, p ≈ 0.001.
- Adverse findings: Heidke Skill Score Δ −0.0029 (not significant); window precision Δ −0.0681 (persistence better, significant); Method D window True Skill Score 0.2150 below persistence.
- Source files, this session: `artifacts/sprint24/results_abc.json`, `artifacts/sprint24/results_d.json`; framework `scripts/sprint24/eval_framework.py`; Step 1 fingerprint verification passed 18/18.

## Confidence Level

**High confidence** that V1 beats persistence on True Skill Score, ROC-AUC, and pre-onset episode recall: the paired advantage is significant, survives every block size, and the framework is reproducible (SHA256-identical reruns). **High confidence** that the advantage is *modest and partial* (Heidke tie, precision deficit). **Moderate confidence** on absolute operational figures, since MC-Dropout suppression and RED confirmation were not simulated (Method C values are bounds). The unresolved architecture-ceiling question is explicitly NOT PROVEN.

## Remaining Scientific Risks

1. The persistence-beating margin depends on the isotonic calibrator; if calibration degrades across regimes, the margin could vanish in live operation (Method D shows raw scores already fail to transfer).
2. Method C's operational figures are upper bounds; the suppression pipeline could reduce recall enough to narrow the persistence advantage — must be measured, not assumed.
3. The single-seed model may not be representative; the +0.0794 margin has no across-seed variance estimate.
4. Pre-onset recall's large lead-time means are partly inflated by long alert episodes (high duty cycle), not pure anticipation; the positive-lead fraction (0.84) is the more trustworthy figure.

## Recommended Sprint 25

**Distribution-shift-aware retraining of the existing PatchTST architecture (Decision Option C), evaluated through the frozen Sprint 24 harness.** Concretely: (1) retrain across multiple seeds to establish variance; (2) make training representative of the Solar Cycle 25 operating regime (regime-inclusive data or explicit domain adaptation) so operating points transfer — directly targeting the measured Method D failure; (3) select cost-sensitive operating points that produce short, sharp alert episodes rather than a 41.5% duty cycle, scored on episode-level pre-onset recall and alert duration; (4) compare every result against the persistence floor (True Skill Score 0.3018) and climatology floor (0.0000) established this session. Exit criterion: if the retrained model materially widens the pre-onset-recall and True Skill Score margins over persistence at a usable duty cycle, the architecture had headroom; if the margin does not move across seeds and procedures, escalate to Decision Option A (architecture redesign).

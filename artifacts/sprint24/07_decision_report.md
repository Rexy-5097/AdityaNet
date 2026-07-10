<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 decision recommendation, justified only by this session's computations. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Decision Report

**Recommendation: C — Retrain the existing architecture with an improved training procedure.** The measured failures are procedure and calibration failures, not discrimination failures: the model's ROC-AUC of 0.7482 [0.7309, 0.7669] beats persistence's 0.6509 [0.6328, 0.6685] with non-overlapping confidence intervals, so the PatchTST architecture demonstrably learns real predictive signal. What breaks is the conversion of that signal into an operating point — the validation-optimal raw threshold collapses from validation True Skill Score 0.5689 to test True Skill Score 0.2150 (below persistence), and the deployed policy alerts 41.5% of the time. Both are training-distribution and calibration problems. Redesigning the architecture (Option A) would discard a model that provably beats persistence to chase an unquantified hope, and no evidence in this sprint identifies the architecture as the bottleneck.

## Why not D (current architecture is sufficient)

Ruled out. The model beats persistence by only +0.0794 True Skill Score, ties on Heidke Skill Score (difference −0.0029, not significant — `06_statistical_tests.md`), is less precise than persistence at the window level, and its usable operating point holds the system in yellow alert 41.5% of the time while still missing 204 of 730 flare episodes (`05_operator_analysis.md`). A modest, partial edge over "assume persistence" with an operator-hostile duty cycle is not sufficient for the stated operational goal.

## Why not B (expand the Aditya-L1 dataset first)

Ruled out as the next step. This sprint evaluated GOES-only V1 against baselines and found it *does* beat persistence — the bottleneck it exposes is not "GOES is insufficient, add instruments," it is "the model's operating-point selection and calibration fail to transfer across the solar-cycle regime shift." Expanding the Aditya-L1 corpus addresses a different, already-documented question (the unproven multi-instrument benefit, frozen in `artifacts/sprint23_5/VERSION3_OPEN_RESEARCH.md`) and would not touch either measured failure. It remains a valid later phase, not the response to this sprint's evidence.

## Why not A (freeze V3 and redesign the architecture)

Ruled out *for now*, on evidence. The single strongest number in the sprint — ROC-AUC 0.7482 versus persistence 0.6509, non-overlapping — says the architecture discriminates well. Redesign is warranted only once an improved training procedure on the existing architecture has been shown to plateau; this sprint provides no such evidence. Escalation to A is the correct move *if* Option C fails to widen the margin (see ambiguity note).

## Why C, specifically

The two measured failure modes both point at training procedure and calibration, which is exactly what Option C changes:
1. **Operating-point transfer failure (measured).** Method D: raw threshold 0.335 is validation-optimal (validation True Skill Score 0.5689) but yields test True Skill Score 0.2150, significantly *below* persistence (paired ΔTSS −0.0868, CI [−0.1296, −0.0451]). The Solar Cycle 24→25 shift moves the score distribution; the model was trained on the 0.62%-positive SC24 regime and operated on the 23.20%-positive SC25 regime. Distribution-shift-aware training and calibration directly target this.
2. **Calibration is load-bearing (measured).** Only the calibrated policy (Method C, True Skill Score 0.3811) clears persistence; the raw-threshold model (Method D) does not. The margin above persistence currently *depends* on the isotonic calibrator — improving calibration and its regime transfer is the highest-leverage change, and it is a training-procedure concern, not an architecture concern.

Option C also produces the evidence that resolves the residual Option-A-versus-C ambiguity at low cost.

## Stated ambiguity and what would resolve it

The evidence does not *fully* separate C from A on one point: whether the modest +0.0794 True Skill Score margin over persistence is the PatchTST architecture's ceiling or a fixable training/operating-point artifact. This sprint cannot decide it because it evaluated a single trained model at fixed operating points. The resolving evidence is the first deliverable of Option C: (1) multi-seed retraining to establish variance (currently a single seed, per `artifacts/sprint14c/test_results_model_D_seed_42.json`); (2) a distribution-shift-aware retrain evaluated through the Sprint 24 harness against these same persistence and climatology baselines. If the margin over persistence — especially pre-onset episode recall and a usable duty cycle — materially widens, the architecture had headroom and C was right. If it does not move, the architecture is the ceiling and the project should escalate to A. Either way, Option C generates a decisive answer; Option A chosen now would not.

## What Option C must change (scope for Sprint 25)

- Train on data representative of the operating regime (incorporate Solar Cycle 25 conditions or apply explicit domain adaptation) so operating points transfer.
- Multi-seed for variance and reproducibility.
- Cost-sensitive operating-point selection producing shorter, sharper alert episodes rather than a 41.5% duty cycle — evaluated on episode-level pre-onset recall and alert-duration, not window True Skill Score alone.
- Every result measured through the frozen Sprint 24 harness against the persistence (0.3018) and climatology (0.0000) floors established this session.

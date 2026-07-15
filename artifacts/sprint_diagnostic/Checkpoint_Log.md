<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Scientific-direction checkpoints for the diagnostic sprint. -->
<!-- DATE: 2026-07-12 -->

# Checkpoint Log — Forecast Reliability Diagnostic

## Checkpoint 1 — implementation complete, battery launched (pre-results)

1. **Is this still testing the highest-value remaining uncertainty?** YES. The epoch-1 collapse / ceiling question (are Study A's 0.44 and Study B's 0.36 TSS real limits or training artifacts?) has been the project's #1 uncertainty across three successive review gates; nothing measured since has displaced it. `OBSERVED` basis: 17/17 S2 arms peak at validation epoch 1 with train-loss↓/val-ROC-AUC↓.
2. **Has any completed result changed the project direction?** NO. No diagnostic results exist yet (battery just launched; the smoke run was discarded unread). Direction unchanged.
3. **Has any assumption been invalidated by what was just measured?** NO. Provenance baseline INTACT (V3 checkpoint, s2_test, harness SHA all match); frozen spec byte-identical; no contradiction found. The window-index-subset refinement is a faithful realization of the spec, not an invalidation.
4. **Is there now a cheaper experiment that should replace the remaining implementation?** NO. The ROI review folded into the frozen spec already established this diagnostic as the cheapest experiment separating the seven hypotheses; the size-matched-V1 control is the minimal decisive addition. No cheaper alternative separates H1 from H2.
5. **Would Nature / NeurIPS / ISRO / FAANG Staff approve continuing from here?** YES. The experiment is pre-registered and frozen (48cbaad), the implementation is verified to match it item-by-item with no contradiction, provenance is intact, threshold-independent metrics are primary, and the design directly answers the strongest cross-panel criticism ("your ceilings come from one-epoch-overfit models").

**All five YES → CONTINUE.** Battery executing.

## Checkpoint 2 — all 20 arms trained (pre-analysis)

1. Highest-value uncertainty? YES — the ceiling question. 2. Direction changed? NO (results not yet analysed). 3. Assumption invalidated? NO. 4. Cheaper experiment? NO. 5. Panels approve continuing to evaluation? YES — all 20 arms exit 0, provenance intact. **All YES → CONTINUE to evaluation.**

## Checkpoint 3 — evaluation & analysis complete

1. **Highest-value uncertainty?** It WAS, and it is now answered (GENUINE LIMIT) — no residual uncertainty of higher value remains at the forecasting layer. 2. **Direction changed?** YES — the verdict redirects V4 from forecaster-training to nowcaster + cycle-diverse data accrual; this is the diagnostic's intended output, not a mid-experiment invalidation, so it does not trigger a STOP. 3. **Assumption invalidated?** YES — the implicit assumption that better training could lift the Aditya forecaster toward GOES parity is invalidated (genuine data-regime limit); again, this is the finding the experiment was designed to produce. 4. **Cheaper experiment?** NO — the diagnostic is complete and decisive. 5. **Panels approve?** YES — pre-registered, primary threshold-independent endpoint, decisive Cohen's d ≈ 15 regime effect, test-tracks-validation confirmed, provenance intact. **Experiment complete; verdict stands. No further code before a human direction decision on the redirect.**

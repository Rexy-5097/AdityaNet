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

## Checkpoint 2 — training complete (PENDING)
## Checkpoint 3 — evaluation complete (PENDING)

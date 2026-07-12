Aditya-L1 feature/fusion program CLOSED — NOT SUPPORTED

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 Phase 5 — decision tree resolution from the era-controlled measurements. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Decision Tree Update

**Resolution: every Aditya-L1 branch of `artifacts/sprint28/05_VERSION4_DECISION_TREE.md` is now resolved negative, and the branch that Sprint 31 provisionally activated (Path B) is falsified by the era-matched control. Path D is foreclosed (F3 does not beat F2); Path B's premise ("the value came from features") is refuted (F2 does not beat era-matched GOES-only); Path A was already foreclosed (Sprint 30). The measured Version 4 direction is a single-encoder GOES-only model retrained on the recent Stage-2 era (the EraMatchedGOES configuration) with the operator-decision-layer program continuing — a refined Path C, with the added, unexpected finding that the dominant lever is data recency, not architecture.**

## Branch-by-branch resolution (from Phase 4 measurements)

| Path | Pre-registered condition | Measured outcome | Status |
|------|--------------------------|------------------|--------|
| A | F1 > F0 (V1 span) AND F2 ≤ F1 | F1 did not beat F0 (Sprint 30, 0/5) | FORECLOSED (Sprint 30) |
| B | F2 > F1 on S2 | TRUE as stated (Sprint 31) — but the era-matched control shows F2's margin was era, not features: ΔTSS(F2−EraMatchedGOES) = −0.0388, and F2 (0.4022) < EraMatchedGOES (0.4383) | PREMISE FALSIFIED — features carry no positive value once era is controlled |
| D | F2 > F1 AND F3 > F2 | F3 ≤ F2: ΔTSS(F3−F2) = −0.0070, 0/5 significant, 0/5 meeting +0.02 | FORECLOSED — no cross-instrument temporal value; do not build cross-attention fusion |
| C | feature & instrument levers exhausted → architecture redesign + operator-decision-layer program | reached: Aditya features (F2), fusion (F3), and physics features (Sprint 30) all fail to beat GOES-only | ACTIVE, refined below |

## What this prescribes for Version 4

1. **Close the Aditya-L1 feature-engineering and fusion hypotheses.** The fair, physics-engineered, era-controlled test is complete: single-encoder Aditya (F2), late-fusion Aditya (F3), and GOES-physics features (Sprint 30 F1) each fail to beat era-matched GOES-only. No pre-registered Aditya branch remains open, and `02_FEATURE_PIPELINE_V4.md` lists no further Aditya feature mechanism with Sprint 27 evidentiary support. Aditya-L1 is retained as a monitored data stream, not a model input.
2. **Adopt the EraMatchedGOES direction for Version 4:** a single-encoder GOES-only PatchTST retrained on the recent Stage-2 era — the best-measured arm (TSS 0.4383, best ROC-AUC and PR-AUC, tightest seed variance), pending the adequately-powered confirmation named in `Operator_Report.md` (the S2 span's ~90 blocks leave its +0.0315 over F0 non-significant per-seed).
3. **Do NOT build the Path D cross-attention architecture.** Its precondition (F3 > F2) is measured false; cross-instrument temporal fusion has no empirical support here.
4. **Continue the operator-decision-layer program** (episode-level cost-loss policy under an explicit operator cost/loss ratio) against the EraMatchedGOES model — the RED tier remains dormant across all arms (Sprint 22 B2 bottleneck untouched by any feature/instrument/architecture work).

The unexpected, actionable discovery of the whole Version 4 campaign: the single largest measured lever is **data recency** (retrain GOES on the current solar cycle: +0.0315 TSS, consistent), not any instrument, feature, or fusion change — which all netted zero or negative.

FAILURE

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 6 — resolution of the first branch of the Version 4 decision tree. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — Decision Tree Update (first branch resolved)

**Verdict: FAILURE. F1 does not meet the primary endpoint.** The first-branch condition of `artifacts/sprint28/05_VERSION4_DECISION_TREE.md` — "F1 > F0 (paired ΔTSS ≥ +0.02, ≥2/3 seeds)" — is measured FALSE: 0 of 5 seeds (after mandatory escalation) meet the criterion; the mean paired ΔTrue Skill Score is −0.0311 ± 0.0276, significantly negative in 3 of 5 seeds and never significantly positive (full evidence: `artifacts/sprint30/Statistical_Analysis.md`, `artifacts/sprint30/analysis.json`).

## Which branch this triggers and what it prescribes

**Path A is foreclosed.** Path A ("Version 4 = single-encoder PatchTST on the 17 GOES-physics features") required F1 > F0; that condition is now measured false, so the cheapest hoped-for gain — physics-engineered GOES features on the proven pipeline — is not available at the window-TSS level under the fair pre-registered test. The tree's most-likely-branch assessment (Path A at ~40%) is refuted by measurement.

**The tree is not yet fully resolved — by its own structure.** The remaining live paths all depend on arms that have not run:
- **Path C** ("architecture-redesign program … alongside the operator-decision-layer program") requires "F1 ≤ F0 AND F2 ≤ F1". The first conjunct is now TRUE (measured); the second requires the F2 experiment (32 Version-4 inputs, concatenated single encoder, Stage-2 spans).
- **Path B** (F2's 32-feature architecture) and **Path D** (fusion) remain possible only if F2 > F1 on the S2 span.

**Prescription:** execute F2 (and, conditional on F2 > F1, F3) per `artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md`, evaluated same-span paired on the Stage-2 test period against F1-on-S2 and F0-on-S2, 3 seeds + the escalation rule. That is Sprint 31. If F2 ≤ F1 there, Path C becomes the measured Version 4 direction.

## What Sprint 31 should execute

"The Fair Test, Part 2": (1) rebuild the Stage-2-boundary splits through the Version 4 pipeline (`03_DATASET_PIPELINE_V4.md` §8, Aditya-instrument features per `02_FEATURE_PIPELINE_V4.md` rows 4–17, per-timestep masks as MODEL INPUTS for these arms per §3); (2) re-evaluate F0 and the existing F1 seed checkpoints on the S2 test span for same-span pairing (`F0.json:spans.test_s2_pairing`); (3) train and sealed-evaluate F2 at seeds 42/43/44 (+ escalation if the range exceeds 0.015); (4) resolve the F2-vs-F1 branch; (5) only if F2 > F1: proceed to F3.

## Constraints carried forward from this measurement

1. **No post-hoc substitution** (`F1.json:failure_criterion`): the FAILURE verdict on F1-vs-F0 full-span is final for this pre-registration; F1 may be re-examined only under a NEW pre-registration (for example, an episode-level operating point), never by re-analysis of this one.
2. **The secondary pre-onset signal is recorded, not promoted:** F1 improved pre-onset episode recall significantly in 5 of 5 seeds (+0.10 to +0.21) at a 5.4× false-episode cost. Under the pre-registered multiple-comparisons stance this cannot modify the verdict; it is legitimate INPUT to the Path C operator-decision-layer program (episode-level cost-loss policy), which the tree prescribes "regardless of model skill gains."
3. **Tie/conflict handling note:** the pre-registered tie rule (V1-span success but S2-span failure) is moot — F1 failed on the V1 span itself.

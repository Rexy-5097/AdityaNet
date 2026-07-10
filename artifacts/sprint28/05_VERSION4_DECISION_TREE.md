<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 Version 4 architecture decision tree keyed to fair-experiment outcomes. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Version 4 Decision Tree (Task 5)

**Most likely branch: Path A (physics-engineered GOES improves, Aditya does not), assessed at roughly 40% confidence — because the instrument-negative evidence, though generated under unfair conditions, points one way three times (conditional mutual information 0.0 given GOES history, `artifacts/aditya_l1/incremental_information_audit.json`; single-seed ablations null-to-negative, `scientific_validation_report.md` §6; selected HEL1OS lightcurves correlating up to 0.9996 with the soft X-ray reference, `artifacts/aditya_l1/cross_instrument_confirmation_audit.json`), while the GOES temperature/emission-measure inversion is untested physics with a genuine mechanism (preflare heating) on the proven pipeline.** Residual probabilities, stated for honesty: Path C roughly 35% (the Sprint 26 pattern of null results may repeat), Path B roughly 20%, Path D roughly 5%. These are judgments, not measurements — the experiment exists precisely because they are not knowable in advance.

Arm labels reference `04_FAIR_ADITYA_EXPERIMENT.md` (F0 GOES-14 baseline, F1 GOES-physics, F2 +Aditya features concatenated, F3 +Aditya via fusion).

```
IF F1 > F0 (paired ΔTSS ≥ +0.02, ≥2/3 seeds) AND F2 ≤ F1 on the S2 span
→ Path A — Version 4 = single-encoder PatchTST on the 17 GOES-physics features,
  frozen V1 architecture otherwise, plus the cost-loss episode-level operator
  policy; Aditya-L1 retained as a monitored data stream, not a model input.
  Rationale: capitalize on the one proven pipeline (16-year archive, measured
  38-minute training) and the cheapest validated gain; do not spend fusion
  complexity where the fair test found no instrument signal.
  Sprint 27 evidence for this branch: 04_SOLAR_PHYSICS_RECOMMENDATIONS.md G1
  (highest-priority untested physics needing no Aditya data) and
  03_GOES_VS_ADITYA_COMPARISON.md (no measurable independent instrument value).

IF F2 > F1 on the S2 span (paired ΔTSS ≥ +0.02, lower CI > 0, ≥2/3 seeds)
→ Path B — Version 4 = the 32-feature concatenated single-encoder architecture
  (F2's own architecture), with fusion adopted only under Path D's condition.
  Rationale: the value came from *features*, so ship the feature win in the
  simplest architecture that expressed it; avoid the encoder data-starvation
  defect (18 months of real Aditya gradients vs 16 GOES years).
  Sprint 27 evidence: 02_FEATURE_VALUE_ANALYSIS.md (UNKNOWN classifications —
  signal possible once inputs are fair) and 04 G2–G4 (the named physics that
  the raw columns never expressed); 01_ADITYA_FEATURE_AUDIT.md loss point 7
  (why separate branches are disfavored).

IF F1 ≤ F0 AND F2 ≤ F1 (neither improves)
→ Path C — Version 4 = architecture-redesign program per the standing Sprint 26
  escalation (artifacts/sprint26b/GO_NO_GO_DECISION.md), pursued alongside the
  operator-decision-layer program (functioning RED tier, duty-cycle reduction)
  which does not depend on model skill gains.
  Rationale: with training-procedure levers exhausted (Sprint 26) and feature/
  instrument levers exhausted (this experiment), architecture is the last
  unexplored model axis; the operator layer remains improvable regardless.
  Sprint 27 evidence: 07_VERSION4_REQUIREMENTS.md S1–S2 (operator-trust
  requirements independent of skill) and the campaign decision logic in
  06_EXPERIMENT_CAMPAIGN.md.

IF F2 > F1 AND F3 > F2 (instrument value present AND fusion adds on top)
→ Path D — Version 4 = token-level cross-attention fusion (GOES patch tokens
  attending to SoLEXS/HEL1OS patch tokens before pooling), the single
  alternative Sprint 27 justified against a named limitation.
  Rationale: only in this branch is there evidence that cross-instrument
  *temporal* structure (the Neupert integral kernel; the measured −5-minute
  HEL1OS lead) carries value the pooled-vector design cannot express.
  Sprint 27 evidence: 05_FUSION_LIMITATIONS.md limitation 1 and its named
  alternative; artifacts/aditya_l1/cross_instrument_confirmation_audit.json
  (median_best_offset −5.0 minutes).
```

**Branches deliberately absent:** an "uncertainty-aware fusion" branch (Sprint 27 assessed it premature until per-timestep masking lands — `05_FUSION_LIMITATIONS.md` alternatives table) and a "more instruments/magnetograms" branch (no data source exists — `04_SOLAR_PHYSICS_RECOMMENDATIONS.md` explicitly-not-recommended section). Per the brief, branches without Sprint 27 evidence do not appear.

**Tie and conflict handling (pre-registered):** if F1-versus-F0 succeeds on the V1 span but fails on the S2 span (regime-dependent gain), Path A still applies but the S2-span number is the one reported to operators (Solar Cycle 25 is the operating regime — the Sprint 24 Method D lesson, `artifacts/sprint24/results_d.json`). If F3 > F2 but F2 ≤ F1, that is *not* Path D — fusion gains without feature-level instrument value would indicate an architecture effect, to be treated as Path C evidence and re-tested on GOES-only inputs before any fusion claim.

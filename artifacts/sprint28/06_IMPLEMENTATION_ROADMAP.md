<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 Version 4 implementation roadmap calibrated to M4 MPS constraints. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Version 4 Implementation Roadmap (Task 6)

**Total estimated calendar time: 7 to 9 weeks from start of implementation, against the only deadline recorded in the repository — `PROJECT_CONFIG.yaml` `deadline: 2026-12-31`, roughly 25 weeks away — so the full plan fits with a wide margin. The specific hackathon submission date is `NOT PROVEN` (no artifact records it); if the hackathon falls earlier than about 8 weeks out, the cut line is drawn below: Sprints 29, 30, and 31 are non-negotiable, Sprint 32 is the first deferrable, and Sprints 33–34 are packaging that compresses to days if needed.** Compute figures are calibrated to the measured Apple M4 anchors (`artifacts/sprint26a/04_COMPUTE_REPORT.md`: 38.2-minute V1-scale training, ~10-minute evaluations, thermal drift lengthening later runs; V3-scale figures are flagged extrapolations).

## Sprint 29 — "Foundations and the GOES fair test" (1.5 weeks) — NON-NEGOTIABLE
- **Goal:** Version control and test substrate first (adversarial-review revision — see `07_EXTERNAL_REVIEW.md`, FAANG criticism): git initialization with remote, continuous-integration run of the existing 25-test suite, unit tests for the Version 4 feature builder; then implement the Version 4 feature pipeline (`02_FEATURE_PIPELINE_V4.md`) and dataset pipeline (`03_DATASET_PIPELINE_V4.md`) for the GOES family; run experiment arms F0-re-evaluation and F1 (3 seeds).
- **Compute:** ~4–5 hours Metal Performance Shaders (F1 ×3 at measured V1 scale + rebuilds + evaluations).
- **Risk:** temperature/emission-measure inversion correctness (mitigated by the pre-specified validation tests in `02_FEATURE_PIPELINE_V4.md` rows 1–3); scaler-leakage bugs (mitigated by train-only-fit gate in the dataset manifest).
- **Dependencies:** none. **Quality gates:** Sprint 23 provenance manifest on the new dataset; all feature validation tests green; AgentOS validator 100/100. **Exit criterion:** F1-versus-F0 paired result exists with 3 seeds — the first branch datum of the decision tree.

## Sprint 30 — "The Aditya fair test" (1.5 weeks) — NON-NEGOTIABLE
- **Goal:** Aditya-L1 engineered features (rows 4–17 of `02_FEATURE_PIPELINE_V4.md`), per-timestep availability channels (`03_DATASET_PIPELINE_V4.md` §3), Stage-2 dataset rebuild; run arms F2 (3 seeds) and F0/F1 S2-span re-evaluations; F3 if compute allows, else defer per the F-priority order.
- **Compute:** ~5–7 hours (F2 ×3 + rebuilds); +6–10 hours if F3 runs (extrapolated V3 scale — the CUDA-deferral candidate).
- **Risk:** the pre-registered failure outcome (no Aditya value) — which is a *result*, not a failure of the sprint; availability-stratification revealing regime artifacts.
- **Dependencies:** Sprint 29. **Quality gates:** pre-registration untouched since Sprint 28 (hash-pinned); same-span pairing rule enforced. **Exit criterion:** the decision tree resolves to exactly one path (`05_VERSION4_DECISION_TREE.md`).

## Sprint 31 — "Operator decision layer" (1.5 weeks) — NON-NEGOTIABLE
- **Goal:** the cost-loss, episode-level operator policy with a functioning RED tier and duty-cycle targets — the Sprint 22 Variant B program required by `artifacts/sprint27/07_VERSION4_REQUIREMENTS.md` S1–S2 and independent of which decision-tree path won.
- **Compute:** ~6–10 hours (validation Monte Carlo Dropout passes per the surviving Sprint 22 WP2 design; measured anchor 196 s per deterministic validation pass).
- **Risk:** the cost-loss frontier may offer no acceptable RED operating point (documented risk R4, `artifacts/sprint23_5/VERSION4_RISK_REGISTER.md`) — in which case the honest frontier is the deliverable.
- **Dependencies:** none on Sprint 30 (runs on whichever model is current); sequenced after it only to apply the policy to the winning model once. **Quality gates:** validation-only selection, provenance-gated policy v3, Sprint 24 harness. **Exit criterion:** deployed policy with episode-level operating point chosen from a published frontier; RED tier fires or its impossibility is quantified.

## Sprint 32 — "Chosen-path build" (2 weeks) — FIRST DEFERRABLE
- **Goal:** implement the winning decision-tree path at publication tier: 5 seeds, full evaluation, extended flare-bearing audit corpus (campaign prerequisite P0) for corroboration, ADR recording the architecture decision.
- **Compute:** ~10–20 hours depending on path (Path A cheapest at measured V1 scale; Path D most expensive, CUDA-preferred).
- **Risk:** Path C outcome makes this sprint an architecture-exploration sprint with genuinely uncertain payoff — the one branch where duration could grow.
- **Dependencies:** Sprints 29–31. **Quality gates:** requirement set M1–M5 in full. **Exit criterion:** Version 4 model + policy candidate passing every mandatory requirement, or an honest determination that Version 3 remains the shipping model.

## Sprint 33 — "Operational hardening" (1–2 weeks) — DEFERRABLE
Shadow-mode ingestion scheduler, monitoring per the walk-forward spec, dashboard skeleton, remaining test coverage. Evidence anchors: `artifacts/sprint23_5/VERSION3_DEPLOYMENT_BASELINE.md` absences. Deferrable because it improves deployment, not the scientific claim.

## Sprint 34 — "Submission package" (1 week; compressible to 2–3 days) — REQUIRED BUT LATE-BINDING
Honest evidence package: matched-baseline tables, pre-registration trail, provenance bundle, figures, reproduction instructions. Every number from frozen artifacts; the leakage-remediation and pre-registration story is itself submission material (`artifacts/sprint23_5/VERSION3_SCIENTIFIC_TIMELINE.md`).

## Cut lines if the hackathon date is early
- **≥ 8 weeks out:** full plan.
- **5–7 weeks:** defer Sprint 33 and Sprint 32's Path-dependent extras (5-seed tier → 3-seed with explicit caveat; P0 corpus in background).
- **≤ 4 weeks:** Sprints 29–31 + Sprint 34 only — submit the fair-test verdict, the operator decision layer, and the integrity story; explicitly do not claim a new model. This is stated now so the scope decision is never made under deadline pressure.

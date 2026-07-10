<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 adversarial review of the V4 plan from five reviewer perspectives. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Adversarial External Review (Task 7)

**Three criticisms resolved by specification revisions already incorporated into Tasks 2–6; two documented as unresolved. The unresolved concern carrying the most scientific risk is the DeepMind reviewer's statistical-power objection: the pre-registered minimum effect of +0.02 True Skill Score is asserted against a seed-noise band whose width has never been measured, so the fair experiment could return an honest but inconclusive answer.**

## Reviewer 1 — Google Research: cross-span incomparability
**Most critical flaw:** "Your instrument arms are trained and tested on a 6-month Solar Cycle 25 window while your baselines live on a 3.5-year span — any F2-versus-F1 comparison across different test distributions is meaningless, and your headline could be an artifact of the easier or harder span."
**Disposition: RESOLVED by revision.** `04_FAIR_ADITYA_EXPERIMENT.md` now carries the binding cross-span comparability rule: every Aditya-relevant comparison is computed same-span and paired on the Stage-2 test period, with F0 and F1 re-evaluated on that span, and the full-span F1-versus-F0 result reported separately; no conclusion may mix spans.

## Reviewer 2 — DeepMind: statistical power
**Most critical flaw:** "You pre-register a minimum effect of +0.02 True Skill Score and a 2-of-3-seeds rule, but you have never measured across-seed variance for any configuration — Sprint 26A ran one seed per arm and Sprint 26B one seed. If seed noise is ±0.02, your design cannot distinguish your minimum effect from nothing, and you will 'honestly' fail to detect real value or 'honestly' anoint noise."
**Disposition: UNRESOLVED — documented.** The concern is correct and cannot be argued away; it can only be measured away. Resolving evidence: the three F1 seeds of Sprint 29 provide the first across-seed True Skill Score spread on this pipeline; if the observed range exceeds ~0.015, the pre-registered protocol requires escalation to five seeds before any verdict (this contingency is hereby added to the pre-registration rather than left discretionary). Until that spread exists, the +0.02 threshold is an evidence-anchored guess (single anchor: the +0.0085 single-seed instrument gap, `scientific_validation_report.md` §6), not a powered design.

## Reviewer 3 — ISRO Mission Scientist: operational availability blindness
**Most critical flaw:** "SoLEXS was available 75.6% of the time in your own measurement; an operational forecaster that silently degrades one quarter of the time is not deployable, and your averaged metrics hide exactly that failure mode."
**Disposition: RESOLVED by revision.** `03_DATASET_PIPELINE_V4.md` §5 defines the per-window quality score, and `04_FAIR_ADITYA_EXPERIMENT.md` mandates availability-stratified reporting (quality ≥ 0.9 versus < 0.9) for every instrument arm, so downtime behavior is a first-class result rather than an averaged-away artifact. The deeper operational-requirements gap (what availability ISRO operations actually demands) remains external input the repository cannot supply — carried on the standing risk register (`artifacts/sprint23_5/VERSION4_RISK_REGISTER.md` R11).

## Reviewer 4 — NASA Space Weather Reviewer: no community benchmark
**Most critical flaw:** "Beating your own persistence and climatology floors is necessary but not sufficient; the space-weather community benchmarks flare forecasts against operational baselines such as NOAA Space Weather Prediction Center probabilistic forecasts, and none of your arms is scored against any external forecast."
**Disposition: UNRESOLVED — documented.** No Space Weather Prediction Center forecast archive exists anywhere in this repository (`NOT PROVEN` obtainable within current scope; no artifact records such data). Resolving evidence: acquiring the archived SWPC daily M/X-class probability forecasts for 2023–2026 and scoring them through the frozen Sprint 24 harness on the identical episodes — a data-acquisition task, estimated small once a source is identified, and the single highest-value addition for publication credibility. Until then, all claims are explicitly scoped as "relative to internal persistence and climatology floors."

## Reviewer 5 — Senior FAANG ML Staff Engineer: irreversible pipeline changes on an untested substrate
**Most critical flaw:** "You are about to rewrite the dataset pipeline — masks, imputation, normalization, feature engineering — in a repository with no version control, one external SSD that already survived one deletion incident, and test coverage limited to the policy layer; the first silent regression will cost you a week and possibly the baseline comparability your entire methodology depends on."
**Disposition: RESOLVED by revision.** `06_IMPLEMENTATION_ROADMAP.md` Sprint 29 now front-loads, as entry gates before any pipeline code: git initialization with a remote, continuous integration running the existing 25-test suite, and unit tests for every new feature builder (the validation tests are already specified per feature in `02_FEATURE_PIPELINE_V4.md`). Dataset outputs additionally carry Sprint 23-style provenance manifests (`03_DATASET_PIPELINE_V4.md` §7), making silent corruption a load-time failure.

## Unresolved Criticisms (consolidated)

| ID | Concern | Scientific risk | Evidence that would resolve it |
|----|---------|-----------------|--------------------------------|
| U1 | Statistical power unknown: minimum effect +0.02 asserted against unmeasured seed variance (DeepMind) | **Highest** — the fair test could be honestly inconclusive, stalling the decision tree | The Sprint 29 three-seed F1 spread; escalation to 5 seeds pre-registered if range > 0.015 |
| U2 | No external community benchmark (NASA) | High for publication, moderate for internal decisions — internal floors still support the V4 branch choice | SWPC probabilistic forecast archive for 2023–2026 scored on the frozen harness |

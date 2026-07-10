<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Complete specification of the recommended next sprint (Sprint 24), written at V4 planning. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — First Sprint Specification (Sprint 24: "The Honest Yardstick")

**Conclusion:** Sprint 24 builds the episode-level, block-bootstrap evaluation harness; scores V1, persistence, and climatology on it under identical conditions; derives the cost-loss frontier and a candidate RED-capable operator policy from validation data; and runs exactly one pre-registered honest test evaluation. It maximizes operator trust (restores the possibility of a working RED tier — problem P1) while minimizing scientific risk (no retraining, no new data, deterministic sweeps on arrays already on disk), and it simultaneously resolves the plan's existential question RQ1. Justification against the dependency graph: it clears root blockers RB1 and RB3 in one sprint because they share all machinery. Justification against the priority matrix: candidate C1 scores 8.70, 1.45 clear of second place, and the ranking is stable under reweighting.

## Objective

One yardstick, three forecasters on it, one operator frontier, one honest test run. At sprint end the project can state — with autocorrelation-honest intervals — whether its model beats trivial forecasting and what RED-tier trade-offs are actually available.

## Why this and not the alternatives (from the graph and matrix, not general principles)

The dependency graph (`VERSION4_DEPENDENCY_GRAPH.md`) shows RB1 blocking nine downstream problems and RB3 blocking every skill claim; no other single sprint clears two root blockers. The runner-up by matrix score, the walk-forward regime study (C3, 7.25), *consumes* this sprint's harness — doing it first is impossible. The Aditya-L1 corpus (C2, 6.75) is scientifically weightier but data-risky (risk R2) and operator-indirect; it is Phase B. Everything involving retraining scored ≤ 6.10 precisely because V3's history shows optimization against an unproven yardstick produces void claims (`artifacts/sprint22_5/FINAL_VERDICT.md`).

## Work packages, files, and changes

**WP1 — Episode harness module.**
- CREATE `app/services/ml/episodes.py`: `build_episodes(timestamps, labels, gap_minutes=60)` (contiguous positive-label grouping, formalizing the Sprint 5.6 method behind `artifacts/operator_backtest.json`); `alert_episodes(...)`; `episode_metrics(...)` (episode POD, episode FAR, false-episodes/month, lead-time distribution); `block_bootstrap(metric_fn, episodes, n=1000, seed)` resampling episodes, not windows. Stdlib+numpy only (testable without torch, mirroring `app/services/ml/policy.py`).
- CREATE `tests/test_episodes.py`: synthetic sequences with known episode structure — gap-boundary merging, lead-time correctness, degenerate cases (zero alerts, all-alert), bootstrap determinism under fixed seed. Target ≥ 15 cases.

**WP2 — Baseline forecasters on the yardstick.**
- CREATE `scripts/sprint24/baselines.py`: persistence (alert if any M/X flare within trailing k minutes; k swept on validation) and climatology (monthly base-rate probability) — both emitting per-window probabilities/alerts consumable by WP1. Regenerates baseline evidence reproducibly, replacing the NOT-PROVEN-provenance `artifacts/baseline_metrics.json` (which is left untouched as a historical artifact).

**WP3 — Validation arrays for policy derivation.**
- CREATE `scripts/sprint24/generate_policy_inputs.py` (per the surviving design in `artifacts/sprint22/Sprint22_Implementation_Plan.md` WP2): deterministic V1 pass over `artifacts/research/validation.parquet` (~2 h MPS) + MC-Dropout (50 passes) over the policy-active subset (calibrated probability ≥ 0.05; ~3–5 h). Outputs under `artifacts/sprint24/` with a provenance manifest (dataset SHA256 9c1b770f…, checkpoint hash, script hash, `test_data_used: false`) mirroring the Sprint 23 promotion-script pattern. **Source hygiene:** neither this script nor WP4's may contain the banned generator tokens enforced by `app/services/ml/policy.py`.

**WP4 — Cost-loss frontier and candidate policy v3.**
- CREATE `scripts/sprint24/optimize_policy_v3.py`: episode-level threshold sweep on calibrated validation outputs; cost-loss frontier for C_miss/C_fa ∈ {2, 5, 10, 20}; uncertainty-tier re-derivation with per-tier marginal-benefit test (tiers lacking positive episode-level benefit are dropped); component ablation (bare thresholds → +suppression → +RED confirmation → +coincidence filter). Emits `artifacts/sprint24/policy_frontier.json` and — after a recorded operating-point choice — `artifacts/policies/operator_policy_v3.json` through the full Sprint 23 provenance pipeline (13 fields, self-hash, leakage guard, startup validation). The operating-point choice is made by the project owner as operator-proxy and recorded as such (risk R11).

**WP5 — Pre-registered honest test evaluation (run once).**
- CREATE `scripts/sprint24/final_evaluation.py` with the protocol pre-registered in its header before execution: inputs are the frozen policy v3, archived test predictions `artifacts/calibration/probs.npy`/`labels.npy` (read-only, canonical per `scientific_validation_report.md` §3), WP2 baselines on the same test timestamps, and test-era MC-Dropout on the bounded active subset. Outputs `artifacts/sprint24/honest_test_report.json` + `Sprint24_Honest_Report.md` containing the matched table {V1+policy-v3, persistence, climatology} × {episode TSS, event recall, episode precision, false-episodes/month, lead-time distribution} with 95% block-bootstrap intervals. One run; any post-hoc parameter change voids the result and requires re-registration.

**WP6 — Production switch (conditional).**
- MODIFY `app/services/ml/inference.py` only if policy v3 passes all gates: single default-path change to the v3 policy file (the Sprint 23 loader needs no code change — schema-compatible). `operator_policy_v2.json` remains as rollback. Extend `tests/test_policy_system.py` with v3-boundary alert-decision cases.

## Expected artifacts

`app/services/ml/episodes.py` · `tests/test_episodes.py` · `scripts/sprint24/{baselines,generate_policy_inputs,optimize_policy_v3,final_evaluation}.py` · `artifacts/sprint24/{validation arrays + manifest, policy_frontier.json, baseline results, honest_test_report.json, Sprint24_Honest_Report.md, component_ablation.json}` · `artifacts/policies/operator_policy_v3.json` (conditional) · updated `context/state.md`.

## Quality gates

QG-004 (research validation): pre-registration verified; provenance manifests machine-checkable; zero test reads before WP5. QG-001/QG-002: episode-module tests green with output shown; policy-system regression suite (existing 15 tests) still green. QG-007 closure of P1 only if the chosen operating point yields a firing RED tier. AgentOS validator 100/100 at sprint end. **Stop rule:** if WP5 shows persistence within the model's CI band, WP6 does not execute a threshold-policy "upgrade" narrative — the sprint ships the honest table and triggers the RQ1 contingency decision instead.

## Success criteria

1. Matched episode-level table for three forecasters with block-bootstrap 95% CIs — published regardless of direction (this alone completes the sprint's scientific objective, RQ1).
2. Cost-loss frontier published; operating point chosen and recorded; every retained policy component shows positive marginal episode-level benefit.
3. RED tier fires at the chosen point (target: episode precision ≥ 0.5 at episode recall ≥ 0.5 *if the frontier permits*; otherwise the frontier is the honest deliverable and P1 closes as "quantified impossibility at 6 h").
4. All tests green with output; provenance gates pass; no V3 artifact modified.

## Estimated effort, compute, risk

One engineer, 1.5–2 weeks. Compute ≤ 10 h MPS total (WP3 dominates), ≤ 8 GB unified memory, ~300 MB new artifacts. Principal risk is an unwelcome RQ1 answer — which is a deliverable, not a failure (risk register R1).

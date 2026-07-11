<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 — Version 4 program status after the first fair-test result. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Version 4 Status Report — after Sprint 30

**Program position: the first of the two pre-registered fair-test questions is answered, negatively. GOES physics features (isothermal temperature, emission measure, 15-minute temperature derivative) through the Version 4 pipeline do NOT improve window-level True Skill Score over the frozen V1 baseline (0.3629 ± 0.0276 vs 0.3940, 0/5 seeds meeting the pre-registered criterion — verdict FAILURE, Path A foreclosed). The deployed operational system is unaffected: V1 with the clean Sprint 23 policy remains the production configuration, and its baseline superiority over persistence (Sprint 24) stands. The second question — Aditya-L1 instrument value under fair conditions (F2/F3 on the Stage-2 span) — is now the program's critical path.**

## What is now MEASURED (vs assumed)

| Question | Status | Evidence |
|----------|--------|----------|
| Do GOES physics features + V4 preprocessing beat frozen V1 on window TSS? | **NO (measured, 5 seeds, pre-registered)** | `Statistical_Analysis.md` |
| Does the preflare-heating signal exist in the archive? | YES (Sprint 29: 94% pre-peak T-rise over 77 X-events) — but it does not convert to window-TSS skill under this architecture/protocol | `artifacts/sprint29/goes_physics_validation.json` |
| Does it convert to anything? | Pre-onset episode recall +0.10..+0.21, significant 5/5 seeds, at 5.4× false episodes/month — secondary, hypothesis-generating only | `Statistical_Analysis.md` |
| Seed-noise band of the pipeline (U1, previously unmeasured) | TSS std 0.028, range 0.064 over 5 seeds | `Seed_Variance_Report.md` |
| V4 dataset pipeline correctness | Built + validated 15/15, tamper-detecting manifest | `Dataset_Validation_Report.md` |
| Frozen-baseline reproducibility through the whole V4 tooling chain | Exact (0.3940129618 vs 0.3940) | `Sprint30_F0_Report.md` |

## Version 4 asset inventory (all new this sprint)

`artifacts/research_v4/dataset_v4.0.0/` (3 splits, manifest, scaler params, feature provenance); `scripts/sprint30/{build_dataset_v4,train_driver,eval_run,analyze}.py`; five F1 seed checkpoints + sealed evals under `artifacts/sprint30/runs/`; the archived calibrated probability arrays enabling any future same-resample paired comparison against these runs.

## Open risks carried forward

1. **R5 analog for Sprint 31:** the S2-span rebuild must reproduce `artifacts/sprint14c/s2_*.parquet` boundaries exactly; same diff-before-training discipline as Phase 1 used here.
2. **Seed variance:** with a measured band of ±0.03, F2-vs-F1 deltas below ~0.02 per seed will again be undecidable without escalation; budget 5 seeds from the start.
3. **Validation-regime mismatch:** validation TSS ranked F1 above F0 in 5/5 seeds while test reversed it; any Sprint 31 selection step that leans harder on validation inherits this risk (mitigated by the frozen protocol's fixed selection rule).
4. **Physics-coefficient provenance (Sprint 29 R1)** — unchanged; irrelevant to relative comparisons, still open for any absolute-value publication claim.
5. **Episode-level operating point:** the recorded pre-onset gain is only actionable through a NEW pre-registration (episode-level cost-loss policy, Path C's parallel operator track); any attempt to reuse this sprint's data for that claim without new pre-registration is barred by `F1.json:failure_criterion`.

## Program schedule position

Sprint 28 roadmap: Sprint 29 (foundation) DONE → Sprint 30 (F0/F1, this sprint) DONE → **Sprint 31 = F2 (+F3 conditional), "The Fair Test, Part 2"** → decision-tree final resolution → Version 4 architecture decision. The program remains on the pre-registered rails; no re-planning is required by the negative result, because the decision tree explicitly anticipated it (Path C was assessed at 35% a priori).

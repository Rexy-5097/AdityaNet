<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 — Version 4 program status after the F2 experiment. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Version 4 Status Report — after Sprint 31

**Program position: both pre-registered fair-test questions now have first answers. Question 1 (GOES physics features, Sprint 30): NO — FAILURE, Path A foreclosed. Question 2 (Aditya-L1 features, this sprint): the pre-registered criterion PASSED (F2 > F1-on-S2, 3/5 seeds significant) activating Path B and mandating F3 — but the incremental-value-beyond-GOES claim is only PARTIALLY SUPPORTED, because F2 ties the GOES-only frozen baseline on the operating span and the arm design confounds instrument features with training-era match. Production remains V1 + the clean policy, still unbeaten at window level on every span tested.**

## The measured Version 4 map

| Question | Status | Evidence |
|----------|--------|----------|
| GOES physics features beat frozen V1 (V1 span)? | NO (Sprint 30, 0/5 seeds) | `artifacts/sprint30/Statistical_Analysis.md` |
| F2 (Aditya + physics, S2-trained) beats F1-on-S2? | YES (3/5 seeds significant, mean ΔTSS +0.0844) | `artifacts/sprint31/Statistical_Analysis.md` |
| F2 beats GOES-only F0 on S2? | NO (0/5 seeds, mean −0.0046) | same |
| F1 transfers to the S2 span? | NO — collapses to 0.288–0.345, at/below the 0.3368 persistence floor, significantly below F0 in 4/5 seeds | same |
| Recurring cross-arm signal | Instrument/physics arms consistently trade window TSS for large significant pre-onset episode recall gains at ~5–10× false-episode load (F1 on V1 span: +0.10..+0.21; F2 on S2: +0.39..+0.46 vs F0) | Sprints 30–31 analyses |
| Availability stratification | Degenerate — SoLEXS gaps are uniform micro-gaps; no low-quality stratum exists on S2 | `Missing_Data_Report.md`, `analysis.json` |
| Seed-noise band | Range 0.024–0.064 across all trained arms; escalation always triggered (twice, once at margin 0.0003) | `Seed_Variance_Report.md` (both sprints) |

## Version 4 asset inventory added this sprint

`app/services/ml/features_v4/aditya.py` (15 verified features); `artifacts/research_v4/dataset_v4.1.0-s2/` (3 splits + manifest + provenance + F1-projection side products); `scripts/sprint31/{build_dataset_v4_s2,train_driver,eval_s2,auto_escalate,analyze_s2}.py`; 5 F2 checkpoints + 11 sealed evaluation records with archived calibrated probabilities under `artifacts/sprint31/runs/`.

## Open items for the program

1. **F3 (mandated by Case A):** late-fusion architecture on the same inputs — the last pre-registered arm; resolves Path B vs Path D.
2. **Era-matched GOES-only control (new pre-registration required):** 17 GOES-physics features trained on the Stage-2 boundaries — the single experiment that de-confounds instrument information from training-era match, and the crux of the ISRO-submission claim (`Scientific_Conclusion.md` Q1).
3. **Episode-level cost-loss operator policy (new pre-registration):** the twice-replicated pre-onset-vs-false-alarm trade needs a C/L-ratio decision framework; independent of model-skill work.
4. Standing risks: 5-seed budgets by default (escalation has always triggered); the S2 span yields wide single-run CIs (~90 blocks); physics-coefficient absolute-value verification (Sprint 29 R1) still open for publication claims; F2's epoch-1 overfitting pattern suggests any future S2-trained arm has data-volume headroom as more Aditya-era data accrues.

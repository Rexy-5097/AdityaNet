# Sprint 22 — V4 Research Roadmap

**Conclusion:** The road to an operator-grade V4 runs in four phases: (1) make the decision layer honest — Sprint 22's selected work; (2) settle the Aditya-L1 question with an extended overlap corpus; (3) make the model regime-robust across the solar cycle; (4) attack the stealth-flare failure mode. Each phase gates the next: there is no point measuring (2)–(4) against a leaked yardstick, and no point building multi-instrument V4 architecture before (2) confirms the instruments carry signal.

---

## Phase 1 — Honest Decision Layer (SELECTED — Sprint 22/23)

**Scientific motivation:** The deployed alert policy was tuned on the test set (`scripts/optimize_operational_policy.py:6`) and delivers 3.97% episode recall (`artifacts/operator_readiness_report.json`). Every operator-facing number is invalid until the policy is re-derived leakage-free and evaluated once, honestly.

| Aspect | Plan |
|--------|------|
| Expected improvement | Episode recall from 3.97% to the 30–60% band available on the calibrated validation sweep (`refine_thresholds.py` yellow constraint recall ≥ 0.30 was satisfiable — its selected yellow point exists) at precision the cost-loss analysis deems acceptable; honest (unbiased) test metrics with episode-level bootstrap CIs |
| Risks | Honest numbers will be *worse* than currently published ones — must be communicated as a correction, not a regression; validation regime (2020–22, 4.07% pos) differs from SC25 test regime |
| Complexity | Low-medium: no retraining; inference passes + sweeps + policy code + tests |
| Validation methodology | Strict data separation manifest embedded in output artifact; single pre-registered test evaluation; window- AND episode-level metrics; block bootstrap over episodes (not windows) for CIs |
| Ablation plan | Policy ablations on validation only: thresholds alone vs +uncertainty suppression vs +RED confirmation vs +hard-X-ray coincidence filter — each component's marginal episode-level contribution |
| Success criteria | (a) zero test reads before final eval (machine-checkable manifest); (b) episode recall ≥ 30% at episode precision ≥ 50% on validation; (c) honest test TSS reported with block-bootstrap CI; (d) `inference.py` loads the new versioned policy file |
| Rollback | Old `operator_thresholds.json` archived, not deleted; policy file versioned; `inference.py` change is a one-line path swap |

Full design in `Sprint22_Selected_Improvement.md` and `Sprint22_Implementation_Plan.md`.

## Phase 2 — Settle the Aditya-L1 Question (Sprint 24)

**Scientific motivation:** The flagship claim (multi-instrument fusion helps) rests on a 4-day, zero-flare joint corpus (`artifacts/aditya_l1/overlap_dataset.parquet`) while ablations (`scientific_validation_report.md` §6: GOES-only 0.405 vs full 0.413) and conditional MI (`artifacts/aditya_l1/incremental_information_audit.json`: CMI=0.0) point toward a null result. Raw SoLEXS (915 files, Dec 2023→) and HEL1OS (960 files, Oct 2023→) parquets already exist under `data/aditya_l1/processed/` — the aligned corpus can be extended ~2.5 years backward without new downloads.

- **Expected improvement:** either a validated multi-instrument benefit on real joint flare windows (V4 justification) or a defensible null result (pivot to GOES-only V4 + Aditya-L1 as monitoring payload). Both outcomes are publishable; only limbo is not.
- **Risks:** alignment/gap-handling bugs manufacturing spurious signal; SC25 overlap era makes SoLEXS saturation during large flares plausible — needs a data-quality audit per event.
- **Complexity:** Medium. Dataset build (`scripts/build_multi_instrument_dataset.py` exists as a template), plus paired significance tests.
- **Validation:** paired bootstrap and McNemar on flare-episode windows only (`app/services/ml/metrics.py::paired_bootstrap_test`, `run_mcnemar_test` already implemented); pre-registered hypothesis and α.
- **Ablation:** V3 Scenarios A–D re-run on the extended corpus, flare-episodes-only stratum reported separately.
- **Success criteria:** ≥ 10 M/X flare episodes inside verified joint coverage; significance verdict either way.
- **Rollback:** none needed — read-only with respect to models.

## Phase 3 — Regime-Robust Model & Calibration (Sprint 25–26)

**Scientific motivation:** 0.62% → 23.2% positive-rate shift between train and test eras (`artifacts/research_dataset_report.json`). The calibrator is fit on 2020–2022 (4.07%); its transfer to solar maximum is unquantified.

- **Options ranked:** (a) rolling-origin recalibration (refit isotonic on trailing 6-month window; cheap, operational); (b) fine-tune V1 on 2020–2022+ data with SC24 pretraining (medium); (c) cycle-phase conditioning feature (F10.7 or sunspot number as covariate; research).  **Recommendation: (a) first** — it is the only one deployable without touching the frozen benchmark model.
- **Expected improvement:** ECE stability across regime boundaries; threshold portability (measured as episode-metric drift between validation halves).
- **Risks:** rolling recalibration on a live system needs governance (when does the calibrator update? who signs off?); fine-tuning risks catastrophic forgetting of SC24 quiet regimes.
- **Complexity:** (a) low, (b) medium (retraining), (c) medium.
- **Validation:** backtest rolling recalibration over 2023–2026 test era in walk-forward fashion — each test month scored by a calibrator that never saw it.
- **Ablation:** static-2020–22 calibrator vs rolling calibrator, same model, same thresholds.
- **Success criteria:** walk-forward ECE ≤ 0.10 every month of the test era (static calibrator currently achieves 0.088 pooled, but pooled hides monthly drift).
- **Rollback:** calibrator files versioned; policy pins a calibrator version.

## Phase 4 — Stealth-Flare Mitigation (Sprint 27+, research)

**Scientific motivation:** FNs come from quiet backgrounds (mean 3,489 min since last flare) with diffuse attention; the model leans on history features that are silent precisely when stealth flares occur (`artifacts/model_failure_evidence_report.md`; `artifacts/information_gap_report.json`).

- **Options ranked:** (a) add precursor-sensitive features — short/long channel ratio dynamics, quiet-sun baseline-relative flux (cheap, testable); (b) two-headed model with a quiet-regime specialist branch (medium); (c) if Phase 2 confirms signal, HEL1OS hard-X-ray impulsive precursors are the physically motivated stealth-flare channel (this is the *strongest scientific* reason to want Phase 2 first). **Recommendation: (a), gated on Phase 1–2 outcomes.**
- **Expected improvement:** recall on the stealth-flare FN stratum specifically; measured on the FN cohort defined in `artifacts/model_failure_evidence_report.md`.
- **Risks:** feature additions require full retraining + re-benchmarking; risk of trading stealth-FN recall for post-flare FP precision.
- **Complexity:** (a) medium (retrain V1), (b) high, (c) high.
- **Validation:** stratified evaluation — metrics reported separately for quiet-background vs active-background windows.
- **Ablation:** feature-set ablation identical in design to `artifacts/information_gap_report.json`.
- **Success criteria:** stealth-stratum episode recall improves with ≤ 2-point episode precision loss overall.
- **Rollback:** V1 checkpoint frozen; V4 candidate promoted only through the Phase-1 honest evaluation harness.

## Deliberately deferred (with reasons)

- **model_v3.py default fix (B7):** one-line change, folded into Phase 2's first commit; not a roadmap item.
- **Temperature-scaling forensics (B8):** isotonic is selected and working; forensics is curiosity, not blocker.
- **Engineering hardening (B10):** tests for the *policy layer* are inside Phase 1; broader auth/Docker/scheduler work is production engineering, sequenced after Phase 3 or run in parallel by a non-research track.
- **Determinism pinning (B11):** handled by convention (archived predictions are canonical; evaluation on pinned hardware), documented in Phase 1's evaluation protocol.

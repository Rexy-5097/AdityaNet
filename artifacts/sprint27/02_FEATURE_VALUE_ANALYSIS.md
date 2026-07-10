<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 27 per-feature value classification for all 22 Aditya-L1 model features. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 27 — Feature Value Analysis (Q2)

**Counts: HIGH CONFIDENCE USEFUL 0 · LIKELY USEFUL 0 · UNKNOWN 10 · LIKELY REDUNDANT 10 · REDUNDANT 2.** Zero of the twenty-two Aditya-L1 model features have any supporting evidence on the production M/X target — `artifacts/aditya_l1/target_relationship_audit.json` records median *and maximum* correlation and mutual information of exactly 0.0 against `target_6hr_binary` for every instrument feature group, because the aligned audit corpus contains zero M/X positives (a constant target correlates with nothing). Ten features are UNKNOWN (surrogate-task signal exists but conditional-on-GOES information is zero), and twelve are duplicates of other columns. The distribution says engineering effort should go first to **evidence generation** (a flare-bearing joint corpus) and second to **replacing raw duplicated channels with physics-engineered compressions** — not to fusion architecture, and not to per-channel tuning of columns that are copies of each other.

## Evidence base and its limits (read first)

- **Official-target evidence is empty, not negative:** all 2,109 raw features show 0.0 correlation/MI against `target_6hr_binary` (`target_relationship_audit.json`, `official_target_relationships`) — an arithmetic consequence of the 4-day, zero-M/X-flare audit corpus (`artifacts/aditya_l1/overlap_dataset.parquet`), not a measurement of uselessness.
- **All positive signal claims are surrogate-task claims** (C-flare surrogate; `target_relationship_audit.json` `surrogate_c_flare_relationships`; the ~65% positive rates visible in `lead_lag_relationship_audit.json`).
- **Model-level ablation evidence is single-seed** (`scientific_validation_report.md` §6, seed 42): GOES+SoLEXS True Skill Score 0.4003 *below* GOES-only 0.4046; GOES+HEL1OS 0.3793. Per the sprint's evidence standard, no `LIKELY` classification is upgraded on single-seed evidence, and none of these can support `HIGH CONFIDENCE` anything.
- Sprint 26A contains **no** instrument ablations (it was GOES-only training-procedure screening); the instrument evidence cited here is sprint14c/audit evidence.

## Per-feature classification

| Feature | Label | Evidence |
|---------|-------|----------|
| solexs_rate_ch1 … ch9 (9 features) | **UNKNOWN** ×9 | Conflicting: their compression `soft_band_mean` shows significant marginal delta-AUC +0.038–0.057 over a 5-feature GOES history baseline on the surrogate task (`incremental_information_audit.json`, p≈0.0099) **but conditional mutual information = 0.0 at every horizon (p=1.0)**; 26 of 340 raw SoLEXS spectra features rate "high quality" on stability-adjusted score, max 0.063 (`stability_adjusted_signal_audit.json`); adjacent raw channels correlate 0.95–0.99 (`solexs_channel_redundancy.json`) so the 9 aggregated rates likely carry 2–3 effective degrees of freedom (inter-channel r=0.78–0.80 among the aggregated rates, computed this session); zero M/X-target evidence exists |
| solexs_counts_ch1 … ch9 (9 features) | **LIKELY REDUNDANT** ×9 | Each correlates r=0.847–0.867 with its own rate twin on available Stage-2 validation rows (computed this session); physically counts ≈ rate × integration time, differing only through the mean-vs-sum resampling (`build_multi_instrument_dataset.py:49-50`) — the residual variance is exposure bookkeeping, not solar signal; `NOT PROVEN` that the residual carries flare information |
| hel1os_rate_band0 | **UNKNOWN** | The only HEL1OS column not duplicated by a sibling; surrogate-task lead correlations for HEL1OS bands are ~0.02–0.03 at all leads to 360 minutes (`lead_lag_relationship_audit.json`); selected HEL1OS lightcurve features reach max correlation 0.9996 with the cross-instrument reference at −5 minutes (`cross_instrument_confirmation_audit.json`) suggesting near-duplication of the soft X-ray curve; zero M/X-target evidence; band-to-raw mapping `NOT PROVEN` |
| hel1os_rate_band1 | **LIKELY REDUNDANT** | r=0.9911 with hel1os_rate_band0 (computed this session) — whatever band0 carries, band1 nearly duplicates |
| hel1os_counts_band0 | **REDUNDANT** | r=0.956 with hel1os_rate_band0 (computed this session) and same physical quantity under sum-vs-mean resampling — duplicate of a column already in the feature set |
| hel1os_counts_band1 | **REDUNDANT** | r=0.954 with hel1os_rate_band1, which itself correlates 0.9911 with band0 — triply duplicated |

## What the distribution implies

Twelve of twenty-two columns are duplicates and the remaining ten are unknowns whose only positive evidence is marginal, surrogate-task, and conditionally zero given GOES history. Two consequences follow. First, **no fusion or architecture work can be justified by these inputs as they stand** — the model is being asked to fuse ~3 effective signals dressed as 22 unnormalized columns. Second, the tractable engineering wins are cheap and prior to any training: deduplicate (drop counts twins and band1 copies), log-scale, and replace raw channels with the physics-derived ratios and dynamics recommended in `04_SOLAR_PHYSICS_RECOMMENDATIONS.md`; then generate the missing evidence (flare-bearing joint corpus) so classifications can move out of UNKNOWN in either direction.

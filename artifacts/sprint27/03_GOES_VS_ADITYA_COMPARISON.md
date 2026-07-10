<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 27 GOES vs Aditya-L1 information content comparison. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 27 — GOES versus Aditya-L1 Information Content (Q3)

**Plain statement: Aditya-L1 does not currently add measurable independent information to the production M/X forecasting task.** Three independent lines of repository evidence converge — and, just as importantly, each is weak in a different way, so the correct scientific reading is "no value demonstrated *and* no adequate test yet performed," not "value disproven."

## The three lines of evidence

1. **Official-target audit evidence is literally empty.** Against `target_6hr_binary`, every audited feature group — 2,109 raw features spanning HEL1OS CZT/CdTe lightcurves, spectra, events, housekeeping and SoLEXS spectra/lightcurve — records median and maximum correlation 0.0 and mutual information 0.0 (`artifacts/aditya_l1/target_relationship_audit.json`, `official_target_relationships`). This is the arithmetic of a constant target: the 4-day aligned audit corpus contains zero M/X events (`artifacts/aditya_l1/overlap_dataset.parquet`). Weakness: it measures nothing; it proves only that the evidence-generating corpus is inadequate.
2. **Surrogate-task conditional information is zero.** On the C-flare surrogate task, the strongest SoLEXS compression (`soft_band_mean`) adds delta-AUC +0.038 to +0.057 over a 5-feature GOES history baseline (significant, p≈0.0099) — but its **conditional mutual information given that GOES baseline is 0.0 at every horizon from 5 to 360 minutes (p=1.0)** (`artifacts/aditya_l1/incremental_information_audit.json`). The marginal signal exists; the *independent* signal, conditioned on what GOES history already provides, does not register. Weakness: 5,760 samples, surrogate target, single quiet-sun window.
3. **Model-level ablations show a null-to-negative single-seed picture.** On the Stage-2 test split (261,095 windows, 11.92% positive — this split *does* contain flares, unlike the audit corpus): full GOES+SoLEXS+HEL1OS True Skill Score 0.4131 vs GOES-only 0.4046 (+0.0085); GOES+SoLEXS 0.4003 (**adding SoLEXS decreased** skill vs GOES-only); GOES+HEL1OS 0.3793 (`scientific_validation_report.md` §6, seed 42). Weakness: one seed, no variance estimate, and the inputs audited in `01_ADITYA_FEATURE_AUDIT.md` were raw/duplicated/unnormalized — the test was unfair to the instruments. Note: Sprint 26A contains no instrument ablations (it screened GOES-only training-procedure changes), so these sprint14c ablations are the repository's only model-level instrument evidence.

## Signal accounting

| Signal | Captured by GOES? | Unique to SoLEXS? | Unique to HEL1OS? | Evidence |
|--------|-------------------|-------------------|-------------------|----------|
| Total soft X-ray flux level and dynamics | **Yes — dominant.** GOES history/engineered features carry nearly all model skill (removing them → True Skill Score 0.0) | Duplicated: SoLEXS soft channels track the same integrated SXR emission | Partly duplicated: selected HEL1OS lightcurve features correlate up to 0.9996 with the cross-instrument reference at −5 min offset | `artifacts/information_gap_report.json`; `artifacts/aditya_l1/cross_instrument_confirmation_audit.json` |
| Flare history / activity persistence | **Yes** (`minutes_since_last_flare`; history-only True Skill Score 0.371 ≈ full 0.382) | No Aditya history features exist to compare | Same | `artifacts/signal_audit_report.json`; `artifacts/feature_columns_v3.json` |
| Soft X-ray **spectral shape** (9-channel resolution vs GOES's 2 broad bands) | Only coarsely (2-band ratio never even computed as a feature) | **Candidate-unique** — but measured conditional contribution is 0.0 (line 2 above), and 9 aggregated channels inter-correlate 0.78–0.80 with adjacent raw channels at 0.95–0.99 | — | `incremental_information_audit.json`; `solexs_channel_redundancy.json`; this session's computations |
| Hard X-ray (>20 keV) non-thermal emission | Not directly (GOES XRS stops ~12 keV — physics claim, see `04_SOLAR_PHYSICS_RECOMMENDATIONS.md`) | — | **Candidate-unique** — but lead correlations to the surrogate target are ~0.02–0.03 at every lead (5–360 min), and the GOES+HEL1OS ablation is the worst configuration (0.3793) | `lead_lag_relationship_audit.json`; `scientific_validation_report.md` §6 |
| Intra-instrument duplication | — | 9 counts columns ≈ their 9 rate twins (r=0.85–0.87) | band1 ≈ band0 (r=0.9911); counts ≈ rates (r≈0.955) | computed this session on `s2_val.parquet` |

## The honest verdict and what would change it

The current pipeline gives no measurable independent Aditya-L1 information — but the repository has never run a fair test: the official-target audit had no positive events, the surrogate audit conditioned away the signal with 5,760 quiet-sun samples, and the model ablation fed the instruments raw duplicated unnormalized columns on one seed. The decisive experiment set is specified in `06_EXPERIMENT_CAMPAIGN.md`: physics-engineered, deduplicated, log-scaled Aditya features (per `04_SOLAR_PHYSICS_RECOMMENDATIONS.md`) versus GOES-only and versus GOES-plus-physics-features, multi-seed, on the flare-bearing Stage-2 splits, with an extended flare-bearing audit corpus rebuilt from the raw archive (`data/aditya_l1/processed/`: SoLEXS 915 files, HEL1OS 960 files, Oct/Dec 2023 → Jun 2026, spanning Solar Cycle 25 maximum).

<!-- VERSION STATUS: FROZEN UPON COMMIT -->
<!-- REASON: Pre-registration for Experiment E — Aditya-L1 Instrument Capability Ceiling. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-17 -->

# Pre-registration: Aditya-L1 Instrument Capability Ceiling (Experiment E)

**Status: FROZEN upon commit. After this commit, no hypothesis, threshold, inclusion rule, regression specification, interpretation boundary, or stopping rule may change. If a result lands between interpretation boundaries, the reported outcome is "Inconclusive" — the boundaries do not move. This experiment measures the physical information content of Aditya-L1 with respect to the GOES-defined C/M boundary; it is not designed to rescue or terminate the project, and the protocol below is valid regardless of which way the result falls.**

**Amendment r1 (2026-07-17, reporting only — applied before execution, before any data were examined).** This amendment changes *wording, organisation and reporting requirements only*. It changes no hypothesis, threshold, inclusion rule, regression specification, bootstrap, stopping rule, interpretation boundary, decision rule, or computation. The freeze in the paragraph above enumerates what may not change; reporting structure is not among them, so this amendment operates within the frozen contract rather than as an exception to it. Its three effects: (1) every section is now labelled with its epistemic class, separating direct physical measurement from bridge-derived inference (§14); (2) Outcome B's interpretation is scoped to the frozen calibration model, making the decision wording consistent with the scope note that §8 already carried; (3) a reporting manifest is frozen so that the same quantities are published for every outcome (§15). No result can change as a consequence.

No data distribution has been examined in designing this protocol. The only inputs to its design were: code inspection of frozen implementations (Experiment A availability rule, Experiment C episode functions), structural column-existence checks, and split date ranges. This mirrors the Experiment C design-integrity standard.

---

## 1. Primary scientific question

Can Aditya-L1 (SoLEXS + HEL1OS) physically resolve the GOES-defined C/M flare boundary sufficiently for **any** Aditya-only method to satisfy the operational deployment criterion (≤ 5.0 false episodes per month at ≥ 0.80 M/X episode recall, frozen from Sprint 33 / Experiment C)?

## 2. Hypotheses

- **H_data** — the instrument/data are the limiting factor: the calibration scatter between Aditya observables and GOES peak flux is too large for any flux-based class separator to meet the criterion.
- **H_objective** — the information exists in the data; the current learning objective fails to exploit it.
- **H_availability** — instrument availability (coverage gaps), rather than discrimination, limits operational recall.

## 3. Frozen inputs

1. Flare catalog `artifacts/research/flares_full.parquet` — SHA-256 **must equal** `536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a` (stopping rule 1 on mismatch). GOES peak flux is decoded from `flare_class` (Section 5.1); the catalog is the sole source of GOES ground truth.
2. Observables and availability: `artifacts/research_v4/dataset_v4.1.0-s2/{train,validation}.parquet` — columns `log_solexs_soft`, `solexs_HR_high_low`, `log_hel1os_band0`, `solexs_available`, `hel1os_available`. Analysis span = **train + validation only** (2023-12-13 → 2025-12-14). **The test span (post 2025-12-14) is never read.**
3. Frozen validation detector streams for the ceiling mapping: `artifacts/sprint33_nowcast/runs/s{42..46}/val_cal_probs.npy` + `operating_point.json`, with episode construction via the frozen `episodes` / `ep_class` / `mx_episode_recall` / `false_eps_per_month` functions of `artifacts/expC_class_separation/run_class_separation.py`, imported verbatim (audit precedent, 2026-07-17).
4. Consistency gate: `log_solexs_soft` on the validation split must be identical (max |Δ| ≤ 1e-9) between `dataset_v4.1.0-s2` and `dataset_adi_nowcast` (stopping rule 3 on failure — provenance investigation, no analysis).

## 4. What this experiment is NOT

No machine learning. No classifier fitting. No optimisation of the regression form. No threshold tuning against any outcome. No GOES quantity enters any detector at runtime — GOES flux is used strictly as the *measurement target* for instrument characterisation, which is legitimate because the project's M/X labels are already GOES-defined. A tight calibration does **not** license deploying GOES-calibrated outputs in the Aditya-only frame; that would be a separate pre-registered decision.

## 5. Primary Analysis A — SoLEXS→GOES calibration regression

**Epistemic class: OBJECT 1 — DIRECT PHYSICAL MEASUREMENT.** Every quantity produced here is measured from data and reported `OBSERVED`. It is conditional on the frozen predictor set, inclusion rule, OLS specification and bootstrap — and on no model of operational behaviour. These quantities remain valid and publishable even if every inference in §7–§8 is rejected. See §14, Layer 1.

### 5.1 Target
For every catalogued flare in the analysis span with class ∈ {B, C, M, X}: decode GOES peak flux F from `flare_class` (letter → decade: B = 1e-7, C = 1e-6, M = 1e-5, X = 1e-4 W/m²; multiplier from the numeric suffix, e.g. "M2.5" → 2.5e-5). Malformed strings are excluded and counted. Target y = log₁₀ F.

### 5.2 Predictors (frozen; exactly these three; no additions, deletions, or transformations)
Per flare, over the window **W(f) = [start_time − 15 min, peak_time + 15 min]** (peak_time missing → start_time), take the per-column **maximum** of:
1. `log_solexs_soft`
2. `solexs_HR_high_low`
3. `log_hel1os_band0`

### 5.3 Inclusion rule (frozen)
A flare is included iff: (a) W(f) intersects the analysis span; (b) mean `solexs_available` over W(f) ≥ 0.5 (the Experiment A artifact threshold, reused verbatim); (c) all three predictors are finite. Excluded counts are reported by reason.

### 5.4 Fit (frozen; executed exactly once)
Ordinary least squares, y ~ intercept + 3 predictors, single fit on all included flares. **Primary measurand: σ = standard deviation of the residuals, in dex.** Also reported: R², coefficients. If the design matrix is rank-deficient, STOP (stopping rule 4).

### 5.5 Uncertainty (frozen)
Cluster bootstrap: resample **calendar days** (UTC) with replacement, keeping all flares of a day together (flares cluster by active region; day-level resampling is the frozen compromise). 1,000 replicates, RNG seed **20260717**. σ_lo / σ_hi = 2.5th / 97.5th percentiles of the replicate σ distribution.

### 5.6 Sample-size stopping rule
If included flares number < 300 for class C or < 100 for M∪X, STOP (stopping rule 2): the calibration would be too weak to bound anything.

## 6. Primary Analysis B — Instrument availability audit

**Epistemic class: OBJECT 1 — DIRECT PHYSICAL MEASUREMENT.** The four fractions are counted directly from frozen columns and reported `OBSERVED`. The H_availability rule below is the sole inference in this section and is `LOGICALLY IMPLIED` from those counts alone — it depends on no bridge model. See §14, Layer 1.

Over all catalogued M/X flares in the analysis span (no availability filter), report the fraction with: (i) mean `solexs_available` over W(f) ≥ 0.5; (ii) mean `hel1os_available` ≥ 0.5; (iii) both; (iv) neither. Same four fractions for C flares, reported for context.

**Frozen H_availability rule:** H_availability is SUPPORTED iff the M/X SoLEXS-usable fraction (i) < 0.80 — no Aditya-only method could then reach the 0.80 recall floor regardless of discrimination. If (i) ≥ 0.80, H_availability is NOT SUPPORTED as a primary limit (residual availability effects remain a secondary).

## 7. Primary Analysis C — Implied operational ceiling

**Epistemic class: OBJECT 2 — DERIVED OPERATIONAL BRIDGE. Nothing in this section is measured.** FE_impl is the output of an idealised-estimator model applied to the measured σ. It is reported `HYPOTHESIS` and may never be quoted without the Layer-2 assumption list of §14. The computation below is unchanged by amendment r1.

Bridge from measured σ to the deployment criterion, computed per frozen rule with **no free choices after this commit**:

For each seed s ∈ {42, 43, 44, 45, 46}: reconstruct validation alert episodes at the frozen detector threshold; classify episodes by the frozen strict-intersection rule. Define:

- **C-population**: false alert episodes with class "C"; each carries F_i = max decoded GOES flux among its overlapping C flares.
- **Retained-other**: all false alert episodes with class ≠ "C" (genuine false, artifact, B/other-overlap, and decay-phase MX-labelled false). These are counted as **retained in full** at every cut — a conservative bias *against* H_objective, accepted because the audit cross-tab measured them small.
- **M/X-population**: detected M/X **label** episodes; each carries F_j = max decoded flux among its overlapping M/X catalog flares. Approximation (frozen): one keep-decision per label episode.

Idealised estimator model: log₁₀ F̂ = log₁₀ F + ε, ε ~ N(0, σ²) i.i.d. For a gate cut c (grid: −7.000 to −4.000, step 0.005 dex): expected kept fraction of episode i is P(F̂_i ≥ c) = 1 − Φ((c − log₁₀F_i)/σ).

- Expected gated recall(c) = (ungated validation M/X recall of seed s) × mean_j P(F̂_j ≥ c)
- Expected FE(c) = [retained-other count + Σ_i P(F̂_i ≥ c)] / validation months

**FE_impl(s, σ) = min over c of expected FE(c) subject to expected recall(c) ≥ 0.80.** If no c satisfies the constraint, FE_impl = +∞. **FE_impl(σ) = mean over the five seeds.** FE_impl is non-decreasing in σ; this is verified numerically as a self-check (Section 11).

## 8. Frozen interpretation thresholds — the decision rule

**Epistemic class: OBJECT 2 — OPERATIONAL INTERPRETATION.** Outcomes A/B/C are `LOGICALLY IMPLIED` *conditional on the §14 Layer-2 bridge assumptions*; Gate 0 alone rests on Layer-1 counts and carries no bridge dependence. Amendment r1 changes no numeric boundary and no recommendation in this section; it revises Outcome B's interpretation wording only, for consistency with the scope note this section already carried.

Evaluated in this order. After results are observed these MUST NOT change; intermediate results are reported "Inconclusive", never reinterpreted.

**Gate 0 (availability):** if H_availability is SUPPORTED (Section 6), the final decision is **"Instrument capability does not support further modelling"** regardless of Analyses A/C, because the recall floor is unreachable. Otherwise proceed:

- **Outcome A** — FE_impl(σ_hi) ≤ 5.0 (even the pessimistic 97.5th-percentile scatter permits the budget at the recall floor). Interpretation: evidence supports **H_objective**; a modelling programme remains scientifically justified. Recommendation: proceed to a fully powered five-seed class-aware retraining study (with a corrected, episode-class-aware model-selection criterion).
- **Outcome B** — FE_impl(σ_lo) > 5.0 (even the optimistic 2.5th-percentile scatter forbids the budget). Interpretation: evidence supports **H_data under the frozen calibration model** — that is, the instrument/data are the limiting factor for calibrations of the form specified in §5.2, which is what this experiment measures; the unrestricted claim "for any method" remains `HYPOTHESIS` per the scope note below. Further modelling on the current dataset is unlikely to change the operational conclusion. Recommendation (unchanged): conclude the modelling programme; frame the paper around the measured instrument capability and the operational limit.
- **Outcome C** — otherwise (the requirement lies inside the σ confidence band). Interpretation: evidence is insufficient to distinguish H_data from H_objective. Report explicitly as inconclusive; do NOT proceed automatically to retraining; design the next experiment using the measured uncertainty.

**Scope note, frozen now (self-audit honesty):** σ is measured for one frozen linear calibration on three peak-window observables. Outcome B therefore `LOGICALLY IMPLIED` rules out *calibrations of this form*; its extension to "any method" is `HYPOTHESIS`, physically motivated (peak flux, spectral hardness, and hard-X-ray output are the channels through which a peak-flux-defined boundary can be sensed) but not mathematically airtight — a temporal-shape estimator achieving materially smaller σ is not excluded by this measurement. The final report must carry this caveat verbatim; it does not soften the frozen decision rule.

## 9. Secondary analyses (exploratory; CANNOT change the primary conclusion)

Residual distribution and QQ-normality; heteroscedasticity (residual SD by target-flux quartile); class-dependent residuals (B/C/M/X); residual vs mean SoLEXS availability; residual vs time; HEL1OS-usable versus HEL1OS-missing subgroup σ; univariate SoLEXS-only σ (predictor 1 alone) for comparison; the implied maximum class-separation AUC at the measured σ (descriptive companion to the required-AUC ≈ 0.963 derivation of 2026-07-17); fraction of *missed* M/X validation label episodes (frozen streams) with SoLEXS availability < 0.5, as the availability-explanation check for the ~9% recall residual.

## 10. Forbidden

Tuning any threshold after seeing results; refitting or re-specifying the regression after observing scatter; redefining hypotheses; adding success criteria or weakening failure criteria; reading any test-span row; using GOES as runtime input to any detector; using sealed-test observations to design follow-ups.

## 11. Self-audit (mandatory before conclusions are presented)

1. Did any interpretation threshold change after analysis? If yes → the experiment is INVALID; report the invalidation, not the result.
2. Does any conclusion depend on a Section 9 analysis? If yes → label it EXPLORATORY explicitly; it cannot enter the decision.
3. Reproducibility: an independent reviewer with this document, the frozen inputs (Section 3 SHAs/paths), and seeds 20260717 (bootstrap) must be able to reproduce every number. Any non-reproducible step must be identified in the report.
4. Numerical check: FE_impl(σ) evaluated at σ_lo, σ̂, σ_hi must be non-decreasing; violation indicates an implementation bug → STOP and classify per the project's bug protocol.
5. Every reported statement labelled OBSERVED / LOGICALLY IMPLIED / HYPOTHESIS; the ε-normality bridge of Section 7 is HYPOTHESIS and must be labelled as such wherever the ceiling is quoted.

## 12. Stopping rules

1. Catalog SHA mismatch → STOP.
2. Included flares < 300 (C) or < 100 (M∪X) → STOP, insufficient sample.
3. Cross-dataset `log_solexs_soft` identity check fails on validation → STOP, provenance investigation.
4. Rank-deficient design matrix → STOP.
5. Self-audit check 4 fails → STOP, bug protocol.

## 13. Deliverables

`artifacts/expE_capability_ceiling/run_capability.py` (single script, executes this protocol verbatim), `capability.json` (all numbers), `Capability_Report.md` (verdict-first, one of exactly three outcomes: capability supports further modelling / does not support / inconclusive — no fourth option, no narrative blending).

**Frozen report structure (amendment r1).** `Capability_Report.md` must present the inferential chain in exactly this order, with these headings, so that measurement is never blended into interpretation: **1. Primary Physical Measurements** (§5–§6, Layer 1, all `OBSERVED`) → **2. Derived Operational Bridge** (§7, Layer 2, `HYPOTHESIS`, assumption list quoted in full) → **3. Operational Interpretation** (§8, Layer 3, `LOGICALLY IMPLIED` conditional on Layer 2) → **4. Decision** (Layer 4, one of exactly three). The verdict line appears first, before Section 1, per project convention. Section 1 must be readable and complete on its own: a reader who rejects the entire bridge must still obtain the full instrument characterisation from it.

---

## 14. The inferential chain (amendment r1 — reporting only; no computation changes)

This section adds no computation. It names, in advance, which reported quantity belongs to which epistemic layer, so that no reader — and no author — can silently promote a bridge-dependent number to a measurement.

**Layer 1 — Primary physical measurements (`OBSERVED`).** §5 and §6: σ, its 95% CI, R², intercept and three slopes, residual mean/SD/MAE/RMSE, the availability fractions, all sample counts. These are properties of the instrument and the catalog, conditional on the frozen predictor set, inclusion rule, OLS specification and bootstrap — and on nothing else. **They remain valid and publishable even if every inference below is rejected.**

**Layer 2 — The derived operational bridge (`HYPOTHESIS`).** §7. FE_impl is not measured; it is the output of an idealised-estimator model whose assumptions are frozen here and must be quoted wherever FE_impl appears:
 (i) residuals are Gaussian with constant σ (homoscedastic);
 (ii) estimator errors are independent across episodes;
 (iii) a real method achieves exactly the measured σ — no better, no worse;
 (iv) σ, measured on flare peak windows W(f), transfers unchanged to episode-level keep-decisions;
 (v) one keep-decision per M/X label episode;
 (vi) non-C false episodes are retained in full at every cut.
Assumption (vi) is conservative — it biases toward Outcome B. Assumption (iii) is the load-bearing one: it converts a *descriptive* scatter into a *prescriptive* ceiling.

**Declared limitation, frozen in advance (amendment r1).** The §5 fit spans B/C/M/X, but the operational question lives at the C/M boundary (10⁻⁵ W/m²). If residuals are heteroscedastic — plausibly worse for faint B-class flares near any SoLEXS noise floor — then σ̂ overstates the scatter *at the boundary*, FE_impl is overstated, and **the primary decision is biased toward Outcome B: toward wrongly terminating a viable direction.** This bias direction is declared now, before results, so that it cannot be invoked selectively afterwards. The §9 heteroscedasticity and class-dependent-residual analyses measure it but are exploratory and **cannot** change the primary outcome; if they contradict the primary, the report states both plainly and the primary governs. Narrowing the fit to a boundary-local flux range would be a change to the frozen regression specification and is **not** authorised by this amendment.

**Layer 3 — Operational interpretation (`LOGICALLY IMPLIED`, conditional on Layer 2).** §8's comparison of FE_impl against the 5.0 budget. Valid only insofar as Layer 2 holds.

**Layer 4 — Decision.** The frozen three-outcome rule. Unchanged.

**Declared asymmetry between Outcome A and Outcome B (amendment r1).** Outcome B carries a calibration-family scope caveat and Outcome A does not; this is deliberate, not an oversight. σ is measured for one restricted family. A *better* family would have *smaller* σ, which can only lower FE_impl. Therefore if this family already suffices (Outcome A), any better family also suffices — that conclusion is one-sided-safe with respect to family choice. If this family fails (Outcome B), a better family might not — that conclusion is family-dependent and must say so. Gate 0 (availability) carries neither caveat: it is decided on Layer-1 counts alone.

## 15. Frozen reporting manifest (amendment r1)

Every quantity below is reported in `capability.json` and `Capability_Report.md` **for every outcome, without exception**, whether or not it flatters the project. No additional *primary* metric may be introduced after results are known; these are frozen before any data are examined.

| Layer | Quantity | Note |
|---|---|---|
| 1 `OBSERVED` | σ (dex) | primary measurand; **identical to** "residual standard deviation" — one quantity, not two |
| 1 `OBSERVED` | σ_lo, σ_hi | 95% CI; day-cluster bootstrap, 1,000 reps, seed 20260717 |
| 1 `OBSERVED` | R² | |
| 1 `OBSERVED` | intercept β₀ | |
| 1 `OBSERVED` | calibration slope β₁ | on `log_solexs_soft` — "the calibration slope" in the physical sense (dex GOES per dex SoLEXS) |
| 1 `OBSERVED` | slopes β₂, β₃ | on `solexs_HR_high_low`, `log_hel1os_band0`; reported alongside β₁ because the frozen spec is 3-predictor, not univariate |
| 1 `OBSERVED` | residual mean | OLS forces ≈ 0; reported as an implementation check |
| 1 `OBSERVED` | residual MAE, RMSE | |
| 1 `OBSERVED` | availability fractions | M/X: SoLEXS-usable, HEL1OS-usable, both, neither; the same four for C |
| 1 `OBSERVED` | sample counts | included; excluded by reason; per class B/C/M/X |
| 2 `HYPOTHESIS` | FE_impl(σ̂) | quoted only with the Layer-2 assumption list |
| 2 `HYPOTHESIS` | FE_impl(σ_lo) | decides Outcome B |
| 2 `HYPOTHESIS` | FE_impl(σ_hi) | decides Outcome A |
| 3 / 4 | Outcome (A/B/C); final decision | one of exactly three; no fourth option |

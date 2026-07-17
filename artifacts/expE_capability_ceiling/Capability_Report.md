<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Experiment E results — Instrument Capability Ceiling per frozen prereg 58fe865 + r1 b9c8e7a. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-17 -->

# Experiment E — Aditya-L1 Instrument Capability Ceiling: Report

**Verdict by the frozen decision rule: OUTCOME B — instrument capability does not support further modelling, *under the frozen calibration model*. FE_impl(σ_lo) = 29.24 > 5.0; even the optimistic 2.5th-percentile scatter forbids the budget. Per the frozen scope note, this rules out calibrations of the §5.2 form; the extension to "any method" was pre-registered as `HYPOTHESIS` — and the exploratory layer, stated plainly below as the frozen §14 rule requires, shows that extension is not merely unproven but empirically CONTRADICTED by the completed record: the frozen detector itself already exceeds this bridge's implied ceiling. The primary governs the frozen decision; the contradiction governs what the decision may be taken to mean.**

Executed per `00_PREREGISTRATION.md` (commit `58fe865`, tag `expE-prereg`; reporting amendment r1 `b9c8e7a`). Catalog SHA verified; cross-dataset provenance gate passed (max |Δ| ≤ 1e-9); sealed test span never read; all five stopping rules cleared; FE_impl monotonicity check passed (29.24 ≤ 29.80 ≤ 30.34).

---

## 1. Primary Physical Measurements (Layer 1 — all `OBSERVED`)

### 1.1 Calibration regression (frozen §5 spec: OLS, 3 predictors, single fit)

| Quantity | Value |
|---|---|
| σ (residual SD) | **0.4195 dex** |
| σ 95% CI (day-cluster bootstrap, 1,000 reps, 732 days, seed 20260717) | **[0.4060, 0.4328]** |
| R² | **0.0018** |
| Intercept β₀ | −5.373 |
| Calibration slope β₁ (`log_solexs_soft`) | **0.0013** |
| Slope β₂ (`solexs_HR_high_low`) | 0.011 |
| Slope β₃ (`log_hel1os_band0`) | −0.000 |
| Residual mean | −0.000 (OLS check) |
| MAE | 0.3193 dex |
| RMSE | 0.4194 dex |
| Included flares | 7,050 (B 165, C 5,596, M 1,217, X 72) |
| Excluded | outside span 14,791; class not B/C/M/X 103; availability < 0.5: 1; malformed 0; non-finite 0 |

**The headline Layer-1 finding is R² = 0.0018 with β₁ = 0.0013: the frozen peak-window observables carry essentially no linear information about absolute GOES peak flux.** The fit is flat — residual means by class (exploratory table, §1.3) are simply the class offsets from a constant: B −0.74, C −0.13, M +0.60, X +1.60 dex. σ = 0.4195 is therefore not a calibration precision; it is the target's own class-mixture spread, unreduced.

`OBSERVED` (structural, from the same data): `log_solexs_soft` has median 0.000, range [−5.80, +17.58] — the signature of a standardized / relative-scale engineered feature, not an absolute flux. The v4 feature pipeline was built for ML training, where removing absolute scale is good practice; a scale-free feature cannot, by construction, regress onto an absolute flux scale. The frozen design could not have known this: the pre-registration was deliberately written without examining any data distribution, and structural column checks do not reveal scale conventions.

### 1.2 Availability audit (frozen §6)

| Group | n | SoLEXS usable | HEL1OS usable | Both | Neither |
|---|---|---|---|---|---|
| M/X | 1,289 | **1.000** | 1.000 | 1.000 | 0.000 |
| C | 5,597 | 0.9998 | 1.000 | 0.9998 | 0.000 |

**Gate 0: H_availability NOT SUPPORTED** (1.000 ≥ 0.80). During flares, instrument coverage is effectively complete; the 24.4% global SoLEXS gap rate (train-span column mean 0.756, consistent with that figure) falls in quiet periods, not flare windows. Corroborating exploratory check: of the 12–14 missed validation M/X label episodes per seed, **zero** were low-availability. Availability limits neither recall nor discrimination.

### 1.3 Residual structure (frozen §9 secondaries — EXPLORATORY)

Residual SD by target-flux quartile: 0.140 / 0.068 / 0.080 / 0.337. Within-class residual SD ≈ 0.25 dex for C, M, X alike; boundary-local (C4–M4) SD 0.234. Given the flat fit, all of this is target-variance structure, not calibration structure. Residual–availability correlation 0.005; first/second-half SDs 0.415/0.394 (temporally stable). Univariate SoLEXS-only σ = 0.4198 — identical to the trivariate, confirming no predictor contributes.

## 2. Derived Operational Bridge (Layer 2 — `HYPOTHESIS`)

Quoted with the frozen §14 assumption list: (i) Gaussian homoscedastic residuals; (ii) independent errors; (iii) a real method achieves exactly the measured σ; (iv) window-to-episode transfer; (v) one decision per label episode; (vi) non-C false episodes retained in full.

| Quantity | Value (per-seed range) |
|---|---|
| FE_impl(σ̂ = 0.4195) | **29.80** /month (per-seed 26.5–33.7) |
| FE_impl(σ_lo = 0.4060) | **29.24** |
| FE_impl(σ_hi = 0.4328) | **30.34** |
| Budget | 5.0 at recall ≥ 0.80 |

Exploratory companion: implied maximum class-separation AUC at σ̂ = **0.8057** (per-seed 0.796–0.815).

**Empirical contradiction of the bridge, stated plainly per the frozen §14 rule.** Two completed `OBSERVED` results exceed this "ceiling":
1. The frozen detector's calibrated probability separates C from M/X at **AUC 0.9146** (Experiment D, validation, same episode populations) — above the bridge's implied maximum 0.8057.
2. The frozen detector already operates at **14.27 false episodes/month** at the 0.80 recall floor (Sprint 33, sealed test) — a factor of 2 *better* than the bridge's FE_impl "floor" of 29.80.

An existing method outperforming a ceiling falsifies the ceiling. Specifically it falsifies assumption (iii)/(iv) in the upward direction: real methods extract substantially more class information than the frozen window-max linear calibration σ represents. The bridge is therefore measuring the information content of *the frozen feature construction*, not of *the instrument*.

## 3. Operational Interpretation (Layer 3 — `LOGICALLY IMPLIED`, conditional on Layer 2)

- Gate 0 fails to trigger (Layer-1 counts alone; no bridge dependence): availability is not the limit.
- FE_impl(σ_lo) = 29.24 > 5.0 → **Outcome B**: evidence supports **H_data under the frozen calibration model** — the instrument/data are the limiting factor *for calibrations of the §5.2 form*. The frozen scope note applies with unusual force here: the exploratory record shows the §5.2 family is a degenerate representative (scale-free features regressed on an absolute scale), and the completed record already contains methods above the family's ceiling. The unrestricted claim "the instrument cannot resolve the C/M boundary" is `HYPOTHESIS`, and it is *weakened*, not supported, by this experiment's exploratory layer.
- The declared pre-registered limitation (§14: heteroscedasticity biasing toward Outcome B, "toward wrongly terminating a viable direction") manifested in an extreme, unanticipated form: not merely heteroscedastic scatter but a scale-free predictor set, which forces σ toward the target's own variance and FE_impl toward its maximum. The primary governs; this bias is reported, not repaired.

## 4. Decision (Layer 4 — frozen rule, one of exactly three)

**2. Instrument capability does not support further modelling** — as bounded by the frozen calibration model, per Outcome B.

What this decision does and does not license, per the frozen scope note: it concludes the modelling programme *as gated by this pre-registration*; it does **not** establish that Aditya-L1 physically cannot resolve the C/M boundary, because the measured object (scale-free engineered features under a linear window-max calibration) demonstrably understates the instrument's usable information — the completed record itself contains two measurements above the derived ceiling. Any future claim about the instrument's physical ceiling would require a new pre-registered measurement on *absolute-scale* SoLEXS data (raw or pre-normalisation fluxes), which does not currently exist in the project's artifact tree. Authorising such an experiment is outside this report's scope.

## Self-audit (frozen §11)

1. **No interpretation threshold changed after analysis** — decision boundaries, availability gate, grid, bootstrap, inclusion rules all executed as frozen; verdict follows mechanically from FE_impl(σ_lo) > 5.0.
2. **No conclusion depends on an exploratory analysis** — the Outcome B decision rests only on Layers 1–2 primaries. Every statement drawing on §1.3 or the implied-AUC companion is labelled EXPLORATORY; the bridge-contradiction statements use completed-record `OBSERVED` results (Experiment D AUC 0.9146; Sprint 33 FE 14.27) plus the frozen-listed implied-AUC secondary, and they alter interpretation scope — which the frozen scope note already bounded — not the decision.
3. **Reproducibility** — `run_capability.py` + frozen inputs (catalog SHA `5368…499a`, dataset paths, seed 20260717) reproduce every number deterministically.
4. **Monotonicity check passed**: 29.24 ≤ 29.80 ≤ 30.34.
5. **Labels** — every quantity above carries OBSERVED / LOGICALLY IMPLIED / HYPOTHESIS; FE_impl is quoted nowhere without the §14 assumption list.

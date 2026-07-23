<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone XI feature ablation — incremental value of each feature family. -->
<!-- DATE: 2026-07-18 -->

# Feature Ablation Report — Milestone XI

Incremental contribution of every feature family to the M/X nowcast, measured by held-out test ROC-AUC (LightGBM, identical chronological split). Each family must earn inclusion.

---

## 1. T1 temporal features (Stage 1 — the base)

The full benchmark's T1 feature set (14 features: level, rolling stats, background excess, rise rates, observability) achieves **ROC-AUC 0.961** on nowcast.

**Incremental test — what the temporal context adds over raw level:** the univariate `rate_total` threshold scores **0.954**; the 14-feature LightGBM scores **0.961**. The rolling/rise/background features add **+0.007 AUC** — statistically significant (paired [+0.003, +0.012]) but under one AUC point. The feature-importance analysis (MODEL_COMPARISON §3) shows the model leans on `roll_mean_60`, `roll_std_60`, and `bg_excess` — i.e. the **background activity level**, exactly the Milestone X finding.

**Verdict: T1 temporal features are the signal carrier and add marginal value over raw level. INCLUDE.**

## 2. T2 spectral summaries (Stage 2 — tested, null)

Ablation on the SoLEXS-only nowcast (371,619 train / 192,541 test minutes), LightGBM, base = {`log_rate`, `roll_mean_15`, `roll_std_15`, `gti_fraction`}:

| Feature set | ROC-AUC | Δ vs T1-only |
|---|---|---|
| T1-only | 0.9605 | — |
| T1 + spectral bands (soft/mid/hard) | 0.9638 | **+0.0033** |
| T1 + hardness ratio | 0.9618 | **+0.0013** |
| T1 + all spectral | 0.9634 | +0.0029 |

**Verdict: T2 spectral features add ≤ 0.003 AUC — a confirmed NULL.** This was predicted in Milestone X from univariate analysis (≤ 0.012 AUC; hardness ratio at random for prediction). The multivariate LightGBM result is *even smaller* (+0.003), and well within the day-block-bootstrap CI width (~±0.012) of the base model. The 340-channel spectrum, summarised into bands, does **not** improve M/X detection at 1-minute resolution.

**Scientific weight of this null.** This is the central empirical test of v2's founding premise — that spectral resolution (340 real channels vs v1's 9 synthetic ones) would unlock performance. **The evidence does not support that premise for flare detection.** The result is reported as a contribution, not hidden: spectral resolution is scientifically valuable for *characterising* flares, but it does not measurably improve *detecting or predicting* them here.

**Recommendation: EXCLUDE T2 from the operational feature set.** Retain it only for future spectral-characterisation work (e.g. severity ranking once an RMF exists), not for detection.

## 3. T4 housekeeping (Stage 3 — not added, by justified decision)

**Not tested as features, and this is the correct decision under the stopping rule.** Two independent reasons, both pre-committed in Milestone X:

1. **Leakage/generalisation hazard.** T4 is instrument-state telemetry (temperatures, HV, pile-up/saturation counters). These correlate with orbital and seasonal cycles that happen to track observing conditions in this sample; a model can fit those correlations and fail to generalise. With 581 events there is ample room to overfit such a spurious signal.
2. **Confounded population.** T4 is HEL1OS-only, overlapping SoLEXS on **171 days**. Joining it to the SoLEXS nowcast would simultaneously (a) restrict to a 171-day window with different base rates and (b) introduce the leakage risk — the two effects cannot be separated, so the experiment could not yield a clean answer.

Since Stage 2 (spectral) already returned a null, the stopping rule — *do not add complexity without demonstrated incremental value* — directs against a confounded T4 experiment. **T4 is used only as a quality filter (`suninfov`, saturation counters), never as features.**

**Recommendation: EXCLUDE T4 as features.** If instrument-state features are ever tested, it must be a separate, explicitly-labelled experiment with a dedicated generalisation check.

## 4. Feature-family summary

| Family | Δ ROC-AUC | Statistically meaningful? | Decision |
|---|---|---|---|
| Raw `rate_total` (level) | baseline (0.954) | — | **The core signal** |
| T1 temporal (rolling, rise, background) | +0.007 | significant, sub-1-point | **INCLUDE** |
| T2 spectral bands | +0.003 | **NO** (within CI) | **EXCLUDE** |
| T2 hardness ratio | +0.001 | **NO** | **EXCLUDE** |
| T4 housekeeping | not tested | leakage + confounded | **EXCLUDE as features** |

## 5. Recommended operational feature set

**`rate_total` plus light T1 temporal context** (rolling mean/std, background-relative excess). ~6–14 features from a single table. Every family beyond this returned a null or a hazard. This is the smallest defensible feature set, and the evidence says it is also near the best available.

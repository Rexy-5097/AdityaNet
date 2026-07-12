<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 pre-registered protocol — EraMatchedGOES, the era-matched GOES-only de-confounding control for the Sprint 31 F2-vs-F1/F0 result. Written before training; no results. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — EraMatchedGOES Protocol (era-matched GOES-only de-confounding control)

**Conclusion (pre-registration, no results claimed).** EraMatchedGOES is a GOES-only PatchTST trained on the 17 GOES features (indices 0..16 of the F2 dataset) on the *same* Stage-2 era as F2, identical to F2 in every training respect except that F2's 15 Aditya-L1 features and 4 availability/staleness disclosure channels are absent (n_features = 17 instead of 36). It is the decisive test of the ISRO hypothesis because it removes the single confound that made Sprint 31 ambiguous: the pre-registered arms tie training era to arm identity (F1 trains on 2010–2019, F2 on 2023–2025), so F2's +0.0844 mean ΔTSS over F1 could be Aditya-L1 information OR era match, and the two cannot be separated within Sprint 31's arms. By holding era fixed at Stage-2 and varying only the presence of the Aditya channels, **(EraMatchedGOES vs F2)** isolates the pure Aditya-L1 feature effect as a clean one-variable comparison, and **(EraMatchedGOES vs F0)** isolates the pure training-era effect. This document specifies and justifies that control; it reports no metric and predicts no outcome.

## 1. Scientific rationale — the confound and the two comparisons

### The confound in plain terms
Sprint 31 measured F2 (GOES + Aditya-L1, trained on the Stage-2 2023–2025 era) against two references:
- **F1** (GOES-only, trained on the original 2010–2019 era): F2 beat F1 by a paired mean ΔTSS of **+0.0844** across 5 seeds — the pre-registered primary endpoint, met in 3 of 5 seeds (`artifacts/sprint31/Statistical_Analysis.md`, `FINAL_VERDICT.md`).
- **F0** (the frozen GOES-only V1 baseline, 14 raw GOES features, original era): F2 did **not** beat F0 on the identical S2 span — paired ΔTSS −0.0195..+0.0185, 0 of 5 seeds significant, mean −0.0046.

The Sprint 31 analysis already showed the arithmetic that exposes the confound: the F2−F1 margin of +0.084 decomposes as F2−F0 (−0.005) plus F0−F1 (+0.089), so nearly all of the primary-endpoint margin comes from **F1's own span-transfer collapse** on the Stage-2 span (F1-on-S2 at or below the recomputed persistence floor 0.3368 in several seeds), not from F2 exceeding GOES-only skill. Because F1 and F2 differ in *two* ways at once — instrument set (GOES-only vs GOES+Aditya) **and** training era (2010–2019 vs 2023–2025) — the +0.0844 cannot be attributed to Aditya-L1 with confidence. This is the exact limitation flagged in `Decision_Tree_Update.md` (caveat 2) and `Statistical_Analysis.md`: "the pre-registered design ties training era to arm ... Aditya features and training-regime match are confounded."

### The two comparisons EraMatchedGOES enables
EraMatchedGOES is GOES-only **but trained on the Stage-2 era**, so it differs from each Sprint 31 reference in exactly one intended dimension:

- **EraMatchedGOES vs F2 → the pure Aditya-L1 feature effect.** Both are trained on the identical Stage-2 splits, identical protocol, identical GOES feature values (see §3, byte-identical columns 0..16). The only difference is that F2 additionally sees the 15 Aditya-L1 features and 4 availability/staleness channels. Any measured skill difference is therefore attributable to the Aditya-L1 channels and nothing else. **This is the clean test of the ISRO hypothesis.**
- **EraMatchedGOES vs F0 → the pure training-era effect.** Both are GOES-only; they differ principally in training era (Stage-2 2023–2025 vs original 2010–2019). A difference here is attributable to era/regime, telling us whether "training on the recent, higher-activity Stage-2 era" is itself worth more than the deployed 16-year model, independent of Aditya. (This comparison carries one minor secondary difference — 17 vs 14 GOES features — discussed honestly in §6.)

### Why "one and only one deliberate difference" is essential
A control experiment answers a causal question only if it changes exactly one variable. Sprint 31's ambiguity is the textbook consequence of changing two variables (instrument + era) simultaneously between F1 and F2. EraMatchedGOES is designed so that against F2 there is precisely one deliberate difference — the presence/absence of the Aditya-L1 and disclosure channels. If any *second* difference were introduced — a different learning rate, a different sampler, a different calibration split, a different evaluator, even a different random-seed scheme — the Aditya question would again be confounded and the experiment would be invalidated. The line-by-line comparison table in §4 exists so that a reader can confirm the one-variable design mechanically, from the table alone.

## 2. Full training protocol

### 2.1 Data
- **Source dataset:** `artifacts/research_v4/dataset_v4.1.0-s2/` — the already-built, train-only-scaled Version-4 Stage-2 dataset used to train F2 (`manifest.json`, `dataset_version: dataset_v4.1.0-s2`).
- **Feature selection:** EraMatchedGOES consumes **columns 0..16 only** of that dataset's `feature_list` — the GOES subset. Because these are the very columns F2 was trained on (the F2 dataset is a superset), the GOES feature **values are byte-identical** to F2's GOES columns: same rows, same window construction, same scaling constants. This is the cleanest possible one-variable difference; no separate dataset build is performed and no GOES value can drift between the two arms.
- **Splits (identical files to F2):**
  - Train: `artifacts/research_v4/dataset_v4.1.0-s2/train.parquet` — **786,298 rows** (246,518 positives).
  - Validation: `artifacts/research_v4/dataset_v4.1.0-s2/validation.parquet` — **262,480 rows** (43,691 positives).
  - Test: `artifacts/research_v4/dataset_v4.1.0-s2/test.parquet` — **261,455 rows** (31,111 positives).
- **The 17 GOES feature names** (dataset indices 0..16; the 14 KEEP GOES columns plus the three GOES-physics columns `goes_T_iso`, `goes_EM`, `goes_dT_iso_15m`):

  | idx | feature | group |
  |----:|---------|-------|
  | 0 | `short_flux` | 14 KEEP GOES |
  | 1 | `long_flux` | 14 KEEP GOES |
  | 2 | `log_long_flux` | 14 KEEP GOES |
  | 3 | `mean_15m` | 14 KEEP GOES |
  | 4 | `variance_15m` | 14 KEEP GOES |
  | 5 | `mean_60m` | 14 KEEP GOES |
  | 6 | `variance_60m` | 14 KEEP GOES |
  | 7 | `peak_30m` | 14 KEEP GOES |
  | 8 | `peak_60m` | 14 KEEP GOES |
  | 9 | `flux_gradient_5m` | 14 KEEP GOES |
  | 10 | `flux_gradient_15m` | 14 KEEP GOES |
  | 11 | `flux_acceleration_5m` | 14 KEEP GOES |
  | 12 | `flux_acceleration_15m` | 14 KEEP GOES |
  | 13 | `minutes_since_last_flare` | 14 KEEP GOES |
  | 14 | `goes_T_iso` | GOES-physics |
  | 15 | `goes_EM` | GOES-physics |
  | 16 | `goes_dT_iso_15m` | GOES-physics |

  **Explicitly excluded** (present in F2, absent here): the 15 Aditya-L1 features (indices 17..31: `solexs_HR_high_low`, `solexs_HR_mid_low`, `solexs_dHR_15m`, `solexs_HR_peak_60m`, `log_solexs_soft`, `solexs_variance_15m`, `solexs_variance_60m`, `solexs_peak_30m`, `minutes_since_solexs_active`, `solexs_active_fraction_6h`, `hel1os_fluence_30m`, `hel1os_fluence_60m`, `nonthermal_thermal_ratio`, `d_ntr_15m`, `log_hel1os_band0`) and the 4 availability/staleness disclosure channels (indices 32..35: `solexs_available`, `solexs_staleness_n`, `hel1os_available`, `hel1os_staleness_n`). 17 + 15 + 4 = 36 = F2's `n_features`.
- **Scaling provenance:** train-only **RobustScaler** (median/IQR) fit on `s2_train`, inherited unchanged from the F2 dataset (`manifest.json` → `scaler_params.fitted_on_split: "train"`). The per-column median and IQR for all 17 GOES columns are already baked into the dataset and are used exactly as F2 used them (e.g. `log_long_flux` median −13.0973, IQR 0.9667; `goes_T_iso` median 4.9174, IQR 1.0826; `goes_EM` median 48.9030, IQR 0.3306; `goes_dT_iso_15m` median 0.0, IQR 0.3659). No re-fitting occurs; there is no test or validation leakage into the scaler.

### 2.2 Model
- **Architecture:** single-encoder PatchTST — the identical F2 architecture (single concatenated-input encoder, no per-instrument branches), with the **input width set to 17** instead of 36. This is the only architectural change, and it is the mechanical consequence of dropping the 19 non-GOES channels; it introduces no new architectural choice.
- **n_features = 17.** (F2: n_features = 36, `run_meta.json`.)

### 2.3 Optimizer / scheduler / loss / sampler / training loop (all identical to F2)
Taken verbatim from `artifacts/sprint31/runs/F2_s42/run_meta.json` and the Sprint 25/28 frozen protocol (`artifacts/sprint25/02_retraining_protocol.md`, `artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md`):
- Optimizer **AdamW**, learning rate **1e-4**, weight decay **1e-4**.
- Loss **FocalLoss**, alpha **0.25**, gamma **2.0**.
- Gradient clipping, clip_norm **1.0**.
- Batch size **64**.
- Steps per epoch **5000**.
- Max epochs **20**, early-stopping **patience 3** on validation TSS.
- Scheduler **CosineAnnealingLR**, T_max **20**.
- **WeightedRandomSampler** for the train loader.
- Validation loader **SHUFFLED** (matching F2's configuration exactly).
- num_workers **2**, device **MPS**.

### 2.4 Seeds and escalation rule
Seeds **42, 43, 44** minimum, with the pre-registered escalation rule from Sprint 31: **if the max−min seed TSS range exceeds 0.015, add seeds 45 and 46** (the 5-seed publication tier). This is the identical rule F2 ran under (its 3-seed range was 0.0153 > 0.015, which triggered escalation to 5 seeds).

### 2.5 Calibration
**Isotonic** calibration fit on the **validation split only**, identical to F2. No calibration information is drawn from the test set. Policy thresholds are selected on validation only.

### 2.6 Sealed evaluation
Each trained seed is scored **once** through the frozen **Sprint 24 `UnifiedEvaluator`**, instantiated on the **Stage-2 test span**, identical to `scripts/sprint31/eval_s2.py`:
- Policy operating point: **yellow = 0.14**, **red = 0.95**.
- Episode construction with 60-minute merge gap; onset = episode start + 360 minutes.
- Paired moving-block bootstrap, **2,880-window blocks**, 1,000 confusion replicates / 200 ranking replicates, RNG seed **20260704**.
- **Persistence and climatology floors recomputed on the S2 span** through the identical frozen class (S2 persistence TSS 0.3368, climatology TSS 0.0, per Sprint 31).
- Nothing in the frozen harness is modified. Paired comparisons (EraMatchedGOES vs F2; EraMatchedGOES vs F0) use identical resample indices on the same S2 test span, exactly as Sprint 31's pairings were computed.

## 3. Line-by-line comparison against F2 — one deliberate difference only

Every row must read **MATCH** except exactly one: the feature set / n_features. Any second row reading a non-MATCH would reintroduce the confound and invalidate the experiment.

| Parameter | F2 value | EraMatchedGOES value | MATCH? |
|-----------|----------|----------------------|--------|
| Optimizer | AdamW | AdamW | MATCH |
| lr | 1e-4 | 1e-4 | MATCH |
| weight_decay | 1e-4 | 1e-4 | MATCH |
| Loss | FocalLoss | FocalLoss | MATCH |
| alpha | 0.25 | 0.25 | MATCH |
| gamma | 2.0 | 2.0 | MATCH |
| clip_norm | 1.0 | 1.0 | MATCH |
| batch_size | 64 | 64 | MATCH |
| steps_per_epoch | 5000 | 5000 | MATCH |
| max_epochs | 20 | 20 | MATCH |
| patience (val TSS) | 3 | 3 | MATCH |
| Scheduler | CosineAnnealingLR | CosineAnnealingLR | MATCH |
| t_max | 20 | 20 | MATCH |
| Train sampler | WeightedRandomSampler | WeightedRandomSampler | MATCH |
| Val loader shuffle | SHUFFLED | SHUFFLED | MATCH |
| Calibration method | Isotonic | Isotonic | MATCH |
| Calibration fit split | Validation only | Validation only | MATCH |
| num_workers | 2 | 2 | MATCH |
| Device | MPS | MPS | MATCH |
| Train parquet | `dataset_v4.1.0-s2/train.parquet` (786,298 rows) | `dataset_v4.1.0-s2/train.parquet` (786,298 rows) | MATCH |
| Val parquet | `dataset_v4.1.0-s2/validation.parquet` (262,480 rows) | `dataset_v4.1.0-s2/validation.parquet` (262,480 rows) | MATCH |
| Test parquet | `dataset_v4.1.0-s2/test.parquet` (261,455 rows) | `dataset_v4.1.0-s2/test.parquet` (261,455 rows) | MATCH |
| Scaler | train-only RobustScaler (s2_train) | train-only RobustScaler (s2_train), same constants | MATCH |
| Evaluator | frozen Sprint 24 UnifiedEvaluator on S2 span | frozen Sprint 24 UnifiedEvaluator on S2 span | MATCH |
| Policy thresholds | yellow 0.14 / red 0.95 | yellow 0.14 / red 0.95 | MATCH |
| Persistence/climatology floors | recomputed on S2 span | recomputed on S2 span | MATCH |
| Bootstrap block / replicates / seed | 2,880 / 1,000 / 20260704 | 2,880 / 1,000 / 20260704 | MATCH |
| Seeds | 42, 43, 44 (+45, 46 on escalation) | 42, 43, 44 (+45, 46 on escalation) | MATCH |
| Escalation rule | range > 0.015 → add 45, 46 | range > 0.015 → add 45, 46 | MATCH |
| Architecture | single-encoder PatchTST | single-encoder PatchTST | MATCH |
| **Feature set / n_features** | **36 (17 GOES + 15 Aditya + 4 disclosure)** | **17 (GOES only, indices 0..16)** | **DIFFERENT — the one deliberate variable** |

**Invalidation clause.** The scientific validity of the (EraMatchedGOES vs F2) comparison depends on this table showing exactly one non-MATCH row. If a reader finds any second difference, the Aditya-L1 attribution is confounded and the result must not be reported as isolating the Aditya effect. The feature-set row is the intended manipulation; everything else is held fixed by construction, including the GOES feature values themselves (columns 0..16 are shared, not rebuilt).

## 4. Expected-outcomes interpretation matrix (conditional definitions only — no prediction)

These are pre-committed *definitions* of what each pattern would mean. The document does **not** predict which will occur; each label states the meaning of the ISRO/Aditya hypothesis under that pattern.

| # | Observed pattern (to be measured) | Meaning for the ISRO / Aditya-L1 hypothesis | Label |
|---|-----------------------------------|---------------------------------------------|-------|
| a | EraMatchedGOES ≈ F2 **and** both > F0 | The improvement over the deployed baseline is attributable to the **training era**; the Aditya-L1 channels add nothing beyond what era-matched GOES already provides. | Aditya value **NOT SUPPORTED**; era effect real |
| b | F2 > EraMatchedGOES (paired, under the pre-registered rule) | Aditya-L1 adds **genuine information beyond era**, since era and all else are held fixed and only the Aditya channels differ. | Aditya value **SUPPORTED** |
| c | EraMatchedGOES ≈ F0 | The training era does **not** explain F2's behavior either (era-matched GOES matches the original-era baseline), pointing to something else; neither a clean Aditya effect nor a clean era effect is demonstrated by this pair. | **AMBIGUOUS** — cause lies elsewhere |

Notes: "≈" and ">" are adjudicated by the same pre-registered paired moving-block bootstrap and minimum-effect rule used in Sprint 31 (paired ΔTSS with the ≥ +0.02 / lower-95%-bound-> 0 / majority-of-seeds criterion; pre-onset recall not degraded). Rows a and b are not mutually exclusive across metrics — e.g. window-TSS and pre-onset episode recall may resolve differently, and each is reported on its own terms exactly as Sprint 31 did. No row is promoted to a headline until measured.

## 5. Threats to validity

1. **The (EraMatchedGOES vs F0) comparison carries a minor secondary feature difference.** F0 is the frozen V1 baseline trained on **14 raw GOES features** on the **original 2010–2019 era**, whereas EraMatchedGOES uses **17 GOES-physics features** (the 14 KEEP columns plus `goes_T_iso`, `goes_EM`, `goes_dT_iso_15m`) on the **Stage-2 era**. So this particular comparison mixes the intended era difference with a secondary 14-vs-17 GOES-feature difference. This is stated honestly as a limitation of the *era* comparison: a difference between EraMatchedGOES and F0 cannot be attributed to era alone with the same cleanliness as the Aditya comparison. By contrast, **the (EraMatchedGOES vs F2) comparison remains perfectly clean** for the Aditya question, because both use the identical 17 GOES features (byte-identical values) and differ only in the presence of the Aditya-L1 and disclosure channels. The decisive test — the Aditya effect — is therefore uncompromised; only the auxiliary era readout carries this caveat.
2. **Availability has no variance on the S2 span.** As reported in Sprint 31, the S2 test span shows SoLEXS quality p01 0.697 / median 0.752 / p99 0.805 — no window reaches the 0.9 stratum boundary and none falls below 0.5. The availability-stratification question is therefore unanswerable on this span for either arm; EraMatchedGOES omits the 4 disclosure channels, but on this span those channels carry little cross-window information anyway. This is a property of the span, not of the control, and is reported as-is.
3. **Seed noise.** The escalation rule (range > 0.015 → 5 seeds) is inherited precisely so that a marginal EraMatchedGOES–F2 gap is not over-read from a 3-seed sample; F2 itself triggered escalation at a 0.0153 range, so a 5-seed run is anticipated but not assumed.
4. **Single-span scope.** Both comparisons live entirely on the S2 test span, per the Sprint 28 cross-span comparability rule ("no conclusion may mix spans"). EraMatchedGOES makes no claim about the original V1 span.

---

*Pre-registration note.* This protocol is written before any EraMatchedGOES training or evaluation has been run. It contains no metric numbers for EraMatchedGOES and asserts no result. It inherits its statistical machinery, thresholds, seeds, and stopping rules unchanged from the frozen Sprint 24 harness and the Sprint 25/28/31 pre-registrations, so that no endpoint, threshold, or rule can move after results are seen. Grounding documents: `artifacts/sprint31/FINAL_VERDICT.md`, `artifacts/sprint31/Statistical_Analysis.md`, `artifacts/sprint31/Decision_Tree_Update.md`, `artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md`, `artifacts/sprint25/07_preregistered_analysis_plan.md`, `artifacts/sprint31/runs/F2_s42/run_meta.json`, `artifacts/research_v4/dataset_v4.1.0-s2/manifest.json`.

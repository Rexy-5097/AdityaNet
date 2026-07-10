<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 unified evaluation protocol. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Unified Evaluation Framework (Protocol)

**Conclusion:** One class — `UnifiedEvaluator` in `scripts/sprint24/eval_framework.py` — evaluates every method through byte-identical dataset, window construction, episode construction, metric formulas, moving-block bootstrap, and confidence-interval computation. Methods differ only in the probability/alert arrays they submit. The block length is 2,880 windows (two days), chosen because it is eight times the 360-minute mechanical label dependence and comfortably longer than typical flare-cluster alert episodes; sensitivity to this choice is reported in `04_bootstrap_analysis.md`.

## Dataset and window construction (identical for all methods)

- **Source:** `artifacts/research/test.parquet` (2023-01-01 → 2026-06-14; 1,806,673 rows), frozen and fingerprint-verified in Step 1 (`labels.npy ≡ target_6hr_binary[360:]` confirmed by array equality this session).
- **Window i:** label = `target_6hr_binary` at parquet row i+360 (flare within the next 360 minutes of that row's timestamp); decision timestamp = that row's timestamp. N = 1,806,313 windows.
- **V1 probabilities:** the canonical archived deterministic test predictions `artifacts/calibration/probs.npy` (chosen over fresh inference because archived arrays are the reproducibility anchor — cross-platform MPS drift up to 9.76e-4 is documented in `scientific_validation_report.md` §3). Calibration via the frozen `artifacts/calibrator.pkl` (isotonic, validation-fit).
- **No preprocessing differs by method.** Persistence and climatology consume the same label/timestamp arrays; nothing is resampled, filtered, or imputed differently anywhere.

## Method definitions

| Method | Probability array | Alert rule |
|--------|-------------------|-----------|
| A — persistence (causal) | Trailing-360-minute M/X flare indicator. With window i's label defined at row i+360, the trailing indicator at decision time is exactly `target_6hr_binary[row i]` — fully observable at decision time | alert iff indicator = 1 |
| A′ — persistence (literal, NON-CAUSAL) | The brief's literal "last-window label" (window i−1's label = row i+359's label) covers flares up to 359 minutes **after** decision time; it is not a realizable forecaster. Computed for completeness, flagged, excluded from the verdict | alert iff label = 1 |
| B — climatology | Fixed probability = validation-era positive window rate, computed this session from `artifacts/research/validation.parquet` | alert iff p ≥ yellow threshold (it is not, so B never alerts — the honest consequence of "fixed probability" under the deployed policy) |
| C — V1 + clean policy | Calibrated archived test probabilities | yellow at ≥ 0.14, red at ≥ 0.95, from `artifacts/policies/operator_policy_v2.json` (Step 1-verified). Deterministic thresholds only: MC-Dropout suppression and sequential RED confirmation are **not** simulated (both only remove alerts ⇒ C's recall and false-alarm counts are upper bounds; noted wherever C is reported) |
| D — V1 + validation-swept threshold | Raw archived test probabilities | alert iff raw p ≥ θ*, where θ* maximizes window TSS on a **fresh, this-session deterministic validation pass** (`scripts/sprint24/run_validation_inference.py`; no test data read — the script's not-loaded list and manifest prove it) |

## Episode construction (identical for all methods)

- **Label episodes:** maximal runs of positive-label windows; runs separated by ≤ 60 minutes merge (gap tolerance for the 0.23% data-gap rate).
- **First flare onset:** label-episode start + 360 minutes (the label leads the first flare by exactly the horizon).
- **Detected:** any alert window inside the episode span. **Pre-onset detected:** alerting began before the first flare onset — the operator-decisive variant, since alerts after onset have no protective value for the first flare.
- **Lead time:** onset − start of the earliest overlapping alert episode (may exceed 360 minutes via carry-in alerts; negative if alerting begins after onset).
- **False alert episode:** alert episode overlapping no label episode; normalized per 30.44-day month.

## Block bootstrap (never IID)

- **Why not IID:** adjacent windows share 359/360 input minutes and labels are 360-minute-lookahead indicators — mechanical MA(360)-type dependence — and flare activity clusters on multi-hour to multi-day scales. IID resampling would shrink confidence intervals by roughly the square root of the effective dependence length.
- **Window metrics:** the window axis is partitioned into contiguous blocks of **2,880 windows (2 days)**; per-block confusion sums are precomputed once per method; 1,000 replicates resample blocks with replacement and recompute every confusion-derived metric (TSS, HSS, MCC, Precision, Recall/POD, F1, FAR, POFD). ROC-AUC and PR-AUC use 200 block-resampled replicates (each requires full re-ranking of 1.8M scores).
- **Block length justification:** dependence sources are (i) the 360-minute label horizon and (ii) alert/flare episode durations (hours). 2,880 minutes = 8 × the label horizon, so at most one block boundary in eight cuts through a dependence span, which the moving-block bootstrap tolerates. `04_bootstrap_analysis.md` reports the TSS interval width at block lengths 1,440 / 2,880 / 5,760 to show the conclusion is not block-size sensitive.
- **Episode metrics:** bootstrap over blocks of **10 consecutive label episodes** (episodes cluster; adjacent-episode outcomes are not independent), 1,000 replicates for episode recall and pre-onset recall.
- **Paired comparisons:** all methods share literally the same resample index matrices (single seeded RNG, seed 20260704, drawn once in the evaluator constructor), so method deltas are computed replicate-by-replicate on identical resamples — the paired design used in `06_statistical_tests.md`. Significance criterion: the 95% bootstrap interval of the delta excludes zero; bootstrap p-values are reported with floor 1/1000.
- **Why not McNemar:** McNemar's test assumes independent paired trials; stride-1 windows violate this by construction, so it is not used.

## Reproducibility

The evaluator is deterministic given (arrays, seed): the ABC runner constructs two fresh evaluators, evaluates method A through both, and compares SHA256 hashes of the serialized results — recorded in `results_abc.json` under `reproducibility` and reported in the quality gates.

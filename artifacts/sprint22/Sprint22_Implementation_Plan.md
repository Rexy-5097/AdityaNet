# Sprint 22 — Implementation Plan: Honest Decision Layer

**Conclusion:** Six work packages, executable in order on the existing Apple M4/MPS machine, no retraining, estimated 6–9 hours of compute (dominated by two full-split inference passes) and 2–3 working days of engineering. Output: a versioned, provenance-stamped operator policy derived exclusively from validation data, an episode-level evaluation module with tests, one pre-registered honest test evaluation, and a one-line production switch in `inference.py` with full rollback.

---

## WP1 — Freeze and quarantine the leaked policy

**Files:**
- Move nothing; create `artifacts/policy_archive/operator_thresholds_v1_TEST_LEAKED.json` as a copy of `artifacts/operator_thresholds.json` with an added `"deprecation"` block documenting the leak (source script, docstring line, date).
- Add `artifacts/policy_archive/README.md` explaining why v1 is invalid, citing `scripts/optimize_operational_policy.py:6`.

**Quality gate:** QG-004 checklist item — leak documented with file-level evidence before any new derivation begins.

## WP2 — Validation inference pass (reuse, don't rewrite)

**Files:** new `scripts/sprint22/generate_policy_inputs.py`, importing from `app/services/ml/dataset.py`, `model.py`, and `inference.py`'s `CalibratorWrapper`.

**Behavior:**
1. Deterministic pass (model.eval, no_grad) over `artifacts/research/validation.parquet` (1,568,759 windows) — mirrors `scripts/refine_thresholds.py` lines 146–161.
2. MC Dropout pass (50 samples) over the *policy-active subset only* — windows whose calibrated deterministic prob ≥ 0.05 — to bound compute (the uncertainty tiers only act above threshold; precedent: the Sprint operator-policy replay used a calibrated-prob ≥ 0.40 active subset, `scientific_validation_report.md` §5).
3. Save `artifacts/sprint22/val_probs.npy`, `val_probs_calibrated.npy`, `val_unc.npy`, `val_labels.npy`, plus a JSON manifest: dataset SHA256, checkpoint SHA256 (43de19dd… convention per `benchmark_manifest.json`), script git-less content hash, timestamps, `"test_data_used": false`, and the explicit not-loaded list (pattern from `scripts/refine_thresholds.py` lines 63–68).

**Runtime estimate:** deterministic pass ≈ 1.5–2.5 h on MPS at batch 512 (extrapolated from prior validation passes in `refine_thresholds.py` usage); MC Dropout on the active subset (expected ≤ 10% of windows × 50 passes) ≈ 2–4 h. Memory: ≤ 8 GB unified (batch 512 × 360 × 14 float32 ≈ 10 MB per batch; arrays ≈ 6 × 1.57M floats ≈ 40 MB).

## WP3 — Episode-level evaluation module

**Files:** new `app/services/ml/episodes.py` + tests `tests/test_episodes.py` (first entries in a new `tests/` tree — chips at GAP-001).

**Behavior:**
- `build_episodes(timestamps, labels, alerts, gap_minutes=60)` — groups contiguous positive-label windows into flare episodes and contiguous alert windows into alert episodes (formalizing the Sprint 5.5 method behind `artifacts/operator_readiness_report.json`, n_episodes=77).
- `episode_metrics(...)` — episode POD, episode FAR, false-episode rate/month, median lead time (first true alert minute → episode start).
- `block_bootstrap_ci(metric_fn, episodes, n=1000)` — resamples *episodes*, not windows, fixing the autocorrelation flaw in window-level CIs (`app/services/ml/metrics.py::paired_bootstrap_test` resamples i.i.d. windows).

**Tests:** synthetic sequences with known episode structure — merge behavior at the gap boundary, lead-time computation, degenerate cases (zero alerts, all-alert), CI reproducibility under fixed seed.

## WP4 — Cost-loss policy optimizer

**Files:** new `scripts/sprint22/optimize_policy_v2.py`; reuses `app/services/ml/metrics.py` and WP3's module.

**Behavior:**
1. Sweep thresholds 0.02→0.95 (step 0.01) on calibrated validation probs; compute **episode-level** metrics per point via WP3.
2. Select yellow/red by cost-loss: minimize `C_miss × missed_episodes + C_fa × false_episodes` for an explicit cost-ratio grid `C_miss/C_fa ∈ {2, 5, 10, 20}`; publish the full frontier so the operator (not the optimizer) owns the trade-off. Default recommendation: the C=10 point, subject to floor constraints episode-recall ≥ 0.30 and episode-precision ≥ 0.50 (same floors Sprint 5.6 used — `scripts/refine_thresholds.py` lines 20–31 — now enforced at episode level).
3. Re-derive uncertainty-suppression tiers on validation MC-Dropout outputs: grid-search the three cutoffs (currently unexplained constants 0.10/0.15/0.20 in `artifacts/operator_thresholds.json`) for episode-level net benefit; drop any tier whose marginal contribution is not positive.
4. Component ablation on validation: bare thresholds → +uncertainty suppression → +RED confirmation (3-sample rolling mean + slope, `app/services/ml/inference.py`) → +hard-X-ray coincidence filter; write `artifacts/sprint22/policy_ablation.json`.
5. Emit `artifacts/operator_policy_v2.json`: thresholds, tiers, confirmation params, full provenance block (WP2 manifest hash, constraint set, cost ratio chosen, sweep CSV path).

**Runtime:** minutes (NumPy sweeps over precomputed arrays).

## WP5 — Pre-registered honest test evaluation (run once)

**Files:** new `scripts/sprint22/final_test_evaluation.py`; outputs `artifacts/sprint22/honest_test_report.json` + `Sprint22_Honest_Test_Report.md`.

**Protocol (pre-registered in the script header before running):**
1. Inputs: frozen policy v2 (WP4), saved test probabilities `artifacts/calibration/probs.npy`/`labels.npy` (canonical archived predictions — avoids MPS re-inference drift, `scientific_validation_report.md` §3), test timestamps from `artifacts/research/test.parquet`.
2. Metrics: window-level full suite (`app/services/ml/metrics.py::compute_full_suite`) + episode-level suite (WP3) + block-bootstrap 95% CIs.
3. One run. No parameter may change afterward; any post-hoc change reverts status to "validation-tuned" and requires a fresh hold-out.
4. Report includes the side-by-side correction table: leaked-policy published numbers vs honest-policy numbers, so the downward revision is explicit and owned.

**Note:** MC-Dropout-dependent tiers are evaluated on the test set via a bounded active-subset MC pass (same method as WP2 step 2; precedent `scientific_validation_report.md` §5). Runtime ≈ 2–3 h.

## WP6 — Production switch + regression tests

**Files changed:** `app/services/ml/inference.py` — replace the `operator_thresholds.json` path with `operator_policy_v2.json` and parse the (superset) schema; no logic change beyond re-derived tier constants.
**Files added:** `tests/test_alert_policy.py` — table-driven cases pinning the full alert decision function: prob/uncertainty grids × suppression tiers × RED confirmation state machine (rolling deque behavior, slope condition, coincidence filter), including the exact boundary values from policy v2.

**Quality gates before completion:**
- QG-004 (research validation): WP1 evidence + WP2 manifest + WP5 pre-registration all machine-checkable.
- QG-002 (PR checklist): policy diff reviewed against `Sprint22_Selected_Improvement.md` "done" criteria.
- QG-007 (bug fix): B1/B3 closed with the archived-v1 + deployed-v2 pair as evidence.
- AgentOS validator (`tools/scripts/validate_agentos.py`) 100/100; `context/state.md` updated (SCI-002 → RESOLVED-with-nuance: calibrator clean, thresholds were the leak; B1/B2/B3 → closed).

## Resource summary

| Resource | Requirement |
|----------|-------------|
| GPU | Apple M4 MPS (existing); no CUDA needed |
| Compute | ≈ 6–9 h total (WP2 ≈ 4–6 h, WP5 ≈ 2–3 h, sweeps ≈ minutes) |
| Memory | ≤ 8 GB unified peak (batch-512 inference); arrays ≈ 100 MB |
| Disk | ≈ 200 MB new artifacts under `artifacts/sprint22/` |
| Retraining | None — model and calibrator untouched |

## Rollback plan

1. `operator_policy_v2.json` is additive; v1 remains in `artifacts/policy_archive/`.
2. `inference.py` change is a single path + schema-parse commit; revert restores prior behavior exactly.
3. If the honest test evaluation reveals the v2 policy underperforms even the leaked v1 on episode POD *and* FAR simultaneously (not expected — v1's episode recall floor is 3.97%), ship v2 anyway with the honest numbers and open a Phase-3 (recalibration) fast-follow: a scientifically valid worse number beats an invalid better one for operator trust, and the correction is the hackathon story, not the setback.
4. All WP2/WP5 arrays are content-hashed in manifests; any downstream dispute is re-checkable without re-running inference.

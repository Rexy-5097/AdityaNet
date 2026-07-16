<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Layer 3 frozen implementation contract — Aditya-only operational nowcaster. Immutable from the moment implementation begins. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Aditya-only Operational Nowcaster: FROZEN Implementation Contract

Immutable. No hypothesis, metric, threshold, stopping rule, statistical test, episode/bootstrap parameter, or deliverable may change once implementation begins.

## Frozen objectives
Establish whether the Aditya-only (SoLEXS + HEL1OS) flare nowcaster, at a validation-selected operating point, achieves an operationally usable episode-level detection profile — false-episodes-per-month at or below the budget while retaining episode recall at or above the floor — on the sealed Stage-2 test set.

## Frozen hypotheses
- **Primary.** At the operating point selected on validation to achieve ≥ 0.90 validation episode recall, the nowcaster achieves test false-episodes-per-month ≤ 5.0 with test episode recall ≥ 0.80 in ≥ 2 of 3 seeds. Endpoint: test false-episodes-per-month. Success: ≤ 5.0 with recall ≥ 0.80 in ≥ 2/3 seeds. Failure: the conjunction fails in ≥ 2/3 seeds (null holds — publishable, not deployable).
- **Capability sub-hypothesis.** The three-seed mean window-level ROC-AUC (measured on the validation split, to preserve the single-test-touch discipline) reproduces the feasibility separability. Success: ≥ 0.87. Failure: < 0.87 (halt, report non-replication).

## Frozen metrics
- **Primary endpoint — false-episodes-per-month:** count of alert episodes (contiguous alert-minute runs merged across gaps < 60 minutes) overlapping no true episode, per 30.44-day month, at the frozen operating point; minimum required effect ≤ 5.0.
- **Secondary endpoints:** episode recall (gating floor 0.80); detection latency (minutes from flare `start_time` to first alert within the episode); time under alert (fraction of the test period in the alert state); operating-point stability (|validation episode recall − test episode recall|); window-level ROC-AUC and PR-AUC (separability references; capability gate on validation ROC-AUC).
- True episodes: M/X rise-phase intervals [`start_time`, `peak_time`] merged under the 60-minute gap. Positive nowcast window: end-minute within a rise phase.

## Frozen statistical analysis
Episode metrics through the frozen Sprint-24 `UnifiedEvaluator`; 95% CIs from the moving-block bootstrap, block length 2,880 windows (2 days = 8× the 360-minute horizon; preserves the 359/360-minute window autocorrelation that invalidates IID resampling), 1,000 confusion replicates, RNG seed 20260704. Three seeds (42, 43, 44), justified by the measured ROC-AUC seed standard deviation ≈ 0.005 for this problem class (`artifacts/sprint_diagnostic/Statistical_Analysis.md`); escalate to five seeds (45, 46) iff the across-seed false-episodes-per-month range exceeds 1.0/month. Decision rule: a seed passes iff test false-episodes-per-month ≤ 5.0 and test episode recall ≥ 0.80; primary CONFIRMED iff ≥ 2/3 (or ≥ 3/5 after escalation) seeds pass, else REJECTED.

## Frozen operating-point selection
Isotonic calibration fit on the validation split only; alert threshold = the highest validation threshold achieving ≥ 0.90 validation episode recall (or, if 0.90 is unattainable, the highest threshold achieving the maximum attainable recall provided it is ≥ 0.80); test probabilities transformed by the validation-fit calibrator and scored exactly once.

## Frozen stopping rules
(1) No validation threshold reaches 0.80 episode recall → terminate early; verdict: not usable, report maximum attainable recall. (2) Three-seed mean validation window ROC-AUC < 0.87 → halt before the operating-point analysis; verdict: single-seed feasibility did not replicate. (3) No threshold/label/metric/episode/bootstrap/seed altered after results; no run repeated for being disappointing.

## Frozen deliverables (under artifacts/sprint33_nowcast/)
`00_PREREGISTRATION.md` (this contract); `runs/s<seed>/` (per-seed checkpoint reference, calibrated probability arrays, sealed episode eval.json); `Operating_Point_Analysis.md` (recall-vs-false-episodes trade-off curve + capability checkpoint); `Nowcast_Results.md` (primary verdict, metrics labelled OBSERVED/DERIVED/NOT PROVEN); `Statistical_Analysis.md` (bootstrap intervals, seed variance, escalation record); `Sensitivity_Labels.md` (whole-event + onset-only labels); `Provenance_Report.md`; `Verdict.md` (usable YES/NO).

## File-level implementation plan (in order)
1. Reuse `scripts/sprint33/train_driver.py` unmodified to train seeds 42/43/44 on `artifacts/research_v4/dataset_adi_nowcast/` (run-ids NC_s42/43/44; checkpoints under `artifacts/sprint33/runs/`).
2. Create `scripts/sprint33_nowcast/eval_episode_nowcast.py` — infer val+test, isotonic-calibrate on val, select the highest val threshold hitting ≥ 0.90 episode recall, instantiate the frozen `UnifiedEvaluator` on the nowcast-label array for episode recall + false-episodes-per-month, add detection-latency and time-under-alert; write sealed eval to `artifacts/sprint33_nowcast/runs/s<seed>/`.
3. Create `scripts/sprint33_nowcast/analyze.py` — aggregate 3 seeds, build the trade-off curve, apply the decision rule, run the sensitivity labels.
4. Create `scripts/sprint33_nowcast/run.sh` — orchestrate with `;`-separated resilient arms; write the reports.

## Quality gates (in run order)
(1) Provenance pre-check: V3 checkpoint, frozen s2_test, Sprint-24 harness SHA, `v4-goes-final` tag byte-identical. (2) Leakage check: operating point + calibrator on validation only. (3) Capability gate: three-seed validation window ROC-AUC ≥ 0.87. (4) Determinism: analyze.py identical primary verdict on rerun. (5) Provenance post-check.

## Definition of DONE
Complete iff, regardless of metric outcome: three seeds trained and sealed-evaluated (or five after escalation); primary verdict computed by the frozen decision rule in `Verdict.md`; all five quality gates passed; all eight deliverables written. A NO verdict meeting these is complete; a YES leaving any gate unrun is incomplete.

## Compute
Calibrated to `artifacts/sprint26a/04_COMPUTE_REPORT.md` (~256 s / 5,000-step epoch) and this session's ~20–35 min per 15-epoch early-stopped nowcast run: three seeds + episode evaluation ≈ 2–3 h; five-seed escalation +~1 h.

# Sprint 22 — Selected Improvement: The Honest Decision Layer

**Conclusion:** The single highest expected-return improvement is a leakage-free rebuild of the operator decision layer — validation-only cost-loss threshold selection, re-derived uncertainty-suppression tiers, episode-level evaluation as the primary yardstick, and exactly one pre-registered honest test evaluation — deployed into `app/services/ml/inference.py` as a versioned, provenance-stamped policy. It repairs a scientific-validity flaw (test-tuned thresholds), an operational failure (3.97% flare recall), and a process failure (a computed fix never deployed) in one low-cost, zero-retraining work item.

---

## Why this one

Three independent lines of evidence converge on the decision layer:

1. **It is scientifically invalid today.** `scripts/optimize_operational_policy.py` selected the deployed thresholds by sweeping the saved *test-set* probabilities (docstring line 6; inputs `artifacts/calibration/probs.npy`/`labels.npy`, N=1,806,313 = test set). Every operator-level number in `artifacts/operator_readiness_report.json` and `artifacts/bootstrap_metrics.json` evaluates thresholds on their own selection data.
2. **It is operationally useless today.** Episode recall 3.97%, TSS 0.039 at deployed settings (`artifacts/operator_readiness_report.json`) — and those are the *leak-inflated* numbers.
3. **It is cheap to fix.** The model is fine as-is for this work (calibrated PR-AUC 0.475, ROC-AUC 0.748 — `artifacts/calibration/calibration_report.json`); the calibrator is already leakage-clean (`scripts/calibrate_model.py` fits on validation, lines 191–202); half the machinery already exists (`scripts/refine_thresholds.py` proves validation-only sweeps run on this hardware). No retraining, no new data, no GPU-days.

The decision layer is also the *measurement instrument* for everything else on the roadmap. A fixed model behind a leaked, 96%-blind alert policy is invisible to operators; an improved model measured by a biased yardstick is unpublishable. This work item unblocks both.

## Why each other top-ranked bottleneck should wait

**B5 — Aditya-L1 overlap extension (score 7.05).** Highest publication upside, but three reasons to sequence it second. First, its outcome doesn't change what operators see: even a confirmed multi-instrument benefit lands behind the same broken alert layer. Second, it is partially data-uncertain — the extended corpus may still contain few clean joint flare episodes (SoLEXS availability during the largest SC25 events is unaudited), so its expected value has wide error bars, whereas the decision-layer fix has essentially deterministic payoff. Third, its significance testing *needs* the episode-level evaluation harness that Phase 1 builds — doing B5 first means building that harness anyway, inside a bigger and riskier work item.

**B4 — Distribution-shift recalibration (score 6.75).** Genuinely important, but it modifies the calibrator — the one component that is currently clean. Touching it before the threshold layer is honest would stack two changes on the same downstream metrics and make attribution impossible. The decision-layer rebuild also *contains* the cheapest slice of B4: thresholds get re-derived on the most SC25-like validation data available, and the walk-forward backtest design in the roadmap (Phase 3) reuses Phase 1's harness. B4 is the natural Sprint 25 follow-on, not a competitor.

**B9 — Episode-level evaluation harness (score 6.55).** Not deferred — absorbed. It is a mandatory component of the selected improvement (episode metrics are the primary selection criterion for the new thresholds), just not valuable enough standing alone: an honest harness measuring a leaked policy still reports invalid operator numbers.

**B6 — Stealth-flare mitigation (score 5.95).** Requires retraining and re-benchmarking (high cost), and its success metric — stealth-stratum episode recall — literally does not exist yet as a measured quantity until the episode harness lands. Building the yardstick before the intervention is the only defensible order.

**B10 — Engineering hardening (score 4.50).** Auth, Dockerfile, scheduler, and broad test coverage make the system deployable, not correct. Deploying today's policy more robustly would industrialize a scientifically invalid alert layer. The policy-layer regression tests inside Phase 1 are the slice of B10 that can't wait; the rest can run as a parallel non-research track whenever capacity exists.

**B7, B8, B11, B12 (scores ≤ 4.30).** B7 is a one-line fix folded into whichever sprint next touches V3. B8 is contained (isotonic selected and working). B11 is handled by protocol (pinned hardware, archived predictions canonical). B12's remedy — machine-checkable provenance stamps — is built directly into Phase 1's output artifacts rather than pursued separately.

## What "done" means

1. `artifacts/operator_policy_v2.json` exists with embedded provenance (data manifest, script hash, constraint set, selection date) and was derived from validation data only — verifiable from the artifact itself.
2. `app/services/ml/inference.py` loads the v2 policy; the leaked v1 file is archived with a deprecation note, not deleted.
3. Episode-level evaluation is a first-class module with tests, and the single honest test-set evaluation is published with block-bootstrap CIs — including the expected *downward correction* of headline operator metrics, stated plainly.
4. The alert-policy component ablation (thresholds / uncertainty suppression / RED confirmation / coincidence filter) is documented, so future policy changes have a measured baseline per component.

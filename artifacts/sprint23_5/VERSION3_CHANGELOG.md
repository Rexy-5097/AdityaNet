<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Chronological change record for frozen Version 3. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Changelog

**Conclusion:** Version 3's significant changes run from the 2026-06-15 V1 training day through the 2026-07-03 reconciliation. Dates are filesystem mtimes (rsync-preserved) or dated reports.

| Date | Sprint | Change | Key artifacts |
|------|--------|--------|---------------|
| 2026-06-15 13:10–13:19 | 5 | V1 PatchTST trained (epoch 3 best); test predictions saved for calibration analysis | `artifacts/models/patchtst_best.pt`, `artifacts/calibration/probs.npy`/`labels.npy` |
| 2026-06-15 19:25 | 5 | Isotonic calibrator fit on validation, selected on validation Brier | `artifacts/calibrator.pkl`, `artifacts/calibration/calibration_report.json` |
| 2026-06-15 19:54 | 5.5 | Operator thresholds yellow=0.46/red=0.88 selected — **on test-set predictions (the leak)** — and deployed as production default | quarantined: `artifacts/archive/operator_thresholds.json` |
| 2026-06-15 20:00 | 5.5 | Operator readiness evaluated at leaked thresholds (trust 0.524, precision 91.12%, recall 3.97% — void) | `artifacts/operator_readiness_report.json` |
| 2026-06-15 20:11–20:31 | 5.6 | Leak internally detected; validation-only thresholds computed (yellow=0.14/red=0.95) — **never deployed** | `artifacts/operator_thresholds_validation_only.json`, `scripts/refine_thresholds.py`, `artifacts/operator_trust_audit.json` |
| 2026-06-15 (evening) | 5.6–7 | Honest backtest of validation-only policy; bootstrap CIs; trust projections | `artifacts/operator_backtest.json`, `artifacts/bootstrap_metrics.json`, `artifacts/operator_trust_projection.json` |
| 2026-06 (mid) | 5.7–10L | Failure-mode analysis (stealth-flare FNs, post-flare-decay FPs); architecture ceiling audit; operator-trust inventories and repository fingerprints — all expressed at the leaked operating points | `artifacts/model_failure_evidence_report.md`, `artifacts/sprint10h5/`, `artifacts/sprint10k/`, `artifacts/sprint10l/` |
| 2026-06 (mid) | 14b | Publication-oriented ablation study and results tables (cite leaked-policy values — annotated INVALIDATED in Sprint 23.5) | `artifacts/sprint14b/` |
| 2026-06-19–21 | 14c | V3 LateFusionPatchTST implemented and trained (two-stage transfer learning, seed 42); S2 evaluation TSS 0.384 isotonic | `app/services/ml/model_v3.py`, `artifacts/sprint14c/` |
| 2026-06-21 | — | Independent scientific validation of V3 pipeline (benchmark NOT CERTIFIED; MPS float variance; 8-minute split-boundary mismatch) | `scientific_validation_report.md` |
| 2026-06 (late) | 15a–21a | Explainability samples, analogue retrieval casebook, stability audits, sprint verification passes | `operator_casebook.md`, `artifacts/sprint15b/`, `analogue_retrieval.json` |
| 2026-06 (late) | 18a–20b | Independent validation reports; Sprint 20B concluded **FAIL** (parameter miscounts, inventory omission) contradicting its own summary JSON | `validation_report_18a.md` … `validation_report_20b.md` |
| 2026-07-01 | — | Repository migrated to external SSD via rsync -a (timestamps preserved); confirmed not a git repository | `MIGRATION_REPORT.md` |
| 2026-07-01 | — | Read-only onboarding audit; `PROJECT_STATUS.md` written (thresholds 0.46/0.88 then believed production-legitimate) | `PROJECT_STATUS.md` |
| 2026-07-03 (morning) | — | AgentOS v1.0.0 governance installed; `adityanet` profile; context files populated | `AGENTOS.md`, `PROJECT_CONFIG.yaml`, `context/` |
| 2026-07-03 (midday) | 22 | Research planning: six documents; decision-layer rebuild selected as highest-value improvement; threshold provenance question surfaced | `artifacts/sprint22/` |
| 2026-07-03 14:35 | 22.5 | Forensic investigation; **LEAKAGE PROVEN** (all four conditions confirmed; exact six-decimal reproduction of deployed metrics from test arrays) | `artifacts/sprint22_5/` incl. `FINAL_VERDICT.md` |
| 2026-07-03 18:48–18:58 | 23 | Versioned policy system built (`policy.py`); leaked artifacts quarantined; Sprint 5.6 policy promoted to `operator_policy_v2.0.0` and deployed in `inference.py`; first test suite (15 regression + integration, all green); five quality gates passed | `app/services/ml/policy.py`, `artifacts/policies/`, `artifacts/archive/`, `tests/`, `artifacts/sprint23/` |
| 2026-07-03 (evening) | 23.5 | Repository reconciled: stale documents annotated (VERSION STATUS blocks), `PROJECT_STATUS.md` restructured (Current/Historical/Archived), six lock documents + scientific timeline written, open items tagged `[V4]`; **Version 3 frozen** | `artifacts/sprint23_5/`, annotated docs repository-wide |

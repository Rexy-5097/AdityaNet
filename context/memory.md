<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Living context document; pre-Sprint-23 statements presenting thresholds 0.46/0.88 as production were stale and are corrected inline below with [SUPERSEDED — Sprint 23] markers; original text preserved. -->
<!-- SUPERSEDED BY: Sprint 23 (artifacts/policies/operator_policy_v2.json); proof: artifacts/sprint22_5/FINAL_VERDICT.md; clean baseline: artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md -->
<!-- DATE: 2026-07-03 -->

# Project Memory — SuryaNet / AdityaNet

> **Purpose:** Persistent facts that must survive session boundaries — lessons learned, validated choices, anti-patterns
> **Owner:** All agents (write on discovery) · All agents (read every session)
> **Cross-refs:** `context/state.md` · `context/decisions.md`

---

## Validated Choices (Do These Again)

| Choice | Evidence | Context |
|--------|----------|---------|
| Isotonic regression > temperature scaling | Temperature scaling at T=1.4168 yields TSS=0.00 on V3 test set — it shifts the probability distribution but destroys the decision boundary | V3 calibration, scientific_validation_report.md §4 |
| Chronological split over random shuffle | TSS inflates significantly with random shuffle (cross-contamination of adjacent windows) | train_test_boundary_audit.json: PASS |
| History features are the dominant signal | Information gap audit: removing history features collapses TSS to 0.0 (vs baseline 0.38) | artifacts/information_gap_report.json |
| MC Dropout with 50 passes | Provides stable uncertainty estimate; 50 is sufficient for operational use; more doesn't meaningfully change std_prob | inference.py empirical observation |
| Per-instrument encoders (late fusion) | Allows graceful degradation; V3 Scenario B (GOES-only) still achieves TSS=0.405 vs 0.413 full model | scientific_validation_report.md §6 |

---

## Anti-Patterns (Never Do These)

| Anti-Pattern | Why | What Happened |
|-------------|-----|---------------|
| Using model_v3.py defaults for feature counts | Defaults say n_features_solexs=25, n_features_hel1os=10; trained checkpoint is 18 and 4; loading raises shape mismatch | BUG-001 |
| Reporting model parameters by counting model.parameters() only | Positional encoding buffers are stored in checkpoint but not counted by model.parameters() — actual checkpoint param count is higher (V3: +20,160; V1: +5,760) | Sprint 20B validation FAIL |
| Using calibration_report.json thresholds in production | These are yellow=0.09/red=0.19 from an older calibration run — production uses 0.46/0.88 *[SUPERSEDED — Sprint 23: production now uses 0.14/0.95 from artifacts/policies/operator_policy_v2.json; 0.46/0.88 were proven test-leaked and quarantined]* | CONFLICT-002 |
| Consuming any policy file via raw json.load | Bypasses the Sprint 23 leakage guard and provenance checks — always go through app/services/ml/policy.py | Sprint 23 |
| Claiming V3 improves over GOES-only without joint flare evidence | Ablation shows TSS gap of only 0.008 on a test set with 11.92% positive rate; the joint overlap dataset has zero flare events | SCI-001 open |
| Random test window selection for evaluation | Must use contiguous chronological test set (2023–2026 for V1, Dec 2025–Jun 2026 for V3) | data integrity requirement |
| Forward-filling NaN flux values before the sliding window starts | fill NaN within the window only, not globally — global fill can corrupt the first window of a new orbit/downlink gap | inference.py NaN handling |

---

## Key Numerical Facts (Verified, Version-Locked)

| Fact | Value | Source | Version |
|------|-------|--------|---------|
| V1 TSS at production thresholds (bootstrap 95% CI) | [0.369, 0.393] | artifacts/bootstrap_metrics.json | V1 patchtst_best.pt epoch 3 |
| V1 TSS at eval threshold (0.3367) | 0.2298 | artifacts/evaluation_audit_report.json | V1 patchtst_best.pt epoch 3 |
| V1 Recall at eval threshold | 0.9286 | artifacts/evaluation_audit_report.json | — |
| V1 PR-AUC (raw) | 0.4950 | artifacts/evaluation_audit_report.json | — |
| V1 ECE post-calibration | 0.0876 | artifacts/calibration/calibration_report.json | — |
| V3 TSS (isotonic calibrated, S2 test) | 0.3840 | artifacts/sprint14c/test_results_model_D_seed_42.json | seed=42, stage2_best |
| V3 ECE post-calibration | 0.0420 | same | — |
| V3 best validation TSS | 0.4644 | same | — |
| Positive rate SC24 train | 0.62% | artifacts/research_dataset_report.json | — |
| Positive rate SC25 test | 23.2% | artifacts/research_dataset_report.json | — |
| Overlap dataset flare events | 0 (zero) | artifacts/aditya_l1/overlap_dataset.parquet | Jun 2026 |
| ~~Production thresholds~~ **[SUPERSEDED — Sprint 23: test-leaked, quarantined]** | ~~yellow=0.46, red=0.88~~ | artifacts/archive/operator_thresholds.json (was artifacts/operator_thresholds.json) | pre-Sprint-23 |
| Production thresholds (current) | yellow=0.14, red=0.95 | artifacts/policies/operator_policy_v2.json | Sprint 23 |
| Honest operator backtest at current thresholds | TSS 0.3817, Recall 0.7227, EventRecall 0.6963, RED alerts 0 | artifacts/operator_backtest.json | Sprint 5.6/23 |
| Uncertainty suppression tiers | unc>0.20→GREEN; unc>0.15→floor GREEN; unc>0.10→cap YELLOW | app/services/ml/inference.py | — |
| V1 parameters (trainable) | 822,401 | model.py | — |
| V1 parameters (checkpoint total with PE buffers) | 828,161 | patchtst_best.pt | — |
| V3 parameters (trainable) | 4,353,217 | trainer_v3.py | — |
| V3 parameters (checkpoint total with PE buffers) | 4,373,377 | sprint14c checkpoints | — |

---

## Open Questions (Unresolved, Don't Assume Answers)

| ID | Question | Last Status |
|----|----------|-------------|
| SCI-001 | Do SoLEXS/HEL1OS provide statistically significant benefit on flare windows? | UNRESOLVED — 4 days overlap, zero flares |
| SCI-002 | Was calibrator.pkl fit on validation or test data? | UNVERIFIED — probs.npy has 1,806,313 rows = test set size |
| SCI-003 | How does the model hold up across SC24→SC25 cycle transition? | UNRESOLVED — distribution shift unaddressed |

---

*Last updated: 2026-07-03 · AgentOS onboarding*

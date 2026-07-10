# Sprint 22 — Scientific Baseline

**Conclusion:** SuryaNet is a two-model system whose research layer is methodologically strong (clean chronological splits, validation-fit calibration, extensive audits) but whose operational decision layer is scientifically compromised: the production alert thresholds in `artifacts/operator_thresholds.json` were selected on the test set (`scripts/optimize_operational_policy.py:6`), and the validation-only replacement computed in Sprint 5.6 was never deployed. Every claim below cites its repository evidence.

---

## 1. Production Architecture (V1 — ACTIVE)

| Property | Value | Evidence |
|----------|-------|----------|
| Model | PatchTST with CLS token, 4 layers, 8 heads, embed=128, dropout=0.2 | `app/services/ml/model.py` |
| Input | [B, 360, 14] — 360-minute window, 14 GOES features | `app/services/ml/model.py` (SEQ_LEN=360, N_FEATURES=14) |
| Patching | 44 overlapping patches (patch_len=16, stride=8) + CLS = 45 tokens | `app/services/ml/model.py` |
| Parameters | 822,401 trainable; 828,161 in checkpoint (PE buffers) | `validation_report_20b.md` §2 |
| Checkpoint | epoch 3 | `artifacts/models/patchtst_best.pt` |
| Uncertainty | MC Dropout, 50 forward passes → mean_prob, std_prob | `app/services/ml/model.py` (`predict_with_uncertainty`) |
| Serving | Loads V1 + `artifacts/calibrator.pkl` + `artifacts/operator_thresholds.json` | `app/services/ml/inference.py` |
| API | POST `/predict/nowcast`, 360–362 flux records | `app/api/v1/endpoints/inference.py` |

## 2. Research Architecture (V3 — NOT DEPLOYED)

| Property | Value | Evidence |
|----------|-------|----------|
| Model | LateFusionPatchTST: 3 asymmetric encoders + cross-attention fusion | `app/services/ml/model_v3.py` |
| Inputs | GOES 14 / SoLEXS 18 / HEL1OS 4 features + availability masks | `artifacts/feature_columns_v3.json` |
| Known defect | `model_v3.py` defaults declare SoLEXS=25, HEL1OS=10 — incompatible with trained checkpoint (18/4); shape mismatch on load | `app/services/ml/model_v3.py` vs `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` (patch_embed_solexs.projection.weight [160,288]=18×16; hel1os [160,64]=4×16) |
| Parameters | 4,353,217 trainable; 4,373,377 in checkpoint | `artifacts/sprint14c/experiment.log`; `validation_report_20b.md` §2 |
| Missing data | Learnable missing tokens per instrument | `app/services/ml/model_v3.py` (`missing_token_solexs`, `missing_token_hel1os`) |
| Training | Stage 1: GOES encoder pretrain (SC24); Stage 2: full fine-tune (Aditya-L1 overlap era) | `app/services/ml/trainer_v3.py`; `artifacts/sprint14c/experiment.log` |

## 3. Datasets

| Split | Rows | Period | Positive Rate | Evidence |
|-------|------|--------|---------------|----------|
| V1 train | 5,161,312 | 2010-01-02 → 2019-12-31 (SC24) | 0.62% | `artifacts/research/train.parquet`; `artifacts/sprint14c/experiment.log` |
| V1 val | 1,568,759 | 2020 → 2022 | 4.07% | `artifacts/research/validation.parquet` |
| V1 test | 1,806,673 | 2023 → 2026-06-14 (SC25 max) | 23.20% | `artifacts/research/test.parquet`; `artifacts/evaluation_audit_report.json` |
| V3 S2 train | 785,938 | 2023-12-13 → 2025-06-14 | 31.37% | `artifacts/sprint14c/s2_train.parquet`; `experiment.log` |
| V3 S2 val | 262,120 | 2025-06-15 → 2025-12-14 | 16.57% | `artifacts/sprint14c/s2_val.parquet` |
| V3 S2 test | 261,095 | 2025-12-15 → 2026-06-14 | 11.92% | `artifacts/sprint14c/s2_test.parquet` |
| GOES+Aditya-L1 overlap | 5,760 (4 days) | 2026-06-10 → 06-13 | **0.00% — zero flares** | `artifacts/aditya_l1/overlap_dataset.parquet` |

Split hygiene is verified: chronological boundaries with 60-second gaps (`artifacts/aditya_l1/train_test_boundary_audit.json` — PASS) and no cross-split window overlap (`artifacts/aditya_l1/window_overlap_audit.json` — PASS).

## 4. Feature Engineering

14 GOES features: short/long flux, log long flux, rolling mean/variance (15m, 60m), peaks (30m, 60m), gradients (5m, 15m), accelerations (5m, 15m), `minutes_since_last_flare` capped at 10,080 min — `app/services/ml/features.py`; manifest `artifacts/feature_columns.json`. The information gap audit shows history features are the dominant signal: removing them collapses TSS from 0.382 to 0.000 (`artifacts/information_gap_report.json`); history-only achieves TSS 0.371 (`artifacts/signal_audit_report.json`).

## 5. Training Pipeline

V1: FocalLoss(γ=2.0, α=pos_rate), AdamW, CosineAnnealingLR, WeightedRandomSampler, early stop on val TSS — `app/services/ml/trainer.py`, `scripts/train_patchtst.py`. V3 adds two-stage transfer learning with freeze/unfreeze and optimizer rebuild — `app/services/ml/trainer_v3.py`. Sprint 20B audit found Stage 1/2 learning rates constant (1e-4 / 5e-5, no scheduler stepped) — `validation_report_20b.md` §1.

## 6. Calibration Pipeline (V1)

**Clean.** `scripts/calibrate_model.py` fits Platt and isotonic calibrators on validation predictions (lines 191–202: `isotonic_calib.fit(val_probs, val_labels)`), selects the winner on validation Brier (lines 222–262), and evaluates on saved test probs only for reporting. Isotonic won: test Brier 0.237→0.159, ECE 0.272→0.088 (`artifacts/calibration/calibration_report.json`).

## 7. Threshold / Alert Policy Pipeline

**Compromised.** Three generations exist:

| File | Values | Provenance | Status |
|------|--------|------------|--------|
| `artifacts/calibration/calibration_report.json` → `operational_thresholds` | yellow=0.09, red=0.19 | Validation sweep in `calibrate_model.py` (Sprint 5) | Superseded |
| `artifacts/operator_thresholds.json` | yellow=0.46, red=0.88 + uncertainty tiers 0.10/0.15/0.20 | **Test-set sweep** — `scripts/optimize_operational_policy.py:6` ("Sweeps calibrated probability thresholds on the saved test-set probabilities"), reads `artifacts/calibration/probs.npy`/`labels.npy` (test predictions, N=1,806,313) | **DEPLOYED — loaded by `app/services/ml/inference.py`** |
| `artifacts/operator_thresholds_validation_only.json` | yellow=0.14, red=0.95 | Validation-only rerun, Sprint 5.6 — `scripts/refine_thresholds.py` (explicitly excludes test files, lines 63–68) | Computed, **never deployed** |

## 8. Evaluation Methodology

- Window-level metrics at stride-1 (heavily autocorrelated samples): TSS, HSS, MCC, ECE, PR-AUC, Brier — `app/services/ml/metrics.py` (`compute_full_suite`)
- V1 full-test audit verified across 3 independent passes: ROC-AUC 0.7485, PR-AUC 0.4950, TSS 0.2298 @ t=0.3367 — `artifacts/evaluation_audit_report.json`
- Bootstrap 95% CI at operator thresholds: TSS [0.369, 0.393] — `artifacts/bootstrap_metrics.json` (but thresholds themselves were test-tuned; see §7)
- Episode-level evaluation exists once (Sprint 5.5): 77 episodes, 91.1% precision, **3.97% recall**, trust score 0.524 — `artifacts/operator_readiness_report.json`
- V3: TSS 0.384 isotonic-calibrated on S2 test; ablation shows GOES-only TSS 0.405 vs full 0.413 — `artifacts/sprint14c/test_results_model_D_seed_42.json`; `scientific_validation_report.md` §6

## 9. Deployment Assumptions

FastAPI + TimescaleDB (Docker, port 5433) + Redis — `docker-compose.yml`, `app/main.py`, `app/core/config.py`. No app Dockerfile, no auth, no scheduler, no tests, no git — absence verified in `PROJECT_STATUS.md` §Backend/§Deployment. Inference assumes 360 contiguous 1-minute GOES records plus a 7-day flare-history DB query — `app/api/v1/endpoints/inference.py`.

## 10. Known Limitations (with evidence)

1. **Production thresholds are test-leaked** — `scripts/optimize_operational_policy.py` docstring + `PROBS_PATH = artifacts/calibration/probs.npy`.
2. **Operational recall 3.97%** at deployed thresholds — `artifacts/operator_readiness_report.json`.
3. **Aditya-L1 benefit unproven** — ablation gap 0.008 TSS (`scientific_validation_report.md` §6); joint overlap has zero flares (`artifacts/aditya_l1/overlap_dataset.parquet`); conditional mutual information of Aditya-L1 features given GOES ≈ 0 (`artifacts/aditya_l1/incremental_information_audit.json`).
4. **SC24→SC25 distribution shift** — 0.62% → 23.2% positive rate (`artifacts/research_dataset_report.json`).
5. **Temperature scaling fails** — TSS=0.000 at fitted T=1.4168 (`scientific_validation_report.md` §2).
6. **FN failure mode: stealth flares** from quiet backgrounds (mean 3,489 min since last flare), diffuse attention (entropy≈1.0); FP mode: post-flare decay elevations — `artifacts/model_failure_evidence_report.md`.
7. **MPS non-determinism across platforms** — max |Δ| 9.76e-4 vs saved predictions — `scientific_validation_report.md` §3.
8. **Sprint 20B self-report contradicts audit** — `artifacts/sprint20b/sprint20b_summary.json` says PASS; `validation_report_20b.md` concludes FAIL (parameter counts, missing `scripts/train_baseline.py` from inventory).

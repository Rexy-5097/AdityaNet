# Project Status

**Generated:** 2026-07-01  
**Auditor:** Read-only repository reconstruction  
**Method:** Direct source code, checkpoint, dataset, and artifact inspection  
**Authority:** Repository source code supersedes all documentation where conflicts exist

---

## Repository Overview

**Repository directory:** `/Users/soumyadebtripathy/AdityaNet`  
**Git status:** NOT a git repository (no `.git` directory found)  
**Project name in code:** SuryaNet (README says "SuryaNet: Physics-Informed Solar Flare Forecasting and Space Weather Intelligence Platform")  
**Directory name:** AdityaNet  
**CONFLICT:** The working directory is named "AdityaNet" but all source code, documentation, config, and README refer to the project as "SuryaNet". These are used interchangeably throughout the repository with no canonical resolution.

**Repository size:** ~29 GB total; ~3.7 GB parquet datasets; ~296 MB model checkpoints  
**Source files:** 286 Python, 1,235 JSON, 60 Markdown, 10 Shell, 1 INI  
**Runtime environment (observed):** Python 3.14.4, PyTorch 2.9.1, macOS Darwin 25.5.0, Apple M4 (MPS accelerator)  
**Historical training environment (per sprint20b):** Python 3.12.12, PyTorch 2.12.0, macOS 26.5.1

---

## Problem Statement

**VERIFIED** from README and source code:

SuryaNet aims to forecast M-class and X-class solar flares 6 hours in advance using:
1. GOES XRS (1-minute cadence X-ray flux data from NOAA geostationary satellites, 2010–2026)
2. SoLEXS (Solar Low Energy X-ray Spectrometer) aboard Aditya-L1, India's first solar mission
3. HEL1OS (High Energy L1 Orbiting X-ray Spectrometer) aboard Aditya-L1

The intended users are satellite operators at ISRO who need operational space weather alerts (GREEN/YELLOW/RED) with 6-hour lead time.

The project targets this operational workflow:
- Ingest real-time GOES XRS telemetry into TimescaleDB
- Run inference every minute using a sliding 360-minute window
- Issue calibrated probability + tiered alert
- Support ISRO mission-specific impact assessment and explainability

---

## Scientific Objective

**VERIFIED** from source code, model architecture, and audit artifacts:

**Primary hypothesis:** Multi-instrument X-ray observations from multiple energy channels (GOES soft/hard X-ray + SoLEXS EUV/soft X-ray + HEL1OS hard X-ray) can predict M/X-class solar flares 6 hours ahead with better accuracy than GOES alone.

**Why GOES:** The longest solar observation archive (16 years, 2010–2026), 1-minute cadence, two X-ray channels (0.05-0.4 nm short, 0.1-0.8 nm long). Standard operational tool for space weather.

**Why SoLEXS:** Provides soft X-ray spectral coverage from Aditya-L1's L1 vantage point. 9 energy channels. Different viewing geometry than GOES. INFERRED to offer complementary pre-flare chromospheric/coronal temperature information.

**Why HEL1OS:** Provides hard X-ray coverage not available in GOES. Non-thermal emission during flares. INFERRED to give early impulse signals for impulsive-phase flares.

**Why PatchTST:** Patch-based time series transformer with CLS token. Captures local temporal patterns (16-minute patches) and global sequence context simultaneously. Parameter-efficient (<5M parameters). Chosen to model the complex non-stationary X-ray time series.

**Why late fusion:** Each instrument has different cadence, energy range, and missing data patterns. Late fusion allows independent per-instrument encoding then cross-instrument attention, enabling graceful degradation when instruments are unavailable.

**Why missing tokens:** Aditya-L1 data may be unavailable due to orbital constraints, downlink gaps, or instrument calibration. Learnable missing tokens allow the model to represent "absence" explicitly rather than assuming zero-fill.

**Why calibration:** Raw model outputs are poorly calibrated (ECE=0.272 before calibration). Satellite operators need trustworthy probability estimates for decision-making. Isotonic regression calibration reduces ECE from 0.272 to 0.088.

**Why uncertainty estimation (MC Dropout):** Single-point predictions are insufficient for operational safety. MC Dropout (50 stochastic forward passes) provides epistemic uncertainty. Alerts are suppressed (RED→YELLOW→GREEN) when uncertainty is high, reducing false alarms.

**EXPERIMENTAL VALIDATION STATUS:**
- Chronological split and leakage audit: VERIFIED PASS
- Calibration on validation data: VERIFIED (operator_thresholds_validation_only.json confirms `"data_used_for_selection": "validation"`)
- Aditya-L1 incremental information: VERIFIED Class C signals (weak but statistically significant across all forecast horizons)
- SoLEXS/HEL1OS ablation: **CRITICAL FINDING** — removing these instruments causes minimal TSS degradation (see Model Audit)
- Multi-instrument fusion benefit: NOT VALIDATED — the V3 model's fusion layers add complexity without demonstrably improving over GOES alone on the S2 test set

---

## Repository Architecture

```
AdityaNet/
├── app/                          IMPLEMENTED — FastAPI backend
│   ├── api/v1/endpoints/         IMPLEMENTED — 5 endpoint groups
│   │   ├── health.py             IMPLEMENTED
│   │   ├── solar.py              IMPLEMENTED (GOES telemetry queries)
│   │   ├── flares.py             IMPLEMENTED
│   │   ├── system.py             IMPLEMENTED
│   │   └── inference.py          IMPLEMENTED (V1 model only)
│   ├── core/config.py            IMPLEMENTED
│   ├── core/redis.py             IMPLEMENTED
│   ├── db/                       IMPLEMENTED
│   ├── models/                   IMPLEMENTED (DB ORM models)
│   └── services/
│       ├── ml/
│       │   ├── model.py          IMPLEMENTED — V1 PatchTST (14 GOES features)
│       │   ├── model_v3.py       IMPLEMENTED — V3 LateFusionPatchTST (DEFAULT PARAMS WRONG - see conflicts)
│       │   ├── trainer.py        IMPLEMENTED — V1 trainer
│       │   ├── trainer_v3.py     IMPLEMENTED — V3 trainer with transfer learning
│       │   ├── dataset.py        IMPLEMENTED — V1 dataset
│       │   ├── dataset_v3.py     IMPLEMENTED — V3 multi-instrument dataset
│       │   ├── features.py       IMPLEMENTED — GOES feature engineering
│       │   ├── inference.py      IMPLEMENTED — ACTIVE service (V1 only)
│       │   ├── evaluator_v3.py   IMPLEMENTED — V3 calibration
│       │   ├── metrics.py        IMPLEMENTED — full metric suite
│       │   ├── explainability.py IMPLEMENTED
│       │   └── config.py         IMPLEMENTED
│       ├── backfill/             IMPLEMENTED
│       └── operations/impact.py  IMPLEMENTED — ISRO mission impact
├── data_pipeline/                IMPLEMENTED
│   ├── download_manager.py       IMPLEMENTED
│   ├── plugins/                  IMPLEMENTED (SoLEXS, HEL1OS, GOES, NOAA stubs)
│   ├── parsers/                  IMPLEMENTED
│   └── processing/               IMPLEMENTED
├── scripts/                      IMPLEMENTED — training, eval, calibration scripts
├── scratch/                      EXPERIMENTAL — audit/verification scripts
├── alembic/                      IMPLEMENTED — DB migrations
├── data/aditya_l1/processed/     POPULATED — raw Aditya-L1 parquets
│   ├── solexs/ (915 files)       POPULATED — Dec 2023 to Jun 2026
│   └── hel1os/ (960 files)       POPULATED — Oct 2023 to Jun 2026
├── artifacts/                    POPULATED — models, datasets, reports
│   ├── models/patchtst_best.pt   V1 CHECKPOINT — 9.96 MB (ACTIVE)
│   ├── models/patchtst_last.pt   V1 CHECKPOINT — 9.96 MB
│   ├── models_v3/test_checkpoint.pt  V3 UNTRAINED — 52.57 MB (epoch=1, best_tss=-1.0)
│   ├── sprint14c/checkpoints/    V3 BEST CHECKPOINTS — 17.57 MB each
│   ├── research/                 V1 DATASETS (train/val/test parquets)
│   ├── research_v3/              V3 DATASETS (train/val/test parquets with Aditya-L1)
│   ├── calibration/              CALIBRATION artifacts
│   └── aditya_l1/                EXTENSIVE AUDIT artifacts
├── legacy/                       HISTORICAL — original PRADAN download scripts
├── docker-compose.yml            IMPLEMENTED — TimescaleDB + Redis
└── requirements.txt              IMPLEMENTED
```

**ABSENT:**
- No frontend (no HTML, JSX, TSX, Vue, or package.json files)
- No test suite (no pytest, unittest, or test files)
- No CI/CD configuration
- No authentication/authorization layer
- No monitoring or alerting
- No real-time GOES data ingestion scheduler (scripts exist but no orchestration)
- No git version control

---

## Dataset Inventory

### GOES XRS Archive

| Property | Value |
|----------|-------|
| Path | `artifacts/raw/goes_{year}.parquet` (2010–2026) |
| Full dataset | `artifacts/research/goes_full.parquet` |
| Total records | 8,631,360 |
| Date range | 2010-01-02 to 2026-06-14 |
| Missing minutes | 20,160 (0.23% gap rate) — ACCEPTABLE |
| Solar Cycle 24 | 2010–2019, 5,237,280 records, 109 M-flares, 4 X-flares |
| Solar Cycle 25 | 2020–2026, 3,394,080 records, 1,945 M-flares, 105 X-flares |

### GOES ML Datasets (V1, GOES-only)

| Split | Path | Rows | Date Range | Positive Rate | Status |
|-------|------|------|------------|---------------|--------|
| Train | `artifacts/research/train.parquet` | 5,161,312 | 2010-01-02 to 2019-12-31 | 0.62% | CANONICAL |
| Validation | `artifacts/research/validation.parquet` | 1,568,759 | 2020-01-01 to 2022-12-31 | 4.07% | CANONICAL |
| Test | `artifacts/research/test.parquet` | 1,806,673 | 2023-01-01 to 2026-06-14 | 23.20% | CANONICAL |

**CRITICAL WARNING:** The positive rate increases from 0.62% (train) to 23.20% (test). This is caused by Solar Cycle 25 being dramatically more active than SC24. The model was trained on SC24 quiet period and is evaluated on the most active period of SC25 solar maximum. This distributional shift makes direct comparison of train/test performance misleading. The model did NOT see data from SC25 active conditions during training.

**Columns per split:** 20 (timestamp, short_flux, long_flux, satellite, quality_flag, source, target_6hr_binary, target_6hr_class, 12 engineered features)

### Multi-Instrument Datasets (V3)

| Split | Path | Rows | Date Range | Positive Rate | GOES cols | SoLEXS cols | HEL1OS cols |
|-------|------|------|------------|---------------|-----------|-------------|-------------|
| Train (S1) | `artifacts/research_v3/train_v3.parquet` | 5,161,312 | 2010-01-02 to 2019-12-31 | 0.62% | 14 | 18 | 4 |
| Val (S1) | `artifacts/research_v3/validation_v3.parquet` | 1,568,759 | 2020-01-01 to 2022-12-31 | 4.07% | 14 | 18 | 4 |
| Train (S2) | `artifacts/sprint14c/s2_train.parquet` | 785,938 | 2023-12-13 to 2025-06-14 | 31.37% | 14 | 18 | 4 |
| Val (S2) | `artifacts/sprint14c/s2_val.parquet` | 262,120 | 2025-06-15 to 2025-12-14 | 16.57% | 14 | 18 | 4 |
| Test (S2) | `artifacts/sprint14c/s2_test.parquet` | 261,095 | 2025-12-15 to 2026-06-14 | 11.92% | 14 | 18 | 4 |

**Note:** S1 = Stage 1 pretraining (GOES encoder only). S2 = Stage 2 fine-tuning (all instruments). SoLEXS columns are all zero-filled for pre-2023 data (SoLEXS didn't exist). HEL1OS same.

### Aditya-L1 Raw Data

| Instrument | Files | Date Range | Path |
|------------|-------|------------|------|
| SoLEXS | 915 files | Dec 2023 – Jun 2026 | `data/aditya_l1/processed/solexs/` |
| HEL1OS | 960 files | Oct 2023 – Jun 2026 | `data/aditya_l1/processed/hel1os/` |

### GOES + Aditya-L1 Overlap Dataset

| Property | Value |
|----------|-------|
| Path | `artifacts/aditya_l1/overlap_dataset.parquet` |
| Rows | 5,760 |
| Date range | 2026-06-10 to 2026-06-13 (4 days only) |
| Positive flare rate | 0.0000 (ZERO positive events) |
| Columns | timestamp, short_flux, long_flux, target_6hr_binary, hel1os_hard_flux_low, hel1os_hard_flux_high, solexs_soft_flux, solexs_gradient_5m, soft_hard_ratio |

**CRITICAL FINDING:** The GOES+SoLEXS+HEL1OS aligned joint evaluation dataset covers only 4 days and contains zero positive flare events. All Aditya-L1 multi-instrument scientific validation was done on this tiny, quiet-sun period. No joint flare events have been observed in the combined GOES+Aditya-L1 dataset.

### Flare Catalog

| Property | Value |
|----------|-------|
| Full catalog | `artifacts/research/flares_full.parquet` |
| Records | 21,945 flare events |
| M-class | 2,054 |
| X-class | 109 |
| Target classes (active) | M and X only |
| Local test DB | 571 records (2015-03-01 to 2026-06-14), only 30 M/X class events |

---

## Model Inventory

### V1 Model — PatchTST GOES-only (ACTIVE IN PRODUCTION)

| Property | Value |
|----------|-------|
| Architecture | PatchTST with CLS token |
| Input | [batch, 360, 14] (360 min × 14 GOES features) |
| Patches | 44 overlapping patches (patch_len=16, stride=8) |
| Encoder | 4 layers, 8 heads, embed_dim=128, FF_dim=512, dropout=0.2 |
| Trainable parameters | 822,401 (4,353,217 including PE buffers: 828,161) |
| Best checkpoint | `artifacts/models/patchtst_best.pt` (9.96 MB) |
| Latest checkpoint | `artifacts/models/patchtst_last.pt` (9.96 MB) |
| Checkpoint format | Keys: `epoch`, `val_tss`, `best_threshold`, `model`, `optimizer`, `scheduler` |
| Epoch saved | 3 |
| Features | 14 GOES features (see feature_columns.json) |
| Status | ACTIVE — loaded by `inference.py` |

### V3 Model — LateFusionPatchTST Multi-Instrument (RESEARCH STAGE, NOT IN PRODUCTION)

| Property | Value |
|----------|-------|
| Architecture | Late Fusion PatchTST with asymmetric encoders |
| Inputs | GOES [batch,360,14] + SoLEXS [batch,360,18] + HEL1OS [batch,360,4] |
| GOES Encoder | 4 layers, embed_dim=128, FF_dim=512 |
| SoLEXS Encoder | 5 layers, embed_dim=160, FF_dim=640 |
| HEL1OS Encoder | 5 layers, embed_dim=160, FF_dim=640 |
| Fusion | Cross-attention on 3×128 projected embeddings |
| Trainable parameters | 4,353,217 (4,373,377 including PE buffers) |
| Best checkpoint (Stage 1) | `artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt` (17.57 MB) |
| Best checkpoint (Stage 2) | `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` (17.57 MB) |
| Checkpoint format | Keys: epoch, model_state_dict, optimizer_state_dict, scheduler_state_dict, scaler_state_dict, best_val_tss, current_epoch |
| Training seed | 42 |
| Status | RESEARCH — not integrated into inference.py |

**CRITICAL CONFLICT — model_v3.py defaults vs. trained checkpoint:**
- `model_v3.py` specifies `n_features_solexs=25` and `n_features_hel1os=10` as defaults
- Checkpoint analysis: `patch_embed_solexs.projection.weight: [160, 288]` → 18 features (288 ÷ 16 patch_len = 18)
- Checkpoint analysis: `patch_embed_hel1os.projection.weight: [160, 64]` → 4 features (64 ÷ 16 = 4)
- Instantiating `LateFusionPatchTST()` with defaults and loading the sprint14c checkpoint will FAIL
- The model was trained with `n_features_solexs=18`, `n_features_hel1os=4` — not documented in model_v3.py defaults

**CONFLICT — `artifacts/models_v3/test_checkpoint.pt` (52.57 MB):**
- Size is 3× larger than the sprint14c checkpoints (likely different architecture)
- Contains: epoch=1, best_val_tss=-1.0
- best_val_tss=-1.0 means the best checkpoint was never updated from initialization
- This is either an aborted training run or a testing artifact
- Status: UNTRAINED / ABANDONED

### Calibrator

| Property | Value |
|----------|-------|
| Path | `artifacts/calibrator.pkl` |
| Method | Isotonic Regression |
| Fit dataset | UNVERIFIED (calibration_audit.json shows n=1,806,313 which matches test set; operator_thresholds_validation_only.json shows calibrator was selected using validation data) |
| Raw ECE → Calibrated ECE | 0.272 → 0.088 (VERIFIED from calibration_audit.json) |
| Raw Brier → Calibrated Brier | 0.237 → 0.159 (VERIFIED) |

**UNVERIFIED CONCERN:** `artifacts/calibration/probs.npy` and `artifacts/calibration/labels.npy` have 1,806,313 samples matching the test set size. If the calibrator was fit on these, that constitutes calibration leakage. The `operator_thresholds_validation_only.json` suggests calibration was selected using validation, but the source of `calibration/*.npy` is ambiguous. NOT CONFIRMED EITHER WAY.

---

## Training Pipeline

### V1 Pipeline (IMPLEMENTED, VERIFIED EXECUTED)

```
GOES raw parquets (2010–2026)
    ↓ scripts/build_research_dataset.py
Train/Val/Test chronological split (2010–2019 / 2020–2022 / 2023–2026)
    ↓ app/services/ml/features.py :: compute_features()
14 GOES features (raw flux, log, rolling stats, gradients, event distance)
    ↓ app/services/ml/dataset.py :: SolarFlareWindowDataset
Sliding 360-min windows, weighted sampler (class balancing)
    ↓ scripts/train_patchtst.py + app/services/ml/trainer.py
PatchTST training (AdamW, CosineAnnealingLR, FocalLoss, 3 epochs)
    ↓ scripts/calibrate_model.py
Isotonic regression calibration on validation predictions
    ↓ scripts/refine_thresholds.py
Threshold optimization on validation (yellow/red)
    ↓ artifacts/models/patchtst_best.pt + artifacts/calibrator.pkl
```

### V3 Pipeline (IMPLEMENTED, VERIFIED EXECUTED via sprint14c/experiment.log)

```
GOES + Aditya-L1 parquets (processed)
    ↓ scripts/build_multi_instrument_dataset.py
Stage 1 data (research_v3): GOES+SoLEXS+HEL1OS (2010–2022, SoLEXS/HEL1OS zero-filled pre-2023)
Stage 2 data (sprint14c): Real Aditya-L1 overlap (Dec 2023 – Jun 2026)
    ↓ app/services/ml/dataset_v3.py :: SolarFlareMultiWindowDataset
18 SoLEXS + 4 HEL1OS + 14 GOES features per window
    ↓ scratch/run_sprint14c_experiment.py
Stage 1: GOES encoder pretrained (SoLEXS/HEL1OS frozen) on Stage 1 data
Stage 2: Full model fine-tuned on Stage 2 Aditya-L1 data (all encoders unfrozen)
    ↓ artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt
V3 evaluation with isotonic calibration
    ↓ test_results_model_D_seed_42.json
```

**TRAINING HYPERPARAMETERS (V3, from experiment.log):**
- Stage 1 LR: constant 1e-4 (confirmed by sprint20b: no scheduler instantiated)
- Stage 2 LR: constant 5e-5
- Batch size: 64
- Weighted random sampler (class balancing)
- Focal Loss alpha = pos_rate (0.0062 for Stage 1)
- Total V3 params: 4,353,217 trainable

---

## Evaluation Pipeline

### V1 Evaluation (IMPLEMENTED, VERIFIED)

**Test set:** 2023-01-01 to 2026-06-14 (1,806,313 windows)  
**Positive rate:** 23.20%  
**Threshold used:** 0.3367 (optimized on validation)

Metrics verified independently across three runs (original, recomputed, fresh inference) — all match:

| Metric | Value | Status |
|--------|-------|--------|
| ROC-AUC | 0.7485 | VERIFIED |
| PR-AUC | 0.4950 | VERIFIED |
| TSS | 0.2298 | VERIFIED |
| Recall (POD) | 0.9286 | VERIFIED |
| POFD | 0.6988 | VERIFIED |
| Precision | 0.2865 | VERIFIED |
| FAR | 0.7135 | VERIFIED |
| F1 | 0.4379 | VERIFIED |
| Brier (raw) | 0.2365 | VERIFIED |
| ECE (raw) | 0.2722 | VERIFIED |
| Brier (isotonic) | 0.1594 | VERIFIED |
| ECE (isotonic) | 0.0876 | VERIFIED |

**Confusion matrix (threshold 0.3367):** TP=389,229, FP=969,386, FN=29,921, TN=417,777

**Bootstrap 95% CI (TSS at operator thresholds):** [0.369, 0.393]

### V3 Evaluation (IMPLEMENTED, VERIFIED via scientific_validation_report.md)

**Test set:** Stage 2 test (2025-12-15 to 2026-06-14, 261,095 windows)  
**Positive rate:** 11.92%

| Metric | Raw | Isotonic Calibrated | Temperature Scaled |
|--------|-----|---------------------|-------------------|
| ROC-AUC | 0.7404 | 0.7398 | 0.7404 |
| PR-AUC | 0.4522 | 0.4259 | 0.4522 |
| TSS | 0.3689 | 0.3840 | 0.0000 |
| Precision | 0.2424 | 0.3580 | N/A |
| Recall | 0.6391 | 0.5070 | N/A |
| F1 | 0.3515 | 0.4196 | N/A |
| Brier | 0.1359 | 0.0887 | 0.1606 |
| ECE | 0.2273 | 0.0420 | 0.2751 |

**Best validation TSS:** 0.4644 (at threshold 0.3169 on S2 val)  
**Temperature scaling:** T=1.4168 (VERIFIED from validation)

**V3 Ablation (SoLEXS/HEL1OS contribution):**

| Scenario | TSS | ROC-AUC | PR-AUC |
|----------|-----|---------|--------|
| Full Model (GOES+SoLEXS+HEL1OS) | 0.4131 | 0.7402 | 0.4495 |
| GOES Only | 0.4046 | 0.7416 | 0.4500 |
| GOES + SoLEXS | 0.4003 | 0.7406 | 0.4499 |
| GOES + HEL1OS | 0.3793 | 0.7414 | 0.4497 |

**CRITICAL FINDING:** SoLEXS and HEL1OS provide minimal additional predictive value over GOES alone. GOES-only achieves 97.95% of the full model's TSS. Adding SoLEXS alone decreases TSS by 3% vs GOES-only. Adding HEL1OS alone decreases TSS by 8.2%. The multi-instrument fusion hypothesis is NOT validated by this evidence on the S2 test set.

**V3 Reproducibility:** Minor floating-point differences on MPS hardware (max diff 9.76e-4) — CONFIRMED NOT deterministic across hardware platforms but deterministic within the same platform (SHA256 hashes matched across 3 runs on same hardware).

### Operator-Level Metrics (V1, Sprint 5.5)

Evaluated with thresholds yellow=0.46, red=0.88 on the test set:

| Metric | Value |
|--------|-------|
| Operator Trust Score | 0.524 |
| Operator Readiness Score | 1.0 |
| Criteria Passed | 3/5 |
| Precision (all alerts) | 91.12% |
| Recall | 3.97% |
| TSS | 0.039 |
| False Alarm Ratio | 8.88% |
| F1 | 0.076 |
| ROC-AUC | 0.745 |
| Avg Lead Time | 10.16 hours |
| Alert Episodes | 77 (70 true, 7 false) |
| False Episode Rate | 9.1%/month |

Note: The extremely high precision (91%) is achieved only by being very conservative (red threshold=0.88 + uncertainty suppression), resulting in near-zero recall (3.97%). The system as deployed at these thresholds misses 96% of actual flares.

---

## Backend Status

| Component | Status | Evidence |
|-----------|--------|---------|
| FastAPI application | IMPLEMENTED | `app/main.py` |
| Health endpoint (`/health`) | IMPLEMENTED | `app/api/v1/endpoints/health.py` |
| Solar data endpoint (`/solar`) | IMPLEMENTED | `app/api/v1/endpoints/solar.py` |
| Flare events endpoint (`/flares`) | IMPLEMENTED | `app/api/v1/endpoints/flares.py` |
| System status endpoint (`/system`) | IMPLEMENTED | `app/api/v1/endpoints/system.py` |
| Inference endpoint (`/predict/nowcast`) | IMPLEMENTED (V1 only) | `app/api/v1/endpoints/inference.py` |
| TimescaleDB (PostgreSQL) | IMPLEMENTED | `docker-compose.yml`, `alembic/` |
| Redis caching | IMPLEMENTED | `app/core/redis.py` |
| DB migrations | IMPLEMENTED | `alembic/versions/a541577be3f5_add_goes_flare_and_ingestion_tables.py` |
| GOES data backfill | IMPLEMENTED | `app/services/backfill/goes_backfill.py` |
| Flare event backfill | IMPLEMENTED | `app/services/backfill/flare_backfill.py` |
| Authentication | ABSENT | No auth middleware found |
| Real-time ingestion scheduler | ABSENT | Scripts exist but no cron/scheduler |
| Monitoring / alerting | ABSENT | No metrics endpoint, no alerting |
| Rate limiting | ABSENT | |
| HTTPS/TLS | ABSENT | Config shows HTTP only |

**NOTE:** The `uvicorn.log` and `uvicorn_sprint35.log` files exist at root level, indicating the server has been started previously. The API is runnable but requires Docker (for TimescaleDB + Redis) plus data backfill before the inference endpoint works.

---

## Frontend Status

**ABSENT.** No frontend code exists anywhere in the repository. There are no HTML files, JavaScript/TypeScript files, React/Vue components, package.json, or any browser-facing code. The project has a backend API but no user interface.

---

## Deployment Status

| Component | Status |
|-----------|--------|
| Docker Compose (TimescaleDB + Redis) | IMPLEMENTED |
| Container for the FastAPI app | ABSENT (no Dockerfile) |
| Cloud deployment | ABSENT |
| CI/CD | ABSENT |
| Environment configuration | IMPLEMENTED (`.env.example`, pydantic-settings) |
| Alembic migrations | IMPLEMENTED |

The project is deployable locally only via: activate venv → start docker-compose → run alembic → run uvicorn. No automated deployment pipeline exists.

---

## Verified Performance

### V1 Model (Primary, Active)

**On full test set (2023–2026), verified across 3 independent evaluations:**
- ROC-AUC = 0.7485 ± (no CI on this metric from saved artifacts)
- PR-AUC = 0.4950
- TSS = 0.230 at threshold 0.337
- TSS = 0.381–0.393 at operator thresholds (bootstrap 95% CI)

### V3 Model (Research)

**On S2 test set (Dec 2025–Jun 2026, 11.92% positive rate):**
- ROC-AUC = 0.7398, PR-AUC = 0.4259, TSS = 0.384 (isotonic calibrated)

### Baselines

| Metric | Signal-only Model | TSS | Notes |
|--------|-------------------|-----|-------|
| History-only (no flux) | ablation_history | 0.0 | TSS collapse |
| Engineered-only | ablation_engineered | 0.0 | TSS collapse |
| Long flux only | ablation_long_flux | 0.060 | Severe degradation |
| Flux without history | similar to baseline | ~0.37 | Minor loss |

---

## Historical Corrections

The following inconsistencies and corrections are documented within the repository:

1. **Sprint 20B: model_v3.py default parameter count mismatch**  
   Reports claim 4,353,217 parameters. Actual state_dict loaded from disk sums to 4,373,377 (difference = positional encoding buffers not counted as trainable). VERIFIED: buffers exist in checkpoint.

2. **Sprint 20B: missing training script**  
   `scripts/train_baseline.py` (Logistic Regression baseline) was omitted from Sprint 20A's corrected inventory.

3. **Sprint 20B validation verdict conflict**  
   `sprint20b_summary.json` reports `"validation_verdict": "PASS"`. Validation report 20b.md concludes `## Overall Status: FAIL`. The FAIL verdict is supported by the script omission and parameter count errors. The `sprint20b_summary.json` verdict is INCORRECT.

4. **Operator threshold conflict (THREE sets exist)**:
   - `artifacts/calibration/calibration_report.json`: yellow=0.09, red=0.19
   - `artifacts/operator_thresholds_validation_only.json`: yellow=0.14, red=0.95
   - `artifacts/operator_thresholds.json` (used in production): yellow=0.46, red=0.88
   These represent three different optimization passes. The production thresholds (0.46/0.88) result in 91% precision but only 3.97% recall. NOT RESOLVED in code.

5. **Sprint 5.7 threshold conflict with production**:  
   Model failure report (Sprint 5.7) uses yellow=0.14 thresholds (from validation-only). Production inference.py uses 0.46. Results are not comparable.

6. **V3 feature count defaults conflict with checkpoint**:  
   `model_v3.py` defaults: `n_features_solexs=25`, `n_features_hel1os=10`. Actual trained checkpoint: SoLEXS=18, HEL1OS=4. Loading with defaults will raise a shape mismatch error.

7. **Scientific validation report S2 test end time mismatch**:  
   Protocol specifies end at 2026-06-14 23:59; actual test set ends 2026-06-14 23:51. An 8-minute discrepancy. Flagged as WARNING by the validation report.

---

## Outstanding Issues

### Scientific

1. **SoLEXS/HEL1OS minimal contribution**: Full V3 model provides only 0.85% TSS improvement over GOES-only. This undermines the scientific rationale for Aditya-L1 multi-instrument fusion. NOT RESOLVED.

2. **Solar cycle distribution mismatch**: Train (SC24, 0.62% positive) vs test (SC25, 23.2% positive). The model's calibration, threshold selection, and performance statistics are influenced by this drift. NOT RESOLVED.

3. **Temperature scaling failure**: Temperature scaling yields TSS=0.00 on V3 test set (temperature=1.4168 shifts predictions but fails to preserve decision boundary). Isotonic regression is the only viable calibration. NOT FULLY EXPLAINED.

4. **Zero positive events in overlap dataset**: The GOES+Aditya-L1 joint evaluation window (4 days, Jun 2026) contains no M/X flares. Scientific claim that Aditya-L1 improves forecasting cannot be validated without joint flare events. NOT RESOLVED.

5. **Flat attention entropy in false negatives**: Attention maps show near-uniform entropy (0.999999) for false negative cases. The model assigns nearly equal weight to all temporal patches when predicting quiet periods — explainability is uninformative for missed flares.

6. **False positive clustering near prior events**: FPs occur when residual post-flare flux triggers elevated predictions. `minutes_since_last_flare` feature attempts to address this but is insufficient.

7. **Calibration leakage status**: UNVERIFIED whether `calibration/probs.npy` (1,806,313 samples = test set size) represents test predictions used to fit the calibrator. If so, this constitutes calibration leakage.

### Engineering

8. **V3 not integrated into inference service**: `inference.py` loads V1 model only. The V3 multi-instrument model exists only in research scripts.

9. **V3 model_v3.py defaults wrong**: Instantiating with defaults cannot load the trained checkpoint without specifying `n_features_solexs=18, n_features_hel1os=4`.

10. **No frontend**: The dashboard, alert interface, and operator workflow are entirely absent.

11. **No authentication**: The `/predict/nowcast` endpoint is unauthenticated.

12. **No real-time ingestion**: GOES data must be manually backfilled. No automated scheduler exists.

13. **No test suite**: Zero automated tests for any component.

14. **No Dockerfile**: The FastAPI app cannot be containerized without a Dockerfile.

15. **`artifacts/models_v3/test_checkpoint.pt` is a 52 MB untrained model** (epoch=1, best_val_tss=-1.0) consuming disk space with no documented purpose.

---

## Scientific Assessment

### Chronological Split
**PASS.** Train/val/test boundaries are strictly chronological with 60-second gaps, no overlap. Verified via `artifacts/aditya_l1/train_test_boundary_audit.json` and `artifacts/aditya_l1/window_overlap_audit.json`.

### Temporal Leakage
**PASS.** No sliding window overlap across split boundaries detected. Window overlap audit confirms 0 leakage rows at all lag offsets.

### Calibration Leakage
**UNVERIFIED.** The source dataset for calibrator fitting cannot be conclusively confirmed from repository artifacts. See Outstanding Issue #7.

### Threshold Leakage
**PASS.** `operator_thresholds_validation_only.json` confirms: `"data_used_for_selection": "validation"`, `"test_data_used": false`.

### Data Leakage (Target)
**PASS.** Target labels use 6-hour lookahead strictly after the input window endpoint. No future-target information in input features verified.

### Reproducibility
**PARTIAL.** Deterministic on same hardware platform (SHA256 verified). Non-deterministic across platforms (MPS vs CPU gives max diff 9.76e-4 due to floating-point implementation differences in Apple Silicon MPS backend).

### Ablation Support
**PARTIAL.** Extensive ablations exist for GOES features (information gap analysis). Cross-instrument ablations performed but show minimal Aditya-L1 benefit. No systematic learning rate, architecture, or training procedure ablations.

### Uncertainty Estimation
**IMPLEMENTED.** MC Dropout (50 forward passes) provides epistemic uncertainty. Tiered suppression system uses uncertainty to down-grade alerts. This is appropriate but NOT independently validated against actual forecast error rates.

### Distribution Shift Handling
**NOT IMPLEMENTED.** No drift monitoring, no distribution shift detection, no adaptive threshold mechanism. The 37-fold increase in positive rate from train to test is not addressed.

### Missing Data Handling
**IMPLEMENTED (V3).** Learnable missing tokens + binary availability masks for SoLEXS and HEL1OS. Forward-fill/backward-fill for short_flux NaN values in inference.

---

## Engineering Assessment

| Subsystem | Status | Notes |
|-----------|--------|-------|
| Data ingestion (PRADAN/GOES) | IMPLEMENTED | Operational, download manager with checksums, resumable |
| Data processing (FITS → Parquet) | IMPLEMENTED | For SoLEXS/HEL1OS |
| Feature engineering | IMPLEMENTED | 14 GOES physics features |
| V1 Model definition | IMPLEMENTED | PatchTST, correct |
| V3 Model definition | IMPLEMENTED (BUGGY DEFAULTS) | Default params incompatible with checkpoint |
| V1 Training pipeline | IMPLEMENTED, EXECUTED | 3 epochs trained |
| V3 Training pipeline | IMPLEMENTED, EXECUTED | Stage 1+2 training completed |
| Calibration | IMPLEMENTED | Isotonic regression |
| Threshold optimization | IMPLEMENTED | Validation-set sweep |
| V1 Inference service | IMPLEMENTED | MC Dropout, calibration, alerts |
| V3 Inference service | ABSENT | V3 not wired to API |
| Backend API | IMPLEMENTED | 5 endpoint groups |
| Database (TimescaleDB) | IMPLEMENTED | Schema, migrations |
| Redis caching | IMPLEMENTED | Connected but minimal usage |
| Docker compose | IMPLEMENTED | TimescaleDB + Redis only |
| Frontend / Dashboard | ABSENT | |
| Authentication | ABSENT | |
| Tests | ABSENT | |
| CI/CD | ABSENT | |
| Monitoring | ABSENT | |
| Real-time ingestion | ABSENT | |
| Dockerfile (app) | ABSENT | |
| Documentation | PARTIAL | README + validation reports |

---

## ISRO Assessment

**Strengths:**
- Uses India's own Aditya-L1 mission data (SoLEXS, HEL1OS) — strong institutional alignment
- Covers ISRO satellite mission impact assessment in inference output
- Data provenance tracking with SHA256 checksums and download manifests
- 16-year GOES archive for robust historical training base

**Weaknesses:**
- SoLEXS and HEL1OS provide statistically minimal improvement over GOES alone — the core scientific justification for Aditya-L1 instrumentation is not demonstrated
- Only 4 days of joint GOES+Aditya-L1 data with zero flare events — scientific validation is impossible
- No real-time connection to Aditya-L1 data streams (PRADAN download is semi-manual)
- Extremely low recall (3.97%) at operational thresholds — most flares will be missed
- No uncertainty calibration proof for SC25 distribution (model trained on SC24)
- No peer review or independent scientific validation

**Missing for ISRO Operational Use:**
- Formal verification of temporal calibration across solar cycles
- Independent validation on ISRO mission-specific scenarios
- Real-time PRADAN/ISAC data feed integration
- Regulatory or scientific review board approval
- Reliability requirement specifications (false alarm rate budget)
- Human-in-the-loop workflow for operator confirmation

---

## Research Assessment

### For NeurIPS/ICML Review

**Strengths:**
- Novel application of PatchTST to solar flare forecasting
- Multi-instrument late fusion architecture with learnable missing tokens
- Comprehensive ablations, calibration analysis, explainability
- Rigorous chronological train/test split

**Weaknesses / Publication Blockers:**
1. **Primary claim not supported:** "Aditya-L1 improves forecasting" is not validated. The ablation shows GOES-only performs as well as or better than full multi-instrument model.
2. **No comparison to baselines:** No comparison against persistence model, NOAA operational model, or prior solar flare forecasting literature (e.g., LSTM-based, CNN-based approaches).
3. **Distribution shift not addressed:** SC24→SC25 shift confounds evaluation; train/test are not from the same distribution.
4. **Only 4 days of joint flare data:** Statistical claims about multi-instrument fusion require at minimum multiple flare events observed jointly by both systems.
5. **Calibration source unresolved:** If calibrator was fit on test data, this is a fatal methodological flaw.
6. **Positive rate collapse on SC24:** 0.62% positive rate in training creates extreme class imbalance; the very high recall (92.9%) at the evaluation threshold is likely inflated by SC25 higher base rate.
7. **Missing ablations:** No learning rate sensitivity analysis, no architecture depth ablations, no seed variance analysis (only seed=42 reported).
8. **Temporal resolution assumption:** The 1-minute sliding window with stride=1 creates highly autocorrelated samples. Statistical tests don't account for this autocorrelation.

**Publication readiness: NOT READY.** Requires multi-flare joint validation, baseline comparisons, and distribution shift analysis before submission.

---

## Production Assessment

**Production Readiness: NOT PRODUCTION READY**

Critical gaps:
1. No real-time data ingestion
2. No frontend
3. No authentication
4. No test suite (any regression could go undetected)
5. No CI/CD
6. No monitoring or alerting
7. V3 model not integrated
8. No Dockerfile for the application
9. Model performance at operational thresholds (3.97% recall) is operationally unacceptable for satellite protection
10. No documented SLA or reliability requirements

---

## Repository Health Score (/100)

**Score: 48/100**

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Code organization | 7/10 | Clear separation of app/scripts/scratch/data/artifacts |
| Documentation | 6/10 | README good, validation reports comprehensive, but no API docs, no CONTRIBUTING |
| Testing | 0/10 | Zero automated tests |
| Reproducibility | 5/10 | Seeds set, but platform-dependent; no git history |
| Correctness | 6/10 | V3 default params wrong; calibration leakage unverified; 3 threshold sets |
| Version control | 0/10 | Not a git repository |
| Dependency management | 5/10 | requirements.txt exists but package versions drift (installed vs. pinned differ) |
| Data management | 7/10 | Checksums, manifests, versioned datasets |
| Architecture clarity | 7/10 | Clear two-model architecture, well-documented |
| Security | 5/10 | No auth, plaintext passwords in config, but local dev context |

---

## Scientific Readiness (/100)

**Score: 52/100**

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Temporal leakage prevention | 10/10 | Verified clean chronological split |
| Distribution shift analysis | 2/10 | SC24/SC25 mismatch acknowledged but not addressed |
| Calibration quality | 7/10 | ECE reduced from 0.27 to 0.09; source data unverified |
| Multi-instrument validation | 2/10 | 4 days, zero flares, marginal improvement |
| Ablation studies | 7/10 | Extensive; signal audit, information gap, feature importance |
| Baseline comparisons | 2/10 | No comparison to literature or NOAA operational model |
| Uncertainty quantification | 7/10 | MC Dropout implemented and integrated operationally |
| Reproducibility | 5/10 | Platform-dependent; deterministic within same HW |
| Statistical rigor | 3/10 | Bootstrap CI present; autocorrelation in samples not addressed |
| Evidence strength | 7/10 | Extensive auditing pipeline; comprehensive validation reports |

---

## Engineering Readiness (/100)

**Score: 38/100**

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| API completeness | 7/10 | 5 endpoints working |
| Data ingestion | 5/10 | Manual, no real-time scheduler |
| Model serving | 5/10 | V1 only; V3 not integrated; missing Dockerfile |
| Testing | 0/10 | Zero automated tests |
| Security | 2/10 | No auth, hardcoded passwords |
| Monitoring | 0/10 | None |
| CI/CD | 0/10 | None |
| Frontend | 0/10 | Absent |
| Database | 7/10 | TimescaleDB + migrations + Redis |
| Configuration management | 5/10 | .env.example present; docker-compose works |
| Error handling | 7/10 | Comprehensive in inference.py |

---

## Hackathon Readiness (/100)

**Score: 65/100**

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Working demo | 7/10 | API + model inference works; requires Docker setup |
| Compelling story | 8/10 | India's Aditya-L1 + ISRO satellite protection narrative |
| Scientific depth | 8/10 | Extensive audit trail; calibration; uncertainty |
| Technical novelty | 7/10 | Multi-instrument late fusion with missing tokens; MC Dropout operational |
| Presentation assets | 6/10 | Validation reports, attention maps, casebook exist; no frontend |
| Live demo capability | 4/10 | Requires local Docker setup; no hosted version |
| Edge cases covered | 8/10 | Missing data, uncertainty suppression, RED confirmation |
| Documentation quality | 7/10 | Good README; extensive sprint documentation |

---

## Production Readiness (/100)

**Score: 18/100**

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Core ML model | 6/10 | V1 trained and calibrated; operational thresholds set |
| Real-time data | 0/10 | No scheduler; manual ingestion only |
| Frontend | 0/10 | Absent |
| Authentication | 0/10 | None |
| Testing | 0/10 | Zero automated tests |
| Monitoring | 0/10 | None |
| CI/CD | 0/10 | None |
| Reliability | 3/10 | Error handling exists; no uptime guarantees |
| Performance | 5/10 | MPS inference; Redis caching available |
| Documentation | 4/10 | Partial; no operator manual |

---

## Highest Priority Next Step

**The single highest priority action is:**

**Establish whether SoLEXS and HEL1OS provide genuine predictive value beyond GOES alone under active flare conditions.**

The entire scientific justification for this project rests on this claim. The current evidence (minimal TSS improvement of 0.85%, 4-day overlap with zero flare events) does not support it. Before any further engineering investment, this question must be answered:

1. Collect GOES + Aditya-L1 joint data during a period containing at least 5–10 M/X flare events
2. Evaluate V3 full model vs GOES-only ablation on this flare-containing overlap period
3. Conduct a formal significance test (paired bootstrap or McNemar) on the flare-event windows

If Aditya-L1 instruments provide no statistically significant improvement, the project should pivot to a V1-focused operational system (simpler, more maintainable, backed by 16 years of training data) while maintaining Aditya-L1 data ingestion for future validation as the mission matures.

If Aditya-L1 instruments do improve performance on flare events, the V3 model should be integrated into the inference service, and the `model_v3.py` default parameters must be corrected to match the trained checkpoint.

---

## Appendix: Key Files Reference

| Purpose | Path |
|---------|------|
| V1 model architecture | `app/services/ml/model.py` |
| V3 model architecture | `app/services/ml/model_v3.py` |
| Active inference service | `app/services/ml/inference.py` |
| V1 best checkpoint | `artifacts/models/patchtst_best.pt` |
| V3 best checkpoint | `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` |
| Calibrator | `artifacts/calibrator.pkl` |
| Production thresholds | `artifacts/operator_thresholds.json` |
| V1 feature columns | `artifacts/feature_columns.json` |
| V3 feature columns | `artifacts/feature_columns_v3.json` |
| V1 test results | `artifacts/evaluation_audit_report.json` |
| V3 test results | `artifacts/sprint14c/test_results_model_D_seed_42.json` |
| Scientific validation | `scientific_validation_report.md` |
| Ablation results | `artifacts/information_gap_report.json` |
| Overlap dataset | `artifacts/aditya_l1/overlap_dataset.parquet` |
| Bootstrap CI | `artifacts/bootstrap_metrics.json` |
| Operator readiness | `artifacts/operator_readiness_report.json` |
| V3 training log | `artifacts/sprint14c/experiment.log` |

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Living context document; pre-Sprint-23 statements presenting thresholds 0.46/0.88 as production were stale and are corrected inline below with [SUPERSEDED — Sprint 23] markers; original text preserved. -->
<!-- SUPERSEDED BY: Sprint 23 (artifacts/policies/operator_policy_v2.json); proof: artifacts/sprint22_5/FINAL_VERDICT.md; clean baseline: artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md -->
<!-- DATE: 2026-07-03 -->

# Tech Stack — SuryaNet / AdityaNet

> **Owner:** Soumyadeb Tripathy
> **Update:** When dependencies change
> **Cross-refs:** `context/architecture.md` · `PROJECT_CONFIG.yaml`

---

## Runtime Environment

| Component | Value | Notes |
|-----------|-------|-------|
| OS | macOS Darwin 25.5.0 | Apple Silicon M4 |
| CPU/GPU | Apple M4 (MPS accelerator) | CUDA unavailable |
| Python (active) | 3.14.4 | Current runtime |
| Python (historical training) | 3.12.12 | Used when sprint14c checkpoints were trained |
| PyTorch (active) | 2.9.1 | Current runtime |
| PyTorch (historical training) | 2.12.0 | Used for sprint14c |
| Virtual environment | `venv/` | Standard pip venv |

**WARNING:** MPS backend introduces floating-point non-determinism between hardware platforms. Predictions differ by up to 9.76e-4 max absolute difference between MPS and CPU runs. Metrics from saved `.npz` files are canonical; fresh inference metrics will differ slightly.

---

## ML / AI Stack

| Library | Version | Purpose |
|---------|---------|---------|
| PyTorch | 2.9.1 | Model architecture, training, inference |
| NumPy | latest | Feature arrays, memory-mapped datasets |
| Pandas | latest | Parquet I/O, data manipulation |
| scikit-learn | latest | Isotonic regression calibration, metrics |
| SciPy | latest | Temperature scaling (LBFGS), linear regression (RED confirmation) |

### Key ML Files

| File | Purpose |
|------|---------|
| `app/services/ml/model.py` | V1 PatchTST — ACTIVE IN PRODUCTION |
| `app/services/ml/model_v3.py` | V3 LateFusionPatchTST — RESEARCH ONLY (default params WRONG — see BUG-001) |
| `app/services/ml/inference.py` | Production inference service (loads V1 only) |
| `app/services/ml/features.py` | 14 GOES feature engineering functions |
| `app/services/ml/dataset.py` | V1 sliding window dataset |
| `app/services/ml/dataset_v3.py` | V3 multi-instrument dataset with memory mapping |
| `app/services/ml/trainer.py` | V1 training loop |
| `app/services/ml/trainer_v3.py` | V3 Stage 1+2 training with transfer learning |
| `app/services/ml/evaluator_v3.py` | V3 calibration (Isotonic + Temperature Scaling) |
| `app/services/ml/metrics.py` | Full metric suite: TSS, HSS, MCC, ECE, PR-AUC, bootstrap CI |
| `app/services/ml/config.py` | `FORECAST_HORIZON_MINUTES=360`, `TARGET_FLARE_CLASSES=["M","X"]` |

### Model Checkpoints

| Checkpoint | Size | Status | Epoch | Best Val TSS |
|------------|------|--------|-------|--------------|
| `artifacts/models/patchtst_best.pt` | 9.96 MB | ACTIVE (V1) | 3 | — |
| `artifacts/models/patchtst_last.pt` | 9.96 MB | Backup (V1) | 3 | — |
| `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` | 17.57 MB | Research (V3) | — | 0.4644 (val) |
| `artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt` | 17.57 MB | Research (V3 S1) | — | — |
| `artifacts/models_v3/test_checkpoint.pt` | 52.57 MB | UNTRAINED / ABANDONED | 1 | -1.0 |

---

## Backend Stack

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| API framework | FastAPI | latest | 5 endpoint groups |
| ASGI server | Uvicorn | latest | Logs in `uvicorn.log` |
| ORM | SQLModel | latest | Built on SQLAlchemy |
| Database | TimescaleDB | 2.15.3-pg16 | Port 5433:5432 (Docker) |
| Cache | Redis | 7.2.4-alpine | Port 6379 |
| Container orchestration | Docker Compose | — | `docker-compose.yml` |
| Migrations | Alembic | latest | Single migration: `a541577be3f5` |

### Key Backend Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI lifespan: Redis connect + DB init |
| `app/core/config.py` | Settings: PROJECT_NAME="SuryaNet", DB host/port/redis |
| `app/api/v1/endpoints/inference.py` | POST /predict/nowcast — V1 model only |
| `app/api/v1/endpoints/solar.py` | GOES telemetry queries |
| `app/api/v1/endpoints/flares.py` | Flare event queries |
| `app/services/operations/impact.py` | ISRO mission impact assessment |

### API Configuration

```
FORECAST_HORIZON_MINUTES = 360   # 6 hours
INPUT_WINDOW_MINUTES     = 360   # 360 flux records required per request
SEQ_LEN                  = 360   # matches model input
MC_DROPOUT_SAMPLES       = 50    # uncertainty estimation passes
YELLOW_THRESHOLD         = 0.46  # production (artifacts/operator_thresholds.json)
RED_THRESHOLD            = 0.88  # production
```

> **[SUPERSEDED — Sprint 23]** The two threshold lines above are void: those values were proven test-set derived (`artifacts/sprint22_5/FINAL_VERDICT.md`) and the file quarantined. Current production: `YELLOW_THRESHOLD = 0.14`, `RED_THRESHOLD = 0.95`, loaded from `artifacts/policies/operator_policy_v2.json` via the provenance-gated `app/services/ml/policy.py`.

---

## Data Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Time series storage | TimescaleDB | GOES flux + flare events |
| Bulk storage | Parquet (pandas/pyarrow) | Research datasets (~3.7 GB) |
| Cache layer | NumPy .npy (memory-mapped) | V3 dataset cache in artifacts/sprint14c/cache/ |
| Data download | `data_pipeline/download_manager.py` | PRADAN + NOAA, checksum verification |

### Dataset Sizes

| Dataset | Records | Size |
|---------|---------|------|
| GOES archive (8.6M minutes, 2010–2026) | 8,631,360 | ~3.7 GB parquet |
| V1 train (2010–2019, SC24) | 5,161,312 | — |
| V1 validation (2020–2022) | 1,568,759 | — |
| V1 test (2023–2026, SC25) | 1,806,673 | — |
| V3 S2 train (Dec 2023 – Jun 2025) | 785,938 | — |
| V3 S2 test (Dec 2025 – Jun 2026) | 261,095 | — |
| GOES+Aditya-L1 overlap | 5,760 (4 days) | — |

---

## Instruments / Data Sources

| Instrument | Source | Features in Model | Coverage |
|-----------|--------|-------------------|---------|
| GOES XRS | NOAA (GOES 16/17/18) | 14 engineered features | 2010-01-02 to present |
| SoLEXS | ISRO Aditya-L1 (L1 orbit) | 18 spectral features | Dec 2023 to present (915 files) |
| HEL1OS | ISRO Aditya-L1 (L1 orbit) | 4 hard X-ray features | Oct 2023 to present (960 files) |

**HEL1OS trust:** 97.93% scientific coverage (verified, `hel1os_trust_certificate.json`)

---

## Missing / Not Yet Implemented

| Gap | Severity |
|-----|---------|
| No test framework (pytest) | High |
| No authentication middleware | High |
| No Dockerfile for FastAPI app | High |
| No real-time ingestion scheduler (cron/celery) | High |
| No frontend (HTML/JS/React) | Medium |
| No CI/CD pipeline | Medium |
| No git repository | High |

---

*Last updated: 2026-07-03 · AgentOS onboarding*

# AdityaNet (SuryaNet) — Project Structure

SuryaNet is a physics-informed solar flare forecasting and space-weather intelligence platform built on data from ISRO's **Aditya-L1** mission (SoLEXS and HEL1OS instruments). This document describes the repository layout for new contributors, reviewers, and researchers reproducing results.

---

## 1. Repository Layout

```
AdityaNet/
├── app/                    # FastAPI service — the deployable inference/API application
│   ├── main.py             # ASGI entry point (uvicorn app.main:app)
│   ├── api/v1/              # Versioned REST API routes
│   │   └── endpoints/        # flares, health, inference, solar, system
│   ├── core/                # Settings (pydantic-settings) and Redis client
│   ├── db/                  # SQLModel session + DB init (TimescaleDB/Postgres)
│   ├── models/               # ORM models: checkpoint, flare, goes, ingestion
│   ├── schemas/              # Pydantic request/response schemas
│   └── services/
│       ├── ingestion/         # GOES/flare data client + ingestion service
│       ├── backfill/          # Historical backfill jobs (checkpointed)
│       ├── ml/                # Model definitions, training, inference, explainability
│       └── operations/        # Operational impact assessment
│
├── data_pipeline/          # Standalone data acquisition & curation pipeline (Aditya-L1)
│   ├── download_manager.py  # Main orchestrator
│   ├── hel1os_downloader.py # HEL1OS-specific downloader
│   ├── config.yaml           # Pipeline configuration
│   ├── downloader/            # Session, manifest, verifier, checksum, streaming logic
│   ├── plugins/                # Per-instrument payload plugins (e.g. solexs.py)
│   ├── parsers/, processing/   # FITS/format parsing and processing
│   ├── datasets/                # Curated dataset versions (dataset_v1 … dataset_v3, test_dataset)
│   ├── inventory/, registry/, reporting/, reports/ # Metadata, catalog, and QA reports
│   └── checksums/, database/, downloads/, logs/     # Pipeline state and raw downloads
│
├── scripts/                 # Operational & research CLI entry points (train/eval/audit)
│   ├── train_patchtst.py      # Primary training entry point
│   ├── train_baseline.py      # Baseline model training
│   ├── build_research_dataset.py, build_multi_instrument_dataset.py
│   ├── run_ablation_*.py       # Ablation study suite
│   ├── calibrate_model.py, refine_thresholds.py
│   ├── backtest_*.py            # Alert-system and operator-policy backtests
│   ├── analyze_*.py, audit_*.py, verify_*.py  # Result analysis & audits
│   ├── aditya_l1/, signal_audit/, sprint9b/    # Sub-suites of related scripts
│   └── ingest_goes.py, backfill_flares.py, backfill_goes.py
│
├── scratch/                  # One-off research/audit scripts (NOT part of the production
│   │                          # pipeline — not imported by app/ or data_pipeline/). Kept for
│   │                          # research traceability. See CONTRIBUTING.md before adding here.
│
├── artifacts/                 # Generated outputs: checkpoints, reports, figures, run logs
│   ├── models/, models_v3/     # Saved model checkpoints (current + v3 architecture)
│   ├── sprint*/                # Per-sprint checkpoints, reports, and validation artifacts
│   ├── runs/, runs_v3/, tensorboard/  # TensorBoard event logs
│   ├── calibration/, attention_maps/, information_gap/  # Interpretability / analysis outputs
│   └── *.md, *.json, *.csv      # Sprint-level validation reports and metrics snapshots
│
├── data/                      # Working dataset area
│   └── aditya_l1/               # Processed Aditya-L1 observation data
│
├── raw-data/                  # Minimal raw data samples (flares/, goes/)
│
├── alembic/                    # Database schema migrations (SQLAlchemy/Alembic)
│   └── versions/                 # Migration scripts (currently: add GOES/flare/ingestion tables)
│
├── legacy/                     # Superseded bash-based downloader scripts, kept for reference
│
├── logs/                       # Runtime log output directory
│
├── venv/                       # Python 3.12 virtual environment (git-ignored, machine-local)
│
├── docker-compose.yml           # TimescaleDB + Redis service definitions for local dev
├── alembic.ini                  # Alembic migration configuration
├── requirements.txt              # Pinned Python dependencies
├── .env / .env.example           # Runtime configuration (.env is git-ignored; .example is tracked)
└── README.md                     # Project overview and technical stack
```

---

## 2. Important Datasets

| Location | Contents |
|---|---|
| `data_pipeline/datasets/dataset_v1` … `dataset_v3` | Successive curated dataset versions, each with `inventory.csv`/`inventory.json` and `metadata.json` describing provenance (file counts, SHA-256 manifest, software/Python version used to build it) |
| `data_pipeline/datasets/test_dataset` | Held-out evaluation set |
| `data/aditya_l1/` | Processed Aditya-L1 instrument data used directly by training/inference |
| `raw-data/flares/`, `raw-data/goes/` | Small raw reference samples (not the full acquisition corpus) |
| `artifacts/feature_dataset.parquet`, `artifacts/sprint14c/s2_train.parquet`, `s2_test.parquet` | Feature-engineered training/test tables consumed by specific sprint experiments |

All bulk columnar/binary dataset formats (`*.parquet`, `*.csv`, `*.npy`, `*.npz`, `*.h5`, FITS files) are **excluded from Git** via `.gitignore` — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to reference and reproduce them.

## 3. Important Checkpoints

19 model checkpoint files (`*.pt`) exist under `artifacts/`, notably:

| Checkpoint | Purpose |
|---|---|
| `artifacts/models/patchtst_best.pt`, `patchtst_last.pt` | Current best/last PatchTST checkpoint |
| `artifacts/models_v3/test_checkpoint.pt` | Latest architecture (`LateFusionPatchTST`) test checkpoint |
| `artifacts/sprint13/checkpoints/*`, `sprint14b/checkpoints/*`, `sprint14c/checkpoints/*` | Per-sprint staged checkpoints (pretraining / stage1 / stage2, multiple seeds) |
| `artifacts/sprint9b/*.pt` | Early baseline flux-only / history-only models |

All checkpoints are **excluded from Git** (`*.pt`, `*.pth`, `*.ckpt`, `*.safetensors`). They must be stored/shared via external artifact storage (see CONTRIBUTING.md).

## 4. Training Pipeline

1. Data curated via `data_pipeline/` → versioned dataset in `data_pipeline/datasets/`.
2. Feature/dataset construction: `scripts/build_research_dataset.py`, `build_multi_instrument_dataset.py`, or `app/services/ml/dataset_builder.py` / `dataset.py` / `dataset_v3.py`.
3. Model definitions: `app/services/ml/model.py` (`PatchTST`) and `model_v3.py` (`LateFusionPatchTST`).
4. Training entry points: `scripts/train_patchtst.py` (primary) and `scripts/train_baseline.py`, backed by `app/services/ml/trainer.py` / `trainer_v3.py`.
5. Output: checkpoints written to `artifacts/`, TensorBoard logs to `artifacts/runs*/` and `artifacts/tensorboard/`.

Example (documented in `scripts/train_patchtst.py`):
```bash
PYTHONPATH=$PWD venv/bin/python3 scripts/train_patchtst.py
```

## 5. Inference Pipeline

- `app/services/ml/inference.py` — loads a checkpoint and runs prediction.
- Exposed via the FastAPI route `app/api/v1/endpoints/inference.py`.
- `app/services/ml/explainability.py` — attention/feature-attribution outputs for interpretability (see `artifacts/attention_maps/`, `artifacts/information_gap/`).

## 6. Evaluation Pipeline

- `app/services/ml/evaluator_v3.py` and `app/services/ml/metrics.py` compute evaluation metrics.
- `scripts/run_ablation_*.py` — ablation study suite (flux-only, history-only, engineered features, derivatives, etc.).
- `scripts/calibrate_model.py`, `refine_thresholds.py` — post-hoc calibration and operational threshold tuning.
- `scripts/backtest_alert_system.py`, `backtest_operator_policy.py` — end-to-end operational backtests.
- Results are written as `.md`/`.json`/`.csv` reports under `artifacts/` (sprint-numbered subfolders).

## 7. Deployment Pipeline

- `app/main.py` is the ASGI entry point, served via `uvicorn app.main:app`.
- `docker-compose.yml` provisions the two runtime dependencies: **TimescaleDB** (`timescaledb` service, port 5433) and **Redis** (port 6379).
- `alembic/` manages database schema migrations (`alembic upgrade head`).
- `app/core/config.py` loads runtime configuration from `.env` via `pydantic-settings`.

---

*This file is maintained as part of the repository's Git/version-control setup. It documents structure only — it does not alter, retrain, or regenerate any application logic, models, or datasets.*

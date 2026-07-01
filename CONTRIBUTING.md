# Contributing to AdityaNet (SuryaNet)

This guide covers how to work on this repository — for ISRO hackathon development, university coursework, and ongoing research. It complements [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

---

## 1. Branch Strategy

- `main` — always deployable / reproducible. Do not commit directly for anything beyond trivial doc fixes.
- `feature/<short-description>` — new functionality (e.g. `feature/late-fusion-model`).
- `experiment/<sprint-or-topic>` — research experiments, ablations, audits (e.g. `experiment/sprint15-calibration`). Mirrors the `sprint*`/`scratch/` naming already used in `artifacts/`.
- `fix/<short-description>` — bug fixes.
- `docs/<short-description>` — documentation-only changes.

Open a pull request into `main` for anything that isn't a solo throwaway experiment. Keep branches short-lived; rebase or merge `main` back in regularly to avoid large divergence.

## 2. Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<optional body — the "why", not the "what">
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `experiment`, `data`, `perf`.

**Examples:**
```
feat(ml): add LateFusionPatchTST architecture (model_v3)
fix(api): correct timezone handling in flare ingestion endpoint
experiment(sprint14b): stage-2 fine-tuning with seed sweep
docs(structure): document inference pipeline entry points
data(pipeline): add dataset_v3 provenance manifest
```

Keep the summary line under ~72 characters, imperative mood ("add", not "added"). Reference sprint numbers or artifact folders in the scope/body where relevant, since this repo's history in `artifacts/` is organized by sprint.

## 3. Coding Standards

- **Python**: follow PEP 8. This project targets **Python 3.12**.
- Type hints are expected for new/modified function signatures in `app/` (the codebase already uses `pydantic`/`SQLModel` typed models throughout).
- Keep FastAPI route handlers thin — business logic belongs in `app/services/`, not in `app/api/v1/endpoints/`.
- New ML code goes in `app/services/ml/`; one-off analysis/audit scripts go in `scripts/` (if durable/reusable) or `scratch/` (if exploratory — see §4).
- Run `python -m compileall app` before committing to catch syntax errors.
- Do not hardcode absolute filesystem paths (e.g. `/Users/...`) anywhere in `app/`, `data_pipeline/`, or `scripts/` — this has caused real portability bugs during prior machine migrations. Use `Path(__file__).parent`-relative paths or config/env values instead.

## 4. How to Add Experiments

- **Durable, reusable scripts** (training variants, ablations, audits meant to be re-run) go in `scripts/`, following the existing naming pattern (`run_ablation_<variant>.py`, `verify_<thing>.py`, `audit_<thing>.py`).
- **One-off exploratory scripts** go in `scratch/`. These are not imported by `app/` or `data_pipeline/` and are not part of the production pipeline — treat them as a lab notebook, not shipped code.
- Write experiment outputs (reports, metrics, checkpoints) into a new `artifacts/sprint<N><letter>/` directory, matching the existing convention (e.g. `artifacts/sprint15a/`). Include a short `.md` summary and any `.json` metrics alongside the checkpoint.
- Large outputs (`*.pt`, `*.parquet`, `*.npy`, etc.) are git-ignored by design — do not force-add them (`git add -f`). See §6 for how to share them.

## 5. How to Add Datasets

1. Place new dataset versions under `data_pipeline/datasets/dataset_v<N>/`, following the existing structure: an `inventory.csv`/`inventory.json` (file-level manifest) and a `metadata.json` (dataset version, creation timestamp, file counts, SHA-256 manifest, software/Python version).
2. Do **not** commit the raw dataset files themselves (covered by `.gitignore`: `*.parquet`, `*.csv`, `*.npy`, `*.h5`, FITS formats, etc.) — only the manifest/metadata files, which are small and version-controllable.
3. Document the dataset's source instrument (SoLEXS/HEL1OS/GOES), acquisition method, and any known quality caveats in the metadata or an accompanying `.md`.
4. If the dataset changes the data pipeline itself (e.g. a new plugin), add it under `data_pipeline/plugins/` with a corresponding entry in `data_pipeline/config.yaml`.

## 6. Sharing Large Files (Datasets & Checkpoints)

Since datasets and checkpoints are intentionally excluded from Git (see `.gitignore` and [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)), use one of:
- A shared external drive / lab storage (as this repository itself currently uses).
- Git LFS, if the team decides to adopt it for a specific small set of checkpoints.
- Cloud object storage (S3/GCS/institutional storage) with the manifest/checksum files (which *are* tracked) used to verify integrity after download.

Always keep the small manifest/metadata/checksum files in Git even when the large payloads live elsewhere — that is what makes the dataset/checkpoint reproducible and verifiable.

## 7. How to Reproduce Results

1. Clone the repo and create a fresh venv:
   ```bash
   python3.12 -m venv venv
   venv/bin/pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in local values (database credentials, ports).
3. Start local services: `docker compose up -d` (TimescaleDB + Redis).
4. Apply migrations: `venv/bin/alembic upgrade head`.
5. Obtain the dataset version referenced by the experiment you're reproducing (see `data_pipeline/datasets/<version>/metadata.json` for the exact manifest/checksum to verify against).
6. Obtain the checkpoint (if evaluating rather than retraining) from wherever it's shared per §6, and place it at the path referenced in the relevant `artifacts/sprint*/` report.
7. Run the corresponding script from `scripts/` (e.g. `venv/bin/python3 scripts/train_patchtst.py` or the specific `run_ablation_*.py` / `verify_*.py` used in that sprint's report).
8. Compare your output against the `.md`/`.json` report already committed under `artifacts/` for that sprint.

If a result can't be reproduced exactly, check first for path portability issues (see §3) and dataset/checkpoint version mismatches before assuming a code regression.

---

*This file documents contribution process only — it does not alter any existing application logic, training code, or data.*

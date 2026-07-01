# AdityaNet — SSD Build Info

Generated: 2026-07-01 11:55 IST
Location: `/Volumes/T7 Shield/Projects/AI/AdityaNet`

## Environment

| Property | Value |
|---|---|
| Python version | 3.12.12 |
| OS | macOS (ProductVersion 26.5.1, Build 25F80) |
| Architecture | arm64 (Apple Silicon) |
| Torch version | 2.12.1 |
| MPS built | True |
| MPS available | True |
| Installed package count | 87 (via `pip list` in the SSD venv) |
| Virtual environment location | `/Volumes/T7 Shield/Projects/AI/AdityaNet/venv` — freshly created in place with `/opt/homebrew/bin/python3.12 -m venv venv`, all dependencies reinstalled from `requirements.txt` |

## Repository

| Metric | Value |
|---|---|
| Total repository size | 35G (`du -sh`, includes venv, artifacts, datasets, logs) |
| `data/` size | 4.0G |
| `data_pipeline/datasets/` size | 421M |
| `raw-data/` size | 7.5M |
| `artifacts/` size (checkpoints + reports) | 3.7G |

## Checkpoint Inventory (19 files found under `artifacts/`)

| Checkpoint | Size |
|---|---|
| artifacts/sprint9b/best_flux_only.pt | 3.2M |
| artifacts/sprint9b/best_history_only.pt | 3.1M |
| artifacts/sprint9b/suryanet_flux_only.pt | 3.2M |
| artifacts/sprint9b/suryanet_history_only.pt | 3.1M |
| artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt | 17M |
| artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt | 17M |
| artifacts/models/patchtst_best.pt | 9.5M |
| artifacts/models/patchtst_last.pt | 9.5M |
| artifacts/models_v3/test_checkpoint.pt | 50M |
| artifacts/sprint13/checkpoints/stage1_best_loss.pt | 17M |
| artifacts/sprint13/checkpoints/stage1_best_prauc.pt | 17M |
| artifacts/sprint13/checkpoints/stage1_best_tss.pt | 17M |
| artifacts/sprint13/checkpoints/stage1_pretrained.pt | 17M |
| artifacts/sprint13/checkpoints/stage2_best_loss.pt | 17M |
| artifacts/sprint13/checkpoints/stage2_best_prauc.pt | 17M |
| artifacts/sprint13/checkpoints/stage2_best_tss.pt | 17M |
| artifacts/sprint14b/checkpoints/model_seed_42_best_tss.pt | 17M |
| artifacts/sprint14b/checkpoints/stage1_seed_123_pretrained.pt | 17M |
| artifacts/sprint14b/checkpoints/stage1_seed_42_pretrained.pt | 17M |

Sample checkpoint (`artifacts/sprint9b/best_flux_only.pt`) was loaded with `torch.load(map_location='cpu')` and confirmed readable (dict with keys `epoch`, `model`). No checkpoints were modified, retrained, or regenerated.

## Notes

- This venv was built fresh on the SSD (the previous copy inherited absolute paths from the original venv — see `MIGRATION_FINAL_CERTIFICATE.md` for full detail).
- macOS AppleDouble sidecar files (`._*`), generated because the exFAT filesystem cannot store extended attributes, were removed via `dot_clean` after being identified as the cause of a real `alembic history` failure and false-positive `compileall` errors. This did not touch any project source, data, or checkpoint file — only OS-generated shadow files paired 1:1 with real files.

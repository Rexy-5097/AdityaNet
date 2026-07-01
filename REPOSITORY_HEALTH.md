# AdityaNet — Repository Health Report

Generated: 2026-07-01, during Git repository initialization on `/Volumes/T7 Shield/Projects/AI/AdityaNet`.

---

## 1. Repository Size

| Metric | Value |
|---|---|
| Total working-tree size | 35G |
| Total working-tree file count (excluding `.git` internals) | 47,872 |
| Total directory count | 3,804 |
| `.git` object database size (after correction below) | 707M |
| Files staged for the initial commit | 2,540 |
| Total size of staged content | 226.2 MB |
| Files/paths excluded by `.gitignore` | ~45,332 files (everything not staged — `venv/`, datasets, checkpoints, logs, caches, archives) |

## 2. A Bug Found and Fixed During Setup

The first `git add -A` pass took ~6 minutes and produced a **21GB `.git` directory** — a red flag. Direct investigation found the cause: `*.zip` and `*.gz` were **not** in the original `.gitignore` extension list, even though the task explicitly required "large datasets" to be excluded. Audit results:

| Pattern found | Count | Size |
|---|---|---|
| `*.zip` under `data_pipeline/downloads/` (raw Aditya-L1 instrument archives) | 2,127 files | 20.9 GB |
| `*.gz` under `data/aditya_l1/` (compressed SoLEXS telemetry, `.pi.gz`) | multiple | tens of MB each |

**Fix applied:** added `*.zip`, `*.tar`, `*.tar.gz`, `*.tgz`, `*.gz`, `*.7z`, `*.rar`, `*.bz2`, plus `*.pi` and `*.pkl`/`*.pickle` (pickled model artifacts, e.g. `artifacts/*/calibrator.pkl`) to `.gitignore`. Since zero commits existed at the time (the first `git init` had never been committed), the bloated `.git` was deleted and the repository was re-initialized cleanly — this is **not** a history rewrite, as no history existed yet. Re-running `git add -A` afterward took **7.9 seconds** and produced a 707M `.git`, confirming the fix.

## 3. Remaining Large Files — Disclosed, Not Silently Excluded

A full audit for files >5MB anywhere in the working tree (excluding `venv/` and `.git/`) found **772 files totaling 26.4 GB**. After the `.gitignore` fix, the following **10 large JSON files (226 MB total, all currently staged)** remain tracked, because JSON was not in the task's explicit exclusion list and these may be intentionally valuable reproducibility artifacts (not raw data):

| File | Size |
|---|---|
| `artifacts/aditya_l1/signal_localization_audit.json` | 59M |
| `artifacts/aditya_l1/raw_channel_generalization.json` | 25M |
| `artifacts/aditya_l1/checkpoints/localization_task_1.json` | 25M |
| `artifacts/aditya_l1/checkpoints/localization_task_2.json` | 20M |
| `artifacts/aditya_l1/physical_band_generalization.json` | 20M |
| `artifacts/aditya_l1/cross_instrument_confirmation_audit.json` | 20M |
| `artifacts/aditya_l1/target_relationship_audit.json` | 13M |
| `artifacts/aditya_l1/checkpoints/localization_task_3.json` | 9.3M |
| `artifacts/aditya_l1/compression_generalization.json` | 9.3M |
| `artifacts/aditya_l1/lead_lag_relationship_audit.json` | 6.8M |

**Recommendation:** decide deliberately whether these belong in Git history. Options: (a) keep as-is if they're small enough relative to your GitHub plan and valuable for reproducibility, (b) move to Git LFS, or (c) add `artifacts/aditya_l1/*.json` and `artifacts/aditya_l1/checkpoints/*.json` to `.gitignore` and store them alongside the checkpoints/datasets externally. This decision was left to you rather than made automatically.

All other >5MB files found in the audit (599 `.zip`, 90 `.fits`, 32 `.parquet`, 15 `.pt`, 12 `.npy`, 10 `.gz`, 1 `.npz`, 1 `.csv`) are correctly excluded by the current `.gitignore`.

## 4. Largest Directories (on disk, not just tracked content)

| Directory | Size |
|---|---|
| `data_pipeline/` | 21G (mostly `.zip`/`.gz` raw downloads — ignored) |
| `venv/` | 5.8G (ignored) |
| `data/` | 4.0G (mostly `.gz`/processed data — ignored) |
| `artifacts/` | 3.7G (checkpoints ignored; ~226MB of JSON reports currently tracked — see §3) |
| `scratch/` | 41M |
| `app/` | 16M |
| `raw-data/` | 7.5M |
| `scripts/` | 7.4M |
| `brain/` (external symlink target, not copied) | 3.5M |
| `alembic/` | 1.1M |

## 5. Duplicate Files

A byte-for-byte duplicate check was run, scoped to `app/`, `scripts/`, `scratch/`, and root-level files (small text/code — a full 35GB checksum sweep was not performed, as it is not feasible at this scale/drive speed and unlikely to find duplicates among multi-GB binary datasets that are already excluded from version control). Method: grouped files by exact byte size, then diffed same-size candidates.

**Result: zero true duplicates found.** All 7 same-size candidate pairs (e.g. two empty `__init__.py` files, `scratch/print_fold_results.py` vs `scratch/print_metadata_summary.py`) were confirmed via `diff` to have **different content** — the size match was coincidental. The near-identical-looking script family `scratch/copy_artifacts.py`, `copy_sprint13b_artifacts.py`, `copy_sprint14b_artifacts.py` was checked via MD5 and confirmed to be three genuinely distinct files (different sizes and hashes), not copy-paste duplicates.

## 6. Broken Symlinks

**None.** All 5 symlinks in the repository resolve correctly:
- `brain` → `/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/3ec42318-ed37-471e-b5fd-4a0ca103f854` (external, resolves; excluded from Git via `.gitignore` since it's not portable across machines)
- `artifacts/tensorboard` → `runs` (internal, resolves)
- `venv/bin/python`, `venv/bin/python3`, `venv/bin/python3.12` (resolve to system Homebrew Python; `venv/` itself is git-ignored)

## 7. Missing Documentation

- Only two README-style files exist in the whole tree: root `README.md` and Alembic's auto-generated `alembic/README`. No per-directory READMEs exist for `data_pipeline/`, `scripts/`, or `scratch/`. **Mitigated** by the new `PROJECT_STRUCTURE.md` created in this task, which documents every directory's purpose.
- Module-level docstrings are inconsistent in `app/`: of 29 non-`__init__.py` files checked, **24 have no module docstring** (e.g. `app/main.py`, `app/core/config.py`, all of `app/api/v1/endpoints/`). `app/services/ml/trainer.py` and a few others do have them. `data_pipeline/download_manager.py` also has no module docstring (`data_pipeline/hel1os_downloader.py` does).
- **Not fixed automatically** — the task instructions prohibit rewriting existing source/documentation; this is reported as an opportunity only.

## 8. Unused Scripts / Dead Code

**No dead code was proven**, per the requirement to only report it "if proven." Method: cross-referenced every `.py` filename in `scripts/` (35 files) and repo-root loose scripts (11 files) against the rest of the repository (`.py`, `.md`, `.sh` files) for any mention.

- 20 of 35 `scripts/` files and 6 of 11 root-level scripts are not mentioned by name anywhere else in the repository.
- **This is not evidence of dead code.** These are standalone CLI research tools, designed to be invoked directly (`venv/bin/python3 scripts/run_ablation_short_flux.py`), not imported by other modules — the same pattern applies to `train_patchtst.py` itself (documented and referenced) and to scripts with zero references. Direct spot-check confirmed several "unreferenced" scripts (e.g. the `run_ablation_*` family) have matching output artifacts in `artifacts/information_gap/` (e.g. `ablation_both_flux.json`, `ablation_derivatives.json`) and `artifacts/sprint9b/` (`*_history_only.*`), proving they were in fact executed historically. No unreferenced script was found to be provably non-functional or superseded.

## 9. Other Notes (verified, not part of the required checklist)

- `git config core.filemode` is `false` and `core.ignorecase` is `true` on this exFAT-mounted volume — both are exFAT/macOS-driver defaults, not something this task changed. Practical effect: Git will **not** track file permission changes (e.g. chmod +x on a new script) on this checkout, and filename matching is case-insensitive. This is a filesystem limitation of exFAT, not a project issue — worth knowing if you later `git mv`/rename files on this drive.
- No global `git config user.name` / `user.email` is set on this machine. **NOT VERIFIED as a problem** — this needs to be set (locally or globally) before the first `git commit` will succeed. Not set automatically here, since it wasn't provided and shouldn't be guessed.
- `.env.example` and `.env` currently share the same `POSTGRES_PASSWORD` value (`postgres_secure_pass`) — a local Docker Compose default, not a production credential, but not a true placeholder either. Since `.env.example` is tracked (by design, via the `!.env.example` negation in `.gitignore`), this value will enter Git history once committed. Recommend replacing it with an obvious placeholder (e.g. `CHANGE_ME`) before the first commit if this repository will ever be pushed publicly. **Not changed automatically** — modifying `.env.example`'s content was outside this task's stated scope (only files created by this task may be authored/rewritten).

---

*This report reflects the repository state at the time of generation. Numbers will change as files are added/removed.*

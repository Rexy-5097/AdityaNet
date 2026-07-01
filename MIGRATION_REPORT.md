# AdityaNet Workspace Migration Report

Date: 2026-07-01

## 1. SSD Detection

| Property | Value |
|---|---|
| Device | `/dev/disk4s1` (external physical disk `/dev/disk4`) |
| Volume name | T7 Shield |
| Mount path | `/Volumes/T7 Shield` |
| Filesystem | ExFAT (mounted via macOS `fskit`, options: `local, nodev, nosuid, noowners, noatime`) |
| Total capacity | 1.0 TB (931 Gi) |
| Available before copy | 931 Gi |
| Available after copy | 892 Gi |
| Write permission | Confirmed (write/read/delete test file succeeded) |
| Symlink support | Confirmed (test symlink created and read back successfully) |

Note: `diskutil list` initially labeled the partition type as `Windows_NTFS`, but `mount` and `diskutil info` both confirm the actual filesystem personality is **ExFAT**. ExFAT does not natively support POSIX permission bits, ownership, or extended attributes (the mount includes `noowners`). See Limitations below.

## 2. Workspace Created

```
/Volumes/T7 Shield/Projects/AI/AdityaNet/
```

No other folders were created.

## 3. Source Repository Selection

Searched the entire local filesystem (`find / -iname "*AdityaNet*"`, excluding `/System`, `/Library`, `/private/var`) for any copy of the project.

**Result: exactly one candidate exists.**

- Canonical path: `/Users/soumyadebtripathy/AdityaNet`
- No duplicate, stale, or backup copies were found anywhere else on the machine.
- Other matches found were unrelated artifacts, not project copies: two PPTX/PDF export files in `Downloads/`, Claude Code's own session/cache directories, and Gemini CLI history/tmp folders that merely reference the name "adityanet" in filenames — none contain a copy of the project tree.

**Important finding: this directory is not a Git repository.** No `.git` directory exists at `/Users/soumyadebtripathy/AdityaNet` or any parent, and `git rev-parse --is-inside-work-tree` fails with "not a git repository." Selection was therefore based on it being the sole directory on disk matching the project name, containing the expected project structure (`app/`, `README.md`, `requirements.txt`, `alembic/`, `data_pipeline/`, `artifacts/`, `venv/`, `.env`), and being the only actively-modified copy (most recent file timestamps are from today, 2026-07-01).

## 4. Copy

- Source: `/Users/soumyadebtripathy/AdityaNet/`
- Destination: `/Volumes/T7 Shield/Projects/AI/AdityaNet/`
- Method: `rsync -a` (archive mode: recursive, preserves symlinks, timestamps, and permissions to the extent the destination filesystem supports).
- Hidden files (`.env`, `.env.example`, `.claude/`, `.DS_Store`) were included.
- The `venv/` directory (1.0 GB) was included because it is required to run/develop the project without rebuilding the environment.
- rsync reported **0 errors** and exit code 0.

### Symlinks (5 found in source, all preserved in destination)

| Symlink | Target | Notes |
|---|---|---|
| `brain` | `/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/3ec42318-ed37-471e-b5fd-4a0ca103f854` | **Points outside the project**, into another tool's (Gemini CLI / antigravity) data store. The symlink itself was copied as-is (still points to the original absolute path on the internal disk, since ExFAT emulation preserved the literal link text). The target content was **not** copied, per instructions not to move unrelated projects/data. If AdityaNet code depends on reading through `brain/`, it will only resolve while the internal disk is present. Flagged for user decision — see Recommendations. |
| `artifacts/tensorboard` | `runs` (relative, internal to `artifacts/`) | Preserved correctly; resolves fine on the SSD. |
| `venv/bin/python3` | `python3.12` (relative, internal to `venv/bin/`) | Preserved correctly. |
| `venv/bin/python` | `python3.12` (relative, internal to `venv/bin/`) | Preserved correctly. |
| `venv/bin/python3.12` | `/opt/homebrew/opt/python@3.12/bin/python3.12` (external, system Homebrew Python) | Expected venv behavior — points at the system Python interpreter, not project data. Verified working from the new location. |

## 5. Verification — File/Folder Counts and Size

| Metric | Source | Destination | Match |
|---|---|---|---|
| Regular files | 40,153 | 40,153 | ✅ |
| Directories | 2,992 | 2,992 | ✅ |
| Symlinks | 5 | 5 | ✅ |
| Total logical (apparent) size | 29.3088 GB | 29.3088 GB | ✅ |

A checksum-based dry-run comparison (`rsync -avn --checksum`) was run after the copy. Result: **every one of the 40,153 real project files matches byte-for-byte** between source and destination. No content differences were found.

### Explaining the raw `du -sh` discrepancy (29G source vs 39G destination)

A naive `du -sh` on the destination initially showed 39G vs 29G on the source, and a doubled file count (83,302 vs 40,153) via `find -type f`. Root-caused directly, not guessed:

1. **43,149 extra files** are macOS "AppleDouble" sidecar files (`._filename`), auto-created by the OS on ExFAT to store extended attributes/resource forks that ExFAT can't hold natively (APFS, the source filesystem, doesn't need these). They total 231 MB and contain no project data — they are OS metadata shadows, not part of AdityaNet. Excluding them, destination file count is exactly 40,153, matching source.
2. **The remaining ~10 GB apparent gap** was a `du` block-accounting artifact: ExFAT on this volume uses a 128 KB allocation block size (vs APFS's much smaller blocks), which inflates on-disk usage for many small files (internal fragmentation). Comparing **logical/apparent byte size** instead (`stat -f%z` summed over all files) gives **29.3088 GB on both sides**, an exact match.

Neither discrepancy reflects missing or corrupted data.

## 6. Git Verification

**Not applicable — source has no Git history.** `/Users/soumyadebtripathy/AdityaNet` was never initialized as a Git repository (no `.git` directory, confirmed by direct filesystem inspection and `git rev-parse` failing in the source itself). Therefore `git status`, `git remote -v`, and `git log` cannot be run in either the source or the destination — this is a pre-existing condition of the project, not a migration defect. The destination correctly mirrors this (also no `.git`).

## 7. Python Verification

- Copied venv Python binary runs correctly from the new path: `Python 3.12.12` (via `venv/bin/python3` → `venv/bin/python3.12` → `/opt/homebrew/opt/python@3.12/bin/python3.12`).
- `pip 25.3` operational from the new venv location.
- All 18 packages pinned in `requirements.txt` import successfully from the SSD copy with matching versions (fastapi 0.111.0, uvicorn 0.30.1, sqlmodel 0.0.19, asyncpg 0.29.0, redis 5.0.4, pydantic-settings 2.3.1, python-dotenv, greenlet 3.0.3, alembic 1.13.1, pandas 2.2.2, pandera 0.19.2, numpy 1.26.4, pyarrow 16.1.0, scikit-learn 1.5.0, netCDF4 1.7.4, torch 2.12.0, tensorboard 2.20.0, matplotlib 3.11.0). No failures.
- Project's own code imports successfully: `import app` and `from app.core import config` both succeed from the SSD copy.
- **No retraining, evaluation, or heavyweight execution was performed** — only lightweight `import` statements and `--version` checks, per instructions.

## 8. Project Structure Verification

Checked all top-level directories named as examples in the migration instructions, against the SSD copy:

| Expected (example) | Present in destination? | Notes |
|---|---|---|
| `artifacts` | ✅ Yes (104 subfolders) | |
| `app` | ✅ Yes | Contains `api/`, `core/`, `db/`, `models/`, `schemas/`, `services/`, `main.py` |
| `scratch` | ✅ Yes | |
| `models` | Not present as a top-level folder | Confirmed **also absent in source** — model code actually lives at `app/models/`, trained artifacts at `artifacts/models/` and `artifacts/models_v3/`. Not a copy defect. |
| `services` | Not present as a top-level folder | Confirmed **also absent in source** — lives at `app/services/`. Not a copy defect. |
| `datasets` | Not present as a top-level folder | Confirmed **also absent in source** — lives at `data_pipeline/datasets/`. Not a copy defect. |
| `documentation` | Not present as a top-level folder | Confirmed **also absent in source** — docs are distributed as `README.md`, `PROJECT_STATUS.md`, `benchmark_protocol.md`, `operator_casebook.md`, and various `validation_report_*.md` / `scientific_*` files at the repo root. Not a copy defect. |

Other verified-present top-level items: `data/`, `data_pipeline/`, `scripts/`, `legacy/`, `logs/`, `raw-data/`, `venv/`, `alembic/`, `.env`, `.env.example`, `.claude/`, `requirements.txt`, `docker-compose.yml`, `alembic.ini`.

No files were modified, opened for writing, or deleted in the source or destination during verification (all checks were read-only: `import`, `--version`, `git rev-parse`, `find`, `du`, `rsync --dry-run`).

## 9. Missing Files / Copy Errors

**None.** rsync reported 0 errors across the full transfer. The checksum verification pass found zero content mismatches in the 40,153 real project files. The only file that changed between the initial copy and final verification was `.claude/settings.local.json` — this is Claude Code's own live session-permissions file, which was being actively appended to *during this migration session itself* (unrelated to AdityaNet's ML content). It was re-synced as the final step and now matches exactly.

## 10. Limitations / Recommendations

1. **ExFAT does not preserve Unix permissions, ownership, or symlink semantics as robustly as APFS.** The mount uses `noowners`, so file ownership on the SSD copy is nominal (mapped to the mounting user) rather than truly preserved bit-for-bit. Executable bits on scripts (`verify.sh`, `venv/bin/*`) were checked and remained functional in spot checks, but if any script relies on exact permission bits (e.g. group/other restrictions), verify before relying on them in production.
2. **AppleDouble (`._*`) sidecar files**: 43,149 of these now exist on the destination (231 MB), generated automatically by macOS because ExFAT lacks native extended-attribute support. They are harmless but add clutter; they can be safely deleted with `dot_clean "/Volumes/T7 Shield/Projects/AI/AdityaNet"` if desired — **not done automatically**, since Step 9 prohibits any cleaning/deletion.
3. **`brain` symlink** (`/Users/soumyadebtripathy/AdityaNet/brain`) points outside the project into Gemini CLI's internal data store (`~/.gemini/antigravity-cli/brain/...`) on the internal disk. It was preserved as a symlink but its target was intentionally **not copied** onto the SSD, per the instruction not to move unrelated projects. If AdityaNet's build/train/eval workflow actually reads through this symlink at runtime, it will silently fail once the SSD is used on another machine (or if the internal disk's Gemini data is ever cleared) — recommend the user clarify whether this symlink's target should be treated as part of "everything required to build/train/evaluate AdityaNet" and, if so, copy it in explicitly as a follow-up.
4. **No Git repository exists** for this project at all (source or destination). If version control is desired going forward, recommend running `git init` in the SSD copy (or the original) as a separate, explicit action — not performed here since it would alter the project state beyond a pure migration.
5. The project is now fully self-contained at `/Volumes/T7 Shield/Projects/AI/AdityaNet` and verified functional (Python/venv/imports all pass). The original at `/Users/soumyadebtripathy/AdityaNet` was **not deleted or modified** — this was a copy, not a move. Deleting the original was intentionally left for the user to confirm separately.

---

**Summary**: 40,153 files / 2,992 folders / 5 symlinks / 29.3088 GB copied with zero errors and a verified byte-for-byte checksum match. Python environment and all dependencies confirmed working from the new SSD path without any retraining or data modification.

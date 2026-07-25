# Validation Report — Sprint 19A Complete Repository and Restart Readiness Audit

This independent validation report presents the verification results for the Sprint 19A repository state and restart readiness audit. All facts, file counts, dimensions, checkpoints, dependencies, and datasets have been recomputed directly from the repository, independent of the generated artifacts.

## Overall Status: FAIL

While the core datasets, model checkpoints, and repository files are intact and verify to the single byte, the overall audit status is **FAIL** due to structural inconsistencies in the reported dependency graph and a path configuration discrepancy in the validation inventory.

***

## Detailed Verification Checklist

### 1. Dependency Graph
- **Status: FAIL**
- **Discrepancies:** The reported dependency graph (`dependency_graph.csv`) contains 8 bi-directional symmetry gaps:
  1. `Window generation` lists `Training pipeline` as downstream dependent, but `Training pipeline` direct dependencies do not list `Window generation`.
  2. `Training pipeline` lists `Calibration pipeline` as downstream dependent, but `Calibration pipeline` direct dependencies do not list `Training pipeline`.
  3. `Explainability` lists `Model architectures` as direct dependency, but `Model architectures` downstream dependents do not list `Explainability`.
  4. `Anomaly taxonomy` lists `Evaluation pipeline` as direct dependency, but `Evaluation pipeline` downstream dependents do not list `Anomaly taxonomy`.
  5. `Operator trust layer` lists `Evaluation pipeline` as direct dependency, but `Evaluation pipeline` downstream dependents do not list `Operator trust layer`.
  6. `Statistical validation` lists `Evaluation pipeline` as direct dependency, but `Evaluation pipeline` downstream dependents do not list `Statistical validation`.
  7. `Artifact generation` lists `Evaluation pipeline` as direct dependency, but `Evaluation pipeline` downstream dependents do not list `Artifact generation`.
  8. `Artifact generation` lists `Statistical validation` as direct dependency, but `Statistical validation` downstream dependents do not list `Artifact generation`.

### 2. Build Cost Inventory
- **Status: PASS**
- **Verification:** All 9 pipeline stages and their scripts listed in `pipeline_inventory.csv` exist. Their execute permissions match filesystem observations (all are non-executable python files, so `executable_status` is correctly reported as `False`).

### 3. Project State
- **Status: PASS**
- **Verification:** All 19 subsystem classifications match `project_state.csv` and `restart_readiness.json` exactly:
  - **Observed (16):** Datasets, Feature engineering, Data preprocessing, Window generation, Dataset splits, Model architectures, Evaluation pipeline, Calibration pipeline, Threshold optimization, Operator trust layer, Explainability, Anomaly taxonomy, Statistical validation, Bootstrap validation, Artifact generation, Documentation.
  - **Partially Active (3):** Training pipeline, Inference pipeline, Deployment code.

### 4. Technical Debt
- **Status: PASS**
- **Verification:** The 4 outstanding work items reported in the project status exist and their repo status is verified:
  1. Encoder pretraining is halted at Epoch 1 (model checkpoint epoch metadata shows `NOT AVAILABLE`).
  2. Production ML inference endpoints load the V1 model (loaded checkpoint has architecture `PatchTST` instead of V3 `LateFusionPatchTST`).
  3. Real-time telemetry streaming from ISRO databases is outstanding.
  4. Chronological generalization validation after the 2026-06-14 cutoff is outstanding.

### 5. Restart Impact Matrix
- **Status: FAIL**
- **Discrepancies:** Because of the 8 bi-directional symmetry gaps identified in the dependency graph, the restart impact matrix (which relies on the upstream/downstream relationships) is structurally inconsistent.

### 6. Training Inventory
- **Status: PASS**
- **Verification:** All 14 checkpoints in `checkpoint_inventory.csv` exist. Their sizes, SHA256 checksums, tensor counts, parameter counts, epochs, and architecture names were loaded and verified to match exactly.

### 7. Immutable Assets
- **Status: FAIL**
- **Discrepancies:** `validation_report_18a.md` exists in the repository root at `validation_report_18a.md` but was configured in the audit script as `artifacts/validation_report_18a.md`. Because the file was not found at the configured path, it was omitted from the `validation_inventory.csv` deliverable.

### 8. Rebuild Candidates
- **Status: PASS**
- **Verification:** Only the 3 partially active subsystems (Training pipeline, Inference pipeline, Deployment code) are classified as rebuild candidates. No reusable component (observed subsystems) is incorrectly classified.

### 9. Summary Counts
- **Status: PASS**
- **Verification:**
  - **Reusable components:** 16 (observed subsystems)
  - **Rebuild candidates:** 3 (partially active subsystems)
  - **Verified artifacts:** 25 (5 validation reports + 20 statistical artifacts)
  - **Unfinished components:** 3 (partially active subsystems)
  - **Deprecated components:** 1 (`legacy/pradan_downloader.sh`)

### 10. Repository Integrity
- **Status: PASS**
- **Verification:** Once the validation script files and temporary checkpoints/dataset test files are excluded, and the size of `scratch/validation_summary.json` is restored to its original value, all file counts and sizes match the expected 8,807 total files, 30,437,754,058 total bytes, and 235,298,879 code bytes exactly. All 6 datasets and 14 checkpoints match their original sizes and SHA256 hashes.

***

## Summary of Discrepancies

| Subsystem / Deliverable | Field | Expected | Observed / Actual | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Dependency Graph** | Symmetry bi-directionality | Bi-directional links | Missing upstream/downstream links (8 gaps) | Structural graph inconsistency |
| **Restart Impact Matrix** | Downstream dependencies | Consistent dependency tree | Inconsistent tree | Broken downstream impact tracing |
| **Immutable Assets** | `validation_report_18a.md` | Omitted | Present at root `validation_report_18a.md` | Configured path error in audit |

***

## Verification Environment

- **Operating System:** macOS-26.5.1-arm64-arm-64bit-Mach-O
- **Processor:** arm (Apple Silicon)
- **Accelerator:** MPS
- **Python Version:** 3.14.4
- **Core Library Versions:**
  - PyTorch: `2.9.1`
  - NumPy: `2.3.5`
  - Pandas: `2.3.3`
  - Scikit-Learn: `1.7.2`

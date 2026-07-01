# Version 3 Scientific Benchmark Protocol

This document establishes the official scientific evaluation protocol for the **Version 3 Multi-Instrument Solar Flare Forecasting Pipeline** (AdityaNet). All future experiments, model developments, and evaluations MUST reference and adhere to the specifications detailed below.

---

## 1. Dataset & Features

### Dataset Versions
*   **Version:** Version 3 (V3) Scientific Benchmark Dataset (derived from GOES, SoLEXS, and HEL1OS instruments).
*   **cadence:** 1-minute cadence.

### Parquet Hashes (SHA-256)
*   **Training Set (`s2_train.parquet`):** `8fba40164aa14c4f7ba94af5794882fd9f72f26e6084848236eae30e7f9b46b4`
*   **Validation Set (`s2_val.parquet`):** `e8e3d43fed06088f1a2a4ea43c6959f66f7041f4bed2b41f8e65b70a78eebb0b`
*   **Test Set (`s2_test.parquet`):** `d2680df034a334e3eef632cb63dfb4b031f932b9df5e7eabd8aa2572d53e1bb7`

### Feature Manifest Hash (SHA-256)
*   **Feature Columns Spec (`artifacts/feature_columns_v3.json`):** `c5142e4a0d492f44ce67aa505bc47a676be2bcbd5c0e6c211960556dda74b82a`

---

## 2. Windowing & Partitioning

### Split Boundaries (Temporal Range)
*   **Stage 2 Training Split:** `2023-12-13 00:00:00` to `2025-06-14 23:59:00` (inclusive)
*   **Stage 2 Validation Split:** `2025-06-15 00:00:00` to `2025-12-14 23:59:00` (inclusive)
*   **Stage 2 Test Split:** `2025-12-15 00:00:00` to `2026-06-14 23:59:00` (inclusive)

### Window Configuration
*   **Sequence Length:** `360` minutes (6 hours input history).
*   **Window Stride:** `1` minute sliding window.
*   **Target Window:** `6` hour look-ahead binary flare target (`target_6hr_binary`).

---

## 3. Calibration & Threshold Protocols

### Calibration Protocol
*   **Primary Method:** Isotonic Regression fitted on validation split predictions and applied to test split predictions.
*   **Secondary Method:** Temperature Scaling fitted on validation split logits (optimizing temperature parameter $T$).

### Threshold Protocol
*   **Optimal Threshold Selection:** Validation-optimal threshold obtained by running a grid sweep over validation probabilities to maximize the **True Skill Score (TSS)**.
*   **Test Application:** The validation-optimal threshold is frozen and applied to test set calibrated probabilities to obtain binary alert levels without test leakage.

### Alert Operator Policy
*   **Alert Levels:**
    *   **GREEN:** Probability $<$ validation-optimal yellow threshold.
    *   **YELLOW:** Validation-optimal yellow threshold $\le$ Probability $<$ validation-optimal red threshold.
    *   **RED:** Probability $\ge$ validation-optimal red threshold.
*   **Tiered Uncertainty Suppression:** Alerts are suppressed based on MC Dropout epistemic uncertainty (std dev $\sigma$):
    *   Suppress all to **GREEN** if $\sigma > 0.20$.
    *   Suppress **YELLOW** / **RED** to **GREEN** if $\sigma > 0.15$.
    *   Suppress **RED** to **YELLOW** if $\sigma > 0.10$.
*   **RED Confirmation:** A RED alert is only confirmed if the rolling mean of the last 3 predictions exceeds the red threshold AND the slope of those predictions is positive (rising trend). Otherwise, it is downgraded to YELLOW.

---

## 4. Model & Training Hyperparameters

### Model Architecture
*   **Class:** `LateFusionPatchTST`
*   **Total Parameters:** `4,353,217` parameters (under the 5,000,000 parameter budget cap).
*   **Branches:**
    *   **GOES Branch:** Embedding dim = 128, Transformer layers = 4
    *   **SoLEXS Branch:** Embedding dim = 160, Transformer layers = 5
    *   **HEL1OS Branch:** Embedding dim = 160, Transformer layers = 5
*   **Fusion Mechanism:** Cross-Attention (Multi-Head Attention) followed by MLP classification head.

### Random Seed Policy
*   **Global Seed:** `42`
*   **Seeding Code:**
    ```python
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)
    ```

### Training Parameters (Stage 2)
*   **Optimizer:** `AdamW`
*   **Learning Rate:** `5e-5`
*   **Weight Decay:** `1e-4`
*   **Batch Size:** `128`
*   **Effective Batch Size:** `256` (via gradient accumulation steps = 2)
*   **Mixed Precision Settings:** PyTorch automatic mixed precision (`torch.amp.autocast`) with `bfloat16` enabled for MPS acceleration.
*   **Gradient Clipping:** L2 norm clipped at `1.0`.
*   **Loss Function:** Focal Loss with $\gamma = 2.0$ and $\alpha$ clamped between $0.25$ and $0.75$ based on the class imbalance ratio.

---

## 5. System & Software Specs

### Hardware
*   **Processor:** Apple M4 (MacBook Air)
*   **Memory:** 16 GB Unified Memory
*   **Acceleration Device:** Metal Performance Shaders (MPS) backend

### Software Versions
*   **OS:** macOS 26.5.1
*   **Python:** 3.12.12
*   **PyTorch:** 2.12.0
*   **NumPy:** 1.26.4 or compatible
*   **Pandas:** 2.2.2 or compatible

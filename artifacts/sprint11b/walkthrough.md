# Sprint 11B — Multi-Instrument Feasibility & Dataset Design Audit Walkthrough

This document presents a comprehensive summary of the scientific feasibility audit conducted for the new Version 3 Multi-Instrument forecasting system using GOES, SoLEXS, and HEL1OS.

---

## 1. Multi-Instrument Temporal Overlap

Based on the forensic audit of processed parquet files on disk:

*   **GOES Processed Telemetry:**
    *   First timestamp: `2010-01-02 00:00:00`
    *   Last timestamp: `2026-06-14 23:59:00`
    *   Sampling cadence: `60.0 seconds`
    *   Total observations: `8,631,360`
    *   Processed parquet files: `1` ([goes_full.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/goes_full.parquet))
    *   Missing intervals: `0`
*   **SoLEXS Processed Telemetry:**
    *   First timestamp: `2023-12-13 00:00:00`
    *   Last timestamp: `2026-06-14 23:59:55`
    *   Sampling cadence: `5.0 seconds`
    *   Total observations: `15,811,200`
    *   Processed parquet files: `915` in `data/aditya_l1/processed/solexs/`
    *   Missing intervals: `0` (within day-files; observation outages occur as complete missing day parquets)
*   **HEL1OS Processed Telemetry:**
    *   First timestamp: `2023-10-29 00:00:00`
    *   Last timestamp: `2026-06-14 23:59:55`
    *   Sampling cadence: `5.0 seconds`
    *   Total observations: `16,588,800`
    *   Processed parquet files: `960` in `data/aditya_l1/processed/hel1os/`
    *   Missing intervals: `0` (within day-files)

### Common Temporal Overlap
*   **Start Timestamp:** `2023-12-13 00:00:00` (determined by SoLEXS launch/activation date)
*   **End Timestamp:** `2026-06-14 23:59:00` (determined by GOES data freeze boundary)
*   **Overlap Duration:** `79,055,940` seconds (**`914.999` days**)
*   **Overlap Percentages:**
    *   Relative to GOES timeline: **15.23%** (GOES covers 16.5 years; overlap is ~2.5 years)
    *   Relative to SoLEXS timeline: **100.00%**
    *   Relative to HEL1OS timeline: **95.31%** (HEL1OS started ~1.5 months before SoLEXS)

---

## 2. Dataset Design Options

Every scientifically valid partition strategy is detailed below:

*   **Option A: Current GOES-only baseline**
    *   *Train:* 2010-01-02 to 2019-12-31 | *Val:* 2020-01-01 to 2022-12-31 | *Test:* 2023-01-01 to 2026-06-14
    *   *Leakage Risk:* Low (chronologically isolated)
    *   *Operator Comparability:* Direct (Version 1 baseline: TSS=0.2298, ROC-AUC=0.7485)
    *   *Scientific Novelty:* None
    *   *Advantages:* Large data volume (16 years, 5.1M training windows); captures long-term solar cycle dynamics.
    *   *Limitations:* Blind to spatial and spectral resolution from Aditya-L1 instruments.
*   **Option B: Aditya-L1 only**
    *   *Train:* 2023-12-13 to 2025-06-14 | *Val:* 2025-06-15 to 2025-12-14 | *Test:* 2025-12-15 to 2026-06-14
    *   *Leakage Risk:* Low (temporally split)
    *   *Operator Comparability:* Zero (test set dates and distribution do not match baseline)
    *   *Scientific Novelty:* High (first model solely based on Indian solar space observatory telemetry)
    *   *Advantages:* High-cadence (5s) soft and hard X-ray measurements directly utilized.
    *   *Limitations:* Very short duration (~2.5 years total); lacks historical contexts of Solar Cycle 24.
*   **Option C: GOES + SoLEXS + HEL1OS common-overlap dataset**
    *   *Train:* 2023-12-13 to 2025-06-14 | *Val:* 2025-06-15 to 2025-12-14 | *Test:* 2025-12-15 to 2026-06-14
    *   *Leakage Risk:* Medium (timestamp alignment must be strictly causal)
    *   *Operator Comparability:* Low (evaluation test set is restricted to overlap phase)
    *   *Scientific Novelty:* High (multi-instrument satellite fusion for nowcasting)
    *   *Advantages:* Combines continuous solar background (GOES) with high-cadence local diagnostics.
    *   *Limitations:* Discards 13 years of historical GOES training data.
*   **Option D: Transfer learning strategy (pretrain on GOES, fine-tune on overlap)**
    *   *Train:* Pretrain on GOES 2010-01-02 to 2023-12-12; Fine-tune on Overlap 2023-12-13 to 2025-06-14 | *Val:* Overlap 2025-06-15 to 2025-12-14 | *Test:* Overlap 2025-12-15 to 2026-06-14
    *   *Leakage Risk:* Medium (requires strict boundaries between pretraining and validation splits)
    *   *Operator Comparability:* Medium (comparable if baseline model is re-evaluated on the overlap test split)
    *   *Scientific Novelty:* Very High (cross-instrument satellite representation learning)
    *   *Advantages:* Retains 14 years of historical context while fine-tuning on high-resolution local features.
    *   *Limitations:* Architectural complexity (requires projecting variable input features).

---

## 3. Feature Alignment and Synchronization

*   **Sampling Cadence:** GOES is 1-minute cadence; SoLEXS and HEL1OS are 5-second cadence.
*   **Resampling Strategy:**
    *   *Downsampling Aditya-L1 to 1-minute:* Resample using mean/max/std to match the 1-minute GOES grid. This preserves sequence token length (360 tokens = 6 hours) and is highly compatible with the current PatchTST model.
    *   *Upsampling GOES to 5-second:* Linear interpolation or forward-fill. This increases token length to 4,320, which exceeds computational constraints.
*   **Tolerances:** Timestamp alignment tolerance of +/- 30 seconds for 1-minute grids.
*   **Missing Values:** Samplings show 0.0% missing rate in day parquets. Gaps exist between days due to instrument duty cycles (occupying ~49% of calendar days).
*   **Time Sync:** UTC GPS time tags (GOES) aligned with Modified Julian Date (MJD) or epoch seconds (Aditya-L1) using astropy converters.
*   **Available Channels:**
    *   GOES: `short_flux` (0.05-0.4 nm), `long_flux` (0.1-0.8 nm).
    *   SoLEXS: `solexs_sdd2_lc_counts`, `solexs_sdd2_spec_counts_ch13 to ch37` (25 soft-to-hard channels).
    *   HEL1OS: `hel1os_band_*_ctr` (lightcurves for 5 bands), `hel1os_counts_ch0 to ch339` (340 spectral channels), event counts CZT/CdTe.

---

## 4. Architecture Candidates

1.  **Single-stream PatchTST:**
    *   *Input:* Concatenated 1-minute grid shape `[batch, 360, n_features]`.
    *   *Fusion:* Early Fusion.
    *   *Parameters:* ~1.2M (EMBED_DIM=128) to ~4.5M (EMBED_DIM=256).
    *   *Latency:* 15ms - 30ms.
    *   *Compatibility:* Extremely High (minor configuration tweaks).
2.  **Late Fusion PatchTST:**
    *   *Input:* Three separate inputs for GOES, SoLEXS, and HEL1OS.
    *   *Fusion:* Late Fusion (CLS tokens concatenated/averaged).
    *   *Parameters:* ~2.5M.
    *   *Latency:* 40ms - 60ms.
    *   *Compatibility:* High (defines parallel submodules in model.py).
3.  **Cross-Attention Fusion:**
    *   *Input:* Three separate inputs.
    *   *Fusion:* Cross-Attention (GOES attends to SoLEXS and HEL1OS tokens).
    *   *Parameters:* ~3.5M to ~5.0M.
    *   *Latency:* 60ms - 90ms.
    *   *Compatibility:* Medium (custom transformer layers).
4.  **Hierarchical Fusion:**
    *   *Input:* Mixed cadence (5s Aditya-L1, 1m GOES).
    *   *Fusion:* High-frequency local encoders process 5s inputs to 1m, then fuse.
    *   *Parameters:* ~2.0M to ~4.0M.
    *   *Latency:* 50ms.
    *   *Compatibility:* Medium-to-Low (requires custom data loaders and pooling heads).
5.  **Temporal Fusion Transformer (TFT):**
    *   *Input:* Multivariate sequences.
    *   *Fusion:* Gated Residual Networks (GRNs) and variable selection.
    *   *Parameters:* ~4.0M to ~8.0M.
    *   *Latency:* 80ms - 120ms.
    *   *Compatibility:* Low (major structural rewrite).

---

## 5. Risk Register

*   **R1: Distribution Shift (Severity: CRITICAL)**
    *   *Evidence:* Positive label rate is 0.62% in Train, 4.07% in Validation, and 23.20% in Test.
    *   *Mitigation:* Class-balanced loss functions (Focal Loss) and validation-set threshold tuning.
*   **R2: Sensor Drift (Severity: HIGH)**
    *   *Evidence:* No calibration layers exist in feature pipelines.
    *   *Mitigation:* Differential/gradient features or satellite status self-calibration.
*   **R3: Telemetry Outages (Severity: HIGH)**
    *   *Evidence:* Calendar coverage shows 49% gaps in SoLEXS/HEL1OS parquets.
    *   *Mitigation:* Zero-masking for missing instruments or forward-filling.
*   **R4: Cadence Mismatch (Severity: MEDIUM)**
    *   *Evidence:* GOES is 1m; Aditya-L1 is 5s. Resampling is required.
    *   *Mitigation:* Downsampling Aditya-L1 to 1m.
*   **R5: Overfitting (Severity: HIGH)**
    *   *Evidence:* Overlap training split is only 1.5 years compared to 10-year baseline.
    *   *Mitigation:* Transfer learning (pretrain on GOES-only) or strong regularization.
*   **R6: Evaluation Fairness (Severity: MEDIUM)**
    *   *Evidence:* Baseline test set includes dates before SoLEXS activation.
    *   *Mitigation:* Evaluate baseline on the overlap test sub-split.
*   **R7: Deployment Dependency (Severity: HIGH)**
    *   *Evidence:* Inference endpoint requires a single concatenated matrix. Missing streams cause errors.
    *   *Mitigation:* Implement real-time fallbacks to GOES-only model.

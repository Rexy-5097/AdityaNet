# Version 3 Late Fusion PatchTST Architecture: Integration & Verification Report

This document details the architectural design, shape flows, parameter audits, and integration status of the new **Version 3 Late Fusion PatchTST** forecasting model.

---

## 1. Structural Design and Specifications

The Version 3 model is designed to integrate GOES, SoLEXS, and HEL1OS observations in a unified, robust multi-instrument model, while remaining under a strict **5,000,000 parameter budget** and providing fallback operation when telemetry streams are missing.

### Asymmetrical Encoders
To maximize predictive capacity, we allocate model parameters asymmetrically based on the physical information content of each instrument:
*   **GOES Encoder:** Process 14 features using a 4-layer PatchTST encoder with an embedding dimension of `128` and feedforward dimension of `512` (~822K parameters).
*   **SoLEXS Encoder:** Process 25 features using a 5-layer PatchTST encoder with an embedding dimension of `160` and feedforward dimension of `640` (~1.6M parameters).
*   **HEL1OS Encoder:** Process 10 features using a 5-layer PatchTST encoder with an embedding dimension of `160` and feedforward dimension of `640` (~1.6M parameters).

### Attention Pooling
Instead of relying solely on a fixed `CLS` token, each instrument's encoder output (`[batch, 45, d_model]`) is mapped to a single vector using an **Attention Pooling** module. A learnable query token attends to the sequence of 44 temporal patches, dynamically compressing the full sequence context while preserving temporal relations.

### Learnable Missing Tokens
If SoLEXS or HEL1OS is missing (due to instrument duty cycles or transmission outages), their pooled embedding vectors are replaced by a learnable **missing token** parameter (`missing_token_solexs` / `missing_token_hel1os`). This allows the model to learn the semantic representation of missing telemetry rather than assuming a zero-state input.

### Cross-Attention Fusion
Projected embeddings (`fusion_dim=128`) are stacked into a sequence of shape `[batch, 3, 128]`. A multi-head self-attention layer allows the tokens representing each instrument to exchange information (cross-attention late fusion) before being flattened and projected to the final binary logit.

---

## 2. Tensor Shape Propagation

The tensor shapes propagate through the network as follows:

| Layer / Operation | Input Shape | Output Shape | Notes |
| :--- | :---: | :---: | :--- |
| **GOES Input** | `[B, 360, 14]` | `[B, 360, 14]` | 14 physics-aware features |
| **SoLEXS Input** | `[B, 360, 25]` | `[B, 360, 25]` | 25 spectral channels |
| **HEL1OS Input** | `[B, 360, 10]` | `[B, 360, 10]` | 10 band lightcurves |
| **GOES PatchEmbedding** | `[B, 360, 14]` | `[B, 44, 128]` | `patch_len=16`, `stride=8` |
| **SoLEXS PatchEmbedding** | `[B, 360, 25]` | `[B, 44, 160]` | `patch_len=16`, `stride=8` |
| **HEL1OS PatchEmbedding** | `[B, 360, 10]` | `[B, 44, 160]` | `patch_len=16`, `stride=8` |
| **GOES Encoder** | `[B, 45, 128]` | `[B, 45, 128]` | Prepend CLS token + PE |
| **SoLEXS Encoder** | `[B, 45, 160]` | `[B, 45, 160]` | Prepend CLS token + PE |
| **HEL1OS Encoder** | `[B, 45, 160]` | `[B, 45, 160]` | Prepend CLS token + PE |
| **GOES Attention Pooling** | `[B, 45, 128]` | `[B, 128]` | Learnable query token pooling |
| **SoLEXS Attention Pooling** | `[B, 45, 160]` | `[B, 160]` | Learnable query token pooling |
| **HEL1OS Attention Pooling** | `[B, 45, 160]` | `[B, 160]` | Learnable query token pooling |
| **SoLEXS Masking / Missing** | `[B, 160]` | `[B, 160]` | Mask with learnable token |
| **HEL1OS Masking / Missing** | `[B, 160]` | `[B, 160]` | Mask with learnable token |
| **Instrument Projections** | `[B, 160]` | `[B, 128]` | Projected to common `fusion_dim=128` |
| **Tokens Stack** | `[B, 128] × 3` | `[B, 3, 128]` | Stacked along dimension 1 |
| **Fusion Attention** | `[B, 3, 128]` | `[B, 3, 128]` | Multihead self-attention |
| **Flat & Classification Head** | `[B, 3, 128]` | `[B, 1]` | Flattened to 384 → nn.Linear |

---

## 3. Verification and Latency Profile

The integration verification script `scratch/verify_late_fusion_model.py` was executed successfully:

*   **Total Trainable Parameters:** **`4,386,497`** (Budget limit = `5,000,000` cap)
*   **Verification Status:** **`PASSED`**
*   **Average Inference Latency (Batch=8):** **`10.81 ms`**
*   **Execution Fallbacks Verified:**
    *   **All Instruments Present:** Success (`Output shape: [8, 1]`)
    *   **SoLEXS Missing (Masked):** Success (`Output shape: [8, 1]`)
    *   **SoLEXS Input is None (Raw Gaps):** Success (`Output shape: [8, 1]`)
    *   **SoLEXS & HEL1OS Inputs are None (GOES-only fallback):** Success (`Output shape: [8, 1]`)

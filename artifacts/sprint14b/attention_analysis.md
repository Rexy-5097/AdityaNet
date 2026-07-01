# Attention Analysis & Interpretability Diagnostics

This report presents the attention diagnostics of the Late Fusion PatchTST model.

## 1. Fusion Attention Matrix (3x3)
Average cross-attention weights between projected encoder embeddings:
```
        GOES      SoLEXS    HEL1OS
GOES    0.6648    0.1494    0.1858
SoLEXS  0.3581    0.3255    0.3164
HEL1OS  0.4191    0.2978    0.2831
```

## 2. Encoder Attention Entropy
*   **GOES Encoder Layer-1 Entropy:** `3.3818`
*   **SoLEXS Encoder Layer-1 Entropy:** `3.7988`
*   **HEL1OS Encoder Layer-1 Entropy:** `3.8037`

High entropy values indicate that the model distributes attention broadly across temporal patches to capture macro solar evolution, whereas low entropy values indicate focus on transient peaks.

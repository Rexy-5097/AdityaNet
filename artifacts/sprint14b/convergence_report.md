# Version 3 Convergence Analysis Report

**Validation Date:** 2026-06-19  
**Status:** **CONVERGED**

This report documents the learning dynamics and training convergence of the upgraded **Version 3 Late Fusion PatchTST** model.

## 1. Learning Curves and Diagnostics
*   **Stage 1 GOES Pretraining:** The model starts learning baseline GOES flux features quickly. Pretraining Focal loss decays smoothly from `0.02971` to `0.02111` by epoch 5, showing a clean stabilization without signs of overfitting.
*   **Stage 2 Fine-Tuning:** Dynamic unfreezing of the SoLEXS and HEL1OS encoders starts at Epoch 6. The loss stabilizes at `0.02306` by Epoch 10.
*   **Validation Checkpointing:** Epoch-wise metrics verify that model checkpoints match the best validation TSS checkpoint successfully.

## 2. Gradient Ingestion Stability
*   No NaN gradients or losses were encountered.
*   Average training throughput is `120.0` samples/second.
*   Gradient norm curves verify that parameters in the newly unfrozen SoLEXS and HEL1OS branches receive stable, non-zero gradient updates, confirming gradient propagation.

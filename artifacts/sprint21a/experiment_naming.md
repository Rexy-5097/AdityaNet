# SuryaNet V3 Experiment Naming Standard

## Experiment Identifier Scheme
Every experiment executed during the retraining campaign must follow this deterministic naming convention to avoid overlap and maintain traceability:

`V3_S{seed}_E{epochs}_LR{learning_rate}_WD{weight_decay}_{ablation_tag}`

### Fields:
*   `V3`: Model architecture version.
*   `S{seed}`: Random seed value (e.g. `S42`, `S123`, `S3407`, `S2026`, `S9999`).
*   `E{epochs}`: Maximum epochs configured (e.g. `E10`).
*   `LR{learning_rate}`: Learning rate parameter with decimal removed (e.g. `LR5e5` for `5e-5`).
*   `WD{weight_decay}`: Weight decay parameter (e.g. `WD1e4` for `1e-4`).
*   `{ablation_tag}`: Optional tag for instrument ablations (e.g. `GOES` for GOES-only, `GOES_SOLEXS` for GOES+SoLEXS, etc.). Omitted for full multi-instrument runs.

### Examples:
1.  **Full Multi-Instrument Run with Seed 42**: `V3_S42_E10_LR5e5_WD1e4`
2.  **GOES-only Ablation Run with Seed 123**: `V3_S123_E10_LR5e5_WD1e4_GOES`
3.  **GOES+HEL1OS Ablation Run with Seed 3407**: `V3_S3407_E10_LR5e5_WD1e4_GOES_HEL1OS`

# SuryaNet V3 Experiment Naming Standard
# Sprint 21B corrected — aligned with corrected_training_manifest.csv.

> IMPORTANT: This naming scheme is PROPOSED for the retraining campaign.
> Current repository checkpoints use the format model_seed_{seed}_stage{N}_best.pt.

## Proposed Identifier Scheme

V3_S{seed}_E{epochs}_LR{lr_stage2}_WD{weight_decay}[_{ablation_tag}]

### Field Definitions
- V3:             Model architecture version (LateFusionPatchTST).
- S{seed}:        Random seed. Campaign seeds: 42, 123, 3407, 2026, 9999.
- E{epochs}:      Maximum epochs configured (campaign default: E10).
- LR{lr_stage2}:  Stage 2 LR, decimal removed. LR5e5 means 5e-5.
- WD{weight_decay}: Weight decay, decimal removed. WD1e4 means 1e-4.
- {ablation_tag}: Optional. Absent for full multi-instrument runs (model-type D).
    GOES         -> --model-type A (GOES only)
    GOES_SOLEXS  -> --model-type B (GOES + SoLEXS)
    GOES_HEL1OS  -> --model-type C (GOES + HEL1OS)

## Canonical Experiment List (8 total, all unique)

Campaign Runs:
1. V3_S42_E10_LR5e5_WD1e4    seed=42,   --model-type D
2. V3_S123_E10_LR5e5_WD1e4   seed=123,  --model-type D
3. V3_S3407_E10_LR5e5_WD1e4  seed=3407, --model-type D
4. V3_S2026_E10_LR5e5_WD1e4  seed=2026, --model-type D
5. V3_S9999_E10_LR5e5_WD1e4  seed=9999, --model-type D

Ablation Runs (seed 42 only, reuses existing Stage 1 checkpoint):
6. V3_S42_E10_LR5e5_WD1e4_GOES        seed=42, --model-type A
7. V3_S42_E10_LR5e5_WD1e4_GOES_SOLEXS seed=42, --model-type B
8. V3_S42_E10_LR5e5_WD1e4_GOES_HEL1OS seed=42, --model-type C

Uniqueness: All 8 IDs verified unique. No duplicates.

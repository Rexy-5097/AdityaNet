# SuryaNet V3 Checkpoint Storage Standard
# Sprint 21B corrected — current practice vs proposed standard separated.

## SECTION 1 — CURRENT REPOSITORY CHECKPOINT PRACTICE (Historical Fact)

### Current Format
`scratch/run_sprint14c_experiment.py` saves checkpoints as a plain state dict:
  torch.save(model.state_dict(), path)
No metadata dictionary. No scheduler state. No optimizer state.
Sources: run_sprint14c_experiment.py (L288, L332, L382)

### Current Naming Convention
- Stage 1: artifacts/sprint14c/checkpoints/model_seed_{seed}_stage1_best.pt
- Stage 2: artifacts/sprint14c/checkpoints/model_seed_{seed}_stage2_best.pt

### Existing Checkpoints (pre-campaign, confirmed on disk)
- artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt  [EXISTS]
- artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt  [EXISTS]

### Scheduler State Note
No scheduler is active in run_sprint14c_experiment.py. There is no
scheduler_state_dict to save or restore in the current training script.

---

## SECTION 2 — PROPOSED CAMPAIGN CHECKPOINT STANDARD (PLANNED, NOT ACTIVE)

> All entries below are PROPOSED. These checkpoint files do not yet exist.

### Proposed Directory
artifacts/sprint21b/checkpoints/

### Proposed Naming
- Optimal: {experiment_id}_best.pt  (epoch with highest val_tss)
- Final:   {experiment_id}_last.pt  (final epoch state)

Planned checkpoint names are listed in corrected_training_manifest.csv
under the planned_checkpoint_name column. They DO NOT currently exist on disk.

### Proposed Metadata Dictionary Schema
- epoch: int
- val_tss: float
- model_state_dict: OrderedDict
- optimizer_state_dict: OrderedDict
- scheduler_state_dict: OrderedDict  (if CosineAnnealingLR is activated)
- hyperparameters: dict (from corrected_training_campaign_config.yaml)
- sha256_dataset: str (SHA256 of s2_train.parquet)

### Resume Verification
Before re-launching any interrupted run, verify the checkpoint is loadable
and val_tss matches the training log.

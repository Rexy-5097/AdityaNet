# SuryaNet V3 Checkpoint Storage Standard

## Directory Structure
Checkpoints generated during training runs must be saved under:
`artifacts/sprint21/checkpoints/`

## Checkpoint Naming Standard
For each experiment identifier (e.g. `V3_S42_E10_LR5e5_WD1e4`), two checkpoint files must be saved:
1.  **Optimal Checkpoint**: `{experiment_id}_best.pt` (represents the epoch with the optimal validation TSS).
2.  **Last Checkpoint**: `{experiment_id}_last.pt` (represents the final epoch state).

## Checkpoint Metadata Schema
Checkpoints must not be saved as a simple parameter state dict. Instead, they must be saved as a dictionary containing the following keys:
*   `epoch`: Integer representing the epoch at which the checkpoint was saved.
*   `val_tss`: Float representing the validation TSS score.
*   `model_state_dict`: OrderedDict of parameter weights.
*   `optimizer_state_dict`: OrderedDict of optimizer parameters (for resuming).
*   `scheduler_state_dict`: OrderedDict of learning rate scheduler parameters.
*   `hyperparameters`: Dictionary of all training hyperparameters from `training_campaign_config.yaml`.
*   `sha256`: SHA256 hash of the dataset split used.

## Verification & Resume
Resume capability must be verified by loading the optimizer and scheduler state dicts along with the parameter weights, preventing parameter mismatches.

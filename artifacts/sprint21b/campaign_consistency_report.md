# Sprint 21B: Campaign Consistency and Execution Readiness Report

## 1. Scope
Factual inconsistencies identified across Sprint 21A deliverables
and corrections applied in Sprint 21B. All findings from direct source inspection.

---

## 2. Inconsistencies Found and Corrected

### Inconsistency 1 — Scheduler Misclassification
File: campaign_matrix.csv (Sprint 21A)
Problem: scheduler column = CosineAnnealingLR for all 5 seed rows.
Fact: run_sprint14c_experiment.py has zero scheduler instantiations or .step() calls.
      Learning rate is constant per stage. CosineAnnealingLR only exists in
      trainer_v3.py (L177) Trainer class, which is not invoked by the active script.
Correction: Two columns added: scheduler_historical=NOT_ACTIVE, scheduler_proposed=CosineAnnealingLR (PROPOSED).

### Inconsistency 2 — Checkpoint Format Mismatch
File: checkpoint_standard.md (Sprint 21A)
Problem: Required scheduler_state_dict inside saved checkpoints.
Fact: run_sprint14c_experiment.py saves plain model.state_dict() only (L332, L382).
      No scheduler to serialize. trainer_v3.py Trainer class does save scheduler_state_dict (L389)
      but is not invoked.
Correction: corrected_checkpoint_standard.md separates current practice from proposed standard.

### Inconsistency 3 — Planned Checkpoints Implied to Exist
File: training_manifest.csv (Sprint 21A)
Problem: Listed V3_S{seed}_... checkpoint names without stating they do not exist.
Fact: Only model_seed_42_stage1_best.pt and model_seed_42_stage2_best.pt exist on disk.
Correction: Added status=PLANNED and historical_checkpoint_note columns.

### Inconsistency 4 — Ablation Commands Missing from campaign_commands.sh
File: campaign_commands.sh (Sprint 21A)
Problem: 3 ablation runs in manifest had no corresponding launch command.
Fact: run_sprint14c_experiment.py fully supports --model-type A/B/C (L215).
      --skip-stage1 allows reuse of existing seed 42 Stage 1 checkpoint.
Correction: 3 ablation commands added to corrected_campaign_commands.sh with --skip-stage1.

### Inconsistency 5 — Experiment Naming Examples Out-of-Scope
File: experiment_naming.md (Sprint 21A)
Problem: Examples implied seed 123 and 3407 ablation runs were planned.
Fact: Ablation runs are scheduled for seed 42 only in training_manifest.csv.
Correction: corrected_experiment_naming.md lists exactly the 8 canonical manifest entries.

### Inconsistency 6 — Incorrect Alpha Clamp Source Line
File: training_campaign_config.yaml (Sprint 21A)
Problem: focal_loss_alpha_source cited trainer_v3.py (L46-47).
Fact: Alpha clamping is at L48: self.alpha = float(torch.clamp(torch.tensor(alpha), 0.25, 0.75))
Correction: Source reference corrected to trainer_v3.py (L48).

---

## 3. Source Reference Validation

| Reference                                 | Claimed | Actual | Status   |
|-------------------------------------------|---------|--------|----------|
| run_sprint14c_experiment.py AdamW stage1  | L295    | L295   | CORRECT  |
| run_sprint14c_experiment.py lr=5e-5       | L345    | L345   | CORRECT  |
| run_sprint14c_experiment.py weight_decay  | L295    | L295   | CORRECT  |
| run_sprint14c_experiment.py CosineAnneal  | present | ABSENT | CORRECTED|
| model_v3.py dropout=0.2                   | L166    | L166   | CORRECT  |
| trainer_v3.py FocalLoss gamma=2.0         | L45     | L45    | CORRECT  |
| trainer_v3.py alpha clamp                 | L46-47  | L48    | CORRECTED|
| trainer_v3.py CosineAnnealingLR           | L177    | L177   | CORRECT  |

---

## 4. Experiment ID Uniqueness Audit (8 total)

| # | Experiment ID                         | Seed | Type | Unique |
|---|---------------------------------------|------|------|--------|
| 1 | V3_S42_E10_LR5e5_WD1e4               | 42   | D    | YES    |
| 2 | V3_S123_E10_LR5e5_WD1e4              | 123  | D    | YES    |
| 3 | V3_S3407_E10_LR5e5_WD1e4             | 3407 | D    | YES    |
| 4 | V3_S2026_E10_LR5e5_WD1e4             | 2026 | D    | YES    |
| 5 | V3_S9999_E10_LR5e5_WD1e4             | 9999 | D    | YES    |
| 6 | V3_S42_E10_LR5e5_WD1e4_GOES          | 42   | A    | YES    |
| 7 | V3_S42_E10_LR5e5_WD1e4_GOES_SOLEXS   | 42   | B    | YES    |
| 8 | V3_S42_E10_LR5e5_WD1e4_GOES_HEL1OS   | 42   | C    | YES    |

No duplicate IDs found.

---

## 5. Manifest-Command Parity

| Experiment ID                        | In Manifest | In .sh | Executable | Notes               |
|--------------------------------------|-------------|--------|------------|---------------------|
| V3_S42_E10_LR5e5_WD1e4              | YES         | YES    | YES        |                     |
| V3_S123_E10_LR5e5_WD1e4             | YES         | YES    | YES        |                     |
| V3_S3407_E10_LR5e5_WD1e4            | YES         | YES    | YES        |                     |
| V3_S2026_E10_LR5e5_WD1e4            | YES         | YES    | YES        |                     |
| V3_S9999_E10_LR5e5_WD1e4            | YES         | YES    | YES        |                     |
| V3_S42_E10_LR5e5_WD1e4_GOES         | YES         | YES    | YES        | Uses --skip-stage1  |
| V3_S42_E10_LR5e5_WD1e4_GOES_SOLEXS  | YES         | YES    | YES        | Uses --skip-stage1  |
| V3_S42_E10_LR5e5_WD1e4_GOES_HEL1OS  | YES         | YES    | YES        | Uses --skip-stage1  |

All 8 experiments have an executable command. Parity: PASS.

---

## 6. Checkpoint Clarification

| Checkpoint Path                                                    | Status  |
|--------------------------------------------------------------------|---------|
| artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt       | EXISTS  |
| artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt       | EXISTS  |
| artifacts/sprint21b/checkpoints/V3_S42_E10_LR5e5_WD1e4_best.pt    | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S123_E10_LR5e5_WD1e4_best.pt   | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S3407_E10_LR5e5_WD1e4_best.pt  | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S2026_E10_LR5e5_WD1e4_best.pt  | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S9999_E10_LR5e5_WD1e4_best.pt  | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S42_E10_..._GOES_best.pt        | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S42_E10_..._GOES_SOLEXS_best.pt | PLANNED |
| artifacts/sprint21b/checkpoints/V3_S42_E10_..._GOES_HEL1OS_best.pt | PLANNED |

PLANNED checkpoints will only exist after the campaign executes.

---

## 7. Campaign Document Consistency

| Document                                | Same Protocol | Notes                              |
|-----------------------------------------|---------------|------------------------------------|
| corrected_campaign_matrix.csv            | YES           | 5 seeds, model-type D              |
| corrected_training_manifest.csv          | YES           | 8 runs (5 campaign + 3 ablation)   |
| corrected_campaign_commands.sh           | YES           | 8 executable commands              |
| corrected_experiment_naming.md           | YES           | 8 canonical IDs                    |
| corrected_checkpoint_standard.md         | YES           | Proposed standard documented       |
| evaluation_protocol.md (Sprint 21A)      | YES           | Unchanged, consistent              |
| corrected_training_campaign_config.yaml  | YES           | Historical/proposed separated      |

All documents describe the identical 8-experiment campaign.

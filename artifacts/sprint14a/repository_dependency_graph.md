# Repository Dependency Graph — Sprint 14A Forensic Audit

Generated: 2026-06-19T10:06:44Z

---

## Complete Pipeline Dependency Graph

```
artifacts/research_v3/
├── train_v3.parquet       SHA256=08ff98f399f81f93...  rows=5,161,312
│   (2010-01-02 → 2023-12-12  GOES-only historical)
│   │
│   └─► [Stage 1 Source]
│        5 × 10,000-row chronological blocks
│        Saved to: artifacts/sprint13/tmp/s1_train_block_{0..4}.parquet
│        │
│        └─► SolarFlareMultiWindowDataset (dataset_v3.py)
│             seq_len=360, sliding windows
│             ConcatDataset → WeightedRandomSampler
│             │
│             └─► DataLoader (s1_train_loader)
│                  │
│                  └─► LateFusionPatchTST.forward(x_goes, x_s=missing_token, x_h=missing_token)
│                       SoLEXS encoder: FROZEN  HEL1OS encoder: FROZEN
│                       Gradients → GOES encoder + fusion_attn + head
│                       Loss: FocalLoss(alpha=pos_rate)
│                       Optimizer: AdamW(lr=1e-4)
│                       Saved: stage1_best_tss.pt / stage1_best_loss.pt
│
├── validation_v3.parquet  SHA256=7c519088c85d1d7c...  rows=1,568,759
│   (independent GOES historical val split)
│   │
│   └─► [Stage 1 Validation Source]
│        5 × 2,000-row blocks
│        Saved to: artifacts/sprint13/tmp/s1_val_block_{0..4}.parquet
│        │
│        └─► SolarFlareMultiWindowDataset → DataLoader (s1_val_loader)
│             evaluate_model() → compute_metrics() + compute_prob_metrics()
│
└── test_v3.parquet        SHA256=2aaf8d57c52e67c0...  rows=1,806,673
    (Multi-instrument overlap 2023-12-13 → 2026-06-14)
    │
    ├─► [Stage 2 Train Source]  time-filter: 2023-12-13 → 2025-06-14
    │    5 × 10,000-row blocks  (mask_solexs>500 AND mask_hel1os>500)
    │    Saved to: artifacts/sprint13/tmp/s2_train_block_{0..4}.parquet
    │    │
    │    └─► SolarFlareMultiWindowDataset → ConcatDataset → WeightedRandomSampler
    │         │
    │         └─► DataLoader (s2_train_loader)
    │              │
    │              └─► LateFusionPatchTST.forward(x_goes, x_solexs, x_hel1os, m_s, m_h)
    │                   All encoders: ACTIVE (unfrozen after Stage 1)
    │                   model loaded from stage1_best_tss.pt
    │                   Gradients → ALL encoders + projection layers + fusion + head
    │                   Optimizer: AdamW(lr=5e-5)
    │                   Saved: stage2_best_tss.pt / stage2_best_loss.pt / stage2_best_prauc.pt
    │
    ├─► [Stage 2 Validation Source]  time-filter: 2025-06-15 → 2025-12-14
    │    5 × 2,000-row blocks
    │    Saved to: artifacts/sprint13/tmp/s2_val_block_{0..4}.parquet
    │    │
    │    └─► DataLoader (s2_val_loader)
    │         evaluate_model() → compute_metrics()
    │         Checkpoint selected: highest val TSS on this split
    │
    ├─► [Calibration Source]  SAME as Stage 2 Validation
    │    EvaluatorV3.fit_calibrators(val_logits, val_targets)
    │    Isotonic Regression + Temperature Scaling fitted on val probs only
    │    ⚠ Test set is NOT touched during calibration fitting
    │
    └─► [Stage 2 Test Source]  time-filter: 2025-12-15 → 2026-06-14
         5 × 2,000-row blocks  (UNTOUCHED FUTURE PERIOD)
         Saved to: artifacts/sprint13/tmp/s2_test_block_{0..4}.parquet
         │
         └─► DataLoader (s2_test_loader)
              evaluate_model() → calibrated probs
              compute_comprehensive_metrics()
              Threshold sweep on calibrated isotonic probs
              │
              └─► artifacts/sprint13/
                   ├── final_evaluation_metrics.json
                   ├── final_evaluation_certificate.json
                   ├── calibration_curve.png
                   ├── confusion_matrix.png
                   ├── threshold_sweep.png
                   └── fusion_attention.png
```

---

## Module Dependency Chain

```
artifacts/feature_columns_v3.json   (column manifest, SHA256=c5142e4a0d492f44...)
        │
        ▼
app/services/ml/dataset_v3.py       SolarFlareMultiWindowDataset
        │  - reads feature_columns_v3.json at init
        │  - loads parquet file passed as parquet_path argument
        │  - returns (x_goes, x_solexs, x_hel1os, mask_solexs, mask_hel1os), label
        │
        ▼
torch.utils.data.DataLoader         (via make_train_loader_v3_concat / DataLoader)
        │
        ▼
app/services/ml/model_v3.py         LateFusionPatchTST
        │  - GOES encoder: embed_dim=128, 4 layers, 8 heads
        │  - SoLEXS encoder: embed_dim=160, 5 layers, 8 heads
        │  - HEL1OS encoder: embed_dim=160, 5 layers, 8 heads
        │  - Late Fusion: cross-attention on 3 embeddings
        │  - Classifier head: Linear(128 → 1)
        │
        ▼
app/services/ml/trainer_v3.py       TrainerV3 / set_encoder_frozen / FocalLoss
        │  - Stage 1: freeze solexs + hel1os
        │  - Stage 2: unfreeze all
        │  - GradScaler + AdamW + CosineAnnealingLR
        │
        ▼
app/services/ml/evaluator_v3.py     EvaluatorV3
        │  - TemperatureScaler.fit(val_logits, val_targets)
        │  - IsotonicRegression.fit(val_probs, val_targets)
        │  - evaluate() returns full metric dict incl. reliability_diagram
        │
        ▼
app/services/ml/metrics.py          compute_metrics / compute_prob_metrics
        │
        ▼
artifacts/sprint13/                 Reports, plots, certificates
```

---

## Key Forensic Findings

| Finding | Evidence | Verdict |
| :--- | :--- | :---: |
| Stage 1 source is `train_v3.parquet` (historical, 2010-2023) | Line 352 of `pilot_train_v3.py` | ✅ CORRECT |
| Stage 2 source is `test_v3.parquet` time-filtered to overlap | Lines 358-360 of `pilot_train_v3.py` | ✅ CORRECT |
| Stage 1 val uses `validation_v3.parquet` (independent from Stage 2) | Line 353 of `pilot_train_v3.py` | ✅ CORRECT |
| No legacy `artifacts/research/` (non-v3) paths referenced | Full repo scan | ✅ CLEAN |
| Calibration uses Stage 2 val set only | Lines 657-659 of `pilot_train_v3.py` | ✅ CLEAN |
| Test set untouched during calibration fitting | Code trace | ✅ CLEAN |
| SoLEXS encoder frozen during Stage 1 | `set_encoder_frozen("solexs", True)` line 432 | ✅ CORRECT |
| HEL1OS encoder frozen during Stage 1 | `set_encoder_frozen("hel1os", True)` line 433 | ✅ CORRECT |
| All encoders unfrozen in Stage 2 | Lines 543-545 of `pilot_train_v3.py` | ✅ CORRECT |


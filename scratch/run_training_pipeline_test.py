import sys
import os
import torch
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset, make_train_loader_v3
from app.services.ml.trainer_v3 import TrainerV3, set_encoder_frozen
from app.services.ml.evaluator_v3 import EvaluatorV3

def run_dry_run_pipeline():
    print("==================================================")
    print("Version 3 Training Pipeline Verification Dry-Run")
    print("==================================================")

    # 1. Load Dataset splits and check sizes
    print("Checking dataset splits...")
    train_path = "artifacts/research_v3/train_v3.parquet"
    val_path = "artifacts/research_v3/validation_v3.parquet"
    test_path = "artifacts/research_v3/test_v3.parquet"
    
    assert os.path.exists(train_path), "Train split v3 missing!"
    assert os.path.exists(val_path), "Validation split v3 missing!"
    assert os.path.exists(test_path), "Test split v3 missing!"
    print("✓ Dataset splits are present.")

    # 2. Instantiate datasets (with a small sequence slice for speed)
    # We will only load the validation set since it's smaller, or a subset of it
    val_dataset = SolarFlareMultiWindowDataset(val_path, seq_len=360, split_name="validation_v3")
    
    # Check shape of a single sample
    inputs, target = val_dataset[0]
    x_g, x_s, x_h, m_s, m_h = inputs
    
    print(f"Sample shapes:")
    print(f"  GOES input:    {list(x_g.shape)}")
    print(f"  SoLEXS input:  {list(x_s.shape)}")
    print(f"  HEL1OS input:  {list(x_h.shape)}")
    print(f"  Mask SoLEXS:   {list(m_s.shape)} (value={m_s.item()})")
    print(f"  Mask HEL1OS:   {list(m_h.shape)} (value={m_h.item()})")
    print(f"  Target:        {list(target.shape)} (value={target.item()})")
    
    assert x_g.shape == (360, 14), f"Unexpected GOES shape: {x_g.shape}"
    assert x_s.shape == (360, 18), f"Unexpected SoLEXS shape: {x_s.shape}"
    assert x_h.shape == (360, 4), f"Unexpected HEL1OS shape: {x_h.shape}"
    assert m_s.shape == (1,), f"Unexpected SoLEXS mask shape: {m_s.shape}"
    assert m_h.shape == (1,), f"Unexpected HEL1OS mask shape: {m_h.shape}"
    print("✓ Dataset window shapes verified.")

    # Create dummy tiny dataloaders for the dry run (to avoid running full 5M dataset steps)
    # Wrap a slice of dataset
    tiny_dataset = torch.utils.data.Subset(val_dataset, list(range(0, 16)))
    train_loader = torch.utils.data.DataLoader(tiny_dataset, batch_size=8, shuffle=True)
    val_loader = torch.utils.data.DataLoader(tiny_dataset, batch_size=8, shuffle=False)

    # 3. Instantiate model with specific feature counts from v3 columns
    # We pass n_features_solexs=18 and n_features_hel1os=4 since those are the active features on disk!
    print("\nInitializing LateFusionPatchTST...")
    model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    )

    # 4. Verify Selective Freezing
    print("\nVerifying Selective Freezing...")
    set_encoder_frozen(model, "goes", freeze=True)
    
    # Check that GOES parameters do not require grad
    for n, p in model.named_parameters():
        if "encoder_goes" in n:
            assert not p.requires_grad, f"Parameter {n} was not frozen!"
    print("✓ Encoder GOES frozen successfully.")

    set_encoder_frozen(model, "goes", freeze=False)
    for n, p in model.named_parameters():
        if "encoder_goes" in n:
            assert p.requires_grad, f"Parameter {n} was not unfrozen!"
    print("✓ Encoder GOES unfrozen successfully.")

    # 5. Dry-run Trainer
    print("\nInitializing TrainerV3 and running dry-run epochs...")
    trainer = TrainerV3(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        pos_rate=0.04,
        max_epochs=2,
        patience=1,
        lr=1e-4,
        device="cpu" # CPU dry run
    )
    
    # Pretraining step (Stage 1)
    train_loss, _ = trainer.train_epoch(1)
    val_loss, best_tss, val_th = trainer.validate()
    print(f"Dry-run Epoch 1 finished: Train Loss={train_loss:.5f} | Val Loss={val_loss:.5f} | Val TSS={best_tss:.4f}")
    
    # 6. Fit calibrator and evaluate
    print("\nInitializing EvaluatorV3 and running dry-run calibration...")
    evaluator = EvaluatorV3()
    
    # Generate mock validation logits/targets
    mock_logits = np.random.randn(100, 1)
    mock_targets = np.random.randint(0, 2, size=(100,))
    
    evaluator.fit_calibrators(mock_logits, mock_targets)
    metrics_raw = evaluator.evaluate(mock_logits, mock_targets)
    
    cal_probs = evaluator.calibrate_probabilities(mock_logits, method="isotonic")
    metrics_cal = evaluator.evaluate(np.log(cal_probs / (1.0 - cal_probs + 1e-9)), mock_targets)
    
    print(f"Raw metrics: TSS={metrics_raw['tss']:.4f} | ECE={metrics_raw['ece']:.4f} | Brier={metrics_raw['brier_score']:.4f}")
    print(f"Calibrated metrics: TSS={metrics_cal['tss']:.4f} | ECE={metrics_cal['ece']:.4f} | Brier={metrics_cal['brier_score']:.4f}")
    
    assert 0.0 <= metrics_cal["ece"] <= 1.0, f"Invalid ECE value: {metrics_cal['ece']}"
    print("✓ Probability calibration fit and ECE computation PASSED.")

    # Save verification report
    import json
    report = {
        "verification_status": "PASSED",
        "dataset_alignment": "OK",
        "trainer_dry_run": "OK",
        "selective_freezing": "OK",
        "calibration_pipeline": "OK",
        "ece_calculation": "OK",
        "parameter_budget": int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    }
    
    report_path = "artifacts/sprint12b/verification_report.json"
    os.makedirs("artifacts/sprint12b", exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Verification report saved to {report_path}")
    print("==================================================")
    print("Training Pipeline Verification Dry-Run Complete!")
    print("==================================================")

if __name__ == "__main__":
    run_dry_run_pipeline()

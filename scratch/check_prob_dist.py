import os
import sys
import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.evaluator_v3 import EvaluatorV3

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = LateFusionPatchTST(14, 18, 4).to(device)
model.load_state_dict(torch.load("artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt", map_location=device))
model.eval()

val_ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_val.parquet", seq_len=360, split_name="s2_val")
test_ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_test.parquet", seq_len=360, split_name="s2_test")

val_loader = DataLoader(val_ds, batch_size=128, shuffle=False, num_workers=0)
test_loader = DataLoader(test_ds, batch_size=128, shuffle=False, num_workers=0)

# Evaluate validation set to fit calibrator
print("Evaluating validation set...")
val_probs = []
val_targets = []
with torch.no_grad():
    for inputs, targets in val_loader:
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
            logits = model(x_g, x_s, x_h, m_s, m_h)
        probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
        val_probs.append(probs)
        val_targets.append(targets.numpy())

val_probs = np.concatenate(val_probs)
val_targets = np.concatenate(val_targets)
val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))

evaluator = EvaluatorV3()
evaluator.fit_calibrators(val_logits, val_targets)

# Evaluate test set
print("Evaluating test set...")
test_probs = []
with torch.no_grad():
    for inputs, targets in test_loader:
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
            logits = model(x_g, x_s, x_h, m_s, m_h)
        probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
        test_probs.append(probs)

test_probs = np.concatenate(test_probs)
test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")

# Print counts above various thresholds
for th in [0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.46]:
    count = np.sum(cal_probs >= th)
    print(f"Calibrated prob >= {th:.2f}: {count} / {len(cal_probs)} ({100*count/len(cal_probs):.2f}%)")

import time
import torch
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.model_v3 import LateFusionPatchTST
from torch.utils.data import DataLoader

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_test.parquet", seq_len=360, split_name="s2_test", use_mmap=False)
loader = DataLoader(ds, batch_size=128, shuffle=False, num_workers=0)
model = LateFusionPatchTST(14, 18, 4).to(device)
model.eval()

# Method 1: Immediate CPU transfer
start = time.time()
with torch.no_grad():
    iterator = iter(loader)
    all_probs_1 = []
    for _ in range(50):
        inputs, targets = next(iterator)
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
            logits = model(x_g, x_s, x_h, m_s, m_h)
        probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
        all_probs_1.append(probs)
print(f"Method 1 (Immediate CPU transfer) took: {time.time() - start:.4f}s")

# Method 2: Accumulate on GPU
start = time.time()
with torch.no_grad():
    iterator = iter(loader)
    all_probs_2 = []
    for _ in range(50):
        inputs, targets = next(iterator)
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
            logits = model(x_g, x_s, x_h, m_s, m_h)
        probs = torch.sigmoid(logits).squeeze(-1) # keep on GPU
        all_probs_2.append(probs)
    all_probs_2 = torch.cat(all_probs_2, dim=0).float().cpu().numpy()
print(f"Method 2 (Accumulate on GPU) took: {time.time() - start:.4f}s")

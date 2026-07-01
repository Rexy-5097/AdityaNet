import time
import torch
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ml.model_v3 import LateFusionPatchTST

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

model = LateFusionPatchTST(14, 18, 4).to(device)
model.train() # MC Dropout mode

batch_size = 128
n_samples = 50

# Generate dummy batch
x_g = torch.randn(batch_size, 360, 14, device=device)
x_s = torch.randn(batch_size, 360, 18, device=device)
x_h = torch.randn(batch_size, 360, 4, device=device)
m_s = torch.ones(batch_size, 1, device=device)
m_h = torch.ones(batch_size, 1, device=device)

# Method 3: Unstacked passes with GPU aggregation
start = time.time()
with torch.no_grad():
    probs_seq = []
    for _ in range(n_samples):
        with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
            logits = model(x_g, x_s, x_h, m_s, m_h)
        probs_seq.append(torch.sigmoid(logits).squeeze(-1))
    probs_seq = torch.stack(probs_seq, dim=0) # [50, 128] on GPU
    mean_seq = probs_seq.mean(dim=0).float().cpu().numpy()
    std_seq = probs_seq.std(dim=0).float().cpu().numpy()
print(f"Method 3 (Unstacked GPU aggregation) took: {time.time() - start:.4f}s")

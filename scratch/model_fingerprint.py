import torch
import os
import sys
import json
import hashlib

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"
sys.path.insert(0, REPO_ROOT)

from app.services.ml.model import PatchTST

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

model_path = os.path.join(REPO_ROOT, "artifacts/models/patchtst_best.pt")
checkpoint = torch.load(model_path, map_location="cpu")

model = PatchTST()
model.load_state_dict(checkpoint["model"])
model.eval()

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"Total Parameters: {total_params:,}")
print(f"Trainable Parameters: {trainable_params:,}")

# Check training epochs in checkpoint or training history
training_history_path = os.path.join(REPO_ROOT, "artifacts/training_history.json")
training_history = []
if os.path.exists(training_history_path):
    with open(training_history_path) as f:
        training_history = json.load(f)

epochs = len(training_history)
print(f"Training Epochs from History: {epochs}")

checkpoint_keys = list(checkpoint.keys())
print(f"Checkpoint keys: {checkpoint_keys}")

if "epoch" in checkpoint:
    print(f"Checkpoint Epoch: {checkpoint['epoch']}")
if "best_val_tss" in checkpoint:
    print(f"Checkpoint Best Val TSS: {checkpoint['best_val_tss']}")

info = {
    "architecture": "PatchTST (CLS-token variant, multivariate-patch)",
    "number_of_parameters": total_params,
    "trainable_parameters": trainable_params,
    "checkpoint_hash": sha256(model_path),
    "checkpoint_size_bytes": os.path.getsize(model_path),
    "training_epochs": epochs,
    "optimizer": "AdamW (lr=1e-3, weight_decay=1e-4, clip_norm=1.0)",
    "scheduler": "CosineAnnealingLR (T_max=3)",
    "loss_function": "Focal Loss (gamma=2.0, alpha=0.25)",
    "dropout": 0.2,
    "window_length_minutes": 360,
    "feature_count": 14,
    "input_tensor_shape": "[batch, seq_len=360, n_features=14]",
    "output_definition": "Single raw logit [batch, 1] representing M/X flare risk within 6 hours"
}

with open(os.path.join(REPO_ROOT, "scratch/model_info.json"), "w") as f:
    json.dump(info, f, indent=2)
print("Saved model info to scratch/model_info.json")

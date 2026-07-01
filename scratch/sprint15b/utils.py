"""
scratch/sprint15b/utils.py

Shared utilities for Sprint 15B diagnostics.
Provides dataset, model, and calibration loading functions.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import compute_full_suite, find_best_threshold

logger = logging.getLogger(__name__)

# Canonical paths
MODEL_PATH = "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt"
VAL_PARQUET = "artifacts/sprint14c/s2_val.parquet"
TEST_PARQUET = "artifacts/sprint14c/s2_test.parquet"
THRESHOLDS_PATH = "artifacts/operator_thresholds.json"

def get_device():
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")

def load_model(device):
    model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    ).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
    return model

def load_datasets(use_mmap=False):
    val_ds = SolarFlareMultiWindowDataset(VAL_PARQUET, seq_len=360, split_name="s2_val", use_mmap=use_mmap)
    test_ds = SolarFlareMultiWindowDataset(TEST_PARQUET, seq_len=360, split_name="s2_test", use_mmap=use_mmap)
    return val_ds, test_ds

def get_loaders(val_ds, test_ds, batch_size=128):
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=False)
    return val_loader, test_loader

def evaluate_simple(model, loader, device):
    model.eval()
    all_probs = []
    all_targets = []
    all_mask_s = []
    all_mask_h = []
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                logits = model(x_g, x_s, x_h, m_s, m_h)
            probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
            all_probs.append(probs)
            all_targets.append(targets.numpy())
            all_mask_s.append(m_s.cpu().numpy().squeeze(-1))
            all_mask_h.append(m_h.cpu().numpy().squeeze(-1))
    return (
        np.concatenate(all_probs),
        np.concatenate(all_targets),
        np.concatenate(all_mask_s),
        np.concatenate(all_mask_h)
    )

def get_calibrators_and_threshold(model, val_loader, device):
    val_probs, val_targets, _, _ = evaluate_simple(model, val_loader, device)
    val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))
    evaluator = EvaluatorV3()
    evaluator.fit_calibrators(val_logits, val_targets)
    
    # Find best threshold on validation raw probabilities (as done in sprint15a)
    best_th, _ = find_best_threshold(val_targets, val_probs, metric="tss")
    return evaluator, best_th

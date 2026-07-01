"""
scratch/sprint16a/utils.py

Shared utilities for Sprint 16A diagnostics.
"""

import os
import sys
import logging
import numpy as np
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

"""
scratch/sprint16a/cache_predictions.py

Generates and caches model predictions, logits, calibrated probabilities,
attention rollouts, and uncertainty under multiple configurations.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import find_best_threshold

def evaluate_configuration(model, loader, device, mask_override=None):
    """
    Evaluates the model under a specific sensor mask override.
    mask_override: None (baseline), 'goes_only', 'goes_solexs', or 'goes_hel1os'
    """
    model.eval()
    all_probs = []
    all_targets = []
    all_masks_s = []
    all_masks_h = []
    
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            
            # Apply overrides
            if mask_override == "goes_only":
                m_s = torch.zeros_like(m_s)
                m_h = torch.zeros_like(m_h)
                x_s = torch.zeros_like(x_s)
                x_h = torch.zeros_like(x_h)
            elif mask_override == "goes_solexs":
                m_h = torch.zeros_like(m_h)
                x_h = torch.zeros_like(x_h)
            elif mask_override == "goes_hel1os":
                m_s = torch.zeros_like(m_s)
                x_s = torch.zeros_like(x_s)
                
            with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                logits = model(x_g, x_s, x_h, m_s, m_h)
                
            probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
            all_probs.append(probs)
            all_targets.append(targets.numpy())
            all_masks_s.append(m_s.cpu().numpy().squeeze(-1))
            all_masks_h.append(m_h.cpu().numpy().squeeze(-1))
            
    return (
        np.concatenate(all_probs),
        np.concatenate(all_targets),
        np.concatenate(all_masks_s),
        np.concatenate(all_masks_h)
    )

def compute_rollout(layers_attn):
    # layers_attn: list of numpy arrays, each of shape [num_heads, 45, 45]
    rollout = np.eye(45, dtype=np.float32)
    for attn in layers_attn:
        mean_attn = np.mean(attn, axis=0)
        A_tilde = 0.5 * mean_attn + 0.5 * np.eye(45, dtype=np.float32)
        row_sums = A_tilde.sum(axis=-1, keepdims=True)
        A_tilde = A_tilde / (row_sums + 1e-9)
        rollout = np.matmul(A_tilde, rollout)
    return rollout

def extract_rollouts_subset(model, dataset, indices, device):
    """
    Extracts attention rollout CLS distributions for GOES, SoLEXS, and HEL1OS in batches.
    """
    model.eval()
    subset_ds = Subset(dataset, indices)
    loader = DataLoader(subset_ds, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    
    all_r_goes = []
    all_r_solexs = []
    all_r_hel1os = []
    
    logger.info("Extracting attention rollouts for 20,000 subset (batched)...")
    with torch.no_grad():
        for inputs, _ in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            B = x_g.size(0)
            
            # 1. GOES branch
            g = model.patch_embed_goes(x_g)
            cls_g = model.cls_token_goes.expand(B, -1, -1)
            g = torch.cat([cls_g, g], dim=1)
            g = model.pos_enc_goes(g)
            goes_attn = []
            for layer in model.encoder_goes:
                g, attn = layer(g, return_attn=True)
                goes_attn.append(attn.cpu().numpy())  # [B, num_heads, 45, 45]
            
            rollout_g = np.tile(np.eye(45, dtype=np.float32), (B, 1, 1))
            for attn in goes_attn:
                mean_attn = np.mean(attn, axis=1)  # [B, 45, 45]
                A_tilde = 0.5 * mean_attn + 0.5 * np.eye(45, dtype=np.float32)
                row_sums = A_tilde.sum(axis=-1, keepdims=True)
                A_tilde = A_tilde / (row_sums + 1e-9)
                rollout_g = np.matmul(A_tilde, rollout_g)
            all_r_goes.append(rollout_g[:, 0, :])
            
            # 2. SoLEXS branch
            s = model.patch_embed_solexs(x_s)
            cls_s = model.cls_token_solexs.expand(B, -1, -1)
            s = torch.cat([cls_s, s], dim=1)
            s = model.pos_enc_solexs(s)
            solexs_attn = []
            for layer in model.encoder_solexs:
                s, attn = layer(s, return_attn=True)
                solexs_attn.append(attn.cpu().numpy())
            
            rollout_s = np.tile(np.eye(45, dtype=np.float32), (B, 1, 1))
            for attn in solexs_attn:
                mean_attn = np.mean(attn, axis=1)
                A_tilde = 0.5 * mean_attn + 0.5 * np.eye(45, dtype=np.float32)
                row_sums = A_tilde.sum(axis=-1, keepdims=True)
                A_tilde = A_tilde / (row_sums + 1e-9)
                rollout_s = np.matmul(A_tilde, rollout_s)
            mask_s_np = m_s.cpu().numpy()  # [B, 1]
            rollout_s = rollout_s * mask_s_np.reshape(-1, 1, 1)
            all_r_solexs.append(rollout_s[:, 0, :])
            
            # 3. HEL1OS branch
            h = model.patch_embed_hel1os(x_h)
            cls_h = model.cls_token_hel1os.expand(B, -1, -1)
            h = torch.cat([cls_h, h], dim=1)
            h = model.pos_enc_hel1os(h)
            hel1os_attn = []
            for layer in model.encoder_hel1os:
                h, attn = layer(h, return_attn=True)
                hel1os_attn.append(attn.cpu().numpy())
            
            rollout_h = np.tile(np.eye(45, dtype=np.float32), (B, 1, 1))
            for attn in hel1os_attn:
                mean_attn = np.mean(attn, axis=1)
                A_tilde = 0.5 * mean_attn + 0.5 * np.eye(45, dtype=np.float32)
                row_sums = A_tilde.sum(axis=-1, keepdims=True)
                A_tilde = A_tilde / (row_sums + 1e-9)
                rollout_h = np.matmul(A_tilde, rollout_h)
            mask_h_np = m_h.cpu().numpy()
            rollout_h = rollout_h * mask_h_np.reshape(-1, 1, 1)
            all_r_hel1os.append(rollout_h[:, 0, :])
            
    return (
        np.concatenate(all_r_goes, axis=0),
        np.concatenate(all_r_solexs, axis=0),
        np.concatenate(all_r_hel1os, axis=0)
    )

def compute_dropout_uncertainty_subset(model, dataset, indices, device, num_passes=50):
    """
    Computes MC Dropout standard deviation for the subset.
    """
    logger.info("Computing MC Dropout uncertainty for 20,000 subset...")
    model.train()  # Enable dropout
    
    subset_ds = Subset(dataset, indices)
    loader = DataLoader(subset_ds, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    
    all_std = []
    with torch.no_grad():
        for inputs, _ in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            batch_probs = []
            for _ in range(num_passes):
                with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                    logits = model(x_g, x_s, x_h, m_s, m_h)
                probs = torch.sigmoid(logits).squeeze(-1)
                batch_probs.append(probs)
                
            batch_probs = torch.stack(batch_probs, dim=0)  # [num_passes, B]
            std_p = batch_probs.std(dim=0).float().cpu().numpy()
            all_std.extend(std_p)
            
    model.eval()
    return np.array(all_std)

def main():
    device = get_device()
    logger.info(f"Using device: {device}")
    
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    
    val_loader, test_loader = get_loaders(val_ds, test_ds, batch_size=256)
    
    # 1. Fit Calibrator on Validation set
    logger.info("Evaluating validation set...")
    val_probs, val_targets, _, _ = evaluate_configuration(model, val_loader, device)
    val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))
    
    logger.info("Fitting calibrators on validation logits...")
    evaluator = EvaluatorV3()
    evaluator.fit_calibrators(val_logits, val_targets)
    
    best_th, _ = find_best_threshold(val_targets, val_probs, metric="tss")
    logger.info(f"Optimal raw threshold from validation: {best_th:.6f}")
    
    # Load test set timestamps
    logger.info("Loading test timestamps...")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet", columns=["timestamp"])
    timestamps = df_test["timestamp"].values[360:]
    
    # 2. Run test set configurations
    logger.info("Running Baseline test set inference...")
    test_probs, test_targets, mask_s, mask_h = evaluate_configuration(model, test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    
    # Calibrate Baseline
    test_probs_cal_iso = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    test_probs_cal_temp = evaluator.calibrate_probabilities(test_logits, method="temperature")
    test_preds_binary = (test_probs_cal_iso >= best_th).astype(int)
    
    # Mask override configurations
    logger.info("Running GOES-only test set inference...")
    probs_goes_only, _, _, _ = evaluate_configuration(model, test_loader, device, mask_override="goes_only")
    logits_goes_only = np.log(probs_goes_only / (1.0 - probs_goes_only + 1e-9))
    probs_cal_iso_goes_only = evaluator.calibrate_probabilities(logits_goes_only, method="isotonic")
    
    logger.info("Running GOES + SoLEXS test set inference...")
    probs_goes_solexs, _, _, _ = evaluate_configuration(model, test_loader, device, mask_override="goes_solexs")
    logits_goes_solexs = np.log(probs_goes_solexs / (1.0 - probs_goes_solexs + 1e-9))
    probs_cal_iso_goes_solexs = evaluator.calibrate_probabilities(logits_goes_solexs, method="isotonic")
    
    logger.info("Running GOES + HEL1OS test set inference...")
    probs_goes_hel1os, _, _, _ = evaluate_configuration(model, test_loader, device, mask_override="goes_hel1os")
    logits_goes_hel1os = np.log(probs_goes_hel1os / (1.0 - probs_goes_hel1os + 1e-9))
    probs_cal_iso_goes_hel1os = evaluator.calibrate_probabilities(logits_goes_hel1os, method="isotonic")
    
    # 3. Handle representative 20k subset for attention and uncertainty
    np.random.seed(42)
    subset_size = 20000
    subset_indices = np.random.choice(len(test_ds), subset_size, replace=False)
    
    rollouts_goes, rollouts_solexs, rollouts_hel1os = extract_rollouts_subset(model, test_ds, subset_indices, device)
    subset_uncertainty = compute_dropout_uncertainty_subset(model, test_ds, subset_indices, device)
    
    # 4. Save everything to cached_predictions.npz
    logger.info("Saving predictions cache to scratch/sprint16a/cached_predictions.npz...")
    os.makedirs("scratch/sprint16a", exist_ok=True)
    np.savez_compressed(
        "scratch/sprint16a/cached_predictions.npz",
        # Validation stats
        validation_threshold=best_th,
        # Full test set - Baseline
        test_logits=test_logits,
        test_probs_raw=test_probs,
        test_probs_cal_iso=test_probs_cal_iso,
        test_probs_cal_temp=test_probs_cal_temp,
        test_preds_binary=test_preds_binary,
        test_targets=test_targets,
        test_timestamps=timestamps,
        test_masks_solexs=mask_s,
        test_masks_hel1os=mask_h,
        # Full test set - Mask Overrides
        test_probs_raw_goes_only=probs_goes_only,
        test_probs_cal_iso_goes_only=probs_cal_iso_goes_only,
        test_probs_raw_goes_solexs=probs_goes_solexs,
        test_probs_cal_iso_goes_solexs=probs_cal_iso_goes_solexs,
        test_probs_raw_goes_hel1os=probs_goes_hel1os,
        test_probs_cal_iso_goes_hel1os=probs_cal_iso_goes_hel1os,
        # Subset details
        subset_indices=subset_indices,
        subset_uncertainty=subset_uncertainty,
        subset_rollouts_goes=rollouts_goes,
        subset_rollouts_solexs=rollouts_solexs,
        subset_rollouts_hel1os=rollouts_hel1os
    )
    logger.info("Predictions cache created successfully.")

if __name__ == "__main__":
    main()

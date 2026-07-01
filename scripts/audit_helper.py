"""
scripts/audit_helper.py

Sprint 8 — Information Gap Audit Shared Helper

Provides:
- Data and model loaders
- Memory-safe chunked MC Dropout inference (n_samples=10, batch_size=128)
- Memory-safe batched attention metrics extraction
- Optimized coincidence policy evaluation
- Standardization of outputs
"""

import os
import sys
import json
import logging
import pickle
import math
import gc
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST

logger = logging.getLogger(__name__)

# Paths
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH = os.path.join("artifacts", "calibrator.pkl")
THRESHOLDS_PATH = os.path.join("artifacts", "operator_thresholds_validation_only.json")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_DIR = os.path.join("artifacts", "information_gap")


def compute_confusion(y_true, y_pred):
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    return tp, fp, fn, tn


def compute_metrics_from_cm(tp, fp, fn, tn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pod       = recall
    pofd      = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss       = pod - pofd
    far       = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    return {
        "precision": round(precision, 8),
        "recall":    round(recall,    8),
        "f1":        round(f1,        8),
        "tss":       round(tss,       8),
        "far":       round(far,       8),
    }


def determine_raw_alert(prob, yellow_t, red_t):
    if prob < yellow_t:
        return "GREEN"
    elif prob < red_t:
        return "YELLOW"
    return "RED"


def apply_tiered_uncertainty_suppression(alert, unc, tier_r2y, tier_y2g, tier_a2g):
    if unc > tier_a2g:
        return "GREEN"
    if unc > tier_y2g and alert in ("YELLOW", "RED"):
        return "GREEN"
    if unc > tier_r2y and alert == "RED":
        return "YELLOW"
    return alert


def check_red_confirmation(j, cal_probs, red_threshold):
    if j < 2:
        return False
    last3 = cal_probs[j - 2 : j + 1]
    mean_p = float(np.mean(last3))
    from scipy.stats import linregress
    slope, _, _, _, _ = linregress(np.arange(3, dtype=float), last3)
    return (mean_p > red_threshold) and (slope > 0.0)


@torch.no_grad()
def compute_batched_attention_metrics(model, X_all, device, batch_size=256):
    model.eval()
    all_entropies = []
    all_top_shares = []
    
    for start in range(0, len(X_all), batch_size):
        end = min(len(X_all), start + batch_size)
        X_b = torch.from_numpy(X_all[start:end]).to(device)
        
        _, attn_maps = model.forward_with_attention(X_b)
        
        layer_vectors = []
        for layer_attn in attn_maps:
            head_avg = layer_attn.mean(dim=1)  # [B, 45, 45]
            cls_row = head_avg[:, 0, :]        # [B, 45]
            patch_attn = cls_row[:, 1:]        # [B, 44]
            layer_vectors.append(patch_attn)
            
        stacked = torch.stack(layer_vectors, dim=0)  # [4, B, 44]
        mean_attn = stacked.mean(dim=0)              # [B, 44]
        
        row_sums = mean_attn.sum(dim=-1, keepdim=True)
        mean_attn_norm = mean_attn / torch.clamp(row_sums, min=1e-9)  # [B, 44]
        
        p = torch.clamp(mean_attn_norm, min=1e-12, max=1.0)
        entropy = -torch.sum(p * torch.log(p), dim=-1)  # [B]
        norm_entropy = entropy / math.log(44)           # [B]
        top_patch_share = torch.max(mean_attn_norm, dim=-1).values  # [B]
        
        all_entropies.append(norm_entropy.cpu().numpy())
        all_top_shares.append(top_patch_share.cpu().numpy())
        
        if device.type == "mps":
            torch.mps.empty_cache()
        
    return np.concatenate(all_entropies), np.concatenate(all_top_shares)


def load_config_and_model():
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    with open(THRESHOLDS_PATH, "r") as fh:
        td = json.load(fh)

    yellow_threshold = float(td["yellow_threshold"])
    red_threshold    = float(td["red_threshold"])
    tier_r2y = float(td.get("uncertainty_suppress_red_to_yellow",   0.10))
    tier_y2g = float(td.get("uncertainty_suppress_yellow_to_green", 0.15))
    tier_a2g = float(td.get("uncertainty_suppress_all_to_green",    0.20))

    with open(CALIBRATOR_PATH, "rb") as fh:
        calibrator = pickle.load(fh)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    # Load test data
    load_cols = list(dict.fromkeys(
        ["timestamp", "short_flux", "long_flux", "target_6hr_binary", "target_6hr_class"] + feature_cols
    ))
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])

    return {
        "model": model,
        "feature_cols": feature_cols,
        "yellow_threshold": yellow_threshold,
        "red_threshold": red_threshold,
        "tier_r2y": tier_r2y,
        "tier_y2g": tier_y2g,
        "tier_a2g": tier_a2g,
        "calibrator": calibrator,
        "device": device,
        "test_df": test_df
    }


def run_experiment(test_df_mod, name, output_filename):
    logger.info(f"Running experiment: {name}...")
    cfg = load_config_and_model()
    
    model = cfg["model"]
    feature_cols = cfg["feature_cols"]
    yellow_threshold = cfg["yellow_threshold"]
    red_threshold = cfg["red_threshold"]
    tier_r2y = cfg["tier_r2y"]
    tier_y2g = cfg["tier_y2g"]
    tier_a2g = cfg["tier_a2g"]
    calibrator = cfg["calibrator"]
    device = cfg["device"]
    
    total_len = len(test_df_mod)
    stride = 60
    indices = np.arange(362, total_len, stride)
    y_true = test_df_mod["target_6hr_binary"].values[indices - 1]

    # Pre-extract values to numpy arrays for optimized coincidence check
    short_flux_arr = test_df_mod["short_flux"].values
    timestamp_arr = test_df_mod["timestamp"].values

    # Run chunked inference
    chunk_size = 1000
    batch_size = 128
    n_samples = 10
    
    mean_probs = np.zeros(len(indices), dtype=np.float32)
    std_probs = np.zeros(len(indices), dtype=np.float32)
    
    features_array = test_df_mod[feature_cols].values.astype(np.float32)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)
    
    for c_start in range(0, len(indices), chunk_size):
        c_end = min(len(indices), c_start + chunk_size)
        chunk_indices = indices[c_start:c_end]
        
        # Slicing chunk
        X_chunk = np.stack([features_array[i - 360 : i] for i in chunk_indices])
        
        mean_list = []
        std_list = []
        for start in range(0, len(X_chunk), batch_size):
            end = min(len(X_chunk), start + batch_size)
            curr_batch = end - start
            X_b = torch.from_numpy(X_chunk[start:end]).to(device)
            
            # Tile 10 times for memory safety and speed
            X_b_tiled = X_b.repeat(n_samples, 1, 1)
            
            model.train()  # activate dropout
            with torch.no_grad():
                logit_tiled = model(X_b_tiled)
                prob_tiled = torch.sigmoid(logit_tiled).squeeze(-1)
                
            prob_tiled = prob_tiled.view(n_samples, curr_batch)
            mean_prob = prob_tiled.mean(dim=0).cpu().numpy()
            std_prob = prob_tiled.std(dim=0).cpu().numpy()
            
            mean_list.append(mean_prob)
            std_list.append(std_prob)
            
            if device.type == "mps":
                torch.mps.empty_cache()
                
        mean_probs[c_start:c_end] = np.concatenate(mean_list)
        std_probs[c_start:c_end] = np.concatenate(std_list)
        
        del X_chunk
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()

    model.eval()
    
    # Calibrate
    cal_probs = calibrator(mean_probs)
    
    # Apply coincidence alert logic
    raw_alerts = []
    for i in range(len(cal_probs)):
        ra   = determine_raw_alert(cal_probs[i], yellow_threshold, red_threshold)
        supp = apply_tiered_uncertainty_suppression(ra, std_probs[i], tier_r2y, tier_y2g, tier_a2g)
        raw_alerts.append(supp)

    coincidence_alerts = []
    for j, a in enumerate(raw_alerts):
        if a == "RED":
            confirmed = check_red_confirmation(j, cal_probs, red_threshold)
            if not confirmed:
                a = "YELLOW"
            else:
                global_idx = indices[j]
                
                # Fast numpy slice
                short_flux_window = short_flux_arr[global_idx - 360 : global_idx]
                
                has_nans = np.any(np.isnan(short_flux_window))
                if has_nans:
                    s = pd.Series(short_flux_window).ffill().bfill()
                    short_flux_filled = s.values
                else:
                    short_flux_filled = short_flux_window
                
                t_curr = timestamp_arr[global_idx - 1]
                t_5m = timestamp_arr[global_idx - 6]
                t_10m = timestamp_arr[global_idx - 11]
                
                dt = float((t_curr - t_5m) / np.timedelta64(1, 'm'))
                dt_prev = float((t_5m - t_10m) / np.timedelta64(1, 'm'))
                
                if dt <= 0.0 or dt_prev <= 0.0:
                    dt = 5.0
                    dt_prev = 5.0
                    
                val_t = float(short_flux_filled[-1])
                val_t5 = float(short_flux_filled[-6])
                val_t10 = float(short_flux_filled[-11])
                
                grad = (val_t - val_t5) / dt
                grad_prev = (val_t5 - val_t10) / dt_prev
                acc = (grad - grad_prev) / ((dt + dt_prev) / 2.0)
                
                rules_passed = 0
                if grad > 0.0:
                    rules_passed += 1
                if acc > 0.0:
                    rules_passed += 1
                    
                if rules_passed < 2:
                    a = "YELLOW"
        coincidence_alerts.append(a)

    # Evaluate metrics
    y_pred = pd.Series(coincidence_alerts).isin(["YELLOW", "RED"]).astype(int).values
    tp, fp, fn, tn = compute_confusion(y_true, y_pred)
    metrics = compute_metrics_from_cm(tp, fp, fn, tn)
    
    roc_auc = float(roc_auc_score(y_true, cal_probs))
    pr_auc = float(average_precision_score(y_true, cal_probs))
    
    # Slice and compute attention in chunks
    X_all = np.stack([features_array[i - 360 : i] for i in indices])
    mean_attention_entropy, mean_top_patch_share = run_attention_inference(model, X_all, device)
    
    result = {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Precision": metrics["precision"],
        "Recall": metrics["recall"],
        "F1": metrics["f1"],
        "TSS": metrics["tss"],
        "FAR": metrics["far"],
        "ROC-AUC": roc_auc,
        "PR-AUC": pr_auc,
        "mean_attention_entropy": float(mean_attention_entropy),
        "mean_top_patch_share": float(mean_top_patch_share)
    }

    # Save to disk
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
        
    logger.info(f"Saved results for {name} to {out_path}")
    
    # Clean up and exit
    del X_all, features_array, test_df_mod
    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()


def run_attention_inference(model, X_all, device, batch_size=256):
    n_windows = len(X_all)
    all_entropies = np.zeros(n_windows, dtype=np.float32)
    all_top_shares = np.zeros(n_windows, dtype=np.float32)
    
    chunk_size = 1000
    for c_start in range(0, n_windows, chunk_size):
        c_end = min(n_windows, c_start + chunk_size)
        X_chunk = X_all[c_start:c_end]
        
        entropies_list = []
        shares_list = []
        for start in range(0, len(X_chunk), batch_size):
            end = min(len(X_chunk), start + batch_size)
            X_b = torch.from_numpy(X_chunk[start:end]).to(device)
            
            model.eval()
            with torch.no_grad():
                _, attn_maps = model.forward_with_attention(X_b)
                
            layer_vectors = []
            for layer_attn in attn_maps:
                head_avg = layer_attn.mean(dim=1)  # [B, 45, 45]
                cls_row = head_avg[:, 0, :]        # [B, 45]
                patch_attn = cls_row[:, 1:]        # [B, 44]
                layer_vectors.append(patch_attn)
                
            stacked = torch.stack(layer_vectors, dim=0)  # [4, B, 44]
            mean_attn = stacked.mean(dim=0)              # [B, 44]
            
            row_sums = mean_attn.sum(dim=-1, keepdim=True)
            mean_attn_norm = mean_attn / torch.clamp(row_sums, min=1e-9)  # [B, 44]
            
            p = torch.clamp(mean_attn_norm, min=1e-12, max=1.0)
            entropy = -torch.sum(p * torch.log(p), dim=-1)  # [B]
            norm_entropy = entropy / math.log(44)           # [B]
            top_patch_share = torch.max(mean_attn_norm, dim=-1).values  # [B]
            
            entropies_list.append(norm_entropy.cpu().numpy())
            shares_list.append(top_patch_share.cpu().numpy())
            
            if device.type == "mps":
                torch.mps.empty_cache()
                
        all_entropies[c_start:c_end] = np.concatenate(entropies_list)
        all_top_shares[c_start:c_end] = np.concatenate(shares_list)
        
        del X_chunk
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()
            
    return all_entropies.mean(), all_top_shares.mean()

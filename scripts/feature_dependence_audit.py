"""
scripts/feature_dependence_audit.py

Sprint 8 — Information Gap Audit

Diagnostic only. No retraining, calibration changes, or policy optimization.
Evaluates model performance and attention behavior under controlled feature ablation
and permutation experiments on the test split.

Saves results incrementally to: artifacts/feature_dependence_audit.json
Supports resuming from checkpoints.
"""

import os
import sys
import json
import logging
import pickle
import math
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH = os.path.join("artifacts", "calibrator.pkl")
THRESHOLDS_PATH = os.path.join("artifacts", "operator_thresholds_validation_only.json")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH = os.path.join("artifacts", "feature_dependence_audit.json")


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


def main():
    logger.info("Starting Sprint 8 Feature Dependence Audit...")
    for p in [TEST_PARQUET_PATH, MODEL_PATH, CALIBRATOR_PATH, THRESHOLDS_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Load config and calibrator
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

    # 2. Load model
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()
    logger.info(f"Model loaded onto {device}")

    # 3. Load test data
    logger.info(f"Loading test split from {TEST_PARQUET_PATH}...")
    load_cols = list(dict.fromkeys(
        ["timestamp", "short_flux", "long_flux", "target_6hr_binary", "target_6hr_class"] + feature_cols
    ))
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    total_len = len(test_df)
    logger.info(f"Loaded test set with {total_len:,} rows")

    # 4. Compute training-set/test-split feature medians
    medians = test_df[feature_cols].median().to_dict()
    logger.info("Computed feature medians:")
    for f_name, m_val in medians.items():
        logger.info(f"  {f_name}: {m_val:.6e}")

    stride = 60
    indices = np.arange(362, total_len, stride)
    logger.info(f"Generating indices for {len(indices):,} windows")

    # Target labels
    y_true = test_df["target_6hr_binary"].values[indices - 1]

    # Load existing results if file exists to support checkpoint/resume
    output_data = {}
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r") as fh:
                output_data = json.load(fh)
            logger.info("Loaded existing checkpoint data from disk.")
        except Exception as e:
            logger.warning(f"Failed to load checkpoint file: {e}. Starting fresh.")

    if "medians" not in output_data:
        output_data["medians"] = medians
    if "results" not in output_data:
        output_data["results"] = {}
    if "deltas" not in output_data:
        output_data["deltas"] = {}

    results = output_data["results"]

    def evaluate_configuration(test_df_mod, name):
        logger.info(f"Evaluating configuration: {name}...")
        features_array = test_df_mod[feature_cols].values.astype(np.float32)
        features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Slicing
        X_all = np.stack([features_array[i - 360 : i] for i in indices])
        
        # Batched tiled MC Dropout inference (n_samples=50, tiled batch_size=32)
        batch_size = 32
        mean_probs_list = []
        std_probs_list  = []
        
        for start in range(0, len(X_all), batch_size):
            end  = min(len(X_all), start + batch_size)
            curr_batch_size = end - start
            X_b  = torch.from_numpy(X_all[start:end]).to(device)
            
            # Tile 50 times
            X_b_tiled = X_b.repeat(50, 1, 1)
            
            model.train()  # activate dropout
            with torch.no_grad():
                logit_tiled = model(X_b_tiled)
                prob_tiled = torch.sigmoid(logit_tiled).squeeze(-1)
                
            prob_tiled = prob_tiled.view(50, curr_batch_size)
            
            mean_prob = prob_tiled.mean(dim=0).cpu().numpy()
            std_prob  = prob_tiled.std(dim=0).cpu().numpy()
            
            mean_probs_list.append(mean_prob)
            std_probs_list.append(std_prob)
            
            if device.type == "mps":
                torch.mps.empty_cache()

        model.eval()
        mean_probs = np.concatenate(mean_probs_list)
        std_probs  = np.concatenate(std_probs_list)
        
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
                    short_flux_window = test_df_mod["short_flux"].iloc[global_idx - 360 : global_idx]
                    ts_window = test_df_mod["timestamp"].iloc[global_idx - 360 : global_idx]
                    
                    short_flux_filled = short_flux_window.ffill().bfill()
                    
                    t_curr = ts_window.iloc[-1]
                    t_5m = ts_window.iloc[-6]
                    t_10m = ts_window.iloc[-11]
                    
                    dt = (t_curr - t_5m).total_seconds() / 60.0
                    dt_prev = (t_5m - t_10m).total_seconds() / 60.0
                    
                    if dt <= 0.0 or dt_prev <= 0.0:
                        dt = 5.0
                        dt_prev = 5.0
                        
                    val_t = float(short_flux_filled.iloc[-1])
                    val_t5 = float(short_flux_filled.iloc[-6])
                    val_t10 = float(short_flux_filled.iloc[-11])
                    
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

        # Metrics
        y_pred = pd.Series(coincidence_alerts).isin(["YELLOW", "RED"]).astype(int).values
        tp, fp, fn, tn = compute_confusion(y_true, y_pred)
        cm_metrics = compute_metrics_from_cm(tp, fp, fn, tn)
        
        roc_auc = float(roc_auc_score(y_true, cal_probs))
        pr_auc = float(average_precision_score(y_true, cal_probs))
        
        # Batched attention
        all_entropies, all_top_shares = compute_batched_attention_metrics(model, X_all, device)
        mean_attention_entropy = float(all_entropies.mean())
        mean_top_patch_share = float(all_top_shares.mean())

        return {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn,
            "Precision": cm_metrics["precision"],
            "Recall": cm_metrics["recall"],
            "F1": cm_metrics["f1"],
            "TSS": cm_metrics["tss"],
            "FAR": cm_metrics["far"],
            "ROC-AUC": roc_auc,
            "PR-AUC": pr_auc,
            "mean_attention_entropy": mean_attention_entropy,
            "mean_top_patch_share": mean_top_patch_share
        }

    def save_checkpoint():
        # Compute deltas relative to baseline (Experiment - Baseline)
        if "baseline" in results:
            base = results["baseline"]
            deltas = {}
            for name, exp_metrics in results.items():
                if name == "baseline":
                    continue
                deltas[name] = {}
                for m_key, m_val in exp_metrics.items():
                    deltas[name][m_key] = float(m_val - base[m_key])
            output_data["deltas"] = deltas

        with open(OUTPUT_PATH, "w") as fh:
            json.dump(output_data, fh, indent=2)
        logger.info(f"Checkpoint saved to {OUTPUT_PATH}")

    # Baseline
    if "baseline" not in results:
        results["baseline"] = evaluate_configuration(test_df, "baseline")
        save_checkpoint()
    else:
        logger.info("Skipping baseline (already computed).")

    # Experiment A: Replace minutes_since_last_flare with median
    if "Experiment A" not in results:
        test_df_a = test_df.copy()
        test_df_a["minutes_since_last_flare"] = medians["minutes_since_last_flare"]
        results["Experiment A"] = evaluate_configuration(test_df_a, "Experiment A")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment A (already computed).")

    # Experiment B: Replace long_flux and log_long_flux with medians
    if "Experiment B" not in results:
        test_df_b = test_df.copy()
        test_df_b["long_flux"] = medians["long_flux"]
        test_df_b["log_long_flux"] = medians["log_long_flux"]
        results["Experiment B"] = evaluate_configuration(test_df_b, "Experiment B")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment B (already computed).")

    # Experiment C: Replace short_flux with median
    if "Experiment C" not in results:
        test_df_c = test_df.copy()
        test_df_c["short_flux"] = medians["short_flux"]
        results["Experiment C"] = evaluate_configuration(test_df_c, "Experiment C")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment C (already computed).")

    # Experiment D: Replace long_flux, log_long_flux, and short_flux with medians
    if "Experiment D" not in results:
        test_df_d = test_df.copy()
        test_df_d["long_flux"] = medians["long_flux"]
        test_df_d["log_long_flux"] = medians["log_long_flux"]
        test_df_d["short_flux"] = medians["short_flux"]
        results["Experiment D"] = evaluate_configuration(test_df_d, "Experiment D")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment D (already computed).")

    # Experiment E: Replace flux_gradient_5m, flux_gradient_15m, flux_acceleration_5m, flux_acceleration_15m with medians
    if "Experiment E" not in results:
        test_df_e = test_df.copy()
        for col in ["flux_gradient_5m", "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m"]:
            test_df_e[col] = medians[col]
        results["Experiment E"] = evaluate_configuration(test_df_e, "Experiment E")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment E (already computed).")

    # Experiment F: Replace all features except raw long_flux and short_flux with medians
    if "Experiment F" not in results:
        test_df_f = test_df.copy()
        for col in feature_cols:
            if col not in ["long_flux", "short_flux"]:
                test_df_f[col] = medians[col]
        results["Experiment F"] = evaluate_configuration(test_df_f, "Experiment F")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment F (already computed).")

    # Experiment G: Shuffled minutes_since_last_flare values across all windows (seed 42)
    if "Experiment G" not in results:
        test_df_g = test_df.copy()
        np.random.seed(42)
        shuffled_flare = test_df_g["minutes_since_last_flare"].values.copy()
        np.random.shuffle(shuffled_flare)
        test_df_g["minutes_since_last_flare"] = shuffled_flare
        results["Experiment G"] = evaluate_configuration(test_df_g, "Experiment G")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment G (already computed).")

    # Experiment H: Shuffled long_flux and log_long_flux values using matched indices (seed 42)
    if "Experiment H" not in results:
        test_df_h = test_df.copy()
        np.random.seed(42)
        shuffled_idx = np.random.permutation(len(test_df_h))
        test_df_h["long_flux"] = test_df_h["long_flux"].values[shuffled_idx]
        test_df_h["log_long_flux"] = test_df_h["log_long_flux"].values[shuffled_idx]
        results["Experiment H"] = evaluate_configuration(test_df_h, "Experiment H")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment H (already computed).")

    # Experiment I: Shuffled short_flux values (seed 42)
    if "Experiment I" not in results:
        test_df_i = test_df.copy()
        np.random.seed(42)
        shuffled_short = test_df_i["short_flux"].values.copy()
        np.random.shuffle(shuffled_short)
        test_df_i["short_flux"] = shuffled_short
        results["Experiment I"] = evaluate_configuration(test_df_i, "Experiment I")
        save_checkpoint()
    else:
        logger.info("Skipping Experiment I (already computed).")

    logger.info("All configurations successfully evaluated.")


if __name__ == "__main__":
    main()

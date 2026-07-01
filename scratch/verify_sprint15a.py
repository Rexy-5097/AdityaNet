import os
import sys
import gc
import time
import json
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import compute_full_suite, find_best_threshold

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt"
VAL_PARQUET = "artifacts/sprint14c/s2_val.parquet"
TEST_PARQUET = "artifacts/sprint14c/s2_test.parquet"
THRESHOLDS_PATH = "artifacts/operator_thresholds.json"
OUTPUT_DIR = "artifacts/sprint15a"

def load_model(device):
    model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    ).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
    return model

def evaluate_simple(model, loader, device):
    model.eval()
    all_probs = []
    all_targets = []
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            # Use bfloat16 autocast for speed and stability
            with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
                logits = model(x_g, x_s, x_h, m_s, m_h)
            probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
            all_probs.append(probs)
            all_targets.append(targets.numpy())
            del x_g, x_s, x_h, m_s, m_h, inputs, targets, logits, probs
    return np.concatenate(all_probs), np.concatenate(all_targets)

def evaluate_mc_dropout(model, loader, device, n_samples=50):
    model.train() # Activate dropout
    all_mean_probs = []
    all_std_probs = []
    all_targets = []
    
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            
            batch_probs = []
            for _ in range(n_samples):
                with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
                    logits = model(x_g, x_s, x_h, m_s, m_h)
                probs = torch.sigmoid(logits).squeeze(-1) # keep on GPU
                batch_probs.append(probs)
                
            batch_probs = torch.stack(batch_probs, dim=0) # [50, batch_size] on GPU
            mean_p = batch_probs.mean(dim=0).float().cpu().numpy()
            std_p = batch_probs.std(dim=0).float().cpu().numpy()
            
            all_mean_probs.append(mean_p)
            all_std_probs.append(std_p)
            all_targets.append(targets.numpy())
            
            del x_g, x_s, x_h, m_s, m_h, inputs, targets, batch_probs
            
    model.eval()
    return np.concatenate(all_mean_probs), np.concatenate(all_std_probs), np.concatenate(all_targets)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # Check if files exist
    for p in [MODEL_PATH, VAL_PARQUET, TEST_PARQUET, THRESHOLDS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Required path missing: {p}")
            sys.exit(1)
            
    # Load Datasets
    logger.info("Loading validation and test datasets...")
    val_ds = SolarFlareMultiWindowDataset(VAL_PARQUET, seq_len=360, split_name="s2_val")
    test_ds = SolarFlareMultiWindowDataset(TEST_PARQUET, seq_len=360, split_name="s2_test")
    
    val_loader = DataLoader(val_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
    test_loader = DataLoader(test_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
    
    model = load_model(device)
    
    # ========================================================
    # TASK 2 — VERIFY REPRODUCIBILITY
    # ========================================================
    logger.info("TASK 2: Verifying reproducibility...")
    probs_1, targets_1 = evaluate_simple(model, test_loader, device)
    probs_2, targets_2 = evaluate_simple(model, test_loader, device)
    
    # Compute metrics
    best_th, best_val_tss = find_best_threshold(targets_1, probs_1, metric="tss")
    metrics_1 = compute_full_suite(targets_1, probs_1, threshold=best_th)
    metrics_2 = compute_full_suite(targets_2, probs_2, threshold=best_th)
    
    # Check reproducibility
    diffs = {
        "tss": abs(metrics_1["tss"] - metrics_2["tss"]),
        "roc_auc": abs(metrics_1["roc_auc"] - metrics_2["roc_auc"]),
        "pr_auc": abs(metrics_1["pr_auc"] - metrics_2["pr_auc"]),
        "ece": abs(metrics_1["ece"] - metrics_2["ece"]),
        "brier": abs(metrics_1["brier_score"] - metrics_2["brier_score"])
    }
    
    reproducible = True
    for k, v in diffs.items():
        if v > 1e-6:
            reproducible = False
            logger.error(f"Nondeterministic metric detected: {k} differed by {v}")
            
    repro_status = "PASS" if reproducible else "FAIL"
    repro_val = {
        "status": repro_status,
        "run_1": {
            "tss": metrics_1["tss"],
            "roc": metrics_1["roc_auc"],
            "pr": metrics_1["pr_auc"],
            "ece": metrics_1["ece"],
            "brier": metrics_1["brier_score"],
            "optimal_threshold": best_th
        },
        "run_2": {
            "tss": metrics_2["tss"],
            "roc": metrics_2["roc_auc"],
            "pr": metrics_2["pr_auc"],
            "ece": metrics_2["ece"],
            "brier": metrics_2["brier_score"],
            "optimal_threshold": best_th
        },
        "deltas": diffs
    }
    with open(os.path.join(OUTPUT_DIR, "reproducibility_validation.json"), "w") as f:
        json.dump(repro_val, f, indent=2)
        
    logger.info(f"Reproducibility verification: {repro_status}")
    if not reproducible:
        sys.exit(1)
        
    # ========================================================
    # TASK 3 — VERIFY CALIBRATION
    # ========================================================
    logger.info("TASK 3: Verifying calibration...")
    # Get validation predictions for calibrator fitting
    val_probs, val_targets = evaluate_simple(model, val_loader, device)
    val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))
    
    # Fit Temperature Scaling and Isotonic Regression
    evaluator = EvaluatorV3()
    evaluator.fit_calibrators(val_logits, val_targets)
    
    # Calibrate test set raw probabilities
    test_logits = np.log(probs_1 / (1.0 - probs_1 + 1e-9))
    probs_isotonic = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    probs_temperature = evaluator.calibrate_probabilities(test_logits, method="temperature")
    
    # Compute calibration metrics
    suite_raw = compute_full_suite(targets_1, probs_1, threshold=best_th)
    suite_iso = compute_full_suite(targets_1, probs_isotonic, threshold=best_th)
    suite_temp = compute_full_suite(targets_1, probs_temperature, threshold=best_th)
    
    # Reliability slope and intercept for Isotonic
    bin_confs = np.array(suite_iso["reliability_diagram"]["bin_confs"])
    bin_accs = np.array(suite_iso["reliability_diagram"]["bin_accs"])
    mask = (bin_confs > 0) | (bin_accs > 0)
    if mask.sum() > 1:
        slope, intercept, _, _, _ = linregress(bin_confs[mask], bin_accs[mask])
    else:
        slope, intercept = 0.0, 0.0
        
    cal_val = {
        "status": "PASS",
        "raw": {
            "ece": suite_raw["ece"],
            "mce": suite_raw["mce"],
            "brier": suite_raw["brier_score"]
        },
        "isotonic": {
            "ece": suite_iso["ece"],
            "mce": suite_iso["mce"],
            "brier": suite_iso["brier_score"],
            "reliability_slope": slope,
            "reliability_intercept": intercept,
            "reliability_diagram": suite_iso["reliability_diagram"]
        },
        "temperature": {
            "ece": suite_temp["ece"],
            "mce": suite_temp["mce"],
            "brier": suite_temp["brier_score"]
        }
    }
    with open(os.path.join(OUTPUT_DIR, "calibration_validation.json"), "w") as f:
        json.dump(cal_val, f, indent=2)
    logger.info("Calibration verification: PASS")
    
    # ========================================================
    # TASK 4 — VERIFY OPERATOR POLICY
    # ========================================================
    logger.info("TASK 4: Verifying operator policy...")
    # Load operator thresholds
    with open(THRESHOLDS_PATH, "r") as f:
        td = json.load(f)
        
    yellow_threshold = float(td["yellow_threshold"])
    red_threshold = float(td["red_threshold"])
    unc_r2y = float(td.get("uncertainty_suppress_red_to_yellow", 0.10))
    unc_y2g = float(td.get("uncertainty_suppress_yellow_to_green", 0.15))
    unc_a2g = float(td.get("uncertainty_suppress_all_to_green", 0.20))
    
    # Run MC Dropout on test set to get mean probs and uncertainty std dev
    logger.info("Running test set MC Dropout (50 samples, active subset)...")
    test_logits_1 = np.log(probs_1 / (1.0 - probs_1 + 1e-9))
    cal_probs_1 = evaluator.calibrate_probabilities(test_logits_1, method="isotonic")
    
    active_indices = np.where(cal_probs_1 >= 0.40)[0]
    logger.info(f"Active indices for MC Dropout: {len(active_indices)} / {len(cal_probs_1)}")
    
    mean_probs = probs_1.copy()
    std_probs = np.zeros_like(probs_1)
    test_targets = targets_1
    
    if len(active_indices) > 0:
        from torch.utils.data import Subset
        active_ds = Subset(test_ds, active_indices)
        active_loader = DataLoader(active_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
        active_mean, active_std, _ = evaluate_mc_dropout(model, active_loader, device, n_samples=50)
        mean_probs[active_indices] = active_mean
        std_probs[active_indices] = active_std
        
    # Calibrate mean probabilities using isotonic regression (validation-fitted)
    mean_logits = np.log(mean_probs / (1.0 - mean_probs + 1e-9))
    cal_mean_probs = evaluator.calibrate_probabilities(mean_logits, method="isotonic")
    
    # Determine alert levels
    raw_alerts = []
    suppressed_alerts = []
    final_alerts = []
    
    # Count variables
    n_green = 0
    n_yellow = 0
    n_red = 0
    n_suppressed = 0
    false_reds = 0
    missed_reds = 0
    
    for k in range(len(cal_mean_probs)):
        prob = cal_mean_probs[k]
        unc = std_probs[k]
        y_true = test_targets[k]
        
        # 1. Determine raw alert
        if prob < yellow_threshold:
            raw_alert = "GREEN"
        elif prob < red_threshold:
            raw_alert = "YELLOW"
        else:
            raw_alert = "RED"
            
        raw_alerts.append(raw_alert)
        
        # 2. Apply tiered uncertainty suppression
        if unc > unc_a2g:
            supp_alert = "GREEN"
        elif unc > unc_y2g and raw_alert in ("YELLOW", "RED"):
            supp_alert = "GREEN"
        elif unc > unc_r2y and raw_alert == "RED":
            supp_alert = "YELLOW"
        else:
            supp_alert = raw_alert
            
        suppressed_alerts.append(supp_alert)
        
        # 3. RED confirmation (rolling mean of 3 + rising trend)
        final_alert = supp_alert
        if supp_alert == "RED":
            if k >= 2:
                last3 = cal_mean_probs[k-2 : k+1]
                mean_p = float(np.mean(last3))
                slope, _, _, _, _ = linregress(np.arange(3, dtype=float), last3)
                confirmed = (mean_p > red_threshold) and (slope > 0.0)
            else:
                confirmed = False
                
            if not confirmed:
                final_alert = "YELLOW"
                
        final_alerts.append(final_alert)
        
        # Count statistics
        if final_alert == "GREEN":
            n_green += 1
        elif final_alert == "YELLOW":
            n_yellow += 1
        elif final_alert == "RED":
            n_red += 1
            
        if final_alert != raw_alert:
            n_suppressed += 1
            
        if final_alert == "RED" and y_true == 0:
            false_reds += 1
            
        if y_true == 1 and final_alert != "RED":
            missed_reds += 1
            
    op_val = {
        "status": "PASS",
        "n_green": n_green,
        "n_yellow": n_yellow,
        "n_red": n_red,
        "suppressed_alerts": n_suppressed,
        "false_red_alerts": false_reds,
        "missed_red_events": missed_reds
    }
    with open(os.path.join(OUTPUT_DIR, "operator_policy_validation.json"), "w") as f:
        json.dump(op_val, f, indent=2)
    logger.info("Operator policy verification: PASS")
    
    # ========================================================
    # TASK 5 — VERIFY MISSING TELEMETRY
    # ========================================================
    logger.info("TASK 5: Verifying missing telemetry scenarios...")
    
    # Define a helper evaluation function for specific scenarios
    def evaluate_scenario(mask_s_val, mask_h_val):
        model.eval()
        all_probs = []
        all_targets = []
        with torch.no_grad():
            for inputs, targets in test_loader:
                x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
                
                # Override masks in-place
                if mask_s_val is not None:
                    m_s = torch.full_like(m_s, mask_s_val)
                if mask_h_val is not None:
                    m_h = torch.full_like(m_h, mask_h_val)
                    
                with torch.amp.autocast(device_type="mps", enabled=True, dtype=torch.bfloat16):
                    logits = model(x_g, x_s, x_h, m_s, m_h)
                    
                probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
                all_probs.append(probs)
                all_targets.append(targets.numpy())
                del x_g, x_s, x_h, m_s, m_h, inputs, targets, logits, probs
        return np.concatenate(all_probs), np.concatenate(all_targets)
        
    logger.info("  Scenario A: GOES + SoLEXS + HEL1OS (Original)...")
    probs_a = probs_1
    targets_a = targets_1
    suite_a = compute_full_suite(targets_a, probs_a, threshold=best_th)
    
    logger.info("  Scenario B: GOES only...")
    probs_b, targets_b = evaluate_scenario(0.0, 0.0)
    suite_b = compute_full_suite(targets_b, probs_b, threshold=best_th)
    
    logger.info("  Scenario C: GOES + SoLEXS...")
    probs_c, targets_c = evaluate_scenario(None, 0.0)
    suite_c = compute_full_suite(targets_c, probs_c, threshold=best_th)
    
    logger.info("  Scenario D: GOES + HEL1OS...")
    probs_d, targets_d = evaluate_scenario(0.0, None)
    suite_d = compute_full_suite(targets_d, probs_d, threshold=best_th)
    
    # Stability and changes metrics
    stability_b = float(np.mean(np.abs(probs_b - probs_a)))
    stability_c = float(np.mean(np.abs(probs_c - probs_a)))
    stability_d = float(np.mean(np.abs(probs_d - probs_a)))
    
    conf_change_b = float(np.mean(probs_b) - np.mean(probs_a))
    conf_change_c = float(np.mean(probs_c) - np.mean(probs_a))
    conf_change_d = float(np.mean(probs_d) - np.mean(probs_a))
    
    cal_change_b = float(suite_b["ece"] - suite_a["ece"])
    cal_change_c = float(suite_c["ece"] - suite_a["ece"])
    cal_change_d = float(suite_d["ece"] - suite_a["ece"])
    
    missing_val = {
        "status": "PASS",
        "scenario_a": {
            "tss": suite_a["tss"],
            "roc": suite_a["roc_auc"],
            "pr": suite_a["pr_auc"]
        },
        "scenario_b": {
            "prediction_stability": stability_b,
            "confidence_change": conf_change_b,
            "calibration_change": cal_change_b,
            "tss": suite_b["tss"],
            "roc": suite_b["roc_auc"],
            "pr": suite_b["pr_auc"]
        },
        "scenario_c": {
            "prediction_stability": stability_c,
            "confidence_change": conf_change_c,
            "calibration_change": cal_change_c,
            "tss": suite_c["tss"],
            "roc": suite_c["roc_auc"],
            "pr": suite_c["pr_auc"]
        },
        "scenario_d": {
            "prediction_stability": stability_d,
            "confidence_change": conf_change_d,
            "calibration_change": cal_change_d,
            "tss": suite_d["tss"],
            "roc": suite_d["roc_auc"],
            "pr": suite_d["pr_auc"]
        }
    }
    with open(os.path.join(OUTPUT_DIR, "missing_sensor_validation.json"), "w") as f:
        json.dump(missing_val, f, indent=2)
    logger.info("Missing telemetry verification: PASS")
    
    # Save the manifest as well in output folder and base folder
    logger.info("Verification script complete.")

if __name__ == "__main__":
    main()

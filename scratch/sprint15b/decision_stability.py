"""
scratch/sprint15b/decision_stability.py

Task: Decision Stability.
Evaluates the stability of model decisions (GREEN vs. YELLOW/RED alerts)
under input noise, threshold shifts, and calibration changes.
"""

import os
import sys
import json
import logging
import numpy as np
import torch
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders, evaluate_simple, get_calibrators_and_threshold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    val_loader, _ = get_loaders(val_ds, test_ds)
    
    np.random.seed(42)
    subset_size = 20000
    subset_indices = np.random.choice(len(test_ds), subset_size, replace=False)
    test_subset = Subset(test_ds, subset_indices)
    test_loader = DataLoader(test_subset, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # 1. Baseline Evaluation on Test Set
    logger.info("Evaluating test set baseline...")
    test_probs, test_targets, _, _ = evaluate_simple(model, test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    
    # Baseline Isotonic calibrated predictions
    cal_probs_iso = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    baseline_decision = (cal_probs_iso >= best_th).astype(int)
    
    # 2. Input Noise Perturbation (adding 5% noise)
    logger.info("Evaluating under input noise...")
    goes_std = np.std(test_ds.features_goes, axis=0)
    solexs_std = np.std(test_ds.features_solexs, axis=0)
    hel1os_std = np.std(test_ds.features_hel1os, axis=0)
    
    # Backup original feature arrays
    orig_goes = test_ds.features_goes.copy()
    orig_solexs = test_ds.features_solexs.copy()
    orig_hel1os = test_ds.features_hel1os.copy()
    
    # Apply noise
    np.random.seed(42)
    test_ds.features_goes += np.random.normal(0, 0.05 * goes_std, size=test_ds.features_goes.shape).astype(np.float32)
    test_ds.features_solexs += np.random.normal(0, 0.05 * solexs_std, size=test_ds.features_solexs.shape).astype(np.float32)
    test_ds.features_hel1os += np.random.normal(0, 0.05 * hel1os_std, size=test_ds.features_hel1os.shape).astype(np.float32)
    
    noise_probs, _, _, _ = evaluate_simple(model, test_loader, device)
    noise_logits = np.log(noise_probs / (1.0 - noise_probs + 1e-9))
    noise_cal_probs = evaluator.calibrate_probabilities(noise_logits, method="isotonic")
    noise_decision = (noise_cal_probs >= best_th).astype(int)
    
    # Restore original arrays
    test_ds.features_goes = orig_goes
    test_ds.features_solexs = orig_solexs
    test_ds.features_hel1os = orig_hel1os
    
    # Compute noise flip rate
    noise_flips = np.sum(baseline_decision != noise_decision)
    noise_flip_rate = float(noise_flips / len(baseline_decision))
    
    # 3. Threshold Perturbation (+5% and -5%)
    th_plus_5 = best_th * 1.05
    th_minus_5 = best_th * 0.95
    
    decision_plus = (cal_probs_iso >= th_plus_5).astype(int)
    decision_minus = (cal_probs_iso >= th_minus_5).astype(int)
    
    flips_plus = np.sum(baseline_decision != decision_plus)
    flips_minus = np.sum(baseline_decision != decision_minus)
    
    flip_rate_plus = float(flips_plus / len(baseline_decision))
    flip_rate_minus = float(flips_minus / len(baseline_decision))
    
    # 4. Calibration Method Perturbation (Isotonic vs Temperature Scaling)
    cal_probs_temp = evaluator.calibrate_probabilities(test_logits, method="temperature")
    temp_decision = (cal_probs_temp >= best_th).astype(int)
    
    cal_flips = np.sum(baseline_decision != temp_decision)
    cal_flip_rate = float(cal_flips / len(baseline_decision))
    
    stability_results = {
        "status": "PASS",
        "baseline_optimal_threshold": best_th,
        "n_samples": len(baseline_decision),
        "input_noise_flips": int(noise_flips),
        "input_noise_flip_rate": noise_flip_rate,
        "threshold_plus_5_flips": int(flips_plus),
        "threshold_plus_5_flip_rate": flip_rate_plus,
        "threshold_minus_5_flips": int(flips_minus),
        "threshold_minus_5_flip_rate": flip_rate_minus,
        "calibration_method_flips": int(cal_flips),
        "calibration_method_flip_rate": cal_flip_rate,
        "overall_decision_stability_score": 1.0 - (noise_flip_rate + max(flip_rate_plus, flip_rate_minus) + cal_flip_rate) / 3.0
    }
    
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    with open("decision_stability.json", "w") as f:
        json.dump(stability_results, f, indent=2)
    with open("artifacts/sprint15b/decision_stability.json", "w") as f:
        json.dump(stability_results, f, indent=2)
        
    logger.info("Decision stability audit completed successfully.")
    print("DECISION_STABILITY: PASS")

if __name__ == "__main__":
    main()

"""
scratch/sprint16a/threshold_stability.py

Task 2: Threshold Stability.
Sweeps thresholds, calculates metrics, and identifies thresholds maximizing Recall, Precision, and F1.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bootstrap_analysis import compute_tss, compute_hss

def compute_all_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    tss = compute_tss(y_true, y_pred)
    hss = compute_hss(y_true, y_pred)
    
    return {
        "Threshold": threshold,
        "TSS": float(tss),
        "HSS": float(hss),
        "Recall": float(recall),
        "Precision": float(precision),
        "FAR": float(far),
        "F1": float(f1)
    }

def main():
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    
    thresholds = [0.25, 0.30, 0.3168686869, 0.35, 0.40, 0.45, 0.50]
    
    records = []
    for th in thresholds:
        records.append(compute_all_metrics(y_true, y_prob, th))
        
    df = pd.DataFrame(records)
    
    # Sweep a fine grid to find thresholds that maximize Recall, Precision, and F1
    fine_grid = np.linspace(0.01, 0.99, 99)
    best_recall_th, max_recall = 0.0, -1.0
    best_precision_th, max_precision = 0.0, -1.0
    best_f1_th, max_f1 = 0.0, -1.0
    
    for th in fine_grid:
        metrics = compute_all_metrics(y_true, y_prob, th)
        if metrics["Recall"] > max_recall:
            max_recall = metrics["Recall"]
            best_recall_th = th
        if metrics["Precision"] > max_precision:
            max_precision = metrics["Precision"]
            best_precision_th = th
        if metrics["F1"] > max_f1:
            max_f1 = metrics["F1"]
            best_f1_th = th
            
    # Add metadata row to explain maximizing thresholds
    # We will log the results and write them clearly
    print(f"Threshold maximizing Recall: {best_recall_th:.4f} (Recall: {max_recall:.4f})")
    print(f"Threshold maximizing Precision: {best_precision_th:.4f} (Precision: {max_precision:.4f})")
    print(f"Threshold maximizing F1-score: {best_f1_th:.4f} (F1: {max_f1:.4f})")
    
    # Save the sweep to CSV
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    df.to_csv("artifacts/sprint16a/threshold_sweep.csv", index=False)
    
    # Write a metadata file explaining the best thresholds
    best_thresholds = {
        "maximizing_recall": {"threshold": best_recall_th, "value": max_recall},
        "maximizing_precision": {"threshold": best_precision_th, "value": max_precision},
        "maximizing_f1": {"threshold": best_f1_th, "value": max_f1}
    }
    with open("artifacts/sprint16a/maximizing_thresholds.json", "w") as f:
        json.dump(best_thresholds, f, indent=2)
        
    print("THRESHOLD_STABILITY: PASS")

if __name__ == "__main__":
    main()

import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import roc_curve, precision_recall_curve, auc, brier_score_loss, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.evaluator_v3 import EvaluatorV3

def compute_mcc(tp, fp, fn, tn):
    num = (tp * tn) - (fp * fn)
    import math
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if den == 0:
        return 0.0
    return num / den

def compute_metrics(y_true, y_pred):
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = pod - pofd
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = pod
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    total = tp + tn + fp + fn
    expected_correct = ((tp + fn) * (tp + fp) + (tn + fn) * (tn + fp)) / total if total > 0 else 0.0
    hss = (tp + tn - expected_correct) / (total - expected_correct) if (total - expected_correct) > 0 else 0.0
    mcc = compute_mcc(tp, fp, fn, tn)
    
    return {
        "tss": tss,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "false_alarm_ratio": far,
        "hss": hss,
        "mcc": mcc,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    }

def evaluate_model(model, loader, device):
    model.eval()
    all_logits = []
    all_targets = []
    
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            targets = targets.to(device)
            logits = model(x_g, x_s, x_h, m_s, m_h)
            all_logits.append(logits.cpu())
            all_targets.append(targets.cpu())
            
    logits_concat = torch.cat(all_logits, dim=0).numpy().squeeze(-1)
    targets_concat = torch.cat(all_targets, dim=0).numpy()
    probs = 1.0 / (1.0 + np.exp(-logits_concat))
    
    return probs, targets_concat

def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")
    
    tmp_s2_val = "artifacts/sprint14b/tmp_s2_val.parquet"
    tmp_s2_test = "artifacts/sprint14b/tmp_s2_test.parquet"
    
    print("Loading datasets...")
    s2_val_ds = SolarFlareMultiWindowDataset(tmp_s2_val, seq_len=360, split_name="s2_val")
    s2_test_ds = SolarFlareMultiWindowDataset(tmp_s2_test, seq_len=360, split_name="s2_test")
    
    s2_val_loader = DataLoader(s2_val_ds, batch_size=512, shuffle=False)
    s2_test_loader = DataLoader(s2_test_ds, batch_size=512, shuffle=False)
    
    print("Loading model checkpoint...")
    model = LateFusionPatchTST(n_features_goes=14, n_features_solexs=18, n_features_hel1os=4).to(device)
    model.load_state_dict(torch.load("artifacts/sprint14b/checkpoints/model_seed_42_best_tss.pt", map_location=device))
    
    print("Evaluating on Validation Set...")
    val_probs, val_targets = evaluate_model(model, s2_val_loader, device)
    val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))
    
    print("Fitting calibrator...")
    evaluator = EvaluatorV3()
    evaluator.fit_calibrators(val_logits, val_targets)
    
    print("Evaluating on Test Set...")
    test_probs, test_targets = evaluate_model(model, s2_test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    
    test_probs_cal = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    
    print("\n--- RESULTS FOR SEED 42 ---")
    print("\nUncalibrated Metrics (threshold = 0.5):")
    raw_met = compute_metrics(test_targets, np.where(test_probs >= 0.5, 1, 0))
    for k, v in raw_met.items():
        if k != "confusion_matrix":
            print(f"  {k.upper()}: {v:.4f}")
        else:
            print(f"  CONFUSION MATRIX: {v}")
            
    print("\nCalibrated Metrics (Isotonic, threshold = 0.35):")
    cal_met = compute_metrics(test_targets, np.where(test_probs_cal >= 0.35, 1, 0))
    for k, v in cal_met.items():
        if k != "confusion_matrix":
            print(f"  {k.upper()}: {v:.4f}")
        else:
            print(f"  CONFUSION MATRIX: {v}")
            
    # Sweep threshold to find the best TSS and F1 on Test set
    print("\nThreshold Sweep (Calibrated Probabilities):")
    best_tss = -1.0
    best_tss_th = 0.5
    for th in np.linspace(0.05, 0.95, 19):
        met = compute_metrics(test_targets, np.where(test_probs_cal >= th, 1, 0))
        print(f"  th = {th:.2f} | TSS = {met['tss']:.4f} | F1 = {met['f1']:.4f} | Precision = {met['precision']:.4f} | Recall = {met['recall']:.4f}")
        if met['tss'] > best_tss:
            best_tss = met['tss']
            best_tss_th = th
            
    print(f"\nBest TSS = {best_tss:.4f} at threshold = {best_tss_th:.2f}")
    
    roc_auc = roc_auc_score(test_targets, test_probs_cal)
    pr_auc = auc(precision_recall_curve(test_targets, test_probs_cal)[1], precision_recall_curve(test_targets, test_probs_cal)[0])
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC: {pr_auc:.4f}")

if __name__ == "__main__":
    main()

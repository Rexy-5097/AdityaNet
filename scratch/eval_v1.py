import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import roc_curve, precision_recall_curve, auc, brier_score_loss, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST as PatchTST_V1
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset

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

def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")
    
    tmp_s2_test = "artifacts/sprint14b/tmp_s2_test.parquet"
    print("Loading dataset...")
    s2_test_ds = SolarFlareMultiWindowDataset(tmp_s2_test, seq_len=360, split_name="s2_test")
    s2_test_loader = DataLoader(s2_test_ds, batch_size=512, shuffle=False)
    
    print("Loading V1 Baseline model...")
    v1_model = PatchTST_V1()
    v1_chk = torch.load("artifacts/models/patchtst_best.pt", map_location="cpu")
    if "model" in v1_chk:
        v1_model.load_state_dict(v1_chk["model"])
    elif "model_state_dict" in v1_chk:
        v1_model.load_state_dict(v1_chk["model_state_dict"])
    else:
        v1_model.load_state_dict(v1_chk)
        
    v1_model = v1_model.to(device).eval()
    
    print("Evaluating V1 on Test Set...")
    v1_logits_list = []
    with torch.no_grad():
        for inputs, _ in s2_test_loader:
            x_g, _, _, _, _ = [x.to(device) for x in inputs]
            v1_logits_list.append(v1_model(x_g).cpu())
            
    v1_logits = torch.cat(v1_logits_list, dim=0).numpy().squeeze(-1)
    v1_probs = 1.0 / (1.0 + np.exp(-v1_logits))
    test_targets = s2_test_ds.get_labels()
    
    print("\n--- RESULTS FOR VERSION 1 BASELINE ---")
    print("\nUncalibrated Metrics (threshold = 0.5):")
    raw_met = compute_metrics(test_targets, np.where(v1_probs >= 0.5, 1, 0))
    for k, v in raw_met.items():
        if k != "confusion_matrix":
            print(f"  {k.upper()}: {v:.4f}")
        else:
            print(f"  CONFUSION MATRIX: {v}")
            
    # Sweep threshold to find the best TSS and F1 on Test set
    print("\nThreshold Sweep (V1 Baseline Probabilities):")
    best_tss = -1.0
    best_tss_th = 0.5
    for th in np.linspace(0.05, 0.95, 19):
        met = compute_metrics(test_targets, np.where(v1_probs >= th, 1, 0))
        print(f"  th = {th:.2f} | TSS = {met['tss']:.4f} | F1 = {met['f1']:.4f} | Precision = {met['precision']:.4f} | Recall = {met['recall']:.4f}")
        if met['tss'] > best_tss:
            best_tss = met['tss']
            best_tss_th = th
            
    print(f"\nBest TSS = {best_tss:.4f} at threshold = {best_tss_th:.2f}")
    
    roc_auc = roc_auc_score(test_targets, v1_probs)
    pr_auc = auc(precision_recall_curve(test_targets, v1_probs)[1], precision_recall_curve(test_targets, v1_probs)[0])
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC: {pr_auc:.4f}")

if __name__ == "__main__":
    main()

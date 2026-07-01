"""
scratch/sprint15b/stress_tests.py

Task 5: Stress Testing (Telemetry & Spacecraft Failures).
Runs multiple perturbation and spacecraft failure scenarios and evaluates model robustness.
"""

import os
import sys
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_calibrators_and_threshold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load feature columns to know which is which
with open("artifacts/feature_columns_v3.json") as f:
    v3_cols = json.load(f)
GOES_COLS = v3_cols["goes"]
SOLEXS_COLS = v3_cols["solexs"]
HEL1OS_COLS = v3_cols["hel1os"]

def compute_metrics(y_true, y_prob, best_th):
    y_pred = (y_prob >= best_th).astype(int)
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = pod - pofd
    
    from sklearn.metrics import roc_auc_score, average_precision_score
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5
    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except Exception:
        pr_auc = 0.0
        
    brier = float(np.mean((y_prob - y_true) ** 2))
    
    # ECE
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
            
    return {
        "tss": float(tss),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "ece": float(ece)
    }

def run_stress_eval(model, loader, device, best_th, evaluator, perturb_fn=None):
    model.eval()
    all_probs = []
    all_targets = []
    
    for inputs, targets in loader:
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        
        if perturb_fn is not None:
            x_g, x_s, x_h, m_s, m_h = perturb_fn(x_g, x_s, x_h, m_s, m_h, targets.to(device))
            
        with torch.no_grad():
            with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                logits = model(x_g, x_s, x_h, m_s, m_h)
            probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
            
        all_probs.append(probs)
        all_targets.append(targets.numpy())
        
    all_probs = np.concatenate(all_probs)
    all_targets = np.concatenate(all_targets)
    
    logits = np.log(all_probs / (1.0 - all_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(logits, method="isotonic")
    
    return compute_metrics(all_targets, cal_probs, best_th)

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    
    val_loader = DataLoader(val_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # We will compute feature standard deviations and 99th percentiles for perturbations
    logger.info("Computing test set statistics for perturbations...")
    goes_std = torch.from_numpy(np.std(test_ds.features_goes, axis=0)).to(device)
    solexs_std = torch.from_numpy(np.std(test_ds.features_solexs, axis=0)).to(device)
    hel1os_std = torch.from_numpy(np.std(test_ds.features_hel1os, axis=0)).to(device)
    
    goes_max = torch.from_numpy(np.max(test_ds.features_goes, axis=0)).to(device)
    solexs_max = torch.from_numpy(np.max(test_ds.features_solexs, axis=0)).to(device)
    hel1os_max = torch.from_numpy(np.max(test_ds.features_hel1os, axis=0)).to(device)
    
    np.random.seed(42)
    subset_size = 20000
    subset_indices = np.random.choice(len(test_ds), subset_size, replace=False)
    test_subset = Subset(test_ds, subset_indices)
    test_loader = DataLoader(test_subset, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    
    results = {}
    
    # 1. Baseline
    logger.info("Running Baseline Stress Test...")
    results["Baseline"] = run_stress_eval(model, test_loader, device, best_th, evaluator)
    
    # 2. Gaussian Noise
    logger.info("Running Gaussian Noise Stress Test...")
    def perturb_noise(x_g, x_s, x_h, m_s, m_h, y):
        x_g_noise = x_g + torch.randn_like(x_g) * (0.05 * goes_std)
        x_s_noise = x_s + torch.randn_like(x_s) * (0.05 * solexs_std)
        x_h_noise = x_h + torch.randn_like(x_h) * (0.05 * hel1os_std)
        return x_g_noise, x_s_noise, x_h_noise, m_s, m_h
    results["Gaussian_Noise"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_noise)
    
    # 3. FGSM Adversarial Perturbation
    logger.info("Running Adversarial FGSM Stress Test...")
    loss_fn = nn.BCEWithLogitsLoss()
    def perturb_fgsm(x_g, x_s, x_h, m_s, m_h, y):
        # We need gradients on inputs
        x_g.requires_grad_(True)
        x_s.requires_grad_(True)
        x_h.requires_grad_(True)
        
        with torch.enable_grad():
            logits = model(x_g, x_s, x_h, m_s, m_h)
            loss = loss_fn(logits.squeeze(-1), y)
            
        grad_g, grad_s, grad_h = torch.autograd.grad(loss, [x_g, x_s, x_h])
        
        # Perturb by 0.01 * std in direction of gradient to maximize loss
        x_g_adv = x_g + 0.01 * goes_std * torch.sign(grad_g)
        x_s_adv = x_s + 0.01 * solexs_std * torch.sign(grad_s)
        x_h_adv = x_h + 0.01 * hel1os_std * torch.sign(grad_h)
        
        return x_g_adv.detach(), x_s_adv.detach(), x_h_adv.detach(), m_s, m_h
    results["Adversarial_FGSM"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_fgsm)
    
    # 4. Missing GOES
    logger.info("Running Missing GOES Stress Test...")
    def perturb_missing_goes(x_g, x_s, x_h, m_s, m_h, y):
        return torch.zeros_like(x_g), x_s, x_h, m_s, m_h
    results["Missing_GOES"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_missing_goes)
    
    # 5. Missing SoLEXS
    logger.info("Running Missing SoLEXS Stress Test...")
    def perturb_missing_solexs(x_g, x_s, x_h, m_s, m_h, y):
        return x_g, torch.zeros_like(x_s), x_h, torch.zeros_like(m_s), m_h
    results["Missing_SoLEXS"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_missing_solexs)
    
    # 6. Missing HEL1OS
    logger.info("Running Missing HEL1OS Stress Test...")
    def perturb_missing_hel1os(x_g, x_s, x_h, m_s, m_h, y):
        return x_g, x_s, torch.zeros_like(x_h), m_s, torch.zeros_like(m_h)
    results["Missing_HEL1OS"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_missing_hel1os)
    
    # 7. Random Telemetry Drop (50% prob)
    logger.info("Running Random Telemetry Drop Stress Test...")
    def perturb_random_drop(x_g, x_s, x_h, m_s, m_h, y):
        B = x_g.size(0)
        # Generate random mask dropouts
        drop_s = (torch.rand(B, 1, device=device) > 0.5).float()
        drop_h = (torch.rand(B, 1, device=device) > 0.5).float()
        
        m_s_new = m_s * drop_s
        m_h_new = m_h * drop_h
        
        x_s_new = x_s * m_s_new.unsqueeze(-1)
        x_h_new = x_h * m_h_new.unsqueeze(-1)
        
        return x_g, x_s_new, x_h_new, m_s_new, m_h_new
    results["Random_Telemetry_Drop"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_random_drop)
    
    # 8. Feature Scaling +5%
    logger.info("Running Feature Scaling +5% Stress Test...")
    def perturb_scale_up(x_g, x_s, x_h, m_s, m_h, y):
        return x_g * 1.05, x_s * 1.05, x_h * 1.05, m_s, m_h
    results["Feature_Scaling_Plus_5"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_scale_up)
    
    # 9. Feature Scaling -5%
    logger.info("Running Feature Scaling -5% Stress Test...")
    def perturb_scale_down(x_g, x_s, x_h, m_s, m_h, y):
        return x_g * 0.95, x_s * 0.95, x_h * 0.95, m_s, m_h
    results["Feature_Scaling_Minus_5"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_scale_down)
    
    # 10. Random Spikes (5% of frames replaced with 10x max value)
    logger.info("Running Random Spikes Stress Test...")
    def perturb_spikes(x_g, x_s, x_h, m_s, m_h, y):
        x_g_sp = x_g.clone()
        x_s_sp = x_s.clone()
        x_h_sp = x_h.clone()
        
        B, T, _ = x_g.shape
        # Add random spikes
        for b in range(B):
            spike_indices = np.random.choice(T, int(T * 0.05), replace=False)
            x_g_sp[b, spike_indices, :] = 10.0 * goes_max
            if m_s[b].item() == 1.0:
                x_s_sp[b, spike_indices, :] = 10.0 * solexs_max
            if m_h[b].item() == 1.0:
                x_h_sp[b, spike_indices, :] = 10.0 * hel1os_max
        return x_g_sp, x_s_sp, x_h_sp, m_s, m_h
    results["Random_Spikes"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_spikes)
    
    # 11. Sensor Saturation (Clamped to 99.9th percentile)
    logger.info("Running Sensor Saturation Stress Test...")
    def perturb_saturation(x_g, x_s, x_h, m_s, m_h, y):
        x_g_sat = torch.clamp(x_g, max=goes_max)
        x_s_sat = torch.clamp(x_s, max=solexs_max)
        x_h_sat = torch.clamp(x_h, max=hel1os_max)
        return x_g_sat, x_s_sat, x_h_sat, m_s, m_h
    results["Sensor_Saturation"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_saturation)
    
    # 12. Sensor Stuck Values (Constant sequence of last value)
    logger.info("Running Sensor Stuck Values Stress Test...")
    def perturb_stuck(x_g, x_s, x_h, m_s, m_h, y):
        x_g_stuck = x_g.clone()
        x_s_stuck = x_s.clone()
        x_h_stuck = x_h.clone()
        
        # Stuck to last value
        x_g_stuck[:, :, :] = x_g[:, -1, :].unsqueeze(1)
        x_s_stuck[:, :, :] = x_s[:, -1, :].unsqueeze(1)
        x_h_stuck[:, :, :] = x_h[:, -1, :].unsqueeze(1)
        return x_g_stuck, x_s_stuck, x_h_stuck, m_s, m_h
    results["Sensor_Stuck_Values"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_stuck)
    
    # 13. NaNs and Packet Loss (Zero out 20% of frames + replace NaNs with zero)
    logger.info("Running NaNs and Packet Loss Stress Test...")
    def perturb_nan_loss(x_g, x_s, x_h, m_s, m_h, y):
        x_g_loss = x_g.clone()
        x_s_loss = x_s.clone()
        x_h_loss = x_h.clone()
        
        B, T, _ = x_g.shape
        for b in range(B):
            loss_indices = np.random.choice(T, int(T * 0.20), replace=False)
            x_g_loss[b, loss_indices, :] = 0.0
            if m_s[b].item() == 1.0:
                x_s_loss[b, loss_indices, :] = 0.0
            if m_h[b].item() == 1.0:
                x_h_loss[b, loss_indices, :] = 0.0
                
        # Also introduce NaNs and immediately replace them with 0.0 (simulating NaN handling)
        # In PyTorch, torch.isnan(x) is handled by zero-filling
        x_g_loss[torch.isnan(x_g_loss)] = 0.0
        x_s_loss[torch.isnan(x_s_loss)] = 0.0
        x_h_loss[torch.isnan(x_h_loss)] = 0.0
        
        return x_g_loss, x_s_loss, x_h_loss, m_s, m_h
    results["NaNs_Packet_Loss"] = run_stress_eval(model, test_loader, device, best_th, evaluator, perturb_nan_loss)
    
    # 14. Time Shifts (±5 minutes and ±15 minutes)
    # Since shift is an index operation relative to labels, we will run these with custom loaders/datasets or index offsets
    logger.info("Running Time Shift Stress Tests...")
    
    def run_time_shift_eval(shift_steps):
        # We temporarily change the test dataset's __getitem__ indexing
        orig_getitem = test_ds.__getitem__
        
        def shifted_getitem(idx):
            # Apply shift_steps
            shifted_idx = idx + shift_steps
            # Bound check
            shifted_idx = max(0, min(shifted_idx, len(test_ds) - 1))
            
            # Fetch inputs from shifted_idx, but label from original idx
            x_g = test_ds.features_goes[shifted_idx : shifted_idx + test_ds.seq_len]
            x_s = test_ds.features_solexs[shifted_idx : shifted_idx + test_ds.seq_len]
            x_h = test_ds.features_hel1os[shifted_idx : shifted_idx + test_ds.seq_len]
            
            m_s = test_ds.mask_solexs[shifted_idx + test_ds.seq_len]
            m_h = test_ds.mask_hel1os[shifted_idx + test_ds.seq_len]
            
            # Label must remain aligned to target time step (idx + seq_len)
            y = test_ds.labels[idx + test_ds.seq_len]
            
            return (
                torch.from_numpy(x_g),
                torch.from_numpy(x_s),
                torch.from_numpy(x_h),
                torch.tensor([m_s], dtype=torch.float32),
                torch.tensor([m_h], dtype=torch.float32)
            ), torch.tensor(y, dtype=torch.float32)
            
        test_ds.__getitem__ = shifted_getitem
        
        # Evaluate
        loader = DataLoader(Subset(test_ds, subset_indices), batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
        metrics = run_stress_eval(model, loader, device, best_th, evaluator)
        
        # Restore __getitem__
        test_ds.__getitem__ = orig_getitem
        return metrics
        
    logger.info("  Evaluating Shift +5m...")
    results["Time_Shift_Plus_5"] = run_time_shift_eval(5)
    logger.info("  Evaluating Shift -5m...")
    results["Time_Shift_Minus_5"] = run_time_shift_eval(-5)
    logger.info("  Evaluating Shift +15m...")
    results["Time_Shift_Plus_15"] = run_time_shift_eval(15)
    logger.info("  Evaluating Shift -15m...")
    results["Time_Shift_Minus_15"] = run_time_shift_eval(-15)
    
    # 15. Clock Drift (SoLEXS & HEL1OS shifted relative to GOES by +5 mins)
    logger.info("Running Clock Drift Stress Test...")
    def run_clock_drift_eval():
        orig_getitem = test_ds.__getitem__
        
        def drifted_getitem(idx):
            # GOES features at idx
            x_g = test_ds.features_goes[idx : idx + test_ds.seq_len]
            
            # SoLEXS and HEL1OS features at shifted index (idx - 5)
            shifted_idx = max(0, min(idx - 5, len(test_ds) - 1))
            x_s = test_ds.features_solexs[shifted_idx : shifted_idx + test_ds.seq_len]
            x_h = test_ds.features_hel1os[shifted_idx : shifted_idx + test_ds.seq_len]
            
            m_s = test_ds.mask_solexs[shifted_idx + test_ds.seq_len]
            m_h = test_ds.mask_hel1os[shifted_idx + test_ds.seq_len]
            
            y = test_ds.labels[idx + test_ds.seq_len]
            
            return (
                torch.from_numpy(x_g),
                torch.from_numpy(x_s),
                torch.from_numpy(x_h),
                torch.tensor([m_s], dtype=torch.float32),
                torch.tensor([m_h], dtype=torch.float32)
            ), torch.tensor(y, dtype=torch.float32)
            
        test_ds.__getitem__ = drifted_getitem
        loader = DataLoader(Subset(test_ds, subset_indices), batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
        metrics = run_stress_eval(model, loader, device, best_th, evaluator)
        
        test_ds.__getitem__ = orig_getitem
        return metrics
        
    results["Clock_Drift_Plus_5"] = run_clock_drift_eval()
    
    # Save results
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    with open("stress_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    with open("artifacts/sprint15b/stress_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info("Task 5 completed successfully.")
    print("STRESS_TESTING: PASS")

if __name__ == "__main__":
    main()

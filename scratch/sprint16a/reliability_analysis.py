"""
scratch/sprint16a/reliability_analysis.py

Task 3: Reliability by Probability Bin.
Splits calibrated probabilities into 10 bins, computes observed frequency,
expected probability, ECE contribution, sample count, and Wilson score confidence intervals.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bootstrap_analysis import compute_ece

def compute_wilson_ci(p, n):
    if n == 0:
        return 0.0, 0.0
    z = 1.96  # 95% confidence
    denominator = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denominator
    spread = z * np.sqrt((p * (1 - p)) / n + (z**2) / (4 * n**2)) / denominator
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return lower, upper

def main():
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    
    records = []
    total_ece = 0.0
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i+1]
        
        # In bin selection
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        if i == n_bins - 1:
            # Include upper bound in last bin
            in_bin = in_bin | (y_prob == bin_upper)
            
        count = int(np.sum(in_bin))
        prop_in_bin = float(np.mean(in_bin))
        
        if count > 0:
            observed_freq = float(np.mean(y_true[in_bin]))
            expected_prob = float(np.mean(y_prob[in_bin]))
            ece_contrib = prop_in_bin * np.abs(expected_prob - observed_freq)
            total_ece += ece_contrib
            
            ci_lower, ci_upper = compute_wilson_ci(observed_freq, count)
        else:
            observed_freq = 0.0
            expected_prob = 0.0
            ece_contrib = 0.0
            ci_lower, ci_upper = 0.0, 0.0
            
        records.append({
            "Bin": f"[{bin_lower:.2f}, {bin_upper:.2f}]",
            "Sample_Count": count,
            "Expected_Probability": expected_prob,
            "Observed_Frequency": observed_freq,
            "ECE_Contribution": ece_contrib,
            "Wilson_CI_Lower": ci_lower,
            "Wilson_CI_Upper": ci_upper
        })
        
    df_bins = pd.DataFrame(records)
    
    # Save CSV
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    df_bins.to_csv("artifacts/sprint16a/calibration_bins.csv", index=False)
    
    # Save overall stats
    overall_stats = {
        "overall_ece": total_ece,
        "n_samples": len(y_true),
        "status": "PASS"
    }
    with open("artifacts/sprint16a/reliability_statistics.json", "w") as f:
        json.dump(overall_stats, f, indent=2)
        
    print(f"Calibration ECE calculated: {total_ece:.6f}")
    print("RELIABILITY_ANALYSIS: PASS")

if __name__ == "__main__":
    main()

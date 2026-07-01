"""
scripts/analyze_attention_failures.py

Sprint 6 — Task D: Attention Audit

Loads:
    artifacts/backtest_window_predictions.csv
    artifacts/research/test.parquet
    artifacts/feature_columns.json
    artifacts/models/patchtst_best.pt

Slices:
    Deterministic sample of 100 TP, 100 FP, and 100 FN windows.
    Runs PatchTST attention map extraction.
    Computes:
      - attention_entropy
      - top_patch_share
      - top_1_pos (top patch position)
      - top_2_pos
      - top_3_pos
    Runs Mann-Whitney U and KS tests between groups.
    Saves to artifacts/attention_statistics.json.
"""

import os
import sys
import json
import logging
import torch
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, ks_2samp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST, extract_attention_maps
from app.services.ml.explainability import _aggregate_attention_maps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS_PATH = os.path.join("artifacts", "backtest_window_predictions.csv")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
OUTPUT_PATH = os.path.join("artifacts", "attention_statistics.json")

def get_summary_stats(series):
    if len(series) == 0:
        return {
            "mean": 0.0, "median": 0.0, "std": 0.0
        }
    return {
        "mean": float(np.mean(series)),
        "median": float(np.median(series)),
        "std": float(np.std(series)) if len(series) > 1 else 0.0
    }

def compute_mwu_rank_biserial(g1, g2):
    n1 = len(g1)
    n2 = len(g2)
    if n1 == 0 or n2 == 0:
        return 1.0, 0.0
    res = mannwhitneyu(g1, g2, alternative='two-sided')
    r = 1.0 - (2.0 * res.statistic) / (n1 * n2)
    return float(res.pvalue), float(r)

def compute_ks_test(g1, g2):
    n1 = len(g1)
    n2 = len(g2)
    if n1 == 0 or n2 == 0:
        return 1.0, 0.0
    res = ks_2samp(g1, g2)
    return float(res.pvalue), float(res.statistic)

def main():
    logger.info("Starting Attention Audit...")
    for p in [PREDICTIONS_PATH, TEST_PARQUET_PATH, FEATURE_COLS_PATH, MODEL_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing file: {p}")
            return

    # 1. Load predictions
    preds_df = pd.read_csv(PREDICTIONS_PATH)
    
    # Categorize groups under coincidence policy
    y_pred = preds_df["coincidence_alert_level"].isin(["YELLOW", "RED"])
    y_true = preds_df["true_label"]

    tp_all = preds_df[y_pred & (y_true == 1)]
    fp_all = preds_df[y_pred & (y_true == 0)]
    fn_all = preds_df[(~y_pred) & (y_true == 1)]

    logger.info(f"Available for sampling: TP={len(tp_all)}, FP={len(fp_all)}, FN={len(fn_all)}")

    # Deterministic sample of 100 from each group
    tp_sample = tp_all.sample(n=min(100, len(tp_all)), random_state=42).copy()
    fp_sample = fp_all.sample(n=min(100, len(fp_all)), random_state=42).copy()
    fn_sample = fn_all.sample(n=min(100, len(fn_all)), random_state=42).copy()

    # 2. Load feature columns and test parquet
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)
    
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=feature_cols)

    # 3. Load model
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()
    logger.info(f"Model loaded onto {device} for attention extraction")

    # 4. Extract attention weights for each group
    group_results = {}
    for name, df_sample in [("TP", tp_sample), ("FP", fp_sample), ("FN", fn_sample)]:
        logger.info(f"Processing attention maps for {name} sample...")
        entropies = []
        top_shares = []
        top_1_positions = []
        top_2_positions = []
        top_3_positions = []

        for idx, row in df_sample.iterrows():
            global_idx = int(row["global_idx"])
            # Slice features for the window: [360, 14]
            x_np = test_df.iloc[global_idx - 360 : global_idx].values.astype(np.float32)
            x_np = np.nan_to_num(x_np, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Convert to torch tensor: [1, 360, 14]
            x_t = torch.from_numpy(x_np).unsqueeze(0).to(device)
            
            # Extract maps
            attn_maps = extract_attention_maps(model, x_t)
            patch_importance = _aggregate_attention_maps(attn_maps)  # [44]

            # Compute entropy
            p = np.clip(patch_importance, 1e-12, 1.0)
            entropy = -np.sum(p * np.log(p))
            norm_entropy = float(entropy / np.log(len(p)))
            entropies.append(norm_entropy)

            # Top shares & positions
            top_shares.append(float(np.max(patch_importance)))
            sorted_indices = np.argsort(patch_importance)[::-1]
            top_1_positions.append(int(sorted_indices[0]))
            top_2_positions.append(int(sorted_indices[1]))
            top_3_positions.append(int(sorted_indices[2]))

        group_results[name] = {
            "entropy": entropies,
            "top_share": top_shares,
            "top_1_pos": top_1_positions,
            "top_2_pos": top_2_positions,
            "top_3_pos": top_3_positions
        }

    # 5. Compute summary statistics
    stats = {}
    for name in ["TP", "FP", "FN"]:
        stats[name] = {
            "entropy": get_summary_stats(group_results[name]["entropy"]),
            "top_share": get_summary_stats(group_results[name]["top_share"]),
            "top_1_pos": get_summary_stats(group_results[name]["top_1_pos"]),
            "top_2_pos": get_summary_stats(group_results[name]["top_2_pos"]),
            "top_3_pos": get_summary_stats(group_results[name]["top_3_pos"])
        }

    # 6. Run significance tests
    comparisons = {}
    for pair in [("FP", "TP"), ("FP", "FN"), ("FN", "TP")]:
        g1, g2 = pair
        pair_key = f"{g1}_vs_{g2}"
        comparisons[pair_key] = {}
        for metric in ["entropy", "top_share", "top_1_pos"]:
            v1 = group_results[g1][metric]
            v2 = group_results[g2][metric]
            mwu_p, mwu_r = compute_mwu_rank_biserial(v1, v2)
            ks_p, ks_d = compute_ks_test(v1, v2)
            comparisons[pair_key][metric] = {
                "mwu_pvalue": mwu_p,
                "mwu_effect_size": mwu_r,
                "ks_pvalue": ks_p,
                "ks_statistic": ks_d
            }

    # 7. Save report
    final_report = {
        "sample_sizes": {
            "TP": len(tp_sample),
            "FP": len(fp_sample),
            "FN": len(fn_sample)
        },
        "summary_statistics": stats,
        "significance_tests": comparisons
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(final_report, fh, indent=2)
    logger.info(f"Saved Attention Audit results → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

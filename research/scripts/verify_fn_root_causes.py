"""
scripts/verify_fn_root_causes.py

Sprint 7 — Task B: FN Root Causes Verification

Loads:
    artifacts/backtest_window_predictions.csv
    artifacts/research/test.parquet
    artifacts/research/flares_full.parquet
    artifacts/models/patchtst_best.pt

Computes for every nowcast window:
    - minutes_since_last_flare
    - long_flux
    - short_flux
    - attention_entropy
    - top_attention_share
    - peak_flux_last_24h
    - flare_density_last_24h

Groups:
    FN vs TP
    FN vs TN
under the coincidence policy.

Performs:
    - Mann-Whitney U test (p-value)
    - Kolmogorov-Smirnov test (p-value, KS statistic)
    - Rank Biserial Correlation (effect size)

Saves:
    artifacts/fn_root_cause_verification.json
"""

import os
import sys
import json
import logging
import torch
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, ks_2samp

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS_PATH = os.path.join("artifacts", "backtest_window_predictions.csv")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
FLARES_PARQUET_PATH = os.path.join("artifacts", "research", "flares_full.parquet")
MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH = os.path.join("artifacts", "fn_root_cause_verification.json")


def get_summary_stats(series):
    if len(series) == 0:
        return {"count": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "p25": 0.0, "p75": 0.0}
    return {
        "count": int(len(series)),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()) if len(series) > 1 else 0.0,
        "p25": float(series.quantile(0.25)),
        "p75": float(series.quantile(0.75))
    }


def compute_mwu_rank_biserial(g1, g2):
    n1 = len(g1)
    n2 = len(g2)
    if n1 == 0 or n2 == 0:
        return 1.0, 0.0
    res = mannwhitneyu(g1, g2, alternative='two-sided')
    # Rank-biserial correlation: r = 1 - 2*U / (n1*n2)
    r = 1.0 - (2.0 * res.statistic) / (n1 * n2)
    return float(res.pvalue), float(r)


def compute_ks_test(g1, g2):
    n1 = len(g1)
    n2 = len(g2)
    if n1 == 0 or n2 == 0:
        return 1.0, 0.0
    res = ks_2samp(g1, g2)
    return float(res.pvalue), float(res.statistic)


@torch.no_grad()
def compute_batched_attention_metrics(model, X_batch, device):
    """Compute normalized entropy and top attention share in batches."""
    model.eval()
    X_tensor = torch.from_numpy(X_batch).to(device)
    _, attn_maps = model.forward_with_attention(X_tensor)
    
    layer_vectors = []
    for layer_attn in attn_maps:
        attn_np = layer_attn.cpu().numpy()  # [B, n_heads, 45, 45]
        head_avg = attn_np.mean(axis=1)      # [B, 45, 45]
        cls_row = head_avg[:, 0, :]         # [B, 45]
        patch_attn = cls_row[:, 1:]         # [B, 44]
        layer_vectors.append(patch_attn)
        
    mean_attn = np.mean(layer_vectors, axis=0)  # [B, 44]
    
    # Normalise
    total = mean_attn.sum(axis=1, keepdims=True)
    mean_attn = np.where(total > 1e-9, mean_attn / total, mean_attn)
    
    # Entropy
    p = np.clip(mean_attn, 1e-12, 1.0)
    entropy = -np.sum(p * np.log(p), axis=1)  # [B]
    norm_entropy = entropy / np.log(44)       # [B]
    
    # Top share
    top_share = np.max(mean_attn, axis=1)      # [B]
    
    return norm_entropy, top_share


def main():
    logger.info("Starting FN Root Cause Verification...")
    for p in [PREDICTIONS_PATH, TEST_PARQUET_PATH, FLARES_PARQUET_PATH, MODEL_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing file: {p}")
            return

    # 1. Load predictions
    preds_df = pd.read_csv(PREDICTIONS_PATH)
    
    # 2. Load feature columns and test parquet
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    logger.info("Loading test parquet...")
    load_cols = ["timestamp", "long_flux", "short_flux", "minutes_since_last_flare"] + feature_cols
    load_cols = list(dict.fromkeys(load_cols))
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)

    # 3. Load flares catalog for density calculation
    logger.info("Loading flares catalog...")
    flares_df = pd.read_parquet(FLARES_PARQUET_PATH)
    
    # 4. Compute vectorized features (peak_flux and flare_density)
    logger.info("Computing peak flux in last 24h...")
    test_df["peak_flux_last_24h"] = test_df["long_flux"].rolling(window=1440, min_periods=1).max()
    test_df["peak_flux_last_24h"] = test_df["peak_flux_last_24h"].fillna(0.0)

    logger.info("Computing flare density in last 24h...")
    flare_times_numeric = pd.to_datetime(flares_df["start_time"]).values.astype(np.int64) // 10**9
    flare_times_numeric.sort()

    t_numeric = pd.to_datetime(test_df["timestamp"]).values.astype(np.int64) // 10**9
    idx_right = np.searchsorted(flare_times_numeric, t_numeric, side='right')
    idx_left = np.searchsorted(flare_times_numeric, t_numeric - 86400, side='left')
    test_df["flare_density_last_24h"] = idx_right - idx_left

    # 5. Extract attention maps for all windows in the predictions backtest
    logger.info("Loading PatchTST model for batched attention extraction...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    logger.info("Slicing time-series features for nowcast windows...")
    features_array = test_df[feature_cols].values.astype(np.float32)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    nowcast_indices = preds_df["global_idx"].values
    X_all = np.stack([features_array[idx - 360 : idx] for idx in nowcast_indices])

    logger.info(f"Running batched attention calculations on {device}...")
    batch_size = 512
    all_entropies = []
    all_top_shares = []

    for start in range(0, len(X_all), batch_size):
        end = min(len(X_all), start + batch_size)
        X_b = X_all[start:end]
        entropies, top_shares = compute_batched_attention_metrics(model, X_b, device)
        all_entropies.append(entropies)
        all_top_shares.append(top_shares)

    all_entropies = np.concatenate(all_entropies)
    all_top_shares = np.concatenate(all_top_shares)
    logger.info("Attention calculations complete.")

    # Align features with nowcast timestamps (global_idx - 1)
    aligned_df = test_df.iloc[nowcast_indices - 1].copy().reset_index(drop=True)
    aligned_df["true_label"] = preds_df["true_label"].values
    aligned_df["coincidence_alert_level"] = preds_df["coincidence_alert_level"].values
    aligned_df["attention_entropy"] = all_entropies
    aligned_df["top_attention_share"] = all_top_shares

    # 6. Group data
    y_pred = aligned_df["coincidence_alert_level"].isin(["YELLOW", "RED"])
    y_true = aligned_df["true_label"]

    tp_df = aligned_df[y_pred & (y_true == 1)]
    fn_df = aligned_df[(~y_pred) & (y_true == 1)]
    tn_df = aligned_df[(~y_pred) & (y_true == 0)]

    logger.info(f"Groups identified: TP={len(tp_df)}, FN={len(fn_df)}, TN={len(tn_df)}")

    metrics_list = [
        "minutes_since_last_flare",
        "long_flux",
        "short_flux",
        "attention_entropy",
        "top_attention_share",
        "peak_flux_last_24h",
        "flare_density_last_24h"
    ]

    feature_stats = {}
    for col in metrics_list:
        tp_series = tp_df[col]
        fn_series = fn_df[col]
        tn_series = tn_df[col]

        summary = {
            "TP": get_summary_stats(tp_series),
            "FN": get_summary_stats(fn_series),
            "TN": get_summary_stats(tn_series)
        }

        mwu_p_tp, mwu_r_tp = compute_mwu_rank_biserial(fn_series, tp_series)
        ks_p_tp, ks_d_tp = compute_ks_test(fn_series, tp_series)

        mwu_p_tn, mwu_r_tn = compute_mwu_rank_biserial(fn_series, tn_series)
        ks_p_tn, ks_d_tn = compute_ks_test(fn_series, tn_series)

        feature_stats[col] = {
            "summary": summary,
            "tests": {
                "FN_vs_TP": {
                    "mwu_pvalue": mwu_p_tp,
                    "mwu_effect_size": mwu_r_tp,
                    "ks_pvalue": ks_p_tp,
                    "ks_statistic": ks_d_tp
                },
                "FN_vs_TN": {
                    "mwu_pvalue": mwu_p_tn,
                    "mwu_effect_size": mwu_r_tn,
                    "ks_pvalue": ks_p_tn,
                    "ks_statistic": ks_d_tn
                }
            }
        }

    report = {
        "sample_sizes": {
            "TP": len(tp_df),
            "FN": len(fn_df),
            "TN": len(tn_df)
        },
        "feature_statistics": feature_stats
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)
    logger.info(f"Saved FN root cause verification results → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

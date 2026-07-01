"""
scripts/analyze_false_positives.py

Sprint 6 — Task B: False Positive Analysis

Loads:
    artifacts/backtest_window_predictions.csv
    artifacts/research/test.parquet
    artifacts/feature_columns.json

Categorizes windows under coincidence policy:
    TP: true_label == 1 & y_pred == 1
    FP: true_label == 0 & y_pred == 1
    TN: true_label == 0 & y_pred == 0
where y_pred = coincidence_alert_level in ["YELLOW", "RED"].

Computes feature summary statistics and runs Mann-Whitney U and KS tests (FP vs TP, FP vs TN).
Profiles predicted probability (cal_prob) distribution for TP, FP, TN.
Saves to artifacts/fp_statistics.json.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, ks_2samp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS_PATH = os.path.join("artifacts", "backtest_window_predictions.csv")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH = os.path.join("artifacts", "fp_statistics.json")

def get_summary_stats(series):
    if len(series) == 0:
        return {
            "count": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "p25": 0.0, "p75": 0.0
        }
    return {
        "count": int(len(series)),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()) if len(series) > 1 else 0.0,
        "p25": float(series.quantile(0.25)),
        "p75": float(series.quantile(0.75))
    }

def get_prob_distribution(series):
    if len(series) == 0:
        return {
            "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0,
            "p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0, "max": 0.0
        }
    return {
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()) if len(series) > 1 else 0.0,
        "min": float(series.min()),
        "p10": float(series.quantile(0.10)),
        "p25": float(series.quantile(0.25)),
        "p50": float(series.quantile(0.50)),
        "p75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.90)),
        "max": float(series.max())
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

def main():
    logger.info("Starting False Positive Analysis...")
    for p in [PREDICTIONS_PATH, TEST_PARQUET_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing file: {p}")
            return

    # 1. Load data
    logger.info(f"Loading predictions from {PREDICTIONS_PATH}")
    preds_df = pd.read_csv(PREDICTIONS_PATH)
    
    logger.info(f"Loading feature columns from {FEATURE_COLS_PATH}")
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    logger.info(f"Loading test parquet from {TEST_PARQUET_PATH}")
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=["timestamp"] + feature_cols)
    
    # 2. Extract features at nowcast timestamps (global_idx - 1)
    logger.info("Aligning predictions with features...")
    nowcast_indices = preds_df["global_idx"].values - 1
    aligned_features = test_df.iloc[nowcast_indices].copy().reset_index(drop=True)
    
    # Add predictions columns to the aligned features dataframe
    aligned_features["true_label"] = preds_df["true_label"].values
    aligned_features["coincidence_alert_level"] = preds_df["coincidence_alert_level"].values
    aligned_features["cal_prob"] = preds_df["cal_prob"].values

    # 3. Categorize groups
    y_pred = aligned_features["coincidence_alert_level"].isin(["YELLOW", "RED"])
    y_true = aligned_features["true_label"]

    tp_df = aligned_features[y_pred & (y_true == 1)]
    fp_df = aligned_features[y_pred & (y_true == 0)]
    tn_df = aligned_features[(~y_pred) & (y_true == 0)]

    logger.info(f"Group sizes: TP={len(tp_df)}, FP={len(fp_df)}, TN={len(tn_df)}")

    # 4. Feature summary statistics and significance tests
    feature_stats = {}
    for col in feature_cols:
        tp_series = tp_df[col]
        fp_series = fp_df[col]
        tn_series = tn_df[col]

        # Summary stats
        summary = {
            "TP": get_summary_stats(tp_series),
            "FP": get_summary_stats(fp_series),
            "TN": get_summary_stats(tn_series)
        }

        # Significance tests
        mwu_p_tp, mwu_r_tp = compute_mwu_rank_biserial(fp_series, tp_series)
        ks_p_tp, ks_d_tp = compute_ks_test(fp_series, tp_series)

        mwu_p_tn, mwu_r_tn = compute_mwu_rank_biserial(fp_series, tn_series)
        ks_p_tn, ks_d_tn = compute_ks_test(fp_series, tn_series)

        feature_stats[col] = {
            "summary": summary,
            "tests": {
                "FP_vs_TP": {
                    "mwu_pvalue": mwu_p_tp,
                    "mwu_effect_size": mwu_r_tp,
                    "ks_pvalue": ks_p_tp,
                    "ks_statistic": ks_d_tp
                },
                "FP_vs_TN": {
                    "mwu_pvalue": mwu_p_tn,
                    "mwu_effect_size": mwu_r_tn,
                    "ks_pvalue": ks_p_tn,
                    "ks_statistic": ks_d_tn
                }
            }
        }

    # 5. Calibration distribution by group
    cal_dist = {
        "TP": get_prob_distribution(tp_df["cal_prob"]),
        "FP": get_prob_distribution(fp_df["cal_prob"]),
        "TN": get_prob_distribution(tn_df["cal_prob"])
    }

    # 6. Save report
    report = {
        "group_sizes": {
            "TP": len(tp_df),
            "FP": len(fp_df),
            "TN": len(tn_df)
        },
        "feature_statistics": feature_stats,
        "calibration_by_error_type": cal_dist
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)
    logger.info(f"Saved False Positive analysis results → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

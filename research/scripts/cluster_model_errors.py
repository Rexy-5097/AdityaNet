"""
scripts/cluster_model_errors.py

Sprint 6 — Task E: Error Clustering

Loads:
    artifacts/backtest_window_predictions.csv
    artifacts/research/test.parquet
    artifacts/feature_columns.json

Extracts:
    14 features of the error windows (FP + FN) under the coincidence policy.
    FP: true_label == 0 & y_pred == 1
    FN: true_label == 1 & y_pred == 0

Performs:
    Standardization of features.
    KMeans clustering sweep (K from 2 to 8), selecting optimal K via Silhouette Score.
    Profiles the optimal clusters: sample count, mean probability, flare rate, feature means.

Saves:
    artifacts/error_clusters.json
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS_PATH = os.path.join("artifacts", "backtest_window_predictions.csv")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH = os.path.join("artifacts", "error_clusters.json")

def main():
    logger.info("Starting Error Clustering...")
    for p in [PREDICTIONS_PATH, TEST_PARQUET_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing file: {p}")
            return

    # 1. Load predictions
    preds_df = pd.read_csv(PREDICTIONS_PATH)
    
    # 2. Load feature columns and test parquet
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)
    
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=feature_cols)

    # 3. Align features
    nowcast_indices = preds_df["global_idx"].values - 1
    aligned_features = test_df.iloc[nowcast_indices].copy().reset_index(drop=True)
    aligned_features["true_label"] = preds_df["true_label"].values
    aligned_features["coincidence_alert_level"] = preds_df["coincidence_alert_level"].values
    aligned_features["cal_prob"] = preds_df["cal_prob"].values

    # 4. Identify errors
    y_pred = aligned_features["coincidence_alert_level"].isin(["YELLOW", "RED"])
    y_true = aligned_features["true_label"]

    fp_mask = y_pred & (y_true == 0)
    fn_mask = (~y_pred) & (y_true == 1)
    
    errors_df = aligned_features[fp_mask | fn_mask].copy().reset_index(drop=True)
    
    logger.info(f"Total error windows found: {len(errors_df)} (FP={fp_mask.sum()}, FN={fn_mask.sum()})")
    
    if len(errors_df) < 10:
        logger.warning("Too few errors to cluster. Writing empty report.")
        with open(OUTPUT_PATH, "w") as fh:
            json.dump({"error": "Insufficient errors for clustering"}, fh, indent=2)
        return

    # 5. Scale features
    X = errors_df[feature_cols].values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 6. KMeans sweep K from 2 to 8
    scores = {}
    best_k = 2
    best_score = -1.0
    
    # If the dataset is extremely large, we can take a subsample for silhouette score to be fast.
    # The number of errors is about 7872 + 1946 = 9818, which is small enough for silhouette score on a CPU/MPS in seconds.
    logger.info("Sweeping cluster sizes K = 2..8...")
    for k in range(2, 9):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = float(silhouette_score(X_scaled, labels))
        scores[str(k)] = score
        logger.info(f"K={k} | Silhouette Score: {score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k

    logger.info(f"Optimal cluster count K={best_k} (score={best_score:.4f})")

    # 7. Profile optimal clusters
    kmeans_optimal = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = kmeans_optimal.fit_predict(X_scaled)
    errors_df["cluster"] = cluster_labels

    cluster_profiles = []
    for c in range(best_k):
        c_df = errors_df[errors_df["cluster"] == c]
        
        feature_means = {}
        for col in feature_cols:
            feature_means[col] = float(c_df[col].mean())
            
        profile = {
            "cluster_id": int(c),
            "sample_count": int(len(c_df)),
            "mean_probability": float(c_df["cal_prob"].mean()),
            "flare_rate": float(c_df["true_label"].mean()),
            "feature_means": feature_means
        }
        cluster_profiles.append(profile)

    # 8. Save report
    report = {
        "optimal_k": best_k,
        "silhouette_scores": scores,
        "cluster_profiles": cluster_profiles
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)
    logger.info(f"Saved Error Clustering results → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

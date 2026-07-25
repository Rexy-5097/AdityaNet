import asyncio
import json
import logging
import os
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset_builder import DatasetBuilder
from app.services.ml.metrics import compute_metrics

# Simple formatting for script console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    print("==================================================")
    print("SuryaNet ML Baseline Training Script")
    print("==================================================")

    # 1. Build and export the canonical dataset
    builder = DatasetBuilder()
    X, y_binary, y_class = await builder.build_and_export_dataset()

    N = len(X)
    if N < 10:
        logger.error(f"Insufficient data points ({N}) to train model. Run ingestion first.")
        return

    # 2. Temporal train-test split (oldest 80% train, newest 20% test)
    split_idx = int(N * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y_binary.iloc[:split_idx], y_binary.iloc[split_idx:]
    y_class_train, y_class_test = y_class.iloc[:split_idx], y_class.iloc[split_idx:]

    train_start, train_end = X.index[0], X.index[split_idx - 1]
    test_start, test_end = X.index[split_idx], X.index[-1]

    # Print Dataset Statistics
    print("\n--- Dataset Statistics ---")
    print(f"Total Samples: {N}")
    print(f"Train samples: {len(X_train)} ({train_start} to {train_end})")
    print(f"Test samples:  {len(X_test)} ({test_start} to {test_end})")
    
    print("\n--- Class Distribution (Binary) ---")
    print(f"Train - Neg (No Flare): {np.sum(y_train == 0)}, Pos (M/X Flare): {np.sum(y_train == 1)}")
    print(f"Test  - Neg (No Flare): {np.sum(y_test == 0)}, Pos (M/X Flare): {np.sum(y_test == 1)}")

    print("\n--- Class Distribution (Multiclass Target) ---")
    print(f"Train - Class 0 (None): {np.sum(y_class_train == 0)}, Class 1 (M): {np.sum(y_class_train == 1)}, Class 2 (X): {np.sum(y_class_train == 2)}")
    print(f"Test  - Class 0 (None): {np.sum(y_class_test == 0)}, Class 1 (M): {np.sum(y_class_test == 1)}, Class 2 (X): {np.sum(y_class_test == 2)}")

    # 3. Persistence Baseline Evaluation
    # Rule: Predict positive (1) if an M/X flare occurred in the previous 6 hours.
    # The feature 'minutes_since_last_flare' <= 360 is the exact mapping of this rule.
    y_pred_persistence = (X_test["minutes_since_last_flare"] <= 360.0).astype(int).values
    pers_metrics = compute_metrics(y_test.values, y_pred_persistence)

    # 4. Logistic Regression Evaluation
    # Fit standardizer on train features and scale both
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Logistic Regression model with balanced class weighting
    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    lr_metrics = compute_metrics(y_test.values, y_pred_lr)

    # 5. Calculate relative TSS improvement
    pers_tss = pers_metrics["tss"]
    lr_tss = lr_metrics["tss"]
    if pers_tss > 0:
        improvement = ((lr_tss - pers_tss) / pers_tss) * 100.0
        improvement_str = f"{improvement:+.2f}%"
    else:
        improvement = 0.0
        improvement_str = "N/A"

    # Print Metrics Summary
    print("\n" + "=" * 50)
    print("BASELINE PERFORMANCE METRICS")
    print("=" * 50)
    
    print("\n[Persistence Baseline]")
    print(f"Confusion Matrix: TP={pers_metrics['confusion_matrix']['tp']}, FP={pers_metrics['confusion_matrix']['fp']}, FN={pers_metrics['confusion_matrix']['fn']}, TN={pers_metrics['confusion_matrix']['tn']}")
    print(f"TSS:       {pers_metrics['tss']:.4f}")
    print(f"POD:       {pers_metrics['pod']:.4f}")
    print(f"POFD:      {pers_metrics['pofd']:.4f}")
    print(f"FAR:       {pers_metrics['far']:.4f}")
    print(f"Precision: {pers_metrics['precision']:.4f}")
    print(f"Recall:    {pers_metrics['recall']:.4f}")
    print(f"F1:        {pers_metrics['f1']:.4f}")

    print("\n[Balanced Logistic Regression]")
    print(f"Confusion Matrix: TP={lr_metrics['confusion_matrix']['tp']}, FP={lr_metrics['confusion_matrix']['fp']}, FN={lr_metrics['confusion_matrix']['fn']}, TN={lr_metrics['confusion_matrix']['tn']}")
    print(f"TSS:       {lr_metrics['tss']:.4f}")
    print(f"POD:       {lr_metrics['pod']:.4f}")
    print(f"POFD:      {lr_metrics['pofd']:.4f}")
    print(f"FAR:       {lr_metrics['far']:.4f}")
    print(f"Precision: {lr_metrics['precision']:.4f}")
    print(f"Recall:    {lr_metrics['recall']:.4f}")
    print(f"F1:        {lr_metrics['f1']:.4f}")

    print("\n" + "-" * 50)
    print(f"True Skill Score (TSS) Improvement: {improvement_str}")
    print("-" * 50)

    # 6. Save baseline metrics report
    metrics_path = "artifacts/baseline_metrics.json"
    baseline_metrics = {
        "persistence": pers_metrics,
        "logistic_regression": lr_metrics,
        "tss_improvement_percent": improvement
    }
    
    logger.info(f"Saving baseline metrics json to {metrics_path}...")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=2)

    print("==================================================")
    print("ML Baseline Training Complete.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())

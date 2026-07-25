"""
scripts/generate_explainability_examples.py

Sprint 5.6 — Task G: Explainability Verification

Generates artifacts/explainability_examples.json for 20 predictions.

For each prediction stores:
    timestamp
    top_attention_patch (patch_index, attention_share)
    alert_level
    calibrated_probability
    true_label

Selection:
    10 windows where true_label == 1 (flare)
    10 windows where true_label == 0 (no flare)
    drawn sequentially from test.parquet, stride=60.

No interpretation. No conclusions.
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST, extract_attention_maps
from app.services.ml.explainability import get_top_attention_patches, _aggregate_attention_maps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
TEST_PARQUET_PATH  = os.path.join("artifacts", "research", "test.parquet")
MODEL_PATH         = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH    = os.path.join("artifacts", "calibrator.pkl")
THRESHOLDS_PATH    = os.path.join("artifacts", "operator_thresholds_validation_only.json")
FEATURE_COLS_PATH  = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH        = os.path.join("artifacts", "explainability_examples.json")

N_EXAMPLES_PER_CLASS = 10   # 10 flare + 10 no-flare = 20 total


def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.6 — Task G: Explainability Examples")
    print("=" * 60)

    for p in [TEST_PARQUET_PATH, MODEL_PATH, CALIBRATOR_PATH,
              THRESHOLDS_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing: {p}")
            sys.exit(1)

    # Load configuration
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    with open(THRESHOLDS_PATH, "r") as fh:
        td = json.load(fh)
    yellow_threshold = float(td["yellow_threshold"])
    red_threshold    = float(td["red_threshold"])

    with open(CALIBRATOR_PATH, "rb") as fh:
        calibrator = pickle.load(fh)

    # Load model (eval mode, no dropout)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()
    logger.info(f"Model loaded onto {device}")

    # Load test data (need timestamp + long_flux for physical context)
    load_cols = list(dict.fromkeys(
        ["timestamp", "long_flux", "target_6hr_binary"] + feature_cols
    ))
    logger.info(f"Loading test split: {TEST_PARQUET_PATH}")
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    test_df = test_df.fillna(0.0)
    total_len = len(test_df)
    logger.info(f"Test rows: {total_len:,}")

    features_array = test_df[feature_cols].values.astype(np.float32)

    # Build candidate windows at stride=60 starting from index 360
    stride     = 60
    seq_len    = 360
    candidates = []
    for i in range(seq_len, total_len, stride):
        label = int(test_df.iloc[i]["target_6hr_binary"])
        candidates.append((i, label))

    # Split by class
    pos_cands = [(i, l) for i, l in candidates if l == 1]
    neg_cands = [(i, l) for i, l in candidates if l == 0]
    logger.info(f"Candidate windows: {len(pos_cands)} positive, {len(neg_cands)} negative")

    # Select first N_EXAMPLES_PER_CLASS from each class
    selected = (
        pos_cands[:N_EXAMPLES_PER_CLASS]
        + neg_cands[:N_EXAMPLES_PER_CLASS]
    )
    selected.sort(key=lambda t: t[0])   # sort by time
    logger.info(f"Selected {len(selected)} windows for explainability")

    # Process each window
    examples = []

    for global_idx, true_label in selected:
        # Input window
        x_np  = features_array[global_idx - seq_len : global_idx]  # [360, n_feat]
        x_t   = torch.from_numpy(x_np).unsqueeze(0).to(device)     # [1, 360, n_feat]

        # DataFrame slice for physical context
        df_slice = test_df.iloc[global_idx - seq_len : global_idx].reset_index(drop=True)
        ts_end   = str(test_df.iloc[global_idx]["timestamp"])

        # Deterministic inference + attention extraction
        with torch.no_grad():
            logit = model(x_t)
            raw_prob = float(torch.sigmoid(logit).squeeze().cpu())
            attn_maps = extract_attention_maps(model, x_t)

        cal_prob = float(calibrator(np.array([raw_prob]))[0])

        # Determine alert level
        if cal_prob < yellow_threshold:
            alert_level = "GREEN"
        elif cal_prob < red_threshold:
            alert_level = "YELLOW"
        else:
            alert_level = "RED"

        # Extract top attention patch only
        patch_importance = _aggregate_attention_maps(attn_maps)  # [44]
        top_idx   = int(np.argmax(patch_importance))
        top_share = float(patch_importance[top_idx])

        # Timestamp of top patch centre
        STRIDE    = 8
        PATCH_LEN = 16
        center    = min(top_idx * STRIDE + (PATCH_LEN // 2), len(df_slice) - 1)
        patch_ts  = str(df_slice["timestamp"].iloc[center])

        examples.append({
            "window_end_timestamp":   ts_end,
            "global_row_index":       int(global_idx),
            "true_label":             int(true_label),
            "raw_probability":        round(raw_prob, 8),
            "calibrated_probability": round(cal_prob,  8),
            "alert_level":            alert_level,
            "top_attention_patch": {
                "patch_index":     top_idx,
                "timestamp":       patch_ts,
                "attention_share": round(top_share, 8),
            },
        })

        logger.info(
            f"idx={global_idx} label={true_label} "
            f"cal_prob={cal_prob:.4f} alert={alert_level} "
            f"top_patch={top_idx} attn={top_share:.4f}"
        )

    # Save
    output = {
        "n_examples":              len(examples),
        "n_examples_label_1":      sum(1 for e in examples if e["true_label"] == 1),
        "n_examples_label_0":      sum(1 for e in examples if e["true_label"] == 0),
        "thresholds_source":       THRESHOLDS_PATH,
        "yellow_threshold_used":   yellow_threshold,
        "red_threshold_used":      red_threshold,
        "calibrator_method":       calibrator.method,
        "examples":                examples,
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"\nSaved {len(examples)} examples → {OUTPUT_PATH}")
    print(f"\n{'#':<4} {'Label':>5} {'RawP':>8} {'CalP':>8} {'Alert':>7} {'TopPatch':>9} {'AttnShare':>10} {'PatchTS'}")
    for i, ex in enumerate(examples, 1):
        print(
            f"{i:<4} {ex['true_label']:>5} "
            f"{ex['raw_probability']:>8.4f} {ex['calibrated_probability']:>8.4f} "
            f"{ex['alert_level']:>7} {ex['top_attention_patch']['patch_index']:>9} "
            f"{ex['top_attention_patch']['attention_share']:>10.4f} "
            f"{ex['top_attention_patch']['timestamp']}"
        )


if __name__ == "__main__":
    main()

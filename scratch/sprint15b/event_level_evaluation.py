"""
scratch/sprint15b/event_level_evaluation.py

Task 1: Event Level Evaluation.
Computes event-level Recall, Precision, FAR, and Lead Times (mean, median, max).
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders, evaluate_simple, get_calibrators_and_threshold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def find_contiguous_segments(labels):
    segments = []
    in_segment = False
    start_idx = None
    for idx, val in enumerate(labels):
        if val == 1 and not in_segment:
            in_segment = True
            start_idx = idx
        elif val == 0 and in_segment:
            segments.append((start_idx, idx - 1))
            in_segment = False
    if in_segment:
        segments.append((start_idx, len(labels) - 1))
    return segments

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    val_loader, test_loader = get_loaders(val_ds, test_ds)
    
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    logger.info(f"Optimal Threshold: {best_th}")

    logger.info("Evaluating on test dataset...")
    test_probs, test_targets, _, _ = evaluate_simple(model, test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    
    preds = (cal_probs >= best_th).astype(int)
    
    # Event-level grouping
    actual_events = find_contiguous_segments(test_targets)
    predicted_episodes = find_contiguous_segments(preds)
    
    logger.info(f"Total Actual Events: {len(actual_events)}")
    logger.info(f"Total Predicted Episodes: {len(predicted_episodes)}")
    
    # Calculate Event Recall and Lead Times
    caught_count = 0
    lead_times_min = []
    
    for S, E in actual_events:
        # Check if there is any positive prediction in [S, E]
        event_preds = preds[S : E + 1]
        if np.any(event_preds == 1):
            caught_count += 1
            # First alert within the event window
            first_alert_local = np.where(event_preds == 1)[0][0]
            first_alert_global = S + first_alert_local
            # Lead time: (Event Start + 6 hours) - Alert Time
            # S is the first window where lookahead includes the flare, meaning the flare starts at S + 360
            lead_time = (S + 360) - first_alert_global
            lead_times_min.append(lead_time)
            
    # Calculate Event Precision and FAR
    tp_episodes = 0
    fp_episodes = 0
    
    for s, e in predicted_episodes:
        # Check if the episode overlaps with any true positive window
        episode_targets = test_targets[s : e + 1]
        if np.any(episode_targets == 1):
            tp_episodes += 1
        else:
            fp_episodes += 1
            
    event_recall = caught_count / len(actual_events) if len(actual_events) > 0 else 0.0
    event_precision = tp_episodes / len(predicted_episodes) if len(predicted_episodes) > 0 else 0.0
    event_far = fp_episodes / len(predicted_episodes) if len(predicted_episodes) > 0 else 0.0
    
    lead_times_hrs = [lt / 60.0 for lt in lead_times_min]
    
    mean_lt = float(np.mean(lead_times_hrs)) if lead_times_hrs else 0.0
    median_lt = float(np.median(lead_times_hrs)) if lead_times_hrs else 0.0
    max_lt = float(np.max(lead_times_hrs)) if lead_times_hrs else 0.0
    
    metrics = {
        "event_recall": event_recall,
        "event_precision": event_precision,
        "event_far": event_far,
        "mean_detection_lead_time_hrs": mean_lt,
        "median_detection_lead_time_hrs": median_lt,
        "maximum_lead_time_hrs": max_lt,
        "n_actual_events": len(actual_events),
        "n_caught_events": caught_count,
        "n_predicted_episodes": len(predicted_episodes),
        "n_tp_episodes": tp_episodes,
        "n_fp_episodes": fp_episodes
    }
    
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    with open("artifacts/sprint15b/event_level_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    logger.info("Task 1 completed successfully.")
    print("EVENT_LEVEL_EVALUATION: PASS")

if __name__ == "__main__":
    main()

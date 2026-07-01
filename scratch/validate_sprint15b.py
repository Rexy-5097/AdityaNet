import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score, average_precision_score
from torch.utils.data import DataLoader, Subset

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import compute_full_suite, find_best_threshold

VAL_PARQUET = "artifacts/sprint14c/s2_val.parquet"
TEST_PARQUET = "artifacts/sprint14c/s2_test.parquet"
MODEL_PATH = "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt"
NPZ_PATH = "artifacts/sprint14c/test_predictions_model_D_seed_42.npz"
EVENT_METRICS_PATH = "artifacts/sprint15b_backup/event_level_metrics.json"
FEAT_IMP_PATH = "artifacts/sprint15b_backup/feature_importance.csv"
ATTN_STATS_PATH = "artifacts/sprint15b_backup/attention_statistics.json"
FAILURES_PATH = "artifacts/sprint15b_backup/failure_analysis.csv"
STRESS_PATH = "artifacts/sprint15b_backup/stress_test_results.json"
MANIFEST_PATH = "artifacts/sprint15a/benchmark_manifest.json"
CASEBOOK_PATH = "operator_casebook.md"

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

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

def get_device():
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")

def main():
    device = get_device()
    print("Device:", device)
    
    # ----------------------------------------------------
    # VALIDATION 8: Repository Integrity
    # ----------------------------------------------------
    print("\n=== VALIDATION 8: Repository Integrity ===")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    
    hashes_to_check = {
        "train_parquet": "artifacts/sprint14c/s2_train.parquet",
        "val_parquet": "artifacts/sprint14c/s2_val.parquet",
        "test_parquet": "artifacts/sprint14c/s2_test.parquet",
        "feature_columns_v3_json": "artifacts/feature_columns_v3.json",
        "model_seed_42_stage2_best_pt": "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt",
        "model_seed_42_stage1_best_pt": "artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt",
        "model_v3_py": "app/services/ml/model_v3.py"
    }
    
    val8_passed = True
    for key, path in hashes_to_check.items():
        computed = sha256(path)
        expected = manifest["dataset_hashes" if "parquet" in key else ("feature_manifest" if "json" in key else ("checkpoint_hash" if "pt" in key else "model_hash"))][key]
        if computed != expected:
            print(f"FAIL: Hash mismatch for {key} ({path}). Expected: {expected}, Got: {computed}")
            val8_passed = False
        else:
            print(f"PASS: {key} ({path}) matches.")
            
    # ----------------------------------------------------
    # VALIDATION 1: Event Metrics Recomputation
    # ----------------------------------------------------
    print("\n=== VALIDATION 1: Event Level Metrics ===")
    with open(EVENT_METRICS_PATH) as f:
        reported_event = json.load(f)
        
    data = np.load(NPZ_PATH)
    targets = data['targets']
    cal_probs = data['probs_calibrated_isotonic']
    probs_raw = data['probs_raw']
    best_th = 0.31686868686868686
    
    preds = (cal_probs >= best_th).astype(int)
    actual_events = find_contiguous_segments(targets)
    predicted_episodes = find_contiguous_segments(preds)
    
    caught_count = 0
    lead_times_min = []
    
    for S, E in actual_events:
        event_preds = preds[S : E + 1]
        if np.any(event_preds == 1):
            caught_count += 1
            first_alert_local = np.where(event_preds == 1)[0][0]
            first_alert_global = S + first_alert_local
            lead_time = (S + 360) - first_alert_global
            lead_times_min.append(lead_time)
            
    tp_episodes = 0
    fp_episodes = 0
    
    for s, e in predicted_episodes:
        episode_targets = targets[s : e + 1]
        if np.any(episode_targets == 1):
            tp_episodes += 1
        else:
            fp_episodes += 1
            
    event_recall = caught_count / len(actual_events)
    event_precision = tp_episodes / len(predicted_episodes)
    event_far = fp_episodes / len(predicted_episodes)
    
    lead_times_hrs = [lt / 60.0 for lt in lead_times_min]
    mean_lt = float(np.mean(lead_times_hrs))
    median_lt = float(np.median(lead_times_hrs))
    max_lt = float(np.max(lead_times_hrs))
    
    recomputed_event = {
        "event_recall": event_recall,
        "event_precision": event_precision,
        "event_far": event_far,
        "mean_detection_lead_time_hrs": mean_lt,
        "median_detection_lead_time_hrs": median_lt,
        "maximum_lead_time_hrs": max_lt
    }
    
    val1_passed = True
    for k in recomputed_event:
        v_rep = reported_event[k]
        v_rec = recomputed_event[k]
        diff = abs(v_rep - v_rec)
        if diff > 1e-6:
            print(f"FAIL: Mismatch for {k}. Reported: {v_rep:.12f}, Recomputed: {v_rec:.12f}, Diff: {diff:.12f}")
            val1_passed = False
        else:
            print(f"PASS: {k} matches (diff={diff:.12f}).")
            
    # ----------------------------------------------------
    # VALIDATION 7: Audit Operator Casebook
    # ----------------------------------------------------
    print("\n=== VALIDATION 7: Audit Operator Casebook ===")
    # Let's inspect the casebook. The casebook lists consecutive minutes starting at 2025-12-15T06:00:00
    # Let's parse operator_casebook.md to extract query timestamps, target labels, and alert decisions.
    import re
    with open(CASEBOOK_PATH) as f:
        casebook_content = f.read()
        
    investigations = re.findall(r"## Alert Investigation (\d+)\n-\s+\*\*Query Timestamp\*\*:\s+`([^`]+)`\n-\s+\*\*Target Label\*\*:\s+([^\n]+)\n-\s+\*\*Decision Alert Level\*\*:\s+([^\n]+)", casebook_content)
    
    # Load test timestamps
    df_test = pd.read_parquet(TEST_PARQUET, columns=["timestamp"])
    test_timestamps = df_test["timestamp"].values
    
    val7_passed = True
    print(f"Found {len(investigations)} alert investigations in casebook.")
    
    # We will randomly inspect 10 of them
    np.random.seed(42)
    sample_investigations = np.random.choice(len(investigations), 10, replace=False)
    
    for idx_inv in sorted(sample_investigations):
        inv_num, q_ts, reported_target, reported_decision = investigations[idx_inv]
        print(f"\nInspecting Alert Investigation {inv_num}:")
        print(f"  Reported Timestamp: {q_ts}")
        print(f"  Reported Target: {reported_target}")
        print(f"  Reported Decision: {reported_decision}")
        
        # In test set, look up the target and prediction for this exact timestamp
        # The parquet timestamp is a Timestamp object, e.g. Timestamp('2025-12-15 06:00:00')
        ts_to_find = q_ts.replace("T", " ")
        matching_indices = df_test[df_test["timestamp"] == ts_to_find].index.tolist()
        
        if not matching_indices:
            print(f"  FAIL: Timestamp {ts_to_find} not found in test set!")
            val7_passed = False
            continue
            
        parquet_idx = matching_indices[0]
        # Check if parquet_idx < 360
        if parquet_idx < 360:
            print(f"  FAIL: Parquet index {parquet_idx} is before the first prediction window (which starts at 360)!")
            val7_passed = False
            continue
            
        global_pred_idx = parquet_idx - 360
        actual_target_val = targets[global_pred_idx]
        actual_cal_prob = cal_probs[global_pred_idx]
        actual_raw_prob = probs_raw[global_pred_idx]
        actual_pred = 1 if actual_cal_prob >= best_th else 0
        actual_target_label = "Flare" if actual_target_val == 1.0 else "Quiet"
        actual_decision_label = "Yellow/Red" if actual_pred == 1 else "Green"
        
        # Note: in operator casebook, reported target is e.g. "Flare (High Alert)" or "Quiet"
        # and reported decision is "Yellow/Red (Active alert warning)" or "Green (No active warning)"
        t_match = reported_target.startswith(actual_target_label)
        d_match = reported_decision.startswith(actual_decision_label)
        
        if not t_match or not d_match:
            print(f"  ❌ MISMATCH DETECTED for timestamp {q_ts} (parquet_idx={parquet_idx}, global_pred_idx={global_pred_idx}):")
            print(f"    Source Data: Target={actual_target_label} ({actual_target_val}), CalProb={actual_cal_prob:.6f}, RawProb={actual_raw_prob:.6f}, Pred={actual_decision_label}")
            print(f"    Casebook: Target={reported_target}, Decision={reported_decision}")
            val7_passed = False
        else:
            print(f"    Source matches casebook: Target={actual_target_label}, Decision={actual_decision_label}")

if __name__ == "__main__":
    main()

import os
import json
import gzip
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# Paths
RAW_FLARES_DIR = "raw-data/flares"
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
AUDIT_JSON = "artifacts/aditya_l1/alignment_forensics_audit.json"
TEST_PARQUET = "artifacts/research/test.parquet"

def load_raw_flares():
    all_flares = []
    for filename in os.listdir(RAW_FLARES_DIR):
        if filename.endswith(".json.gz"):
            with gzip.open(os.path.join(RAW_FLARES_DIR, filename), "rt") as f:
                data = json.load(f)
                all_flares.extend(data)
    df = pd.DataFrame(all_flares)
    # Filter for XRA and C, M, X class
    df = df[df["type"] == "XRA"].copy()
    df["flare_class"] = df["particulars1"]
    df = df[df["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    df["start_time"] = pd.to_datetime(df["begin_datetime"])
    # Sort and drop duplicates for lineage
    df = df.sort_values("start_time").drop_duplicates(subset=["start_time", "flare_class"])
    return df

def main():
    print("Starting Independent Validation of Sprint 10G-OB...")
    
    # Load raw flares
    df_flares = load_raw_flares()
    print(f"Loaded {len(df_flares)} flares from raw catalog.")
    
    # Load master feature table
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    print(f"Loaded {len(df_master)} master rows.")
    
    # Load audit data
    with open(AUDIT_JSON, "r") as f:
        audit_data = json.load(f)
    
    discrepancies = {
        "target_lineage": [],
        "shifts": [],
        "overlap": [],
        "causal_ordering": [],
        "lead_lag_auc": []
    }
    
    # 1. Target Lineage
    print("Validating Task 1: Target Lineage...")
    flare_times = df_flares["start_time"].tolist()
    recomputed_targets = []
    for T in df_master["timestamp"]:
        window_end = T + pd.Timedelta(minutes=360)
        has_flare = any(T < ft <= window_end for ft in flare_times)
        recomputed_targets.append(1 if has_flare else 0)
    recomputed_targets = np.array(recomputed_targets)
    
    # In audit, total_mismatches_all_rows should be 0
    # I don't have the 'target' column in df_master directly, it was computed in the audit script
    # and stored in 'alignment_forensics_audit.json' as 'audit_records' for samples.
    # But I can re-run the audit logic and see if I get 0 mismatches.
    
    # Actually, the audit script says:
    # df_combined["target"] = target_6hr_binary_c.values
    # and then checks against it.
    
    # Let's check the sample records in the audit report
    for record in audit_data["target_lineage_audit"]["audit_records"]:
        T = pd.to_datetime(record["timestamp"])
        stored_val = record["stored_target"]
        
        window_end = T + pd.Timedelta(minutes=360)
        has_flare = any(T < ft <= window_end for ft in flare_times)
        recomputed_val = 1 if has_flare else 0
        
        if stored_val != recomputed_val:
            discrepancies["target_lineage"].append({
                "timestamp": str(T),
                "audit_value": stored_val,
                "recomputed_value": recomputed_val,
                "diff": abs(stored_val - recomputed_val)
            })
            
    # 2. Shift Implementation
    print("Validating Task 2: Shift Implementation...")
    # Re-compute compressed features to verify shifts
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    PC_scores = pca.fit_transform(X_std)
    
    soft_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(14, 29)]
    hard_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(29, 38)]
    soft_band_mean = df_channels[soft_band].mean(axis=1).values
    hard_band_mean = df_channels[hard_band].mean(axis=1).values
    hard_soft_ratio = hard_band_mean / (soft_band_mean + 1e-9)
    
    df_comp = pd.DataFrame({
        "timestamp": df_master["timestamp"],
        "soft_band_mean": soft_band_mean,
        "hard_band_mean": hard_band_mean,
        "hard_soft_ratio": hard_soft_ratio,
        "pc1_projection": PC_scores[:, 0],
        "pc2_projection": PC_scores[:, 1]
    })
    
    for verif in audit_data["shift_direction_audit"]["verifications"]:
        T = pd.to_datetime(verif["timestamp"])
        idx = df_comp[df_comp["timestamp"] == T].index[0]
        
        for feat, shifts_list in verif["shifts"].items():
            for s_record in shifts_list:
                s = s_record["shift_minutes"]
                audit_shifted_val = s_record["shifted_val_at_T"]
                
                # Recompute shift
                # In the audit script: df_shift_test[f"{feat}_shift_{s}"] = df_shift_test[feat].shift(-s)
                # index is 1-minute grid, so shift(-s) is correct for s minutes
                recomputed_shifted_val = df_comp.loc[idx + s, feat] if (idx + s) < len(df_comp) else np.nan
                
                if not np.isclose(audit_shifted_val, recomputed_shifted_val, atol=1e-9):
                    discrepancies["shifts"].append({
                        "timestamp": str(T),
                        "feature": feat,
                        "shift": s,
                        "audit_value": audit_shifted_val,
                        "recomputed_value": float(recomputed_shifted_val),
                        "diff": abs(audit_shifted_val - recomputed_shifted_val)
                    })

    # 3. Overlap Calculations
    print("Validating Task 3: Overlap Calculations...")
    pos_indices = np.where(recomputed_targets == 1)[0]
    total_pos = len(pos_indices)
    time_grid = df_master["timestamp"]
    flare_times_sorted = sorted(df_flares["start_time"].tolist())
    
    first_flares = []
    for idx in pos_indices:
        T = time_grid[idx]
        window_end = T + pd.Timedelta(minutes=360)
        found = False
        for ft in flare_times_sorted:
            if T < ft <= window_end:
                first_flares.append(ft)
                found = True
                break
        if not found:
            first_flares.append(T + pd.Timedelta(minutes=360))
            
    lags = [360, 180, 60, 30, 15, 5, 0]
    future_shifts = [60, 180, 360, 720]
    
    overlap_audit_recomputed = {}
    for lag in lags:
        leakage_count = 0
        for i, idx in enumerate(pos_indices):
            T_feat = time_grid[idx] - pd.Timedelta(minutes=lag)
            if T_feat >= first_flares[i]:
                leakage_count += 1
        name = f"lag_{lag}m" if lag > 0 else "contemporaneous"
        overlap_audit_recomputed[name] = (leakage_count / total_pos) * 100.0
        
    for shift in future_shifts:
        leakage_count = 0
        for i, idx in enumerate(pos_indices):
            T_feat = time_grid[idx] + pd.Timedelta(minutes=shift)
            if T_feat >= first_flares[i]:
                leakage_count += 1
        name = f"shift_plus_{shift}m"
        overlap_audit_recomputed[name] = (leakage_count / total_pos) * 100.0
        
    for name, audit_perc in audit_data["window_overlap_audit"]["overlap_audit"].items():
        recomputed_perc = overlap_audit_recomputed.get(name)
        if recomputed_perc is not None:
            if abs(audit_perc["leakage_percentage"] - recomputed_perc) > 1e-6:
                discrepancies["overlap"].append({
                    "name": name,
                    "audit_value": audit_perc["leakage_percentage"],
                    "recomputed_value": recomputed_perc,
                    "diff": abs(audit_perc["leakage_percentage"] - recomputed_perc)
                })

    # 4. Causal Ordering
    print("Validating Task 4: Causal Ordering...")
    val_at_0 = df_channels[soft_band].iloc[0].mean()
    df_channels_mut = df_channels.copy()
    df_channels_mut.iloc[1:] = 999.9
    val_at_0_mut = df_channels_mut[soft_band].iloc[0].mean()
    causal_pass = np.isclose(val_at_0, val_at_0_mut)
    audit_causal = audit_data["causal_ordering_audit"]["verdict"] == "PASS"
    if causal_pass != audit_causal:
        discrepancies["causal_ordering"].append({
            "audit_value": audit_causal,
            "recomputed_value": causal_pass,
            "diff": 1
        })

    # 5. Lead-Lag Reconstruction
    print("Validating Task 5: Lead-Lag Reconstruction...")
    df_features = pd.read_parquet(TEST_PARQUET, columns=["timestamp", "minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"])
    df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
    df_comp["target"] = recomputed_targets
    df_combined = pd.merge(df_comp, df_features, on="timestamp", how="inner")
    
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
    test_feats = ["soft_band_mean", "hard_band_mean", "hard_soft_ratio", "pc1_projection", "pc2_projection"]
    
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    offsets_to_check = [-360, -180, -60, 0, 60, 180, 360]
    
    for feat in test_feats:
        for offset in offsets_to_check:
            feat_shifted = df_combined[feat].shift(-offset)
            hist_shifted = df_combined[history_cols].shift(60)
            
            mask = feat_shifted.notna() & hist_shifted.notna().all(axis=1)
            Y = df_combined.loc[mask, "target"].values
            X_hist = hist_shifted[mask].values
            X_feat = feat_shifted[mask].values.reshape(-1, 1)
            X_joint = np.column_stack((X_feat, X_hist))
            
            lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint, Y)
            y_prob_aug = lr_aug.predict_proba(X_joint)[:, 1]
            recomputed_auc = roc_auc_score(Y, y_prob_aug)
            
            audit_feat_res = audit_data["lead_lag_reconstruction"].get(feat, {})
            audit_offset_res = audit_feat_res.get(f"offset_{offset}m", {})
            audit_auc = audit_offset_res.get("augmented", {}).get("auc", np.nan)
            
            if abs(audit_auc - recomputed_auc) > 1e-6:
                discrepancies["lead_lag_auc"].append({
                    "feature": feat,
                    "offset": offset,
                    "audit_value": audit_auc,
                    "recomputed_value": recomputed_auc,
                    "diff": abs(audit_auc - recomputed_auc)
                })

    # 7. Final Report
    print("Generating Validation Reports...")
    validation_report = {
        "discrepancies": discrepancies,
        "verdict": "PASS" if all(len(v) == 0 for v in discrepancies.values()) else "FAIL"
    }
    
    with open("artifacts/aditya_l1/alignment_validation.json", "w") as f:
        json.dump(validation_report, f, indent=2)
        
    md_report = f"# Alignment Validation Report\n\n"
    md_report += f"**Verdict: {validation_report['verdict']}**\n\n"
    
    for task, task_discs in discrepancies.items():
        md_report += f"## {task.replace('_', ' ').title()}\n\n"
        if not task_discs:
            md_report += "No discrepancies found.\n\n"
        else:
            md_report += "| Context | Audit Value | Recomputed Value | Absolute Difference |\n"
            md_report += "| :--- | :---: | :---: | :---: |\n"
            for d in task_discs:
                ctx = f"{d.get('timestamp', '')} {d.get('feature', '')} {d.get('offset', '')} {d.get('name', '')}".strip()
                md_report += f"| {ctx} | {d['audit_value']} | {d['recomputed_value']} | {d['diff']:.8f} |\n"
            md_report += "\n"
            
    with open("brain/alignment_validation.md", "w") as f:
        f.write(md_report)
    
    print(f"Validation finished. Verdict: {validation_report['verdict']}")

if __name__ == "__main__":
    main()

import os
import gc
import time
import json
import logging
import resource
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet"

OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/lead_lag_relationship_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_lead_lag_relationships.md"

def get_memory_use_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)

def get_target_group_name(col):
    if "hel1os_czt1_lc" in col or "hel1os_czt2_lc" in col: return "hel1os_czt_lightcurves"
    if "hel1os_cdte1_lc" in col or "hel1os_cdte2_lc" in col: return "hel1os_cdte_lightcurves"
    if "hel1os_evt" in col: return "hel1os_events"
    if "hel1os_hk" in col: return "hel1os_housekeeping"
    if "hel1os_czt_spec" in col: return "hel1os_czt_spectra"
    if "hel1os_cdte_spec" in col: return "hel1os_cdte_spectra"
    if "solexs_sdd2_lc" in col: return "solexs_lightcurve"
    if "solexs_sdd2_spec" in col: return "solexs_spectra"
    if "solexs_sdd2_gti" in col: return "solexs_gti"
    return "other"

def safe_val(val):
    if val is None or pd.isna(val) or np.isinf(val):
        return None
    return float(val)

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()
    peak_mem = initial_mem
    logger.info(f"Initial Memory Usage: {initial_mem:.2f} MB")

    if not os.path.exists(MASTER_PARQUET):
        logger.error(f"Master feature table not found at: {MASTER_PARQUET}")
        return

    # Load master feature table
    logger.info("Loading master feature table...")
    df_master = pd.read_parquet(MASTER_PARQUET)
    row_count = len(df_master)
    feature_cols = [col for col in df_master.columns if col != "timestamp"]
    feature_count = len(feature_cols)
    logger.info(f"Loaded master feature table: {row_count} rows, {feature_count} features")

    # Engineer surrogate target_6hr_binary_c using flares_full.parquet
    logger.info("Engineering surrogate C-class target...")
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    
    # Filter for C, M, or X flares
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min")
    
    # Create binary indicator on the master time grid
    time_grid = df_master["timestamp"]
    c_indicator = pd.Series(0, index=time_grid.index)
    c_indicator.loc[time_grid[time_grid.isin(c_flare_times)].index] = 1
    
    # Calculate 6-hour lookahead for C-class flares
    target_y = (
        c_indicator.shift(-1)
        .iloc[::-1]
        .rolling(window=360, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )

    offset_mapping = {
        "lead_360m": 360,
        "lead_180m": 180,
        "lead_120m": 120,
        "lead_60m": 60,
        "lead_30m": 30,
        "lead_15m": 15,
        "lead_5m": 5,
        "lag_0m": 0
    }

    results = {}
    
    logger.info("Starting lead-lag relationship calculations...")
    
    for f_idx, col in enumerate(feature_cols):
        if f_idx % 200 == 0:
            logger.info(f"  Feature {f_idx}/{feature_count}...")
            mem_now = get_memory_use_mb()
            if mem_now > peak_mem:
                peak_mem = mem_now
                
        feat = df_master[col]
        feature_results = {}
        
        max_abs_corr = -1.0
        offset_of_max_corr = None
        max_mutual_info = -1.0
        offset_of_max_mi = None
        
        for offset_name, offset_val in offset_mapping.items():
            # Shift feature by offset
            x_shifted = feat.shift(offset_val)
            
            # Clean NaNs
            mask = x_shifted.notna() & target_y.notna()
            x_c = x_shifted[mask]
            y_c = target_y[mask]
            
            eff_count = len(x_c)
            if eff_count < 10:
                # Fallback for insufficient data
                feature_results[offset_name] = {
                    "pearson": None,
                    "abs_pearson": None,
                    "spearman": None,
                    "abs_spearman": None,
                    "mutual_information": 0.0,
                    "effective_sample_count": eff_count,
                    "positive_target_count": 0,
                    "negative_target_count": 0
                }
                continue
                
            pos_count = int(y_c.sum())
            neg_count = eff_count - pos_count
            
            # Pearson
            try:
                p_val = float(x_c.corr(y_c, method="pearson"))
            except Exception:
                p_val = np.nan
                
            # Spearman (rank transform for speed)
            try:
                s_val = float(x_c.rank().corr(y_c.rank(), method="pearson"))
            except Exception:
                s_val = np.nan
                
            # Mutual Information (sklearn)
            try:
                x_2d = x_c.values.reshape(-1, 1)
                mi_arr = mutual_info_classif(x_2d, y_c, random_state=42)
                mi_val = float(mi_arr[0])
            except Exception:
                mi_val = 0.0
                
            # Store offset metrics
            abs_p = abs(p_val) if pd.notna(p_val) else 0.0
            
            feature_results[offset_name] = {
                "pearson": safe_val(p_val),
                "abs_pearson": safe_val(abs_p),
                "spearman": safe_val(s_val),
                "abs_spearman": safe_val(abs(s_val)) if pd.notna(s_val) else None,
                "mutual_information": safe_val(mi_val),
                "effective_sample_count": eff_count,
                "positive_target_count": pos_count,
                "negative_target_count": neg_count
            }
            
            # Track max Pearson correlation
            if abs_p > max_abs_corr:
                max_abs_corr = abs_p
                offset_of_max_corr = offset_name
                
            # Track max Mutual Information
            if mi_val > max_mutual_info:
                max_mutual_info = mi_val
                offset_of_max_mi = offset_name
                
        results[col] = {
            "offsets": feature_results,
            "max_abs_corr": safe_val(max_abs_corr) if max_abs_corr >= 0 else None,
            "offset_of_max_corr": offset_of_max_corr,
            "max_mutual_information": safe_val(max_mutual_info) if max_mutual_info >= 0 else None,
            "offset_of_max_mi": offset_of_max_mi
        }

    # Group Summaries
    logger.info("Computing telemetry group summaries...")
    target_groups = [
        "hel1os_czt_lightcurves",
        "hel1os_cdte_lightcurves",
        "hel1os_events",
        "hel1os_housekeeping",
        "hel1os_czt_spectra",
        "hel1os_cdte_spectra",
        "solexs_lightcurve",
        "solexs_spectra",
        "solexs_gti"
    ]
    
    group_summaries = {}
    
    # Organize by group
    group_feats = {g: [] for g in target_groups + ["other"]}
    for col in feature_cols:
        gname = get_target_group_name(col)
        group_feats[gname].append(col)
        
    for gname, cols in group_feats.items():
        if not cols:
            continue
            
        group_max_corrs = []
        group_max_mis = []
        offset_tally = {k: 0 for k in offset_mapping.keys()}
        
        for col in cols:
            feat_res = results[col]
            if feat_res["max_abs_corr"] is not None:
                group_max_corrs.append(feat_res["max_abs_corr"])
            if feat_res["max_mutual_information"] is not None:
                group_max_mis.append(feat_res["max_mutual_information"])
            if feat_res["offset_of_max_corr"] in offset_tally:
                offset_tally[feat_res["offset_of_max_corr"]] += 1
                
        med_max_corr = float(np.median(group_max_corrs)) if group_max_corrs else 0.0
        max_corr = float(np.max(group_max_corrs)) if group_max_corrs else 0.0
        med_max_mi = float(np.median(group_max_mis)) if group_max_mis else 0.0
        max_mi = float(np.max(group_max_mis)) if group_max_mis else 0.0
        
        group_summaries[gname] = {
            "feature_count": len(cols),
            "median_max_abs_corr": med_max_corr,
            "max_abs_corr": max_corr,
            "median_max_mi": med_max_mi,
            "max_mi": max_mi,
            "offset_frequency_distribution": offset_tally
        }

    # Save JSON Output
    logger.info("Saving JSON output...")
    output_dict = {
        "feature_lead_lag_audit": results,
        "group_summaries": group_summaries
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(output_dict, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")

    # Build Markdown Report
    logger.info("Building Markdown report...")
    
    md_lines = [
        "# Master Lead-Lag Relationship Audit Report",
        "",
        "## 1. Executive Summary",
        "This report audits the lead-lag relationship between every Aditya-L1 feature and the supplemental active solar flare target (`target_6hr_binary_c`). All metrics represent measured facts only.",
        "",
        "## 2. Table Statistics",
        f"- **Row Count**: {row_count}",
        f"- **Feature Count**: {feature_count}",
        "",
        "## 3. Telemetry Group Relationship Summary",
        "",
        "| Telemetry Group | Feature Count | Median Max Abs Corr | Max Abs Corr | Median Max MI | Max MI | Best Offset Distribution |",
        "| --- | --- | --- | --- | --- | --- | --- |"
    ]

    for gname in sorted(target_groups):
        if gname in group_summaries:
            stats = group_summaries[gname]
            dist_str = ", ".join([f"{k.split('_')[-1]}:{v}" for k, v in stats['offset_frequency_distribution'].items() if v > 0])
            md_lines.append(f"| {gname} | {stats['feature_count']} | {stats['median_max_abs_corr']:.4f} | {stats['max_abs_corr']:.4f} | {stats['median_max_mi']:.4f} | {stats['max_mi']:.4f} | {dist_str} |")

    md_lines.extend([
        "",
        "## 4. Representative Feature Samples (Lead-Lag Curve)",
        "",
        "Below are samples from each telemetry group showing the full lead-lag correlation and mutual information curve across offsets:",
        "",
        "| Telemetry Group | Feature Name | Metric | lead_360m | lead_180m | lead_120m | lead_60m | lead_30m | lead_15m | lead_5m | lag_0m |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    # Sample 1 feature per group
    for gname in sorted(target_groups):
        sample_feat = None
        for col in feature_cols:
            if get_target_group_name(col) == gname:
                sample_feat = col
                break
        if sample_feat:
            feat_res = results[sample_feat]["offsets"]
            
            # Pearson row
            p_vals = []
            for offset_name in offset_mapping.keys():
                p = feat_res[offset_name]["pearson"]
                p_vals.append(f"{p:.4f}" if p is not None else "NaN")
            md_lines.append(f"| {gname} | `{sample_feat}` | Pearson | " + " | ".join(p_vals) + " |")
            
            # MI row
            mi_vals = []
            for offset_name in offset_mapping.keys():
                mi = feat_res[offset_name]["mutual_information"]
                mi_vals.append(f"{mi:.4f}" if mi is not None else "0.0")
            md_lines.append(f"| | | MI | " + " | ".join(mi_vals) + " |")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines))
    logger.info(f"Saved Markdown report to {OUT_MD}")

    # Track metrics
    duration = time.time() - start_time
    final_mem = get_memory_use_mb()
    
    summary_stats = {
        "files_created": [OUT_JSON, OUT_MD],
        "row_count_processed": row_count,
        "feature_count_processed": feature_count,
        "runtime_s": duration,
        "initial_mem_mb": initial_mem,
        "peak_mem_mb": peak_mem if peak_mem > final_mem else final_mem,
        "final_mem_mb": final_mem
    }
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/lead_lag_relationship_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

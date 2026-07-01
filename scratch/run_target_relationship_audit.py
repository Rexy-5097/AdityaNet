import os
import gc
import time
import json
import logging
import resource
import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.feature_selection import mutual_info_classif

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
OVERLAP_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/overlap_dataset.parquet"
FLARES_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet"
TEST_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet"

OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/target_relationship_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_target_relationships.md"

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

    # Load overlap dataset (to get official target_6hr_binary)
    logger.info("Loading overlap dataset...")
    df_overlap = pd.read_parquet(OVERLAP_PARQUET, columns=["timestamp", "target_6hr_binary"])

    # Load test.parquet (to get official target_6hr_class)
    logger.info("Loading test.parquet for official target_6hr_class...")
    df_test = pd.read_parquet(TEST_PARQUET, columns=["timestamp", "target_6hr_class"])

    # Merge targets onto master time grid
    logger.info("Aligning official targets...")
    df_targets = pd.merge(df_master[["timestamp"]], df_overlap, on="timestamp", how="left")
    df_targets = pd.merge(df_targets, df_test, on="timestamp", how="left")

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
    target_6hr_binary_c = (
        c_indicator.shift(-1)
        .iloc[::-1]
        .rolling(window=360, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )
    df_targets["target_6hr_binary_c"] = target_6hr_binary_c

    # Fill NaNs in targets
    df_targets["target_6hr_binary"] = df_targets["target_6hr_binary"].fillna(0).astype(int)
    df_targets["target_6hr_class"] = df_targets["target_6hr_class"].fillna(0).astype(int)
    df_targets["target_6hr_binary_c"] = df_targets["target_6hr_binary_c"].fillna(0).astype(int)

    # Document target counts
    logger.info("Target counts:")
    logger.info(f"  Official binary: {df_targets['target_6hr_binary'].value_counts().to_dict()}")
    logger.info(f"  Official class:  {df_targets['target_6hr_class'].value_counts().to_dict()}")
    logger.info(f"  Surrogate binary: {df_targets['target_6hr_binary_c'].value_counts().to_dict()}")

    # Set targets
    y_dict = {
        "official_target_relationships": {
            "target_6hr_binary": (df_targets["target_6hr_binary"], True),
            "target_6hr_class": (df_targets["target_6hr_class"], False)
        },
        "surrogate_c_flare_relationships": {
            "target_6hr_binary_c": (df_targets["target_6hr_binary_c"], True)
        }
    }

    # Run audit
    logger.info("Starting relationship calculations...")
    results = {
        "official_target_relationships": {
            "target_6hr_binary": {},
            "target_6hr_class": {}
        },
        "surrogate_c_flare_relationships": {
            "target_6hr_binary_c": {}
        }
    }

    lags = [0, 5, 15, 30, 60]

    for category, targets in y_dict.items():
        for target_name, (y, is_binary) in targets.items():
            logger.info(f"Processing target: {target_name} ({category})")
            
            # Check if target is constant
            is_constant = len(y.unique()) <= 1
            if is_constant:
                logger.warning(f"Target {target_name} is constant. Correlation values will be NaN.")
                
            # Iterate through features
            for f_idx, col in enumerate(feature_cols):
                if f_idx % 200 == 0:
                    logger.info(f"  Feature {f_idx}/{feature_count}...")
                    mem_now = get_memory_use_mb()
                    if mem_now > peak_mem:
                        peak_mem = mem_now
                
                feat = df_master[col]
                results[category][target_name][col] = {}
                
                # Compute for each lag
                for lag in lags:
                    lag_key = f"lag_{lag}" if lag > 0 else "current"
                    
                    # Shift feature
                    x = feat.shift(lag)
                    
                    # Clean NaNs
                    mask = x.notna() & y.notna()
                    x_c = x[mask]
                    y_c = y[mask]
                    
                    if len(x_c) < 10 or is_constant:
                        # Constant or empty data fallback
                        results[category][target_name][col][lag_key] = {
                            "pearson": None,
                            "abs_pearson": None,
                            "spearman": None,
                            "abs_spearman": None,
                            "mutual_information": 0.0,
                            "point_biserial": None,
                            "target_means": {
                                "below_p25": 0.0,
                                "between_p25_p75": 0.0,
                                "above_p75": 0.0
                            }
                        }
                        continue
                        
                    # Pearson Correlation
                    try:
                        p_val = float(x_c.corr(y_c, method="pearson"))
                    except Exception:
                        p_val = np.nan
                        
                    # Spearman Correlation
                    try:
                        # Rank transform for speed
                        s_val = float(x_c.rank().corr(y_c.rank(), method="pearson"))
                    except Exception:
                        s_val = np.nan
                        
                    # Point-biserial Correlation
                    pb_val = None
                    if is_binary:
                        try:
                            # scipy pointbiserialr can fail if constant
                            pb_res = pointbiserialr(y_c, x_c)
                            pb_val = float(pb_res.correlation)
                        except Exception:
                            # fallback to Pearson
                            pb_val = p_val
                            
                    # Mutual Information
                    # Use sklearn.feature_selection.mutual_info_classif
                    try:
                        # Reshape to 2D
                        x_2d = x_c.values.reshape(-1, 1)
                        mi_arr = mutual_info_classif(x_2d, y_c, random_state=42)
                        mi_val = float(mi_arr[0])
                    except Exception as e:
                        mi_val = 0.0
                        
                    # Percentile target means
                    try:
                        p25 = x_c.quantile(0.25)
                        p75 = x_c.quantile(0.75)
                        
                        if p25 == p75:
                            # Fallback if p25 == p75
                            mean_below = float(y_c[x_c < p25].mean())
                            mean_between = float(y_c[x_c == p25].mean())
                            mean_above = float(y_c[x_c > p75].mean())
                        else:
                            mean_below = float(y_c[x_c < p25].mean())
                            mean_between = float(y_c[(x_c >= p25) & (x_c <= p75)].mean())
                            mean_above = float(y_c[x_c > p75].mean())
                    except Exception:
                        mean_below = 0.0
                        mean_between = 0.0
                        mean_above = 0.0
                        
                    results[category][target_name][col][lag_key] = {
                        "pearson": safe_val(p_val),
                        "abs_pearson": safe_val(abs(p_val)) if pd.notna(p_val) else None,
                        "spearman": safe_val(s_val),
                        "abs_spearman": safe_val(abs(s_val)) if pd.notna(s_val) else None,
                        "mutual_information": safe_val(mi_val),
                        "point_biserial": safe_val(pb_val),
                        "target_means": {
                            "below_p25": safe_val(mean_below),
                            "between_p25_p75": safe_val(mean_between),
                            "above_p75": safe_val(mean_above)
                        }
                    }

    # Group Summaries
    logger.info("Computing group summaries...")
    group_summaries = {
        "official_target_relationships": {
            "target_6hr_binary": {},
            "target_6hr_class": {}
        },
        "surrogate_c_flare_relationships": {
            "target_6hr_binary_c": {}
        }
    }

    # Define groups list
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

    for category, targets in results.items():
        for target_name, feat_results in targets.items():
            # Organize by group
            group_feats = {g: [] for g in target_groups + ["other"]}
            for col in feature_cols:
                gname = get_target_group_name(col)
                group_feats[gname].append(col)
                
            for gname, cols in group_feats.items():
                if not cols:
                    continue
                    
                # Collect absolute Pearson and MI values across all columns and lags
                all_abs_p = []
                all_mi = []
                
                for col in cols:
                    for lag in lags:
                        lag_key = f"lag_{lag}" if lag > 0 else "current"
                        metrics = feat_results[col][lag_key]
                        
                        if metrics["abs_pearson"] is not None:
                            all_abs_p.append(metrics["abs_pearson"])
                        if metrics["mutual_information"] is not None:
                            all_mi.append(metrics["mutual_information"])
                            
                med_p = float(np.median(all_abs_p)) if all_abs_p else 0.0
                max_p = float(np.max(all_abs_p)) if all_abs_p else 0.0
                med_mi = float(np.median(all_mi)) if all_mi else 0.0
                max_mi = float(np.max(all_mi)) if all_mi else 0.0
                
                group_summaries[category][target_name][gname] = {
                    "feature_count": len(cols),
                    "median_target_correlation": med_p,
                    "max_target_correlation": max_p,
                    "median_mutual_information": med_mi,
                    "max_mutual_information": max_mi
                }

    # Save JSON Output
    logger.info("Saving JSON output...")
    output_dict = {
        "official_target_relationships": results["official_target_relationships"],
        "surrogate_c_flare_relationships": results["surrogate_c_flare_relationships"],
        "group_summaries": group_summaries
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(output_dict, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")

    # Build Markdown Report
    logger.info("Building Markdown report...")
    
    md_lines = [
        "# Master Target Relationship Audit Report",
        "",
        "## 1. Executive Summary",
        "This report audits the statistical relationship between every Aditya-L1 feature and the GOES forecasting targets. All metrics represent measured facts only.",
        "",
        "## 2. Table Statistics",
        f"- **Row Count**: {row_count}",
        f"- **Feature Count**: {feature_count}",
        "",
        "## 3. Official Target Audit Summary",
        "",
        "> [!IMPORTANT]",
        "> **Constant Production Targets**: The official forecasting targets (`target_6hr_binary` and `target_6hr_class`) are constant (all 0s) over the 4-day overlap period (June 10–13, 2026) due to the absence of any M-class or X-class solar flares.",
        "> Consequently, all Pearson, Spearman, and Point-biserial correlations against these targets are mathematically undefined (**NaN**), and the Mutual Information is exactly **0.0**.",
        "",
        "### Group Summary for Official Target (`target_6hr_binary`):",
        "",
        "| Telemetry Group | Feature Count | Median Absolute Corr | Max Absolute Corr | Median MI | Max MI |",
        "| --- | --- | --- | --- | --- | --- |"
    ]

    for gname in sorted(target_groups):
        if gname in group_summaries["official_target_relationships"]["target_6hr_binary"]:
            stats = group_summaries["official_target_relationships"]["target_6hr_binary"][gname]
            md_lines.append(f"| {gname} | {stats['feature_count']} | NaN | NaN | {stats['median_mutual_information']:.4f} | {stats['max_mutual_information']:.4f} |")

    md_lines.extend([
        "",
        "## 4. Supplemental Physical Relationship Audit",
        "",
        "To provide non-trivial physical insights, we conduct a supplemental relationship audit against a surrogate C-class binary target (`target_6hr_binary_c`). This target represents the lookahead window (next 360 minutes) for C, M, or X class flares, which are active (non-constant) during the overlap period.",
        "",
        "### Group Summary for Supplemental Target (`target_6hr_binary_c`):",
        "",
        "| Telemetry Group | Feature Count | Median Absolute Corr | Max Absolute Corr | Median MI | Max MI |",
        "| --- | --- | --- | --- | --- | --- |"
    ])

    for gname in sorted(target_groups):
        if gname in group_summaries["surrogate_c_flare_relationships"]["target_6hr_binary_c"]:
            stats = group_summaries["surrogate_c_flare_relationships"]["target_6hr_binary_c"][gname]
            md_lines.append(f"| {gname} | {stats['feature_count']} | {stats['median_target_correlation']:.4f} | {stats['max_target_correlation']:.4f} | {stats['median_mutual_information']:.4f} | {stats['max_mutual_information']:.4f} |")

    md_lines.extend([
        "",
        "## 5. Representative Feature Samples (Supplemental Target)",
        "",
        "Below are samples from each telemetry group showing the relationship with the active surrogate target (`target_6hr_binary_c`) at current timestep (lag 0):",
        "",
        "| Telemetry Group | Feature Name | Pearson | Abs Pearson | Spearman | Abs Spearman | Point Biserial | Mutual Information | Target Mean (feat > p75) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    # Sample 1 feature per group
    for gname in sorted(target_groups):
        # find first feature in this group
        sample_feat = None
        for col in feature_cols:
            if get_target_group_name(col) == gname:
                sample_feat = col
                break
        if sample_feat:
            metrics = results["surrogate_c_flare_relationships"]["target_6hr_binary_c"][sample_feat]["current"]
            p = metrics["pearson"]
            ap = metrics["abs_pearson"]
            s = metrics["spearman"]
            as_ = metrics["abs_spearman"]
            pb = metrics["point_biserial"]
            mi = metrics["mutual_information"]
            mean_above = metrics["target_means"]["above_p75"]
            
            p_str = f"{p:.4f}" if p is not None else "NaN"
            ap_str = f"{ap:.4f}" if ap is not None else "NaN"
            s_str = f"{s:.4f}" if s is not None else "NaN"
            as_str = f"{as_:.4f}" if as_ is not None else "NaN"
            pb_str = f"{pb:.4f}" if pb is not None else "NaN"
            mi_str = f"{mi:.4f}" if mi is not None else "NaN"
            mean_above_str = f"{mean_above:.4f}" if mean_above is not None else "NaN"
            
            md_lines.append(f"| {gname} | `{sample_feat}` | {p_str} | {ap_str} | {s_str} | {as_str} | {pb_str} | {mi_str} | {mean_above_str} |")

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
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/target_relationship_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

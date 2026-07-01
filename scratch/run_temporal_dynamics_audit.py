import os
import gc
import time
import json
import logging
import resource
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

PARQUET_PATH = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/temporal_dynamics_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_temporal_dynamics.md"

def get_memory_use_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)

def safe_val(val):
    if val is None or pd.isna(val) or np.isinf(val):
        return None
    return float(val)

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()
    logger.info(f"Initial Memory Usage: {initial_mem:.2f} MB")
    
    if not os.path.exists(PARQUET_PATH):
        logger.error(f"Master feature table not found at: {PARQUET_PATH}")
        return
        
    pq_file = pq.ParquetFile(PARQUET_PATH)
    row_count = pq_file.metadata.num_rows
    all_columns = [col for col in pq_file.schema.names if col != "timestamp"]
    feature_count = len(all_columns)
    logger.info(f"Table has {row_count} rows and {feature_count} features")
    
    batch_size = 100
    results = {}
    peak_mem = initial_mem
    
    # Process in batches of columns
    for idx in range(0, feature_count, batch_size):
        batch_cols = all_columns[idx:idx+batch_size]
        df_batch = pq_file.read(columns=batch_cols).to_pandas()
        
        mem_now = get_memory_use_mb()
        if mem_now > peak_mem:
            peak_mem = mem_now
            
        for col in batch_cols:
            series = df_batch[col]
            
            # Lag-k autocorrelations
            r1 = series.autocorr(lag=1)
            r5 = series.autocorr(lag=5)
            r60 = series.autocorr(lag=60)
            
            # First differences
            diff = series.diff()
            valid_pairs = diff.notna()
            total_pairs = int(valid_pairs.sum())
            
            if total_pairs == 0:
                results[col] = {
                    "lag1_autocorrelation": None,
                    "lag5_autocorrelation": None,
                    "lag60_autocorrelation": None,
                    "first_difference_mean": None,
                    "first_difference_std": None,
                    "unchanged_consecutive_pct": 0.0,
                    "change_points_count": 0
                }
                continue
                
            diff_mean = diff.mean()
            diff_std = diff.std()
            
            unchanged = int((diff == 0.0).sum())
            unchanged_pct = (unchanged / total_pairs) * 100.0
            
            change_points = int(((diff != 0.0) & valid_pairs).sum())
            
            results[col] = {
                "lag1_autocorrelation": safe_val(r1),
                "lag5_autocorrelation": safe_val(r5),
                "lag60_autocorrelation": safe_val(r60),
                "first_difference_mean": safe_val(diff_mean),
                "first_difference_std": safe_val(diff_std),
                "unchanged_consecutive_pct": float(unchanged_pct),
                "change_points_count": int(change_points)
            }
            
        # Free memory of this batch
        del df_batch
        gc.collect()
        
    duration = time.time() - start_time
    final_mem = get_memory_use_mb()
    
    logger.info("Writing JSON report...")
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")
    
    # Group features by source
    def get_group_name(col):
        if "hel1os_czt1_lc" in col: return "hel1os_czt1_lightcurve"
        if "hel1os_czt2_lc" in col: return "hel1os_czt2_lightcurve"
        if "hel1os_cdte1_lc" in col: return "hel1os_cdte1_lightcurve"
        if "hel1os_cdte2_lc" in col: return "hel1os_cdte2_lightcurve"
        if "solexs_sdd2_lc" in col: return "solexs_sdd2_lightcurve"
        if "hel1os_hk" in col: return "hel1os_housekeeping"
        if "solexs_sdd2_gti" in col: return "solexs_sdd2_gti"
        if "hel1os_czt_spec" in col: return "hel1os_czt_spectra"
        if "hel1os_cdte_spec" in col: return "hel1os_cdte_spectra"
        if "solexs_sdd2_spec" in col: return "solexs_sdd2_spectra"
        if "hel1os_evt" in col: return "hel1os_events"
        return "other"
        
    groups = {}
    for col in all_columns:
        gname = get_group_name(col)
        groups[gname] = groups.get(gname, [])
        groups[gname].append(col)
        
    # Build Markdown
    logger.info("Building Markdown report...")
    md_lines = [
        "# Master Feature Temporal Dynamics Audit Report",
        "",
        "## 1. Executive Summary",
        "This report audits the temporal behaviors, autocorrelations, and change point statistics of every feature in the master telemetry table. All metrics represent measured facts only.",
        "",
        "## 2. Table Statistics",
        f"- **Row Count**: {row_count}",
        f"- **Feature Count**: {feature_count}",
        "",
        "## 3. Telemetry Group Temporal Dynamics Summary",
        "",
        "| Telemetry Group | Total Features | Median Lag-1 Autocorr | Median Lag-5 Autocorr | Median Lag-60 Autocorr | Median Unchanged Pct | Median Change Points |",
        "| --- | --- | --- | --- | --- | --- | --- |"
    ]
    
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        g_r1 = [results[c]["lag1_autocorrelation"] for c in cols if results[c]["lag1_autocorrelation"] is not None]
        g_r5 = [results[c]["lag5_autocorrelation"] for c in cols if results[c]["lag5_autocorrelation"] is not None]
        g_r60 = [results[c]["lag60_autocorrelation"] for c in cols if results[c]["lag60_autocorrelation"] is not None]
        g_unchanged = [results[c]["unchanged_consecutive_pct"] for c in cols]
        g_change = [results[c]["change_points_count"] for c in cols]
        
        med_r1 = float(np.median(g_r1)) if g_r1 else 0.0
        med_r5 = float(np.median(g_r5)) if g_r5 else 0.0
        med_r60 = float(np.median(g_r60)) if g_r60 else 0.0
        med_unch = float(np.median(g_unchanged))
        med_ch = float(np.median(g_change))
        
        md_lines.append(f"| {gname} | {len(cols)} | {med_r1:.4f} | {med_r5:.4f} | {med_r60:.4f} | {med_unch:.2f}% | {med_ch:.1f} |")
        
    md_lines.append("")
    md_lines.append("## 4. Telemetry Group Feature Details")
    md_lines.append("")
    
    # Detailed sample features per group
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        md_lines.append(f"### Telemetry Group: `{gname}`")
        md_lines.append(f"- **Total Features**: {len(cols)}")
        md_lines.append("- **Representative Feature Samples**:")
        md_lines.append("")
        md_lines.append("  | Feature Name | Lag-1 Autocorr | Lag-5 Autocorr | Lag-60 Autocorr | Diff Mean | Diff Std | Unchanged Pct | Change Points |")
        md_lines.append("  | --- | --- | --- | --- | --- | --- | --- | --- |")
        
        # Sample 5 features
        for c in cols[:5]:
            r = results[c]
            r1_s = f"{r['lag1_autocorrelation']:.4f}" if r["lag1_autocorrelation"] is not None else "N/A"
            r5_s = f"{r['lag5_autocorrelation']:.4f}" if r["lag5_autocorrelation"] is not None else "N/A"
            r60_s = f"{r['lag60_autocorrelation']:.4f}" if r["lag60_autocorrelation"] is not None else "N/A"
            diff_mean_s = f"{r['first_difference_mean']:.4e}" if r["first_difference_mean"] is not None else "N/A"
            diff_std_s = f"{r['first_difference_std']:.4e}" if r["first_difference_std"] is not None else "N/A"
            
            md_lines.append(f"  | `{c}` | {r1_s} | {r5_s} | {r60_s} | {diff_mean_s} | {diff_std_s} | {r['unchanged_consecutive_pct']:.2f}% | {r['change_points_count']} |")
        md_lines.append("")
        
    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines))
    logger.info(f"Saved Markdown report to {OUT_MD}")
    
    # Save statistics for return value
    summary_stats = {
        "files_created": [OUT_JSON, OUT_MD],
        "row_count_processed": row_count,
        "feature_count_processed": feature_count,
        "runtime_s": duration,
        "initial_mem_mb": initial_mem,
        "peak_mem_mb": peak_mem,
        "final_mem_mb": final_mem
    }
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/temporal_dynamics_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

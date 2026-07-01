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
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/information_content_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_information_content.md"

def get_memory_use_mb():
    # Peak memory usage on macOS/Unix (ru_maxrss is in bytes on macOS)
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)

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
            valid = series.dropna()
            n_valid = len(valid)
            n_total = len(series)
            
            missing_pct = ((n_total - n_valid) / n_total) * 100.0
            
            if n_valid == 0:
                results[col] = {
                    "missing_pct": missing_pct,
                    "unique_values_count": 0,
                    "unique_values_pct": 0.0,
                    "zero_pct": 0.0,
                    "entropy": 0.0,
                    "is_constant": True,
                    "is_near_constant": True,
                    "is_zero_dominated": False
                }
                continue
                
            nunique = int(valid.nunique())
            unique_val_pct = (nunique / n_valid) * 100.0
            
            zero_count = int(np.sum(valid == 0.0))
            zero_pct = (zero_count / n_valid) * 100.0
            is_zero_dominated = zero_pct >= 90.0
            
            # Shannon entropy from observed frequencies
            p = valid.value_counts(normalize=True)
            entropy = -float(np.sum(p * np.log2(p)))
            
            is_constant = (nunique <= 1)
            is_near_constant = float(p.max()) >= 0.99
            
            results[col] = {
                "missing_pct": float(missing_pct),
                "unique_values_count": nunique,
                "unique_values_pct": float(unique_val_pct),
                "zero_pct": float(zero_pct),
                "entropy": float(entropy),
                "is_constant": bool(is_constant),
                "is_near_constant": bool(is_near_constant),
                "is_zero_dominated": bool(is_zero_dominated)
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
        "# Master Feature Information Content Audit Report",
        "",
        "## 1. Executive Summary",
        "This report audits the information content and entropy of every feature in the master telemetry table. All metrics represent measured facts only.",
        "",
        "## 2. Table Statistics",
        f"- **Row Count**: {row_count}",
        f"- **Feature Count**: {feature_count}",
        "",
        "## 3. Telemetry Group Information Content Summary",
        "",
        "| Telemetry Group | Total Features | Constant Count | Near-Constant Count | Zero-Dominated Count | Median Entropy | Entropy Range |",
        "| --- | --- | --- | --- | --- | --- | --- |"
    ]
    
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        g_entropy = [results[c]["entropy"] for c in cols]
        g_constant = sum(1 for c in cols if results[c]["is_constant"])
        g_near_const = sum(1 for c in cols if results[c]["is_near_constant"])
        g_zero_dom = sum(1 for c in cols if results[c]["is_zero_dominated"])
        
        med_ent = float(np.median(g_entropy))
        min_ent, max_ent = min(g_entropy), max(g_entropy)
        
        md_lines.append(f"| {gname} | {len(cols)} | {g_constant} | {g_near_const} | {g_zero_dom} | {med_ent:.4f} | {min_ent:.4f}..{max_ent:.4f} |")
        
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
        md_lines.append("  | Feature Name | Missing Pct | Unique Val Count | Unique Val Pct | Zero Pct | Entropy | Constant? | Near-Constant? | Zero-Dominated? |")
        md_lines.append("  | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        
        # Sample 5 features
        for c in cols[:5]:
            r = results[c]
            md_lines.append(f"  | `{c}` | {r['missing_pct']:.2f}% | {r['unique_values_count']} | {r['unique_values_pct']:.2f}% | {r['zero_pct']:.2f}% | {r['entropy']:.4f} | {r['is_constant']} | {r['is_near_constant']} | {r['is_zero_dominated']} |")
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
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/information_content_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

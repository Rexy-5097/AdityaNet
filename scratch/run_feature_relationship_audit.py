import os
import gc
import time
import json
import logging
import resource
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

PARQUET_PATH = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/feature_relationship_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_feature_relationships.md"

def get_memory_use_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)

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

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()
    peak_mem = initial_mem
    logger.info(f"Initial Memory Usage: {initial_mem:.2f} MB")
    
    if not os.path.exists(PARQUET_PATH):
        logger.error(f"Master feature table not found at: {PARQUET_PATH}")
        return
        
    logger.info("Loading master feature table...")
    df = pd.read_parquet(PARQUET_PATH)
    row_count = len(df)
    feature_cols = [col for col in df.columns if col != "timestamp"]
    feature_count = len(feature_cols)
    logger.info(f"Loaded master feature table: {row_count} rows, {feature_count} features")
    
    # Extract only features
    df_feat = df[feature_cols]
    
    # 1. Pearson Correlation
    logger.info("Computing Pearson correlation matrix...")
    corr_pearson = df_feat.corr(method="pearson").abs()
    
    # 2. Spearman Correlation (Pearson of rank-transformed columns for speed)
    logger.info("Computing Spearman correlation matrix...")
    df_feat_ranked = df_feat.rank()
    corr_spearman = df_feat_ranked.corr(method="pearson").abs()
    
    mem_now = get_memory_use_mb()
    if mem_now > peak_mem:
        peak_mem = mem_now
    logger.info(f"Memory after correlation computations: {mem_now:.2f} MB")
    
    # 3. Duplicate Relationship Audit
    logger.info("Detecting exact duplicates...")
    # Hash values column-wise to quickly find duplicates
    col_hashes = {}
    for col in feature_cols:
        col_hashes[col] = hash(tuple(df_feat[col].values))
        
    hash_to_cols = {}
    for col, h in col_hashes.items():
        hash_to_cols[h] = hash_to_cols.get(h, []) + [col]
        
    exact_duplicates = {}
    for h, cols in hash_to_cols.items():
        if len(cols) > 1:
            for c1 in cols:
                exact_duplicates[c1] = []
                for c2 in cols:
                    if c1 != c2:
                        # check exact equality (handling NaNs)
                        if df_feat[c1].equals(df_feat[c2]):
                            exact_duplicates[c1].append(c2)
                            
    # Aggregate duplicate features list
    all_duplicates = []
    seen = set()
    for col, dups in exact_duplicates.items():
        if col not in seen:
            seen.add(col)
            for d in dups:
                seen.add(d)
            all_duplicates.append({
                "features": [col] + dups
            })
            
    # Count of duplicate features total (features that have at least one exact duplicate)
    duplicate_feature_count = len(exact_duplicates)
    
    # 4. Global Correlation Statistics
    logger.info("Computing global correlation statistics...")
    # Total feature pairs (upper triangle)
    n = feature_count
    total_pairs = int(n * (n - 1) / 2)
    
    # Get values from upper triangle of Pearson correlation matrix
    triu_indices = np.triu_indices(n, k=1)
    pearson_vals = corr_pearson.values[triu_indices]
    
    pair_count_corr_ge_0_90 = int(np.sum(pearson_vals >= 0.90))
    pair_count_corr_ge_0_95 = int(np.sum(pearson_vals >= 0.95))
    pair_count_corr_ge_0_99 = int(np.sum(pearson_vals >= 0.99))
    
    # 5. Build per-feature JSON results
    logger.info("Building per-feature JSON statistics...")
    results = {}
    for idx, col in enumerate(feature_cols):
        # absolute correlation against all others (exclude diagonal)
        p_row = corr_pearson.iloc[idx].copy()
        p_row.iloc[idx] = np.nan # exclude self
        
        s_row = corr_spearman.iloc[idx].copy()
        s_row.iloc[idx] = np.nan # exclude self
        
        max_p = float(p_row.max()) if pd.notna(p_row.max()) else 0.0
        med_p = float(p_row.median()) if pd.notna(p_row.median()) else 0.0
        
        count_ge_0_90 = int(np.sum(p_row >= 0.90))
        count_ge_0_95 = int(np.sum(p_row >= 0.95))
        count_ge_0_99 = int(np.sum(p_row >= 0.99))
        
        max_s = float(s_row.max()) if pd.notna(s_row.max()) else 0.0
        med_s = float(s_row.median()) if pd.notna(s_row.median()) else 0.0
        
        dups = exact_duplicates.get(col, [])
        
        results[col] = {
            "max_absolute_correlation": max_p,
            "median_absolute_correlation": med_p,
            "count_corr_ge_0_90": count_ge_0_90,
            "count_corr_ge_0_95": count_ge_0_95,
            "count_corr_ge_0_99": count_ge_0_99,
            "max_absolute_spearman": max_s,
            "median_absolute_spearman": med_s,
            "duplicate_feature_count": len(dups),
            "duplicate_feature_names": dups
        }
        
    # 6. Telemetry Group Relationships
    logger.info("Computing telemetry group relationships...")
    groups = {}
    for col in feature_cols:
        gname = get_group_name(col)
        groups[gname] = groups.get(gname, [])
        groups[gname].append(col)
        
    group_relation_stats = {}
    for gname, cols in groups.items():
        # Within-group correlations
        if len(cols) > 1:
            g_sub = corr_pearson.loc[cols, cols].values
            # get upper triangle
            n_g = len(cols)
            g_triu = g_sub[np.triu_indices(n_g, k=1)]
            # filter out nans
            g_triu = g_triu[np.isfinite(g_triu)]
            med_within = float(np.median(g_triu)) if len(g_triu) > 0 else 0.0
        else:
            med_within = 1.0 # only 1 feature
            
        # Cross-group correlations (columns not in cols)
        other_cols = [c for c in feature_cols if c not in cols]
        if other_cols:
            cross_sub = corr_pearson.loc[cols, other_cols].values
            cross_sub = cross_sub[np.isfinite(cross_sub)]
            med_cross = float(np.median(cross_sub)) if len(cross_sub) > 0 else 0.0
        else:
            med_cross = 0.0
            
        group_relation_stats[gname] = {
            "feature_count": len(cols),
            "median_within_group_absolute_corr": med_within,
            "median_cross_group_absolute_corr": med_cross
        }
        
    # Save JSON Report
    logger.info("Saving JSON output...")
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")
    
    # Build Markdown Report
    logger.info("Building Markdown report...")
    md_lines = [
        "# Master Feature Relationship Audit Report",
        "",
        "## 1. Executive Summary",
        "This report audits the Pearson and Spearman correlations, exact duplicates, and group relationship statistics of the master feature table. All metrics represent measured facts only.",
        "",
        "## 2. Table Statistics",
        f"- **Row Count**: {row_count}",
        f"- **Feature Count**: {feature_count}",
        "",
        "## 3. Global Correlation Statistics",
        f"- **Total Feature Count**: {feature_count}",
        f"- **Total Feature Pairs**: {total_pairs}",
        f"- **Feature Pairs with Pearson Correlation >= 0.90**: {pair_count_corr_ge_0_90}",
        f"- **Feature Pairs with Pearson Correlation >= 0.95**: {pair_count_corr_ge_0_95}",
        f"- **Feature Pairs with Pearson Correlation >= 0.99**: {pair_count_corr_ge_0_99}",
        f"- **Exact Duplicate Features Count**: {duplicate_feature_count}",
        ""
    ]
    
    if all_duplicates:
        md_lines.append("**Exact Duplicate Feature Groups Detected**:")
        for idx, item in enumerate(all_duplicates[:5]):
            md_lines.append(f"- Group {idx+1}: `{item['features'][0]}` has {len(item['features'])-1} duplicates: {item['features'][1:5]}")
            if len(item['features']) > 5:
                md_lines.append(f"  - ... and {len(item['features'])-5} more duplicates")
        if len(all_duplicates) > 5:
            md_lines.append(f"- ... and {len(all_duplicates)-5} more duplicate groups")
        md_lines.append("")
        
    md_lines.append("## 4. Telemetry Group Relationship Summary")
    md_lines.append("")
    md_lines.append("| Telemetry Group | Feature Count | Median Within-Group Absolute Corr | Median Cross-Group Absolute Corr |")
    md_lines.append("| --- | --- | --- | --- |")
    
    for gname in sorted(group_relation_stats.keys()):
        stats = group_relation_stats[gname]
        md_lines.append(f"| {gname} | {stats['feature_count']} | {stats['median_within_group_absolute_corr']:.4f} | {stats['median_cross_group_absolute_corr']:.4f} |")
        
    md_lines.append("")
    md_lines.append("## 5. Representative Feature Samples")
    md_lines.append("")
    md_lines.append("| Feature Name | Max Pearson | Median Pearson | Max Spearman | Median Spearman | Duplicates Count | count corr >= 0.90 |")
    md_lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        for c in cols[:2]: # Sample 2 features per group
            r = results[c]
            md_lines.append(f"| `{c}` | {r['max_absolute_correlation']:.4f} | {r['median_absolute_correlation']:.4f} | {r['max_absolute_spearman']:.4f} | {r['median_absolute_spearman']:.4f} | {r['duplicate_feature_count']} | {r['count_corr_ge_0_90']} |")
            
    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines))
    logger.info(f"Saved Markdown report to {OUT_MD}")
    
    # Save statistics for return value
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
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/feature_relationship_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

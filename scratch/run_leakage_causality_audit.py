import os
import gc
import time
import json
import logging
import resource
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
LEAD_LAG_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/lead_lag_relationship_audit.json"
STABILITY_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/feature_stability_audit.json"
INFO_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/information_content_audit.json"
TEMPORAL_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/temporal_dynamics_audit.json"

OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/leakage_causality_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_leakage_causality_audit.md"

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

def classify_feature_type(col):
    types = []
    if "hel1os_czt1_lc" in col or "hel1os_czt2_lc" in col or "hel1os_cdte1_lc" in col or "hel1os_cdte2_lc" in col or "solexs_sdd2_lc" in col:
        types.append("lightcurve")
    if "spec" in col:
        types.append("spectra")
    if "evt" in col or "event" in col:
        types.append("event")
    if "hk" in col or "housekeeping" in col:
        types.append("housekeeping")
    if "gti" in col:
        types.append("gti")
        
    if "counts" in col or "ctr" in col or "lc_counts" in col or "counts_ch" in col or "counts_total" in col or "counts_band" in col or "rate" in col:
        types.append("counts")
    if "stat_err" in col or "err" in col:
        types.append("stat_err")
    if "temp" in col or "temperature" in col:
        types.append("temperature")
    if "volt" in col or "voltage" in col:
        types.append("voltage")
    if "count" in col or "num" in col or "recnum" in col:
        types.append("counter")
    if "time" in col or "clock" in col or "sec" in col or "mjd" in col:
        types.append("timing")
        
    if not types:
        types.append("other")
    return types

def classify_feature_origin(col):
    if "stat_err" in col or "_err" in col:
        return "statistical_error"
    if "gradient" in col or "acceleration" in col or "ratio" in col or "mask" in col:
        return "derived_measurement"
    if "mean" in col or "variance" in col or "peak" in col or "std" in col:
        return "aggregation"
    if "recnum" in col or "source" in col or "satellite" in col or "quality" in col:
        return "metadata"
    if "counts" in col or "ctr" in col or "rate" in col:
        return "raw_measurement"
    return "unknown"

def classify_lead_strength(best_offset):
    if best_offset in ["lead_360m", "lead_180m", "lead_120m"]:
        return "strong_lead"
    elif best_offset in ["lead_60m", "lead_30m"]:
        return "moderate_lead"
    elif best_offset in ["lead_15m", "lead_5m"]:
        return "weak_lead"
    elif best_offset == "lag_0m":
        return "contemporaneous"
    return "unknown"

def detect_hk_leakage_flags(col):
    flags = []
    for flag in ["temp", "volt", "curr", "counter", "recnum", "time", "clock", "orbit", "hk"]:
        if flag in col.lower():
            flags.append(flag)
    return flags

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()
    logger.info(f"Initial Memory Usage: {initial_mem:.2f} MB")

    # Verify parquet columns
    logger.info("Loading master feature table schema...")
    import pyarrow.parquet as pq
    pq_file = pq.ParquetFile(MASTER_PARQUET)
    all_features = [col for col in pq_file.schema.names if col != "timestamp"]
    feature_set = set(all_features)
    logger.info(f"Master feature table has {len(all_features)} features")

    # Load lead-lag audit results
    logger.info(f"Loading lead-lag audit from {LEAD_LAG_JSON}...")
    with open(LEAD_LAG_JSON, "r") as f:
        lead_lag_data = json.load(f)
    lead_lag_results = lead_lag_data["feature_lead_lag_audit"]

    # Load stability audit
    logger.info(f"Loading stability audit from {STABILITY_JSON}...")
    with open(STABILITY_JSON, "r") as f:
        stability_data = json.load(f)

    # Load information content audit
    logger.info(f"Loading information content audit from {INFO_JSON}...")
    with open(INFO_JSON, "r") as f:
        info_data = json.load(f)

    # Load temporal dynamics audit
    logger.info(f"Loading temporal dynamics audit from {TEMPORAL_JSON}...")
    with open(TEMPORAL_JSON, "r") as f:
        temporal_data = json.load(f)

    # Compute exact ranks for all features
    logger.info("Ranking features...")
    # Filter features that are in our master feature table
    valid_lead_lag = {k: v for k, v in lead_lag_results.items() if k in feature_set}
    
    sorted_by_corr = sorted(valid_lead_lag.keys(), key=lambda x: valid_lead_lag[x]["max_abs_corr"] if valid_lead_lag[x]["max_abs_corr"] is not None else -1.0, reverse=True)
    corr_ranks = {feat: idx + 1 for idx, feat in enumerate(sorted_by_corr)}

    sorted_by_mi = sorted(valid_lead_lag.keys(), key=lambda x: valid_lead_lag[x]["max_mutual_information"] if valid_lead_lag[x]["max_mutual_information"] is not None else -1.0, reverse=True)
    mi_ranks = {feat: idx + 1 for idx, feat in enumerate(sorted_by_mi)}

    # Candidate pool: Top 100 corr + Top 100 MI
    top_corr_set = set(sorted_by_corr[:100])
    top_mi_set = set(sorted_by_mi[:100])
    candidate_pool = sorted(list(top_corr_set.union(top_mi_set)))
    audited_count = len(candidate_pool)
    logger.info(f"Candidate pool size: {audited_count} features (Top 100 Corr: {len(top_corr_set)}, Top 100 MI: {len(top_mi_set)})")

    # Perform audit for each candidate
    audited_features = {}
    
    for feat in candidate_pool:
        # Determine metadata
        gname = get_target_group_name(feat)
        source_instr = "solexs" if "solexs" in feat else "hel1os"
        
        ftypes = classify_feature_type(feat)
        forig = classify_feature_origin(feat)
        
        ll_metrics = lead_lag_results[feat]
        best_offset = ll_metrics["offset_of_max_corr"]
        best_mi_offset = ll_metrics["offset_of_max_mi"]
        max_corr = ll_metrics["max_abs_corr"]
        max_mi = ll_metrics["max_mutual_information"]
        
        lstrength = classify_lead_strength(best_offset)
        
        # Load from stability audit
        stab = stability_data.get(feat, {})
        missing_pct = stab.get("missing_percentage", 0.0)
        
        # Load from info audit
        inf = info_data.get(feat, {})
        entropy = inf.get("entropy", 0.0)
        unique_cnt = inf.get("unique_value_count", 0)
        
        # Load from temporal audit
        temp_d = temporal_data.get(feat, {})
        lag1 = temp_d.get("lag1_autocorrelation", 0.0)
        lag60 = temp_d.get("lag60_autocorrelation", 0.0)
        
        # Housekeeping flags
        hk_flags = []
        if "housekeeping" in ftypes:
            hk_flags = detect_hk_leakage_flags(feat)
            
        audited_features[feat] = {
            "telemetry_group": gname,
            "source_instrument": source_instr,
            "corr_rank": corr_ranks[feat],
            "mi_rank": mi_ranks[feat],
            "feature_origin": forig,
            "lead_strength": lstrength,
            "feature_types": ftypes,
            "missing_percentage": missing_pct,
            "entropy": entropy,
            "unique_value_count": unique_cnt,
            "lag1_autocorrelation": lag1,
            "lag60_autocorrelation": lag60,
            "max_abs_corr": max_corr,
            "best_correlation_offset": best_offset,
            "max_mutual_information": max_mi,
            "best_mi_offset": best_mi_offset,
            "housekeeping_leakage_flags": hk_flags
        }

    # Group Summaries
    logger.info("Computing group summaries...")
    group_summaries = {}
    
    # Organize by group
    group_feats = {}
    for feat in candidate_pool:
        gname = audited_features[feat]["telemetry_group"]
        group_feats[gname] = group_feats.get(gname, []) + [feat]
        
    for gname, cols in group_feats.items():
        all_corrs = [audited_features[c]["max_abs_corr"] for c in cols if audited_features[c]["max_abs_corr"] is not None]
        all_mis = [audited_features[c]["max_mutual_information"] for c in cols if audited_features[c]["max_mutual_information"] is not None]
        
        # Offset distribution
        offset_dist = {}
        for c in cols:
            offset = audited_features[c]["best_correlation_offset"]
            if offset:
                offset_dist[offset] = offset_dist.get(offset, 0) + 1
                
        # Feature type distribution
        ftype_dist = {}
        for c in cols:
            for t in audited_features[c]["feature_types"]:
                ftype_dist[t] = ftype_dist.get(t, 0) + 1
                
        # Feature origin distribution
        forig_dist = {}
        for c in cols:
            o = audited_features[c]["feature_origin"]
            forig_dist[o] = forig_dist.get(o, 0) + 1
            
        group_summaries[gname] = {
            "feature_count": len(cols),
            "median_corr": float(np.median(all_corrs)) if all_corrs else 0.0,
            "max_corr": float(np.max(all_corrs)) if all_corrs else 0.0,
            "median_mi": float(np.median(all_mis)) if all_mis else 0.0,
            "max_mi": float(np.max(all_mis)) if all_mis else 0.0,
            "offset_distribution": offset_dist,
            "feature_type_distribution": ftype_dist,
            "feature_origin_distribution": forig_dist
        }

    # Generate category counts
    category_counts = {}
    for feat in candidate_pool:
        for t in audited_features[feat]["feature_types"]:
            category_counts[t] = category_counts.get(t, 0) + 1

    # Housekeeping leakage review data
    hk_review = []
    for feat in candidate_pool:
        aud = audited_features[feat]
        if "housekeeping" in aud["feature_types"]:
            hk_review.append({
                "feature_name": feat,
                "max_abs_corr": aud["max_abs_corr"],
                "max_mutual_information": aud["max_mutual_information"],
                "best_offset": aud["best_correlation_offset"],
                "flags_detected": aud["housekeeping_leakage_flags"]
            })

    # Save JSON Report
    logger.info("Saving JSON output...")
    output_dict = {
        "audited_features": audited_features,
        "group_summaries": group_summaries,
        "category_counts": category_counts,
        "housekeeping_leakage_review": hk_review
    }
    with open(OUT_JSON, "w") as f:
        json.dump(output_dict, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")

    # Build Markdown Report
    logger.info("Building Markdown report...")
    
    md_lines = [
        "# Leakage and Causality Audit Report",
        "",
        "## 1. Executive Summary",
        "This report performs a descriptive analysis of the strongest Aditya-L1 features to identify whether their relationships with solar flare forecasting targets represent physical signals, derived patterns, or leakage of metadata/housekeeping parameters.",
        "",
        "## 2. Table Statistics",
        f"- **Audited Feature Count**: {audited_count}",
        "",
        "## 3. Telemetry Group Relationship Summary",
        "",
        "| Telemetry Group | Feature Count | Median Corr | Max Corr | Median MI | Max MI | Offset Distribution | Origin Distribution |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |"
    ]

    for gname in sorted(group_summaries.keys()):
        stats = group_summaries[gname]
        offset_str = ", ".join([f"{k.split('_')[-1]}:{v}" for k, v in stats['offset_distribution'].items()])
        orig_str = ", ".join([f"{k}:{v}" for k, v in stats['feature_origin_distribution'].items()])
        md_lines.append(f"| {gname} | {stats['feature_count']} | {stats['median_corr']:.4f} | {stats['max_corr']:.4f} | {stats['median_mi']:.4f} | {stats['max_mi']:.4f} | {offset_str} | {orig_str} |")

    # Lead strength distribution
    lead_strength_counts = {"strong_lead": 0, "moderate_lead": 0, "weak_lead": 0, "contemporaneous": 0}
    for feat in candidate_pool:
        ls = audited_features[feat]["lead_strength"]
        if ls in lead_strength_counts:
            lead_strength_counts[ls] += 1
            
    md_lines.extend([
        "",
        "## 4. Lead Strength Classification Distribution",
        "",
        f"- **Strong Lead (offset >= 120m)**: {lead_strength_counts['strong_lead']} features",
        f"- **Moderate Lead (30m - 119m)**: {lead_strength_counts['moderate_lead']} features",
        f"- **Weak Lead (< 30m)**: {lead_strength_counts['weak_lead']} features",
        f"- **Contemporaneous (offset = 0m)**: {lead_strength_counts['contemporaneous']} features",
        ""
    ])

    # Housekeeping Leakage Review Section
    md_lines.extend([
        "",
        "## 5. Housekeeping Leakage Review",
        "",
        "This section audits all housekeeping features present in the candidate pool. Housekeeping data often records operational parameters that are highly correlated with flare events but do not represent physical solar signals.",
        "",
        "| Feature Name | Max Abs Corr | Max MI | Best Offset | Flags Detected |",
        "| --- | --- | --- | --- | --- |"
    ])

    for hk in sorted(hk_review, key=lambda x: x['max_abs_corr'] if x['max_abs_corr'] is not None else -1.0, reverse=True):
        flags_str = ", ".join(hk["flags_detected"])
        offset_str = hk["best_offset"] if hk["best_offset"] else "None"
        md_lines.append(f"| `{hk['feature_name']}` | {hk['max_abs_corr']:.4f} | {hk['max_mutual_information']:.4f} | {offset_str} | {flags_str} |")

    # Feature Samples
    md_lines.extend([
        "",
        "## 6. Representative Feature Samples (Audited Pool)",
        "",
        "Below are samples of representative features from different origins showing their statistical profiles:",
        "",
        "| Feature Name | Telemetry Group | Origin | Lead Strength | Corr Rank | MI Rank | Corr | MI | Lag-1 Autocorr | Entropy | Unique Values |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    ])

    # Sample 1 feature of each origin
    origins_seen = set()
    for feat in candidate_pool:
        aud = audited_features[feat]
        orig = aud["feature_origin"]
        if orig not in origins_seen:
            origins_seen.add(orig)
            corr_val = aud["max_abs_corr"]
            mi_val = aud["max_mutual_information"]
            lag1_val = aud["lag1_autocorrelation"]
            ent_val = aud["entropy"]
            
            corr_str = f"{corr_val:.4f}" if corr_val is not None else "NaN"
            mi_str = f"{mi_val:.4f}" if mi_val is not None else "NaN"
            lag1_str = f"{lag1_val:.4f}" if lag1_val is not None else "NaN"
            ent_str = f"{ent_val:.4f}" if ent_val is not None else "NaN"
            
            md_lines.append(f"| `{feat}` | {aud['telemetry_group']} | {orig} | {aud['lead_strength']} | {aud['corr_rank']} | {aud['mi_rank']} | {corr_str} | {mi_str} | {lag1_str} | {ent_str} | {aud['unique_value_count']} |")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines))
    logger.info(f"Saved Markdown report to {OUT_MD}")

    # Track metrics
    duration = time.time() - start_time
    final_mem = get_memory_use_mb()
    
    summary_stats = {
        "files_created": [OUT_JSON, OUT_MD],
        "audited_feature_count": audited_count,
        "runtime_s": duration,
        "initial_mem_mb": initial_mem,
        "peak_mem_mb": final_mem,
        "final_mem_mb": final_mem
    }
    
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/leakage_causality_runtime_stats.json", "w") as f:
        json.dump(summary_stats, f, indent=2)
    print("FINISHED")

if __name__ == "__main__":
    main()

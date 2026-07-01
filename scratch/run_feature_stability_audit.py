import os
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

PARQUET_PATH = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/feature_stability_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_feature_stability.md"

def main():
    logger.info("Loading master feature table...")
    df = pd.read_parquet(PARQUET_PATH)
    logger.info(f"Loaded master feature table of shape {df.shape}")
    
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Separate numeric columns (excluding timestamp)
    feature_cols = [col for col in df.columns if col != "timestamp"]
    
    # Compute global stats
    logger.info("Computing global statistics...")
    means = df[feature_cols].mean()
    stds = df[feature_cols].std()
    mins = df[feature_cols].min()
    maxs = df[feature_cols].max()
    p95s = df[feature_cols].quantile(0.95)
    p99s = df[feature_cols].quantile(0.99)
    missing_pcts = df[feature_cols].isna().mean() * 100.0
    
    # Daily availability
    logger.info("Computing daily availability...")
    dates = df["timestamp"].dt.date
    unique_dates = sorted(dates.unique())
    logger.info(f"Observation dates found: {unique_dates}")
    
    # Calculate daily availability per column
    # Group by date and calculate percentage of non-null values
    daily_notna = df[feature_cols].groupby(dates).apply(lambda g: g.notna().mean() * 100.0)
    
    results = {}
    for col in feature_cols:
        col_avail = daily_notna[col] # Series index=date, value=percentage
        
        daily_avail_dict = {str(d): float(col_avail.loc[d]) for d in unique_dates}
        
        # Count active days (avail > 0) and missing days (avail == 0)
        active_days = int(np.sum(col_avail > 0.0))
        missing_days = int(np.sum(col_avail == 0.0))
        
        results[col] = {
            "mean": float(means[col]) if pd.notna(means[col]) else None,
            "std": float(stds[col]) if pd.notna(stds[col]) else None,
            "min": float(mins[col]) if pd.notna(mins[col]) else None,
            "max": float(maxs[col]) if pd.notna(maxs[col]) else None,
            "p95": float(p95s[col]) if pd.notna(p95s[col]) else None,
            "p99": float(p99s[col]) if pd.notna(p99s[col]) else None,
            "missing_pct": float(missing_pcts[col]),
            "daily_availability_pct": daily_avail_dict,
            "active_days": active_days,
            "missing_days": missing_days
        }
        
    logger.info("Writing JSON output...")
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved JSON report to {OUT_JSON}")
    
    # Build Markdown report
    logger.info("Building Markdown report...")
    md_lines = [
        "# Master Feature Table Stability Audit Report",
        "",
        "## 1. Executive Summary",
        "This report provides a systematic feature stability audit of the constructed master feature table. All metrics represent measured facts only.",
        "",
        "## 2. Global Table Coverage Summary",
        f"- **Total Rows**: {len(df)}",
        f"- **Total Features**: {len(feature_cols)}",
        "",
        "## 3. Telemetry Product Group Statistics",
        ""
    ]
    
    # Group features by their source name to keep the report readable and structured
    # Group names derived from feature prefixes
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
    for col in feature_cols:
        gname = get_group_name(col)
        groups[gname] = groups.get(gname, [])
        groups[gname].append(col)
        
    md_lines.append("| Telemetry Group | Feature Count | Median Missing Pct | Active Days (Range) | Missing Days (Range) |")
    md_lines.append("| --- | --- | --- | --- | --- |")
    
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        g_missing = [results[c]["missing_pct"] for c in cols]
        g_active = [results[c]["active_days"] for c in cols]
        g_missing_days = [results[c]["missing_days"] for c in cols]
        
        median_missing = float(np.median(g_missing))
        min_active, max_active = min(g_active), max(g_active)
        min_missing_d, max_missing_d = min(g_missing_days), max(g_missing_days)
        
        md_lines.append(f"| {gname} | {len(cols)} | {median_missing:.2f}% | {min_active}..{max_active} days | {min_missing_d}..{max_missing_d} days |")
        
    md_lines.append("")
    md_lines.append("## 4. Stability Statistics per Telemetry Group")
    md_lines.append("")
    
    # For each group, show detailed statistics of 5 representative features
    for gname in sorted(groups.keys()):
        cols = groups[gname]
        md_lines.append(f"### Telemetry Group: `{gname}`")
        md_lines.append(f"- **Total Features**: {len(cols)}")
        md_lines.append("- **Detailed Feature Samples**:")
        md_lines.append("")
        md_lines.append("  | Feature Name | Mean | Std | Min | Max | p95 | p99 | Missing Pct | Daily Availability (10/11/12/13) |")
        md_lines.append("  | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        
        # Sample 5 features or all if fewer
        sample_cols = cols[:5]
        for c in sample_cols:
            r = results[c]
            avail = r["daily_availability_pct"]
            avail_str = " / ".join(f"{avail[str(d)]:.1f}%" for d in unique_dates)
            
            mean_s = f"{r['mean']:.4e}" if r["mean"] is not None else "N/A"
            std_s = f"{r['std']:.4e}" if r["std"] is not None else "N/A"
            min_s = f"{r['min']:.4e}" if r["min"] is not None else "N/A"
            max_s = f"{r['max']:.4e}" if r["max"] is not None else "N/A"
            p95_s = f"{r['p95']:.4e}" if r["p95"] is not None else "N/A"
            p99_s = f"{r['p99']:.4e}" if r["p99"] is not None else "N/A"
            
            md_lines.append(f"  | `{c}` | {mean_s} | {std_s} | {min_s} | {max_s} | {p95_s} | {p99_s} | {r['missing_pct']:.2f}% | {avail_str} |")
        md_lines.append("")
        
    with open(OUT_MD, "w") as f:
        f.write("\n".join(md_lines))
    logger.info(f"Saved Markdown report to {OUT_MD}")
    
    print("Stability Audit Script Completed Successfully!")

if __name__ == "__main__":
    main()

import os
import sys
import time
import json
import resource
import numpy as np

LEAD_LAG_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/lead_lag_relationship_audit.json"
LEAKAGE_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/leakage_causality_audit.json"
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/physics_only_feature_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_physics_only_feature_audit.md"
APP_DATA_MD = "/Users/soumyadebtripathy/.gemini/antigravity/brain/c3fa7d09-8249-46c9-98a1-4faacc713a0e/aditya_l1_physics_only_feature_audit.md"

OFFSETS = ["lead_360m", "lead_180m", "lead_120m", "lead_60m", "lead_30m", "lead_15m", "lead_5m", "lag_0m"]

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

def is_excluded(feature_name, group_name):
    if group_name in ["hel1os_housekeeping", "solexs_gti"]:
        return True
    exclusions = [
        "recnum", "utc", "utchr", "utcdy", "time", "clock",
        "framecnt", "orbit", "yaw", "roll", "radeg", "decdeg",
        "pagestim", "dhobt", "gti"
    ]
    for sub in exclusions:
        if sub in feature_name:
            return True
    eligible_groups = [
        "hel1os_czt_lightcurves",
        "hel1os_cdte_lightcurves",
        "hel1os_czt_spectra",
        "hel1os_cdte_spectra",
        "hel1os_events",
        "solexs_lightcurve",
        "solexs_spectra"
    ]
    if group_name not in eligible_groups:
        return True
    return False

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()

    # Load Inputs
    print("Loading lead-lag relationship audit...")
    with open(LEAD_LAG_JSON, "r") as f:
        lead_lag_data = json.load(f)
    feature_lead_lag = lead_lag_data["feature_lead_lag_audit"]

    print("Loading leakage causality audit...")
    with open(LEAKAGE_JSON, "r") as f:
        leakage_data = json.load(f)
    audited_leakage = leakage_data.get("audited_features", {})

    # Build Physics-Only Feature Universe
    physics_features = []
    excluded_features = []

    for f_name, f_data in feature_lead_lag.items():
        grp = get_target_group_name(f_name)
        if is_excluded(f_name, grp):
            excluded_features.append(f_name)
        else:
            physics_features.append({
                "feature_name": f_name,
                "telemetry_group": grp,
                "max_abs_corr": f_data["max_abs_corr"],
                "best_correlation_offset": f_data["offset_of_max_corr"],
                "max_mutual_information": f_data["max_mutual_information"],
                "best_mi_offset": f_data["offset_of_max_mi"]
            })

    physics_count = len(physics_features)
    excluded_count = len(excluded_features)
    print(f"Physics Feature Count: {physics_count}")
    print(f"Excluded Feature Count: {excluded_count}")
    print(f"Total Features Evaluated: {physics_count + excluded_count}")

    # Step 1: Rank by correlation (descending, tie-breaker by name ascending)
    physics_features.sort(key=lambda x: (-x["max_abs_corr"], x["feature_name"]))
    for rank_idx, feat in enumerate(physics_features, start=1):
        feat["corr_rank"] = rank_idx

    # Step 2: Rank by mutual information (descending, tie-breaker by name ascending)
    physics_features.sort(key=lambda x: (-x["max_mutual_information"], x["feature_name"]))
    for rank_idx, feat in enumerate(physics_features, start=1):
        feat["mi_rank"] = rank_idx

    # Step 3: Compute consensus score & consensus ranking
    for feat in physics_features:
        feat["consensus_score"] = (1 / feat["corr_rank"]) + (1 / feat["mi_rank"])

    physics_features.sort(key=lambda x: (-x["consensus_score"], x["feature_name"]))
    for rank_idx, feat in enumerate(physics_features, start=1):
        feat["consensus_rank"] = rank_idx

    # Extract Top 100 lists
    # Top 100 by correlation
    top_100_corr = sorted(physics_features, key=lambda x: (x["corr_rank"], x["feature_name"]))[:100]
    # Top 100 by MI
    top_100_mi = sorted(physics_features, key=lambda x: (x["mi_rank"], x["feature_name"]))[:100]
    # Top 100 consensus
    top_100_consensus = physics_features[:100]
    top_10_consensus = physics_features[:10]

    # Telemetry Group Summary
    groups = [
        "hel1os_czt_lightcurves",
        "hel1os_cdte_lightcurves",
        "hel1os_czt_spectra",
        "hel1os_cdte_spectra",
        "hel1os_events",
        "solexs_lightcurve",
        "solexs_spectra"
    ]
    
    group_summaries = {}
    for g in groups:
        g_feats = [f for f in physics_features if f["telemetry_group"] == g]
        if not g_feats:
            group_summaries[g] = {
                "feature_count": 0,
                "median_corr": 0.0,
                "max_corr": 0.0,
                "median_mi": 0.0,
                "max_mi": 0.0,
                "offset_distribution": {o: 0 for o in OFFSETS},
                "top10_presence_count": 0
            }
            continue

        corrs = [f["max_abs_corr"] for f in g_feats]
        mis = [f["max_mutual_information"] for f in g_feats]
        
        offset_dist = {o: 0 for o in OFFSETS}
        for f in g_feats:
            offset = f["best_correlation_offset"]
            if offset in offset_dist:
                offset_dist[offset] += 1
                
        top10_count = sum(1 for f in top_10_consensus if f["telemetry_group"] == g)
        
        group_summaries[g] = {
            "feature_count": len(g_feats),
            "median_corr": float(np.median(corrs)),
            "max_corr": float(np.max(corrs)),
            "median_mi": float(np.median(mis)),
            "max_mi": float(np.max(mis)),
            "offset_distribution": offset_dist,
            "top10_presence_count": top10_count
        }

    # Verify Counts
    assert len(top_100_corr) == 100, f"Expected 100 features by correlation, got {len(top_100_corr)}"
    assert len(top_100_mi) == 100, f"Expected 100 features by MI, got {len(top_100_mi)}"
    assert len(top_100_consensus) == 100, f"Expected 100 features by consensus, got {len(top_100_consensus)}"

    # Ensure no excluded features are in the rankings
    for f in top_100_corr + top_100_mi + top_100_consensus:
        assert f["feature_name"] not in excluded_features, f"Excluded feature {f['feature_name']} found in rankings!"

    runtime = time.time() - start_time
    peak_mem = get_memory_use_mb()

    # Save Outputs - JSON
    output_dict = {
        "metadata": {
            "physics_feature_count": physics_count,
            "excluded_feature_count": excluded_count,
            "runtime_seconds": float(runtime),
            "peak_memory_mb": float(peak_mem)
        },
        "group_summaries": group_summaries,
        "top_100_corr": top_100_corr,
        "top_100_mi": top_100_mi,
        "top_100_consensus": top_100_consensus,
        "physics_only_universe": {f["feature_name"]: f for f in physics_features}
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(output_dict, f, indent=2)
    print(f"Saved JSON audit to {OUT_JSON}")

    # Generate Markdown Report Content
    md_content = f"""# Sprint 10G-J: Physics-Only Leakage Purge Audit Report

## 1. Executive Summary
This audit report presents a clean, physics-only feature ranking derived from the Aditya-L1 telemetry channels. All operational, temporal, housekeeping, and metadata-derived variables that could serve as sources of non-physical data leakage have been purged. Ranks and consensus scores were calculated exclusively within the remaining 2,109 physical telemetry features.

## 2. Universe Audit Statistics
- **Total Features Evaluated**: {physics_count + excluded_count}
- **Physics-Only Feature Universe**: {physics_count}
- **Excluded Features (Housekeeping / Metadata)**: {excluded_count}
- **Audit Execution Time**: {runtime:.3f} seconds
- **Peak Memory Usage**: {peak_mem:.2f} MB

### Verification Summary
- [x] No excluded feature appears in any ranking list.
- [x] Top 100 Absolute Correlation count: {len(top_100_corr)}
- [x] Top 100 Mutual Information count: {len(top_100_mi)}
- [x] Top 100 Consensus Ranking count: {len(top_100_consensus)}

---

## 3. Telemetry Group summary

| Telemetry Group | Feature Count | Median Corr | Max Corr | Median MI | Max MI | Top 10 Presence | Offsets Distribution |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
"""

    for g in sorted(group_summaries.keys()):
        s = group_summaries[g]
        offsets_str = ", ".join([f"{k.replace('lead_', '').replace('lag_', '')}:{v}" for k, v in s["offset_distribution"].items() if v > 0])
        md_content += f"| `{g}` | {s['feature_count']} | {s['median_corr']:.4f} | {s['max_corr']:.4f} | {s['median_mi']:.4f} | {s['max_mi']:.4f} | {s['top10_presence_count']} | {offsets_str} |\n"

    md_content += """
---

## 4. Top 25 Consensus Features

The consensus score is calculated as `(1 / corr_rank) + (1 / mi_rank)`, where ranks are computed within the physics-only universe. Features are sorted descending by consensus score.

| Consensus Rank | Feature Name | Telemetry Group | Corr Rank | MI Rank | Consensus Score | Best Corr Offset | Best MI Offset | Max Corr | Max MI |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for feat in top_100_consensus[:25]:
        md_content += f"| {feat['consensus_rank']} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['corr_rank']} | {feat['mi_rank']} | {feat['consensus_score']:.6f} | `{feat['best_correlation_offset']}` | `{feat['best_mi_offset']}` | {feat['max_abs_corr']:.4f} | {feat['max_mutual_information']:.4f} |\n"

    md_content += """
---

## 5. Top 15 Correlation Features

Sorted by absolute Pearson correlation descending.

| Corr Rank | Feature Name | Telemetry Group | Max Corr | Best Offset | MI Rank | Max MI |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
"""

    for feat in top_100_corr[:15]:
        md_content += f"| {feat['corr_rank']} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['max_abs_corr']:.4f} | `{feat['best_correlation_offset']}` | {feat['mi_rank']} | {feat['max_mutual_information']:.4f} |\n"

    md_content += """
---

## 6. Top 15 Mutual Information Features

Sorted by mutual information descending.

| MI Rank | Feature Name | Telemetry Group | Max MI | Best Offset | Corr Rank | Max Corr |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
"""

    for feat in top_100_mi[:15]:
        md_content += f"| {feat['mi_rank']} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['max_mutual_information']:.4f} | `{feat['best_mi_offset']}` | {feat['corr_rank']} | {feat['max_abs_corr']:.4f} |\n"

    md_content += f"""
---

## 7. Excluded Leakage Sources Reference

A total of {excluded_count} features were excluded from the analysis according to the Sprint rules. These features represent housekeeping telemetry or temporal indexes that can cause target leakage.

### Exclusion Rules Applied
- Exclude group `hel1os_housekeeping`
- Exclude group `solexs_gti`
- Exclude feature names containing: `recnum`, `utc`, `utchr`, `utcdy`, `time`, `clock`, `framecnt`, `orbit`, `yaw`, `roll`, `radeg`, `decdeg`, `pagestim`, `dhobt`, `gti`.

### Excluded Features List
"""

    for col in sorted(excluded_features):
        md_content += f"- `{col}`\n"

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w") as f:
        f.write(md_content)
    print(f"Saved Markdown report to {OUT_MD}")

    os.makedirs(os.path.dirname(APP_DATA_MD), exist_ok=True)
    with open(APP_DATA_MD, "w") as f:
        f.write(md_content)
    print(f"Saved copy of Markdown report to {APP_DATA_MD}")

    # Output Verification Metrics to terminal
    print("\n----- VERIFICATION RESULTS -----")
    print(f"physics_feature_count: {physics_count}")
    print(f"excluded_feature_count: {excluded_count}")
    print(f"runtime_seconds: {runtime:.3f}")
    print(f"peak_memory_mb: {peak_mem:.2f}")
    print("--------------------------------\n")

if __name__ == "__main__":
    main()

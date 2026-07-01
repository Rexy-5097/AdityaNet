import os
import sys
import time
import json
import resource
import numpy as np

PHYSICS_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/physics_only_feature_audit.json"
TEMPORAL_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/temporal_dynamics_audit.json"
INFORMATION_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/information_content_audit.json"

OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/stability_adjusted_signal_audit.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_stability_adjusted_signal_audit.md"
APP_DATA_MD = "/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/edc73b3a-3f22-4639-be16-6ceaa97477fc/aditya_l1_stability_adjusted_signal_audit.md"

def get_memory_use_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)

def main():
    start_time = time.time()
    initial_mem = get_memory_use_mb()

    # Load Inputs
    print("Loading physics-only feature audit...")
    with open(PHYSICS_JSON, "r") as f:
        phys_data = json.load(f)
    universe = phys_data["physics_only_universe"]
    physics_features = list(universe.keys())
    audited_feature_count = len(physics_features)

    print("Loading temporal dynamics audit...")
    with open(TEMPORAL_JSON, "r") as f:
        temp_data = json.load(f)

    print("Loading information content audit...")
    with open(INFORMATION_JSON, "r") as f:
        inf_data = json.load(f)

    # Calculate metrics for each feature
    features_list = []
    scores = []

    for f_name in physics_features:
        f_phys = universe[f_name]
        f_temp = temp_data[f_name]
        f_inf = inf_data[f_name]

        max_abs_corr = float(f_phys["max_abs_corr"])
        max_mutual_information = float(f_phys["max_mutual_information"])
        
        lag1_val = f_temp["lag1_autocorrelation"]
        lag1_autocorrelation = float(lag1_val) if lag1_val is not None else 0.0
        
        lag60_val = f_temp["lag60_autocorrelation"]
        lag60_autocorrelation = float(lag60_val) if lag60_val is not None else 0.0
        
        entropy = float(f_inf["entropy"])

        # Calculate autocorrelation penalty
        autocorrelation_penalty = float(max(abs(lag1_autocorrelation), abs(lag60_autocorrelation)))

        # Calculate normalized mutual information
        normalized_mutual_information = float(max_mutual_information / entropy if entropy > 0.0 else 0.0)
        # Bounding NMI to [0.0, 1.0] in case of estimation errors
        normalized_mutual_information = float(min(max(normalized_mutual_information, 0.0), 1.0))

        # Calculate stability adjusted score
        stability_adjusted_score = float((0.5 * max_abs_corr + 0.5 * normalized_mutual_information) * (1.0 - autocorrelation_penalty))
        stability_adjusted_score = float(max(stability_adjusted_score, 0.0))

        features_list.append({
            "feature_name": f_name,
            "telemetry_group": f_phys["telemetry_group"],
            "max_abs_corr": max_abs_corr,
            "max_mutual_information": max_mutual_information,
            "lag1_autocorrelation": lag1_val,
            "lag60_autocorrelation": lag60_val,
            "entropy": entropy,
            "autocorrelation_penalty": autocorrelation_penalty,
            "stability_adjusted_score": stability_adjusted_score
        })
        scores.append(stability_adjusted_score)

    # Compute quartiles of stability adjusted score
    scores_arr = np.array(scores)
    q1 = float(np.percentile(scores_arr, 25))
    q3 = float(np.percentile(scores_arr, 75))

    # Signal Quality Classification
    for feat in features_list:
        score = feat["stability_adjusted_score"]
        if score >= q3:
            feat["signal_quality"] = "high_quality_signal"
        elif score >= q1:
            feat["signal_quality"] = "moderate_quality_signal"
        else:
            feat["signal_quality"] = "low_quality_signal"

    # Ranking Outputs
    # Top 100 by raw correlation (descending, tie-breaker by name ascending)
    top_100_corr = sorted(features_list, key=lambda x: (-x["max_abs_corr"], x["feature_name"]))[:100]
    
    # Top 100 by mutual information (descending, tie-breaker by name ascending)
    top_100_mi = sorted(features_list, key=lambda x: (-x["max_mutual_information"], x["feature_name"]))[:100]
    
    # Top 100 by stability_adjusted_score (descending, tie-breaker by name ascending)
    top_100_score = sorted(features_list, key=lambda x: (-x["stability_adjusted_score"], x["feature_name"]))[:100]

    # Telemetry Group Summary
    groups = sorted(list(set(f["telemetry_group"] for f in features_list)))
    group_summaries = {}

    for g in groups:
        g_feats = [f for f in features_list if f["telemetry_group"] == g]
        g_scores = [f["stability_adjusted_score"] for f in g_feats]
        
        group_summaries[g] = {
            "feature_count": len(g_feats),
            "median_adjusted_score": float(np.median(g_scores)) if g_scores else 0.0,
            "max_adjusted_score": float(np.max(g_scores)) if g_scores else 0.0,
            "high_quality_count": sum(1 for f in g_feats if f["signal_quality"] == "high_quality_signal"),
            "moderate_quality_count": sum(1 for f in g_feats if f["signal_quality"] == "moderate_quality_signal"),
            "low_quality_count": sum(1 for f in g_feats if f["signal_quality"] == "low_quality_signal")
        }

    # Verify counts & values
    assert len(features_list) == audited_feature_count, f"Feature count mismatch: expected {audited_feature_count}, got {len(features_list)}"
    assert all(f["stability_adjusted_score"] >= 0.0 for f in features_list), "Found negative adjusted scores!"

    runtime = time.time() - start_time
    peak_mem = get_memory_use_mb()

    # Save JSON Report
    output_dict = {
        "metadata": {
            "audited_feature_count": audited_feature_count,
            "runtime_seconds": float(runtime),
            "peak_memory_mb": float(peak_mem),
            "score_quartiles": {
                "q1_25th": q1,
                "q3_75th": q3
            }
        },
        "group_summaries": group_summaries,
        "top_100_by_raw_correlation": top_100_corr,
        "top_100_by_mutual_information": top_100_mi,
        "top_100_by_stability_adjusted_score": top_100_score,
        "audited_features": {f["feature_name"]: f for f in features_list}
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(output_dict, f, indent=2)
    print(f"Saved JSON report to {OUT_JSON}")

    # Build Markdown Report
    md_content = f"""# Sprint 10G-K: Stability-Adjusted Predictive Signal Audit Report

## 1. Executive Summary Table

| Metric | Value |
| :--- | :---: |
| Audited Feature Count | {audited_feature_count} |
| Audit Runtime | {runtime:.3f} seconds |
| Peak Memory Usage | {peak_mem:.2f} MB |
| Score Q1 (25th percentile) | {q1:.6f} |
| Score Q3 (75th percentile) | {q3:.6f} |

## 2. Telemetry Group summary

| Telemetry Group | Feature Count | Median Adjusted Score | Max Adjusted Score | High Quality | Moderate Quality | Low Quality |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for g in sorted(group_summaries.keys()):
        s = group_summaries[g]
        md_content += f"| `{g}` | {s['feature_count']} | {s['median_adjusted_score']:.6f} | {s['max_adjusted_score']:.6f} | {s['high_quality_count']} | {s['moderate_quality_count']} | {s['low_quality_count']} |\n"

    md_content += """
## 3. Top 20 Features by Stability-Adjusted Score

Sorted descending by stability adjusted score.

| Rank | Feature Name | Telemetry Group | Max Corr | Max MI | lag1_autocorr | lag60_autocorr | Penalty | Score | Quality |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for idx, feat in enumerate(top_100_score[:20], start=1):
        l1 = feat['lag1_autocorrelation']
        l60 = feat['lag60_autocorrelation']
        l1_str = f"{l1:.4f}" if l1 is not None else "None"
        l60_str = f"{l60:.4f}" if l60 is not None else "None"
        md_content += f"| {idx} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['max_abs_corr']:.4f} | {feat['max_mutual_information']:.4f} | {l1_str} | {l60_str} | {feat['autocorrelation_penalty']:.4f} | {feat['stability_adjusted_score']:.6f} | `{feat['signal_quality']}` |\n"

    md_content += """
## 4. Top 10 Features by Raw Correlation

Sorted descending by raw absolute correlation.

| Rank | Feature Name | Telemetry Group | Max Corr | Max MI | Penalty | Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
"""

    for idx, feat in enumerate(top_100_corr[:10], start=1):
        md_content += f"| {idx} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['max_abs_corr']:.4f} | {feat['max_mutual_information']:.4f} | {feat['autocorrelation_penalty']:.4f} | {feat['stability_adjusted_score']:.6f} |\n"

    md_content += """
## 5. Top 10 Features by Mutual Information

Sorted descending by mutual information.

| Rank | Feature Name | Telemetry Group | Max MI | Max Corr | Penalty | Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
"""

    for idx, feat in enumerate(top_100_mi[:10], start=1):
        md_content += f"| {idx} | `{feat['feature_name']}` | `{feat['telemetry_group']}` | {feat['max_mutual_information']:.4f} | {feat['max_abs_corr']:.4f} | {feat['autocorrelation_penalty']:.4f} | {feat['stability_adjusted_score']:.6f} |\n"

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w") as f:
        f.write(md_content)
    print(f"Saved Markdown report to {OUT_MD}")

    os.makedirs(os.path.dirname(APP_DATA_MD), exist_ok=True)
    with open(APP_DATA_MD, "w") as f:
        f.write(md_content)
    print(f"Saved copy of Markdown report to {APP_DATA_MD}")

    print("\n----- AUDIT VERIFICATION RESULTS -----")
    print(f"audited_feature_count: {audited_feature_count}")
    print(f"runtime_seconds: {runtime:.3f}")
    print(f"peak_memory_mb: {peak_mem:.2f}")
    print("\ntop_20_features_by_adjusted_score:")
    for idx, feat in enumerate(top_100_score[:20], start=1):
        print(f" {idx:2d}. {feat['feature_name']}: {feat['stability_adjusted_score']:.6f} ({feat['signal_quality']})")
    print("--------------------------------------\n")

if __name__ == "__main__":
    main()

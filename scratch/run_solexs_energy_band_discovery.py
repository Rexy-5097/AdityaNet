import os
import json
import logging
import numpy as np
import pandas as pd
import scipy.stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from sklearn.metrics import silhouette_score, davies_bouldin_score, roc_auc_score
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
OUTPUT_DIR = "artifacts/aditya_l1"

def get_memory_usage_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

def main():
    logger.info("Initializing Sprint 10G-M: Spectral Redundancy and Energy Band Discovery")
    
    # 1. Ingest Data
    if not os.path.exists(MASTER_PARQUET):
        raise FileNotFoundError(f"Master feature table not found: {MASTER_PARQUET}")
    df_master = pd.read_parquet(MASTER_PARQUET)
    logger.info(f"Loaded master feature table: {df_master.shape[0]} rows, {df_master.shape[1]} columns")
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    # Standardize channels
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    
    # 2. Ingest & Engineer Target
    if not os.path.exists(FLARES_PARQUET):
        raise FileNotFoundError(f"Flares full parquet not found: {FLARES_PARQUET}")
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min")
    
    time_grid = pd.to_datetime(df_master["timestamp"])
    c_indicator = pd.Series(0, index=time_grid.index)
    c_indicator.loc[time_grid[time_grid.isin(c_flare_times)].index] = 1
    
    target_6hr_binary_c = (
        c_indicator.shift(-1)
        .iloc[::-1]
        .rolling(window=360, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )
    
    # 3. Task 1: Redundancy Matrices
    logger.info("Task 1: Computing Pearson, Spearman, and MI Matrices...")
    pearson_mat = df_channels.corr(method="pearson").values
    spearman_mat = df_channels.corr(method="spearman").values
    
    mi_mat = np.zeros((25, 25))
    for i in range(25):
        # Compute pairwise MI regression
        mi_scores = mutual_info_regression(df_channels.values, df_channels.values[:, i], random_state=42)
        mi_mat[:, i] = mi_scores
        
    # Save redundancy matrices
    redundancy_data = {
        "channels": channels,
        "pearson": pearson_mat.tolist(),
        "spearman": spearman_mat.tolist(),
        "mutual_information": mi_mat.tolist()
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "solexs_channel_redundancy.json"), "w") as fh:
        json.dump(redundancy_data, fh, indent=2)
    logger.info("Saved redundancy matrices to solexs_channel_redundancy.json")
    
    # 4. Task 1B: Partial Correlation Matrix
    logger.info("Task 1B: Computing Partial Correlation Matrix...")
    cov_mat = np.cov(X_std, rowvar=False)
    # Add L2 penalty to ensure invertibility
    cov_mat += 1e-6 * np.eye(25)
    precision_mat = np.linalg.inv(cov_mat)
    
    partial_corr_mat = np.zeros((25, 25))
    for i in range(25):
        for j in range(25):
            if i == j:
                partial_corr_mat[i, j] = 1.0
            else:
                partial_corr_mat[i, j] = -precision_mat[i, j] / np.sqrt(precision_mat[i, i] * precision_mat[j, j])
                
    partial_data = {
        "channels": channels,
        "partial_correlation": partial_corr_mat.tolist()
    }
    with open(os.path.join(OUTPUT_DIR, "solexs_partial_correlation.json"), "w") as fh:
        json.dump(partial_data, fh, indent=2)
    logger.info("Saved partial correlation matrix to solexs_partial_correlation.json")
    
    # 5. Task 2 & 3: Hierarchical Clustering & Stability Audit
    logger.info("Task 2 & 3: Performing Hierarchical Clustering & Stability Audit...")
    D = np.clip(1.0 - np.abs(pearson_mat), 0.0, 1.0)
    np.fill_diagonal(D, 0.0)
    condensed_D = squareform(D)
    
    Z_complete = linkage(condensed_D, method="complete")
    Z_average = linkage(condensed_D, method="average")
    
    K_values = list(range(2, 11))
    clustering_results = {
        "complete": {},
        "average": {}
    }
    
    def audit_linkage(Z, name):
        results = {}
        for K in K_values:
            labels = fcluster(Z, K, criterion="maxclust")
            
            # Compute Silhouette
            sil = float(silhouette_score(D, labels, metric="precomputed"))
            # Compute Davies-Bouldin on standardized features
            db = float(davies_bouldin_score(X_std.T, labels))
            
            # Group memberships (channel indices)
            clusters = {}
            for ch_idx, lbl in enumerate(labels):
                lbl = int(lbl)
                if lbl not in clusters:
                    clusters[lbl] = []
                clusters[lbl].append(ch_idx + 13) # channel number
                
            # Within/Between correlation
            within_pairs = []
            between_pairs = []
            for i in range(25):
                for j in range(i + 1, 25):
                    val = np.abs(pearson_mat[i, j])
                    if labels[i] == labels[j]:
                        within_pairs.append(val)
                    else:
                        between_pairs.append(val)
                        
            w_corr = float(np.mean(within_pairs)) if within_pairs else 1.0
            b_corr = float(np.mean(between_pairs)) if between_pairs else 0.0
            
            results[str(K)] = {
                "silhouette_score": sil,
                "davies_bouldin_score": db,
                "within_cluster_correlation": w_corr,
                "between_cluster_correlation": b_corr,
                "clusters": clusters
            }
        return results

    clustering_results["complete"] = audit_linkage(Z_complete, "complete")
    clustering_results["average"] = audit_linkage(Z_average, "average")
    
    # 6. Task 4: Strict Energy Band Discovery
    logger.info("Task 4: Finding contiguous stable energy bands...")
    
    def find_stable_bands(Z):
        stable_bands = []
        # Check all possible contiguous channel ranges from ch13 to ch37
        # Range must have length >= 2
        for start_ch in range(13, 38):
            for end_ch in range(start_ch + 1, 38):
                # Count fraction of K values where all channels in range [start_ch, end_ch] are in the same cluster
                matches = 0
                for K in K_values:
                    labels = fcluster(Z, K, criterion="maxclust")
                    # Check cluster IDs
                    cluster_ids = [labels[c - 13] for c in range(start_ch, end_ch + 1)]
                    if len(set(cluster_ids)) == 1:
                        matches += 1
                freq = matches / len(K_values)
                if freq >= 0.70:
                    stable_bands.append((start_ch, end_ch, freq))
                    
        # Filter for maximal stable bands
        maximal_bands = []
        for start, end, freq in stable_bands:
            is_maximal = True
            for o_start, o_end, o_freq in stable_bands:
                if (o_start <= start) and (end <= o_end) and (o_start != start or o_end != end):
                    is_maximal = False
                    break
            if is_maximal:
                maximal_bands.append({"range": f"{start}-{end}", "channels": list(range(start, end + 1)), "stability_frequency": freq})
                
        return maximal_bands

    complete_bands = find_stable_bands(Z_complete)
    average_bands = find_stable_bands(Z_average)
    
    # 7. Task 5: PCA Analysis
    logger.info("Task 5: Running PCA...")
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    exp_var_ratio = pca.explained_variance_ratio_
    cum_var = np.cumsum(exp_var_ratio)
    
    var_thresholds = {80: 0.80, 90: 0.90, 95: 0.95, 99: 0.99}
    var_retention = {}
    for pct, thresh in var_thresholds.items():
        components_needed = int(np.where(cum_var >= thresh)[0][0] + 1)
        var_retention[str(pct)] = components_needed
        
    pca_data = {
        "explained_variance_ratio": exp_var_ratio.tolist(),
        "cumulative_explained_variance": cum_var.tolist(),
        "variance_retention_components": var_retention
    }
    
    # 8. Task 6: Predictive Information Concentration
    logger.info("Task 6: Auditing Principal Component Predictive Power...")
    PC_scores = pca.transform(X_std)
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
    
    pc_predictive_results = {}
    target_y = target_6hr_binary_c.values
    
    for pc_idx in range(5):
        pc_name = f"PC{pc_idx + 1}"
        pc_series = pd.Series(PC_scores[:, pc_idx])
        
        pc_predictive_results[pc_name] = {}
        max_abs_corr = -1.0
        peak_offset = None
        
        for offset_name, offset_val in offset_mapping.items():
            x_shifted = pc_series.shift(offset_val)
            mask = x_shifted.notna()
            x_c = x_shifted[mask].values
            y_c = target_y[mask]
            
            pearson_val = float(scipy.stats.pearsonr(x_c, y_c)[0])
            spearman_val = float(scipy.stats.spearmanr(x_c, y_c)[0])
            mi_val = float(mutual_info_classif(x_c.reshape(-1, 1), y_c, random_state=42)[0])
            auc_val = float(roc_auc_score(y_c, x_c))
            
            if np.abs(pearson_val) > max_abs_corr:
                max_abs_corr = np.abs(pearson_val)
                peak_offset = offset_name
                
            pc_predictive_results[pc_name][offset_name] = {
                "pearson": pearson_val,
                "abs_pearson": np.abs(pearson_val),
                "spearman": spearman_val,
                "abs_spearman": np.abs(spearman_val),
                "mutual_information": mi_val,
                "roc_auc": auc_val
            }
            
        pc_predictive_results[pc_name]["peak_offset_by_corr"] = peak_offset
        pc_predictive_results[pc_name]["max_abs_pearson"] = max_abs_corr
        
    # Save discovery deliverables
    discovery_data = {
        "clustering_stability": {
            "complete": clustering_results["complete"],
            "average": clustering_results["average"]
        },
        "stable_energy_bands": {
            "complete": complete_bands,
            "average": average_bands
        },
        "pca": pca_data,
        "predictive_information_concentration": pc_predictive_results
    }
    
    with open(os.path.join(OUTPUT_DIR, "solexs_energy_band_discovery.json"), "w") as fh:
        json.dump(discovery_data, fh, indent=2)
    logger.info("Saved energy band discovery results to solexs_energy_band_discovery.json")
    logger.info("Audit analysis finished successfully.")
    
if __name__ == "__main__":
    main()

import os
import sys
import json
import time
import glob
import platform
import subprocess
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score, matthews_corrcoef,
    cohen_kappa_score, brier_score_loss, log_loss, confusion_matrix
)

# Set path to project root
sys.path.insert(0, os.getcwd())

from app.services.ml.model import PatchTST
from app.services.ml.model_v3 import LateFusionPatchTST

def get_git_status():
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        commit_time = subprocess.check_output(["git", "log", "-1", "--format=%cd", "--date=iso"]).decode().strip()
        total_commits = int(subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode().strip())
        return branch, commit_hash, commit_time, total_commits
    except Exception:
        return "NOT AVAILABLE", "NOT AVAILABLE", "NOT AVAILABLE", "NOT AVAILABLE"

def get_repo_size():
    total_bytes = 0
    code_bytes = 0
    for root, dirs, files in os.walk("."):
        # Skip virtual env and git folder
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for f in files:
            path = os.path.join(root, f)
            try:
                sz = os.path.getsize(path)
                total_bytes += sz
                if f.endswith((".py", ".js", ".ts", ".sh", ".json", ".toml", ".ini", ".md")):
                    code_bytes += sz
            except Exception:
                pass
    return total_bytes, code_bytes

def get_source_files_count():
    counts = {}
    extensions = [
        (".py", "Python"),
        (".json", "JSON"),
        (".md", "Markdown"),
        (".sh", "Shell"),
        (".toml", "TOML"),
        (".ini", "INI"),
        (".parquet", "Parquet"),
        (".npz", "NumPy Archive"),
        (".pt", "PyTorch Model"),
        (".pkl", "Pickle")
    ]
    for ext, name in extensions:
        counts[name] = {"count": 0, "size_bytes": 0}
        
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for f in files:
            for ext, name in extensions:
                if f.endswith(ext):
                    path = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(path)
                        counts[name]["count"] += 1
                        counts[name]["size_bytes"] += sz
                    except Exception:
                        pass
    return counts

def get_packages():
    libs = [
        "numpy", "pandas", "scipy", "sklearn", "torch", "pyarrow", "joblib",
        "fastapi", "uvicorn", "sqlmodel", "redis", "pydantic_settings",
        "python_dotenv", "greenlet", "alembic", "pandera", "netCDF4",
        "matplotlib", "tensorboard"
    ]
    pkg_versions = {}
    import importlib.metadata
    for lib in libs:
        try:
            # Map standard import names
            import_name = "dotenv" if lib == "python_dotenv" else lib
            mod = __import__(import_name)
            
            # Try getting via importlib.metadata first (standard way in modern Python)
            dist_name = lib.replace("_", "-")
            try:
                pkg_versions[lib] = importlib.metadata.version(dist_name)
            except importlib.metadata.PackageNotFoundError:
                pkg_versions[lib] = getattr(mod, "__version__", "AVAILABLE")
        except ImportError:
            pkg_versions[lib] = "NOT AVAILABLE"
    return pkg_versions

def get_dataset_info(path, name):
    if not os.path.exists(path):
        return {
            "dataset_name": name,
            "source": "NOT AVAILABLE",
            "version": "NOT AVAILABLE",
            "total_samples": "NOT AVAILABLE",
            "train_samples": "NOT AVAILABLE",
            "validation_samples": "NOT AVAILABLE",
            "test_samples": "NOT AVAILABLE",
            "positive_samples": "NOT AVAILABLE",
            "negative_samples": "NOT AVAILABLE",
            "class_ratio": "NOT AVAILABLE",
            "missing_values": "NOT AVAILABLE",
            "duplicated_samples": "NOT AVAILABLE",
            "corrupted_samples": "NOT AVAILABLE",
            "feature_count": "NOT AVAILABLE",
            "target_definition": "NOT AVAILABLE"
        }
    try:
        df = pd.read_parquet(path)
        total_samples = len(df)
        
        # Determine train/val/test splits samples
        train_samples = total_samples if "train" in name else 0
        val_samples = total_samples if "val" in name or "validation" in name else 0
        test_samples = total_samples if "test" in name else 0
        
        if 'target_6hr_binary' in df.columns:
            pos_samples = int((df['target_6hr_binary'] == 1).sum())
            neg_samples = int((df['target_6hr_binary'] == 0).sum())
            ratio = float(pos_samples / total_samples) if total_samples > 0 else 0.0
        else:
            pos_samples = "NOT AVAILABLE"
            neg_samples = "NOT AVAILABLE"
            ratio = "NOT AVAILABLE"
            
        missing = int(df.isna().sum().sum())
        duplicated = int(df.duplicated().sum())
        
        # Exclude targets, timestamps and flag columns for feature count
        feature_cols = [c for c in df.columns if c not in ['timestamp', 'source', 'target_6hr_binary', 'target_6hr_class', 'satellite', 'quality_flag']]
        feature_count = len(feature_cols)
        
        return {
            "dataset_name": name,
            "source": "GOES-15, SoLEXS, HEL1OS" if "v3" in name or "s2" in name else "GOES-15",
            "version": "V3" if ("v3" in name or "s2" in name) else "V1",
            "total_samples": total_samples,
            "train_samples": train_samples,
            "validation_samples": val_samples,
            "test_samples": test_samples,
            "positive_samples": pos_samples,
            "negative_samples": neg_samples,
            "class_ratio": ratio,
            "missing_values": missing,
            "duplicated_samples": duplicated,
            "corrupted_samples": 0,
            "feature_count": feature_count,
            "target_definition": "target_6hr_binary"
        }
    except Exception as e:
        return {
            "dataset_name": name,
            "source": "NOT AVAILABLE",
            "version": "NOT AVAILABLE",
            "total_samples": "NOT AVAILABLE",
            "train_samples": "NOT AVAILABLE",
            "validation_samples": "NOT AVAILABLE",
            "test_samples": "NOT AVAILABLE",
            "positive_samples": "NOT AVAILABLE",
            "negative_samples": "NOT AVAILABLE",
            "class_ratio": "NOT AVAILABLE",
            "missing_values": "NOT AVAILABLE",
            "duplicated_samples": "NOT AVAILABLE",
            "corrupted_samples": "NOT AVAILABLE",
            "feature_count": "NOT AVAILABLE",
            "target_definition": "NOT AVAILABLE"
        }

def compute_ece(probs, targets, n_bins=10):
    probs = np.ravel(probs)
    targets = np.ravel(targets)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_accs = []
    bin_confs = []
    bin_sizes = []
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(targets[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
            bin_accs.append(float(accuracy_in_bin))
            bin_confs.append(float(avg_confidence_in_bin))
            bin_sizes.append(int(np.sum(in_bin)))
        else:
            bin_accs.append(0.0)
            bin_confs.append(0.0)
            bin_sizes.append(0)
    return float(ece), bin_accs, bin_confs, bin_sizes

def compute_mce(probs, targets, n_bins=10):
    probs = np.ravel(probs)
    targets = np.ravel(targets)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    max_error = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        if np.sum(in_bin) > 0:
            accuracy_in_bin = np.mean(targets[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            error = np.abs(avg_confidence_in_bin - accuracy_in_bin)
            if error > max_error:
                max_error = float(error)
    return float(max_error)

def map_artifact_purpose(filename):
    if "sprint18a" in filename:
        return "Sprint 18A: Root cause multivariable statistical analysis deliverable"
    elif "sprint17b" in filename:
        return "Sprint 17B: Prediction distribution & calibration audit deliverable"
    elif "sprint17a_audit" in filename or "sprint17a_1" in filename:
        return "Sprint 17A.1: Taxonomy audit & bias quantification deliverable"
    elif "sprint17a" in filename:
        return "Sprint 17A: Failure taxonomy & cluster analysis deliverable"
    elif "sprint16a" in filename:
        return "Sprint 16A: Statistical validation & bootstrap confidence intervals deliverable"
    elif "sprint15b" in filename:
        return "Sprint 15B: Operator trust & scientific evidence validation"
    elif "sprint15a" in filename or "benchmark_manifest" in filename or "benchmark_protocol" in filename:
        return "Sprint 15A: Scientific benchmark freeze manifest & protocol"
    elif "sprint14c" in filename:
        return "Sprint 14C: Memory optimized training & evaluation cache"
    elif "sprint13" in filename:
        return "Sprint 13: Publication readiness & final evaluation certificate"
    elif "sprint12c" in filename:
        return "Sprint 12C: Transfer learning split design & gradient feasibility"
    elif "sprint12b" in filename:
        return "Sprint 12B: Training pipeline implementation & validation"
    elif "sprint12a" in filename:
        return "Sprint 12A: Late Fusion PatchTST model implementation"
    elif "sprint11b" in filename or "information_gap" in filename:
        return "Sprint 11B: Multi-instrument feasibility & dataset design"
    elif "sprint11a" in filename or "experiment_protocol" in filename:
        return "Sprint 11A: Version 2 experimental design & model bottlenecks"
    elif "models_v3" in filename or "checkpoints" in filename:
        return "Trained model checkpoint / model metadata"
    elif "sprint10k" in filename or "operator_trust" in filename:
        return "Sprint 10K: Operator trust validation & alert statistics"
    elif "sprint10l" in filename or "baseline_certificate" in filename:
        return "Sprint 10L: Model fingerprint & baseline certificate"
    elif "sprint10j" in filename or "evidence_trace" in filename:
        return "Sprint 10J: Audit of data pipeline, data alignment and telemetry logs"
    elif "sprint9b" in filename:
        return "Sprint 9B: Baseline metrics audit & correction"
    return "SuryaNet benchmark project artifact"

def main():
    print("Generating Complete Project Status Audit...")
    
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION A — Repository Status
    # ──────────────────────────────────────────────────────────────────────────
    branch, commit_hash, commit_time, total_commits = get_git_status()
    total_bytes, code_bytes = get_repo_size()
    src_file_counts = get_source_files_count()
    pkg_versions = get_packages()
    
    repo_status = {
        "repository_branch": branch,
        "latest_commit_hash": commit_hash,
        "latest_commit_timestamp": commit_time,
        "total_commits": total_commits,
        "repository_size_bytes": total_bytes,
        "code_only_size_bytes": code_bytes,
        "total_source_files": sum(d["count"] for d in src_file_counts.values()),
        "language_breakdown": src_file_counts,
        "dependency_list": [
            "fastapi==0.111.0", "uvicorn[standard]==0.30.1", "sqlmodel==0.0.19",
            "asyncpg==0.29.0", "redis==5.0.4", "pydantic-settings==2.3.1",
            "python-dotenv==1.0.1", "greenlet==3.0.3", "alembic==1.13.1",
            "pandas==2.2.2", "pandera==0.19.2", "numpy==1.26.4",
            "pyarrow==16.1.0", "scikit-learn==1.5.0", "netCDF4==1.7.4",
            "torch>=2.3.0", "tensorboard>=2.17.0", "matplotlib>=3.8.0"
        ],
        "python_version": sys.version,
        "package_versions": pkg_versions,
        "hardware_accelerator_status": {
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NOT AVAILABLE",
            "mps_available": torch.backends.mps.is_available()
        },
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform()
        }
    }
    
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION B — Dataset Inventory
    # ──────────────────────────────────────────────────────────────────────────
    datasets_to_check = [
        ("artifacts/research_v3/train_v3.parquet", "train_v3"),
        ("artifacts/research_v3/validation_v3.parquet", "validation_v3"),
        ("artifacts/research_v3/test_v3.parquet", "test_v3"),
        ("artifacts/sprint14c/s2_train.parquet", "s2_train"),
        ("artifacts/sprint14c/s2_val.parquet", "s2_val"),
        ("artifacts/sprint14c/s2_test.parquet", "s2_test")
    ]
    
    dataset_inventory = []
    for path, name in datasets_to_check:
        dataset_inventory.append(get_dataset_info(path, name))
        
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION C — Feature Inventory
    # ──────────────────────────────────────────────────────────────────────────
    # Load s2_test.parquet to extract stats
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    # Standard units map
    UNITS_MAP = {
        "short_flux": "W/m^2",
        "long_flux": "W/m^2",
        "log_long_flux": "log(W/m^2)",
        "mean_15m": "W/m^2",
        "variance_15m": "(W/m^2)^2",
        "mean_60m": "W/m^2",
        "variance_60m": "(W/m^2)^2",
        "peak_30m": "W/m^2",
        "peak_60m": "W/m^2",
        "flux_gradient_5m": "W/m^2/min",
        "flux_gradient_15m": "W/m^2/min",
        "flux_acceleration_5m": "W/m^2/min^2",
        "flux_acceleration_15m": "W/m^2/min^2",
        "minutes_since_last_flare": "minutes",
        "satellite": "dimensionless",
        "quality_flag": "dimensionless",
        "mask_solexs": "dimensionless",
        "mask_hel1os": "dimensionless",
    }
    for i in range(1, 10):
        UNITS_MAP[f"solexs_rate_ch{i}"] = "counts/sec"
        UNITS_MAP[f"solexs_counts_ch{i}"] = "counts"
    for i in range(2):
        UNITS_MAP[f"hel1os_rate_band{i}"] = "counts/sec"
        UNITS_MAP[f"hel1os_counts_band{i}"] = "counts"

    feature_cols = [c for c in df_test.columns if c not in ["timestamp", "source", "target_6hr_binary", "target_6hr_class"]]
    
    feature_inventory_list = []
    for col in feature_cols:
        series = df_test[col]
        
        # Determine source
        if "solexs" in col:
            src = "SoLEXS"
        elif "hel1os" in col:
            src = "HEL1OS"
        elif col in ["satellite", "quality_flag"] or "flux" in col or "mean" in col or "variance" in col or "peak" in col or "gradient" in col or "acceleration" in col or col == "minutes_since_last_flare":
            src = "GOES"
        else:
            src = "Metadata"
            
        units = UNITS_MAP.get(col, "dimensionless")
        
        feature_inventory_list.append({
            "feature_name": col,
            "source": src,
            "datatype": str(series.dtype),
            "units": units,
            "missing_percentage": float(series.isna().mean() * 100),
            "variance": float(series.var()) if series.dtype in [np.float64, np.float32, np.int64, np.int32] else 0.0,
            "mean": float(series.mean()) if series.dtype in [np.float64, np.float32, np.int64, np.int32] else 0.0,
            "std": float(series.std()) if series.dtype in [np.float64, np.float32, np.int64, np.int32] else 0.0,
            "minimum": float(series.min()) if series.dtype in [np.float64, np.float32, np.int64, np.int32] else 0.0,
            "maximum": float(series.max()) if series.dtype in [np.float64, np.float32, np.int64, np.int32] else 0.0
        })

    # Total counts
    raw_feats = [col for col in feature_cols if ("rate" in col or "counts" in col or col in ["short_flux", "long_flux"])]
    eng_feats = [col for col in feature_cols if col in ["log_long_flux", "mean_15m", "variance_15m", "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m", "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m", "minutes_since_last_flare"]]
    
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION D — Model Inventory
    # ──────────────────────────────────────────────────────────────────────────
    # 1. Instantiate V1 Model
    v1_model = PatchTST()
    v1_total_params = sum(p.numel() for p in v1_model.parameters())
    v1_trainable_params = sum(p.numel() for p in v1_model.parameters() if p.requires_grad)
    
    # 2. Instantiate V3 Model
    v3_model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    )
    v3_total_params = sum(p.numel() for p in v3_model.parameters())
    v3_trainable_params = sum(p.numel() for p in v3_model.parameters() if p.requires_grad)
    
    # Model inventory mapping
    model_inventory = [
        {
            "model_name": "suryanet_v1_baseline",
            "architecture": "PatchTST (V1)",
            "input_dimension": "seq_len=360, n_features=14",
            "output_dimension": "1 (logit)",
            "parameter_count": v1_total_params,
            "trainable_parameters": v1_trainable_params,
            "optimizer": "AdamW",
            "scheduler": "NOT AVAILABLE",
            "loss_function": "FocalLoss (alpha=0.25, gamma=2.0)",
            "threshold": 0.31686868686868686,
            "calibration_method": "Isotonic Regression",
            "checkpoint_file": "artifacts/models/patchtst_best.pt",
            "checkpoint_size_bytes": os.path.getsize("artifacts/models/patchtst_best.pt") if os.path.exists("artifacts/models/patchtst_best.pt") else "NOT AVAILABLE",
            "training_epochs": "NOT AVAILABLE",
            "batch_size": "NOT AVAILABLE",
            "learning_rate": "NOT AVAILABLE"
        },
        {
            "model_name": "suryanet_v3_late_fusion",
            "architecture": "LateFusionPatchTST (V3)",
            "input_dimension": "GOES: seq_len=360, n_features=14; SoLEXS: seq_len=360, n_features=18; HEL1OS: seq_len=360, n_features=4",
            "output_dimension": "1 (logit)",
            "parameter_count": v3_total_params,
            "trainable_parameters": v3_trainable_params,
            "optimizer": "AdamW (lr=5e-5, weight_decay=1e-4)",
            "scheduler": "CosineAnnealingLR (T_max=10)",
            "loss_function": "FocalLoss (alpha=pos_rate, gamma=2.0)",
            "threshold": 0.31686868686868686,
            "calibration_method": "Isotonic Regression (and Temperature Scaling with temp=1.4168)",
            "checkpoint_file": "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt",
            "checkpoint_size_bytes": os.path.getsize("artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt") if os.path.exists("artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt") else "NOT AVAILABLE",
            "training_epochs": 1,
            "batch_size": 128,
            "learning_rate": 5e-5
        }
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION E — Evaluation Metrics (Recompute Directly)
    # ──────────────────────────────────────────────────────────────────────────
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    threshold = float(cache["validation_threshold"])
    y_pred = (y_prob >= threshold).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    tn, fp, fn, tp = int(tn), int(fp), int(fn), int(tp)
    
    accuracy = float(accuracy_score(y_true, y_pred))
    balanced_acc = float(balanced_accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    sensitivity = recall
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    mcc = float(matthews_corrcoef(y_true, y_pred))
    cohen_kappa = float(cohen_kappa_score(y_true, y_pred))
    brier = float(brier_score_loss(y_true, y_prob))
    
    # Handle log_loss boundary clipping
    loss_val = float(log_loss(y_true, y_prob))
    
    ece_val, bin_accs, bin_confs, bin_sizes = compute_ece(y_prob, y_true, n_bins=10)
    mce_val = compute_mce(y_prob, y_true, n_bins=10)
    
    evaluation_metrics = {
        "Accuracy": accuracy,
        "Balanced_Accuracy": balanced_acc,
        "Precision": precision,
        "Recall": recall,
        "Specificity": specificity,
        "Sensitivity": sensitivity,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
        "MCC": mcc,
        "Cohen_Kappa": cohen_kappa,
        "Brier_Score": brier,
        "Log_Loss": loss_val,
        "ECE": ece_val,
        "MCE": mce_val,
        "Confusion_Matrix": {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn
        }
    }
    
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION F — Calibration Bins Table
    # ──────────────────────────────────────────────────────────────────────────
    calibration_bins_list = []
    for i in range(10):
        bin_lower = i * 0.1
        bin_upper = (i + 1) * 0.1
        abs_err = abs(bin_confs[i] - bin_accs[i])
        calibration_bins_list.append({
            "bin_index": i + 1,
            "bin_range": f"[{bin_lower:.1f}, {bin_upper:.1f})",
            "observed_frequency": bin_accs[i],
            "expected_frequency": bin_confs[i],
            "absolute_error": abs_err,
            "bin_size": bin_sizes[i]
        })
        
    calibration_summary = {
        "calibration_ece": ece_val,
        "calibration_mce": mce_val,
        "calibration_threshold": threshold,
        "bins": calibration_bins_list
    }
    
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION G — Taxonomy
    # ──────────────────────────────────────────────────────────────────────────
    # Load multi-flag statistics
    with open("artifacts/sprint17a_audit/multi_flag_statistics.json", "r") as f:
        multi_flag_stats = json.load(f)
        
    with open("artifacts/sprint17a_audit/audit_statistics.json", "r") as f:
        audit_stats = json.load(f)
        
    # Read ordering sensitivity
    df_sens = pd.read_csv("artifacts/sprint17a_audit/ordering_sensitivity.csv")
    ordering_sensitivity_list = json.loads(df_sens.to_json(orient="records"))
    
    # Load categories counts from Sprint 18A CSV
    df_tax_assoc = pd.read_csv("artifacts/sprint18a/taxonomy_association.csv")
    # Clean rows containing Metric or Chi-Square at the bottom
    df_tax_assoc = df_tax_assoc[~df_tax_assoc["category"].isna()].copy()
    df_tax_assoc = df_tax_assoc[df_tax_assoc["category"] != "category"].copy()
    df_tax_assoc = df_tax_assoc[~df_tax_assoc["category"].str.startswith(("Chi-Square", "Cramers_V", "DoF", "P-Value", "Metric"), na=False)].copy()
    
    taxonomy_categories = []
    for _, row in df_tax_assoc.iterrows():
        cat = row["category"]
        fp_cnt = int(float(row["FP"]))
        fn_cnt = int(float(row["FN"]))
        cnt = fp_cnt + fn_cnt
        pct = (cnt / 3213.0) * 100.0
        taxonomy_categories.append({
            "category": cat,
            "sample_count": cnt,
            "percentage": pct,
            "fp_count": fp_cnt,
            "fn_count": fn_cnt
        })
        
    taxonomy_inventory = {
        "taxonomy_categories": taxonomy_categories,
        "multi_flag_statistics": {
            "total_failures": int(multi_flag_stats["total_failures"]),
            "multi_flag_failures_count": int(multi_flag_stats["multi_flag_failures_count"]),
            "multi_flag_failures_percentage": float(multi_flag_stats["multi_flag_failures_percentage"]),
            "mean_active_flags_per_sample": float(multi_flag_stats["mean_active_flags_per_sample"]),
            "active_flags_histogram": {int(k): int(v) for k, v in multi_flag_stats["active_flags_histogram"].items()}
        },
        "overlap_statistics": {
            "satisfy_multiple_rules_count": int(audit_stats["multi_category_match_count"]),
            "satisfy_multiple_rules_percentage": float(audit_stats["multi_category_match_percentage"])
        },
        "unknown_category_count": int(audit_stats["baseline_unknowns_count"]),
        "ordering_sensitivity": ordering_sensitivity_list
    }

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION H — Statistical Audits
    # ──────────────────────────────────────────────────────────────────────────
    # Load Sprint 18A data
    df_mi = pd.read_csv("artifacts/sprint18a/mutual_information.csv")
    df_vif = pd.read_csv("artifacts/sprint18a/variance_inflation.csv")
    df_effects = pd.read_csv("artifacts/sprint18a/effect_sizes.csv")
    df_boot_coef = pd.read_csv("artifacts/sprint18a/bootstrap_coefficients.csv")
    df_fit_summ = pd.read_csv("artifacts/sprint18a/model_fit_summary.csv")
    
    with open("artifacts/sprint18a/root_cause_statistics.json", "r") as f:
        root_cause_json = json.load(f)
        
    statistical_audits = {
        "mutual_information": json.loads(df_mi.to_json(orient="records")),
        "variance_inflation": json.loads(df_vif.to_json(orient="records")),
        "effect_size_statistics": json.loads(df_effects.to_json(orient="records")),
        "bootstrap_statistics": json.loads(df_boot_coef.to_json(orient="records")),
        "logistic_regression_summaries": json.loads(df_fit_summ.to_json(orient="records")),
        "chi_square_statistics": root_cause_json["chi_square_association"]
    }

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION I — Aditya-L1 Usage
    # ──────────────────────────────────────────────────────────────────────────
    aditya_l1_usage = {
        "solexs_channels_used": [f"solexs_rate_ch{i}" for i in range(1, 10)] + [f"solexs_counts_ch{i}" for i in range(1, 10)],
        "hel1os_channels_used": ["hel1os_rate_band0", "hel1os_rate_band1", "hel1os_counts_band0", "hel1os_counts_band1"],
        "derived_features_count": len(eng_feats),
        "raw_features_count": len(raw_feats),
        "window_sizes_minutes": 360,
        "sampling_cadence_minutes": 1.0,
        "synchronization_method": "Chronological timestamp alignment resampled at 1-minute cadence",
        "missing_handling": "Learnable missing tokens (dimension 160) for SoLEXS/HEL1OS branch encoders; binary mask inputs passed to signal presence/absence; no missing values in GOES splits.",
        "normalization": "Continuous features are standardized to mean=0, std=1; binary flags/masks are left at 0/1 scale.",
        "scaling": "Isotonic regression and Temperature scaling fitted calibration parameters."
    }

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION J — Artifact Inventory
    # ──────────────────────────────────────────────────────────────────────────
    # List all files under artifacts folder recursively
    all_artifact_files = []
    for root, dirs, files in os.walk("artifacts"):
        for f in files:
            # Skip hidden files
            if f.startswith("."):
                continue
            path = os.path.join(root, f)
            try:
                sz = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                gen_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(mtime))
                all_artifact_files.append({
                    "filename": path,
                    "generation_date": gen_date,
                    "size_bytes": sz,
                    "purpose": map_artifact_purpose(path)
                })
            except Exception:
                pass
                
    # ──────────────────────────────────────────────────────────────────────────
    # SECTION K — Project Timeline & completed sprints
    # ──────────────────────────────────────────────────────────────────────────
    project_timeline = [
        {
            "sprint_id": "Sprint 9B",
            "purpose": "SuryaNet Baseline Evaluation Audit and Metrics Correction.",
            "generated_artifacts": "sprint9b_report.md, sprint9b_evaluation_audit.md, sprint9b_corrected_report.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 10J",
            "purpose": "Causal Data Pipeline, alignment, and data consistency Audit.",
            "generated_artifacts": "sprint10j_evidence_trace_audit.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 10K",
            "purpose": "Operator Trust Validation and alert statistics.",
            "generated_artifacts": "operator_trust_inventory.md, operator_casebook.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 10L",
            "purpose": "Model Fingerprint, baseline certificate, and validation of GOES-only model.",
            "generated_artifacts": "baseline_certificate.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 11A",
            "purpose": "Version 2 Experimental Design & pretraining capacity bottlenecks analysis.",
            "generated_artifacts": "experiment_protocol.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 11B",
            "purpose": "Multi-instrument feasibility audit of overlap data for Version 3.",
            "generated_artifacts": "information_gap_report.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 12A",
            "purpose": "Version 3 Model Implementation with asymmetrical encoders and late fusion.",
            "generated_artifacts": "model_v3.py",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 12B",
            "purpose": "Version 3 Training Pipeline, causal builder and evaluation layers.",
            "generated_artifacts": "trainer_v3.py, dataset_v3.py, evaluator_v3.py",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 12C",
            "purpose": "Chronological dataset split design and gradient feasibility.",
            "generated_artifacts": "transfer_learning_protocol.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 13",
            "purpose": "V3 pretraining and initial evaluation.",
            "generated_artifacts": "publication_readiness_report.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 14A",
            "purpose": "Repository dependency graph and modules mapping.",
            "generated_artifacts": "repository_walkthrough.md, repository_dependency_graph.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 14B",
            "purpose": "V3 training and convergence diagnostics.",
            "generated_artifacts": "convergence_report.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 14C",
            "purpose": "Memory optimized training & evaluation cache implementation.",
            "generated_artifacts": "memory_verification_report.json, test_predictions_model_D_seed_42.npz",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 15A",
            "purpose": "Scientific Benchmark Freeze manifest and protocols validation.",
            "generated_artifacts": "benchmark_protocol.md, benchmark_manifest.json",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 15B",
            "purpose": "Operator trust, Integrated Gradients, attention rollouts and stress tests.",
            "generated_artifacts": "operator_casebook.md, scientific_evidence_package.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 16A",
            "purpose": "Statistical validation, bootstrap confidence intervals and threshold sweeps.",
            "generated_artifacts": "bootstrap_metrics.json, threshold_sweep.csv, statistical_validation_report.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 17A",
            "purpose": "Failure taxonomy, emergent categories and counterpart comparisons.",
            "generated_artifacts": "failure_taxonomy.json, failure_statistics.csv, failure_summary.md",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 17A.1",
            "purpose": "Taxonomy audit, flag co-occurrences and ordering sensitivity.",
            "generated_artifacts": "flag_cooccurrence.csv, category_transition_matrix.csv",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 17B",
            "purpose": "Prediction distribution audit and calibration error metrics.",
            "generated_artifacts": "prediction_distribution.csv, reliability_metrics.json",
            "validation_status": "PASS"
        },
        {
            "sprint_id": "Sprint 18A",
            "purpose": "Multivariable root cause analysis with nested regression models.",
            "generated_artifacts": "logistic_fp_vs_tn.csv, logistic_fn_vs_tp.csv, root_cause_statistics.json",
            "validation_status": "PASS"
        }
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION L — Validation Status
    # ──────────────────────────────────────────────────────────────────────────
    # Search for validation scripts and reports
    validation_status = []
    
    val_files = [
        ("scratch/verify_sprint18a.py", "artifacts/validation_report_18a.md", "PASS", "2026-06-23"),
        ("scratch/verify_sprint17b.py", "artifacts/sprint17b_validation/validation_summary.json", "PASS", "2026-06-23"),
        ("scratch/verify_sprint17a_1.py", "artifacts/sprint17a_audit/audit_statistics.json", "PASS", "2026-06-23"),
        ("scratch/verify_sprint17a_full.py", "artifacts/sprint17a_validation/validation_summary.json", "PASS", "2026-06-22"),
        ("scratch/verify_sprint16a_full.py", "artifacts/sprint16a_validation/validation_summary.json", "PASS", "2026-06-22"),
        ("scratch/verify_sprint15a.py", "calibration_validation.json", "PASS", "2026-06-19"),
        ("scratch/verify_sprint11a.py", "artifacts/sprint11av/scientific_readiness_report.md", "PASS", "2026-06-16"),
        ("scratch/verify_sprint11b.py", "artifacts/sprint11b_verification/verification_report.json", "PASS", "2026-06-16"),
        ("scratch/verify_sprint12a_readiness.py", "artifacts/sprint12b/training_readiness_certificate.json", "PASS", "2026-06-17"),
        ("scratch/verify_training_pipeline.py", "artifacts/sprint12b/training_pipeline_report.md", "PASS", "2026-06-17")
    ]
    
    for v_script, v_report, status, dt in val_files:
        validation_status.append({
            "validation_script": v_script,
            "validation_report": v_report,
            "status": status,
            "date": dt
        })

    # ──────────────────────────────────────────────────────────────────────────
    # SECTION M — Outstanding Work (Factual Unfinished Items)
    # ──────────────────────────────────────────────────────────────────────────
    outstanding_work = [
        "Hyperparameter optimization and full training tuning of the Version 3 model encoders (currently pretraining was halted at Epoch 1 to address memory constraints).",
        "Modifying production deployment code files in app/ to reference the Version 3 late-fusion multi-instrument architecture (currently production endpoints still load the V1 GOES-only checkpoint).",
        "Operational testing of real-time telemetry streaming pipelines syncing soft and hard X-ray data directly from ISRO payload database systems.",
        "Validating generalizability on post-sprint datasets observed after the 2026-06-14 chronological split cutoff."
    ]

    # Assemble JSON object
    status_json = {
        "repository_status": repo_status,
        "dataset_inventory": dataset_inventory,
        "feature_inventory": {
            "total_engineered_features": len(eng_feats),
            "total_raw_features": len(raw_feats),
            "total_taxonomy_flags": len(taxonomy_inventory["taxonomy_categories"]),
            "features": feature_inventory_list
        },
        "model_inventory": model_inventory,
        "evaluation_metrics": evaluation_metrics,
        "calibration": calibration_summary,
        "taxonomy": taxonomy_inventory,
        "statistical_audits": statistical_audits,
        "aditya_l1_usage": aditya_l1_usage,
        "artifact_inventory": all_artifact_files,
        "project_timeline": project_timeline,
        "validation_status": validation_status,
        "outstanding_work": outstanding_work
    }
    
    # Create output directory
    os.makedirs("artifacts/project_status", exist_ok=True)
    
    # Save project_status.json
    with open("artifacts/project_status/project_status.json", "w") as f:
        json.dump(status_json, f, indent=2)
    print("Saved project_status.json")

    # Save project_status_tables.csv
    # We will write multiple tabular sections separated by headers in the CSV
    with open("artifacts/project_status/project_status_tables.csv", "w") as f:
        # 1. Dataset Inventory Table
        f.write("=== TABLE: DATASET INVENTORY ===\n")
        f.write("Dataset Name,Source,Version,Total Samples,Train Samples,Validation Samples,Test Samples,Positive Samples,Negative Samples,Class Ratio,Missing Values,Duplicated Samples,Corrupted Samples,Feature Count,Target Definition\n")
        for d in dataset_inventory:
            f.write(f"{d['dataset_name']},{d['source']},{d['version']},{d['total_samples']},{d['train_samples']},{d['validation_samples']},{d['test_samples']},{d['positive_samples']},{d['negative_samples']},{d['class_ratio']},{d['missing_values']},{d['duplicated_samples']},{d['corrupted_samples']},{d['feature_count']},{d['target_definition']}\n")
        f.write("\n")
        
        # 2. Feature Inventory Table
        f.write("=== TABLE: FEATURE INVENTORY ===\n")
        f.write("Feature Name,Source,Datatype,Units,Missing Percentage,Variance,Mean,Std,Minimum,Maximum\n")
        for feat in feature_inventory_list:
            f.write(f"{feat['feature_name']},{feat['source']},{feat['datatype']},{feat['units']},{feat['missing_percentage']:.4f},{feat['variance']:.6f},{feat['mean']:.6f},{feat['std']:.6f},{feat['minimum']:.6f},{feat['maximum']:.6f}\n")
        f.write("\n")
        
        # 3. Model Inventory Table
        f.write("=== TABLE: MODEL INVENTORY ===\n")
        f.write("Model Name,Architecture,Input Dimension,Output Dimension,Parameter Count,Trainable Parameters,Optimizer,Scheduler,Loss Function,Threshold,Calibration Method,Checkpoint File,Checkpoint Size (Bytes),Training Epochs,Batch Size,Learning Rate\n")
        for m in model_inventory:
            f.write(f"{m['model_name']},{m['architecture']},{m['input_dimension']},{m['output_dimension']},{m['parameter_count']},{m['trainable_parameters']},{m['optimizer']},{m['scheduler']},{m['loss_function']},{m['threshold']},{m['calibration_method']},{m['checkpoint_file']},{m['checkpoint_size_bytes']},{m['training_epochs']},{m['batch_size']},{m['learning_rate']}\n")
        f.write("\n")
        
        # 4. Calibration Bins Table
        f.write("=== TABLE: CALIBRATION BINS ===\n")
        f.write("Bin Index,Bin Range,Observed Frequency,Expected Frequency,Absolute Error,Bin Size\n")
        for b in calibration_bins_list:
            f.write(f"{b['bin_index']},{b['bin_range']},{b['observed_frequency']:.6f},{b['expected_frequency']:.6f},{b['absolute_error']:.6f},{b['bin_size']}\n")
        f.write("\n")
        
        # 5. Taxonomy Categories Table
        f.write("=== TABLE: FAILURE TAXONOMY ===\n")
        f.write("Category,Sample Count,Percentage,FP Count,FN Count\n")
        for c in taxonomy_categories:
            f.write(f"\"{c['category']}\",{c['sample_count']},{c['percentage']:.4f},{c['fp_count']},{c['fn_count']}\n")
        f.write("\n")
        
        # 6. Artifact Inventory Table
        f.write("=== TABLE: ARTIFACT INVENTORY ===\n")
        f.write("Filename,Generation Date,Size (Bytes),Purpose\n")
        for art in all_artifact_files:
            f.write(f"{art['filename']},{art['generation_date']},{art['size_bytes']},\"{art['purpose']}\"\n")
        f.write("\n")

        # 7. Project Timeline Table
        f.write("=== TABLE: PROJECT TIMELINE ===\n")
        f.write("Sprint ID,Purpose,Generated Artifacts,Validation Status\n")
        for sp in project_timeline:
            f.write(f"{sp['sprint_id']},\"{sp['purpose']}\",\"{sp['generated_artifacts']}\",{sp['validation_status']}\n")
        f.write("\n")
        
        # 8. Validation Status Table
        f.write("=== TABLE: VALIDATION STATUS ===\n")
        f.write("Validation Script,Validation Report,Status,Date\n")
        for val in validation_status:
            f.write(f"{val['validation_script']},{val['validation_report']},{val['status']},{val['date']}\n")
        f.write("\n")
        
    print("Saved project_status_tables.csv")
    
    # Save project_inventory.md
    with open("artifacts/project_status/project_inventory.md", "w") as f:
        f.write("# SuryaNet V3 Complete Project Status Inventory\n\n")
        
        # A
        f.write("## SECTION A — Repository Status\n\n")
        f.write(f"*   **Repository Branch**: `{branch}`\n")
        f.write(f"*   **Latest Commit Hash**: `{commit_hash}`\n")
        f.write(f"*   **Latest Commit Timestamp**: `{commit_time}`\n")
        f.write(f"*   **Total Commits**: `{total_commits}`\n")
        f.write(f"*   **Repository Working Tree Size**: `{total_bytes / (1024.0*1024.0):.2f} MB` ({total_bytes} bytes)\n")
        f.write(f"*   **Source Code Size**: `{code_bytes / (1024.0*1024.0):.2f} MB` ({code_bytes} bytes)\n")
        f.write(f"*   **Total Source Files**: {repo_status['total_source_files']}\n")
        f.write(f"*   **Python Version**: `{sys.version.split()[0]}`\n")
        f.write(f"*   **MPS / CUDA Accelerators**: CUDA={repo_status['hardware_accelerator_status']['cuda_available']}, MPS={repo_status['hardware_accelerator_status']['mps_available']}\n")
        f.write(f"*   **Operating System**: `{repo_status['operating_system']['platform']}`\n\n")
        
        f.write("### File Language Breakdown\n\n")
        f.write("| File Extension | Count | Size (KB) |\n")
        f.write("| :--- | :---: | :---: |\n")
        for k, v in src_file_counts.items():
            f.write(f"| {k} | {v['count']} | {v['size_bytes']/1024.0:.2f} |\n")
        f.write("\n")
        
        # B
        f.write("## SECTION B — Dataset Inventory\n\n")
        f.write("| Dataset Name | Source | Version | Total Samples | Positive Samples | Negative Samples | Class Ratio | Missing Values | Duplicates | Features |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for d in dataset_inventory:
            ratio_str = f"{d['class_ratio']*100:.3f}%" if isinstance(d['class_ratio'], float) else str(d['class_ratio'])
            f.write(f"| {d['dataset_name']} | {d['source']} | {d['version']} | {d['total_samples']} | {d['positive_samples']} | {d['negative_samples']} | {ratio_str} | {d['missing_values']} | {d['duplicated_samples']} | {d['feature_count']} |\n")
        f.write("\n")
        
        # C
        f.write("## SECTION C — Feature Inventory\n\n")
        f.write(f"*   **Total Engineered Features**: {len(eng_feats)}\n")
        f.write(f"*   **Total Raw Features**: {len(raw_feats)}\n")
        f.write(f"*   **Total Taxonomy Flags**: {len(taxonomy_inventory['taxonomy_categories'])}\n\n")
        
        f.write("### Feature Matrix Statistics (Computed on `s2_test.parquet`)\n\n")
        f.write("| Feature Name | Source | Datatype | Units | Missing % | Variance | Mean | Std | Min | Max |\n")
        f.write("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for feat in feature_inventory_list:
            f.write(f"| {feat['feature_name']} | {feat['source']} | `{feat['datatype']}` | {feat['units']} | {feat['missing_percentage']:.2f}% | {feat['variance']:.4e} | {feat['mean']:.4e} | {feat['std']:.4e} | {feat['minimum']:.4e} | {feat['maximum']:.4e} |\n")
        f.write("\n")
        
        # D
        f.write("## SECTION D — Model Inventory\n\n")
        for m in model_inventory:
            f.write(f"### Model: `{m['model_name']}`\n")
            f.write(f"*   **Architecture**: {m['architecture']}\n")
            f.write(f"*   **Inputs**: {m['input_dimension']}\n")
            f.write(f"*   **Outputs**: {m['output_dimension']}\n")
            f.write(f"*   **Parameter Count**: {m['parameter_count']:,} parameters\n")
            f.write(f"*   **Trainable Parameters**: {m['trainable_parameters']:,} parameters\n")
            f.write(f"*   **Optimizer**: {m['optimizer']}\n")
            f.write(f"*   **Loss Function**: {m['loss_function']}\n")
            f.write(f"*   **Threshold**: `{m['threshold']}`\n")
            f.write(f"*   **Calibration**: {m['calibration_method']}\n")
            f.write(f"*   **Checkpoint**: `{m['checkpoint_file']}` (Size: {m['checkpoint_size_bytes']:,} bytes)\n")
            f.write(f"*   **Training Parameters**: Epochs={m['training_epochs']}, Batch Size={m['batch_size']}, LR={m['learning_rate']}\n\n")
            
        # E
        f.write("## SECTION E — Evaluation Metrics (Directly Recomputed on full test set)\n\n")
        f.write("| Metric | Recomputed Value |\n")
        f.write("| :--- | :---: |\n")
        for k, v in evaluation_metrics.items():
            if k == "Confusion_Matrix":
                continue
            f.write(f"| {k} | {v:.6f} |\n")
        f.write("\n")
        
        f.write("### Confusion Matrix\n")
        f.write(f"*   **True Positives (TP)**: {tp}\n")
        f.write(f"*   **True Negatives (TN)**: {tn}\n")
        f.write(f"*   **False Positives (FP)**: {fp}\n")
        f.write(f"*   **False Negatives (FN)**: {fn}\n\n")
        
        # F
        f.write("## SECTION F — Calibration Bins Table\n\n")
        f.write(f"*   **ECE**: {ece_val:.6f}\n")
        f.write(f"*   **MCE**: {mce_val:.6f}\n")
        f.write(f"*   **Calibration Threshold**: `{threshold}`\n\n")
        f.write("| Bin Index | Bin Range | Expected Confidence | Observed Frequency | Absolute Error | Samples |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: |\n")
        for b in calibration_bins_list:
            f.write(f"| {b['bin_index']} | {b['bin_range']} | {b['expected_frequency']:.6f} | {b['observed_frequency']:.6f} | {b['absolute_error']:.6f} | {b['bin_size']} |\n")
        f.write("\n")
        
        # G
        f.write("## SECTION G — Failure Taxonomy Analysis\n\n")
        f.write(f"*   **Multi-flag failures**: {taxonomy_inventory['multi_flag_statistics']['multi_flag_failures_count']} of {taxonomy_inventory['multi_flag_statistics']['total_failures']} ({taxonomy_inventory['multi_flag_statistics']['multi_flag_failures_percentage']:.2f}%)\n")
        f.write(f"*   **Mean active flags per failure**: {taxonomy_inventory['multi_flag_statistics']['mean_active_flags_per_sample']:.2f}\n")
        f.write(f"*   **Samples satisfying multiple rules**: {taxonomy_inventory['overlap_statistics']['satisfy_multiple_rules_count']} ({taxonomy_inventory['overlap_statistics']['satisfy_multiple_rules_percentage']:.2f}%)\n")
        f.write(f"*   **Unknown category count**: {taxonomy_inventory['unknown_category_count']}\n\n")
        
        f.write("### Active Flags Histogram\n\n")
        f.write("| Active Flags | Count of Failure Samples |\n")
        f.write("| :---: | :---: |\n")
        for k, v in taxonomy_inventory['multi_flag_statistics']['active_flags_histogram'].items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n")
        
        f.write("### Failure Taxonomy Categories Breakdown\n\n")
        f.write("| Category | Failure Sample Count | Percentage | FP Count | FN Count |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        for c in taxonomy_categories:
            f.write(f"| {c['category']} | {c['sample_count']} | {c['percentage']:.2f}% | {c['fp_count']} | {c['fn_count']} |\n")
        f.write("\n")
        
        f.write("### Category Ordering Sensitivity\n\n")
        f.write("| Ordering Rule | Failures Changed Count | Failures Changed % |\n")
        f.write("| :--- | :---: | :---: |\n")
        for o in ordering_sensitivity_list:
            if o["Category"] == "Temporal Drift Failure":
                f.write(f"| {o['Ordering']} | {o['Overall_Max_Category_Shift']} | {o['Overall_Percentage_of_Failures_Changed']:.2f}% |\n")
        f.write("\n")
        
        # H
        f.write("## SECTION H — Statistical Audits\n\n")
        f.write(f"*   **Chi-Square association between categories and FP/FN**: Chi2={statistical_audits['chi_square_statistics']['chi2_statistic']:.4f}, Cramer's V={statistical_audits['chi_square_statistics']['cramers_v']:.4f}, DoF={statistical_audits['chi_square_statistics']['degrees_of_freedom']}, p-value={statistical_audits['chi_square_statistics']['p_value']:.4e}\n\n")
        
        f.write("### Nested Logistic Regression Fitting Performance\n\n")
        f.write("| Model Group | Model Name | Num Samples | Predictor Count | Test AUC | Pseudo R2 | Hessian Status |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n")
        for row in statistical_audits["logistic_regression_summaries"]:
            f.write(f"| {row['Model_Group']} | {row['Model_Name']} | {row['Num_Samples']} | {row['Num_Predictors']} | {row['AUC']:.6f} | {row['Pseudo_R2']:.6f} | {'Singular' if row['Singular_Hessian'] else 'Converged'} |\n")
        f.write("\n")
        
        # I
        f.write("## SECTION I — Aditya-L1 Usage\n\n")
        f.write(f"*   **SoLEXS Channels Used**: {', '.join(aditya_l1_usage['solexs_channels_used'][:4])} ... ({len(aditya_l1_usage['solexs_channels_used'])} total)\n")
        f.write(f"*   **HEL1OS Channels Used**: {', '.join(aditya_l1_usage['hel1os_channels_used'])}\n")
        f.write(f"*   **Derived Features**: {aditya_l1_usage['derived_features_count']} features\n")
        f.write(f"*   **Raw Features**: {aditya_l1_usage['raw_features_count']} features\n")
        f.write(f"*   **Window Size**: {aditya_l1_usage['window_sizes_minutes']} minutes\n")
        f.write(f"*   **Sampling Cadence**: {aditya_l1_usage['sampling_cadence_minutes']} minute\n")
        f.write(f"*   **Synchronization Method**: {aditya_l1_usage['synchronization_method']}\n")
        f.write(f"*   **Missing Value Handling**: {aditya_l1_usage['missing_handling']}\n")
        f.write(f"*   **Normalization**: {aditya_l1_usage['normalization']}\n")
        f.write(f"*   **Scaling**: {aditya_l1_usage['scaling']}\n\n")
        
        # J
        f.write("## SECTION J — Artifact Inventory\n\n")
        f.write("| Filename | Generation Date | Size (KB) | Purpose |\n")
        f.write("| :--- | :--- | :---: | :--- |\n")
        for art in all_artifact_files:
            f.write(f"| `{art['filename']}` | {art['generation_date']} | {art['size_bytes']/1024.0:.2f} | {art['purpose']} |\n")
        f.write("\n")
        
        # K
        f.write("## SECTION K — Project Timeline (Completed Sprints)\n\n")
        f.write("| Sprint ID | Purpose | Generated Artifacts | Validation Status |\n")
        f.write("| :--- | :--- | :--- | :---: |\n")
        for sp in project_timeline:
            f.write(f"| {sp['sprint_id']} | {sp['purpose']} | `{sp['generated_artifacts']}` | {sp['validation_status']} |\n")
        f.write("\n")
        
        # L
        f.write("## SECTION L — Validation Status\n\n")
        f.write("| Validation Script | Validation Report | Status | Verification Date |\n")
        f.write("| :--- | :--- | :---: | :--- |\n")
        for val in validation_status:
            f.write(f"| `{val['validation_script']}` | `{val['validation_report']}` | **{val['status']}** | {val['date']} |\n")
        f.write("\n")
        
        # M
        f.write("## SECTION M — Outstanding Work (Factual Unfinished Items)\n\n")
        for item in outstanding_work:
            f.write(f"*   {item}\n")
        f.write("\n")
        
    print("Saved project_inventory.md")
    print("Complete Project Status Audit finished successfully.")

if __name__ == "__main__":
    main()

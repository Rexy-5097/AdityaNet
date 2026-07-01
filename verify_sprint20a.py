import os
import sys
import json
import hashlib
import platform
import re
import numpy as np
import pandas as pd
import torch
import importlib.metadata

# Set path to project root
sys.path.insert(0, os.getcwd())

def get_sha256(path):
    if not os.path.exists(path):
        return "absent"
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "absent"

def get_checkpoint_details(path):
    if not os.path.exists(path):
        return {"status": "Missing"}
    try:
        ckpt = torch.load(path, map_location='cpu')
        state_dict = None
        
        if isinstance(ckpt, dict):
            if 'state_dict' in ckpt:
                state_dict = ckpt['state_dict']
            elif 'model_state_dict' in ckpt:
                state_dict = ckpt['model_state_dict']
            elif 'model' in ckpt:
                state_dict = ckpt['model']
            else:
                state_dict = ckpt
        else:
            state_dict = getattr(ckpt, 'state_dict', lambda: None)()
            
        if state_dict is None:
            return {"status": "Error", "message": "No state_dict found"}
            
        param_count = 0
        for k, v in state_dict.items():
            if isinstance(v, torch.Tensor):
                param_count += v.numel()
                
        return {
            "status": "OK",
            "parameter_count": param_count
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}

def main():
    print("=== STARTING INDEPENDENT SPRINT 20A VERIFICATION ===")
    
    results_summary = {}
    mismatches = []
    
    def log_mismatch(section, field, exp, obs):
        mismatches.append({
            "section": section,
            "field": field,
            "expected": exp,
            "observed": obs
        })
        print(f"  [MISMATCH] {section} - {field}: Expected='{exp}', Observed='{obs}'")

    # 1. Training Configuration & Hyperparameters
    print("\nVerifying 1 & 2. Training Configuration & Hyperparameters...")
    config_ok = True
    try:
        df_cfg = pd.read_csv("artifacts/sprint20a/training_configuration.csv")
        # Verify scheduler is not used in run_sprint14c_experiment.py
        with open("scratch/run_sprint14c_experiment.py", "r") as f:
            exp_script_content = f.read()
        
        if "lr_scheduler" in exp_script_content or "CosineAnnealingLR" in exp_script_content:
            pass
        else:
            # Scheduler is not present in the experiment script
            row_sched = df_cfg[df_cfg["hyperparameter"] == "scheduler"]
            if not row_sched.empty:
                reported_val = row_sched.iloc[0]["value"]
                log_mismatch(
                    "Training Configuration", 
                    "scheduler", 
                    "None (run_sprint14c_experiment.py has no scheduler)", 
                    reported_val
                )
                config_ok = False
    except Exception as e:
        log_mismatch("Training Configuration", "Load Error", "CSV file loaded", str(e))
        config_ok = False
    results_summary["Training configuration"] = "PASS" if config_ok else "FAIL"

    # 3. Dataset Balance
    print("\nVerifying 3. Dataset Balance...")
    balance_ok = True
    try:
        df_bal = pd.read_csv("artifacts/sprint20a/dataset_balance.csv")
        datasets = {
            "train_v3.parquet": "artifacts/research_v3/train_v3.parquet",
            "validation_v3.parquet": "artifacts/research_v3/validation_v3.parquet",
            "test_v3.parquet": "artifacts/research_v3/test_v3.parquet",
            "s2_train.parquet": "artifacts/sprint14c/s2_train.parquet",
            "s2_val.parquet": "artifacts/sprint14c/s2_val.parquet",
            "s2_test.parquet": "artifacts/sprint14c/s2_test.parquet"
        }
        for idx, row in df_bal.iterrows():
            name = row["dataset_split"]
            path = datasets.get(name)
            if path and os.path.exists(path):
                df = pd.read_parquet(path, columns=["target_6hr_binary"])
                tot = len(df)
                pos = int((df["target_6hr_binary"] == 1).sum())
                neg = tot - pos
                
                if row["total_rows"] != tot:
                    log_mismatch("Dataset Balance", f"{name}.total_rows", tot, row["total_rows"])
                    balance_ok = False
                if row["positive_count"] != pos:
                    log_mismatch("Dataset Balance", f"{name}.positive_count", pos, row["positive_count"])
                    balance_ok = False
                if row["negative_count"] != neg:
                    log_mismatch("Dataset Balance", f"{name}.negative_count", neg, row["negative_count"])
                    balance_ok = False
    except Exception as e:
        log_mismatch("Dataset Balance", "Verification Error", "Success", str(e))
        balance_ok = False
    results_summary["Dataset balance"] = "PASS" if balance_ok else "FAIL"

    # 4. Feature Inventory / Usage
    print("\nVerifying 4. Feature Inventory...")
    feature_ok = True
    try:
        df_feat = pd.read_csv("artifacts/sprint20a/feature_usage.csv")
        # Features check: GOES (14), SoLEXS (18), HEL1OS (4)
        goes_count = len(df_feat[df_feat["instrument_category"] == "GOES"])
        solexs_count = len(df_feat[df_feat["instrument_category"] == "SoLEXS"])
        hel1os_count = len(df_feat[df_feat["instrument_category"] == "HEL1OS"])
        
        if goes_count != 14:
            log_mismatch("Feature Inventory", "GOES features count", 14, goes_count)
            feature_ok = False
        if solexs_count != 18:
            log_mismatch("Feature Inventory", "SoLEXS features count", 18, solexs_count)
            feature_ok = False
        if hel1os_count != 4:
            log_mismatch("Feature Inventory", "HEL1OS features count", 4, hel1os_count)
            feature_ok = False
    except Exception as e:
        log_mismatch("Feature Inventory", "Verification Error", "Success", str(e))
        feature_ok = False
    results_summary["Feature inventory"] = "PASS" if feature_ok else "FAIL"

    # 5. Loss Configuration
    print("\nVerifying 5. Loss Configuration...")
    loss_ok = True
    try:
        df_loss = pd.read_csv("artifacts/sprint20a/loss_configuration.csv")
        # Line range check in trainer_v3.py
        with open("app/services/ml/trainer_v3.py", "r") as f:
            lines = f.readlines()
        loss_lines = "".join(lines[43:60]) # lines 44 to 60 (0-indexed 43 to 60)
        if "class FocalLoss" not in loss_lines:
            log_mismatch("Loss Configuration", "Line range check L44-60", "class FocalLoss", "Not found in range")
            loss_ok = False
    except Exception as e:
        log_mismatch("Loss Configuration", "Verification Error", "Success", str(e))
        loss_ok = False
    results_summary["Loss configuration"] = "PASS" if loss_ok else "FAIL"

    # 6. Training Scripts existence
    print("\nVerifying 6. Training Scripts...")
    scripts_ok = True
    try:
        df_scr = pd.read_csv("artifacts/sprint20a/training_scripts.csv")
        for idx, row in df_scr.iterrows():
            path = row["path"]
            if not os.path.exists(path):
                log_mismatch("Training Scripts", f"{path} existence", True, False)
                scripts_ok = False
            else:
                sz = os.path.getsize(path)
                if row["size_bytes"] != sz:
                    log_mismatch("Training Scripts", f"{path} size_bytes", sz, row["size_bytes"])
                    scripts_ok = False
                    
        # Check omission: pilot_train_v3.py
        if os.path.exists("scratch/pilot_train_v3.py"):
            if not any(row["path"] == "scratch/pilot_train_v3.py" for _, row in df_scr.iterrows()):
                log_mismatch("Training Scripts Omissions", "scratch/pilot_train_v3.py inclusion", "Included", "Omitted")
                scripts_ok = False
    except Exception as e:
        log_mismatch("Training Scripts", "Verification Error", "Success", str(e))
        scripts_ok = False
    results_summary["Training scripts"] = "PASS" if scripts_ok else "FAIL"

    # 7. Experiment Inventory
    print("\nVerifying 7. Experiment Inventory...")
    exp_ok = True
    try:
        df_exp = pd.read_csv("artifacts/sprint20a/experiment_inventory.csv")
        for idx, row in df_exp.iterrows():
            path = row["checkpoint_path"]
            if os.path.exists(path):
                details = get_checkpoint_details(path)
                if details["status"] == "OK":
                    act_param = details["parameter_count"]
                    rep_param = row["total_parameter_count"]
                    if act_param != rep_param:
                        log_mismatch("Experiment Inventory", f"{path} parameter count", act_param, rep_param)
                        exp_ok = False
    except Exception as e:
        log_mismatch("Experiment Inventory", "Verification Error", "Success", str(e))
        exp_ok = False
    results_summary["Experiment inventory"] = "PASS" if exp_ok else "FAIL"

    # 8. Reproducibility Information
    print("\nVerifying 8. Reproducibility Information...")
    repro_ok = True
    try:
        df_rep = pd.read_csv("artifacts/sprint20a/reproducibility_audit.csv")
        
        # Verify package versions
        actual_versions = {
            "python_version": sys.version.split()[0],
            "numpy_version": importlib.metadata.version("numpy"),
            "pandas_version": importlib.metadata.version("pandas"),
            "pytorch_version": importlib.metadata.version("torch"),
            "scikit_learn_version": importlib.metadata.version("scikit-learn"),
            "scipy_version": importlib.metadata.version("scipy")
        }
        
        for idx, row in df_rep.iterrows():
            param = row["reproducibility_parameter"]
            val = str(row["value"])
            
            if param in actual_versions:
                act_val = actual_versions[param]
                if act_val != val:
                    log_mismatch("Reproducibility Environment", param, act_val, val)
                    repro_ok = False
            elif param.startswith("hash_"):
                # Check hashes
                path_map = {
                    "hash_s2_test_parquet": "artifacts/sprint14c/s2_test.parquet",
                    "hash_model_seed_42_stage2_best_pt": "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt",
                    "hash_calibrator_pkl": "artifacts/calibrator.pkl",
                    "hash_patchtst_best_pt": "artifacts/models/patchtst_best.pt"
                }
                path = path_map.get(param)
                if path:
                    act_hash = get_sha256(path)
                    if act_hash != val:
                        log_mismatch("Reproducibility Hashes", param, act_hash, val)
                        repro_ok = False
    except Exception as e:
        log_mismatch("Reproducibility Information", "Verification Error", "Success", str(e))
        repro_ok = False
    results_summary["Reproducibility information"] = "PASS" if repro_ok else "FAIL"

    # 9. Compute Inventory
    print("\nVerifying 9. Compute Inventory...")
    compute_ok = True
    try:
        df_comp = pd.read_csv("artifacts/sprint20a/compute_inventory.csv")
        
        # Check files sizes
        path_map = {
            "size_train_v3_parquet_mb": "artifacts/research_v3/train_v3.parquet",
            "size_validation_v3_parquet_mb": "artifacts/research_v3/validation_v3.parquet",
            "size_test_v3_parquet_mb": "artifacts/research_v3/test_v3.parquet",
            "size_s2_train_parquet_mb": "artifacts/sprint14c/s2_train.parquet",
            "size_s2_test_parquet_mb": "artifacts/sprint14c/s2_test.parquet",
            "size_stage2_best_checkpoint_mb": "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt"
        }
        
        for idx, row in df_comp.iterrows():
            metric = row["compute_metric"]
            raw_val = row["value"]
            
            try:
                val = float(raw_val)
            except ValueError:
                # String value (e.g. mps (Apple Silicon GPU))
                if metric == "hardware_accelerator":
                    if "mps" not in str(raw_val).lower():
                        log_mismatch("Compute Inventory Accelerator", metric, "mps", raw_val)
                        compute_ok = False
                continue
            
            path = path_map.get(metric)
            if path:
                act_size_mb = round(os.path.getsize(path) / 1e6, 2)
                if abs(act_size_mb - val) > 1e-2:
                    log_mismatch("Compute Inventory Size", metric, act_size_mb, val)
                    compute_ok = False
    except Exception as e:
        log_mismatch("Compute Inventory", "Verification Error", "Success", str(e))
        compute_ok = False
    results_summary["Compute inventory"] = "PASS" if compute_ok else "FAIL"

    # 10. Scientific Inventory
    print("\nVerifying 10. Scientific Inventory...")
    sci_ok = True
    try:
        df_sci = pd.read_csv("artifacts/sprint20a/scientific_inventory.csv")
        # Verify existence of reported validation reports
        for idx, row in df_sci.iterrows():
            art = row["artifacts_found"]
            if art == "none" or pd.isna(art):
                continue
            
            # Find all filenames in the string
            filenames = re.findall(r"([a-zA-Z0-9_]+\.(?:json|csv|md|pt))", art)
            # Find all directories in the string (starts with artifacts/ and ends with /)
            directories = re.findall(r"(artifacts/[a-zA-Z0-9_/]+)", art)
            
            # If directories are found, we associate files with directories
            if directories:
                # If there's only one directory
                if len(directories) == 1:
                    folder = directories[0]
                    for f in filenames:
                        full_path = os.path.join(folder, f)
                        if not os.path.exists(full_path):
                            log_mismatch("Scientific Inventory", f"{full_path} existence", True, False)
                            sci_ok = False
                else:
                    # If multiple directories
                    segments = re.findall(r"([a-zA-Z0-9_]+\.(?:json|csv|md|pt))\s+in\s+(artifacts/[a-zA-Z0-9_/]+)", art)
                    for f, folder in segments:
                        full_path = os.path.join(folder.strip(), f.strip())
                        if not os.path.exists(full_path):
                            log_mismatch("Scientific Inventory", f"{full_path} existence", True, False)
                            sci_ok = False
            else:
                # No directory found, check root and artifacts/
                for f in filenames:
                    paths_to_check = [f, os.path.join("artifacts", f)]
                    if not any(os.path.exists(p) for p in paths_to_check):
                        log_mismatch("Scientific Inventory", f"{f} existence", True, False)
                        sci_ok = False
    except Exception as e:
        log_mismatch("Scientific Inventory", "Verification Error", "Success", str(e))
        sci_ok = False
    results_summary["Scientific inventory"] = "PASS" if sci_ok else "FAIL"

    # ──────────────────────────────────────────────────────────────────────────
    # Overall Status Summary
    # ──────────────────────────────────────────────────────────────────────────
    print("\n==============================================")
    overall_pass = all(status == "PASS" for status in results_summary.values())
    overall_status = "PASS" if overall_pass else "FAIL"
    print(f"OVERALL VALIDATION STATUS: {overall_status}")
    print("==============================================")
    for check_name, status in results_summary.items():
        print(f" - {check_name}: {status}")
    print("==============================================")
    
    # Save the output summary to scratch
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/validation_summary_20a.json", "w") as f:
        json.dump({
            "results_summary": results_summary,
            "overall_status": overall_status,
            "mismatches": mismatches
        }, f, indent=2)
    print("Saved scratch/validation_summary_20a.json")

if __name__ == "__main__":
    main()

import os
import re
import sys
import yaml
import json
import pandas as pd
from datetime import datetime

def check_file_exists(path):
    return os.path.exists(path)

def get_mtime(path):
    if os.path.exists(path):
        return datetime.fromtimestamp(os.path.getmtime(path))
    return None

def main():
    root = "/Users/soumyadebtripathy/AdityaNet"
    sprint21a_dir = os.path.join(root, "artifacts/sprint21a")
    
    print("==================================================")
    print("Sprint 21A Independent Verification Script")
    print("==================================================")
    
    discrepancies = []
    
    # -------------------------------------------------------------------------
    # 1. Every configuration parameter matches repository source code.
    # -------------------------------------------------------------------------
    print("\n--- Check 1: Configuration Parameters vs Source Code ---")
    config_path = os.path.join(sprint21a_dir, "training_campaign_config.yaml")
    if not check_file_exists(config_path):
        discrepancies.append(f"Missing config file: {config_path}")
    else:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        references = config.get("repository_references", {})
        
        # Verify scheduler_source: "trainer_v3.py (L177 CosineAnnealingLR)"
        scheduler_ref = references.get("scheduler_source", "")
        print(f"Checking scheduler_ref: {scheduler_ref}")
        trainer_path = os.path.join(root, "app/services/ml/trainer_v3.py")
        if not check_file_exists(trainer_path):
            discrepancies.append(f"trainer_v3.py does not exist at {trainer_path}")
        else:
            with open(trainer_path, "r") as f:
                trainer_lines = f.readlines()
            # L177 (1-indexed is line 176 in 0-indexed list)
            l177_code = trainer_lines[176].strip()
            print(f"trainer_v3.py L177: {l177_code}")
            if "CosineAnnealingLR" not in l177_code:
                discrepancies.append(f"scheduler_source mismatch: trainer_v3.py L177 code is '{l177_code}', expected 'CosineAnnealingLR'")
                
        # Verify optimizer_source: "run_sprint14c_experiment.py (L345 AdamW)"
        optimizer_ref = references.get("optimizer_source", "")
        print(f"Checking optimizer_ref: {optimizer_ref}")
        experiment_script_path = os.path.join(root, "scratch/run_sprint14c_experiment.py")
        if not check_file_exists(experiment_script_path):
            discrepancies.append(f"run_sprint14c_experiment.py does not exist at {experiment_script_path}")
        else:
            with open(experiment_script_path, "r") as f:
                exp_lines = f.readlines()
            l345_code = exp_lines[344].strip()
            print(f"run_sprint14c_experiment.py L345: {l345_code}")
            if "AdamW" not in l345_code:
                discrepancies.append(f"optimizer_source mismatch: run_sprint14c_experiment.py L345 code is '{l345_code}', expected 'AdamW'")
                
        # Verify learning_rate_stage1_source: "run_sprint14c_experiment.py (L295 1e-4)"
        lr_s1_ref = references.get("learning_rate_stage1_source", "")
        print(f"Checking lr_s1_ref: {lr_s1_ref}")
        if check_file_exists(experiment_script_path):
            l295_code = exp_lines[294].strip()
            print(f"run_sprint14c_experiment.py L295: {l295_code}")
            if "lr=1e-4" not in l295_code and "1e-4" not in l295_code:
                discrepancies.append(f"learning_rate_stage1_source mismatch: run_sprint14c_experiment.py L295 code is '{l295_code}', expected '1e-4'")
                
        # Verify learning_rate_stage2_source: "run_sprint14c_experiment.py (L345 5e-5)"
        lr_s2_ref = references.get("learning_rate_stage2_source", "")
        print(f"Checking lr_s2_ref: {lr_s2_ref}")
        if check_file_exists(experiment_script_path):
            l345_code = exp_lines[344].strip()
            print(f"run_sprint14c_experiment.py L345: {l345_code}")
            if "lr=5e-5" not in l345_code and "5e-5" not in l345_code:
                discrepancies.append(f"learning_rate_stage2_source mismatch: run_sprint14c_experiment.py L345 code is '{l345_code}', expected '5e-5'")
                
        # Verify weight_decay_source: "run_sprint14c_experiment.py (L295 1e-4)"
        wd_ref = references.get("weight_decay_source", "")
        print(f"Checking wd_ref: {wd_ref}")
        if check_file_exists(experiment_script_path):
            l295_code = exp_lines[294].strip()
            print(f"run_sprint14c_experiment.py L295: {l295_code}")
            if "weight_decay=1e-4" not in l295_code and "1e-4" not in l295_code:
                discrepancies.append(f"weight_decay_source mismatch: run_sprint14c_experiment.py L295 code is '{l295_code}', expected '1e-4'")
                
        # Verify dropout_source: "model_v3.py (L166 0.2)"
        dropout_ref = references.get("dropout_source", "")
        print(f"Checking dropout_ref: {dropout_ref}")
        model_path = os.path.join(root, "app/services/ml/model_v3.py")
        if not check_file_exists(model_path):
            discrepancies.append(f"model_v3.py does not exist at {model_path}")
        else:
            with open(model_path, "r") as f:
                model_lines = f.readlines()
            l166_code = model_lines[165].strip()
            print(f"model_v3.py L166: {l166_code}")
            if "0.2" not in l166_code:
                discrepancies.append(f"dropout_source mismatch: model_v3.py L166 code is '{l166_code}', expected '0.2'")
                
        # Verify focal_loss_gamma_source: "trainer_v3.py (L45 2.0)"
        gamma_ref = references.get("focal_loss_gamma_source", "")
        print(f"Checking gamma_ref: {gamma_ref}")
        if check_file_exists(trainer_path):
            l45_code = trainer_lines[44].strip()
            print(f"trainer_v3.py L45: {l45_code}")
            if "gamma: float = 2.0" not in l45_code and "2.0" not in l45_code:
                discrepancies.append(f"focal_loss_gamma_source mismatch: trainer_v3.py L45 code is '{l45_code}', expected '2.0'")
                
        # Verify focal_loss_alpha_source: "trainer_v3.py (L46-47 clamped dynamic alpha)"
        alpha_ref = references.get("focal_loss_alpha_source", "")
        print(f"Checking alpha_ref: {alpha_ref}")
        if check_file_exists(trainer_path):
            l46_code = trainer_lines[45].strip()
            l47_code = trainer_lines[46].strip()
            l48_code = trainer_lines[47].strip()
            print(f"trainer_v3.py L46: {l46_code}")
            print(f"trainer_v3.py L47: {l47_code}")
            print(f"trainer_v3.py L48: {l48_code}")
            # The clamped dynamic alpha is at L48, but the reference says L46-47
            if "clamp" not in l46_code and "clamp" not in l47_code:
                discrepancies.append(f"focal_loss_alpha_source mismatch: trainer_v3.py lists 'clamped dynamic alpha' on line 48 ('{l48_code}'), not lines 46-47 which contain '{l46_code.strip()}' and '{l47_code.strip()}'")

        # Verify proposed_campaign_configuration parameters vs source defaults/capabilities
        proposed = config.get("proposed_campaign_configuration", {})
        # Verify scheduler is CosineAnnealingLR, but run_sprint14c_experiment.py has no scheduler
        print("Checking scheduler in training script run_sprint14c_experiment.py...")
        if check_file_exists(experiment_script_path):
            with open(experiment_script_path, "r") as f:
                exp_content = f.read()
            if "lr_scheduler" in exp_content or "CosineAnnealingLR" in exp_content:
                print("Scheduler found in run_sprint14c_experiment.py")
            else:
                discrepancies.append("Proposed campaign configuration specifies 'scheduler: CosineAnnealingLR', but run_sprint14c_experiment.py does not implement or step any learning rate scheduler (validated also in Sprint 20B).")
                
    # -------------------------------------------------------------------------
    # 2. Every generated training command references existing files.
    # -------------------------------------------------------------------------
    print("\n--- Check 2: Generated Training Commands ---")
    commands_path = os.path.join(sprint21a_dir, "campaign_commands.sh")
    if not check_file_exists(commands_path):
        discrepancies.append(f"Missing commands script: {commands_path}")
    else:
        with open(commands_path, "r") as f:
            commands_content = f.read()
        lines = [l.strip() for l in commands_content.split("\n") if l.strip() and not l.strip().startswith("#")]
        for l in lines:
            print(f"Command line: {l}")
            # Look for python script path
            match = re.search(r"python3\s+([^\s]+)", l)
            if match:
                script_rel_path = match.group(1)
                script_abs_path = os.path.join(root, script_rel_path)
                if not check_file_exists(script_abs_path):
                    discrepancies.append(f"Training command references non-existent script: {script_rel_path} (resolved to {script_abs_path})")
                else:
                    print(f"Verified existence of training script: {script_rel_path}")
            else:
                discrepancies.append(f"Could not parse training script from command: {l}")

    # -------------------------------------------------------------------------
    # 3. Every experiment identifier is unique.
    # -------------------------------------------------------------------------
    print("\n--- Check 3: Experiment Identifier Uniqueness ---")
    manifest_path = os.path.join(sprint21a_dir, "training_manifest.csv")
    if not check_file_exists(manifest_path):
        discrepancies.append(f"Missing training manifest: {manifest_path}")
    else:
        manifest_df = pd.read_csv(manifest_path)
        # Naming convention is: V3_S{seed}_E{epochs}_LR{learning_rate}_WD{weight_decay}_{ablation_tag}
        # In manifest, we have checkpoint_name column. Let's see if we extract the experiment ID from it.
        # Checkpoint name has "_best.pt" or "_last.pt" suffix. Experiment identifier is the prefix.
        exp_ids = []
        for name in manifest_df["checkpoint_name"]:
            if name.endswith("_best.pt"):
                exp_ids.append(name[:-8])
            elif name.endswith("_last.pt"):
                exp_ids.append(name[:-8])
            else:
                exp_ids.append(name)
                
        print(f"Experiment identifiers extracted from manifest: {exp_ids}")
        unique_exp_ids = set(exp_ids)
        if len(exp_ids) != len(unique_exp_ids):
            # Find duplicates
            dups = [x for x in unique_exp_ids if exp_ids.count(x) > 1]
            discrepancies.append(f"Duplicate experiment identifiers found in training_manifest.csv: {dups}")
        else:
            print("All experiment identifiers in training_manifest.csv are unique.")

    # -------------------------------------------------------------------------
    # 4. Every checkpoint path exists.
    # -------------------------------------------------------------------------
    print("\n--- Check 4: Checkpoint Paths Existence ---")
    # In training_manifest.csv, we have checkpoint_name column.
    # Let's see if we can resolve these to files.
    # According to checkpoint_standard.md, they are stored under `artifacts/sprint21/checkpoints/`
    checkpoint_standard_path = os.path.join(sprint21a_dir, "checkpoint_standard.md")
    checkpoint_dir_referenced = "artifacts/sprint21/checkpoints/"
    
    if check_file_exists(manifest_path):
        for name in manifest_df["checkpoint_name"]:
            expected_ckpt_path = os.path.join(root, checkpoint_dir_referenced, name)
            if not check_file_exists(expected_ckpt_path):
                discrepancies.append(f"Checkpoint path does not exist on disk: {os.path.join(checkpoint_dir_referenced, name)} (resolved to {expected_ckpt_path})")
            else:
                print(f"Verified existence of checkpoint: {expected_ckpt_path}")
                
    # -------------------------------------------------------------------------
    # 5. Every dataset path exists.
    # -------------------------------------------------------------------------
    print("\n--- Check 5: Dataset Paths Existence ---")
    # Let's check the dataset splits referenced in evaluation_protocol.md:
    # artifacts/sprint14c/s2_val.parquet
    # artifacts/sprint14c/s2_test.parquet
    eval_protocol_path = os.path.join(sprint21a_dir, "evaluation_protocol.md")
    if not check_file_exists(eval_protocol_path):
        discrepancies.append(f"Missing evaluation protocol: {eval_protocol_path}")
    else:
        with open(eval_protocol_path, "r") as f:
            eval_content = f.read()
        # Find all .parquet paths
        parquet_matches = re.findall(r"artifacts/[^\s,\)\`]+.parquet", eval_content)
        print(f"Parquet paths found in evaluation_protocol.md: {parquet_matches}")
        for p in parquet_matches:
            abs_p = os.path.join(root, p)
            if not check_file_exists(abs_p):
                discrepancies.append(f"Dataset path referenced in evaluation_protocol.md does not exist: {p} (resolved to {abs_p})")
            else:
                print(f"Verified dataset path from evaluation_protocol.md: {p}")
                
    # Let's check dataset column in training_manifest.csv
    # In manifest: dataset column has value "s2_train"
    # Wait, does s2_train map to s2_train.parquet under artifacts/sprint14c/?
    if check_file_exists(manifest_path):
        for idx, row in manifest_df.iterrows():
            dataset_val = row["dataset"]
            # Let's see if we can resolve s2_train. We assume it means artifacts/sprint14c/s2_train.parquet.
            # Let's search if a file named s2_train.parquet exists.
            if dataset_val == "s2_train":
                expected_p = os.path.join(root, "artifacts/sprint14c/s2_train.parquet")
                if not check_file_exists(expected_p):
                    discrepancies.append(f"Manifest dataset entry 's2_train' points to non-existent file: {expected_p}")
                else:
                    print(f"Verified manifest dataset mapping for 's2_train': {expected_p}")
            else:
                discrepancies.append(f"Unknown dataset entry in manifest row {idx}: '{dataset_val}'")

    # -------------------------------------------------------------------------
    # 6. Every seed appears exactly once.
    # -------------------------------------------------------------------------
    print("\n--- Check 6: Seed Occurrence ---")
    # Let's count occurrences of seeds in config, matrix, manifest, commands
    # In config (seeds: [42, 123, 3407, 2026, 9999]):
    if check_file_exists(config_path):
        seeds_config = config.get("proposed_campaign_configuration", {}).get("seeds", [])
        print(f"Seeds in config: {seeds_config}")
        for s in seeds_config:
            count = seeds_config.count(s)
            if count != 1:
                discrepancies.append(f"Seed {s} appears {count} times in training_campaign_config.yaml proposed seeds list (expected exactly once)")
                
    # In campaign_matrix.csv:
    matrix_path = os.path.join(sprint21a_dir, "campaign_matrix.csv")
    if check_file_exists(matrix_path):
        matrix_df = pd.read_csv(matrix_path)
        seeds_matrix = list(matrix_df["seed"])
        print(f"Seeds in campaign matrix: {seeds_matrix}")
        for s in set(seeds_matrix):
            count = seeds_matrix.count(s)
            if count != 1:
                discrepancies.append(f"Seed {s} appears {count} times in campaign_matrix.csv seed column (expected exactly once)")
                
    # In training_manifest.csv:
    if check_file_exists(manifest_path):
        seeds_manifest = list(manifest_df["seed"])
        print(f"Seeds in training manifest: {seeds_manifest}")
        # Note: seed 42 appears 4 times due to ablation runs!
        for s in set(seeds_manifest):
            count = seeds_manifest.count(s)
            if count != 1:
                discrepancies.append(f"Seed {s} appears {count} times in training_manifest.csv (violates 'Every seed appears exactly once')")

    # -------------------------------------------------------------------------
    # 7. Hyperparameter search ranges match the generated configuration.
    # -------------------------------------------------------------------------
    print("\n--- Check 7: Hyperparameter Ranges vs Config ---")
    space_path = os.path.join(sprint21a_dir, "hyperparameter_space.yaml")
    if not check_file_exists(space_path):
        discrepancies.append(f"Missing search space config: {space_path}")
    else:
        with open(space_path, "r") as f:
            space = yaml.safe_load(f)
        search_space = space.get("hyperparameter_search_space", {})
        train_space = search_space.get("training_parameters", {})
        
        # Verify learning rate:
        lr_bounds = train_space.get("learning_rate", {}).get("bounds", [])
        if check_file_exists(config_path) and check_file_exists(matrix_path):
            # In matrix, we have learning_rate_stage1 (1e-4) and learning_rate_stage2 (5e-5)
            for lr_col in ["learning_rate_stage1", "learning_rate_stage2"]:
                for lr_val in matrix_df[lr_col]:
                    val = float(lr_val)
                    low = float(lr_bounds[0])
                    high = float(lr_bounds[1])
                    if not (low <= val <= high):
                        discrepancies.append(f"Config learning rate {val} from {lr_col} is out of bounds {lr_bounds} defined in hyperparameter_space.yaml")
                    else:
                        print(f"Verified learning rate {val} in range {lr_bounds}")
                        
        # Verify dropout:
        dropout_bounds = train_space.get("dropout", {}).get("bounds", [])
        if check_file_exists(matrix_path):
            for val in matrix_df["dropout"]:
                val = float(val)
                low = float(dropout_bounds[0])
                high = float(dropout_bounds[1])
                if not (low <= val <= high):
                    discrepancies.append(f"Config dropout {val} is out of bounds {dropout_bounds} defined in hyperparameter_space.yaml")
                else:
                    print(f"Verified dropout {val} in range {dropout_bounds}")
                    
        # Verify weight decay:
        wd_bounds = train_space.get("weight_decay", {}).get("bounds", [])
        if check_file_exists(matrix_path):
            for val in matrix_df["weight_decay"]:
                val = float(val)
                low = float(wd_bounds[0])
                high = float(wd_bounds[1])
                if not (low <= val <= high):
                    discrepancies.append(f"Config weight decay {val} is out of bounds {wd_bounds} defined in hyperparameter_space.yaml")
                else:
                    print(f"Verified weight decay {val} in range {wd_bounds}")
                    
        # Verify batch_size choices:
        bs_choices = train_space.get("batch_size", {}).get("choices", [])
        if check_file_exists(matrix_path):
            for val in matrix_df["batch_size"]:
                val = int(val)
                if val not in bs_choices:
                    discrepancies.append(f"Config batch_size {val} is not in choices {bs_choices} defined in hyperparameter_space.yaml")
                else:
                    print(f"Verified batch_size {val} in choices {bs_choices}")
                    
        # Verify optimizer choices:
        opt_choices = train_space.get("optimizer", {}).get("choices", [])
        if check_file_exists(matrix_path):
            for val in matrix_df["optimizer"]:
                if val not in opt_choices:
                    discrepancies.append(f"Config optimizer '{val}' is not in choices {opt_choices} defined in hyperparameter_space.yaml")
                else:
                    print(f"Verified optimizer '{val}' in choices {opt_choices}")
                    
        # Verify scheduler choices:
        sched_choices = train_space.get("scheduler", {}).get("choices", [])
        if check_file_exists(matrix_path):
            for val in matrix_df["scheduler"]:
                if val not in sched_choices:
                    discrepancies.append(f"Config scheduler '{val}' is not in choices {sched_choices} defined in hyperparameter_space.yaml")
                else:
                    print(f"Verified scheduler '{val}' in choices {sched_choices}")

    # -------------------------------------------------------------------------
    # 8. Evaluation protocol references existing evaluation scripts.
    # -------------------------------------------------------------------------
    print("\n--- Check 8: Evaluation Scripts References ---")
    if check_file_exists(eval_protocol_path):
        with open(eval_protocol_path, "r") as f:
            eval_content = f.read()
        # Find all python script matches (.py)
        py_matches = re.findall(r"[a-zA-Z0-9_]+\.py", eval_content)
        print(f"Python scripts found in evaluation_protocol.md: {py_matches}")
        for match in py_matches:
            # Let's search where this script is in the repository
            found_script = False
            for dirpath, _, filenames in os.walk(root):
                if match in filenames:
                    abs_match_path = os.path.join(dirpath, match)
                    print(f"Verified evaluation script exists: {match} (at {abs_match_path})")
                    found_script = True
                    break
            if not found_script:
                discrepancies.append(f"Evaluation protocol references non-existent script: {match}")

    # -------------------------------------------------------------------------
    # 9. Manifest entries are internally consistent.
    # -------------------------------------------------------------------------
    print("\n--- Check 9: Manifest Consistency ---")
    # Verify naming convention V3_S{seed}_E{epochs}_LR{learning_rate}_WD{weight_decay}_{ablation_tag}
    # against manifest row values.
    # Check if commands cover all manifest entries.
    if check_file_exists(manifest_path):
        for idx, row in manifest_df.iterrows():
            seed = row["seed"]
            epochs = row["epochs"]
            opt = row["optimizer"]
            dataset = row["dataset"]
            feat_ver = row["feature_version"]
            arch = row["architecture"]
            ckpt = row["checkpoint_name"]
            exp_type = row["experiment_type"]
            
            # Check checkpoint name format
            # If goes_only -> GOES best, goes_solexs -> GOES_SOLEXS best, goes_hel1os -> GOES_HEL1OS best
            expected_ablation_tag = ""
            if feat_ver == "v3_goes_only":
                expected_ablation_tag = "GOES_"
            elif feat_ver == "v3_goes_solexs":
                expected_ablation_tag = "GOES_SOLEXS_"
            elif feat_ver == "v3_goes_hel1os":
                expected_ablation_tag = "GOES_HEL1OS_"
                
            expected_ckpt_name = f"V3_S{seed}_E{epochs}_LR5e5_WD1e4_{expected_ablation_tag}best.pt"
            if ckpt != expected_ckpt_name:
                discrepancies.append(f"Manifest row {idx} checkpoint name mismatch: got '{ckpt}', expected '{expected_ckpt_name}'")
            else:
                print(f"Row {idx} checkpoint name is consistent: {ckpt}")
                
        # Check command coverage: do we have commands for ablation runs?
        # In manifest, we have:
        # - GOES only ablation (seed=42)
        # - GOES + SoLEXS ablation (seed=42)
        # - GOES + HEL1OS ablation (seed=42)
        # Check if campaign_commands.sh has lines executing these runs.
        # Run A -> GOES only, Run B -> GOES + SoLEXS, Run C -> GOES + HEL1OS
        if check_file_exists(commands_path):
            with open(commands_path, "r") as f:
                commands_text = f.read()
            for ab_feat, ab_type, ab_cmd_opt in [
                ("v3_goes_only", "GOES only", "A"),
                ("v3_goes_solexs", "GOES + SoLEXS", "B"),
                ("v3_goes_hel1os", "GOES + HEL1OS", "C")
            ]:
                # Look for model-type option
                pattern = rf"--model-type\s+{ab_cmd_opt}"
                if not re.search(pattern, commands_text):
                    discrepancies.append(f"Ablation run '{ab_feat}' ({ab_type}) listed in manifest has no corresponding launch command in campaign_commands.sh (expected command with option '--model-type {ab_cmd_opt}')")
                else:
                    print(f"Command found for ablation: {ab_feat}")

    # -------------------------------------------------------------------------
    # 10. No training, inference, checkpoint writing, dataset modification, 
    #     calibration, or threshold optimization occurred during Sprint 21A.
    # -------------------------------------------------------------------------
    print("\n--- Check 10: Training, Inference, Calibration Activity ---")
    # Let's get the modification time of the Sprint 21A summary file
    summary_file = os.path.join(sprint21a_dir, "sprint21a_summary.md")
    if check_file_exists(summary_file):
        summary_mtime = get_mtime(summary_file)
        print(f"Sprint 21A Summary mtime: {summary_mtime}")
        
        # Check checkpoints:
        # Check model_seed_42_stage1_best.pt and model_seed_42_stage2_best.pt in artifacts/sprint14c/checkpoints
        # Check patchtst_best.pt and patchtst_last.pt in artifacts/models
        # Check test_checkpoint.pt in artifacts/models_v3
        pt_files = [
            "artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt",
            "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt",
            "artifacts/models/patchtst_best.pt",
            "artifacts/models/patchtst_last.pt",
            "artifacts/models_v3/test_checkpoint.pt"
        ]
        for pt in pt_files:
            abs_pt = os.path.join(root, pt)
            if check_file_exists(abs_pt):
                pt_mtime = get_mtime(abs_pt)
                print(f"File {pt} mtime: {pt_mtime}")
                # We can report if any of these was modified during or after Sprint 21A creation
                # Wait, if they were modified recently (like today), they might have been created or touched during Sprint 21A development.
                # Let's compare their mtime with the summary file mtime.
                if pt_mtime and summary_mtime and pt_mtime >= summary_mtime:
                    discrepancies.append(f"Checkpoint file {pt} was modified during or after Sprint 21A freeze (mtime: {pt_mtime} >= summary mtime: {summary_mtime})")
                    
        # Check datasets:
        # Check if s2_train.parquet, s2_val.parquet, s2_test.parquet were modified
        parquet_files = [
            "artifacts/sprint14c/s2_train.parquet",
            "artifacts/sprint14c/s2_val.parquet",
            "artifacts/sprint14c/s2_test.parquet"
        ]
        for pq in parquet_files:
            abs_pq = os.path.join(root, pq)
            if check_file_exists(abs_pq):
                pq_mtime = get_mtime(abs_pq)
                print(f"File {pq} mtime: {pq_mtime}")
                if pq_mtime and summary_mtime and pq_mtime >= summary_mtime:
                    discrepancies.append(f"Dataset file {pq} was modified during or after Sprint 21A freeze (mtime: {pq_mtime} >= summary mtime: {summary_mtime})")
                    
        # Check calibration and thresholds files:
        # e.g., calibrator.pkl, operational_thresholds.json, operator_thresholds.json
        calib_files = [
            "artifacts/calibrator.pkl",
            "artifacts/operational_thresholds.json",
            "artifacts/operator_thresholds.json",
            "artifacts/operator_thresholds_validation_only.json"
        ]
        for cf in calib_files:
            abs_cf = os.path.join(root, cf)
            if check_file_exists(abs_cf):
                cf_mtime = get_mtime(abs_cf)
                print(f"File {cf} mtime: {cf_mtime}")
                if cf_mtime and summary_mtime and cf_mtime >= summary_mtime:
                    discrepancies.append(f"Calibration/Threshold file {cf} was modified during or after Sprint 21A freeze (mtime: {cf_mtime} >= summary mtime: {summary_mtime})")

        # Scan the entire workspace for any other checkpoint, dataset, calibration, or training files modified recently
        print("\nScanning workspace for recently modified files...")
        cutoff_date = datetime(2026, 6, 25) # June 25, 2026
        exclude_dirs = {".git", ".gemini", "venv", "artifacts/sprint21a", "scratch"}
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune excluded directories
            rel_dir = os.path.relpath(dirpath, root)
            if any(rel_dir.startswith(d) or rel_dir == d for d in exclude_dirs):
                continue
            for f_name in filenames:
                if f_name.startswith(".") or f_name.endswith(".pyc"):
                    continue
                f_path = os.path.join(dirpath, f_name)
                f_mtime = get_mtime(f_path)
                if f_mtime and f_mtime >= cutoff_date:
                    rel_f_path = os.path.relpath(f_path, root)
                    # Skip files in temporary/cache dirs if any
                    if "cache" in rel_f_path or "logs" in rel_f_path:
                        print(f"Recently modified log/cache file: {rel_f_path} (mtime: {f_mtime})")
                        continue
                    print(f"Recently modified workspace file: {rel_f_path} (mtime: {f_mtime})")
                    if rel_f_path.endswith((".pt", ".pth", ".parquet", ".pkl", ".h5")):
                        discrepancies.append(f"File {rel_f_path} was modified since June 25, 2026 (mtime: {f_mtime}), indicating potential training, inference, or checkpoint writing activity.")

    # Print overall verdict
    print("\n==================================================")
    print("Verification Verdict:")
    print("==================================================")
    if discrepancies:
        print("STATUS: FAIL")
        print("\nDiscrepancies found:")
        for idx, d in enumerate(discrepancies, 1):
            print(f"{idx}. {d}")
    else:
        print("STATUS: PASS")
        print("All validations completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()

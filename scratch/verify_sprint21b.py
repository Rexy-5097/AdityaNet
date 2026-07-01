import os
import re
import sys
import yaml
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
    sprint21b_dir = os.path.join(root, "artifacts/sprint21b")
    
    print("==================================================")
    print("Sprint 21B Independent Verification Script")
    print("==================================================")
    
    failures = []
    minor_corrections = []
    
    # -------------------------------------------------------------------------
    # 1. Historical Repository Verification & 4. Source Reference Verification
    # -------------------------------------------------------------------------
    print("\n--- Check 1 & 4: Historical Repository & Source Reference Verification ---")
    config_path = os.path.join(sprint21b_dir, "corrected_training_campaign_config.yaml")
    if not check_file_exists(config_path):
        failures.append(f"Missing config file: {config_path}")
        return
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    hist_state = config.get("historical_repository_state", {})
    
    # Verify active_training_script
    script_path = os.path.join(root, hist_state.get("active_training_script", ""))
    if not check_file_exists(script_path):
        failures.append(f"Historical training script does not exist: {script_path}")
    else:
        print(f"Verified training script path: {script_path}")
        with open(script_path, "r") as f:
            script_lines = f.readlines()
            
    # Verify stage1_optimizer: AdamW, lr=1e-4, weight_decay=1e-4 at L295
    s1_opt = hist_state.get("stage1_optimizer", {})
    print(f"Checking Stage 1 Optimizer: {s1_opt}")
    if check_file_exists(script_path):
        l295_code = script_lines[294].strip() # 0-indexed line 294 is L295
        print(f"run_sprint14c_experiment.py L295: {l295_code}")
        if s1_opt.get("type") != "AdamW" or "AdamW" not in l295_code:
            failures.append(f"Stage 1 optimizer type mismatch: expected AdamW, got code '{l295_code}'")
        if float(s1_opt.get("learning_rate")) != 1e-4 or "lr=1e-4" not in l295_code:
            failures.append(f"Stage 1 learning rate mismatch: expected 1e-4, got code '{l295_code}'")
        if float(s1_opt.get("weight_decay")) != 1e-4 or "weight_decay=1e-4" not in l295_code:
            failures.append(f"Stage 1 weight decay mismatch: expected 1e-4, got code '{l295_code}'")
            
    # Verify stage2_optimizer: AdamW, lr=5e-5, weight_decay=1e-4 at L345
    s2_opt = hist_state.get("stage2_optimizer", {})
    print(f"Checking Stage 2 Optimizer: {s2_opt}")
    if check_file_exists(script_path):
        l345_code = script_lines[344].strip() # L345
        print(f"run_sprint14c_experiment.py L345: {l345_code}")
        if s2_opt.get("type") != "AdamW" or "AdamW" not in l345_code:
            failures.append(f"Stage 2 optimizer type mismatch: expected AdamW, got code '{l345_code}'")
        if float(s2_opt.get("learning_rate")) != 5e-5 or "lr=5e-5" not in l345_code:
            failures.append(f"Stage 2 learning rate mismatch: expected 5e-5, got code '{l345_code}'")
        if float(s2_opt.get("weight_decay")) != 1e-4 or "weight_decay=1e-4" not in l345_code:
            failures.append(f"Stage 2 weight decay mismatch: expected 1e-4, got code '{l345_code}'")
            
    # Verify gradient_clipping: max_norm: 1.0 at L116
    grad_clip = hist_state.get("gradient_clipping", {})
    if check_file_exists(script_path):
        l116_code = script_lines[115].strip() # L116
        print(f"run_sprint14c_experiment.py L116: {l116_code}")
        if float(grad_clip.get("max_norm")) != 1.0 or "max_norm=1.0" not in l116_code:
            failures.append(f"Gradient clipping mismatch: expected 1.0, got code '{l116_code}'")
            
    # Verify mixed_precision: bfloat16 at L95, autocast at L104
    mp = hist_state.get("mixed_precision", {})
    if check_file_exists(script_path):
        l95_code = script_lines[94].strip() # L95
        l104_code = script_lines[103].strip() # L104
        print(f"run_sprint14c_experiment.py L95: {l95_code}")
        print(f"run_sprint14c_experiment.py L104: {l104_code}")
        if mp.get("dtype") != "bfloat16" or "bfloat16" not in l95_code:
            failures.append(f"Mixed precision dtype mismatch: expected bfloat16, got code '{l95_code}'")
        if mp.get("mechanism") != "torch.amp.autocast" or "autocast" not in l104_code:
            failures.append(f"Mixed precision mechanism mismatch: expected torch.amp.autocast, got code '{l104_code}'")
            
    # Verify grad_scaler enabled_on [mps, cuda] at L277
    grad_scaler = hist_state.get("grad_scaler", {})
    if check_file_exists(script_path):
        l277_code = script_lines[276].strip() # L277
        print(f"run_sprint14c_experiment.py L277: {l277_code}")
        if "GradScaler" not in l277_code or "cuda" not in l277_code or "mps" not in l277_code:
            failures.append(f"Grad scaler mismatch: expected enabled on [mps, cuda] in code, got '{l277_code}'")
            
    # Verify early_stopping: L40, L296, L346
    es = hist_state.get("early_stopping", {})
    if check_file_exists(script_path):
        l40_code = script_lines[39].strip()
        l296_code = script_lines[295].strip()
        l346_code = script_lines[345].strip()
        print(f"run_sprint14c_experiment.py L40: {l40_code}")
        print(f"run_sprint14c_experiment.py L296: {l296_code}")
        print(f"run_sprint14c_experiment.py L346: {l346_code}")
        if es.get("patience") != 10 or "patience=args.patience" not in l296_code or "patience=args.patience" not in l346_code:
            failures.append(f"Early stopping patience mismatch in code: expected default/patience args check, got '{l296_code}'")
        if float(es.get("min_delta")) != 1e-4 or "min_delta=1e-4" not in l296_code or "min_delta=1e-4" not in l346_code:
            failures.append(f"Early stopping min_delta mismatch: expected 1e-4, got code '{l296_code}'")
            
    # Verify focal_loss: gamma: 2.0 at trainer_v3.py L45, alpha_clamp at trainer_v3.py L48
    fl = hist_state.get("focal_loss", {})
    trainer_path = os.path.join(root, "app/services/ml/trainer_v3.py")
    if not check_file_exists(trainer_path):
        failures.append(f"Missing trainer file: {trainer_path}")
    else:
        with open(trainer_path, "r") as f:
            trainer_lines = f.readlines()
        l45_code = trainer_lines[44].strip() # L45
        l48_code = trainer_lines[47].strip() # L48
        print(f"trainer_v3.py L45: {l45_code}")
        print(f"trainer_v3.py L48: {l48_code}")
        if fl.get("gamma") != 2.0 or "gamma: float = 2.0" not in l45_code:
            failures.append(f"Focal loss gamma mismatch: expected 2.0, got code '{l45_code}'")
        if "clamp" not in l48_code or "0.25" not in l48_code or "0.75" not in l48_code:
            failures.append(f"Focal loss alpha clamp mismatch: expected clamp [0.25, 0.75], got code '{l48_code}'")
            
    # Verify dropout: 0.2 at model_v3.py L166
    dropout_val = hist_state.get("dropout")
    model_path = os.path.join(root, "app/services/ml/model_v3.py")
    if not check_file_exists(model_path):
        failures.append(f"Missing model file: {model_path}")
    else:
        with open(model_path, "r") as f:
            model_lines = f.readlines()
        l166_code = model_lines[165].strip() # L166
        print(f"model_v3.py L166: {l166_code}")
        if dropout_val != 0.2 or "0.2" not in l166_code:
            failures.append(f"Dropout mismatch: expected 0.2, got code '{l166_code}'")
            
    # Verify existing checkpoints on disk
    ex_ckpts = hist_state.get("existing_checkpoints", [])
    for ckpt in ex_ckpts:
        abs_ckpt = os.path.join(root, ckpt)
        if not check_file_exists(abs_ckpt):
            failures.append(f"Expected existing checkpoint does not exist: {ckpt} (resolved to {abs_ckpt})")
        else:
            print(f"Verified existing checkpoint on disk: {ckpt}")

    # -------------------------------------------------------------------------
    # 2. Proposed Configuration Verification
    # -------------------------------------------------------------------------
    print("\n--- Check 2: Proposed Configuration Verification ---")
    # Verify section 2 has label PROPOSED
    proposed_cfg = config.get("proposed_campaign_configuration", {})
    if proposed_cfg.get("label") != "PROPOSED":
        failures.append("Proposed campaign configuration is not explicitly labeled as PROPOSED")
    else:
        print("Proposed campaign configuration explicitly labeled PROPOSED.")
        
    proposed_sched = proposed_cfg.get("scheduler", {})
    if proposed_sched.get("label") != "PROPOSED":
        failures.append("Proposed scheduler is not explicitly labeled as PROPOSED")
    else:
        print("Proposed scheduler explicitly labeled PROPOSED.")
        
    proposed_ckpt = proposed_cfg.get("proposed_checkpoint_standard", {})
    if proposed_ckpt.get("label") != "PLANNED_NOT_YET_ACTIVE":
        failures.append("Proposed checkpoint standard is not explicitly labeled as PLANNED_NOT_YET_ACTIVE")
    else:
        print("Proposed checkpoint standard explicitly labeled PLANNED_NOT_YET_ACTIVE.")

    # -------------------------------------------------------------------------
    # 3. Scheduler Verification in run_sprint14c_experiment.py
    # -------------------------------------------------------------------------
    print("\n--- Check 3: Scheduler Verification in run_sprint14c_experiment.py ---")
    if check_file_exists(script_path):
        with open(script_path, "r") as f:
            exp_code = f.read()
        # Verify no scheduler usage or stepping
        if "lr_scheduler" in exp_code:
            failures.append("run_sprint14c_experiment.py contains references to 'lr_scheduler'")
        if "scheduler.step" in exp_code:
            failures.append("run_sprint14c_experiment.py contains 'scheduler.step'")
        if "CosineAnnealingLR" in exp_code:
            failures.append("run_sprint14c_experiment.py contains 'CosineAnnealingLR'")
            
        print("Verified run_sprint14c_experiment.py has no scheduler code.")

    # -------------------------------------------------------------------------
    # 5. Manifest Verification
    # -------------------------------------------------------------------------
    print("\n--- Check 5: Manifest Verification ---")
    manifest_path = os.path.join(sprint21b_dir, "corrected_training_manifest.csv")
    if not check_file_exists(manifest_path):
        failures.append(f"Missing training manifest: {manifest_path}")
        return
        
    manifest_df = pd.read_csv(manifest_path)
    # Check experiment ID uniqueness
    exp_ids = list(manifest_df["experiment_id"])
    if len(exp_ids) != len(set(exp_ids)):
        failures.append(f"Duplicate experiment IDs in manifest: {exp_ids}")
    else:
        print("All experiment IDs in manifest are unique.")
        
    # Check that every launch command exists in campaign_commands.sh
    commands_path = os.path.join(sprint21b_dir, "corrected_campaign_commands.sh")
    if not check_file_exists(commands_path):
        failures.append(f"Missing commands script: {commands_path}")
        return
        
    with open(commands_path, "r") as f:
        commands_content = f.read()
        
    for idx, row in manifest_df.iterrows():
        cmd = row["executable_command"].strip()
        exp_id = row["experiment_id"]
        # Normalize whitespace in command to prevent formatting mismatches
        norm_cmd = " ".join(cmd.split())
        norm_content = " ".join(commands_content.split())
        if norm_cmd not in norm_content:
            failures.append(f"Executable command for experiment '{exp_id}' not found in campaign_commands.sh: '{cmd}'")
        else:
            print(f"Verified command for '{exp_id}' exists in corrected_campaign_commands.sh")
            
        # Verify launch command script exists
        match = re.search(r"python3\s+([^\s]+)", cmd)
        if match:
            cmd_script = match.group(1)
            cmd_script_abs = os.path.join(root, cmd_script)
            if not check_file_exists(cmd_script_abs):
                failures.append(f"Manifest executable command references non-existent script: {cmd_script} (resolved to {cmd_script_abs})")
            else:
                print(f"Verified command script exists: {cmd_script}")
        else:
            failures.append(f"Could not parse script from command: '{cmd}'")
            
    # Check that commands file doesn't have extra executable commands that are not in manifest
    cmd_lines = [l.strip() for l in commands_content.split("\n") if l.strip() and not l.strip().startswith("#")]
    manifest_cmds = [cmd.strip() for cmd in manifest_df["executable_command"]]
    for l in cmd_lines:
        norm_l = " ".join(l.split())
        found = False
        for mc in manifest_cmds:
            norm_mc = " ".join(mc.split())
            if norm_l == norm_mc:
                found = True
                break
        if not found:
            failures.append(f"Command script contains extra command not present in manifest: '{l}'")
        else:
            print(f"Command verified in manifest: '{l}'")

    # -------------------------------------------------------------------------
    # 6. Checkpoint Verification
    # -------------------------------------------------------------------------
    print("\n--- Check 6: Checkpoint Verification ---")
    # Verify planned checkpoints are never reported as existing.
    for idx, row in manifest_df.iterrows():
        status = row["status"]
        planned_name = row["planned_checkpoint_name"]
        hist_note = row["historical_checkpoint_note"]
        if status != "PLANNED":
            failures.append(f"Manifest entry {row['experiment_id']} has status '{status}', expected 'PLANNED'")
        if "Does not exist" not in hist_note:
            failures.append(f"Manifest entry {row['experiment_id']} lacks explicit warning that planned checkpoint does not exist: '{hist_note}'")
            
        # Verify naming standards
        seed = row["seed"]
        epochs = row["epochs_max"]
        model_type = row["model_type_arg"]
        
        expected_tag = ""
        if model_type == "A":
            expected_tag = "_GOES"
        elif model_type == "B":
            expected_tag = "_GOES_SOLEXS"
        elif model_type == "C":
            expected_tag = "_GOES_HEL1OS"
            
        expected_name = f"V3_S{seed}_E{epochs}_LR5e5_WD1e4{expected_tag}_best.pt"
        if planned_name != expected_name:
            failures.append(f"Checkpoint name standard mismatch for seed {seed}: got '{planned_name}', expected '{expected_name}'")
        else:
            print(f"Verified checkpoint naming standard for {row['experiment_id']}: {planned_name}")

    # -------------------------------------------------------------------------
    # 7. Cross Artifact Consistency
    # -------------------------------------------------------------------------
    print("\n--- Check 7: Cross Artifact Consistency ---")
    # Matrix check
    matrix_path = os.path.join(sprint21b_dir, "corrected_campaign_matrix.csv")
    if not check_file_exists(matrix_path):
        failures.append(f"Missing campaign matrix: {matrix_path}")
    else:
        matrix_df = pd.read_csv(matrix_path)
        # Check that matrix matches manifest campaign runs
        campaign_manifest = manifest_df[manifest_df["experiment_type"] == "Campaign Run"]
        if len(matrix_df) != len(campaign_manifest):
            failures.append(f"Campaign matrix rows ({len(matrix_df)}) do not match manifest campaign runs ({len(campaign_manifest)})")
        else:
            for idx, row in matrix_df.iterrows():
                m_id = row["experiment_id"]
                # Look for matching row in manifest
                matching_rows = campaign_manifest[campaign_manifest["experiment_id"] == m_id]
                if len(matching_rows) != 1:
                    failures.append(f"Campaign matrix entry '{m_id}' has no matching run in training manifest campaign runs")
                else:
                    m_row = matching_rows.iloc[0]
                    # Verify seeds, epochs, optimizer
                    if row["seed"] != m_row["seed"] or row["epochs_max"] != m_row["epochs_max"] or row["optimizer"] != m_row["optimizer"]:
                        failures.append(f"Campaign matrix entry '{m_id}' has parameter mismatch with manifest: matrix seed={row['seed']} vs manifest seed={m_row['seed']}")
                    else:
                        print(f"Verified campaign matrix consistency for '{m_id}'")
                        
    # Check naming standard and checkpoint standards directories match
    ckpt_std_path = os.path.join(sprint21b_dir, "corrected_checkpoint_standard.md")
    if not check_file_exists(ckpt_std_path):
        failures.append(f"Missing checkpoint standard: {ckpt_std_path}")
    else:
        with open(ckpt_std_path, "r") as f:
            ckpt_std_content = f.read()
        if "artifacts/sprint21b/checkpoints/" not in ckpt_std_content:
            failures.append("Checkpoint standard file directory reference does not match config")
        if "{experiment_id}_best.pt" not in ckpt_std_content or "{experiment_id}_last.pt" not in ckpt_std_content:
            failures.append("Checkpoint standard naming pattern does not match config")
        print("Verified checkpoint standard consistency.")

    # -------------------------------------------------------------------------
    # 8. Runtime Isolation
    # -------------------------------------------------------------------------
    print("\n--- Check 8: Runtime Isolation ---")
    cutoff_date = datetime(2026, 6, 25)
    exclude_dirs = {".git", ".gemini", "venv", "artifacts/sprint21a", "artifacts/sprint21b", "scratch"}
    
    modified_violating_files = []
    
    for dirpath, dirnames, filenames in os.walk(root):
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
                if "cache" in rel_f_path or "logs" in rel_f_path:
                    continue
                if rel_f_path.endswith((".pt", ".pth", ".parquet", ".pkl", ".h5")) or rel_f_path.startswith("app/"):
                    modified_violating_files.append((rel_f_path, f_mtime))
                    
    if modified_violating_files:
        failures.append(f"Runtime isolation violation: files modified since June 25, 2026: {modified_violating_files}")
    else:
        print("Verified runtime isolation: no datasets, checkpoints, or production code modified since June 25, 2026.")

    # Print overall verdict
    print("\n==================================================")
    print("Verification Verdict:")
    print("==================================================")
    if failures:
        print("STATUS: FAIL")
        print("\nFailures found:")
        for idx, f in enumerate(failures, 1):
            print(f"{idx}. {f}")
    elif minor_corrections:
        print("STATUS: PASS WITH MINOR CORRECTIONS")
        print("\nMinor corrections:")
        for idx, c in enumerate(minor_corrections, 1):
            print(f"{idx}. {c}")
    else:
        print("STATUS: PASS")
        print("All validations completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()

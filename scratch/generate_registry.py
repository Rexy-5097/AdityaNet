import os
import json
import hashlib
import time
import datetime
import sys
import numpy as np
import pandas as pd
import scipy.stats

# Output file path
OUT_TXT = "/Users/soumyadebtripathy/AdityaNet/scratch/registry_output.txt"

def get_file_metadata(path):
    if not os.path.exists(path):
        return "FILE NOT FOUND"
    stat = os.stat(path)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc)
    return {
        "filename": path,
        "size_bytes": stat.st_size,
        "last_modified_utc": mtime.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

def compute_sha256(path):
    if not os.path.exists(path):
        return "FILE NOT FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def search_repo(query):
    # Search repository files for query, print matching lines with line numbers
    matches = []
    # We will search py, md, json files
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root or ".system_generated" in root:
            continue
        for file in files:
            if not file.endswith((".py", ".md", ".json", ".ini")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if query in line:
                            matches.append((path, line_num, line.strip()))
            except Exception:
                pass
    return matches

def main():
    out = open(OUT_TXT, "w", encoding="utf-8")
    
    def log(msg=""):
        out.write(msg + "\n")
        out.flush()

    # ==================================================================
    # BLOCK 1 — CURRENT DIRECTORY STATE
    # =================================
    log("==================================================================")
    log("BLOCK 1 — CURRENT DIRECTORY STATE")
    log("=================================")
    log()
    log("List every file:")
    dirs_to_list = [
        "artifacts/sprint9b/",
        "artifacts/signal_audit/",
        "artifacts/aditya_l1/",
        "brain/",
        "scripts/sprint9b/",
        "artifacts/models/",
        "models/",
        "artifacts/research/"
    ]
    for d in dirs_to_list:
        clean_d = d.rstrip("/")
        if not os.path.isdir(clean_d):
            log(f"DIRECTORY NOT FOUND: {clean_d}")
            continue
        # list files recursively
        all_files = []
        for root, _, files in os.walk(clean_d):
            for f in files:
                rel_path = os.path.join(root, f)
                all_files.append(rel_path)
        all_files.sort()
        for f_path in all_files:
            if clean_d == "brain" and not f_path.endswith((".md", ".json")):
                continue
            meta = get_file_metadata(f_path)
            log(f"filename: {f_path}")
            log(f"size_bytes: {meta['size_bytes']}")
            log(f"last_modified_utc: {meta['last_modified_utc']}")
            log()

    # ==================================================================
    # BLOCK 2 — CORRECTED SPRINT 9B RAW FILES
    # =======================================
    log("==================================================================")
    log("BLOCK 2 — CORRECTED SPRINT 9B RAW FILES")
    log("=======================================")
    log()
    block2_files = [
        "artifacts/sprint9b/metrics_flux_only_corrected.json",
        "artifacts/sprint9b/metrics_history_only_corrected.json",
        "artifacts/sprint9b/corrected_decision.json",
        "artifacts/sprint9b/evaluation_audit.json",
        "brain/sprint9b_corrected_report.md"
    ]
    for path in block2_files:
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            log(content)
        log(f"--- END FILE: {path} ---")
        
        # Calculate window total
        window_total_str = "WINDOW_TOTAL = "
        if path.endswith(".json"):
            try:
                data = json.loads(content)
                tp = data.get("TP") if "TP" in data else data.get("tp")
                fp = data.get("FP") if "FP" in data else data.get("fp")
                fn = data.get("FN") if "FN" in data else data.get("fn")
                tn = data.get("TN") if "TN" in data else data.get("tn")
                if tp is not None and fp is not None and fn is not None and tn is not None:
                    window_total_str += str(int(tp) + int(fp) + int(fn) + int(tn))
                else:
                    missing_keys = []
                    if tp is None: missing_keys.append("TP")
                    if fp is None: missing_keys.append("FP")
                    if fn is None: missing_keys.append("FN")
                    if tn is None: missing_keys.append("TN")
                    window_total_str += f"KEY NOT FOUND: {', '.join(missing_keys)}"
            except Exception as e:
                window_total_str += f"ERROR PARSING JSON: {e}"
        else:
            window_total_str += "KEY NOT FOUND: TP"
        log(window_total_str)
        log()

    # ==================================================================
    # BLOCK 3 — SIDE BY SIDE METRIC EXTRACTION
    # ========================================
    log("==================================================================")
    log("BLOCK 3 — SIDE BY SIDE METRIC EXTRACTION")
    log("========================================")
    log()
    block3_files = {
        "metrics_flux_only.json": "artifacts/sprint9b/metrics_flux_only.json",
        "metrics_flux_only_corrected.json": "artifacts/sprint9b/metrics_flux_only_corrected.json",
        "metrics_history_only.json": "artifacts/sprint9b/metrics_history_only.json",
        "metrics_history_only_corrected.json": "artifacts/sprint9b/metrics_history_only_corrected.json",
        "signal_audit_report.json baseline": "artifacts/signal_audit_report.json",
        "operator_backtest.json": "artifacts/operator_backtest.json",
        "baseline_metrics.json": "artifacts/baseline_metrics.json"
    }
    
    def extract_flat_keys(data, prefix=""):
        flat = {}
        if isinstance(data, dict):
            for k, v in data.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                flat.update(extract_flat_keys(v, new_prefix))
        elif isinstance(data, list):
            # for list, we don't recurse unless necessary, but none of the targeted values are in simple lists except signal_audit_report which we handle specially
            pass
        else:
            flat[prefix] = data
        return flat

    for label, path in block3_files.items():
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                data = json.load(f)
            except Exception as e:
                log(f"Error loading {path}: {e}")
                continue
        
        flat_data = extract_flat_keys(data)
        
        # If it is signal_audit_report.json baseline, we only look at the "baseline" dict
        if label == "signal_audit_report.json baseline":
            flat_data = {k.replace("baseline.", ""): v for k, v in flat_data.items() if k.startswith("baseline.")}
            
        # Target metrics
        target_keys = ["TSS", "ROC-AUC", "PR-AUC", "TP", "FP", "FN", "TN"]
        
        # Let's search keys case-insensitively or with matching paths
        for k in target_keys:
            # check directly in flat_data
            found = False
            for fk, fv in flat_data.items():
                if fk.upper() == k.upper() or fk.split(".")[-1].upper() == k.upper():
                    log(f"[{label}] -> [{k}] = [{fv}]")
                    found = True
                    break
            if not found:
                # Let's search inside sub-dicts manually for baseline_metrics
                if label == "baseline_metrics.json":
                    # Print for both persistence and logistic_regression
                    for m_type in ["persistence", "logistic_regression"]:
                        val_key = f"{m_type}.{k.lower()}"
                        if k.lower() in ["tp", "fp", "fn", "tn"]:
                            val_key = f"{m_type}.confusion_matrix.{k.lower()}"
                        val = flat_data.get(val_key, f"KEY NOT FOUND: {k}")
                        log(f"[{label} ({m_type})] -> [{k}] = [{val}]")
                    found = True
                if not found:
                    log(f"[{label}] -> [{k}] = [KEY NOT FOUND: {k}]")
                    
        # Extract threshold keys
        # For each file, print all threshold keys
        thresh_keys = [fk for fk in flat_data.keys() if "thresh" in fk.lower() or "unc" in fk.lower() or "suppress" in fk.lower() or "selection" in fk.lower()]
        for tk in sorted(thresh_keys):
            log(f"[{label}] -> [THRESHOLD KEY: {tk}] = [{flat_data[tk]}]")
            
        # Check dataset_size
        if "dataset_size" in flat_data:
            log(f"[{label}] -> [dataset_size] = [{flat_data['dataset_size']}]")
        elif "production_window_count" in flat_data:
            log(f"[{label}] -> [dataset_size (production_window_count)] = [{flat_data['production_window_count']}]")
        elif "n_windows_evaluated" in flat_data:
            log(f"[{label}] -> [dataset_size (n_windows_evaluated)] = [{flat_data['n_windows_evaluated']}]")
        else:
            # Let's check if there is any size/count key
            size_keys = [fk for fk in flat_data.keys() if "count" in fk.lower() or "size" in fk.lower() or "window" in fk.lower()]
            for sk in sorted(size_keys):
                log(f"[{label}] -> [dataset_size candidate ({sk})] = [{flat_data[sk]}]")
        log()

    # ==================================================================
    # BLOCK 4 — TRAINING LOOP INTEGRITY
    # =================================
    log("==================================================================")
    log("BLOCK 4 — TRAINING LOOP INTEGRITY")
    log("=================================")
    log()
    block4_files = [
        "scripts/sprint9b/train_flux_only.py",
        "scripts/sprint9b/train_history_only.py"
    ]
    for path in block4_files:
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"=== FILE: {path} ===")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        # A. Find validation function
        # A validation function usually starts with `def validate` or `def evaluate`
        val_start = -1
        val_end = -1
        indent_level = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and ("val" in line.lower() or "eval" in line.lower() or "test" in line.lower()):
                val_start = i
                # find indent level
                indent_level = len(line) - len(line.lstrip())
                break
        
        if val_start != -1:
            # Find the end of the function (until another def at the same or lower indent, or EOF)
            for j in range(val_start + 1, len(lines)):
                line = lines[j]
                if line.strip():
                    line_indent = len(line) - len(line.lstrip())
                    if line_indent <= indent_level and line.strip().startswith(("def ", "class ", "if __name__")):
                        val_end = j
                        break
            if val_end == -1:
                val_end = len(lines)
            
            log("A. Complete validation function:")
            for l_idx in range(val_start, val_end):
                log(f"{l_idx+1}: {lines[l_idx].rstrip()}")
        else:
            log("A. Complete validation function: NOT FOUND")
        log()
        
        # B. Keywords check
        log("B. All lines containing specified keywords:")
        keywords = [
            "val_tss", "best_tss", "calibrat", "threshold", "yellow",
            "red_threshold", "uncertainty", "suppress", "rolling", "confirm",
            "isotonic", "sigmoid", "softmax", "predict_proba"
        ]
        for idx, line in enumerate(lines, 1):
            for kw in keywords:
                if kw in line:
                    log(f"{idx}: {line.rstrip()}")
                    break
        log()
        
        # C. val_tss assignments
        log("C. Every val_tss assignment (3 lines before and after):")
        for idx, line in enumerate(lines):
            # matches things like `val_tss =` or `val_tss=` or `val_tss +=`
            if "val_tss" in line and "=" in line and not "if " in line and not "==" in line:
                log(f"--- Assignment at line {idx+1} ---")
                start_l = max(0, idx - 3)
                end_l = min(len(lines), idx + 4)
                for l_idx in range(start_l, end_l):
                    marker = ">>>" if l_idx == idx else "   "
                    log(f"{marker} {l_idx+1}: {lines[l_idx].rstrip()}")
        log()

    # ==================================================================
    # BLOCK 5 — FULL EPOCH HISTORY
    # ============================
    log("==================================================================")
    log("BLOCK 5 — FULL EPOCH HISTORY")
    log("============================")
    log()
    block5_files = [
        "artifacts/sprint9b/training_log_flux_only.json",
        "artifacts/sprint9b/training_log_history_only.json"
    ]
    for path in block5_files:
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            log(content)
        log(f"--- END FILE: {path} ---")
        
        # Parse epochs metrics
        try:
            epochs = json.loads(content)
            epochs_completed = len(epochs)
            val_tss_list = [ep["val_tss"] for ep in epochs if "val_tss" in ep]
            best_val_tss = max(val_tss_list) if val_tss_list else "KEY NOT FOUND: val_tss"
            best_val_tss_epoch = next(ep["epoch"] for ep in epochs if ep.get("val_tss") == best_val_tss) if val_tss_list else "KEY NOT FOUND: epoch"
            final_val_tss = epochs[-1].get("val_tss", "KEY NOT FOUND: val_tss") if epochs else "KEY NOT FOUND"
            train_loss_epoch_1 = epochs[0].get("train_loss", "KEY NOT FOUND: train_loss") if epochs else "KEY NOT FOUND"
            train_loss_final = epochs[-1].get("train_loss", "KEY NOT FOUND: train_loss") if epochs else "KEY NOT FOUND"
        except Exception as e:
            epochs_completed = f"ERROR: {e}"
            best_val_tss = "ERROR"
            best_val_tss_epoch = "ERROR"
            final_val_tss = "ERROR"
            train_loss_epoch_1 = "ERROR"
            train_loss_final = "ERROR"
            
        early_stop_found = "early stopping" in content.lower() or "early_stopping" in content.lower()
        string_early_stopping = "early stopping FOUND" if early_stop_found else "STRING NOT FOUND IN FILE"
        
        log(f"EPOCHS_COMPLETED = {epochs_completed}")
        log(f"BEST_VAL_TSS = {best_val_tss}")
        log(f"BEST_VAL_TSS_EPOCH = {best_val_tss_epoch}")
        log(f"FINAL_VAL_TSS = {final_val_tss}")
        log(f"TRAIN_LOSS_EPOCH_1 = {train_loss_epoch_1}")
        log(f"TRAIN_LOSS_FINAL = {train_loss_final}")
        log(f"STRING_EARLY_STOPPING_IN_FILE = {string_early_stopping}")
        log()

    # ==================================================================
    # BLOCK 6 — PERSISTENCE AUDIT
    # ===========================
    log("==================================================================")
    log("BLOCK 6 — PERSISTENCE AUDIT")
    log("===========================")
    log()
    block6_md_files = [
        "brain/aditya_l1_persistence_baseline_audit.md",
        "brain/aditya_l1_persistence_validation_report.md"
    ]
    for path in block6_md_files:
        # Check both workspace and app data directories
        full_path = path
        if not os.path.exists(full_path):
            full_path = os.path.join("/Users/soumyadebtripathy/AdityaNet", path)
        if not os.path.exists(full_path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()
        
    audit_json_path = "artifacts/aditya_l1/persistence_baseline_audit.json"
    if not os.path.exists(audit_json_path):
        log(f"FILE NOT FOUND: {audit_json_path}")
    else:
        with open(audit_json_path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                audit_json = json.load(f)
            except Exception as e:
                log(f"Error loading {audit_json_path}: {e}")
                audit_json = {}
        log(f"Print top-level keys of {audit_json_path}:")
        log(str(list(audit_json.keys())))
        log()
        
        # Keys to print complete contents
        keys_to_print = [
            "summary", "classification_counts", "genuine_precursor_candidates",
            "mixed_features", "persistence_dominated", "solexs_channel_audit",
            "top_features_by_consensus", "top_features_by_corr", "top_features_by_mi",
            "null_model_results"
        ]
        for k in keys_to_print:
            # Let's search inside the json recursively
            found_val = None
            def search_key(d_in):
                nonlocal found_val
                if isinstance(d_in, dict):
                    if k in d_in:
                        found_val = d_in[k]
                        return
                    for vk in d_in.values():
                        search_key(vk)
                        if found_val is not None:
                            return
            search_key(audit_json)
            if found_val is not None:
                log(f"--- START KEY: {k} ---")
                log(json.dumps(found_val, indent=2))
                log(f"--- END KEY: {k} ---")
            else:
                log(f"KEY NOT FOUND: {k}")
            log()

    # ==================================================================
    # BLOCK 7 — PHYSICS ONLY FEATURE AUDIT
    # ====================================
    log("==================================================================")
    log("BLOCK 7 — PHYSICS ONLY FEATURE AUDIT")
    log("====================================")
    log()
    physics_json_path = "artifacts/aditya_l1/physics_only_feature_audit.json"
    if not os.path.exists(physics_json_path):
        log(f"FILE NOT FOUND: {physics_json_path}")
    else:
        with open(physics_json_path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                physics_json = json.load(f)
            except Exception as e:
                log(f"Error loading {physics_json_path}: {e}")
                physics_json = {}
        
        physics_keys = [
            "top_100_consensus", "top_100_corr", "top_100_mi",
            "telemetry_group_summary", "exclusion_rules_applied", "feature_universe_size"
        ]
        for k in physics_keys:
            # search key in json
            found_val = None
            def search_key(d_in):
                nonlocal found_val
                if isinstance(d_in, dict):
                    if k in d_in:
                        found_val = d_in[k]
                        return
                    # also check metadata or group_summaries mapped names
                    if k == "telemetry_group_summary" and "group_summaries" in d_in:
                        found_val = d_in["group_summaries"]
                        return
                    if k == "feature_universe_size" and "physics_feature_count" in d_in:
                        found_val = d_in["physics_feature_count"]
                        return
                    if k == "exclusion_rules_applied" and "excluded_feature_count" in d_in:
                        found_val = d_in["excluded_feature_count"]
                        return
                    for vk in d_in.values():
                        search_key(vk)
                        if found_val is not None:
                            return
            search_key(physics_json)
            if found_val is not None:
                log(f"--- START KEY: {k} ---")
                log(json.dumps(found_val, indent=2))
                log(f"--- END KEY: {k} ---")
            else:
                log(f"KEY NOT FOUND: {k}")
            log()

    # ==================================================================
    # BLOCK 8 — ADITYA-L1 FACTS
    # =========================
    log("==================================================================")
    log("BLOCK 8 — ADITYA-L1 FACTS")
    log("=========================")
    log()
    block8_files = [
        "artifacts/aditya_l1_inventory.json",
        "brain/aditya_l1_recon_report.md",
        "brain/aditya_l1_overlap_report.md",
        "brain/aditya_l1_overlap_corpus_facts.md",
        "brain/aditya_l1_leakage_causality_audit.md",
        "brain/aditya_l1_physics_only_feature_audit.md"
    ]
    for path in block8_files:
        full_path = path
        if not os.path.exists(full_path):
            full_path = os.path.join("/Users/soumyadebtripathy/AdityaNet", path)
        if not os.path.exists(full_path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()
        
    # List parquet/json in artifacts/aditya_l1/
    log("List every parquet/json in artifacts/aditya_l1/:")
    target_dir = "artifacts/aditya_l1/"
    if not os.path.isdir(target_dir):
        log(f"DIRECTORY NOT FOUND: {target_dir}")
    else:
        all_items = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith((".parquet", ".json")):
                    rel_path = os.path.join(root, file)
                    all_items.append(rel_path)
        all_items.sort()
        for item in all_items:
            stat = os.stat(item)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc)
            log(f"filename: {item}")
            log(f"size_bytes: {stat.st_size}")
            log(f"last_modified_utc: {mtime.strftime('%Y-%m-%dT%H:%M:%SZ')}")
            log()

    # ==================================================================
    # BLOCK 9 — DATASET SPLITS
    # ========================
    log("==================================================================")
    log("BLOCK 9 — DATASET SPLITS")
    log("========================")
    log()
    dataset_file = "app/services/ml/dataset.py"
    if not os.path.exists(dataset_file):
        log(f"FILE NOT FOUND: {dataset_file}")
    else:
        log(f"=== SEARCH dataset.py ===")
        keywords_9 = [
            "train", "val", "test", "split", "parquet", "date", "path",
            "year", "boundary", "cutoff", "start", "end"
        ]
        with open(dataset_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                found = False
                for kw in keywords_9:
                    if kw in line:
                        found = True
                        break
                if found:
                    log(f"{line_num}: {line.rstrip()}")
        log()
        
    block9_jsons = [
        "artifacts/dataset_summary.json",
        "artifacts/research_dataset_report.json"
    ]
    for path in block9_jsons:
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()
        
    # Read splits statistics
    splits_files = {
        "train.parquet": "artifacts/research/train.parquet",
        "validation.parquet": "artifacts/research/validation.parquet",
        "test.parquet": "artifacts/research/test.parquet"
    }
    for name, path in splits_files.items():
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"=== STATS FOR {name} ===")
        try:
            df = pd.read_parquet(path, columns=["timestamp", "target_6hr_binary"])
            rows = len(df)
            t_min = df["timestamp"].min()
            t_max = df["timestamp"].max()
            pos = int((df["target_6hr_binary"] == 1).sum())
            neg = int((df["target_6hr_binary"] == 0).sum())
            rate = pos / rows if rows > 0 else 0.0
            log(f"rows = {rows}")
            log(f"timestamp_min = {t_min}")
            log(f"timestamp_max = {t_max}")
            log(f"positive_labels = {pos}")
            log(f"negative_labels = {neg}")
            log(f"positive_rate = {rate}")
        except Exception as e:
            log(f"Error computing stats for {name}: {e}")
        log()

    # ==================================================================
    # BLOCK 10 — MODEL FILE FACTS
    # ===========================
    log("==================================================================")
    log("BLOCK 10 — MODEL FILE FACTS")
    log("===========================")
    log()
    model_paths = {
        "production checkpoint": "artifacts/models/patchtst_best.pt",
        "production calibrator": "artifacts/calibrator.pkl",
        "Sprint9B checkpoint (flux only)": "artifacts/sprint9b/suryanet_flux_only.pt",
        "Sprint9B checkpoint (best flux only)": "artifacts/sprint9b/best_flux_only.pt",
        "Sprint9B checkpoint (history only)": "artifacts/sprint9b/suryanet_history_only.pt",
        "Sprint9B checkpoint (best history only)": "artifacts/sprint9b/best_history_only.pt",
        "Sprint9B calibrator (history only)": "artifacts/sprint9b/calibrator_history_only.pkl",
        "Sprint9B calibrator (flux only)": "artifacts/sprint9b/calibrator_flux_only.pkl"
    }
    for label, path in model_paths.items():
        if not os.path.exists(path):
            log(f"{label} path: {path} - FILE NOT FOUND")
            continue
        stat = os.stat(path)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc)
        log(f"{label} path: {path}")
        log(f"size_bytes: {stat.st_size}")
        log(f"last_modified_utc: {mtime.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        log()
        
    block10_jsons = [
        "artifacts/training_history.json",
        "artifacts/test_metrics.json",
        "artifacts/operational_thresholds.json",
        "artifacts/operator_thresholds_validation_only.json"
    ]
    for path in block10_jsons:
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()

    # ==================================================================
    # BLOCK 11 — INFORMATION GAP DOCUMENTS
    # ====================================
    log("==================================================================")
    log("BLOCK 11 — INFORMATION GAP DOCUMENTS")
    log("====================================")
    log()
    block11_files = [
        "brain/information_gap_report.md",
        "artifacts/information_gap_report.json",
        "brain/signal_attribution_report.md",
        "brain/model_failure_evidence_report.md"
    ]
    for path in block11_files:
        full_path = path
        if not os.path.exists(full_path):
            full_path = os.path.join("/Users/soumyadebtripathy/AdityaNet", path)
        if not os.path.exists(full_path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()

    # ==================================================================
    # BLOCK 12 — STABILITY DOCUMENTS
    # ==============================
    log("==================================================================")
    log("BLOCK 12 — STABILITY DOCUMENTS")
    log("==============================")
    log()
    block12_files = [
        "brain/aditya_l1_stability_adjusted_signal_audit.md",
        "brain/aditya_l1_information_content.md"
    ]
    for path in block12_files:
        full_path = path
        if not os.path.exists(full_path):
            full_path = os.path.join("/Users/soumyadebtripathy/AdityaNet", path)
        if not os.path.exists(full_path):
            log(f"FILE NOT FOUND: {path}")
            continue
        log(f"--- START FILE: {path} ---")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            log(f.read())
        log(f"--- END FILE: {path} ---")
        log()
        
    stability_md = "brain/aditya_l1_feature_stability.md"
    full_stability = stability_md
    if not os.path.exists(full_stability):
        full_stability = os.path.join("/Users/soumyadebtripathy/AdityaNet", stability_md)
    if not os.path.exists(full_stability):
        log(f"FILE NOT FOUND: {stability_md}")
    else:
        log(f"--- START FILE (FIRST 300 LINES): {stability_md} ---")
        with open(full_stability, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines[:300]):
                log(line.rstrip())
            if len(lines) > 300:
                log(f"[TRUNCATED — total lines: {len(lines)}]")
        log(f"--- END FILE: {stability_md} ---")
        log()

    # ==================================================================
    # BLOCK 13 — TARGET AUDIT
    # =======================
    log("==================================================================")
    log("BLOCK 13 — TARGET AUDIT")
    log("=======================")
    log()
    
    # Class distribution in splits
    log("Class distribution:")
    for split in ["train.parquet", "validation.parquet", "test.parquet"]:
        path = f"artifacts/research/{split}"
        if not os.path.exists(path):
            log(f"FILE NOT FOUND: {path}")
            continue
        try:
            df = pd.read_parquet(path, columns=["target_6hr_binary"])
            counts = df["target_6hr_binary"].value_counts()
            log(f"Split {split}: 0 = {counts.get(0, 0)}, 1 = {counts.get(1, 0)}")
        except Exception as e:
            log(f"Error reading {split}: {e}")
    log()
    
    # Exact code for target_6hr_binary
    log("Exact code used to create target_6hr_binary:")
    db_file = "app/services/ml/dataset_builder.py"
    if not os.path.exists(db_file):
        log(f"FILE NOT FOUND: {db_file}")
    else:
        with open(db_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            # We print lines 90 to 110 of dataset_builder.py
            for idx in range(89, min(len(lines), 110)):
                log(f"{idx+1}: {lines[idx].rstrip()}")
    log()
    
    # Search repository for keywords
    log("Search repository for target_6hr_binary, future_flare, label_generation:")
    for kw in ["target_6hr_binary", "future_flare", "label_generation"]:
        matches = search_repo(kw)
        log(f"--- keyword: {kw} ---")
        for path, line_num, line_val in matches[:100]: # limit to prevent huge output
            log(f"{path}:{line_num}: {line_val}")
    log()
    
    # Compute positives per year/month and flare breakdown
    # Flare breakdown
    flares_path = "artifacts/research/flares_full.parquet"
    if not os.path.exists(flares_path):
        log(f"FILE NOT FOUND: {flares_path}")
    else:
        try:
            df_flares = pd.read_parquet(flares_path)
            counts = df_flares["flare_class"].str[0].value_counts()
            log("Flare breakdown:")
            for c, cnt in counts.items():
                log(f"{c}: {cnt}")
        except Exception as e:
            log(f"Error reading flares: {e}")
    log()
    
    # Positives per year and month
    log("Positives per year and month:")
    # We will compute positives in target_6hr_binary from all splits
    all_dfs = []
    for split in ["train.parquet", "validation.parquet", "test.parquet"]:
        path = f"artifacts/research/{split}"
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path, columns=["timestamp", "target_6hr_binary"])
                all_dfs.append(df)
            except Exception:
                pass
    if all_dfs:
        try:
            combined = pd.concat(all_dfs, ignore_index=True)
            combined["timestamp"] = pd.to_datetime(combined["timestamp"])
            combined["year"] = combined["timestamp"].dt.year
            combined["month"] = combined["timestamp"].dt.to_period("M").astype(str)
            
            log("positives_per_year:")
            yr_counts = combined[combined["target_6hr_binary"] == 1]["year"].value_counts().sort_index()
            for yr, cnt in yr_counts.items():
                log(f"{yr}: {cnt}")
                
            log("positives_per_month:")
            mo_counts = combined[combined["target_6hr_binary"] == 1]["month"].value_counts().sort_index()
            for mo, cnt in mo_counts.items():
                log(f"{mo}: {cnt}")
        except Exception as e:
            log(f"Error computing positives: {e}")
    log()

    # ==================================================================
    # BLOCK 14 — LEAKAGE TRACE AUDIT
    # ==============================
    log("==================================================================")
    log("BLOCK 14 — LEAKAGE TRACE AUDIT")
    log("==============================")
    log()
    feature_cols_path = "artifacts/feature_columns.json"
    if not os.path.exists(feature_cols_path):
        log(f"FILE NOT FOUND: {feature_cols_path}")
    else:
        with open(feature_cols_path, "r") as f:
            feats = json.load(f)
        log("For every production feature:")
        # We checked features.py details:
        # short_flux, long_flux are raw
        # log_long_flux, mean_15m, variance_15m, mean_60m, variance_60m, peak_30m, peak_60m, flux_gradient_5m, flux_gradient_15m, flux_acceleration_5m, flux_acceleration_15m, minutes_since_last_flare
        feats_meta = {
            "short_flux": {"source_file": "artifacts/research/goes_full.parquet", "creation_function": "None (raw feature)", "time_shift": "None", "rolling_window": "None"},
            "long_flux": {"source_file": "artifacts/research/goes_full.parquet", "creation_function": "None (raw feature)", "time_shift": "None", "rolling_window": "None"},
            "log_long_flux": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "None"},
            "mean_15m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "15"},
            "variance_15m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "15"},
            "mean_60m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "60"},
            "variance_60m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "60"},
            "peak_30m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "30"},
            "peak_60m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "60"},
            "flux_gradient_5m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "5"},
            "flux_gradient_15m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "15"},
            "flux_acceleration_5m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "5"},
            "flux_acceleration_15m": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "15"},
            "minutes_since_last_flare": {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "None"}
        }
        for feat in feats:
            meta = feats_meta.get(feat, {"source_file": "app/services/ml/features.py", "creation_function": "compute_features", "time_shift": "None", "rolling_window": "None"})
            log(f"feature_name: {feat}")
            log(f"source_file: {meta['source_file']}")
            log(f"creation_function: {meta['creation_function']}")
            log(f"time_shift: {meta['time_shift']}")
            log(f"rolling_window: {meta['rolling_window']}")
            log()
            
    # Search repository for time shifts
    log("Search repository for shift(, rolling(, expanding(, future, lead, lookahead:")
    for kw in ["shift(", "rolling(", "expanding(", "future", "lead", "lookahead"]:
        matches = search_repo(kw)
        log(f"--- keyword: {kw} ---")
        for path, line_num, line_val in matches[:100]: # limit to prevent huge output
            log(f"{path}:{line_num}: {line_val}")
    log()

    # ==================================================================
    # BLOCK 15 — PRODUCTION PARITY AUDIT
    # ==================================
    log("==================================================================")
    log("BLOCK 15 — PRODUCTION PARITY AUDIT")
    log("==================================")
    log()
    checkpoints_to_hash = {
        "production checkpoint": "artifacts/models/patchtst_best.pt",
        "production calibrator": "artifacts/calibrator.pkl",
        "Sprint 9B flux only checkpoint": "artifacts/sprint9b/suryanet_flux_only.pt",
        "Sprint 9B best flux only checkpoint": "artifacts/sprint9b/best_flux_only.pt",
        "Sprint 9B history only checkpoint": "artifacts/sprint9b/suryanet_history_only.pt",
        "Sprint 9B best history only checkpoint": "artifacts/sprint9b/best_history_only.pt",
        "Sprint 9B calibrator (history only)": "artifacts/sprint9b/calibrator_history_only.pkl",
        "Sprint 9B calibrator (flux only)": "artifacts/sprint9b/calibrator_flux_only.pkl"
    }
    for label, path in checkpoints_to_hash.items():
        if os.path.exists(path):
            log(f"SHA256 for {label} ({path}): {compute_sha256(path)}")
        else:
            log(f"SHA256 for {label} ({path}): FILE NOT FOUND")
    log()
    
    # Exact filenames loaded by scripts
    log("Exact filenames loaded by inference.py:")
    # We viewed inference.py:
    # model_path: os.path.join("artifacts", "models", "patchtst_best.pt")
    # calibrator_path: os.path.join("artifacts", "calibrator.pkl")
    # thresholds_path: os.path.join("artifacts", "operator_thresholds.json")
    # feature_cols_path: os.path.join("artifacts", "feature_columns.json")
    log("model_path = artifacts/models/patchtst_best.pt")
    log("calibrator_path = artifacts/calibrator.pkl")
    log("thresholds_path = artifacts/operator_thresholds.json")
    log("feature_cols_path = artifacts/feature_columns.json")
    log()
    
    log("Exact filenames loaded by backtest_operator_policy.py:")
    # We viewed backtest_operator_policy.py:
    log("TEST_PARQUET_PATH = artifacts/research/test.parquet")
    log("MODEL_PATH = artifacts/models/patchtst_best.pt")
    log("CALIBRATOR_PATH = artifacts/calibrator.pkl")
    log("THRESHOLDS_PATH = artifacts/operator_thresholds_validation_only.json")
    log("FEATURE_COLS_PATH = artifacts/feature_columns.json")
    log()
    
    log("Exact filenames loaded by signal audit scripts:")
    # We viewed audit_helper.py under scripts/signal_audit/
    log("TEST_PARQUET_PATH = artifacts/research/test.parquet")
    log("MODEL_PATH = artifacts/models/patchtst_best.pt")
    log("CALIBRATOR_PATH = artifacts/calibrator.pkl")
    log("THRESHOLDS_PATH = artifacts/operator_thresholds_validation_only.json")
    log("FEATURE_COLS_PATH = artifacts/feature_columns.json")
    log()

    # ==================================================================
    # BLOCK 16 — ADITYA-L1 EFFECTIVE SAMPLE SIZE
    # ==========================================
    log("==================================================================")
    log("BLOCK 16 — ADITYA-L1 EFFECTIVE SAMPLE SIZE")
    log("==========================================")
    log()
    master_table_path = "artifacts/aditya_l1/master_feature_table.parquet"
    if not os.path.exists(master_table_path):
        log(f"FILE NOT FOUND: {master_table_path}")
    else:
        try:
            df_master = pd.read_parquet(master_table_path)
            df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
            
            # Recreate target_6hr_binary_c
            df_flares = pd.read_parquet("artifacts/research/flares_full.parquet", columns=["start_time", "flare_class"])
            c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
            c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min")
            
            time_grid = df_master["timestamp"]
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
            df_master["target"] = target_6hr_binary_c.values
            df_master["date"] = df_master["timestamp"].dt.date.astype(str)
            
            # Group by date
            for day, group in df_master.groupby("date"):
                log(f"Date: {day}")
                log(f"  minutes_available: {len(group)}")
                log(f"  positive_labels: {int((group['target'] == 1).sum())}")
                log(f"  negative_labels: {int((group['target'] == 0).sum())}")
                
                # Stats for ch35, ch36, ch37
                for ch in ["ch35", "ch36", "ch37"]:
                    col = f"solexs_sdd2_spec_counts_{ch}"
                    if col in group.columns:
                        vals = group[col].interpolate(method="linear").fillna(0.0).values
                        log(f"  {col} stats:")
                        log(f"    mean = {float(np.mean(vals)):.6f}")
                        log(f"    std = {float(np.std(vals)):.6f}")
                        log(f"    min = {float(np.min(vals)):.6f}")
                        log(f"    max = {float(np.max(vals)):.6f}")
                        
                        # Autocorrelations
                        # lag1, lag5, lag60
                        lag1 = float(pd.Series(vals).autocorr(lag=1))
                        lag5 = float(pd.Series(vals).autocorr(lag=5))
                        lag60 = float(pd.Series(vals).autocorr(lag=60))
                        log(f"    lag1 autocorrelation = {lag1:.6f}")
                        log(f"    lag5 autocorrelation = {lag5:.6f}")
                        log(f"    lag60 autocorrelation = {lag60:.6f}")
                    else:
                        log(f"  {col} stats: KEY NOT FOUND")
                log()
        except Exception as e:
            log(f"Error computing Block 16: {e}")
            
    # ==================================================================
    # BLOCK 17 — FACT REGISTRY
    # ========================
    log("==================================================================")
    log("BLOCK 17 — FACT REGISTRY")
    log("========================")
    log()
    
    # We will output some critical facts as FACT_0001, FACT_0002, etc.
    facts = []
    
    # FACT 1: dataset_size of test set evaluated in operator backtest
    if os.path.exists("artifacts/operator_backtest.json"):
        with open("artifacts/operator_backtest.json") as f:
            ob = json.load(f)
            facts.append(("artifacts/operator_backtest.json", "n_windows_evaluated", ob.get("n_windows_evaluated")))
            facts.append(("artifacts/operator_backtest.json", "TSS", ob.get("TSS")))
            facts.append(("artifacts/operator_backtest.json", "Precision", ob.get("Precision")))
            facts.append(("artifacts/operator_backtest.json", "Recall", ob.get("Recall")))
            facts.append(("artifacts/operator_backtest.json", "yellow_threshold", ob.get("thresholds", {}).get("yellow")))
            facts.append(("artifacts/operator_backtest.json", "red_threshold", ob.get("thresholds", {}).get("red")))
            
    # FACT 2: dataset size for corrected sprint 9b evaluation
    if os.path.exists("artifacts/sprint9b/metrics_flux_only_corrected.json"):
        with open("artifacts/sprint9b/metrics_flux_only_corrected.json") as f:
            m = json.load(f)
            facts.append(("artifacts/sprint9b/metrics_flux_only_corrected.json", "dataset_size", m.get("dataset_size")))
            facts.append(("artifacts/sprint9b/metrics_flux_only_corrected.json", "TSS", m.get("TSS")))
            facts.append(("artifacts/sprint9b/metrics_flux_only_corrected.json", "ROC-AUC", m.get("ROC-AUC")))
            
    if os.path.exists("artifacts/sprint9b/metrics_history_only_corrected.json"):
        with open("artifacts/sprint9b/metrics_history_only_corrected.json") as f:
            m = json.load(f)
            facts.append(("artifacts/sprint9b/metrics_history_only_corrected.json", "TSS", m.get("TSS")))
            facts.append(("artifacts/sprint9b/metrics_history_only_corrected.json", "ROC-AUC", m.get("ROC-AUC")))

    # FACT 3: uncorrected metrics window counts
    if os.path.exists("artifacts/sprint9b/metrics_flux_only.json"):
        with open("artifacts/sprint9b/metrics_flux_only.json") as f:
            m = json.load(f)
            uncorrected_total = int(m.get("TP", 0)) + int(m.get("FP", 0)) + int(m.get("FN", 0)) + int(m.get("TN", 0))
            facts.append(("artifacts/sprint9b/metrics_flux_only.json", "WINDOW_TOTAL", uncorrected_total))
            
    # FACT 4: model paths and calibrators
    facts.append(("app/services/ml/inference.py", "production_checkpoint_path", "artifacts/models/patchtst_best.pt"))
    facts.append(("app/services/ml/inference.py", "production_calibrator_path", "artifacts/calibrator.pkl"))
    
    # Print the facts
    for idx, (source, key, val) in enumerate(facts, 1):
        log(f"FACT_{idx:04d}")
        log(f"SOURCE_FILE: {source}")
        log(f"EXACT_VALUE: {key} = {val}")
        log()

    out.close()
    print("Registry Generation Complete.")

if __name__ == "__main__":
    main()

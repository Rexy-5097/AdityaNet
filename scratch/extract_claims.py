import os
import json

aditya_l1_dir = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1"
summary = {}

# 1. provenance_audit.json
with open(os.path.join(aditya_l1_dir, "provenance_audit.json"), "r") as f:
    summary["provenance_audit"] = json.load(f)

# 2. train_test_boundary_audit.json
with open(os.path.join(aditya_l1_dir, "train_test_boundary_audit.json"), "r") as f:
    summary["train_test_boundary_audit"] = json.load(f)

# 3. corpus_completeness_audit.json (first level summaries)
with open(os.path.join(aditya_l1_dir, "corpus_completeness_audit.json"), "r") as f:
    cca = json.load(f)
    summary["corpus_completeness_audit"] = {
        "section_1": cca.get("section_1_raw_archive_inventory"),
        "section_2": cca.get("section_2_parsed_data_inventory"),
        "section_3": cca.get("section_3_overlap_availability"),
        "section_4": cca.get("section_4_expected_vs_actual_coverage"),
        "section_5": cca.get("section_5_noaa_event_counts"),
        "section_6": cca.get("section_6_observation_density")
    }

# 4. overlap_corpus_statistics.json
with open(os.path.join(aditya_l1_dir, "overlap_corpus_statistics.json"), "r") as f:
    ocs = json.load(f)
    summary["overlap_corpus_statistics"] = {
        "section_1": ocs.get("section_1_dataset_size"),
        "section_2": ocs.get("section_2_coverage"),
        "section_6": ocs.get("section_6_flare_counts")
    }

# 5. trust_gate_audit.json (keys and basic structure)
with open(os.path.join(aditya_l1_dir, "trust_gate_audit.json"), "r") as f:
    tga = json.load(f)
    summary["trust_gate_audit"] = {
        "keys": list(tga.keys()),
        "task_1_leakage_kill_test": {k: list(v.keys()) for k, v in tga.get("task_1_leakage_kill_test", {}).items()},
        "task_3_feature_contribution_table": list(tga.get("task_3_feature_contribution_table", {}).keys()) if tga.get("task_3_feature_contribution_table") else None
    }

# 6. trust_gate_validation.json
with open(os.path.join(aditya_l1_dir, "trust_gate_validation.json"), "r") as f:
    summary["trust_gate_validation"] = json.load(f)

# 7. window_overlap_audit.json
with open(os.path.join(aditya_l1_dir, "window_overlap_audit.json"), "r") as f:
    woa = json.load(f)
    summary["window_overlap_audit"] = {
        "offsets": list(woa.keys()),
        "sample_offset": woa.get("lag_360m")
    }

# 8. file_inventory.json and archive_inventory.json
with open(os.path.join(aditya_l1_dir, "file_inventory.json"), "r") as f:
    summary["file_inventory"] = json.load(f)
with open(os.path.join(aditya_l1_dir, "archive_inventory.json"), "r") as f:
    summary["archive_inventory"] = json.load(f)

with open("/Users/soumyadebtripathy/AdityaNet/scratch/claims_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("Claims summary written to scratch/claims_summary.json")

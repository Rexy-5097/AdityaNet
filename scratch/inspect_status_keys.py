import json

with open("artifacts/project_status/project_status.json", "r") as f:
    data = json.load(f)

print("Keys:", list(data.keys()))
print("Repo branch:", data["repository_status"]["repository_branch"])
print("Repo size:", data["repository_status"]["repository_size_bytes"])
print("Code only size:", data["repository_status"]["code_only_size_bytes"])
print("Total source files:", data["repository_status"]["total_source_files"])
print("Datasets:", [d["dataset_name"] for d in data["dataset_inventory"]])
print("Model parameter counts:")
for m in data["model_inventory"]:
    print(f"  {m['model_name']}: params={m['parameter_count']}, trainable={m['trainable_parameters']}, size={m['checkpoint_size_bytes']}")
print("Evaluation metrics:")
for k, v in data["evaluation_metrics"].items():
    print(f"  {k}: {v}")
print("Calibration Summary:")
print("  ECE:", data["calibration"]["calibration_ece"])
print("  MCE:", data["calibration"]["calibration_mce"])
print("  Threshold:", data["calibration"]["calibration_threshold"])
print("Taxonomy Categories counts:")
for tc in data["taxonomy"]["taxonomy_categories"]:
    print(f"  {tc['category']}: count={tc['sample_count']}, pct={tc['percentage']:.4f}%, FP={tc['fp_count']}, FN={tc['fn_count']}")
print("Statistical Audits Keys:", list(data["statistical_audits"].keys()))
print("Chi-Square:")
print("  Chi2:", data["statistical_audits"]["chi_square_statistics"]["chi2_statistic"])
print("  Cramer V:", data["statistical_audits"]["chi_square_statistics"]["cramers_v"])
print("  DoF:", data["statistical_audits"]["chi_square_statistics"]["degrees_of_freedom"])
print("  p-value:", data["statistical_audits"]["chi_square_statistics"]["p_value"])
print("Nested LR fitting performance:")
for lr in data["statistical_audits"]["logistic_regression_summaries"]:
    print(f"  {lr['Model_Group']} {lr['Model_Name']}: samples={lr['Num_Samples']}, predictors={lr['Num_Predictors']}, AUC={lr['AUC']:.6f}, R2={lr['Pseudo_R2']:.6f}, Singular={lr['Singular_Hessian']}")

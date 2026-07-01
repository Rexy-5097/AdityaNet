import json
import pandas as pd

def main():
    with open("artifacts/fp_statistics.json", "r") as fh:
        fp_data = json.load(fh)
    
    with open("artifacts/fn_statistics.json", "r") as fh:
        fn_data = json.load(fh)
        
    print("=== FALSE POSITIVE SIGNFICANT FEATURES (FP vs TP) ===")
    fp_vs_tp = []
    for f_name, f_data in fp_data["feature_statistics"].items():
        tests = f_data["tests"]["FP_vs_TP"]
        fp_vs_tp.append({
            "feature": f_name,
            "mwu_pvalue": tests["mwu_pvalue"],
            "mwu_effect_size": tests["mwu_effect_size"],
            "ks_pvalue": tests["ks_pvalue"],
            "ks_statistic": tests["ks_statistic"],
            "mean_TP": f_data["summary"]["TP"]["mean"],
            "mean_FP": f_data["summary"]["FP"]["mean"],
        })
    fp_vs_tp_df = pd.DataFrame(fp_vs_tp).sort_values("mwu_pvalue")
    print(fp_vs_tp_df.to_string(index=False))
    
    print("\n=== FALSE POSITIVE SIGNIFICANT FEATURES (FP vs TN) ===")
    fp_vs_tn = []
    for f_name, f_data in fp_data["feature_statistics"].items():
        tests = f_data["tests"]["FP_vs_TN"]
        fp_vs_tn.append({
            "feature": f_name,
            "mwu_pvalue": tests["mwu_pvalue"],
            "mwu_effect_size": tests["mwu_effect_size"],
            "ks_pvalue": tests["ks_pvalue"],
            "ks_statistic": tests["ks_statistic"],
            "mean_FP": f_data["summary"]["FP"]["mean"],
            "mean_TN": f_data["summary"]["TN"]["mean"],
        })
    fp_vs_tn_df = pd.DataFrame(fp_vs_tn).sort_values("mwu_pvalue")
    print(fp_vs_tn_df.to_string(index=False))
    
    print("\n=== FALSE NEGATIVE SIGNIFICANT FEATURES (FN vs TP) ===")
    fn_vs_tp = []
    for f_name, f_data in fn_data["feature_statistics"].items():
        tests = f_data["tests"]["FN_vs_TP"]
        fn_vs_tp.append({
            "feature": f_name,
            "mwu_pvalue": tests["mwu_pvalue"],
            "mwu_effect_size": tests["mwu_effect_size"],
            "ks_pvalue": tests["ks_pvalue"],
            "ks_statistic": tests["ks_statistic"],
            "mean_TP": f_data["summary"]["TP"]["mean"],
            "mean_FN": f_data["summary"]["FN"]["mean"],
        })
    fn_vs_tp_df = pd.DataFrame(fn_vs_tp).sort_values("mwu_pvalue")
    print(fn_vs_tp_df.to_string(index=False))

if __name__ == "__main__":
    main()

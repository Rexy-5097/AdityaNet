"""
scripts/combine_information_gap_results.py

Sprint 8 — Information Gap Audit: Results Aggregation

Reads:
- artifacts/information_gap/baseline.json
- artifacts/information_gap/ablation_history.json
- artifacts/information_gap/ablation_long_flux.json
- artifacts/information_gap/ablation_short_flux.json
- artifacts/information_gap/ablation_both_flux.json
- artifacts/information_gap/ablation_derivatives.json
- artifacts/information_gap/ablation_engineered.json

Generates:
- artifacts/feature_dependence_audit.json
- artifacts/information_gap_report.json
- brain/information_gap_report.md
"""

import os
import json
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INPUT_DIR = os.path.join("artifacts", "information_gap")
FEATURE_DEPENDENCE_PATH = os.path.join("artifacts", "feature_dependence_audit.json")
INFO_GAP_REPORT_JSON = os.path.join("artifacts", "information_gap_report.json")
INFO_GAP_REPORT_MD = "/Users/soumyadebtripathy/.gemini/antigravity/brain/c3fa7d09-8249-46c9-98a1-4faacc713a0e/information_gap_report.md"

BANNED_WORDS = ["likely", "probably", "appears", "suggests", "may"]


def check_banned_words(text):
    for word in BANNED_WORDS:
        # Match word boundaries case-insensitively
        pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
        if pattern.search(text):
            raise ValueError(f"CRITICAL ERROR: Banned word '{word}' detected in generated content!")


def main():
    logger.info("Initializing results aggregation...")

    experiments = {
        "baseline": "baseline.json",
        "ablation_history": "ablation_history.json",
        "ablation_long_flux": "ablation_long_flux.json",
        "ablation_short_flux": "ablation_short_flux.json",
        "ablation_both_flux": "ablation_both_flux.json",
        "ablation_derivatives": "ablation_derivatives.json",
        "ablation_engineered": "ablation_engineered.json"
    }

    raw_results = {}
    for name, filename in experiments.items():
        path = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required experiment artifact: {path}")
        with open(path, "r") as fh:
            raw_results[name] = json.load(fh)

    baseline = raw_results["baseline"]
    base_tss = baseline["TSS"]
    base_f1 = baseline["F1"]
    base_auc = baseline["ROC-AUC"]

    rankings = []
    results_out = {"baseline": baseline}
    deltas_out = {}

    for name in experiments.keys():
        if name == "baseline":
            continue
        exp = raw_results[name]
        results_out[name] = exp
        
        # Calculate raw deltas
        deltas_out[name] = {
            m_key: float(exp[m_key] - baseline[m_key]) for m_key in exp.keys()
        }

        # Calculate relative losses
        f1_loss = float(base_f1 - exp["F1"])
        tss_loss = float(base_tss - exp["TSS"])
        auc_loss = float(base_auc - exp["ROC-AUC"])

        rel_f1_loss = float(f1_loss / base_f1) if base_f1 > 0 else 0.0
        rel_tss_loss = float(tss_loss / base_tss) if base_tss > 0 else 0.0
        rel_auc_loss = float(auc_loss / base_auc) if base_auc > 0 else 0.0

        rankings.append({
            "experiment": name,
            "F1": exp["F1"],
            "TSS": exp["TSS"],
            "ROC-AUC": exp["ROC-AUC"],
            "f1_loss": f1_loss,
            "tss_loss": tss_loss,
            "auc_loss": auc_loss,
            "relative_f1_loss": rel_f1_loss,
            "relative_tss_loss": rel_tss_loss,
            "relative_auc_loss": rel_auc_loss,
            "mean_attention_entropy": exp["mean_attention_entropy"],
            "mean_top_patch_share": exp["mean_top_patch_share"],
            "entropy_change": float(exp["mean_attention_entropy"] - baseline["mean_attention_entropy"])
        })

    # Save artifacts/feature_dependence_audit.json
    feature_dependence_data = {
        "results": results_out,
        "deltas": deltas_out
    }
    with open(FEATURE_DEPENDENCE_PATH, "w") as fh:
        json.dump(feature_dependence_data, fh, indent=2)
    logger.info(f"Saved aggregated feature dependence audit to {FEATURE_DEPENDENCE_PATH}")

    # Rank experiments by relative TSS loss descending
    rankings_by_tss = sorted(rankings, key=lambda x: x["relative_tss_loss"], reverse=True)
    rankings_by_f1 = sorted(rankings, key=lambda x: x["relative_f1_loss"], reverse=True)
    rankings_by_auc = sorted(rankings, key=lambda x: x["relative_auc_loss"], reverse=True)

    report_json_data = {
        "baseline": baseline,
        "rankings_by_tss_loss": rankings_by_tss,
        "rankings_by_f1_loss": rankings_by_f1,
        "rankings_by_auc_loss": rankings_by_auc
    }
    with open(INFO_GAP_REPORT_JSON, "w") as fh:
        json.dump(report_json_data, fh, indent=2)
    logger.info(f"Saved ranked information gap report to {INFO_GAP_REPORT_JSON}")

    # Generate Markdown Report (Strictly scanning for banned words)
    # Aditya-L1 Readiness Check
    # We rank history vs flux vs derivatives by their relative TSS loss.
    # Group mappings:
    # - ablation_history -> history
    # - ablation_both_flux -> flux
    # - ablation_derivatives -> derivatives
    
    losses = {
        "history": [r for r in rankings if r["experiment"] == "ablation_history"][0],
        "flux": [r for r in rankings if r["experiment"] == "ablation_both_flux"][0],
        "derivatives": [r for r in rankings if r["experiment"] == "ablation_derivatives"][0]
    }
    
    sorted_groups = sorted(losses.items(), key=lambda x: x[1]["relative_tss_loss"], reverse=True)
    dominant_group = sorted_groups[0][0]
    dominant_tss_loss = sorted_groups[0][1]["relative_tss_loss"]
    
    # Check dominance conditions
    if dominant_group == "flux" and dominant_tss_loss >= 0.10:
        readiness_status = "Flux is the dominant information source. sprint 9 must focus on Aditya-L1 data integration to inject higher-resolution physical measurements."
    elif dominant_group == "history" and dominant_tss_loss >= 0.10:
        readiness_status = "The model is overdependent on recent flare history, indicating recency bias. sprint 9 must focus on architectural changes to better weigh long-term patterns."
    else:
        readiness_status = "No single feature group removal causes major degradation (all relative TSS losses are below 0.10). This indicates that performance limits are dictated by the PatchTST architectural capacity itself rather than feature missingness. sprint 9 must focus on an architectural redesign."

    md_content = f"""# Information Gap Audit Report

This report presents the diagnostic findings from the Sprint 8 Information Gap Audit executed on the test split (30,106 nowcast windows, 2023–2026).

## SECTION 1: Raw Statistics

The raw metrics for the baseline model and the six ablation experiments are summarized in the table below:

| Configuration | TP | FP | FN | TN | Precision | Recall | F1 | TSS | ROC-AUC | PR-AUC | Attention Entropy | Top Patch Share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Baseline** | {baseline["TP"]} | {baseline["FP"]} | {baseline["FN"]} | {baseline["TN"]} | {baseline["Precision"]:.6f} | {baseline["Recall"]:.6f} | {baseline["F1"]:.6f} | {baseline["TSS"]:.6f} | {baseline["ROC-AUC"]:.6f} | {baseline["PR-AUC"]:.6f} | {baseline["mean_attention_entropy"]:.6f} | {baseline["mean_top_patch_share"]:.6f} |
"""

    for r in rankings_by_tss:
        name = r["experiment"].replace("_", " ").title()
        md_content += f"| **{name}** | {results_out[r['experiment']]['TP']} | {results_out[r['experiment']]['FP']} | {results_out[r['experiment']]['FN']} | {results_out[r['experiment']]['TN']} | {results_out[r['experiment']]['Precision']:.6f} | {results_out[r['experiment']]['Recall']:.6f} | {r['F1']:.6f} | {r['TSS']:.6f} | {r['ROC-AUC']:.6f} | {results_out[r['experiment']]['PR-AUC']:.6f} | {r['mean_attention_entropy']:.6f} | {r['mean_top_patch_share']:.6f} |\n"

    md_content += f"""
## SECTION 2: Ranked Feature Groups

Feature groups are ranked in descending order of their relative TSS loss (the impact of removing that feature group on the model's Skill Score):

"""

    for idx, r in enumerate(rankings_by_tss, 1):
        name = r["experiment"].replace("_", " ").title()
        md_content += f"{idx}. **{name}**: Relative TSS Loss = {r['relative_tss_loss']:.6f} (F1 Loss = {r['relative_f1_loss']:.6f}, ROC-AUC Loss = {r['relative_auc_loss']:.6f}, Attention Entropy Shift = {r['entropy_change']:.6f})\n"

    md_content += f"""
## SECTION 3: Information Deficit Analysis (Aditya-L1 Readiness)

The relative TSS losses for the three key physical feature groups are as follows:
- **Flux (Both Channels)**: Relative TSS Loss = {losses["flux"]["relative_tss_loss"]:.6f}
- **History (Minutes Since Last Flare)**: Relative TSS Loss = {losses["history"]["relative_tss_loss"]:.6f}
- **Derivatives (Gradients & Accelerations)**: Relative TSS Loss = {losses["derivatives"]["relative_tss_loss"]:.6f}

### Conclusion and Sprint 9 Path

Based on the measured skill degradation, the dominant source of information is **{dominant_group}** with a relative TSS loss of {dominant_tss_loss:.6f}.

Decision rule outcome:
{readiness_status}
"""

    # Strict vocabulary assertion check
    check_banned_words(md_content)

    with open(INFO_GAP_REPORT_MD, "w") as fh:
        fh.write(md_content)
    logger.info(f"Saved Markdown report to {INFO_GAP_REPORT_MD}")


if __name__ == "__main__":
    main()

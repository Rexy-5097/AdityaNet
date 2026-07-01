"""
scripts/information_gap_report.py

Sprint 8 — Information Gap Audit

Loads: artifacts/feature_dependence_audit.json
Ranks experiments by degradation in F1, TSS, and ROC-AUC.
Computes relative degradation metrics.
Saves to: artifacts/information_gap_report.json
"""

import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

AUDIT_PATH = os.path.join("artifacts", "feature_dependence_audit.json")
REPORT_PATH = os.path.join("artifacts", "information_gap_report.json")


def main():
    logger.info("Starting Information Gap Report Generation...")
    if not os.path.exists(AUDIT_PATH):
        logger.error(f"Missing audit results file: {AUDIT_PATH}")
        return

    with open(AUDIT_PATH, "r") as fh:
        audit_data = json.load(fh)

    results = audit_data["results"]
    baseline = results["baseline"]

    baseline_f1 = baseline["F1"]
    baseline_tss = baseline["TSS"]
    baseline_auc = baseline["ROC-AUC"]

    rankings = []
    for exp_name, exp_metrics in results.items():
        if exp_name == "baseline":
            continue

        f1_val = exp_metrics["F1"]
        tss_val = exp_metrics["TSS"]
        auc_val = exp_metrics["ROC-AUC"]

        f1_loss = float(baseline_f1 - f1_val)
        tss_loss = float(baseline_tss - tss_val)
        auc_loss = float(baseline_auc - auc_val)

        rel_f1_loss = float(f1_loss / baseline_f1) if baseline_f1 > 0 else 0.0
        rel_tss_loss = float(tss_loss / baseline_tss) if baseline_tss > 0 else 0.0
        rel_auc_loss = float(auc_loss / baseline_auc) if baseline_auc > 0 else 0.0

        rankings.append({
            "experiment": exp_name,
            "F1": f1_val,
            "TSS": tss_val,
            "ROC-AUC": auc_val,
            "f1_loss": f1_loss,
            "tss_loss": tss_loss,
            "auc_loss": auc_loss,
            "relative_f1_loss": rel_f1_loss,
            "relative_tss_loss": rel_tss_loss,
            "relative_auc_loss": rel_auc_loss,
            "mean_attention_entropy": exp_metrics["mean_attention_entropy"],
            "mean_top_patch_share": exp_metrics["mean_top_patch_share"],
            "entropy_change": float(exp_metrics["mean_attention_entropy"] - baseline["mean_attention_entropy"])
        })

    # Sort experiments by relative TSS loss descending (highest loss first = most important feature)
    rankings_by_tss = sorted(rankings, key=lambda x: x["relative_tss_loss"], reverse=True)
    # Sort experiments by relative F1 loss descending
    rankings_by_f1 = sorted(rankings, key=lambda x: x["relative_f1_loss"], reverse=True)
    # Sort experiments by relative AUC loss descending
    rankings_by_auc = sorted(rankings, key=lambda x: x["relative_auc_loss"], reverse=True)

    report = {
        "baseline": baseline,
        "rankings_by_tss_loss": rankings_by_tss,
        "rankings_by_f1_loss": rankings_by_f1,
        "rankings_by_auc_loss": rankings_by_auc
    }

    with open(REPORT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)
    logger.info(f"Saved ranked information gap report to {REPORT_PATH}")


if __name__ == "__main__":
    main()

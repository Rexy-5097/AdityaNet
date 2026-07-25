"""
scripts/signal_audit/run_impulsive_only.py

Sprint 9A — Signal Attribution Audit: Impulsive Features Only (Experiment D)
"""

import sys
import logging
from audit_helper import run_signal_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing impulsive-features-only signal audit run...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    feature_cols = cfg["feature_cols"]
    
    # Calculate dataset medians
    medians = test_df[feature_cols].median().to_dict()
    
    # Reconstruct test split with all features except impulsive ones replaced with medians
    test_df_mod = test_df.copy()
    impulsive_cols = [
        "short_flux",
        "flux_gradient_5m",
        "flux_gradient_15m",
        "flux_acceleration_5m",
        "flux_acceleration_15m"
    ]
    for col in feature_cols:
        if col not in impulsive_cols:
            test_df_mod[col] = medians[col]
            
    run_signal_experiment(test_df_mod, "impulsive_only", "impulsive_only.json")
    logger.info("Impulsive-features-only run completed.")

if __name__ == "__main__":
    main()

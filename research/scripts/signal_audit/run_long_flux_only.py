"""
scripts/signal_audit/run_long_flux_only.py

Sprint 9A — Signal Attribution Audit: Long Flux Only (Experiment B)
"""

import sys
import logging
from audit_helper import run_signal_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing long-flux-only signal audit run...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    feature_cols = cfg["feature_cols"]
    
    # Calculate dataset medians
    medians = test_df[feature_cols].median().to_dict()
    
    # Reconstruct test split with all features except long_flux/log_long_flux replaced with medians
    test_df_mod = test_df.copy()
    for col in feature_cols:
        if col not in ["long_flux", "log_long_flux"]:
            test_df_mod[col] = medians[col]
            
    run_signal_experiment(test_df_mod, "long_flux_only", "long_flux_only.json")
    logger.info("Long-flux-only run completed.")

if __name__ == "__main__":
    main()

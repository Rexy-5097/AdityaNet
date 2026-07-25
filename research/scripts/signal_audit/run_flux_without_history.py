"""
scripts/signal_audit/run_flux_without_history.py

Sprint 9A — Signal Attribution Audit: Flux Without History (Experiment E)
"""

import sys
import logging
from audit_helper import run_signal_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing flux-without-history signal audit run...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    feature_cols = cfg["feature_cols"]
    
    # Calculate dataset medians
    medians = test_df[feature_cols].median().to_dict()
    
    # Reconstruct test split with history replaced by its median
    test_df_mod = test_df.copy()
    test_df_mod["minutes_since_last_flare"] = medians["minutes_since_last_flare"]
            
    run_signal_experiment(test_df_mod, "flux_without_history", "flux_without_history.json")
    logger.info("Flux-without-history run completed.")

if __name__ == "__main__":
    main()

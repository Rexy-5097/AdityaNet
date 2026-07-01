"""
scripts/signal_audit/run_history_only.py

Sprint 9A — Signal Attribution Audit: History Only (Experiment A)
"""

import sys
import logging
from audit_helper import run_signal_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing history-only signal audit run...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    feature_cols = cfg["feature_cols"]
    
    # Calculate dataset medians
    medians = test_df[feature_cols].median().to_dict()
    
    # Reconstruct test split with all features except history replaced with medians
    test_df_mod = test_df.copy()
    for col in feature_cols:
        if col != "minutes_since_last_flare":
            test_df_mod[col] = medians[col]
            
    run_signal_experiment(test_df_mod, "history_only", "history_only.json")
    logger.info("History-only run completed.")

if __name__ == "__main__":
    main()

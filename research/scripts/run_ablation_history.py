"""
scripts/run_ablation_history.py

Sprint 8 — Information Gap Audit: History Ablation (minutes_since_last_flare -> 0)
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing History Ablation...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    # Ablate History
    test_df_mod = test_df.copy()
    test_df_mod["minutes_since_last_flare"] = 0.0
    
    run_experiment(test_df_mod, "ablation_history", "ablation_history.json")
    logger.info("History ablation finished.")

if __name__ == "__main__":
    main()

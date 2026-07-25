"""
scripts/run_ablation_engineered.py

Sprint 8 — Information Gap Audit: Engineered Feature Ablation
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Engineered Feature Ablation...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    feature_cols = cfg["feature_cols"]
    
    # Ablate Engineered Features (keep only long_flux and short_flux)
    test_df_mod = test_df.copy()
    for col in feature_cols:
        if col not in ["long_flux", "short_flux"]:
            test_df_mod[col] = 0.0
            
    run_experiment(test_df_mod, "ablation_engineered", "ablation_engineered.json")
    logger.info("Engineered feature ablation finished.")

if __name__ == "__main__":
    main()

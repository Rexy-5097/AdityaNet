"""
scripts/run_ablation_derivatives.py

Sprint 8 — Information Gap Audit: Derivative Ablation
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Derivative Ablation...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    # Ablate Derivatives
    test_df_mod = test_df.copy()
    for col in ["flux_gradient_5m", "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m"]:
        test_df_mod[col] = 0.0
    
    run_experiment(test_df_mod, "ablation_derivatives", "ablation_derivatives.json")
    logger.info("Derivative ablation finished.")

if __name__ == "__main__":
    main()

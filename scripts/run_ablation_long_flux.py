"""
scripts/run_ablation_long_flux.py

Sprint 8 — Information Gap Audit: Long Flux Ablation (long_flux & log_long_flux -> 0)
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Long Flux Ablation...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    # Ablate Long Flux
    test_df_mod = test_df.copy()
    test_df_mod["long_flux"] = 0.0
    test_df_mod["log_long_flux"] = 0.0
    
    run_experiment(test_df_mod, "ablation_long_flux", "ablation_long_flux.json")
    logger.info("Long flux ablation finished.")

if __name__ == "__main__":
    main()

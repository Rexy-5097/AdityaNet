"""
scripts/run_ablation_short_flux.py

Sprint 8 — Information Gap Audit: Short Flux Ablation (short_flux -> 0)
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Short Flux Ablation...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    # Ablate Short Flux
    test_df_mod = test_df.copy()
    test_df_mod["short_flux"] = 0.0
    
    run_experiment(test_df_mod, "ablation_short_flux", "ablation_short_flux.json")
    logger.info("Short flux ablation finished.")

if __name__ == "__main__":
    main()

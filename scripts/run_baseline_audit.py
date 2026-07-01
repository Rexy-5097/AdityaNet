"""
scripts/run_baseline_audit.py

Sprint 8 — Information Gap Audit: Baseline Evaluation
"""

import sys
import logging
from audit_helper import run_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Baseline Evaluation...")
    # Load config and model to get test_df
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    # Run baseline experiment
    run_experiment(test_df, "baseline", "baseline.json")
    logger.info("Baseline evaluation finished.")

if __name__ == "__main__":
    main()

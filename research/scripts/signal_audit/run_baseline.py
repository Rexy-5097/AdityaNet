"""
scripts/signal_audit/run_baseline.py

Sprint 9A — Signal Attribution Audit: Baseline Evaluation (n_samples=5)
"""

import sys
import logging
from audit_helper import run_signal_experiment, load_config_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing baseline signal audit run...")
    cfg = load_config_and_model()
    test_df = cfg["test_df"]
    
    run_signal_experiment(test_df, "baseline", "baseline.json")
    logger.info("Baseline run completed.")

if __name__ == "__main__":
    main()

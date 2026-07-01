#!/usr/bin/env bash
set -e

echo "===== SuryaNet Sprint 3 Verification ====="

source venv/bin/activate
export PYTHONPATH=$PWD

# Install dependencies (requirements.txt contains pandas, numpy, scikit-learn, pyarrow, pandera)
pip install -r requirements.txt

# Run ML baseline training
echo "Training baseline model..."
python3 scripts/train_baseline.py

# Verify artifact generation
echo ""
echo "===== Generated Artifacts ====="
ls -la artifacts/

echo ""
echo "===== Baseline Performance Metrics ====="
cat artifacts/baseline_metrics.json

echo ""
echo "===== SPRINT 3 COMPLETE ====="

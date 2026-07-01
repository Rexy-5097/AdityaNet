#!/bin/bash
# SuryaNet V3 Training Campaign - Command Launch Script
# Generated statelessly for the 5 independent campaign seed runs.

python3 scratch/run_sprint14c_experiment.py --seed 42 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 123 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 3407 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 2026 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 9999 --epochs 10 --model-type D

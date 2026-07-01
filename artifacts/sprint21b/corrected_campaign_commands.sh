#!/bin/bash
# SuryaNet V3 Training Campaign — Corrected Command Launch Script
# Sprint 21B: All 8 commands verified against run_sprint14c_experiment.py CLI.
#
# CAMPAIGN SEED RUNS (5 runs, model-type D = GOES + SoLEXS + HEL1OS)
# Status: PLANNED — not yet executed.

python3 scratch/run_sprint14c_experiment.py --seed 42   --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 123  --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 3407 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 2026 --epochs 10 --model-type D
python3 scratch/run_sprint14c_experiment.py --seed 9999 --epochs 10 --model-type D

# ABLATION RUNS — SEED 42 ONLY (scheduled after campaign seed runs complete)
# Uses --skip-stage1 to reuse model_seed_42_stage1_best.pt (already exists).
# model-type A = GOES only
# model-type B = GOES + SoLEXS
# model-type C = GOES + HEL1OS

python3 scratch/run_sprint14c_experiment.py --seed 42 --epochs 10 --model-type A --skip-stage1
python3 scratch/run_sprint14c_experiment.py --seed 42 --epochs 10 --model-type B --skip-stage1
python3 scratch/run_sprint14c_experiment.py --seed 42 --epochs 10 --model-type C --skip-stage1

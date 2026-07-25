"""
scripts/sprint32/auto_escalate.py

Sprint 32 Phase 3 — automatic pre-registered escalation (Sprint 25 / F1.json
rule): if an arm's across-seed test TSS range over seeds 42/43/44 exceeds
0.015, seeds 45/46 must be trained before any verdict. Reads sealed eval.json
files, PRINTS NO METRIC, exits 42 to escalate / 0 otherwise.

Usage: auto_escalate.py <run_prefix>   e.g. F3   or   EMG
"""
import json, os, sys

prefix = sys.argv[1]
tss = [json.load(open(f"artifacts/sprint32/runs/{prefix}_s{s}/eval.json"))
       ["policy"]["window"]["TSS"] for s in (42, 43, 44)]
triggered = (max(tss) - min(tss)) > 0.015
print(f"[{prefix}] ESCALATION {'TRIGGERED' if triggered else 'NOT TRIGGERED'} "
      f"(3-seed range vs 0.015; values sealed until Phase 4)", flush=True)
sys.exit(42 if triggered else 0)

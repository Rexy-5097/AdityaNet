"""
scripts/sprint31/auto_escalate.py

Sprint 31 Phase 3 — automatic application of the pre-registered escalation
rule (Sprint 25 / F1.json / 04_FAIR_ADITYA_EXPERIMENT.md U1): if the F2
across-seed test TSS range over seeds 42/43/44 exceeds 0.015, seeds 45/46
must be trained BEFORE any verdict, with no manual intervention.

Integrity: this script reads the sealed eval.json files but PRINTS NO METRIC
— only the boolean decision. Exit code 42 = escalate; 0 = no escalation.
"""
import json
import sys

tss = [json.load(open(f"artifacts/sprint31/runs/F2_s{s}/eval.json"))
       ["policy"]["window"]["TSS"] for s in (42, 43, 44)]
triggered = (max(tss) - min(tss)) > 0.015
print(f"ESCALATION {'TRIGGERED' if triggered else 'NOT TRIGGERED'} "
      f"(range vs 0.015 threshold; values sealed until Phase 5)", flush=True)
sys.exit(42 if triggered else 0)

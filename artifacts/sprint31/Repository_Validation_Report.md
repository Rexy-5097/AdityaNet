<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 — quality-gate outputs, all gates. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Repository Validation Report

**All quality gates PASS (OBSERVED, this session, after all Sprint 31 artifacts were produced).**

## Gate outputs

**Version 3 integrity:**
```
PASS  V3 stage2 checkpoint  (SHA-256 == benchmark_manifest.json)
PASS  frozen s2_test unchanged
PASS  Sprint 24 harness unchanged  (SHA-256 == artifacts/sprint26/phase1_fingerprints.json)
```
The frozen harness file was never edited; block-length sensitivity used runtime constant override only (Sprint 24 precedent).

**CI (six gates, `scripts/ci/run_ci.sh`):**
```
gate 1 ruff lint: PASS          gate 4 policy provenance: policy 9/9 checks PASS
gate 2 format: PASS (advisory)  gate 5 determinism x2: 3 passed / 3 passed
gate 3 pytest: 59 passed        gate 6 AgentOS validator: 100/100 PASS
CI: ALL GATES PASS
```

**Provenance validity:**
```
PASS  deployed policy 9/9 startup checks
PASS  dataset_v4.0.0 manifest verifies (self-hash + all source SHAs)
PASS  dataset_v4.1.0-s2 manifest verifies (self-hash + all source SHAs)
```

**Reproducibility / deterministic rerun:**
```
PASS  analyze_s2.py rerun produces identical primary endpoint, paired
      comparisons, block-robustness tables, and stratification
PASS  aditya feature computation deterministic (two builds, identical frame
      hashes — build_report.json; independently confirmed by the Phase 2
      subagent on 262,480 rows)
PASS  F0 baseline reproduction: F0-on-V1-span TSS reproduced its
      pre-registered reference exactly in Sprint 30 (0.3940129618); F0-on-S2
      is a first measurement (0.4068), archived with calibrated probabilities
      for future reproduction
```

**AgentOS validation:** 100/100, Final Status PASS (gate 6 above).

## Integrity-measure inventory for this sprint

1. Sealed evaluation runner (`scripts/sprint31/eval_s2.py`) — writes eval.json + probability arrays, prints no test metric.
2. Automatic escalation (`scripts/sprint31/auto_escalate.py`) — the seed-range decision taken without any value reaching the transcript (output: "ESCALATION TRIGGERED (range vs 0.015 threshold; values sealed until Phase 5)").
3. Analysis rules pre-committed (`30d4f23`) before any F2/F1-on-S2/F0-on-S2 result existed — including the F2-vs-F0 comparison that ultimately complicated the verdict, proving it was not a post-hoc addition.
4. Phase 2 verification by an independent subagent with its own reimplementation of every formula.
5. No frozen artifact modified; no threshold changed; no rerun of any seed.

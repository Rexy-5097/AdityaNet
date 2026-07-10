<!-- VERSION STATUS: CURRENT -->
<!-- REASON: V4 problem dependency graph, written at V4 planning. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Dependency Graph

**Conclusion: there are four root blockers.** RB1, the missing episode-level evaluation harness, blocks the largest set of downstream problems (nine), including everything operator-facing; RB2, the flare-empty joint instrument corpus, blocks the entire multi-instrument research line; RB3, the unmatched baseline comparison, blocks every skill claim; RB4, the missing engineering substrate, blocks operational deployment but nothing scientific. RB1 and RB3 are resolved by the same sprint (the harness scores baselines too), which is why Sprint 24 targets them jointly. Problem numbers (P1–P28) refer to the classification table in `VERSION4_MASTER_PLAN.md`.

## Root blockers

| Root | Problem | Why it is a root | Downstream count |
|------|---------|------------------|------------------|
| **RB1** | P3 — no episode-level, block-bootstrap evaluation harness | Every operator-facing quantity (RED-tier design, uncertainty tiers, FN/FP strata, trust metrics) is currently measured with autocorrelated stride-1 windows and i.i.d. bootstraps (`app/services/ml/metrics.py::paired_bootstrap_test`); nothing downstream can be honestly optimized or compared without the yardstick | 9 |
| **RB2** | P5-data — joint GOES+Aditya-L1 corpus contains zero flares | `artifacts/aditya_l1/overlap_dataset.parquet` is 4 quiet days; no engineering or modeling can substitute for flare-bearing joint observations; raw material exists (`data/aditya_l1/processed/`: SoLEXS 915 files from Dec 2023, HEL1OS 960 files from Oct 2023) | 4 |
| **RB3** | P2 — persistence-vs-model superiority unestablished | `artifacts/baseline_metrics.json` (persistence TSS 0.3029) vs `artifacts/evaluation_audit_report.json` (V1 fixed-threshold TSS 0.2298) under mismatched windowing; until matched, no skill claim survives review | 6 |
| **RB4** | P16–P21 — engineering substrate (tests/git/CI/auth/ingestion/Dockerfile) | Blocks live operation and safe iteration; blocks no scientific conclusion | 5 |

## Full graph (edges read "X blocks Y")

```
RB1  P3 episode harness absent
 ├── P1  RED tier restoration (cost-loss selection needs episode-level objective)
 ├── P4  uncertainty-tier derivation (tiers must be judged on episode error rates)
 ├── P14 MC-Dropout validity (std-vs-error correlation needs episode strata)
 ├── P2  matched baseline comparison (persistence must run through the same harness)  ← joint with RB3
 ├── P7  stealth-FN mitigation MEASUREMENT (quiet-background episode recall stratum)
 ├── P8  decay-FP mitigation MEASUREMENT (post-flare episode precision stratum)
 ├── P27 6-hour-horizon actionability (lead-time distributions are episode quantities)
 ├── P23 monitoring design (what to monitor = the harness metrics)
 └── P13 conformal prediction evaluation (coverage must be episode-aware)

RB2  P5-data flare-empty joint corpus
 ├── P5  SCI-001 verdict (significance test needs joint flare episodes)
 │    ├── P11 V3 integrate-or-retire decision
 │    ├── P24 instrument-based explainability hopes (HEL1OS impulsive precursors)
 │    └── publication multi-instrument claim (NMI reviewer, adversarial review F8)
 └── P7-instrument-path (HEL1OS as stealth-flare channel is untestable without joint flares)

RB3  P2 unmatched baselines
 ├── every TSS/skill claim in VERSION3_SCIENTIFIC_BASELINE.md's successor documents
 ├── P28 location-awareness value (only measurable against a fair skill floor)
 └── publication viability (NASA reviewer, adversarial review F5)

RB4  engineering substrate
 ├── P21 ingestion → shadow-mode operation → operator pilot (Phase E)
 ├── P20 auth → any external exposure
 ├── P16/P18 tests+CI → safe retraining iteration in Phase D
 ├── P19 Dockerfile → deployable service
 └── P22 frontend → operator-visible trust surface

Independent / weakly coupled:
 P6  regime portability (needs RB1's harness for episode-level monthly metrics; data already present)
 P9  multi-seed variance (independent; compute-bound)
 P10 temperature forensics (independent; low value)
 P12 model_v3.py defaults (independent; trivial; prerequisite hygiene for RB2's analysis runs)
 P15 determinism pinning (independent; documentation/convention)
 P17 git (prerequisite hygiene for everything in Phase D/E; zero science coupling)
 P25/P26 provenance+docs maintenance (process; independent)
```

## Illustrative chains (the brief's example, made concrete)

- Flare-empty overlap corpus (RB2) → no joint flare episodes → SCI-001 untestable → V3 fusion architecture undecidable (P11) → multi-instrument operator story unsupportable → ISRO value proposition rests on GOES-only skill → which itself is blocked by RB3.
- Missing episode harness (RB1) → RED-tier thresholds cannot be selected against episode costs (P1) → operators receive a GREEN/YELLOW-only forecaster (`artifacts/operator_backtest.json` RED: 0) → highest-severity alerting is untrustworthy by absence → operator trust capped regardless of model quality.
- Unmatched persistence baseline (RB3) → V1's 0.2298 fixed-threshold TSS sits below persistence's 0.3029 with no matched comparison → any reviewer (NASA persona, adversarial review) can nullify the skill claim → publication and ISRO scientific credibility blocked.

## Sequencing consequence

Sprint 24 must attack RB1+RB3 together (one harness, model and baselines both on it) because they share all their machinery and neither requires new data or training. RB2 is the next sprint pair after (or overlapping, since it is data engineering, not evaluation). RB4 is deliberately last among the roots: it multiplies engineering velocity but resolves no scientific unknown, and V3's history (Sprint 20B PASS/FAIL contradiction; the undeployed Sprint 5.6 fix) shows the project's failures have been epistemic, not infrastructural.

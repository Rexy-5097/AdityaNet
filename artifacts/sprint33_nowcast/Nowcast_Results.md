<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 frozen-contract results — five-seed primary verdict with full sealed measurements. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Nowcast Results (five seeds, frozen contract)

**Primary verdict by the frozen decision rule: REJECTED — 0 of 5 seeds pass (majority of 3 required). At validation-selected operating points holding ≈ 0.90 episode recall, the Aditya-only nowcaster produces 22.4–50.9 false episodes per month on the sealed Stage-2 test set against the pre-registered budget of ≤ 5.0. The null hypothesis of the frozen contract holds: no validation-selected threshold operating point yields a deployable low-false-alarm detector; the result is a publishable scientific characterization, not a deployable system.** All values below are `OBSERVED` from the single sealed evaluation pass per seed (`artifacts/sprint33_nowcast/runs/s<seed>/eval.json`) unless labelled `DERIVED`.

## Per-seed sealed measurements (policy: validation-selected threshold at ≥ 0.90 validation episode recall)

| Seed | Threshold | Val recall | Test FE/month [95% CI] | Test episode recall [95% CI] | Detection latency (med, min) | Time under alert | Op-point stability | Window ROC-AUC | Passes |
|------|-----------|------------|------------------------|------------------------------|------------------------------|------------------|--------------------|----------------|--------|
| 42 | 0.030 | 0.9155 | 50.92 [43.21, 59.13] | 0.9279 [0.856, 0.983] | 5.0 | 0.0301 | 0.0124 | 0.8977 | NO |
| 43 | 0.045 | 0.9014 | 39.69 [32.82, 47.06] | 0.9189 [0.829, 0.983] | 6.0 | 0.0218 | 0.0175 | 0.8960 | NO |
| 44 | 0.100 | 0.9014 | 22.44 [18.09, 27.13] | 0.9009 [0.820, 0.968] | 7.0 | 0.0103 | 0.0005 | 0.8982 | NO |
| 45 | 0.110 | 0.9014 | 27.64 [22.11, 33.33] | 0.9099 [0.823, 0.975] | 7.0 | 0.0115 | 0.0085 | 0.8972 | NO |
| 46 | 0.060 | 0.9014 | 39.02 [31.99, 46.40] | 0.9099 [0.823, 0.975] | 6.0 | 0.0158 | 0.0085 | 0.9035 | NO |

`DERIVED` five-seed aggregates (first-principles-verified in `analysis.json`): false episodes per month 35.94 ± 11.17 (range 28.47); episode recall 0.9135 ± 0.0103; time under alert 1.0–3.0% of the period; detection latency median 5–7 minutes into a median 11-minute rise phase.

## What the detector demonstrably does well (OBSERVED)

Episode recall is high and seed-stable (0.90–0.93), detection is fast (first alert a median 5–7 minutes after flare start), the operating point transfers from validation to test almost perfectly (stability 0.0005–0.0175, retiring contract risk 2), the capability gate replicated across all five seeds (validation window ROC-AUC 0.8857–0.8991 vs the 0.87 gate), and total alert load is small in *time* (1–3% duty). The failure is specifically the *count of distinct false alert episodes* under the pre-registered M/X rise-phase label.

## Scope of the finding (corrected wording, agreed in review)

What is `OBSERVED`: the **current detector (15 SoLEXS+HEL1OS features, PatchTST, M/X rise-phase label) under single-threshold operating policies** cannot reach the deployment region — at every threshold with mean episode recall ≥ 0.80, mean false episodes per month is ≥ 14.27 (five-seed curve; `Operating_Point_Analysis.md`). What is **not** demonstrated and remains hypothesis: that the SoLEXS+HEL1OS *signal* is insufficient (one feature set, one architecture, one label family, one policy family tested); that a richer alert policy, a class-aware label formulation, a different detector, or a revised operational budget could not close the gap; and what the "false" episodes physically are — the test span contains thousands of catalogued sub-M/X (C-class) flares that the pre-registered label scores as false detections. Explanatory attribution of the false episodes is registered as follow-up **Experiment A**, and the instrument-relative benchmark (an identical GOES-17 nowcast control) as **Experiment B**; this verdict is based solely on the pre-registered endpoint and is unaffected by either.

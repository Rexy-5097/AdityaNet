NO

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 frozen-contract verdict — operationally usable YES/NO by the frozen decision rule. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Verdict: operationally usable? NO

**By the frozen decision rule (`artifacts/sprint33_nowcast/00_PREREGISTRATION.md`, committed `d142cf8` before any result): the Aditya-only nowcaster is NOT operationally usable at the pre-registered requirements. Zero of five seeds achieve test false-episodes-per-month ≤ 5.0 with episode recall ≥ 0.80 at a validation-selected operating point (majority of 3 required); the observed values are 22.44–50.92 false episodes per month at 0.90–0.93 recall, with every seed's entire 95% confidence interval above the budget. The primary hypothesis is REJECTED and the null holds: the result is a publishable scientific characterization, not a deployable detector.**

This verdict is based solely on the pre-registered endpoint under the M/X rise-phase label and single-threshold operating policies, and its scope is exactly that: the **current detector under threshold policies cannot reach the deployment region** (minimum observed 14.27 false episodes per month at the 0.80 recall floor, five-seed mean curve). It does **not** establish that the SoLEXS+HEL1OS signal is insufficient, that no alert policy or label formulation could close the gap, or that the 5.0 budget is attainable by any detector on this span — those remain open questions. What the sprint *positively* established: high, seed-stable episode recall (0.9135 ± 0.0103), fast detection (median 5–7 minutes into the rise phase), near-perfect validation-to-test operating-point transfer (≤ 0.0175), low alert duty (1–3% of time), and five-seed replication of the window-level capability (validation ROC-AUC 0.886–0.899).

**Forward pointers (separately registered, per the agreed three-phase order):** Experiment A — physical attribution of the false episodes against the flare catalog (are they uncatalogued noise or real sub-M/X flares?); Experiment B — an identical GOES-17 nowcast control (is the gap Aditya-relative or task-relative?). Neither can alter this verdict; both determine what it means and what follows it.

**Definition of DONE:** five seeds trained and sealed-evaluated (escalation completed per the fired clause) — met; primary verdict computed by the frozen rule and recorded here — met; quality gates passed (provenance pre/post, leakage, capability ≥ 0.87, determinism) — met; all eight deliverables written — met. The sprint is COMPLETE with a NO verdict, which under the frozen Definition of DONE is a complete sprint regardless of the metric outcome.

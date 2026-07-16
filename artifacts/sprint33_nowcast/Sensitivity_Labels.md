<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 — pre-registered label sensitivity analyses (whole-event, onset-only). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Sensitivity Labels

**The REJECTED verdict is robust to the label definition: at each seed's frozen operating point, the whole-event label reproduces the failure almost identically, and the onset-only label fails far worse. The rise-phase label was the most favorable of the three pre-registered formulations, so no alternative label choice rescues the primary endpoint.** All values `OBSERVED` from `artifacts/sprint33_nowcast/analysis.json`, computed on the frozen sealed test predictions at the frozen per-seed thresholds — no re-selection, no re-inference.

## Whole-event label ([start_time, end_time] of M/X flares)

| Seed | Episode recall | FE/month | Passes |
|------|----------------|----------|--------|
| 42 | 0.9252 | 50.92 | NO |
| 43 | 0.9159 | 39.69 | NO |
| 44 | 0.8972 | 22.44 | NO |
| 45 | 0.9065 | 27.64 | NO |
| 46 | 0.9065 | 39.02 | NO |

Reading: recall and false-episode rates are nearly identical to the primary rise-phase label — an alert stream overlapping rise phases almost always overlaps the containing whole event, and the "false" set barely changes. `DERIVED`: extending the label window rightward (through decay phases) does not absorb the false episodes, which is a first indication that the false episodes are not late-decay-phase alerts on M/X flares themselves.

## Onset-only label ([start_time] minute of M/X flares)

| Seed | Episode recall | FE/month | Passes |
|------|----------------|----------|--------|
| 42 | 0.5175 | 58.79 | NO |
| 43 | 0.4649 | 47.90 | NO |
| 44 | 0.3772 | 31.99 | NO |
| 45 | 0.4035 | 36.85 | NO |
| 46 | 0.4386 | 47.57 | NO |

Reading: requiring the alert to overlap the single start minute roughly halves recall (the detector typically fires a median of 5–7 minutes *after* start — see detection latency in `Nowcast_Results.md`) and inflates the false count (alerts that graze a rise phase without covering its first minute become "false"). `DERIVED`: the detector behaves as a *developing-flare detector*, not a start-minute detector — consistent with the physics (the soft X-ray enhancement it reads grows through the rise phase).

## Conclusion

Label formulation is not the binding constraint under threshold policies: all three pre-registered labels fail the deployment criterion at every seed. What no label variant here can answer is what the false episodes physically are — that is the registered follow-up Experiment A.

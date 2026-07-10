<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 pre-registered analysis plan, locked before any training result is seen. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Pre-Registered Analysis Plan

**Conclusion:** Every trained model is scored once through the frozen Sprint 24 harness against the fixed persistence and climatology baselines; significance is judged by the paired moving-block bootstrap (2,880-window blocks, 1,000 replicates, seed 20260704) already used in Sprint 24, never by IID tests or naive interval overlap; ablation effects are estimated as the per-configuration mean across five seeds minus the B0 baseline mean, with seed standard deviation reported; and the final recommendation is a mechanical function of the pre-registered success criteria, so it cannot be adjusted after results are seen. Negative results are reported in full and trigger the campaign-failure escalation.

## 1. Statistical tests

- **Model versus baseline (primary and skill secondaries):** paired moving-block bootstrap on identical resample indices, as implemented in `scripts/sprint24/eval_framework.py` (`paired_window`, `paired_episode`). Block length 2,880 windows; 1,000 replicates for confusion-derived metrics; 200 replicates for ROC-AUC and PR-AUC; episode blocks of 10 episodes. Significance = the 95% percentile interval of the paired difference excludes zero. Bootstrap two-sided p-values reported with floor 1/1000.
- **No IID tests, no McNemar:** stride-1 windows are autocorrelated (359/360 input overlap); IID resampling and McNemar's independence assumption are both invalid and are excluded, exactly as justified in `artifacts/sprint24/04_bootstrap_analysis.md` and `artifacts/sprint24/06_statistical_tests.md`.
- **Across-seed:** for each configuration and endpoint, report the five-seed mean and sample standard deviation; a configuration "meets" an endpoint in a seed if that seed's point estimate clears the pre-registered threshold in `04_success_criteria.md`.

## 2. Confidence intervals

- All confidence intervals are 95% percentile intervals from the block bootstrap above, computed identically for every method — no method receives a bespoke interval.
- Seed-level variability is reported separately as mean ± standard deviation across the five seeds; the two sources of uncertainty (within-run bootstrap and across-seed) are never pooled into a single interval, to keep them interpretable.
- Block-size robustness is confirmed once, by recomputing the primary endpoint at block lengths 1,440 / 2,880 / 5,760 as in Sprint 24; the 2,880 result is authoritative.

## 3. Aggregating ablations into a recommendation

- **Per-configuration outcome:** a configuration is `SUCCESS`, `INSUFFICIENT`, or `FAILED-TRIGGER` (the last if any immediate-termination trigger fired). `SUCCESS` requires the primary endpoint plus ≥ 5 of 8 secondary endpoints in ≥ 3 of 5 seeds (`04_success_criteria.md`).
- **Effect attribution:** because each ablation changes exactly one variable from B0, the effect of that variable is estimated as (configuration mean − B0 mean) per endpoint, with the paired bootstrap applied at the per-seed level where seeds are matched. No two-variable interactions are estimated, because no two-variable experiments exist by construction.
- **Campaign recommendation:**
  - If ≥ 1 configuration is `SUCCESS`: recommend adopting the single best-performing `SUCCESS` configuration by primary-endpoint point estimate, and register the resulting model through the Sprint 23 provenance pipeline; ranking ties broken by pre-onset episode recall, then by yellow duty cycle (lower wins).
  - If no configuration is `SUCCESS` but ≥ 1 improves on Sprint 24 Method C without reaching +0.1062: report "insufficient improvement," adopt nothing, and escalate to architecture redesign (Decision Option C).
  - If no configuration improves on Sprint 24 Method C: report campaign `FAILED` and escalate to architecture redesign.
- **Multiple-comparisons stance:** the primary endpoint is a single pre-specified test; the eight secondary endpoints are reported with their individual intervals and explicitly labeled as secondary, so no secondary result can be promoted to the headline claim after the fact. No secondary p-value is used to declare campaign success.

## 4. Reporting negative results

- Every configuration's full metric table (all Sprint 24 metrics plus Expected Calibration Error and Red-tier precision) is published under `artifacts/sprint26/` regardless of outcome, including `FAILED-TRIGGER` runs with the trigger named.
- A negative campaign (no `SUCCESS`) is reported as the headline finding with the same prominence a positive result would receive; the phrasing "training improvements did not close the gap" is pre-authorized and will not be softened.
- The B0 baseline's five-seed distribution is reported first, so every ablation is read against the honest reproduction of the frozen model, not against the single-seed frozen point estimate.
- The pre-registration (this document set) is referenced by every results document, so a reader can confirm no endpoint, threshold, or stopping rule moved after results were seen.

## 5. Fixed inputs (locked)

Frozen Sprint 24 harness (`scripts/sprint24/eval_framework.py`); frozen test split (`artifacts/research/test.parquet`); persistence True Skill Score 0.3018 and climatology True Skill Score 0.0000 baselines (`artifacts/sprint24/results_abc.json`); bootstrap seed 20260704; all thresholds and calibration fit on validation only. None of these may change during the campaign.

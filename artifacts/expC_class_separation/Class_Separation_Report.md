<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Experiment C results — Operational Class Separation per frozen pre-registration bbd99a2. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Experiment C — Operational Class Separation: Report

**Primary verdict by the frozen rule: H0 — the post-hoc class gate does not deliver operationally meaningful separation. Mean false-episode reduction R = 0.405, below the frozen 0.50 cut; 0 of 5 seeds meet the deployment criterion (≤ 5.0 false episodes per month at ≥ 0.80 M/X episode recall); mean gated rate 22.11 per month against the 5.0 budget. Reported without softening.** But the mandatory secondaries make the mechanism unambiguous and overturn the label-reformulation hypothesis outright: the Aditya observables *do* carry real class signal (test class-separation ROC-AUC 0.8745), and the frozen detector is *already strongly class-selective* — it detects 90.9% of M-class and 90.0% of X-class flares but only 24.4% of C-class and 0.2% of B-class. The residual false episodes are the brightest C-class flares, sitting at the C/M boundary where separation is intrinsically hardest. Executed per `00_PREREGISTRATION.md` (commit `bbd99a2`, tag `expC-prereg`); frozen count-reconciliation passed (304/237/134/165/233).

## Primary endpoint (DIRECTLY OBSERVED; sealed test, one touch)

| Seed | Gate | FE/month ungated → gated | Reduction R | Gated M/X recall | Class AUC | Passes |
|------|------|--------------------------|-------------|------------------|-----------|--------|
| 42 | 0.040 | 50.92 → 30.99 | 0.391 | 0.8919 | 0.8446 | NO |
| 43 | 0.020 | 39.69 → 31.15 | 0.215 | 0.9009 | 0.8829 | NO |
| 44 | 0.090 | 22.44 → 10.55 | 0.530 | 0.8108 | 0.8770 | NO |
| 45 | 0.075 | 27.64 → 13.57 | 0.509 | 0.8288 | 0.8777 | NO |
| 46 | 0.035 | 39.02 → 24.29 | 0.378 | 0.8919 | 0.8904 | NO |
| **mean** | — | 35.94 → **22.11** | **0.405** | **0.8649** | **0.8745** | **0/5** |

H0 is assigned because mean R = 0.405 < 0.50. Note the frozen H0 wording — "no *operationally meaningful* class-discriminative signal" — is a statement about operational sufficiency at the ≥ 0.90 validation-recall constraint, not about the existence of signal; the AUC secondary below directly measures that signal exists. Both statements are true and consistent: the distributions separate substantially yet overlap too much *at the recall constraint* to gate operationally.

## Secondary: the label re-characterisation (DIRECTLY OBSERVED) — the ISRO-alignment question, answered

| Label definition | Mean episode recall | Mean FE/month | Seeds passing budget |
|------------------|---------------------|---------------|----------------------|
| M/X-only (frozen Sprint 33) | 0.9135 | 35.94 | 0/5 |
| ≥ C (C+M+X) | **0.3194** | 5.76 | 0/5 |
| All-flare (B+C+M+X) | **0.2802** | 5.59 | 0/5 |

Per-class episode recall of the ungated frozen detector: **M 0.9094, X 0.9000, C 0.2437, B 0.0021.**

This overturns the pre-registered label-reformulation hypothesis decisively, and in the opposite direction from the `DERIVED` arithmetic that motivated it. The earlier reasoning was that, since Experiment A measured genuine false detections at only 1.86% (≈ 1/month, inside the ≤ 5.0 budget), a problem-statement-faithful all-flare label would convert the false alarms into true positives and the detector would pass. **It does not.** Under the ≥ C label the false rate does fall to 5.76 per month, but recall collapses to 0.3194 — far below the 0.80 floor — because the detector only finds 24.4% of the 1,651 catalogued C-class flares in the test span. The recall denominator explodes while the numerator does not follow. The detector is therefore **not** an all-flare monitor that a relabel could legitimise; it is an M/X-selective detector that additionally fires on the brightest quarter of C-class events.

## What this means, scope-bounded per the frozen contract

`DIRECTLY OBSERVED`: Aditya observables carry class-discriminative signal (test ROC-AUC 0.8745, seed range 0.845–0.890); the gate achieves a mean 40.5% false-episode reduction but leaves 22.11 per month; the detector's per-class recall is 3.7× higher for M/X (0.906 mean) than C (0.244); no label definition among the three tested meets the deployment criterion.

`LOGICALLY IMPLIED` (with Experiment A's 94.22% C-overlap composition and Sprint 33's 0.9135 ± 0.0103 M/X recall): the operational gap is not class-blindness — the detector is already substantially class-selective — but a **boundary-resolution limit**. The C-class flares it detects are those bright enough to resemble M-class events; separating them further would sacrifice M/X recall, which is exactly why the gate saturates at 40.5% reduction while holding ≥ 0.90 validation M/X recall. A post-hoc policy layer *can* exploit the signal (it removed 40.5% of false episodes without retraining) but cannot reach the budget.

`STILL HYPOTHESIS` (each requires its own pre-registered experiment before any claim): that a retrained class-aware detector, optimised directly against the C-versus-M/X boundary rather than gated post-hoc, would close the remaining 4.4× gap — the measured AUC of 0.8745 establishes exploitable signal exists, which motivates but does not confirm this; that the finding generalises beyond this single ~6-month solar-maximum window — the forecasting diagnostic established this regime is temporal-diversity-limited, so cycle-diverse data would be required; and that the ≤ 5.0 budget is attainable by any detector on this span — the GOES-17 control with the identical gate and taxonomy addresses that, noting its structural caveat that M/X classes are defined on GOES flux.

## Failure-criterion consequence (pre-registered)

Per the frozen contract, H0 implies the next decision is between accepting an all-flare deployment framing and detector retraining with a class-aware objective. **The all-flare branch is now closed by the secondary above** (recall 0.2802 under the all-flare label). The remaining pre-registered path is a class-aware retraining experiment — for which this experiment supplies the specific quantitative motivation (AUC 0.8745 of exploitable signal, saturating at 40.5% when applied post-hoc) and the specific target (the C/M boundary population).

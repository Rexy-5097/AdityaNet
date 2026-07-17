<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Operational Class Separation Experiment — frozen pre-registration; immutable once any observable is examined. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Operational Class Separation Experiment — FROZEN Pre-Registration

Immutable contract. Nothing may be added, removed, or reinterpreted after any observable is examined. The Sprint 33 frozen verdict (operational NO) and every Experiment A frozen result are fixed inputs this experiment cannot alter. No retraining. No GOES runtime inputs. No frozen artifact modified.

## Objective
Determine, using only frozen detector outputs and frozen Aditya-derived observables, whether a validation-selected episode-level class gate applied post-hoc to the frozen Sprint 33 nowcaster can suppress C-class responses sufficiently to meet the pre-registered deployment criterion (≤ 5.0 false episodes per month at ≥ 0.80 M/X episode recall) on the sealed Stage-2 test set.

## Scientific question (one only; no other question may be introduced during execution)
Can Aditya observables separate C-class responses from M/X responses sufficiently for operational deployment?

## Non-redundancy with completed work
Sprint 33 swept the detector's calibrated probability and measured that it cannot separate classes (14.27 false episodes per month at the 0.80 recall floor; `artifacts/sprint33_nowcast/Operating_Point_Analysis.md`). Experiment A measured that 94.22% of those false episodes are real C-class flares (`artifacts/expA_attribution/Attribution_Report.md`). This experiment uses *different information* — episode-peak intensity, hardness, and hard-X-ray observables — which no completed experiment has examined.

## Hypotheses (mutually exclusive, exhaustive; adjudicated on the sealed test set, majority of the five seeds)
Let *R* = the fractional reduction in false episodes per month achieved by the gate relative to the ungated Sprint 33 rate for the same seed, evaluated at the validation-selected gate while test M/X episode recall remains ≥ 0.80.
- **H0 (null; retained if no class-discriminative signal):** *R* < 50% — Aditya observables do not carry operationally meaningful class-discriminative signal; the C-class and M/X-class episode observable distributions overlap too much to gate.
- **H1 (sufficient separation):** the gated test false episodes per month ≤ 5.0 with test M/X episode recall ≥ 0.80, in ≥ 3 of 5 seeds.
- **H2 (partial separation):** *R* ≥ 50% but the gated result does not meet H1's conjunction — real but operationally insufficient class signal.
The three partition all outcomes by the frozen cut points (< 50% reduction; ≥ 50% but failing the criterion; meeting the criterion).

## Exact observables (nine candidates; every one justified; no observable outside this list may be examined)
All are frozen columns of `artifacts/research_v4/dataset_adi_nowcast/{validation,test}.parquet` (SHA-256 of test parquet pinned in the Experiment A pre-registration: `5f521283a62becee3d89e60f1010ed31ed4939b9f0ac10cfb1c4eb092866387a`). Each is aggregated per alert episode as the **episode-peak (maximum) value over the episode's window span**, because flare class is defined by *peak* soft-X-ray flux.

1. `log_solexs_soft` — flare class is *defined* as a peak soft-X-ray flux threshold (GOES C ≥ 10⁻⁶, M ≥ 10⁻⁵, X ≥ 10⁻⁴ W/m²); Experiment A established the detector fires on real C-class flares, so the open question is whether the Aditya-observed soft flux scales with the class boundary. Primary class variable.
2. `solexs_peak_30m` — rolling maximum of the soft-band aggregate; the direct episode-peak intensity proxy, same justification as (1).
3. `solexs_HR_high_low` — thermal-bremsstrahlung spectral hardening: larger flares reach higher plasma temperatures and harder spectra, so hardness is an intensity/class proxy independent of absolute calibration (relevant because no Aditya-to-GOES flux cross-calibration exists in this project).
4. `solexs_HR_mid_low` — same mechanism, mid band.
5. `solexs_HR_peak_60m` — impulsive-phase hardness memory; same mechanism, retains the episode's peak hardness.
6. `log_hel1os_band0` — nonthermal hard-X-ray emission scales with flare energy release (thick-target bremsstrahlung); M/X-class flares produce detectable hard X-rays while C-class flares frequently do not, making this a class discriminator orthogonal to soft flux.
7. `hel1os_fluence_30m` — Neupert effect: soft-X-ray rise tracks time-integrated hard-X-ray emission, so accumulated hard-X-ray fluence scales with flare magnitude.
8. `hel1os_fluence_60m` — same mechanism, longer integration.
9. `nonthermal_thermal_ratio` — the hard-to-soft ratio directly expresses the nonthermal fraction, which rises with flare class.

Additionally, **episode duration in minutes** (computed from the frozen episode structure, not a parquet column) is included as a tenth candidate: Experiment A measured C-overlap episodes at median 5 minutes and 90th percentile 42 minutes, and larger flares have longer rise phases — a completed-evidence temporal justification.

**Excluded, with reasons:** `solexs_dHR_15m` and `d_ntr_15m` (15-minute derivatives — rate-of-change, not peak intensity; Experiment A's finding concerns which *events* are detected, not their rate of change); `solexs_variance_15m` and `solexs_variance_60m` (intermittency — an activity texture, not a class quantity); `minutes_since_solexs_active` and `solexs_active_fraction_6h` (waiting-time and recency — flare-clustering statistics, carrying no per-episode intensity information). Detector calibrated probability is excluded because Sprint 33 already measured it is not class-discriminative.

## Feature-selection protocol (validation data only; immutable)
No subset selection is performed. All ten candidates enter a single L2-regularised logistic classifier ("M/X-overlap episode" versus "C-overlap episode") fit on **validation alert episodes only**, with features standardised using validation-only means and standard deviations. Fixing the feature set in advance and using L2 regularisation rather than data-driven subset selection eliminates a selection-flexibility pathway entirely. Episode class membership for fitting is assigned by the Experiment A taxonomy's strict-intersection rule against the frozen catalog (`artifacts/research/flares_full.parquet`, SHA-256 `536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a`), applied to validation episodes.

## Validation-only parameter selection (exhaustive list)
1. Feature standardisation means and standard deviations — computed on validation alert episodes only.
2. Logistic-regression coefficients and intercept — fit on validation alert episodes only, L2 penalty, inverse-regularisation strength C = 1.0 (frozen now; no tuning).
3. Gate threshold on the classifier's predicted M/X probability — selected on validation only as the **highest threshold retaining ≥ 0.90 validation M/X episode recall after gating**, mirroring the frozen Sprint 33 operating-point protocol.
4. The stage-one detector threshold — **not** re-selected; the frozen per-seed Sprint 33 values (0.030, 0.045, 0.100, 0.110, 0.060) are reused unchanged.

## Primary endpoint and minimum required effect
**Primary endpoint:** sealed-test false episodes per month at the two-stage (frozen detector threshold plus validation-selected class gate) operating point, subject to sealed-test M/X episode recall ≥ 0.80. **Minimum required effect for success: false episodes per month ≤ 5.0 with M/X episode recall ≥ 0.80, in at least 3 of 5 seeds.** The threshold is inherited unchanged from the Sprint 33 frozen contract, where it was justified from the operational requirement — anchored below the deployed GOES forecasting operating point of 3.16 false episodes per month recorded in `artifacts/GOES_Study_Final_Report.md` — and not from any expectation of this experiment's performance.

## Secondary endpoints (supporting only; cannot override the primary verdict)
Class-separation ROC-AUC of the validation-fit classifier measured on test episodes (the raw signal magnitude); per-observable coefficient magnitudes (which observable carries the separation); fractional false-episode reduction *R*; gated detection latency and time under alert; operating-point stability (absolute difference between validation and test M/X episode recall); and the **problem-statement label re-characterisation**: the frozen detector's per-class episode recall (M, X, C, B) and its false-episodes-per-month under alternative label definitions (M/X-only, ≥ M, ≥ C all-flare), computed on frozen episode streams. This secondary is reported prominently because the ISRO problem statement requests detection of "solar flares" without class restriction; a finding that the ungated detector satisfies the budget under an all-flare label is a first-class reported result but **cannot** override the primary M/X-selectivity verdict.

## Statistical tests
The deployment criterion is evaluated per seed and adjudicated by the frozen ≥ 3-of-5 majority rule. False episodes per month and M/X episode recall are reported with 95% confidence intervals from the moving-block bootstrap using the frozen harness parameters — block length 2,880 windows, 1,000 replicates, RNG seed 20260704 — imported unmodified from `scripts/sprint24/eval_framework.py`. **The block bootstrap explicitly accounts for episode-level autocorrelation**: stride-1 windows overlap 359 of 360 minutes and alert episodes are temporally contiguous, so independent resampling is invalid; the 2,880-window (two-day) block is eight times the 360-minute window span and preserves within-block dependence, and it is retained unchanged from Sprint 33 so results remain directly comparable to the ungated baseline. The class-separation ROC-AUC is reported with the same block bootstrap. No test assumes independence across episodes.

## Stopping rules
1. If no validation gate threshold retains ≥ 0.80 validation M/X episode recall, terminate; verdict H0 (the gate cannot preserve recall at all).
2. If reconstructed per-seed false-episode counts do not equal the frozen Experiment A values exactly (304, 237, 134, 165, 233), stop before any gating — this indicates a reconstruction defect, not a result.
3. If the validation classifier fails to converge, stop and report a technical failure; do not substitute another model family.
4. No parameter is adjusted in response to any result; no run is repeated because its result is disappointing.

## Compute estimate
No training occurs. Per seed: episode-peak observable aggregation over frozen alert streams, a logistic fit on validation episodes, gate-threshold selection, and one sealed test application — seconds each; the block bootstrap dominates at roughly a minute per seed. Full analysis including bootstrap across five seeds: **under 15 minutes**. Against the `artifacts/sprint26a/04_COMPUTE_REPORT.md` anchor of approximately 256 seconds per 5,000-step training epoch, this experiment costs less than a single training epoch — the cheapest experiment available.

## Failure criteria and what each implies
H0 (*R* < 50%): Aditya observables lack operationally meaningful class signal; the next experiment is a decision between accepting an all-flare deployment framing (if the label re-characterisation secondary supports it) and detector retraining with a class-aware objective. H2 (partial): the signal is real but insufficient post-hoc; the next experiment is retraining with a class-aware objective, now motivated by measured signal. H1 (success): a deployable M/X-selective Aditya-only nowcaster exists; the next steps are the GOES-17 control with the identical gate and operator packaging.

## Quality gates (execution order)
1. Provenance pre-check — Version 3 checkpoint, `artifacts/sprint14c/s2_test.parquet`, the Sprint-24 harness, the `v4-goes-final` tag, and the Experiment A catalog SHA-256 all byte-identical.
2. Count reconciliation — reconstructed per-seed false-episode counts equal 304/237/134/165/233 exactly.
3. Leakage check — standardisation, logistic coefficients, and gate threshold all fit on validation episodes only; test accessed once after all parameters are frozen.
4. Determinism — the analysis re-run reproduces identical primary endpoint, hypothesis verdict, and secondary endpoints.
5. Provenance post-check — all frozen artifacts byte-identical after execution.

## Scope boundaries (fixed now; nothing moves between categories after results)
`DIRECTLY OBSERVED`: whether Aditya observables carry class-discriminative signal (the test-measured class-separation ROC-AUC and the coefficient magnitudes); the gated false episodes per month and M/X episode recall per seed; the fractional reduction *R*; the per-class recall and alternative-label false rates.
`LOGICALLY IMPLIED`: that a post-hoc policy layer can exploit the signal without retraining — implied if H1 holds, because the gate *is* such a layer applied to frozen outputs, combined with the Sprint 33 completed result that the frozen detector achieves 0.9135 ± 0.0103 M/X episode recall; and that the operational gap is class discrimination rather than noise rejection — implied by Experiment A's completed 94.22% C-overlap and 1.86% genuine-false composition.
`STILL HYPOTHESIS`: that the signal is sufficient for *operational deployment* in the field beyond this sealed evaluation — H1 on the Stage-2 test span would be a pre-registered pass, not a deployment certification, and confirmation requires operator-facing validation on a subsequent span; that a retrained class-aware detector would outperform the gate — confirmation requires a separate pre-registered retraining experiment; that the finding generalises beyond the current evaluation period — the Stage-2 test span is a single ~6-month solar-maximum window, and the forecasting diagnostic established this regime is temporal-diversity-limited, so confirmation requires cycle-diverse data; and that the all-flare label re-characterisation constitutes problem-statement satisfaction — confirmation requires a separate pre-registered operational-framing decision. No `STILL HYPOTHESIS` conclusion may be presented as established without a follow-up pre-registered experiment.

## Final audit
1. **No post-hoc optimisation — CONFIRMED:** all ten observable candidates, the no-subset-selection protocol, the L2 penalty C = 1.0, the ≥ 0.90 validation-recall gate rule, the ≥ 0.80 recall floor, the ≤ 5.0 budget, the 50% reduction cut point, and the 3-of-5 majority are specified above; no observable distribution has been examined (only structural column existence was verified).
2. **No test leakage — CONFIRMED:** standardisation, logistic coefficients, and the gate threshold are fit on validation alert episodes only; class membership for fitting uses the catalog, not test outcomes.
3. **Single-test-touch preserved — CONFIRMED:** the test set is accessed once, after all parameters are frozen; the frozen detector probabilities are reused, not recomputed, so no model inference occurs.
4. **Frozen artifacts unchanged — CONFIRMED:** all inputs are read-only; outputs are written only under `artifacts/expC_class_separation/`.
5. **Provenance unchanged — CONFIRMED:** every input traces to a committed artifact — Sprint 33 outputs at `e7cad01`, Experiment A at `febe2af`, the catalog and test parquet pinned by SHA-256 above.
6. **Implementation complexity justified — CONFIRMED:** the experiment costs under 15 minutes, less than a single training epoch against the Sprint 26A anchor, and answers the deliverable's core open question with a conclusion-changing outcome in every branch.

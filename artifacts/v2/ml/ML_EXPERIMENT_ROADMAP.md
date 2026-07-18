<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone X experimental sequence. Simplest defensible baseline first. -->
<!-- DATE: 2026-07-18 -->

# ML Experiment Roadmap — `AdityaNet_v2_dataset_r1`

**Principle: the sequence is ordered by what each stage can *falsify*, not by model sophistication.** A stage exists only if its result could change what we do next. Where a simpler experiment is more convincing, it is scheduled earlier and the complex one is made conditional on it.

The governing constraint throughout: **581 independent M/X events**, not 564,160 minutes. Everything below is sized to that number.

---

## Stage 0 — Evaluation harness and splits *(before any model)*

**Why first.** Every result in this project will be interpreted through the harness. Building it after the first model invites tuning the harness to flatter the model. The frozen v1 harness (episode-level metrics, moving-block bootstrap, GAP/merge rules) already exists and is validated — it should be reused, not rewritten.

**Do.** Fix the chronological split — **train 2024Q1–2025Q4 (~423 M/X events), test 2026Q1–Q2 (~155 events)** — and freeze it before any model sees data. Define event-level metrics: episode recall, false episodes per unit time, detection latency, and a precision–recall frontier. Confidence intervals by **block bootstrap over events**.

**Exit.** Harness reproduces v1's known numbers on v1 inputs; split is committed and immutable.

## Stage 1 — Threshold baseline on a single column

**Why here.** Because it is already known to score **AUC 0.9536**. Any subsequent model that cannot beat a one-column threshold is not worth reporting, and knowing the threshold's operating curve is what makes later claims meaningful. This is the cheapest experiment in the entire programme and the most consequential for interpretation.

**Do.** Sweep a threshold on `rate_total` for M/X nowcast. Publish the full recall / false-alarm frontier and the operating point at fixed recall.

**Exit.** A published baseline frontier. **This becomes the number every later stage must beat.**

## Stage 2 — Persistence and climatology baselines for prediction

**Why here — and why before any forecasting model.** The measured prediction AUC is **horizon-flat**: 0.8119 at 30 min versus 0.7884 at 360 min, a 12× horizon change costing 0.024. That is the signature of activity-state persistence, not precursor information. If a forecasting model is trained before these baselines exist, its AUC of ~0.80 will be read as forecasting skill when most of it is persistence. **This stage exists to prevent a false claim, which makes it more valuable than any model.**

**Do.** Implement (a) persistence — current activity state predicts future state; (b) climatology — base rate by period; (c) the **skill-vs-horizon curve** from 30 min to 6 h for both.

**Exit.** A quantified persistence floor. All later forecasting results are reported as **improvement over persistence**, never as raw AUC.

## Stage 3 — Classical model on the recommended T1 feature set

**Why here.** ~15 features, 581 events. Gradient-boosted trees or regularised logistic regression are the right capacity for this ratio; they are interpretable, fast enough to bootstrap properly, and give feature attributions that inform Stage 4. Starting with deep learning at this sample size would confound "the architecture is wrong" with "the signal is absent."

**Do.** Fit on the Stage-0 split, evaluate at event level, compare against Stages 1–2. Report feature importances.

**Exit.** Either a measured improvement over the threshold with non-overlapping confidence intervals, or an honest null. **A null here is a publishable result**, not a failure — it would establish that M/X nowcasting from SoLEXS is threshold-limited.

## Stage 4 — Spectral ablation (T2)

**Why here, and conditional.** Band sums add **≤ 0.012 AUC** over the total rate, and hardness ratios *hurt* (−0.030 nowcast; **0.5075** — random — for 60-min prediction). The evidence says the spectrum is probably not the win v2 assumed. But "probably not, univariately" is not "no," and the 340-channel spectrum is the genuinely new capability of this dataset. It deserves one controlled test, not an act of faith.

**Do.** Repeat Stage 3 with T1 + coarse spectral bands, identical split and metrics. Report the delta with CIs.

**Exit.** A definitive answer to *does the spectrum add measurable predictive value at 1-minute resolution?* **Run this even if the expected answer is no** — a rigorous null closes the question and is a legitimate scientific contribution.

## Stage 5 — Combined-instrument ablation (SoLEXS vs SoLEXS+HEL1OS)

**Why here.** This answers the ISRO brief's actual question — does hard X-ray add information? — and it must come *after* the SoLEXS baseline exists, because the comparison is only meaningful against a known reference. The **171-day / 179-event** window makes it lower-powered than Stages 1–4, so it must be interpreted as an ablation, not as the headline benchmark.

**Do.** Restrict **both** arms to the identical 171 shared days. Compare SoLEXS-only against SoLEXS+HEL1OS. Any difference is then attributable to the instrument rather than to a different span.

**Exit.** A measured, honest answer to the brief's central question, with event counts and CIs stated.

## Stage 6 — Sequence model, strictly conditional

**Why last, and why gated.** With 581 events, a sequence model has ample capacity to memorise. It is justified **only if** Stage 3 shows that temporal-context features materially outperform instantaneous ones — i.e. only if there is evidence that temporal structure carries signal a tree cannot capture.

**Gate.** Proceed only if Stage 3's rolling-window features rank above instantaneous level in importance **and** improve on the Stage-1 threshold. Otherwise **stop** and report the classical result.

**Do (if gated open).** A small sequence model on T1 windows, same split, same event-level metrics, with the Stage-3 model as the mandatory baseline.

## Stage 7 — Operational characterisation

**Why here.** v1's most valuable finding was not a model score but the **attribution** of apparent false alarms to real C-class flares (94.2 %). Operational characterisation converts a benchmark number into an interpretable statement, and it requires a settled model to characterise.

**Do.** For the best model: false-alarm attribution against the catalogue, detection latency distribution, recall stratified by class (M vs X, with event counts always attached), and the full operating frontier.

**Exit.** A publishable operational profile: what the system detects, what it misses, what its alarms actually are.

---

## Sequence rationale

| Stage | Falsifies | Cost |
|---|---|---|
| 0 harness/splits | — (prevents post-hoc tuning) | low |
| 1 threshold | "ML is needed here" | very low |
| 2 persistence | "AUC 0.80 is forecasting skill" | low |
| 3 classical | "features beat a threshold" | low |
| 4 spectral ablation | "340 channels add value" | medium |
| 5 combined ablation | "HEL1OS adds value" | medium |
| 6 sequence model *(gated)* | "temporal structure needs deep learning" | high |
| 7 operational | "the benchmark number means something operationally" | low |

**Stages 1, 2, 4 and 5 are the scientifically decisive ones, and three of the four are cheap.** Stage 6 is the only expensive stage and it is explicitly gated — I recommend against running it unless Stage 3 opens the gate.

## What I recommend *against*

- **Starting with a deep sequence model.** 581 events; a null result would be uninterpretable (bad architecture, or no signal?).
- **Hyperparameter search before Stage 3 exists.** With this event count, extensive search on a fixed split *is* fitting the test set by proxy.
- **Any multi-model comparison before the persistence baseline (Stage 2).** Every number would be uninterpretable.
- **X-class-specific modelling.** 47 events; report as a stratified subgroup only.
- **Skipping Stage 4 because the answer looks predictable.** The measured null is the contribution.

## Pre-registration recommendation

Given this project's history — six contradictions found by execution, several from assumptions asserted before measurement — I recommend **pre-registering Stages 1–3 as a single frozen protocol** before any model is fit: split, metrics, baselines, and success criteria fixed in advance. The v1 pre-registration machinery already exists. The cost is a day; the alternative is a result that cannot be defended against the charge of post-hoc tuning.

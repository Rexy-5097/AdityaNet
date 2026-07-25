# Methodology

This document describes the scientific question, the dataset, and the evaluation protocol
behind AdityaNet's headline result. It is a summary; the authoritative, machine‑readable
record is the committed artifacts under `artifacts/v2/`, and the verbatim adjudicated
protocol is published at [`/findings/method`](https://adityanet-re1t.onrender.com/findings/method/).

## The instruments

Aditya‑L1 carries two soft X‑ray payloads whose flux tracks solar flare activity:

- **SoLEXS** — Solar Low Energy X‑ray Spectrometer.
- **HEL1OS** — High Energy L1 Orbiting X‑ray Spectrometer.

The count rate rises sharply during M‑ and X‑class flares, which makes it a natural signal
for both **nowcasting** (is a flare in progress?) and short‑horizon **prediction**.

## The dataset

`AdityaNet_v2_dataset_r1` (digest `43fd0e22…`) is derived from the SoLEXS and HEL1OS
Level‑1 products and frozen:

| Property | Value |
| --- | --- |
| Canonical tables | 7 |
| Files | 1,985 |
| Size | 569.3 MiB |
| Archive span | 2024‑02‑01 → 2026‑06‑17 (UTC) |
| Specification revision | r6 |
| Integrity | per‑table + dataset SHA‑256 digests |

Provenance — how raw products became these tables — is published on
[`/build/reproduce`](https://adityanet-re1t.onrender.com/build/reproduce/), and every
adjudicated deviation between implementation and specification is on
[`/validation`](https://adityanet-re1t.onrender.com/validation/).

## The research question

> Does machine learning provide **measurable operational value** beyond strong classical
> baselines, for M/X‑class flare **nowcast** and **30‑minute prediction**, on this dataset?

The word *operational* matters. The bar is not "can a model achieve a high score" — trivial
baselines already do, because flare activity is autocorrelated. The bar is "does a learned
model *separate* from a simple, deployable detector by a margin that survives its confidence
interval."

## Features

Derived per minute from the count‑rate series (14 features): the log rate, rolling means
(5 / 15 / 30 / 60 min), a rolling max and rolling standard deviations, a background‑excess
term, short rise measures, a good‑time‑interval fraction, seconds‑present, and a partial‑
coverage flag. The spectral‑band ablation adds SoLEXS band features on top of the count
rate.

## Evaluation protocol (frozen before any model was fit)

The protocol was pre‑registered — decided and committed before fitting — so it cannot be
tuned toward a favourable result:

| Choice | Value | Rationale |
| --- | --- | --- |
| Seed | `20260718` | Deterministic, published. |
| Test split | time‑ordered, from 2026‑01‑01 | No future information leaks into training. |
| Test size | 192,541 minutes; 581 M/X events | The held‑out horizon. |
| Uncertainty | day‑block bootstrap 95% CIs | Respects temporal correlation; per‑minute bootstrap would understate it. |
| Baselines | Random, Majority, Climatology, Persistence, Threshold | Trivial + one deployable simple detector. |
| Models | Logistic regression, Random forest, LightGBM | Standard learned comparators. |

**Why day‑block bootstrap.** Minutes within a day are highly correlated (a flare spans many
consecutive minutes). Resampling individual minutes would treat them as independent and
produce artificially tight intervals — making models look more distinguishable than they
are. Resampling whole days preserves the correlation structure and yields honest CIs.

## The result

For the M/X nowcast task (ROC‑AUC, held‑out test):

| Model | ROC‑AUC | 95% CI |
| --- | --- | --- |
| Threshold (count rate) | 0.954 | 0.940 – 0.966 |
| Logistic regression | 0.964 | 0.953 – 0.974 |
| LightGBM | 0.961 | 0.949 – 0.972 |
| Random forest | 0.966 | 0.956 – 0.976 |
| Persistence (trivial) | 0.982 | 0.978 – 0.986 |

**Reading it correctly.** The best learned model's interval (random forest, 0.956–0.976)
overlaps the threshold's (0.940–0.966). They are **not statistically distinguishable**, so
the verdict is *no operational gain*, not a ranking. And the highest scorer of all is a
*trivial* baseline (Persistence), which tells you the nowcast task is dominated by
short‑timescale autocorrelation rather than by anything learned.

**Spectral ablation (confirmed null).** Adding spectral‑band features moves ROC‑AUC from
0.9605 to 0.9638 — a delta of +0.0033, within noise.

## Scope and limitations

- The result is **specific to the evaluated tasks and this frozen dataset**. It is not a
  claim about solar‑flare physics, nor about machine learning in general.
- "No operational gain" is a statement about *distinguishability under the pre‑registered
  protocol*, not proof that no model could ever help with more data or different framing.
- Trivial baselines scoring highly is itself a finding: it characterises the task, and it is
  why a naive "our model gets 0.97 AUC" claim would be misleading.

## Why publish a negative result

The incentive gradient in ML pushes toward reporting the model that "wins." AdityaNet's
credibility rests on doing the opposite where the evidence demands it: pre‑registering the
protocol, comparing against baselines that can embarrass the models, and publishing the
outcome at full weight with its uncertainty intact. That is the methodology the platform is
built to demonstrate.

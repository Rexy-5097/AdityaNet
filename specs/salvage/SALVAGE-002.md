---
id: SALVAGE-002
title: The v4 feature framework — design knowledge, and the gate it was missing
status: active
supersedes: []
superseded_by: null
origin: salvaged
source_tag: v1-surya-final
source_paths: research/app/services/ml/features_v4/framework.py
source_loc: 95
---

# SALVAGE-002 — The v4 feature framework

> **Provenance.** Design knowledge extracted from the v1 generation before its removal by
> M1/E2/#9. The implementation is recoverable at tag `v1-surya-final`:
>
> ```
> git show v1-surya-final:research/app/services/ml/features_v4/framework.py
> ```
>
> **This document contains no code and mandates nothing.** Binding decisions live in `adr/`.

## Why this one matters most

This is the framework that produced the v1 disaster, and reading it is uncomfortable in a
specific and instructive way: **it was well designed, and it recorded the exact fact that
would have prevented the failure.** It just never compared that fact against anything.

`NonthermalThermalRatio` declared `instrument = "hel1os+goes"` and declared GOES long flux
among its required columns. The framework dutifully wrote both into the provenance manifest
for every run. The feature then entered a set described throughout the project as
"Aditya-only", correlating −0.9151 with the label-generating flux, and no code anywhere
asked whether a feature requiring GOES belonged in an Aditya-only set.

**The metadata was correct. The gate did not exist.** That is the whole lesson, and it is
why [ADR-0011](../../adr/ADR-0011.md) exists.

## Design decisions that were right

**Features are stateless by construction, not by convention.** The framework rejected any
feature exposing a fitting method. Fitted transforms — scaling was the only one — lived in a
separate layer entirely. This makes train/test contamination through a feature structurally
impossible rather than a thing reviewers must watch for.

**Declared requirements, and computation restricted to them.** A feature declared the
columns it needed, and `compute` received a view containing *only* those columns. A feature
could not quietly read a column it had not declared, so the declaration was load-bearing
rather than documentary. This is the mechanism [ADR-0011](../../adr/ADR-0011.md) reuses; the
missing half was comparing the declaration against a permitted set.

**Label columns forbidden in requirements.** A feature declaring a label column was rejected
outright. Leakage through the most obvious channel was closed at the framework rather than
left to review.

**The input frame is never modified.** Computation worked on a copy. A feature could not
perturb the frame a later feature would see, so feature order could not silently change
results.

**Provenance included a digest of the compute source.** Per feature, the manifest recorded
instrument, required columns, parameters, **and a SHA-256 of the computation's own source
text**. Changing a feature's logic changed its provenance even when its name and parameters
did not. [ADR-0010](../../adr/ADR-0010.md) requires the same property of a MethodRelease.

**Processing order stated as a contract.** Physical-domain feature engineering happens
before scaling, and scaling never happens inside a feature. Order was written down as a
rule rather than left implicit in call sites.

## The failure, stated precisely

Every property above is a *local* guarantee: this feature is stateless, this feature reads
only what it declared, this feature's source is hashed. None of them is a *global* one. No
component held the claim "this feature set uses only these instruments" and checked it.

A declaration that nothing reads is decoration. The v1 framework proves the point at full
scale: it had complete, accurate, machine-readable instrument metadata for every feature,
and it shipped a GOES detector labelled Aditya-only for months.

## What the frozen architecture does differently

| v1 | Frozen architecture |
|---|---|
| Feature declares `instrument`; manifest records it | MethodRelease declares instruments; **Protocol declares permitted instruments; the engine refuses to score on mismatch** ([ADR-0011](../../adr/ADR-0011.md)) |
| Leakage closed for label columns only | Leakage gate over bitemporal availability ([ADR-0022](../../adr/ADR-0022.md)), plus the instrument gate |
| Source digest per feature | Content addressing for every immutable object ([ADR-0005](../../adr/ADR-0005.md)) |
| Framework is a library callers may bypass | Methods invoked through a serialised wire format ([ADR-0016](../../adr/ADR-0016.md)) |

The regression test for [ADR-0011](../../adr/ADR-0011.md) reproduces this exact failure: a
method declaring a GOES input is rejected by an Aditya-only protocol. It is a required CI
check specifically so this cannot recur.

## What must not be carried forward

The feature definitions themselves. They were computed over simulated Aditya data
([L-01](../limitations/L-01.md) … [L-10](../limitations/L-10.md) describe the real corpus's
constraints, which differ). The framework's *discipline* transfers; its features do not.

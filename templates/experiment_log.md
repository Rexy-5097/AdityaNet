---
id: ART-EXP-NNNN
title: "[Experiment Name]"
version: 1.0
status: draft
owner: science-reviewer
created: YYYY-MM-DD
modified: YYYY-MM-DD
related_adr: None
related_standard: standards/research.md
related_checklist: QG-004
related_workflow: research.md
related_agent: science-reviewer
---

# Experiment Log: [ID]

## Hypothesis

State the concrete, measurable hypothesis before running the experiment.

## Dataset Provenance

- **Source:** [URL or directory path]
- **Version/Hash:** [SHA-256 hash of dataset]
- **Held-out Split:** [Verified split method - 0% leakage]

## Methodology

Outline the step-by-step procedure used to train or evaluate the model.

## Statistical Results

| Metric | Baseline Score | Model Score | p-value | Effect Size (d) | Status |
|--------|----------------|-------------|---------|-----------------|--------|
| [e.g., F1] | [Value] | [Value] | [Value] | [Value] | [PASS/FAIL] |

## Reproducibility Verification

- **Docker/Env Lock:** [Verified in isolated container - YES/NO]
- **Correlation score:** $r = $ [Value]
- **Variance range:** $\pm$ [Value]

## Conclusion & Next Actions

What did the results reveal? Should we deploy this model or discard the experiment?

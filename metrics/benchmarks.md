# Metrics: Benchmarks

> **Owner:** ML Lead / Research Lead | **Consumers:** `ai-reviewer` · `science-reviewer`
> **Update Frequency:** Per training run · Per model release · Milestone evaluation
> **Max Size:** ~900 tokens | **Cross-refs:** `standards/ai_ml.md` · `standards/research.md` · `metrics/quality.md`

---

## Purpose

Define structural benchmarks for validation of AI models and scientific research findings. This file establishes targets for model performance, statistical validity, and reproducibility.

---

## AI/ML Model Benchmarks

| Metric | Definition | Target | Acceptable Range | Measurement Method | Frequency | Responsible |
|--------|-----------|--------|------------------|-------------------|-----------|-------------|
| **Accuracy** | Overall correct rate | > 95% | > 90% | Evaluated on test dataset | Per training | `ai-reviewer` |
| **Precision** | True Pos / (True Pos + False Pos) | > 93% | > 88% | Evaluated on test dataset | Per training | `ai-reviewer` |
| **Recall** | True Pos / (True Pos + False Neg) | > 93% | > 88% | Evaluated on test dataset | Per training | `ai-reviewer` |
| **F1 Score** | Harmonic mean of precision/recall | > 93% | > 88% | Computed from Prec/Recall | Per training | `ai-reviewer` |
| **ROC-AUC** | Area under receiver operating curve | > 0.97 | > 0.93 | Computed over class probs | Milestone | `ai-reviewer` |
| **Log Loss** | Cross-entropy loss | < 0.15 | < 0.25 | Computed over predictions | Per training | `ai-reviewer` |
| **Calibration** | Expected Calibration Error (ECE) | < 0.05 | < 0.10 | Reliability diagram computation | Per release | `ai-reviewer` |

---

## LLM / Generative Model Benchmarks

> Complete if the project implements LLMs, Agents, or RAG components.

| Benchmark | Focus Area | Target | Acceptable Range | Measurement Tool | Frequency |
|-----------|------------|--------|------------------|------------------|-----------|
| **MMLU** | General knowledge | > 80% | > 75% | `lm-eval-harness` | Per model release |
| **GSM8k** | Mathematical reasoning | > 85% | > 78% | `lm-eval-harness` | Per model release |
| **RAG Faithfulness**| Context utilization (no hallucination) | > 95% | > 90% | Ragas / TruLens evaluation | Per release / weekly |
| **RAG Answer Relevancy**| Answer relevance to prompt | > 90% | > 85% | Ragas / TruLens | Per release / weekly |
| **BLEU / ROUGE** | Text generation overlap | BLEU > 40 | BLEU > 30 | NLTK / rouge-score | Per model release |
| **Agent Task Success**| Completed multi-step agent actions | > 90% | > 80% | Custom agent harness run | Pre-release |

---

## Scientific & Research Benchmarks

| Metric | Definition | Target | Acceptable Range | Measurement Method | Frequency |
|--------|-----------|--------|------------------|-------------------|-----------|
| **P-Value Threshold**| Probability of observing extreme results | ≤ 0.01 | ≤ 0.05 | Statistical tests (t-test, ANOVA) | Per experiment |
| **Statistical Power**| Probability of correctly rejecting null | ≥ 0.90 | ≥ 0.80 | Power analysis computation | Pre-experiment |
| **Effect Size (Cohen's d)**| Standardized difference in means | > 0.8 (Large) | > 0.5 (Medium) | Computed from sample variance | Per experiment |
| **Variance Explained ($R^2$)**| Proportion of variance explained by model | > 0.85 | > 0.70 | Regression analysis evaluation | Per experiment |
| **CI Coverage** | Percent of parameter inside CI | 95% | 95% | Bootstrapping / parametric calculation | Per experiment |

---

## Reproducibility Metrics

| Metric | Definition | Target | Acceptable Range | Validation Method |
|--------|-----------|--------|------------------|-------------------|
| **Clean-Room Run** | Execution in isolated container succeeds | 100% | 100% | Docker execution test in CI |
| **Result Correlation** | Correlation of original vs reproduced results | $r \ge 0.99$ | $r \ge 0.95$ | Pearson correlation on output vectors |
| **Metric Divergence** | Max change in key metric on reproduction | < 1% | < 3% | Absolute difference computation |
| **Data Provenance** | Percentage of datasets with recorded hash | 100% | 100% | Checksum verification scan |

---

## Baseline and Project Customization

When configuring a new project, copy this table to document your baseline models or scientific benchmarks:

| Benchmark Name | Baseline Score | Project Target | Validation Dataset | Date Updated |
|----------------|----------------|----------------|--------------------|--------------|
| [e.g., Accuracy] | [e.g., 78.4%] | [e.g., 90.0%] | [e.g., val_v1_split] | [YYYY-MM-DD] |
| | | | | |

---

*Benchmark targets must be validated against held-out datasets. Self-evaluation on training data is invalid.*

# Standard: Research

> **Tier:** Domain — applies to scientific and research projects
> **Owner:** Research Lead | **Reviewer:** `science-reviewer`
> **Consumers:** `science-reviewer` · `ai-reviewer` (joint AI/ML research tasks) | **Max:** ~1400 tokens
> **Cross-refs:** `standards/documentation.md` · `standards/testing.md` · `standards/ai_ml.md` · `metrics/benchmarks.md` · `checklists/research_validation.md`

---

## Purpose

Ensure that scientific work produces findings that are honest, reproducible, statistically valid, and useful to future researchers — including future AI agents reading the experiment logs.

## Scope

**Governs:** Experiment design, hypothesis formulation, data collection, statistical analysis, results reporting, reproducibility.
**Does NOT govern:** ML model training specifics (→ `standards/ai_ml.md`), data pipeline engineering (→ `standards/data_engineering.md`), documentation format (→ `standards/documentation.md`).

---

## Guiding Principles

1. **Hypothesis before experiment.** Formulate and log the expected outcome before collecting data.
2. **Pre-registration where consequential.** For results that will influence major decisions, document methodology before running.
3. **Negative results are results.** A well-run experiment that disproves a hypothesis is as valuable as one that confirms it.
4. **Show your work.** Methodology must be complete enough for independent reproduction.
5. **Statistical significance is not practical significance.** Report effect sizes, not just p-values.
6. **Beware multiple comparisons.** Testing many hypotheses without correction inflates false positives.
7. **Uncertainty is information.** Report confidence intervals; never hide variance.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Hypothesis logging | Before analysis begins | Before data collection | Logged in `context/memory.md` | Pre-registered externally |
| Methodology documentation | Notes exist | Reproducible by team | Reproducible by external researcher | Independent reproduction verified |
| Statistical testing | Basic metrics reported | Significance tests used | Effect sizes + confidence intervals | Power analysis + multiple comparison correction |
| Baseline comparison | None required | Compared to naive baseline | Compared to prior art | Compared to SOTA benchmarks |
| Negative results | Discarded | Noted privately | Logged in experiment log | Published or shared |
| Data documentation | Dataset name noted | Source + version logged | Full data card documented | Open dataset with DOI |
| Reproducibility | Team can reproduce | Environment logged | Clean-room reproduction tested | Third-party reproduction |
| Peer review | None | Internal review | External collaborator review | Formal peer review |

---

## Experiment Lifecycle

| Phase | Action | Output | Logged Where |
|-------|--------|--------|-------------|
| Ideation | Document hypothesis | Hypothesis statement | `context/memory.md` |
| Design | Define methodology, metrics, baselines | Experiment design | `templates/experiment_log.md` |
| Data | Validate and document dataset | Data quality report | Experiment log |
| Execution | Run experiment; log everything | Raw results | Experiment log |
| Analysis | Apply statistical tests; compute effect sizes | Analysis report | Experiment log |
| Review | `science-reviewer` validates methodology + stats | Review finding | Linked from experiment log |
| Conclusion | Document findings including negatives | Conclusion + next steps | Experiment log; update `context/memory.md` |
| Archive | Move to `artifacts/experiments/` | Archived experiment | `artifacts/experiments/EXP-*.md` |

---

## Statistical Requirements

| Metric | When Required | Notes |
|--------|-------------|-------|
| p-value | When claiming significance | Report exact value, not just < 0.05 |
| Effect size (Cohen's d, η², etc.) | Whenever p-value is used | Effect size + CI required alongside p-value |
| Confidence intervals | Recommended at all levels | 95% CI minimum |
| Power analysis | Production Grade + | Before data collection; prevents underpowered studies |
| Multiple comparison correction | When testing > 1 hypothesis | Bonferroni, Benjamini-Hochberg, or equivalent |

---

## Best Practices

- **Log the experiment before you know the results.** Pre-logging prevents unconscious HARKing (Hypothesizing After Results are Known).
- **Use a held-out test set.** Never evaluate on data used to tune the methodology.
- **Report variance.** Mean ± standard deviation for all key metrics; not just the mean.
- **Compare to baselines.** A result without a baseline is an assertion, not a finding.
- **Document what failed.** Failed experiments prevent teammates from repeating them.
- **Environment is part of the result.** Log framework versions, hardware, OS, and random seeds.
- **Keep raw data.** Never overwrite raw output; re-derive processed data from raw.
- **Distinguish exploratory from confirmatory.** Exploratory analysis generates hypotheses; confirmatory tests them.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| HARKing (Hypothesizing After Results are Known) | Appears to confirm hypothesis that was actually discovered |
| p-value hacking (running until p < 0.05) | Inflated false positive rate; results don't replicate |
| Reporting only positive results | Biases the literature; wastes others' time repeating failures |
| No baseline comparison | Impossible to assess whether result is meaningful |
| Overfit conclusion to one dataset | Generalizes poorly; misleads future work |
| Discarding "failed" experiments | Loses institutional knowledge; team repeats the same failures |
| Missing environment documentation | Results irreproducible even by original researcher |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Irreproducible results | Environment undocumented; seeds missing | Reproduction attempt by another researcher | Audit and fix logging; consider retraction |
| Data leakage into results | Evaluation data used in methodology design | Methodology review before execution | Re-design and re-run with clean split |
| Underpowered study | No power analysis; too little data | Effect size small; CI wide | Collect more data; report the limitation |
| False positives (multiple comparisons) | Testing many hypotheses with one threshold | Review of statistical methodology | Apply correction; re-analyze |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | Experiment log exists · Results recorded · Dataset identified |
| Recommended | + Hypothesis logged before analysis · Baseline compared · Significance tests applied |
| Production | + Effect sizes + CIs reported · Environment documented · Internal review passed · Negatives logged |
| Flagship | + Power analysis run · Multiple comparison correction applied · External validation · Open dataset |

---

## Reviewer Questions

```
RESEARCH REVIEW CHECKLIST
□ Was the hypothesis documented before the experiment was run?
□ Is the methodology fully documented for independent reproduction?
□ Is evaluation performed on data not used in methodology design?
□ Are effect sizes and confidence intervals reported alongside p-values?
□ Has multiple comparison correction been applied if testing > 1 hypothesis?
□ Is there a baseline comparison (naive or prior art)?
□ Are negative and null results logged, not discarded?
□ Is the environment (versions, seeds, hardware) fully documented?
□ Does the experiment log capture variance, not just the mean result?
□ Has science-reviewer validated the statistical methodology?
```

---

## Completion Criteria

- [ ] Experiment log complete and archived in `artifacts/experiments/`
- [ ] Hypothesis was logged before execution (verified by log timestamp)
- [ ] Acceptance criteria for the project's quality level are met
- [ ] `science-reviewer` has reviewed and approved
- [ ] `context/memory.md` updated with discoveries

---

## Cross-references

| Topic | Standard |
|-------|---------|
| ML experiment specifics | `standards/ai_ml.md` |
| Data collection and validation | `standards/data_engineering.md` |
| Experiment log format | `templates/experiment_log.md` |
| Benchmark targets | `metrics/benchmarks.md` |
| Validation checklist | `checklists/research_validation.md` |

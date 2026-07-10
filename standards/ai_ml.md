# Standard: AI/ML Systems

> **Tier:** Domain — applies to AI/ML projects
> **Owner:** ML Lead / Chief Architect | **Reviewer:** `ai-reviewer`
> **Consumers:** `ai-reviewer` · `science-reviewer` (joint tasks) | **Max:** ~1500 tokens
> **Cross-refs:** `standards/testing.md` · `standards/research.md` · `standards/data_engineering.md` · `standards/security.md` · `metrics/benchmarks.md`

---

## Purpose

Ensure AI/ML systems are reproducible, measurable, safe to deploy, and honest about their capabilities and limitations. Prevent the three endemic failures of ML engineering: unreproducible experiments, silent model degradation, and overconfident deployment.

## Scope

**Governs:** Model training, evaluation, validation, deployment, inference systems, experiment tracking, model versioning.
**Does NOT govern:** Training data pipelines (→ `standards/data_engineering.md`), statistical methodology (→ `standards/research.md`), API serving design (→ `standards/api_design.md`).

---

## Guiding Principles

1. **Reproducibility by design.** A training run that cannot be reproduced is not an engineering asset — it is a liability.
2. **Validate data before training.** Bad data produces bad models; data quality gates precede training gates.
3. **Measure everything.** If you cannot measure model behavior, you cannot know when it degrades.
4. **Separate evaluation from training data.** A held-out test set is not optional; it is the definition of honest evaluation.
5. **Models fail silently in production.** Performance monitoring is as important as training performance.
6. **Explain what the model cannot do.** Known limitations are engineering requirements, not embarrassments.
7. **Deployment is a decision, not an endpoint.** Serving a model requires documented approval criteria.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Experiment tracking | Manual notes | MLflow / W&B logged | Full hyperparameter log + artifacts | Reproducibility verified by CI |
| Train/val/test split | Fixed split used | Stratified split documented | Split justification documented | + Distribution shift analysis |
| Evaluation metrics | Accuracy logged | Precision + Recall + F1 | Full benchmark suite | + Uncertainty quantification |
| Reproducibility | Not required | Seeds set; env logged | Environment pinned; run script exists | Third-party reproduction |
| Bias testing | None | Protected attributes checked | Bias metrics in CI | Formal bias audit |
| Model card | None | Brief description | Full model card published | Peer-reviewed model card |
| Monitoring | None | Manual checks | Automated drift detection | Real-time alerting + auto-rollback |
| Deployment gate | Manual decision | Review checklist | Formal approval + rollback plan | Staged rollout + canary |

---

## Experiment Protocol

| Step | Requirement | Output |
|------|-----------|--------|
| Hypothesis | Document expected outcome before running | `context/memory.md` (active experiments) |
| Data validation | Validate dataset quality before training | Data quality report |
| Training | Reproducible with fixed seed and pinned environment | Experiment log in `artifacts/experiments/` |
| Evaluation | Measured on held-out test set | Evaluation report with confidence intervals |
| Comparison | Compared to baseline; improvement quantified | Comparison table |
| Review | `science-reviewer` validates methodology | Review finding |
| Decision | Deploy / iterate / discard — documented | Decision logged in `context/state.md` |

---

## Best Practices

- **Fix random seeds.** Every training run sets seeds for Python, NumPy, and the framework.
- **Pin the environment.** `requirements.txt` or `pyproject.toml` with exact versions; reproduce in a clean env.
- **Evaluate on held-out data only.** Never optimize hyperparameters on the test set — use a validation set.
- **Log to experiment tracker before, during, and after training.** Not after results are known.
- **Version models alongside code.** A model artifact without its training code version is untrustworthy.
- **Document known failure modes.** Every deployed model must have a documented list of inputs it handles poorly.
- **Monitor production inference.** Distribution drift, latency degradation, and error rates require active monitoring.
- **Calibrate confidence.** A model that is 90% confident should be right ~90% of the time. Test calibration.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Training on the test set | Optimistic metrics hide real generalization failure |
| No experiment tracking | Results cannot be compared; work cannot be reproduced |
| Serving a model without a rollback plan | Degraded production performance with no recovery path |
| Treating accuracy as the only metric | Precision/recall imbalances cause real-world harm |
| Not validating training data | Garbage in, garbage out — at scale |
| Deploying without monitoring | Silent performance degradation goes undetected |
| Hyperparameter search on test data | Overfitting disguised as model improvement |
| Missing model card | Downstream users don't know what the model cannot do |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Irreproducible results | Seeds not set; env not pinned | Reproducibility CI check | Audit and fix training script; pin env |
| Data leakage | Test data used during feature engineering | Pipeline audit; metric suspiciously high | Re-split data; retrain |
| Silent production degradation | No monitoring; distribution shift | Add drift detection alerting | Rollback model; investigate data shift |
| Metric gaming | Single metric optimized while others degrade | Full evaluation suite | Add multi-metric evaluation gate |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | Model trains without error · Basic metrics logged · Train/val/test split used |
| Recommended | + Reproducible with seed + env · Experiment tracked · Precision + Recall + F1 logged |
| Production | + Full benchmark suite · Bias metrics checked · Model card published · Monitoring deployed |
| Flagship | + Third-party reproducibility · Formal bias audit · Uncertainty quantification · Staged deployment |

---

## Reviewer Questions

```
AI/ML REVIEW CHECKLIST
□ Is the experiment fully logged (hyperparameters, metrics, artifacts)?
□ Are random seeds fixed in the training script?
□ Is the environment pinned and reproducible?
□ Is evaluation performed on a held-out test set (not validation set)?
□ Are precision, recall, and F1 reported alongside accuracy?
□ Is training data validated for quality before training begins?
□ Is there a model card documenting capabilities and limitations?
□ Is there a production monitoring plan or deployed monitoring?
□ Is there a documented rollback plan if the deployed model degrades?
□ Have protected attribute / bias metrics been checked?
```

---

## Completion Criteria

- [ ] Experiment log exists in `artifacts/experiments/`
- [ ] Training is reproducible with documented instructions
- [ ] Evaluation metrics meet targets in `metrics/benchmarks.md`
- [ ] Acceptance criteria for the project's quality level are met
- [ ] `ai-reviewer` has reviewed and approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Data pipeline quality | `standards/data_engineering.md` |
| Statistical validity | `standards/research.md` |
| Test suite requirements | `standards/testing.md` |
| Model serving security | `standards/security.md` |
| Benchmark targets | `metrics/benchmarks.md` |

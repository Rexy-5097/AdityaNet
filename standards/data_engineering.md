# Standard: Data Engineering

> **Tier:** Component — applies to data pipelines, ETL/ELT, and storage systems
> **Owner:** Data Lead / Tech Lead | **Reviewer:** `ai-reviewer` or `science-reviewer`
> **Consumers:** `ai-reviewer` · `science-reviewer` | **Max:** ~1400 tokens
> **Cross-refs:** `standards/security.md` · `standards/testing.md` · `standards/code_quality.md` · `standards/ai_ml.md`

---

## Purpose

Ensure that data pipelines are reliable, reproducible, observable, and safe — that data flowing through the system is trustworthy, and that failures are detected before they corrupt downstream consumers.

## Scope

**Governs:** ETL/ELT pipelines, data validation, schema management, data lineage, storage design, batch and streaming pipelines.
**Does NOT govern:** ML model training (→ `standards/ai_ml.md`), database security (→ `standards/security.md`), API data contracts (→ `standards/api_design.md`).

---

## Guiding Principles

1. **Data quality is a first-class concern.** Bad data corrupts every downstream consumer silently.
2. **Validate at every boundary.** Data entering the system must be validated before it proceeds.
3. **Make pipelines idempotent.** Re-running a pipeline must produce the same output — never duplicate or corrupt.
4. **Assume data will be wrong.** Design validation before transformation; don't assume schema compliance.
5. **Lineage is an audit trail.** Every piece of data must have a traceable origin.
6. **Fail early, loudly.** A pipeline that fails in the first stage is cheaper than one that silently corrupts at the last stage.
7. **Schema is a contract.** Changes to schema require versioning and consumer notification.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Schema validation | None | Input schema validated | Schema validation at every stage | + Schema evolution tracked |
| Idempotency | Best-effort | Key deduplication | Fully idempotent pipeline | + Exactly-once delivery |
| Data quality checks | None | Null/type checks | Completeness + range + uniqueness | + Distribution monitoring |
| Lineage tracking | None | Source documented | Lineage tracked per record | Formal lineage graph |
| Error handling | Crash on failure | Errors logged | Dead letter queue + alerts | + Automatic retry with backoff + SLA |
| Monitoring | None | Manual checks | SLA monitoring + alerting | Real-time dashboards + anomaly detection |
| Testing | None | Pipeline runs without errors | Input/output unit tested | Contract tests + data quality regression |
| Data documentation | None | Dataset name + source | Full data card | + Data dictionary + provenance |

---

## Data Quality Dimensions

| Dimension | Definition | Minimum Check | Production Check |
|-----------|-----------|--------------|-----------------|
| Completeness | No unexpected nulls | Null count | Per-column null budget |
| Accuracy | Values are correct | Type validation | Range checks + reference data |
| Consistency | No contradictions | Cross-column checks | Cross-table consistency |
| Uniqueness | No unexpected duplicates | Primary key check | Deduplication audit |
| Timeliness | Data arrives when expected | Ingestion timestamp | SLA monitoring |
| Validity | Conforms to schema | Schema validation | Regex + format + enum checks |

---

## Best Practices

- **Schema-first design.** Define the expected schema before writing the pipeline.
- **Log every transformation.** Record what changed, when, and from what input version.
- **Never mutate raw data.** Raw data is immutable; derived tables are re-derivable.
- **Test with adversarial inputs.** Include malformed, missing, and out-of-range values in test data.
- **Separate ingestion from transformation.** Land raw data first; transform in a separate step.
- **Set SLAs explicitly.** Every pipeline has a documented freshness SLA.
- **Dead letter queue for failures.** Failed records go to a quarantine queue, never silently dropped.
- **Monitor data drift.** When the distribution of production data shifts from training data, model behavior changes.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| Mutable raw data store | Cannot audit or reprocess; corrupts all derived data |
| Pipelines without validation | Bad data silently propagates to all consumers |
| Silent failure on partial load | Consumers receive incomplete data without knowing |
| No deduplication | Double-counting corrupts downstream analytics and models |
| Schema changes without versioning | Breaks all consumers without warning |
| Pipeline testing with only valid data | Hides failure modes that appear in production |
| Missing lineage | Cannot trace a bad value back to its source |
| Hardcoded connection strings | Security violation (→ `standards/security.md`) |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Silent data corruption | Validation removed for performance | Data quality monitoring | Halt pipeline; audit from last known-good state |
| Schema drift | Upstream source changes schema without notice | Schema validation failure | Version the schema; add schema change alerting |
| Pipeline idempotency failure | Re-run creates duplicates | Data quality: uniqueness check | Implement key-based deduplication; add idempotency test |
| Stale data serving | Pipeline SLA missed silently | Freshness monitoring alert | Add freshness gate before serving to consumers |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | Pipeline runs without error · Data lands in expected location · Basic error logging |
| Recommended | + Schema validated at input · Idempotent re-runs · Null checks · Dataset documented |
| Production | + Full data quality suite · Lineage tracked · Dead letter queue · SLA monitoring |
| Flagship | + Exactly-once delivery · Formal lineage graph · Distribution monitoring · Compliance audit |

---

## Reviewer Questions

```
DATA ENGINEERING REVIEW CHECKLIST
□ Is input data validated against a schema before any transformation?
□ Is the pipeline idempotent — does re-running it produce identical output?
□ Are data quality checks run on output (completeness, uniqueness, range)?
□ Is raw data immutable — never overwritten or modified?
□ Are all pipeline failures logged and routed to a dead letter queue?
□ Is data lineage tracked from source to output?
□ Are there any hardcoded connection strings or credentials?
□ Is there a documented freshness SLA for each pipeline output?
□ Are schema changes versioned and communicated to consumers?
□ Is the pipeline tested with adversarial and malformed inputs?
```

---

## Completion Criteria

- [ ] Schema validation is implemented at pipeline input
- [ ] Pipeline has been verified to be idempotent
- [ ] Acceptance criteria for the project's quality level are met
- [ ] Data quality checks pass on the output
- [ ] Security review complete for credentials and data handling
- [ ] Reviewer has approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Credentials and data security | `standards/security.md` |
| Pipeline code quality | `standards/code_quality.md` |
| Test data design | `standards/testing.md` |
| Training data for ML | `standards/ai_ml.md` |

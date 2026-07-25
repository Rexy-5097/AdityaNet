# Release Candidate 1 (RC1) Validation Benchmarks

> **Layer:** Verification | **Status:** Active
> **Purpose:** Documenting developer productivity metrics and audit logs for AgentOS RC1.
> **Cross-refs:** `production_validation/rc1_validation_report.md` · `production_validation/productivity_metrics.csv`

---

## 1. Subsystem Audit Rules

This layer tracks actual productivity metrics recorded across our controlled representative benchmark tasks:
- **Project A (Backend Task):** Bootstrap verification, JWT implementation metrics, and API endpoint additions.
- **Project B (AI/Research Task):** ML model training pipeline reviews and scientific data assertions.

---

## 2. Validation Execution Command

To execute the static validator checklist for RC1 verification, run:
```bash
python3 tools/scripts/validate_agentos.py
```

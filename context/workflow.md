<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Living context document; pre-Sprint-23 statements presenting thresholds 0.46/0.88 as production were stale and are corrected inline below with [SUPERSEDED — Sprint 23] markers; original text preserved. -->
<!-- SUPERSEDED BY: Sprint 23 (artifacts/policies/operator_policy_v2.json); proof: artifacts/sprint22_5/FINAL_VERDICT.md; clean baseline: artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md -->
<!-- DATE: 2026-07-03 -->

# Project Workflow — SuryaNet / AdityaNet

> **Adapted from:** `workflows/master.md` for the `adityanet` profile
> **Profile:** adityanet (flagship + space-weather domain)
> **Cross-refs:** `context/state.md` · `checklists/` · `agents/`

---

## Active Workflow Types

| Workflow | When to Use | Gate |
|----------|-------------|------|
| Feature Development | Adding new capabilities | QG-001, QG-002 |
| Research Experiment | New model architecture, ablation, evaluation | QG-004 |
| Bug Fix | Fixing confirmed defects (BUG-001 through BUG-003) | QG-007 |
| Security Review | Any API, data access, or auth change | QG-005 |
| Production Promotion | Promoting V3 to production, or new V1 checkpoint | QG-003, QG-004, QG-006, QG-008 |

---

## Standard Task Lifecycle

```
1. Read context/state.md (what is in flight, what is blocked)
2. Read context/decisions.md (what has been decided — don't relitigate)
3. Plan → agents/planner.md routes task to correct reviewer(s)
4. Implement with relevant standard applied (standards/ai_ml.md for model code, standards/research.md for experiments)
5. Self-review with AI reviewer if ML code; science reviewer if metrics/calibration/evaluation
6. Run quality gate checklist
7. Update context/state.md (mark task done, add next actions)
8. Generate ADR if architectural decision was made
9. Run: python3 tools/scripts/validate_agentos.py
10. Confirm 100/100 before declaring DONE
```

---

## Domain-Specific Rules

### Rule 1: Never modify calibration artifacts without SCI-002 resolved
`artifacts/calibrator.pkl` and `artifacts/operator_thresholds.json` are live production artifacts.
Changes require: (a) leakage audit complete, (b) re-evaluation on held-out test set, (c) bootstrap CI updated.

### Rule 2: Model evaluation must always be chronological
No random shuffling. Train on SC24, validate on 2020–2022, test on SC25. If you need a new split, the split must be strictly temporal and documented as an ADR.

### Rule 3: Three threshold files conflict — always use production values
`artifacts/operator_thresholds.json` (yellow=0.46, red=0.88) is the production source of truth.
The other two files (`calibration_report.json`, `operator_thresholds_validation_only.json`) are historical research artifacts, not operational values.

> **[SUPERSEDED — Sprint 23] Rule 3 is inverted.** The file this rule endorsed was proven test-set derived (`artifacts/sprint22_5/FINAL_VERDICT.md`) and is quarantined in `artifacts/archive/`. The production source of truth is now `artifacts/policies/operator_policy_v2.json` (yellow=0.14, red=0.95, validation-derived), and it must only ever be consumed through `app/services/ml/policy.py` (`load_policy` + `validate_policy_at_startup`) — never raw `json.load`. The same applies to Rule 1's mention of `operator_thresholds.json` as a live production artifact: it no longer is.

### Rule 4: V3 model_v3.py requires explicit feature count override
Until BUG-001 is fixed, always instantiate V3 as:
```python
LateFusionPatchTST(n_features_solexs=18, n_features_hel1os=4, ...)
```
Never use defaults — they are wrong and will raise a shape mismatch.

### Rule 5: SCI-001 blocks V3 production promotion
V3 cannot be promoted to production until multi-instrument benefit is demonstrated on a test window
containing actual joint GOES+Aditya-L1 flare events (current overlap: 4 days, zero flares).

### Rule 6: Every metric claim requires bootstrap CI
All published TSS/PR-AUC/ROC-AUC values must include 95% bootstrap confidence intervals
(n=1000 resamples). Single-point estimates without CI are insufficient for research or operational reports.

---

## Reviewer Routing (AdityaNet)

| File Pattern | Reviewer |
|-------------|---------|
| `app/services/ml/model*.py` | ai-reviewer |
| `app/services/ml/trainer*.py` | ai-reviewer |
| `app/services/ml/dataset*.py` | science-reviewer |
| `app/services/ml/evaluator*.py` | science-reviewer |
| `app/services/ml/metrics.py` | science-reviewer |
| `app/services/ml/inference.py` | ai-reviewer + security-reviewer |
| `app/api/v1/endpoints/*.py` | performance-reviewer |
| `app/core/config.py` | security-reviewer |
| `data_pipeline/*.py` | security-reviewer |
| `app/services/operations/impact.py` | science-reviewer + docs-reviewer |
| `context/*.md` | docs-reviewer |
| `artifacts/decisions/ADR-*.md` | chief-architect |

---

## Sprint Ceremony (Lightweight)

**Sprint start:**
- Update context/state.md with sprint goal and active tasks
- Confirm all blockers from previous sprint are triaged

**Sprint end:**
- Archive completed tasks in context/state.md
- Update bootstrap metrics (TSS, ECE) if model changed
- Run validator: 100/100 required before closing sprint

---

*Last updated: 2026-07-03 · AgentOS onboarding*

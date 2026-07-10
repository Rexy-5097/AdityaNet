# Sprint 23 — Migration Guide

**Conclusion:** The migration is a path change plus a schema change: consumers of `artifacts/operator_thresholds.json` must move to `artifacts/policies/operator_policy_v2.json` via `app/services/ml/policy.py` (never raw `json.load`). Production `inference.py` is already migrated. Operational behavior changes materially — thresholds are now yellow=0.14/red=0.95 (validation-derived) instead of the leaked 0.46/0.88 — and several scratch verifier scripts are knowingly broken against the old path.

## Before → after

| Aspect | Before (leaked) | After (Sprint 23) |
|--------|-----------------|-------------------|
| Policy file | `artifacts/operator_thresholds.json` (mutable, no provenance) | `artifacts/policies/operator_policy_v2.json` (signed, 13 provenance fields) |
| Thresholds | yellow=0.46, red=0.88 — swept on **test** predictions | yellow=0.14, red=0.95 — swept on **validation** predictions (Sprint 5.6) |
| Loading | raw `json.load`, silent `.get` defaults | `load_policy()` + `validate_policy_at_startup()`; abort on any failure |
| Mutation | edit the file | impossible without re-signing; re-signing requires regeneration through the guarded generators |
| Metadata | none | `service.policy_metadata`, `service.policy_startup_report` |

## How to consume a policy (any new code)

```python
from app.services.ml.policy import ACTIVE_POLICY_PATH, load_policy, validate_policy_at_startup

policy = load_policy(ACTIVE_POLICY_PATH)      # schema, integrity, leakage
validate_policy_at_startup(policy)            # fingerprint, split, generator, versions
td = policy.thresholds                        # yellow_threshold, red_threshold, tiers...
md = policy.metadata                          # all 13 provenance fields
```

Never `json.load` a policy file directly. Never catch `PolicyError` to continue with defaults — the absence of silent degradation is the point.

## How to produce a new policy

- **Regeneration from scratch:** `python3 scripts/sprint23/generate_validation_policy.py` (venv recommended; runs full validation inference, ~hours on MPS). Dataset is fixed to `artifacts/research/validation.parquet` by construction.
- **Never** hand-edit a policy file: the self-hash makes edits unloadable, deliberately.
- **If the generator script is edited**, every policy it produced fails startup check 4 (`generator_version`) — regenerate. This is intended behavior, not a bug.
- **If the validation dataset is rebuilt**, startup check 3 fails everywhere — regenerate policies against the new fingerprint and record why.

## Behavioral change operators must know

At yellow=0.14/red=0.95, honest backtest behavior (`artifacts/operator_backtest.json`): window Precision 0.390, Recall 0.723, TSS 0.382, EventRecall 0.696, ~6.9 false episodes/month, and **zero RED alerts** (red=0.95 is effectively unreachable; recorded in the policy's `lineage.known_limitations`). The previous 91%-precision/4%-recall behavior was an artifact of test-tuned thresholds and is void. The Sprint 22 cost-loss policy (Variant B) is the planned successor with a functioning RED tier.

## Knowingly broken / stale after migration (no action this sprint)

| Reference | Status |
|-----------|--------|
| `scratch/compute_hashes.py`, `scratch/verify_sprint15a.py`, `scratch/verify_sprint10k.py`, `scratch/verify_everything.py`, `scratch/run_full_validation_check.py`, `scratch/extract_all_json_values.py`, `scratch/generate_sprint10l_artifacts.py` | Reference `artifacts/operator_thresholds.json` at its old path; will report missing-file. These verify a superseded historical state; their hash baselines are evidence of that state, not of the current one |
| `scripts/optimize_operational_policy.py` | The leaked generator. Left in place as evidence (Sprint 22.5 cites its lines); must never be run again. Its outputs are quarantined |
| `artifacts/operational_thresholds.json` (yellow=0.09/red=0.19) | Validation-derived (clean) but dead — superseded; not quarantined, not consumed |
| Docs citing 0.46/0.88 as production (`PROJECT_STATUS.md`, `context/workflow.md` Rule 3, `context/memory.md`, `context/architecture.md`, Sprint 10K/14B artifacts) | Blast radius enumerated in `artifacts/sprint22_5/05_impact_analysis.md`; correction sweep is follow-up work |

## Rollback

Revert the `inference.py` edit (docstring, import, default path, section 4) and restore `artifacts/operator_thresholds.json` from `artifacts/archive/` minus the injected `QUARANTINE_REASON`/`quarantine_details` fields (pre-injection SHA256 033063ef… recorded inside for byte-exact verification). **Rolling back redeploys a proven-leaked policy — there is no legitimate reason to do so.**

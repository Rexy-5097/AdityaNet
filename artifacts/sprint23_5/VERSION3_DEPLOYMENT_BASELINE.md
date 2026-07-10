<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Definitive record of what frozen Version 3 deploys and what it lacks. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Deployment Baseline

**Conclusion:** Frozen Version 3 deploys a single production inference path — V1 PatchTST + validation-fit isotonic calibrator + provenance-gated operator policy v2.0.0 — behind a FastAPI service with TimescaleDB/Redis infrastructure. The V3 research model is not deployed. Frontend, real-time ingestion, authentication, an application Dockerfile, CI/CD, git version control, and test coverage beyond the policy layer are absent.

## Deployed (verified in Sprint 23 integration test with the real stack)

| Component | Artifact | Notes |
|-----------|----------|-------|
| Model checkpoint | `artifacts/models/patchtst_best.pt` (9.96 MB, epoch 3, 822,401 trainable params) | Loaded onto Apple M4 MPS |
| Calibrator | `artifacts/calibrator.pkl` (isotonic, validation-fit) | Unchanged since 2026-06-15 |
| Operator policy | `artifacts/policies/operator_policy_v2.json` — policy_id `operator_policy_v2.0.0`, yellow=0.14, red=0.95, schema 1.0, operator 2.0.0, scientific V1-2026.06 | Generator pinned at sha256:46209ddd…; dataset fingerprint sha256 9c1b770f… re-verified at every startup |
| Policy enforcement | `app/services/ml/policy.py` — 13 mandatory provenance fields, self-hash integrity, five-layer leakage guard, nine startup checks with abort-on-failure | Stdlib-only module |
| Inference service | `app/services/ml/inference.py` — MC Dropout (50 passes), tiered uncertainty suppression (0.10/0.15/0.20), RED confirmation (rolling mean + slope), hard X-ray coincidence filter, explainability, ISRO impact assessment | Alert logic byte-unchanged from Sprint 5.5; only the policy loading changed in Sprint 23 |
| API | FastAPI: `/health`, `/solar`, `/flares`, `/system`, `POST /predict/nowcast` (`app/main.py`, `app/api/v1/`) | Nowcast requires 360–362 one-minute flux records |
| Infrastructure | `docker-compose.yml`: TimescaleDB 2.15.3-pg16 (port 5433), Redis 7.2.4-alpine (6379); Alembic migration `a541577be3f5` | DB/cache only — no app container |
| Tests | `tests/test_policy_system.py` (15), `tests/integration_service_init.py`, `tests/conftest.py` | Policy layer only |
| Quarantine | `artifacts/archive/` — leaked policy + sweep CSV + README, structurally unloadable | Evidence-continuity hashes recorded |

## Effective operational behavior (honest backtest, `artifacts/operator_backtest.json`)

Window precision 0.390 / recall 0.723 / TSS 0.382; event recall 0.696; ~6.9 false episodes/month; median lead time 11.8 h; **zero RED alerts** at red=0.95 — the RED tier, its confirmation chain, and the coincidence filter are dormant. `[V4]` Successor policy with a functioning RED tier.

## NOT deployed / absent (unchanged by Sprints 22–23.5, which touched only the policy layer)

| Absence | Consequence | Tag |
|---------|-------------|-----|
| V3 research model (`model_v3.py`, sprint14c checkpoints) not wired to the API | Production is GOES-only; multi-instrument value undemonstrated anyway (SCI-001) | `[V4]` |
| Frontend / operator dashboard | No human interface; API-only | `[V4]` |
| Real-time GOES/Aditya-L1 ingestion scheduler | Data must be backfilled manually; the service cannot run truly live | `[V4]` |
| Authentication / authorization on any endpoint | Cannot be exposed beyond localhost responsibly | `[V4]` |
| Application Dockerfile | FastAPI app not containerized (compose covers DB/Redis only) | `[V4]` |
| CI/CD pipeline | Tests run manually; no automated gate on change | `[V4]` |
| Git version control | No history, no rollback, no commit-pinned provenance (`generator_commit` uses file hashes as substitute) | `[V4]` |
| Test coverage beyond the policy layer | Model, features, dataset, API, and alert-logic behavior remain untested by automation | `[V4]` |
| Monitoring / drift detection | Calibration and threshold portability across the solar cycle unmonitored in operation | `[V4]` |

## Startup contract (what "deployed" now means)

The service constructor aborts — by design, never degrading silently — unless: the policy file exists, carries complete provenance, matches its self-hash, passes the leakage guard, its dataset file hashes to the recorded fingerprint, its generator script hashes to `generator_commit`, and its schema/scientific/operator versions are supported. Rollback procedure and its (illegitimate) implications: `artifacts/sprint23/Migration_Guide.md`.

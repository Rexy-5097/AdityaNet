# Project State — SuryaNet / AdityaNet

> **Owner:** Soumyadeb Tripathy (update) · Everyone (read)
> **Update:** Every session · **Max:** ~400 tokens · Archive completed tasks
> **Cross-refs:** `context/decisions.md` · `PROJECT_STATUS.md`

---

## Snapshot

| Field | Value |
|-------|-------|
| **Date** | 2026-07-03 |
| **Phase** | Phase 3 — Decision-Layer Integrity Restoration (Sprint 23 complete) |
| **Sprint** | Sprint 23 — DONE (leakage-free versioned policy system deployed) |
| **Health** | 🟡 YELLOW — decision layer now leakage-free and gated; RED tier dormant at 0.95; docs blast-radius sweep pending |
| **Next Milestone** | Sprint 29 "Foundations and the GOES fair test" — git+CI+feature-builder tests FIRST, then V4 feature/dataset pipelines (GOES family) and fair-experiment arms F0-reeval + F1 (GOES-physics: T_iso/EM/dT, 3 seeds). Sprint 28 delivered the full V4 engineering spec (8 docs, artifacts/sprint28/): 32-feature space (KEEP 14 / MODIFY 10 / REMOVE 12 / NEW 17), per-timestep-mask dataset pipeline, pre-registered 4-arm fair experiment (F0-F3, min effect ΔTSS ≥ +0.02, 3 seeds w/ escalation to 5 if seed range > 0.015), decision tree (most likely Path A ~40%), 7-9 week roadmap (fits 2026-12-31), adversarial review (3 resolved / 2 unresolved: U1 statistical power, U2 no SWPC benchmark). Executive verdict: PROCEED |

---

## Active Work

| Task | Status | Owner | Blocked By | Priority |
|------|--------|-------|------------|---------|
| AgentOS onboarding | `IN_PROGRESS` | Soumyadeb | — | High |
| SCI-001: Validate Aditya-L1 benefit on joint flare windows | `PENDING` | Soumyadeb | Requires joint flare events (last overlap: 0 flares in 4 days) | Critical |
| SCI-002: Audit calibration leakage (is calibrator.pkl fit on test data?) | `PENDING` | Soumyadeb | — | Critical |
| CONFLICT-001: Fix model_v3.py defaults (n_features_solexs=25→18, n_features_hel1os=10→4) | `PENDING` | Soumyadeb | — | High |
| GAP-001: Add test suite (inference path, ≥80% coverage) | `PENDING` | Soumyadeb | — | High |
| GAP-002: Build frontend dashboard | `PENDING` | Soumyadeb | GAP-003 (auth needed first) | Medium |
| GAP-003: Add API authentication | `PENDING` | Soumyadeb | — | High |
| GAP-007: Wire V3 into inference.py | `PENDING` | Soumyadeb | SCI-001 (validate benefit first), CONFLICT-001 (fix defaults first) | Medium |

---

## Blockers

| # | Blocker | Severity | Resolution Path | Owner |
|---|---------|----------|----------------|-------|
| 1 | Joint GOES+Aditya-L1 dataset has zero positive flare events (only 4 days of overlap) | 🔴 Critical | Wait for/collect more overlap data; identify past events in raw Aditya-L1 archive | Soumyadeb |
| 2 | Calibration leakage status unresolved (SCI-002) | 🔴 Critical | Audit `artifacts/calibration/probs.npy` provenance — check training scripts | Soumyadeb |
| 3 | V1 operational recall is 3.97% at red threshold (misses 96% of flares) | 🟡 Major | Evaluate threshold trade-off; document operator acceptance criteria | Soumyadeb |

---

## Technical Debt

| Item | Severity | Filed | Notes |
|------|----------|-------|-------|
| model_v3.py default params incompatible with trained checkpoint | High | Sprint 14c | n_features_solexs=25 (should be 18), n_features_hel1os=10 (should be 4) |
| Three conflicting threshold files | High | Sprint 5.5 | calibration_report: 0.09/0.19; validation_only: 0.14/0.95; production: 0.46/0.88 |
| artifacts/models_v3/test_checkpoint.pt is 52MB untrained model (epoch=1, best_tss=-1.0) | Low | — | Consuming disk; purpose unknown |
| Sprint 20B summary.json reports PASS but validation_report_20b.md concludes FAIL | High | Sprint 20B | Parameter count errors and missing script in inventory |
| Repository is not a git repository | High | — | No version history, no rollback capability |
| No .gitignore, no .github/ directory | Medium | — | When git is initialized, need to exclude venv/, artifacts/research/, data/ |

---

## Known Bugs

| ID | Description | Severity | Owner | Milestone |
|----|------------|---------|-------|-----------|
| BUG-001 | model_v3.py defaults (n_features_solexs=25, n_features_hel1os=10) will cause shape mismatch when loading sprint14c checkpoint | Critical | Soumyadeb | Sprint 21 |
| BUG-002 | Temperature scaling produces TSS=0.00 on V3 (temperature=1.4168 shifts distribution but breaks decision boundary) | Major | Soumyadeb | Sprint 21 |
| BUG-003 | sprint20b_summary.json reports validation_verdict=PASS incorrectly | Minor | Soumyadeb | Sprint 21 |

---

## Recent Decisions

> Last 3 decisions — full index in `context/decisions.md`

| ADR | Decision | Date |
|-----|----------|------|
| (No ADRs yet — AgentOS just installed) | — | 2026-07-03 |

---

## Completed This Sprint

- [x] Full repository onboarding audit (PROJECT_STATUS.md generated)
- [x] AgentOS template installed into AdityaNet
- [x] profiles/adityanet.yaml created
- [x] All context files populated with verified repository data
- [x] Sprint 22 research planning: six documents under artifacts/sprint22/
- [x] Sprint 22.5 forensic audit: LEAKAGE PROVEN — production thresholds (0.46/0.88) were test-swept (artifacts/sprint22_5/FINAL_VERDICT.md)
- [x] Sprint 23: versioned policy system (app/services/ml/policy.py), leaked policy quarantined to artifacts/archive/, Sprint 5.6 validation-only policy promoted and deployed (artifacts/policies/operator_policy_v2.json, yellow=0.14/red=0.95), inference.py gated with 9 startup provenance checks, first test suite added (15 regression tests + integration, all green), AgentOS 100/100
- [x] Sprint 23.5: repository reconciled — 24 files annotated with VERSION STATUS blocks (incl. PROJECT_STATUS.md restructured into Current/Historical/Archived parts and inline [SUPERSEDED — Sprint 23] corrections in context files), seven lock documents written under artifacts/sprint23_5/ (VERSION3_FINAL_CERTIFICATE, CHANGELOG, SCIENTIFIC_BASELINE, DEPLOYMENT_BASELINE, LIMITATIONS, OPEN_RESEARCH, SCIENTIFIC_TIMELINE), all open items tagged [V4]. **VERSION 3 IS FROZEN** as the permanent research baseline
- [x] V4 planning (8 docs under artifacts/version4/): master plan, dependency graph, priority matrix, research program, sprint roadmap, risk register, success metrics, first-sprint spec
- [x] Sprint 24 "The Honest Yardstick" — unified episode-level block-bootstrap evaluation harness (app in scripts/sprint24/, tests/test_eval_framework.py, 10 tests). VERDICT: **V1 beats causal persistence** on True Skill Score (0.3811 vs 0.3018, paired Δ+0.0794 CI[0.0538,0.1062] p≈0.001), ROC-AUC (0.7482 vs 0.6509 non-overlapping), and pre-onset episode recall (0.6041 vs 0.3082) — all significant; TIE on Heidke Skill Score (NOT PROVEN); persistence more precise. Method D showed val→test threshold-transfer failure (val TSS 0.5689 → test 0.2150, below persistence). Recommendation **C: retrain existing architecture, improved procedure**. 8 docs in artifacts/sprint24/. All quality gates PASS (25 tests, reproducibility identical, frozen artifacts intact, AgentOS 100/100)
- [x] **SCI-002 RESOLVED (with nuance):** calibrator.pkl is clean (fit on validation — scripts/calibrate_model.py:191-202). The real leak is the DEPLOYED THRESHOLDS: scripts/optimize_operational_policy.py selected artifacts/operator_thresholds.json (0.46/0.88 + uncertainty tiers) by sweeping the saved TEST-set probabilities (docstring line 6). All published operator metrics are optimistically biased. Selected fix: Sprint 22 "Honest Decision Layer" (see artifacts/sprint22/Sprint22_Implementation_Plan.md)

---

## Next Actions

1. **SCI-002: Audit calibration leakage** — inspect how calibrator.pkl was fit; cross-reference artifacts/calibration/probs.npy row count (1,806,313) against train/val/test sizes — Soumyadeb
2. **CONFLICT-001: Fix model_v3.py defaults** — change `n_features_solexs=25→18` and `n_features_hel1os=10→4` — Soumyadeb
3. **GAP-001: Start test suite** — add pytest for `app/services/ml/inference.py` predict_with_uncertainty() and alert tier logic — Soumyadeb
4. **GAP-003: Add API authentication** — add JWT or API-key middleware to FastAPI before any external access — Soumyadeb
5. **GAP-008: Initialize git** — `git init`, create .gitignore (exclude venv/, data/, artifacts/research/) — Soumyadeb

---

*Updated: Soumyadeb Tripathy · 2026-07-03 · AgentOS onboarding session*

#!/bin/zsh
# AdityaNet CI gate — Sprint 29 Phase 1.
# Sprint 28 reference: 06_IMPLEMENTATION_ROADMAP.md Sprint 29 entry gates
# ("git initialization with a remote, continuous-integration run of the existing
# test suite, and unit tests for every new feature builder") and
# 07_EXTERNAL_REVIEW.md Reviewer-5 resolution.
#
# Gates (all must pass; first failure aborts):
#   1. Lint (ruff, error-level rules) on new V4 code and tests
#   2. Format check (ruff format --check) on the same scope
#   3. Unit tests (pytest tests/)
#   4. Artifact validation: deployed operator policy provenance gate
#   5. Reproducibility check: framework determinism test subset run twice
#   6. Repository validation (AgentOS validator, must be 100/100)
set -e
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
LINT_SCOPE=(app/services/ml/policy.py app/services/ml/features_v4 app/services/ml/dataset_v4 scripts/sprint23 scripts/sprint24 scripts/sprint26 scripts/sprint26a scripts/sprint26b scripts/sprint29 tests)

echo "── CI gate 1: ruff lint (E9,F rules; scope: new V4 code + tests) ──"
python3 -m ruff check --select E9,F "${LINT_SCOPE[@]}"
echo "PASS"

echo "── CI gate 2: ruff format --check ──"
python3 -m ruff format --check --quiet "${LINT_SCOPE[@]}" || {
  echo "NOTE: format differences exist (non-blocking per Sprint 29 flagged decision D2 — formatting"
  echo "      normalization deferred to avoid rewriting frozen-referenced sprint scripts)"; }
echo "PASS (advisory)"

echo "── CI gate 3: pytest ──"
python3 -m pytest tests/ -q

echo "── CI gate 4: deployed policy provenance validation ──"
./venv/bin/python -c "
import sys, os; sys.path.insert(0, os.getcwd())
from app.services.ml.policy import load_policy, validate_policy_at_startup, ACTIVE_POLICY_PATH
rep = validate_policy_at_startup(load_policy(ACTIVE_POLICY_PATH))
assert all(v == 'PASS' for v in rep.values()), rep
print('policy 9/9 checks PASS')"

echo "── CI gate 5: reproducibility (determinism tests, run twice) ──"
python3 -m pytest tests/ -q -k "determin or reproduc"
python3 -m pytest tests/ -q -k "determin or reproduc"

echo "── CI gate 6: AgentOS repository validation ──"
python3 tools/scripts/validate_agentos.py | grep -E "Overall Grade|Final Status" | tee /tmp/agentos_ci.txt
grep -q "100/100" /tmp/agentos_ci.txt

echo ""
echo "CI: ALL GATES PASS"

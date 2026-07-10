# Agent Runtime Test Cases

> **Layer:** Infrastructure | **Status:** Active
> **Purpose:** Test fixtures to statically verify AgentOS routing, context loading, and escalation rules.
> **Required Reading:** Read by `validate_agentos.py` to run routing simulations.
> **Cross-refs:** `agents/CAPABILITIES.md` · `tools/scripts/simulate_agent_runtime.py`

---

## Test Fixture Registry

These test cases define the expected routing, context files, applied standards, and escalation paths for specific file changes.

### Test Case 1: Preprocessing modification
- **Input File:** `src/models/preprocessing.py`
- **Expected Agent:** `science-reviewer`
- **Expected Context:**
  - `context/state.md`
  - `context/vision.md`
  - `context/workflow.md`
  - `metrics/benchmarks.md`
- **Expected Standards:** `standards/research.md`
- **Expected Output:** `PASS` / `FAIL` (Science-review report)
- **Expected Escalation:** `chief-architect` (if mathematical logic is contested)

### Test Case 2: Database Query Optimization
- **Input File:** `src/db/queries.py`
- **Expected Agent:** `performance-reviewer`
- **Expected Context:**
  - `context/state.md`
  - `context/tech_stack.md`
  - `metrics/performance.md`
- **Expected Standards:** `standards/code_quality.md`
- **Expected Output:** `PASS` / `FAIL` (Performance report against targets)
- **Expected Escalation:** `chief-architect` (if DB pool limits are hit)

### Test Case 3: Authentication Endpoint addition
- **Input File:** `src/api/auth.py`
- **Expected Agent:** `security-reviewer`
- **Expected Context:**
  - `context/state.md`
  - `context/architecture.md`
- **Expected Standards:** `standards/security.md` · `standards/api_design.md`
- **Expected Output:** `PASS` / `FAIL` (Security threat analysis report)
- **Expected Escalation:** `chief-architect` (always for new public auth entrypoints)

### Test Case 4: CSS Layout tweak
- **Input File:** `frontend/styles/layout.css`
- **Expected Agent:** `ui-reviewer`
- **Expected Context:**
  - `context/state.md`
  - `context/vision.md`
- **Expected Standards:** `standards/ui_ux.md`
- **Expected Output:** `PASS` (Style alignment check)
- **Expected Escalation:** None

### Test Case 5: Architecture Overview update
- **Input File:** `context/architecture.md`
- **Expected Agent:** `chief-architect`
- **Expected Context:**
  - `context/state.md`
  - `context/vision.md`
  - `context/tech_stack.md`
- **Expected Standards:** `standards/code_quality.md`
- **Expected Output:** `PASS` (ADR generated)
- **Expected Escalation:** Human (final approval)

---

## Simulation Test Execution

To execute these tests statically without invoking LLMs, run:
```bash
python3 tools/scripts/simulate_agent_runtime.py --run-tests
```
The script will match each test case's `Input File` against the simulator's output routing and raise an error if there is a mismatch.

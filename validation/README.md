# Synthetic Validation Suite

> **Layer:** Test Harness | **Status:** Active
> **Purpose:** Executable engineering validation cases verifying all subsystems of AgentOS.
> **Cross-refs:** `validation/runner/` · `validation/scenarios/`

---

## 1. Directory Structure

- `runner/`: Contains Python test suites (`execute_suite.py`) and reports.
- `scenarios/`: 20 directories (`VS-001/` to `VS-020/`) each containing:
  - `scenario.md`: Test parameters.
  - `input/request.json`: Test payload.
  - `assertions.yaml`: Assertions scorecard.

---

## 2. Running Scenarios

### Run entire test suite
```bash
python3 validation/runner/execute_suite.py
```

### Run a single scenario
```bash
python3 validation/runner/execute_scenario.py --id VS-004
```

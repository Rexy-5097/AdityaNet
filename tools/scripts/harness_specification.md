# Harness Engine Interface Specification

> **Layer:** Infrastructure | **Status:** Active
> **Purpose:** Documenting Harness Contracts, Request schema, Plan schema, and runtime monitor rules.
> **Cross-refs:** `tools/scripts/harness_engine.py` · `runtime/policies/`

---

## 1. Harness Interface Contract

The Harness Engine is the operating kernel of AgentOS. It coordinates incoming user requests by compiling deterministic execution plans and routing tasks to the appropriate reviewer agents.

```
Incoming Request Object
         │
         ▼
 ┌───────────────┐
 │Task Classifier│ ──▶ Identifies category & domain
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ Agent Router  │ ──▶ Selects specialist agents (agent_router.py)
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │Tool & Context │ ──▶ Selects scripts & token limits
 └───────────────┘
         │
         ▼
Compiled Execution Plan Object
```

---

## 2. Request Object Schema

Every request input received by the Harness Engine must adhere to the following schema:

```json
{
  "request_id": "REQ-100",
  "task": "Fix security vulnerability in authentication token expiration logic",
  "category": "hotfix",
  "priority": "high",
  "changed_files": [
    "src/auth.py",
    "tests/test_auth.py"
  ],
  "profile": "backend",
  "created": "2026-07-02 21:04:19"
}
```

---

## 3. Execution Plan Object Schema

Before dispatching any work, the Harness Engine compiles a plan object conforming to this schema:

```json
{
  "request_id": "REQ-100",
  "task_classification": {
    "domain": "security",
    "category": "hotfix",
    "quality_gates": ["QG-005", "QG-002"]
  },
  "workflow": "workflows/bug_fix.md",
  "agents": ["security-reviewer"],
  "tools": ["tools/scripts/validate_agentos.py"],
  "context_files": [
    "BOOTSTRAP.md",
    "PROJECT_CONFIG.yaml",
    "context/vision.md",
    "context/state.md",
    "agents/security-reviewer.md",
    "checklists/security_review.md"
  ],
  "estimated_tokens": 1200,
  "estimated_runtime": 10,
  "stopping_condition": "All Quality Gates evaluated and final validator status = PASS"
}
```

---

## 4. Execution Monitor Rules

1. **Cycle Limit:** If a workflow enters a retry loop, it is capped at `max_execution_cycles` = 5.
2. **Timeout:** The monitor halts execution if runtime exceeds `time_out_seconds` = 600.
3. **Escalation Target:** If loops or timeouts trigger, control escalates to the Target Owner (`chief-architect`) and halts execution.

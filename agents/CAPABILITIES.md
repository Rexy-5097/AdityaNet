# Agent Capabilities Matrix

> **Layer:** Infrastructure | **Status:** Active
> **Purpose:** The routing table and capabilities registry for the Orchestrator.
> **Required Reading:** Read by `orchestrator` to determine routing.
> **Cross-refs:** `agents/README.md` · `.agentos/config.yml` · `context/workflow.md`

---

## Routing Table Matrix

This matrix maps agent roles to their functional capabilities. The `orchestrator` parses this table (or the YAML equivalent in `config.yml`) to route tasks.

| Agent | Target Directory | Evaluates Standards | Evaluates Metrics | Can Approve | Can Reject | Escalates To |
|-------|------------------|---------------------|-------------------|-------------|------------|--------------|
| **orchestrator** | `*` (All changed files) | None | None | ❌ No | ❌ No | Human |
| **chief-architect**| `context/architecture.md` | `code_quality` | `quality` | ✅ Yes | ✅ Yes | Human |
| **planner** | `context/state.md` | `code_quality` | `quality` | ✅ Yes | ✅ Yes | Human |
| **ai-reviewer** | `models/`, `training/` | `ai_ml` | `benchmarks` | ✅ Yes | ✅ Yes | `chief-architect` |
| **science-reviewer**| `experiments/`, `math/` | `research` | `benchmarks` | ✅ Yes | ✅ Yes | `chief-architect` |
| **security-reviewer**| `auth/`, `api/`, `config/`| `security` | `quality` | ✅ Yes | ✅ Yes | `chief-architect` |
| **performance-reviewer**| `critical/`, `infra/`| `code_quality` | `performance` | ✅ Yes | ✅ Yes | `chief-architect` |
| **ui-reviewer** | `frontend/`, `views/` | `ui_ux` | `performance` | ✅ Yes | ✅ Yes | `chief-architect` |
| **qa-reviewer** | `tests/` | `testing` | `quality` | ✅ Yes | ✅ Yes | `chief-architect` |
| **docs-reviewer** | `docs/`, `README.md` | `documentation` | `quality` | ✅ Yes | ✅ Yes | `chief-architect` |
| **release-reviewer**| `releases/` | `documentation` | `quality` | ✅ Yes | ✅ Yes | `chief-architect` |

---

## Capability Flags

- **Reviews:** Analyzes changes against code, methodology, or design standards.
- **Writes:** Can generate or edit files directly.
- **Can Approve:** Has authority to mark a quality gate as passed.
- **Can Reject:** Has authority to block a quality gate and request changes.
- **Creates ADR:** Authorizes and writes Architecture Decision Records.
- **Uses Metrics:** Evaluates specific performance, quality, or benchmark targets.

| Agent | Reviews | Writes | Can Approve | Can Reject | Creates ADR | Uses Metrics |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| **orchestrator** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **chief-architect**| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **planner** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **ai-reviewer** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **science-reviewer**| ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **security-reviewer**| ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **performance-reviewer**| ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **ui-reviewer** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **qa-reviewer** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **docs-reviewer** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **release-reviewer**| ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |

---

## Extension Rules

To add a new capability or agent:
1. Update this matrix with a new row.
2. Define the new file trigger extensions in `.agentos/config.yml` trigger map.
3. Validate that the new agent does not introduce circular escalations (checked by `validate_agentos.py`).

# Tools — WAT Layer 3

> **Layer:** Infrastructure | **Status:** Placeholder — Populated per project

---

## Purpose

Tools are **deterministic executors**. They receive instructions from agents and execute them reliably.

```
AI orchestrates → Tools execute
```

Examples of tools:
- Python scripts
- CLI utilities
- REST APIs
- MCP servers
- Databases
- Automation pipelines

---

## Tool Categories

### MCP Servers (`mcp/`)
Model Context Protocol servers that extend agent capabilities.

Each MCP integration is defined as a modular configuration file. Adding or removing an MCP server does not affect the rest of the system.

### Scripts (`scripts/`)
Utility and automation scripts for common engineering tasks.

---

## Design Principles

1. **Prefer deterministic tools over AI for execution** — AI decides; tools do.
2. **Keep integrations modular** — adding a tool should not require changes to agents or workflows.
3. **Never hard-code tool credentials** — use environment variables.
4. **Document every tool** — purpose, inputs, outputs, error behaviors.
5. **Version tool configurations** — track changes to tool setups in CHANGELOG.

---

## MCP Integration Pattern

MCP servers plug into the tool layer without coupling to agents.

```
Agent needs data from an external service
         ↓
Agent invokes the appropriate MCP tool
         ↓
MCP server executes deterministically
         ↓
Result returned to agent
```

See `mcp/README.md` for integration details.

---

*Tools directory is configured per project. See subdirectories for details.*

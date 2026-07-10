# MCP Server Integrations

> **Layer:** Infrastructure | **Status:** Placeholder — Configure per project

---

## Purpose

This directory contains MCP (Model Context Protocol) server configurations.

Each MCP server provides a specific set of tools that agents can invoke for deterministic execution.

---

## Integration Template

See `template.yml` for the standard format to add a new MCP server.

---

## Available Integrations

Add integrations here as they are configured for the project:

| MCP Server | Purpose | Status |
|-----------|---------|--------|
| *(none yet)* | | |

---

## How to Add an MCP Server

1. Copy `template.yml` and rename it to `{server-name}.yml`.
2. Fill in all required fields.
3. Add a row to the table above.
4. Register in `.agentos/config.yml` under `tools.mcp`.
5. Update `context/tech_stack.md` with the new tool.

---

## Design Rules

- One configuration file per MCP server.
- Never put credentials in configuration files — reference environment variables.
- Keep MCP configurations independent of each other.
- Document what the agent can and cannot do with each tool.

---

*Configure MCP integrations when setting up a project.*

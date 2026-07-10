# Integrations

> **Layer:** Infrastructure | **Principle:** Vendor Neutrality

---

## Purpose

The `integrations/` directory contains **vendor-specific configuration files** for AI coding agents, cloud platforms, and external systems.

Everything outside this directory is **vendor-neutral** — it works with any AI agent or platform.

This separation ensures AgentOS remains usable as the AI tooling landscape evolves.

---

## Vendor Directories

| Directory | Vendor | Status |
|----------|--------|--------|
| `claude/` | Anthropic Claude / Claude Code | Placeholder |
| `gemini/` | Google Gemini / Antigravity | Placeholder |
| `codex/` | OpenAI Codex / ChatGPT | Placeholder |

---

## What Belongs Here

Each vendor directory may contain:

| File Type | Purpose |
|-----------|---------|
| System prompt / memory file | Agent-specific initialization context |
| Tool configuration | Vendor-specific tool setup |
| Workflow adaptations | How the agent handles AgentOS workflows |
| Known limitations | What this agent cannot do that the standard expects |
| Setup instructions | How to configure this agent for AgentOS |

---

## What Does NOT Belong Here

- Engineering standards → `standards/`
- Checklists → `checklists/`
- Workflows → `workflows/`
- Agent specifications → `agents/`
- Project context → `context/`

If a file in `integrations/` duplicates content from elsewhere, it should instead reference that content.

---

## Adding a New Integration

1. Create a new directory: `integrations/{vendor-name}/`
2. Add a `README.md` explaining what this integration provides.
3. Add vendor-specific configuration files.
4. Add a row to the table above.
5. **Do NOT modify any files outside `integrations/`** to add vendor-specific behavior.

---

*Phase 1 creates the structure. Vendor-specific content is added per project.*

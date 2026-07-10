# Claude Code — AgentOS Integration

> **Compatibility:** Claude Code (claude.ai/code) | **AgentOS Version:** 1.0.0

---

## How AgentOS is Discovered by Claude Code

Claude Code automatically reads markdown files at the root of a repository. Place `AGENTOS.md` at the repository root and Claude will discover it on first open.

**Recommended CLAUDE.md content** (create this file at repo root for Claude-specific hints):
```markdown
# AgentOS Repository
Read AGENTOS.md first and follow its initialization protocol exactly.
Do not begin implementation until AgentOS initialization completes.
```

---

## Initialization Pattern

When Claude Code opens this repository:

1. Claude reads `AGENTOS.md` (auto-discovered)
2. Claude loads `context/state.md` + `PROJECT_CONFIG.yaml`
3. Claude confirms: "AgentOS initialized. Profile: [X]. Ready."
4. You assign a task

**Prompt to use when starting a session:**
```
Initialize this repository using AgentOS.
Load AGENTOS.md, context/state.md, and PROJECT_CONFIG.yaml.
Report the active profile and enabled standards before proceeding.
```

---

## Context Loading Strategy for Claude

Claude has a generous context window. Recommended loading:

- **Always load:** `AGENTOS.md`, `context/state.md`, `PROJECT_CONFIG.yaml`
- **On demand:** Load specific agents, standards, and checklists as needed
- **Never eagerly load:** `artifacts/decisions/` (56+ ADRs), `runtime/` internals

---

## Recommended Workflow

```bash
# 1. Bootstrap (once per project)
python3 tools/scripts/bootstrap_project.py --interactive

# 2. Start Claude Code in this directory
# Claude discovers AGENTOS.md automatically

# 3. Validate before any work
python3 tools/scripts/validate_agentos.py
```

---

## Claude-Specific Notes

- Claude handles long markdown contracts well — agent contracts in `agents/` load efficiently
- For complex multi-agent tasks, invoke the orchestrator pattern explicitly
- Claude respects structured YAML policies in `.agentos/config.yml`
- Paste validator output when debugging: Claude correctly interprets the structured report

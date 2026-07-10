# OpenAI Codex / GitHub Copilot — AgentOS Integration

> **Compatibility:** GitHub Copilot, Codex API | **AgentOS Version:** 1.0.0

---

## How AgentOS is Discovered by Codex / Copilot

GitHub Copilot reads open files and workspace context. To initialize AgentOS:

1. Open `AGENTOS.md` in your editor before starting Copilot
2. Use Copilot Chat with the initialization prompt below
3. Keep `AGENTOS.md` and `context/state.md` open in editor tabs

**Initialization prompt for Copilot Chat:**
```
I'm using an AgentOS repository. The framework spec is in AGENTOS.md.
Read it completely, then load context/state.md and PROJECT_CONFIG.yaml.
Follow the initialization protocol. Do not write code until initialization confirms.
```

---

## Context Loading Strategy for Copilot

Copilot works with files open in the editor. For best results:

- Keep `AGENTOS.md` open in a pinned tab
- Open `context/state.md` before each session
- Open the relevant agent contract (`agents/{agent}.md`) before invoking it
- Open the relevant standard (`standards/{standard}.md`) before implementation

---

## Recommended Workflow

```bash
# 1. Bootstrap
python3 tools/scripts/bootstrap_project.py --interactive

# 2. Open editor (VS Code recommended with Copilot extension)
# Open: AGENTOS.md, context/state.md, PROJECT_CONFIG.yaml in tabs

# 3. Use Copilot Chat with initialization prompt
```

---

## Codex API Notes

When using Codex directly via API, prepend `AGENTOS.md` content to your system prompt:

```python
system_prompt = open("AGENTOS.md").read() + "\n\n" + open("context/state.md").read()
```

This ensures AgentOS protocol is always active.

---

## Copilot-Specific Notes

- Copilot is strongest at inline completion — use it for implementing after the plan is set
- Use Copilot Chat for agent invocation and review tasks
- Keep agent contract files open in tabs for domain-specific reviewer behavior
- Copilot respects structured comments — use `# AgentOS: invoke security-reviewer` style hints

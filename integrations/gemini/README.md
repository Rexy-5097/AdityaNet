# Google Gemini — AgentOS Integration

> **Compatibility:** Gemini (aistudio.google.com / Antigravity IDE) | **AgentOS Version:** 1.0.0

---

## How AgentOS is Discovered by Gemini

Gemini (via Google AI Studio or Antigravity) reads files from the repository context. `AGENTOS.md` at the root is the primary discovery target.

**Recommended prompt when starting Gemini:**
```
I'm working in an AgentOS repository. Read AGENTOS.md first, then load
context/state.md and PROJECT_CONFIG.yaml. Confirm initialization before
proceeding with any task.
```

---

## Initialization Pattern

1. Open Gemini with access to this repository
2. Paste the initialization prompt above, or provide `AGENTOS.md` as context
3. Gemini loads and confirms the active profile
4. Assign engineering tasks

---

## Context Loading Strategy for Gemini

Gemini has a very large context window (1M+ tokens on Gemini 1.5 Pro/Flash). Still, follow the minimal context protocol:

- **Always load:** `AGENTOS.md`, `context/state.md`, `PROJECT_CONFIG.yaml`
- **Load sparingly:** Agent contracts, standards files, checklist gates
- **Don't mass-load:** Entire `artifacts/` or `runtime/` directories

---

## Recommended Workflow

```bash
# 1. Bootstrap
python3 tools/scripts/bootstrap_project.py --interactive

# 2. Open Gemini with repo context

# 3. Validate
python3 tools/scripts/validate_agentos.py
```

---

## Gemini-Specific Notes

- Gemini performs well at multi-document analysis — use it for architecture reviews
- When running Harness tasks, paste the structured YAML policy from `.agentos/config.yml`
- Gemini's code generation is strong for Python — ideal for runtime and validator work
- For the Loop Runtime, Gemini handles iterative refinement prompts very well

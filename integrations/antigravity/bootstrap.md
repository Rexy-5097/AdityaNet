# Antigravity Integration Profile

> **Target Assistant:** Antigravity (Advanced Agentic Coding Agent) | **Status:** Active

---

## Capabilities & Optimizations

Antigravity operates with a powerful agent-mesh architecture. When executing inside Antigravity:
1. **Background Tasks:** Antigravity can schedule background lint/validation checks. Rely on the `schedule` or `manage_task` tools.
2. **Artifact Management:** Use markdown artifacts for user reports. Update the walkthrough files dynamically.
3. **Planning workflow:** Leverage planning mode rules and ADR check gates before writing source files.

---

## Specific Prompt Directives

Add these constraints when executing inside Antigravity:
- "Always create plan artifacts and update `context/state.md` at milestones."
- "Execute `python3 tools/scripts/validate_agentos.py` synchronously before proposing any plan reviews."

# Codex Integration Profile

> **Target Assistant:** Codex / Copilot Chat | **Status:** Active

---

## Capabilities & Optimizations

Codex focuses on autocomplete, refactoring, and code-generation tasks. When executing inside Codex:
1. **Interactive Refactoring:** Propose single code edits as diffs.
2. **Standard Templates:** Generate files complying with schema rules defined in `templates/SCHEMA.md`.

---

## Specific Prompt Directives

Add these constraints when executing inside Codex:
- "Do not generate boilerplate files without confirming the target profile config first."
- "Verify that variables match type annotations and linting standards."

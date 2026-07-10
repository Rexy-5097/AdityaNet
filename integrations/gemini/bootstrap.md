# Gemini CLI & Workspace Integration Profile

> **Target Assistant:** Gemini (API / Workspace) | **Status:** Active

---

## Capabilities & Optimizations

Gemini Workspace excels at massive context ingestion and structured schema parsing. When executing inside Gemini:
1. **Context Window:** Gemini can ingest the entire repository in one shot. However, enforce token budgets to prevent model distraction and latency.
2. **Structured JSON:** Enforce JSON schema validation rules using strict type parameters.

---

## Specific Prompt Directives

Add these constraints when executing inside Gemini:
- "Parse Frontmatter blocks strictly using Python `yaml` package to prevent false positives."
- "Verify that links to files contain correct paths and hashes."

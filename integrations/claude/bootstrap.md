# Claude Code Integration Profile

> **Target Assistant:** Claude Code CLI | **Status:** Active

---

## Capabilities & Optimizations

Claude Code is a command-line first agent with deep local environment access. When executing inside Claude Code:
1. **Direct CLI Execution:** Claude Code should execute `python3 tools/scripts/bootstrap_project.py --interactive` directly in the terminal environment.
2. **Path Resolution:** Claude Code resolves absolute file links easily. Use full path links when referencing directories.
3. **Task Tracking:** Claude Code can run the validation script in parallel. Use validation logs to debug syntax issues.

---

## Specific Prompt Directives

Add these constraints when executing inside Claude Code:
- "Run command line tools synchronously. Avoid background execution loops."
- "If validation returns warnings, fix them immediately using `replace_file_content` before asking the developer."

# Antigravity (Google DeepMind) — AgentOS Integration

> **Compatibility:** Antigravity IDE (Google DeepMind) | **AgentOS Version:** 1.0.0

---

## How AgentOS is Discovered by Antigravity

Antigravity automatically scans for `AGENTOS.md` at the workspace root. When found, it loads the initialization protocol on first open.

**This is the native integration.** AgentOS was designed with Antigravity as the primary AI coding assistant.

---

## Initialization Pattern

Antigravity reads `AGENTOS.md` on workspace open. No additional prompt is needed.

If you want to explicitly trigger initialization:
```
Initialize this AgentOS repository. Load AGENTOS.md, context/state.md,
and PROJECT_CONFIG.yaml. Confirm the active profile and report ready status.
```

---

## Context Loading Strategy for Antigravity

Antigravity uses a corpus-based workspace system. AgentOS is optimized for this:

- `AGENTOS.md` is eagerly discovered
- `context/` files load on demand using semantic search
- `runtime/policies/` is loaded when routing decisions are needed
- Agent contracts are loaded by name when invoked

---

## Makefile Integration

Antigravity supports the `Makefile` directly:

```bash
make bootstrap          # Interactive setup
make validate           # Run health validator
make health             # Quick health summary
make test               # Run synthetic suite
make profile P=flagship # Bootstrap with flagship profile
```

---

## Recommended Workflow

```bash
# 1. Bootstrap
python3 tools/scripts/bootstrap_project.py --interactive
# OR
make bootstrap

# 2. Open Antigravity in this workspace directory
# AGENTOS.md is auto-discovered

# 3. Run validator
make validate
```

---

## Antigravity-Specific Notes

- Antigravity's subagent system maps naturally to AgentOS specialist reviewers
- Use `invoke_subagent` patterns for multi-agent review scenarios
- The Loop Runtime architecture mirrors Antigravity's planning-execution model
- AgentOS ADRs and artifacts integrate cleanly with Antigravity's artifact system
- For large projects, use Antigravity's `/teamwork-preview` command alongside the Harness

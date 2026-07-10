# Scripts

> **Layer:** Infrastructure | **Status:** Placeholder — Add scripts per project

---

## Purpose

This directory contains utility and automation scripts that support the engineering workflow.

Scripts are **deterministic tools** — they execute reliably given consistent input.

---

## Script Categories

| Category | Description |
|---------|-------------|
| `setup/` | Environment setup and initialization scripts |
| `validation/` | Data and output validation scripts |
| `reporting/` | Report generation and export scripts |
| `migration/` | Data migration and schema change scripts |
| `testing/` | Test execution and coverage scripts |

---

## Script Standards

Every script must:
1. Have a clear filename describing its purpose.
2. Include a top-of-file comment: purpose, inputs, outputs, usage.
3. Handle errors explicitly and exit with appropriate codes.
4. Accept configuration via environment variables (never hardcoded).
5. Be idempotent where possible.
6. Be documented in this README when added.

---

## How to Add a Script

1. Create the script in the appropriate subdirectory.
2. Add a usage entry to the table below.
3. Test with an explicit input.

## Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| *(none yet)* | | |

---

*Add scripts here as they are developed for the project.*

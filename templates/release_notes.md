---
id: ART-REL-NNNN
title: "Release [Version] Notes"
version: 1.0
status: draft
owner: release-reviewer
created: YYYY-MM-DD
modified: YYYY-MM-DD
related_adr: None
related_standard: standards/documentation.md
related_checklist: QG-008
related_workflow: release.md
related_agent: release-reviewer
---

# Release Notes: [ID]

## Metadata Snapshot

- **Release Version:** [e.g. 1.2.0]
- **Release Date:** [YYYY-MM-DD]
- **Target Environment:** [e.g. Production]

## Quality Gate Checklist Sign-offs

All prior checkpoints must be marked PASS before packing.

- **QG-001 (Feature Completion):** [PASS / FAIL]
- **QG-003 (QA Verification):** [PASS / FAIL]
- **QG-005 (Security Review):** [PASS / FAIL]

## Major Highlights & Features

- **[Feature ID]:** Short description of the user impact.

## Security Audit & CVE Status

- **Vulnerability scan status:** [CLEAN / MITIGATED]
- **Secrets check:** [VERIFIED ZERO SECRETS COMITTED]

## Migration Guidelines & Rollback Script

- **Migration Steps:** [Database indices updates or config changes]
- **Rollback command:** [Execution command on failure]

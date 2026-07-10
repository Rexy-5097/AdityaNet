# Templates

> **Layer:** Infrastructure | **Status:** Placeholders — Populated in Phase 6

---

## Purpose

Templates are **reusable document shells** for recurring project artifacts.

Rules:
- Copy a template to the appropriate records directory before filling it in.
- Never modify the template itself when creating a document.
- Templates are pristine; filled documents accumulate in `artifacts/`.

---

## Template Library

| Template | Used For | Output Location |
|---------|---------|----------------|
| `experiment_log.md` | Documenting experiments | `artifacts/experiments/` |
| `decision_record.md` | Architecture Decision Records | `artifacts/decisions/` |
| `architecture_review.md` | Architecture review sessions | `artifacts/decisions/` |
| `bug_report.md` | Bug intake and tracking | Project tracker |
| `feature_proposal.md` | New feature requests | Project tracker |
| `meeting_notes.md` | Meetings and discussions | Project notes |
| `release_notes.md` | Release announcements | `artifacts/releases/` |

---

*Phase 6 will populate all template files in this directory.*

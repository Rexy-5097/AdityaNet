---
id: STD-06
title: Evidence consistency
status: active
verification: INTG
---

# STD-06 — Evidence consistency

After each build, artifacts are re-read from storage, pointers resolved, and values compared
against the rendered output. Drift fails the build ([ADR-0012](../adr/ADR-0012.md)).

Coverage claims must state **pointer-bound**, never "published" — see VVMP §10.2 U-4.

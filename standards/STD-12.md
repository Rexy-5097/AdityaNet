---
id: STD-12
title: Tests run without proprietary data
status: active
verification: INTG
---

# STD-12 — Tests run without proprietary data

Every test suite must execute against a clean repository export. Tests requiring the real
archive **skip**, never fail.

A skip guard must test for **the files it needs**, not for a directory. A directory
containing tracked auxiliary files exists in every clean checkout while the data does not;
guarding on the directory silently disables the suite.

**Enforcement:** clean-export CI job.

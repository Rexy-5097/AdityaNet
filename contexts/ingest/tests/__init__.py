"""Marks the ingest test directory as a package.

Bare `pytest` and `python -m pytest` differ in `sys.path`: the latter inserts the current
directory, the former does not. Without this file the suite passes locally and fails in CI
(IMPL-007, M2/E3). The marker makes both invocations resolve `contexts.ingest.*` the same way.
"""

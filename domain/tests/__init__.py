"""Marks the domain test directory as a package.

Not ceremony. Bare `pytest` and `python -m pytest` differ in `sys.path`: the latter inserts
the current directory, the former does not. Without this file the suite passed locally under
`python -m pytest` and failed in CI under bare `pytest`, which is how M2/E3 shipped a red
build (IMPL-007). The marker makes both invocations resolve `domain.*` the same way.
"""

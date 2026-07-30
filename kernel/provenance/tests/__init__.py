"""Unit tests for the provenance kernel.

WHY THIS FILE EXISTS. Without it, pytest roots `sys.path` at this directory rather than at
the repository, and `import kernel` fails — but only under a bare `pytest` invocation.
`python -m pytest` inserts the working directory into `sys.path` and masks it entirely,
which is how this reached CI green locally and red on the runner.

Making the chain kernel -> provenance -> tests a package means pytest walks up to the first
directory without an `__init__.py` — the repository root — and the import resolves under
either invocation.

These modules import pytest. That is not the kernel importing a third party: the isolation
test in tests/architecture/ scans runtime modules only, and excludes this directory
explicitly, because the shipped package does not contain it.
"""

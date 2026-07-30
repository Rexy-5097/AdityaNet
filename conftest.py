"""Makes the repository root importable for every suite.

WHY THIS FILE EXISTS
--------------------
Under pytest's default `prepend` import mode, the directory inserted into `sys.path` for a
test module is the first ancestor that is *not* a package. `domain/tests/` and
`kernel/provenance/tests/` carry `__init__.py` all the way up, so the repository root is
inserted and `import domain` resolves. `tests/integration/` and `tests/architecture/` do not,
so the inserted directory is the test directory itself — and until now that was invisible,
because no test outside a package imported a first-party package.

M2/E4/#12 adds the first one: `tests/integration/test_domain_contract_conformance.py` imports
`domain` and `kernel` together, which is the whole point of it. Without this file it fails at
collection with `ModuleNotFoundError: No module named 'domain'`.

A `conftest.py` at the root is the mechanism pytest provides for exactly this: its directory
is prepended to `sys.path`, uniformly, for every invocation and every suite.

WHY NOT THE ALTERNATIVES
------------------------
Adding `__init__.py` to `tests/` and each subdirectory would work, but it makes the test tree
a package and every future subdirectory a place to remember one — the same footgun that made
`kernel/provenance/tests/__init__.py` a CI-only failure once already (IMPL-007). Setting
`PYTHONPATH` in the workflows would work in CI and not locally, which is the exact asymmetry
that produced that defect: green on a developer's machine, red on the runner.
"""

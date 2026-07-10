import os
import sys

# Make the repository root importable (app.services.ml.policy) regardless of
# how pytest resolves rootdir. Tests must be run with cwd = repository root
# because the policy layer resolves artifact paths relative to it.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

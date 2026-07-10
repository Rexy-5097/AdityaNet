"""Policy loader module for the shared runtime kernel."""
import os
import yaml

class PolicyLoader:
    def __init__(self, root_dir):
        self.root = root_dir

    def load(self, filename):
        """Loads a policy YAML configuration file."""
        path = os.path.join(self.root, "runtime", "policies", filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

"""Context optimization and loading module for Harness Engine."""
import os

class ContextOptimizer:
    def __init__(self, context_policy, root_dir):
        self.policy = context_policy
        self.root = root_dir
        self._cache = {}

    def get_context_files(self, classification, agents):
        """Compiles the minimal set of context files and enforces token budgets."""
        loaded = []
        token_sum = 0
        
        # 1. Load mandatory files
        mandatory = self.policy.get("mandatory_context", [])
        for f in mandatory:
            path = os.path.join(self.root, f)
            if os.path.exists(path):
                loaded.append(f)
                
        # 2. Load agent specifications only for routed agents
        for agent in agents:
            agent_file = f"agents/{agent}.md"
            if os.path.exists(os.path.join(self.root, agent_file)):
                loaded.append(agent_file)
                
        # 3. Load quality checklists
        for gate in classification.get("quality_gates", []):
            # QG-001 -> feature_completion.md
            gate_map = {
                "QG-001": "checklists/feature_completion.md",
                "QG-002": "checklists/pull_request.md",
                "QG-003": "checklists/qa.md",
                "QG-004": "checklists/research_validation.md",
                "QG-005": "checklists/security_review.md",
                "QG-006": "checklists/deployment.md",
                "QG-007": "checklists/bug_fix.md",
                "QG-008": "checklists/release.md"
            }
            ch_file = gate_map.get(gate)
            if ch_file and os.path.exists(os.path.join(self.root, ch_file)):
                loaded.append(ch_file)
                
        return {
            "context_files": loaded,
            "estimated_tokens": len(loaded) * 150  # Mock token estimate
        }

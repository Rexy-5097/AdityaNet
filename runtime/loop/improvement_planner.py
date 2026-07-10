"""Improvement planner mapping failures to correction modes."""

class ImprovementPlanner:
    def __init__(self):
        pass

    def select_strategy(self, reflection_report):
        """Maps root cause to target improvement strategy."""
        cause = reflection_report.get("root_cause_category", "unknown")
        
        strategy_map = {
            "syntax-error": "error correction",
            "import-error": "refactoring",
            "assertion-failure": "optimization",
            "security-leak": "security hardening"
        }
        
        return strategy_map.get(cause, "optimization")

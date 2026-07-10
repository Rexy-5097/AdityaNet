"""Reflection module for analyzing defects and repeated failures."""

class ReflectionEngine:
    def __init__(self, reflection_policy):
        self.policy = reflection_policy
        self.history = []

    def analyze_failure(self, iteration_info, error_logs):
        """Generates a structured reflection report."""
        errors = [err.lower() for err in error_logs]
        root_cause = "Unknown gap"
        
        # Categorize root causes based on log keywords
        categories = self.policy.get("root_causes", {
            "syntax": "syntax-error",
            "import": "import-error",
            "assertion": "assertion-failure",
            "security": "security-leak"
        })
        
        for key, cause in categories.items():
            if any(key in err for err in errors):
                root_cause = cause
                break
                
        report = {
            "iteration": iteration_info.get("iteration", 1),
            "detected_errors": error_logs,
            "root_cause_category": root_cause,
            "recommended_action": f"Fixing {root_cause} pattern."
        }
        self.history.append(report)
        return report

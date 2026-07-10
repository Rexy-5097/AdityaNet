"""Cost optimizer module for Harness Engine."""

class CostOptimizer:
    def __init__(self, context_policy):
        self.policy = context_policy
        self._cache = {}

    def get_cached_plan(self, request):
        """Checks for duplicate requests in the decision cache."""
        task = request.get("task", "").strip()
        return self._cache.get(task)

    def cache_plan(self, request, plan):
        """Caches compilation outputs for duplicate requests."""
        task = request.get("task", "").strip()
        self._cache[task] = plan

    def evaluate_budget(self, plan):
        """Verifies if the estimated token counts are within policies."""
        max_context = self.policy.get("token_limits", {}).get("max_context_window", 4000)
        est = plan.get("estimated_tokens", 0)
        if est > max_context:
            return "WARNING: Context load estimate exceeds max target limits."
        return "OK"

"""Tool router module for Harness Engine."""

class ToolRouter:
    def __init__(self, tools_policy):
        self.policy = tools_policy

    def route_tools(self, request, agents):
        """Routes deterministic scripts to run (e.g. validator, test runner)."""
        task = request.get("task", "").lower()
        tools = []
        
        # Check trigger keywords
        triggers = self.policy.get("tool_triggers", {})
        for name, t_data in triggers.items():
            if name in task:
                tools.append(t_data["script"])
                
        # Always route static validator for general checks
        if "tools/scripts/validate_agentos.py" not in tools:
            tools.append("tools/scripts/validate_agentos.py")
            
        return tools

"""Task classifier module for Harness Engine."""

class TaskClassifier:
    def __init__(self, routing_policy, quality_policy):
        self.routing = routing_policy
        self.quality = quality_policy

    def classify(self, request):
        """Determines domain, category, and target quality gates."""
        task = request.get("task", "").lower()
        files = request.get("changed_files", [])
        
        # 1. Infer domain from changed files or task string
        domain = "architecture"  # default fallback
        for f in files:
            if f.endswith(".py"):
                if "preprocessing" in f or "train" in f:
                    domain = "science"
                elif "auth" in f or "login" in f:
                    domain = "security"
                else:
                    domain = "ai"
                break
            elif f.endswith(".css") or f.endswith(".html") or f.endswith(".js"):
                domain = "ui"
                break
            elif f.endswith(".md") or f.endswith(".yaml") or f.endswith(".yml"):
                domain = "docs"
                break
                
        # Sub-check matching keywords in task description
        if "perf" in task or "optimize" in task or "db" in task or "api" in task:
            domain = "performance"
        elif "security" in task or "cve" in task or "credential" in task:
            domain = "security"
        elif "test" in task or "regression" in task or "bug" in task:
            domain = "science"
            
        # 2. Determine category
        category = "feature"
        if "fix" in task or "bug" in task or "error" in task:
            category = "hotfix"
        elif "release" in task or "tag" in task:
            category = "release"
        elif "research" in task or "experiment" in task:
            category = "research"
            
        # 3. Select Quality Gates
        gates = self.quality.get("category_gates", {}).get(category, ["QG-001"])
        
        return {
            "domain": domain,
            "category": category,
            "quality_gates": gates
        }

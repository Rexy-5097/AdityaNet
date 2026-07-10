"""Workflow router module for Harness Engine."""

class WorkflowRouter:
    def __init__(self):
        pass

    def select_workflow(self, classification):
        """Determines the target workflow based on task category."""
        category = classification.get("category", "feature")
        
        workflow_map = {
            "feature": "workflows/master.md",
            "hotfix": "workflows/bug_fix.md",
            "release": "workflows/release.md",
            "research": "workflows/research.md"
        }
        
        return workflow_map.get(category, "workflows/master.md")

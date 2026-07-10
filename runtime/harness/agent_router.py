"""Agent router module for Harness Engine."""
import os

class AgentRouter:
    def __init__(self, routing_policy):
        self.policy = routing_policy

    def route(self, request, classification):
        """Standardizes agent dispatch selection based on file paths and domain categories."""
        files = request.get("changed_files", [])
        domain = classification.get("domain", "architecture")
        
        agents = set()
        
        # 1. Check overrides
        for f in files:
            override_agent = self.policy.get("file_override_routing", {}).get(f)
            if not override_agent:
                # Fallback to checking the filename basename
                override_agent = self.policy.get("file_override_routing", {}).get(os.path.basename(f))
            if override_agent:
                agents.add(override_agent)
                
        # 2. Check extension default routing
        if not agents:
            for f in files:
                ext = f[f.rfind("."):] if "." in f else ""
                ext_agent = self.policy.get("file_extension_routing", {}).get(ext)
                if ext_agent:
                    agents.add(ext_agent)
                    
        # 3. Fallback to domain default
        if not agents:
            domain_agent = self.policy.get("domain_routing", {}).get(domain, "orchestrator")
            agents.add(domain_agent)
            
        return sorted(list(agents))

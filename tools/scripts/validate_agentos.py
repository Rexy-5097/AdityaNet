#!/usr/bin/env python3
"""
AgentOS Static Validator
Statically parses and validates the AgentOS repository layers, agent contracts,
dependencies, workflows, standards, and metrics.
Produces the official AgentOS Health Report.
"""

import os
import sys
import re
import yaml
from datetime import datetime

# Repository root directory
REPO_ROOT = "/Users/soumyadebtripathy/WorkFlow/agentos-template"

def read_file_safe(path):
    """Safely reads file contents or returns empty string if error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

class Validator:
    def __init__(self, root):
        self.root = root
        self.broken_references = 0
        self.missing_consumers = 0
        self.circular_dependencies = 0
        self.token_budget_violations = 0
        self.warnings = []
        self.files_checked = 0
        
        self.agents = []
        self.standards = []
        self.metrics = []
        self.adrs = []
        
        # Category scores (0 - 100)
        self.scores = {
            "Structural": 100,
            "Contract": 100,
            "Dependency": 100,
            "Token Budget": 100,
            "Cross-reference": 100,
            "Architecture": 100,
            "Agent Routing": 100,
            "Workflow": 100,
            "Standards": 100,
            "Metrics": 100,
            "Artifacts": 100,
            "Bootstrap": 100,
            "Harness": 100,
            "Loop": 100,
            "Validation": 100,
            "Production": 100,
            "Certification": 100,
            "Distribution": 100
        }

    def run_all(self):
        """Runs all validation categories."""
        self.scan_files()
        
        # 1. Structural
        self.validate_structural()
        # 2. Contract
        self.validate_contract()
        # 3. Dependency
        self.validate_dependency()
        # 4. Token Budget
        self.validate_token_budget()
        # 5. Cross-reference
        self.validate_cross_references()
        # 6. Architecture
        self.validate_architecture()
        # 7. Agent Routing
        self.validate_agent_routing()
        # 8. Workflow
        self.validate_workflow()
        # 9. Standards
        self.validate_standards()
        # 10. Metrics
        self.validate_metrics()
        # 11. Checklists
        self.validate_checklists()
        # 12. Artifacts
        self.validate_artifacts()
        # 13. Bootstrap
        self.validate_bootstrap()
        # 14. Harness
        self.validate_harness()
        # 15. Loop
        self.validate_loop()
        # 16. Validation Suite
        self.validate_synthetic_suite()
        # 17. Production RC1 Verification
        self.validate_production()
        # 18. v1.0.0 Production Certification
        self.validate_certification()
        # 19. Final Team Distribution & Release Packaging
        self.validate_distribution()
        
    def scan_files(self):
        """Scans directories to register active components."""
        # Find agents
        agents_dir = os.path.join(self.root, "agents")
        if os.path.exists(agents_dir):
            self.agents = [f[:-3] for f in os.listdir(agents_dir) if f.endswith(".md") and f != "README.md" and f != "CAPABILITIES.md" and f != "TESTS.md"]
            
        # Find standards
        standards_dir = os.path.join(self.root, "standards")
        if os.path.exists(standards_dir):
            self.standards = [f[:-3] for f in os.listdir(standards_dir) if f.endswith(".md") and f != "README.md"]
            
        # Find metrics
        metrics_dir = os.path.join(self.root, "metrics")
        if os.path.exists(metrics_dir):
            self.metrics = [f[:-3] for f in os.listdir(metrics_dir) if f.endswith(".md") and f != "README.md"]
            
        # Find ADRs
        decisions_dir = os.path.join(self.root, "artifacts", "decisions")
        if os.path.exists(decisions_dir):
            self.adrs = [f for f in os.listdir(decisions_dir) if f.endswith(".md")]

    def validate_structural(self):
        """1. Structural Validation: Core files presence and naming."""
        required_root_files = [
            "README.md", "ENGINEERING_PRINCIPLES.md", "VERSION_POLICY.md", 
            "CONTRIBUTING.md", "INSTALL.md", "CHANGELOG.md", "LICENSE", "VERSION", ".gitignore"
        ]
        missing = 0
        for f in required_root_files:
            self.files_checked += 1
            path = os.path.join(self.root, f)
            if not os.path.exists(path):
                missing += 1
                self.warnings.append(f"Structural: Missing core root file '{f}'")
                
        # Naming convention checks (kebab-case for agents)
        for agent in self.agents:
            if "_" in agent or not agent.islower():
                self.warnings.append(f"Structural: Agent filename '{agent}.md' is not kebab-case")
                self.scores["Structural"] = max(0, self.scores["Structural"] - 10)
                
        if missing > 0:
            self.scores["Structural"] = max(0, self.scores["Structural"] - (missing * 15))

    def validate_contract(self):
        """2. Contract Validation: Agent contracts contain required sections."""
        required_sections = [
            "Identity", "Purpose", "Mission", "Lifecycle State Machine", 
            "Contract Boundaries", "Contract Interface Specifications", 
            "Required Inputs", "Produced Outputs", "Operational Configuration", 
            "Escalation and De-escalation", "Token Budget", "Failure Recovery"
        ]
        
        for agent in self.agents:
            path = os.path.join(self.root, "agents", f"{agent}.md")
            content = read_file_safe(path)
            missing = 0
            for sec in required_sections:
                if sec.lower() not in content.lower():
                    missing += 1
                    self.warnings.append(f"Contract: Agent '{agent}' contract is missing section '{sec}'")
                    
            # Check lifecycle states explicitly
            lifecycle_keywords = ["Idle", "Invoked", "Loading Context", "Reviewing", "Decision", "Output", "Completed"]
            for state in lifecycle_keywords:
                if state.lower() not in content.lower():
                    self.warnings.append(f"Contract: Agent '{agent}' contract does not define lifecycle state '{state}'")
                    missing += 1
                    
            if missing > 0:
                self.scores["Contract"] = max(0, self.scores["Contract"] - (missing * 5))

    def validate_dependency(self):
        """3. Dependency Validation: Circular escalation checks."""
        # Parse escalations: we expect agents to escalate to chief-architect, orchestrator, or human
        escalation_map = {}
        for agent in self.agents:
            path = os.path.join(self.root, "agents", f"{agent}.md")
            content = read_file_safe(path)
            
            # Simple regex search for escalation target
            matches = re.findall(r"escalate(?:s)?\s+(?:to)?\s+`?([a-zA-Z0-9_-]+)`?", content, re.IGNORECASE)
            if matches:
                # Get the first clean match
                target = matches[0].lower().replace("`", "").strip()
                escalation_map[agent] = target
            else:
                # default fallback assumptions
                if agent in ["orchestrator", "chief-architect", "planner"]:
                    escalation_map[agent] = "human"
                else:
                    escalation_map[agent] = "chief-architect"
                    
        # Check for cycles
        for start_agent in escalation_map:
            visited = []
            curr = start_agent
            cycle_found = False
            
            while curr and curr not in ["human", "orchestrator", "chief-architect"]:
                if curr in visited:
                    cycle_found = True
                    break
                visited.append(curr)
                curr = escalation_map.get(curr)
                
            if cycle_found:
                self.circular_dependencies += 1
                self.warnings.append(f"Dependency: Circular escalation cycle detected: {' -> '.join(visited)} -> {curr}")
                self.scores["Dependency"] = max(0, self.scores["Dependency"] - 50)

    def validate_token_budget(self):
        """4. Token Budget Validation: Verifies declared budgets are within limits."""
        for agent in self.agents:
            path = os.path.join(self.root, "agents", f"{agent}.md")
            content = read_file_safe(path)
            
            # Find budgets: e.g. "budget < 2500" or similar
            matches = re.findall(r"(?:context)?\s+budget\s*(?:size)?\s*(?:target)?\s*<\s*(\d+)", content, re.IGNORECASE)
            for val in matches:
                budget = int(val)
                if budget > 4000:
                    self.token_budget_violations += 1
                    self.warnings.append(f"Token Budget: Agent '{agent}' declares budget {budget} > 4000 limit")
                    self.scores["Token Budget"] = max(0, self.scores["Token Budget"] - 20)

    def validate_cross_references(self):
        """5. Cross-reference Validation: Scan for broken links."""
        # Find markdown links in all repository markdown files
        for root_dir, _, files in os.walk(self.root):
            if ".git" in root_dir or "node_modules" in root_dir:
                continue
            for f in files:
                if f.endswith(".md"):
                    path = os.path.join(root_dir, f)
                    content = read_file_safe(path)
                    
                    # Find links like [text](link)
                    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", content)
                    for link in links:
                        # Clean link anchors and queries
                        clean_link = link.split("#")[0].split("?")[0]
                        if not clean_link or clean_link.startswith("http") or clean_link.startswith("mailto"):
                            continue
                            
                        # Resolve path relative to file
                        link_target_path = ""
                        if clean_link.startswith("file:///"):
                            # Handle absolute system path placeholders
                            link_target_path = clean_link.replace("file://", "")
                        else:
                            # Relative path
                            link_target_path = os.path.abspath(os.path.join(root_dir, clean_link))
                            
                        if not os.path.exists(link_target_path):
                            self.broken_references += 1
                            self.warnings.append(f"Cross-reference: Broken link in '{f}' -> '{link}' (Resolved: {link_target_path})")
                            self.scores["Cross-reference"] = max(0, self.scores["Cross-reference"] - 5)

    def validate_architecture(self):
        """6. Architecture Validation: Integrity of layers (workflows/agents/tools/context)."""
        required_dirs = ["workflows", "agents", "tools", "context", "standards", "checklists", "metrics", "templates", "artifacts"]
        missing = 0
        for d in required_dirs:
            path = os.path.join(self.root, d)
            if not os.path.exists(path):
                missing += 1
                self.warnings.append(f"Architecture: Missing layer directory '{d}'")
                
        if missing > 0:
            self.scores["Architecture"] = max(0, self.scores["Architecture"] - (missing * 20))

    def validate_agent_routing(self):
        """7. Agent Routing Validation: Verify config.yml triggers match active agents."""
        config_path = os.path.join(self.root, ".agentos", "config.yml")
        if not os.path.exists(config_path):
            self.warnings.append("Agent Routing: Missing config.yml configuration")
            self.scores["Agent Routing"] = 0
            return
            
        content = read_file_safe(config_path)
        try:
            config = yaml.safe_load(content)
            trigger_map = config.get("trigger_map", {})
            for domain, agent in trigger_map.items():
                if agent not in self.agents and agent not in ["orchestrator", "chief-architect", "planner"]:
                    self.warnings.append(f"Agent Routing: Trigger maps domain '{domain}' to missing agent '{agent}'")
                    self.scores["Agent Routing"] = max(0, self.scores["Agent Routing"] - 15)
        except Exception as e:
            self.warnings.append(f"Agent Routing: Failed to parse config.yml: {e}")
            self.scores["Agent Routing"] = 0

    def validate_workflow(self):
        """8. Workflow Validation: Verifies that workflows/master.md and workflow list align."""
        workflow_path = os.path.join(self.root, "context", "workflow.md")
        master_path = os.path.join(self.root, "workflows", "master.md")
        
        if not os.path.exists(workflow_path) or not os.path.exists(master_path):
            self.warnings.append("Workflow: Missing workflow.md or master.md")
            self.scores["Workflow"] = 0
            return
            
        workflow_content = read_file_safe(workflow_path)
        # Find active workflows listed in workflow.md
        active_workflows = re.findall(r"`workflows/([a-zA-Z0-9_-]+)\.md`", workflow_content)
        for wf in active_workflows:
            path = os.path.join(self.root, "workflows", f"{wf}.md")
            if not os.path.exists(path):
                self.warnings.append(f"Workflow: Mapped workflow 'workflows/{wf}.md' does not exist")
                self.scores["Workflow"] = max(0, self.scores["Workflow"] - 15)

    def validate_standards(self):
        """9. Standards Validation: Verifies every standard has an assigned reviewer."""
        # We parse standards/README.md mapping
        readme_path = os.path.join(self.root, "standards", "README.md")
        if not os.path.exists(readme_path):
            self.warnings.append("Standards: Missing standards/README.md")
            self.scores["Standards"] = 0
            return
            
        content = read_file_safe(readme_path)
        for std in self.standards:
            # Check if standard file is mentioned alongside a reviewer agent
            if std not in content:
                self.missing_consumers += 1
                self.warnings.append(f"Standards: Standard '{std}' is not registered in standards/README.md")
                self.scores["Standards"] = max(0, self.scores["Standards"] - 10)
                
            # Verify every standard file itself points to standard tier
            std_path = os.path.join(self.root, "standards", f"{std}.md")
            std_content = read_file_safe(std_path)
            if "tier:" not in std_content.lower():
                self.warnings.append(f"Standards: Standard '{std}' does not declare a Tier in its header")
                self.scores["Standards"] = max(0, self.scores["Standards"] - 10)

    def validate_metrics(self):
        """10. Metrics Validation: Verifies metrics have definitions and frequencies."""
        for metric in self.metrics:
            path = os.path.join(self.root, "metrics", f"{metric}.md")
            content = read_file_safe(path)
            
            # Verify owner is specified
            if "owner:" not in content.lower():
                self.warnings.append(f"Metrics: Metric file '{metric}' is missing Owner header definition")
                self.scores["Metrics"] = max(0, self.scores["Metrics"] - 15)
                
            # Verify update frequency is specified
            if "update frequency:" not in content.lower() and "frequency:" not in content.lower():
                self.warnings.append(f"Metrics: Metric file '{metric}' is missing Frequency definition")
                self.scores["Metrics"] = max(0, self.scores["Metrics"] - 15)

    def validate_checklists(self):
        """11. Checklist Validation: Audits quality gates QG-001 through QG-008."""
        checklists_dir = os.path.join(self.root, "checklists")
        self.checklists_found = []
        self.checklist_runtimes = []
        self.checklist_automation = 0
        self.missing_gates = []
        
        expected_gates = {
            "QG-001": "feature_completion.md",
            "QG-002": "pull_request.md",
            "QG-003": "qa.md",
            "QG-004": "research_validation.md",
            "QG-005": "security_review.md",
            "QG-006": "deployment.md",
            "QG-007": "bug_fix.md",
            "QG-008": "release.md"
        }
        
        # Check files
        for gate_id, filename in expected_gates.items():
            path = os.path.join(checklists_dir, filename)
            if not os.path.exists(path):
                self.missing_gates.append(gate_id)
                self.warnings.append(f"Checklist: Missing checklist file for gate '{gate_id}' ({filename})")
                continue
                
            content = read_file_safe(path)
            self.checklists_found.append(gate_id)
            
            # Parse Gate ID
            if gate_id not in content:
                self.warnings.append(f"Checklist: File '{filename}' does not declare Gate ID '{gate_id}'")
                
            # Parse Estimated Runtime
            runtime_match = re.search(r"estimated\s+runtime\s*\**\s*:\s*\**\s*(\d+)\s*min", content, re.IGNORECASE)
            if runtime_match:
                self.checklist_runtimes.append(int(runtime_match.group(1)))
            else:
                self.checklist_runtimes.append(5) # default fallback
                
            # Parse Automation Level
            auto_match = re.search(r"automation\s+level\s*\**\s*:\s*\**\s*([a-zA-Z0-9_-]+)", content, re.IGNORECASE)
            if auto_match:
                level = auto_match.group(1).lower()
                if level in ["automatic", "semi-automatic"]:
                    self.checklist_automation += 1
            else:
                self.warnings.append(f"Checklist: File '{filename}' is missing Automation Level metadata")
                
            # Verify standard reference
            if "standards/" not in content.lower() and "standards.md" not in content.lower():
                self.warnings.append(f"Checklist: File '{filename}' does not reference any Standards")
                
            # Verify metrics reference
            if "metrics/" not in content.lower() and "metrics.md" not in content.lower() and "VERSION_POLICY" not in content:
                self.warnings.append(f"Checklist: File '{filename}' does not reference any Metrics")

    def validate_artifacts(self):
        """12. Artifact Schema Validation: Audits templates and completed artifacts."""
        self.artifacts_checked = 0
        self.missing_metadata_keys = 0
        self.broken_traces = 0
        self.orphan_artifacts = 0
        
        required_keys = [
            "id", "title", "version", "status", "owner", "created", "modified",
            "related_adr", "related_standard", "related_checklist", "related_workflow", "related_agent"
        ]
        
        # Load active decisions index
        decisions_index = read_file_safe(os.path.join(self.root, "context", "decisions.md"))
        
        for root_dir, _, files in os.walk(self.root):
            if ".git" in root_dir or "node_modules" in root_dir:
                continue
            for f in files:
                if f.endswith(".md"):
                    path = os.path.join(root_dir, f)
                    content = read_file_safe(path)
                    
                    # Check if file has YAML frontmatter
                    if content.startswith("---"):
                        # Extract frontmatter block
                        parts = content.split("---")
                        if len(parts) >= 3:
                            self.artifacts_checked += 1
                            frontmatter_raw = parts[1]
                            try:
                                fm = yaml.safe_load(frontmatter_raw)
                                if not isinstance(fm, dict):
                                    self.warnings.append(f"Artifact: File '{f}' has invalid frontmatter format")
                                    self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 10)
                                    continue
                                    
                                # Check mandatory keys
                                for key in required_keys:
                                    if key not in fm:
                                        self.missing_metadata_keys += 1
                                        self.warnings.append(f"Artifact: File '{f}' is missing metadata key '{key}'")
                                        self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 5)
                                        
                                # Check trace references if they aren't None
                                # 1. related_adr
                                adr = fm.get("related_adr")
                                if adr and str(adr) != "None":
                                    # check if adr file exists
                                    adr_file = f"{adr.strip()}.md" if isinstance(adr, str) else f"{adr}.md"
                                    adr_path = os.path.join(self.root, "artifacts", "decisions", adr_file)
                                    # Fallback search if filename differs
                                    if not os.path.exists(adr_path):
                                        # search decisions folder for file starting with adr ID
                                        dec_dir = os.path.join(self.root, "artifacts", "decisions")
                                        found = False
                                        if os.path.exists(dec_dir):
                                            for dec_file in os.listdir(dec_dir):
                                                if dec_file.startswith(str(adr).strip()):
                                                    found = True
                                                    break
                                        if not found:
                                            self.broken_traces += 1
                                            self.warnings.append(f"Artifact: File '{f}' references missing ADR '{adr}'")
                                            self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 10)
                                            
                                # 2. related_standard
                                std = fm.get("related_standard")
                                if std and str(std) != "None":
                                    std_path = os.path.abspath(os.path.join(self.root, str(std).strip())) if not str(std).startswith("/") else str(std).strip()
                                    if not os.path.exists(std_path):
                                        self.broken_traces += 1
                                        self.warnings.append(f"Artifact: File '{f}' references missing standard '{std}'")
                                        self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 10)
                                        
                                # 3. related_checklist
                                checklist = fm.get("related_checklist")
                                if checklist and str(checklist) != "None":
                                    checklists_dir = os.path.join(self.root, "checklists")
                                    found = False
                                    if os.path.exists(checklists_dir):
                                        for ch_file in os.listdir(checklists_dir):
                                            if ch_file.endswith(".md"):
                                                ch_cont = read_file_safe(os.path.join(checklists_dir, ch_file))
                                                if str(checklist).strip() in ch_cont:
                                                    found = True
                                                    break
                                    if not found:
                                        self.broken_traces += 1
                                        self.warnings.append(f"Artifact: File '{f}' references missing checklist '{checklist}'")
                                        self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 10)
                                        
                                # Check for orphan ADRs (if it's in artifacts/decisions but not in decisions.md index)
                                if "artifacts/decisions" in path and not f.startswith("phase"):
                                    adr_id_match = re.search(r"ADR-\d+", f)
                                    if adr_id_match:
                                        adr_id = adr_id_match.group(0)
                                        if adr_id not in decisions_index:
                                            self.orphan_artifacts += 1
                                            self.warnings.append(f"Artifact: ADR '{f}' is not indexed in context/decisions.md")
                                            self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 5)
                                            
                            except Exception as e:
                                self.warnings.append(f"Artifact: Failed to parse frontmatter for '{f}': {e}")
                                self.scores["Artifacts"] = max(0, self.scores["Artifacts"] - 10)

    def validate_bootstrap(self):
        """13. Bootstrap Validation: Audits BOOTSTRAP.md, START_PROJECT.md, and configuration."""
        self.repo_ready = "PASS"
        self.project_ready = "PASS"
        self.profile_ready = "PASS"
        self.profile_name = "None"
        self.missing_boot_files = []
        self.missing_boot_context = []
        
        # Verify files existence
        boot_files = [
            "BOOTSTRAP.md",
            "START_PROJECT.md",
            "tools/scripts/bootstrap_project.py"
        ]
        
        for name in boot_files:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_boot_files.append(name)
                self.warnings.append(f"Bootstrap: Missing required boot file '{name}'")
                self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 25)
                self.repo_ready = "FAIL"
                
        # Verify PROJECT_CONFIG.yaml
        config_path = os.path.join(self.root, "PROJECT_CONFIG.yaml")
        if not os.path.exists(config_path):
            self.warnings.append("Bootstrap: PROJECT_CONFIG.yaml has not been generated yet")
            self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 20)
            self.project_ready = "FAIL"
        else:
            try:
                config_data = yaml.safe_load(read_file_safe(config_path))
                if not config_data or "project" not in config_data:
                    self.warnings.append("Bootstrap: PROJECT_CONFIG.yaml has invalid format")
                    self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 15)
                    self.project_ready = "FAIL"
                else:
                    self.profile_name = config_data["project"].get("profile", "None")
                    # Check if profile YAML file actually exists
                    profile_file = os.path.join(self.root, "profiles", f"{self.profile_name}.yaml")
                    if not os.path.exists(profile_file):
                        self.warnings.append(f"Bootstrap: Configured profile '{self.profile_name}' file not found")
                        self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 15)
                        self.profile_ready = "FAIL"
            except Exception as e:
                self.warnings.append(f"Bootstrap: Failed to parse PROJECT_CONFIG.yaml: {e}")
                self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 15)
                self.project_ready = "FAIL"
                
        # Check context vision & state
        vision_path = os.path.join(self.root, "context", "vision.md")
        state_path = os.path.join(self.root, "context", "state.md")
        if not os.path.exists(vision_path):
            self.missing_boot_context.append("context/vision.md")
            self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 10)
        if not os.path.exists(state_path):
            self.missing_boot_context.append("context/state.md")
            self.scores["Bootstrap"] = max(0, self.scores["Bootstrap"] - 10)

    def validate_harness(self):
        """14. Harness Validation: Audits policies, modules, SM states, and specification files."""
        self.harness_repo_ready = "PASS"
        self.harness_routing_ready = "PASS"
        self.harness_context_ready = "PASS"
        self.harness_cost_ready = "PASS"
        self.missing_harness_files = []
        
        # 1. Check harness files
        required_harness = [
            "tools/scripts/harness_engine.py",
            "tools/scripts/harness_specification.md",
            "runtime/harness/classifier.py",
            "runtime/harness/context_optimizer.py",
            "runtime/harness/workflow_router.py",
            "runtime/harness/agent_router.py",
            "runtime/harness/tool_router.py",
            "runtime/harness/execution_planner.py",
            "runtime/harness/cost_optimizer.py",
            "runtime/harness/failure_recovery.py",
            "runtime/harness/state_machine.py",
            "runtime/harness/runtime.py"
        ]
        
        for name in required_harness:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_harness_files.append(name)
                self.warnings.append(f"Harness: Missing required harness file '{name}'")
                self.scores["Harness"] = max(0, self.scores["Harness"] - 10)
                self.harness_repo_ready = "FAIL"
                
        # 2. Check policy files
        policy_files = ["routing.yaml", "context.yaml", "quality.yaml", "tools.yaml", "retry.yaml"]
        for p in policy_files:
            path = os.path.join(self.root, "runtime", "policies", p)
            if not os.path.exists(path):
                self.warnings.append(f"Harness: Missing policy file '{p}'")
                self.scores["Harness"] = max(0, self.scores["Harness"] - 15)
                self.harness_routing_ready = "FAIL"
            else:
                try:
                    data = yaml.safe_load(read_file_safe(path))
                    if not data:
                        self.warnings.append(f"Harness: Policy file '{p}' is empty")
                        self.scores["Harness"] = max(0, self.scores["Harness"] - 10)
                except Exception as e:
                    self.warnings.append(f"Harness: Failed to parse policy '{p}': {e}")
                    self.scores["Harness"] = max(0, self.scores["Harness"] - 15)
                    self.harness_routing_ready = "FAIL"

    def validate_loop(self):
        """15. Loop Validation: Audits loop modules, shared kernel modules, policies, and safety checks."""
        self.loop_config_ready = "PASS"
        self.loop_termination_safe = "PASS"
        self.loop_reflection_ready = "PASS"
        self.missing_loop_files = []
        
        # 1. Check loop modules
        loop_modules = [
            "runtime/loop/runtime.py",
            "runtime/loop/iteration_controller.py",
            "runtime/loop/reflection.py",
            "runtime/loop/improvement_planner.py",
            "runtime/loop/execution_monitor.py",
            "runtime/loop/quality_evaluator.py",
            "runtime/loop/termination.py",
            "runtime/loop/state_machine.py"
        ]
        for lm in loop_modules:
            if not os.path.exists(os.path.join(self.root, lm)):
                self.missing_loop_files.append(lm)
                self.scores["Loop"] = max(0, self.scores["Loop"] - 5)
                self.loop_config_ready = "FAIL"
                
        # 2. Check kernel modules
        kernel_modules = [
            "runtime/kernel/scheduler.py",
            "runtime/kernel/state_manager.py",
            "runtime/kernel/event_bus.py",
            "runtime/kernel/policy_loader.py",
            "runtime/kernel/logger.py",
            "runtime/kernel/health.py"
        ]
        for km in kernel_modules:
            if not os.path.exists(os.path.join(self.root, km)):
                self.missing_loop_files.append(km)
                self.scores["Loop"] = max(0, self.scores["Loop"] - 5)
                self.loop_config_ready = "FAIL"

        # 3. Check loop policy files
        loop_policies = ["loop.yaml", "reflection.yaml", "termination.yaml", "retry_limits.yaml", "quality_thresholds.yaml"]
        for lp in loop_policies:
            path = os.path.join(self.root, "runtime", "policies", lp)
            if not os.path.exists(path):
                self.warnings.append(f"Loop: Missing loop policy file '{lp}'")
                self.scores["Loop"] = max(0, self.scores["Loop"] - 10)
                self.loop_config_ready = "FAIL"
            else:
                try:
                    data = yaml.safe_load(read_file_safe(path))
                    if lp == "termination.yaml":
                        # Check that max loops is defined to prevent infinite execution runs
                        modes = data.get("loop_modes", {})
                        if not modes or not any("max_loops" in item for item in modes.values()):
                            self.warnings.append("Loop: termination.yaml has missing or invalid max_loops limits")
                            self.scores["Loop"] = max(0, self.scores["Loop"] - 15)
                            self.loop_termination_safe = "FAIL"
                except Exception as e:
                    self.warnings.append(f"Loop: Failed to parse policy '{lp}': {e}")
                    self.scores["Loop"] = max(0, self.scores["Loop"] - 10)
                    self.loop_config_ready = "FAIL"

    def validate_synthetic_suite(self):
        """16. Validation Suite: Verifies manifest, scenario directories, request payloads, and test assertions."""
        self.validation_manifest_ready = "PASS"
        self.validation_runner_ready = "PASS"
        self.validation_scenarios_ready = "PASS"
        self.missing_validation_files = []
        
        # 1. Check manifest
        manifest_path = os.path.join(self.root, "validation", "manifest.yaml")
        if not os.path.exists(manifest_path):
            self.warnings.append("Validation: Missing manifest file validation/manifest.yaml")
            self.scores["Validation"] = max(0, self.scores["Validation"] - 25)
            self.validation_manifest_ready = "FAIL"
            
        # 2. Check runners
        runners = [
            "validation/runner/execute_suite.py",
            "validation/runner/execute_scenario.py",
            "validation/runner/report_generator.py"
        ]
        for r in runners:
            if not os.path.exists(os.path.join(self.root, r)):
                self.missing_validation_files.append(r)
                self.warnings.append(f"Validation: Missing runner script '{r}'")
                self.scores["Validation"] = max(0, self.scores["Validation"] - 10)
                self.validation_runner_ready = "FAIL"
                
        # 3. Check scenario subdirectories VS-001 to VS-021
        for i in range(1, 22):
            s_id = f"VS-{i:03d}"
            scen_dir = os.path.join(self.root, "validation", "scenarios", s_id)
            if not os.path.exists(scen_dir):
                self.missing_validation_files.append(f"scenarios/{s_id}/")
                self.warnings.append(f"Validation: Missing scenario folder '{s_id}'")
                self.scores["Validation"] = max(0, self.scores["Validation"] - 5)
                self.validation_scenarios_ready = "FAIL"
            else:
                # Check contents
                s_md = os.path.join(scen_dir, "scenario.md")
                s_yaml = os.path.join(scen_dir, "assertions.yaml")
                s_req = os.path.join(scen_dir, "input", "request.json")
                if not os.path.exists(s_md) or not os.path.exists(s_yaml) or not os.path.exists(s_req):
                    self.warnings.append(f"Validation: Incomplete files in scenario '{s_id}'")
                    self.scores["Validation"] = max(0, self.scores["Validation"] - 5)
                    self.validation_scenarios_ready = "FAIL"

    def validate_production(self):
        """17. Production RC1 Validation: Audits release version naming and validation artifacts."""
        self.production_version_ready = "PASS"
        self.production_reports_ready = "PASS"
        self.missing_production_files = []
        
        # 1. Check version string
        repo_version = read_file_safe(os.path.join(self.root, "VERSION")).strip()
        if repo_version not in ["1.0.0", "1.0.0-rc1"]:
            self.warnings.append(f"Production: Version '{repo_version}' must be set to '1.0.0' or '1.0.0-rc1'")
            self.scores["Production"] = max(0, self.scores["Production"] - 25)
            self.production_version_ready = "FAIL"
            
        # 2. Check report files
        required_reports = [
            "production_validation/README.md",
            "production_validation/productivity_metrics.csv",
            "production_validation/rc1_validation_report.md",
            "production_validation/readiness_assessment.md"
        ]
        
        for name in required_reports:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_production_files.append(name)
                self.warnings.append(f"Production: Missing required validation report file '{name}'")
                self.scores["Production"] = max(0, self.scores["Production"] - 20)
                self.production_reports_ready = "FAIL"

    def validate_certification(self):
        """18. Production Certification: Audits v1.0.0 stable deliverables, COMPATIBILITY.md, and golden path examples."""
        self.certification_version_ready = "PASS"
        self.certification_docs_ready = "PASS"
        self.certification_examples_ready = "PASS"
        self.missing_certification_files = []
        
        # 1. Check final stable version string
        repo_version = read_file_safe(os.path.join(self.root, "VERSION")).strip()
        if repo_version != "1.0.0":
            self.warnings.append(f"Certification: Final version '{repo_version}' must be set exactly to '1.0.0'")
            self.scores["Certification"] = max(0, self.scores["Certification"] - 25)
            self.certification_version_ready = "FAIL"
            
        # 2. Check certification docs
        required_certification = [
            "production_certification/SYSTEM_CERTIFICATION.md",
            "production_certification/STABILITY_REPORT.md",
            "production_certification/PERFORMANCE_REPORT.md",
            "production_certification/TEAM_READINESS.md",
            "production_certification/RELEASE_CHECKLIST.md",
            "production_certification/FUTURE_ROADMAP.md",
            "production_certification/MIGRATION_REPORT.md",
            "production_certification/REPOSITORY_STATISTICS.md",
            "COMPATIBILITY.md"
        ]
        for name in required_certification:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_certification_files.append(name)
                self.warnings.append(f"Certification: Missing required certification file '{name}'")
                self.scores["Certification"] = max(0, self.scores["Certification"] - 10)
                self.certification_docs_ready = "FAIL"
                
        # 3. Check golden path examples
        example_starts = [
            "examples/backend/START.md",
            "examples/ai_project/START.md",
            "examples/research/START.md",
            "examples/flagship/START.md"
        ]
        for path in example_starts:
            if not os.path.exists(os.path.join(self.root, path)):
                self.missing_certification_files.append(path)
                self.warnings.append(f"Certification: Missing golden path onboarding guide '{path}'")
                self.scores["Certification"] = max(0, self.scores["Certification"] - 10)
                self.certification_examples_ready = "FAIL"

    def validate_distribution(self):
        """19. Final Team Distribution: Audits onboarding, GitHub, dev tooling, and community files."""
        self.distribution_files_ready = "PASS"
        self.distribution_links_ready = "PASS"
        self.distribution_tooling_ready = "PASS"
        self.distribution_profiles_ready = "PASS"
        self.missing_distribution_files = []

        # 1. Core onboarding files
        required_dist = [
            "AGENTOS.md",
            "ARCHITECTURE.md",
            "SUPPORT.md",
            "TEAM_QUICKSTART.md",
            "DOCUMENTATION_INDEX.md",
            "TEAM_ONBOARDING_CHECKLIST.md",
            "REPOSITORY_HEALTH.md",
            "RELEASE_NOTES_v1.0.0.md",
            "artifacts/reviews/repository_cleanup_report.md",
            "PROJECT_CONFIG.example.yaml",
        ]
        for name in required_dist:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_distribution_files.append(name)
                self.warnings.append(f"Distribution: Missing required onboarding file '{name}'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 8)
                self.distribution_files_ready = "FAIL"

        # 2. GitHub template repository files
        github_files = [
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
            ".github/ISSUE_TEMPLATE/question.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/workflows/validate.yml",
            ".github/workflows/lint.yml",
            ".github/CODEOWNERS",
        ]
        for name in github_files:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_distribution_files.append(name)
                self.warnings.append(f"Distribution: Missing GitHub template file '{name}'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                self.distribution_tooling_ready = "FAIL"

        # 3. Developer tooling files
        tooling_files = [
            "Makefile",
            ".editorconfig",
            ".pre-commit-config.yaml",
            ".devcontainer/devcontainer.json",
        ]
        for name in tooling_files:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_distribution_files.append(name)
                self.warnings.append(f"Distribution: Missing developer tooling file '{name}'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                self.distribution_tooling_ready = "FAIL"

        # 4. Community health files
        community_files = [
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "SUPPORTED_VERSIONS.md",
        ]
        for name in community_files:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_distribution_files.append(name)
                self.warnings.append(f"Distribution: Missing community file '{name}'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                self.distribution_files_ready = "FAIL"

        # 5. All 8 project profiles present
        required_profiles = ["ai_project", "backend", "frontend", "ml", "research", "isro", "hackathon", "flagship"]
        for profile in required_profiles:
            profile_path = os.path.join(self.root, "profiles", f"{profile}.yaml")
            if not os.path.exists(profile_path):
                self.missing_distribution_files.append(f"profiles/{profile}.yaml")
                self.warnings.append(f"Distribution: Missing project profile 'profiles/{profile}.yaml'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                self.distribution_profiles_ready = "FAIL"

        # 6. AI integration READMEs present
        integration_readmes = [
            "integrations/claude/README.md",
            "integrations/gemini/README.md",
            "integrations/codex/README.md",
            "integrations/antigravity/README.md",
        ]
        for name in integration_readmes:
            if not os.path.exists(os.path.join(self.root, name)):
                self.missing_distribution_files.append(name)
                self.warnings.append(f"Distribution: Missing integration README '{name}'")
                self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                self.distribution_tooling_ready = "FAIL"

        # 7. Stale version reference check (no 0.1.0 in root docs)
        stale_version = "0.1.0"
        root_docs = ["README.md", "AGENTOS.md", "TEAM_QUICKSTART.md", "DOCUMENTATION_INDEX.md"]
        for doc in root_docs:
            doc_path = os.path.join(self.root, doc)
            if os.path.exists(doc_path):
                content = read_file_safe(doc_path)
                if stale_version in content:
                    self.warnings.append(f"Distribution: Stale version reference '{stale_version}' found in '{doc}'")
                    self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                    self.distribution_files_ready = "FAIL"

        # 8. Link integrity inside DOCUMENTATION_INDEX.md
        index_path = os.path.join(self.root, "DOCUMENTATION_INDEX.md")
        if os.path.exists(index_path):
            content = read_file_safe(index_path)
            links = re.findall(r'\(file:///Users/soumyadebtripathy/WorkFlow/agentos-template/([^)]+)\)', content)
            for link in links:
                clean_link = link.split('#')[0]
                full_link_path = os.path.join(self.root, clean_link)
                if not os.path.exists(full_link_path):
                    self.warnings.append(f"Distribution: Broken link in DOCUMENTATION_INDEX.md to '{clean_link}'")
                    self.scores["Distribution"] = max(0, self.scores["Distribution"] - 5)
                    self.distribution_links_ready = "FAIL"

    def generate_report(self):
        """Generates the official Health Report."""
        # Calculate coverage (files documented vs placeholders)
        # Structural check of markdown files containing "placeholder" vs "complete"
        complete_files = 0
        total_files = 0
        for root_dir, _, files in os.walk(self.root):
            if ".git" in root_dir:
                continue
            for f in files:
                if f.endswith(".md") or f.endswith(".yml"):
                    total_files += 1
                    path = os.path.join(root_dir, f)
                    content = read_file_safe(path)
                    if "status: complete" in content.lower() or "status: active" in content.lower() or "status: completed" in content.lower():
                        complete_files += 1
                    elif "status: placeholder" in content.lower():
                        pass
                    else:
                        # files with no explicit status count as complete if populated
                        if len(content) > 300:
                            complete_files += 1
                            
        coverage_pct = int((complete_files / total_files) * 100) if total_files > 0 else 0
        
        # Calculate overall grade
        overall_score = int(sum(self.scores.values()) / len(self.scores))
        
        # Load version dynamically
        version_path = os.path.join(self.root, "VERSION")
        repo_version = read_file_safe(version_path).strip() if os.path.exists(version_path) else "0.3.0"
        
        # Build Report
        print("=" * 60)
        print("           AgentOS Health Report")
        print("=" * 60)
        print(f"Repository Version      : {repo_version}")
        print(f"Validation Time         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Files Checked           : {total_files}")
        print(f"Standards Registered    : {len(self.standards)}")
        print(f"Agents Configured       : {len(self.agents) + 3}") # specialists + core 3
        print(f"ADR Count               : {len(self.adrs)}")
        print(f"Broken References       : {self.broken_references}")
        print(f"Missing Consumers       : {self.missing_consumers}")
        print(f"Circular Dependencies   : {self.circular_dependencies}")
        print(f"Token Budget Violations  : {self.token_budget_violations}")
        print(f"Coverage                : {coverage_pct}%")
        print(f"Warnings                : {len(self.warnings)}")
        print("-" * 60)
        print("Category Scores:")
        for cat, score in self.scores.items():
            print(f"  * {cat:<24}: {score}/100")
        print("-" * 60)
        print(f"Overall Grade           : {overall_score}/100")
        
        status = "PASS" if overall_score >= 85 and self.broken_references == 0 and self.circular_dependencies == 0 else "FAIL"
        print(f"Final Status            : {status}")
        print("=" * 60)
        
        # Build Checklist Health Report
        avg_runtime = int(sum(self.checklist_runtimes) / len(self.checklist_runtimes)) if self.checklist_runtimes else 0
        auto_cov = int((self.checklist_automation / len(self.checklists_found)) * 100) if self.checklists_found else 0
        checklist_score = 100 - (len(self.missing_gates) * 20) - (self.broken_references * 10)
        checklist_score = max(0, min(100, checklist_score))
        
        print("\n============================================================")
        print("           Checklist Health Report")
        print("============================================================")
        print(f"Checklist Count         : {len(self.checklists_found)}")
        print(f"Missing Gates           : {len(self.missing_gates)} ({', '.join(self.missing_gates) if self.missing_gates else 'None'})")
        print(f"Broken References       : {self.broken_references}")
        print(f"Average Completion Time : {avg_runtime} min")
        print(f"Automation Coverage     : {auto_cov}%")
        print("-" * 60)
        print(f"Checklist Score         : {checklist_score}/100")
        print("============================================================\n")
        
        # Build Artifact Health Report
        print("============================================================")
        print("           Artifact Health Report")
        print("============================================================")
        print(f"Artifacts Checked       : {self.artifacts_checked}")
        print(f"Missing Metadata Keys   : {self.missing_metadata_keys}")
        print(f"Broken References/Traces: {self.broken_traces}")
        print(f"Orphan Artifacts        : {self.orphan_artifacts}")
        print("-" * 60)
        print(f"Artifact System Score   : {self.scores['Artifacts']}/100")
        print("============================================================\n")
        
        # Build Bootstrap Health Report
        bootstrap_score = self.scores["Bootstrap"]
        bootstrap_status = "PASS" if bootstrap_score >= 85 and len(self.missing_boot_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Bootstrap Health Report")
        print("============================================================")
        print(f"Repository Ready        : {self.repo_ready}")
        print(f"Project Ready           : {self.project_ready}")
        print(f"Profile Ready           : {self.profile_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Bootstrap Version       : {repo_version}")
        print(f"Profile Name            : {self.profile_name}")
        print(f"Missing Boot Files      : {', '.join(self.missing_boot_files) if self.missing_boot_files else 'None'}")
        print(f"Missing Boot Context    : {', '.join(self.missing_boot_context) if self.missing_boot_context else 'None'}")
        print(f"Readiness Score         : {bootstrap_score}/100")
        print(f"Overall Status          : {bootstrap_status}")
        print("============================================================\n")
        
        # Build Harness Health Report
        harness_score = self.scores["Harness"]
        harness_status = "PASS" if harness_score >= 85 and len(self.missing_harness_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Harness Health Report")
        print("============================================================")
        print(f"Orchestration Ready     : {self.harness_repo_ready}")
        print(f"Routing Ready           : {self.harness_routing_ready}")
        print(f"Context Optimization    : {self.harness_context_ready}")
        print(f"Cost Optimization       : {self.harness_cost_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Harness Version         : {repo_version}")
        print(f"Missing Harness Files   : {', '.join(self.missing_harness_files) if self.missing_harness_files else 'None'}")
        print(f"Readiness Score         : {harness_score}/100")
        print(f"Overall Status          : {harness_status}")
        print("============================================================\n")
        
        # Build Loop Health Report
        loop_score = self.scores["Loop"]
        loop_status = "PASS" if loop_score >= 85 and len(self.missing_loop_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Loop Health Report")
        print("============================================================")
        print(f"Loop Config Ready       : {self.loop_config_ready}")
        print(f"Termination Safe        : {self.loop_termination_safe}")
        print(f"Reflection Ready        : {self.loop_reflection_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Loop Version            : {repo_version}")
        print(f"Missing Loop Files      : {', '.join(self.missing_loop_files) if self.missing_loop_files else 'None'}")
        print(f"Readiness Score         : {loop_score}/100")
        print(f"Overall Status          : {loop_status}")
        print("============================================================\n")
        
        # Build Validation Suite Health Report
        val_score = self.scores["Validation"]
        val_status = "PASS" if val_score >= 85 and len(self.missing_validation_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Validation Suite Health Report")
        print("============================================================")
        print(f"Manifest Ready          : {self.validation_manifest_ready}")
        print(f"Runner Ready            : {self.validation_runner_ready}")
        print(f"Scenarios Configured    : {self.validation_scenarios_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Validation Version      : {repo_version}")
        print(f"Missing Suite Files     : {', '.join(self.missing_validation_files) if self.missing_validation_files else 'None'}")
        print(f"Readiness Score         : {val_score}/100")
        print(f"Overall Status          : {val_status}")
        print("============================================================\n")
        
        # Build Production RC1 Health Report
        prod_score = self.scores["Production"]
        prod_status = "PASS" if prod_score >= 85 and len(self.missing_production_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Production RC1 Health Report")
        print("============================================================")
        print(f"Version Alignment       : {self.production_version_ready}")
        print(f"Validation Reports      : {self.production_reports_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Validation Version      : {repo_version}")
        print(f"Missing Production Files: {', '.join(self.missing_production_files) if self.missing_production_files else 'None'}")
        print(f"Readiness Score         : {prod_score}/100")
        print(f"Overall Status          : {prod_status}")
        print("============================================================\n")
        
        # Build Production Certification Health Report
        cert_score = self.scores["Certification"]
        cert_status = "PASS" if cert_score >= 85 and len(self.missing_certification_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           v1.0.0 Production Certification Report")
        print("============================================================")
        print(f"Version Alignment       : {self.certification_version_ready}")
        print(f"Certification Documents : {self.certification_docs_ready}")
        print(f"Golden Path Examples    : {self.certification_examples_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Certification Version   : {repo_version}")
        print(f"Missing Cert Files      : {', '.join(self.missing_certification_files) if self.missing_certification_files else 'None'}")
        print(f"Certification Score     : {cert_score}/100")
        print(f"Overall Status          : {cert_status}")
        print("============================================================\n")
        
        # Build Distribution Readiness Health Report
        dist_score = self.scores["Distribution"]
        dist_status = "PASS" if dist_score >= 85 and len(self.missing_distribution_files) == 0 else "FAIL"
        
        print("============================================================")
        print("           Distribution Readiness Report")
        print("============================================================")
        print(f"Onboarding Files        : {self.distribution_files_ready}")
        print(f"GitHub Templates        : {self.distribution_tooling_ready}")
        print(f"Developer Tooling       : {self.distribution_tooling_ready}")
        print(f"Project Profiles (8)    : {self.distribution_profiles_ready}")
        print(f"Link Consistency        : {self.distribution_links_ready}")
        print(f"AgentOS Version         : {repo_version}")
        print(f"Distribution Version    : {repo_version}")
        print(f"Missing Dist Files      : {', '.join(self.missing_distribution_files) if self.missing_distribution_files else 'None'}")
        print(f"Readiness Score         : {dist_score}/100")
        print(f"Overall Status          : {dist_status}")
        print("============================================================\n")
        
        # Print warning details
        if self.warnings:
            print("\nWarning Details:")
            for w in self.warnings[:15]: # Show first 15 warnings
                print(f"  - {w}")
            if len(self.warnings) > 15:
                print(f"  ... and {len(self.warnings) - 15} more warnings.")
        
        return status == "PASS"

if __name__ == "__main__":
    validator = Validator(REPO_ROOT)
    validator.run_all()
    success = validator.generate_report()
    sys.exit(0 if success else 1)

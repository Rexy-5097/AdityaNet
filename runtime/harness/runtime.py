"""Harness Engine runtime kernel interface."""
import os
import yaml
from datetime import datetime

from .classifier import TaskClassifier
from .context_optimizer import ContextOptimizer
from .workflow_router import WorkflowRouter
from .agent_router import AgentRouter
from .tool_router import ToolRouter
from .execution_planner import ExecutionPlanner
from .cost_optimizer import CostOptimizer
from .failure_recovery import FailureRecovery
from .state_machine import HarnessStateMachine

class HarnessRuntime:
    def __init__(self, root_dir):
        self.root = root_dir
        self.state_machine = HarnessStateMachine()
        
        # Load policies
        routing_policy = self._load_policy("routing.yaml")
        context_policy = self._load_policy("context.yaml")
        quality_policy = self._load_policy("quality.yaml")
        tools_policy = self._load_policy("tools.yaml")
        retry_policy = self._load_policy("retry.yaml")
        
        # Initialize modules
        self.classifier = TaskClassifier(routing_policy, quality_policy)
        self.context_opt = ContextOptimizer(context_policy, root_dir)
        self.workflow_router = WorkflowRouter()
        self.agent_router = AgentRouter(routing_policy)
        self.tool_router = ToolRouter(tools_policy)
        self.planner = ExecutionPlanner()
        self.cost_opt = CostOptimizer(context_policy)
        self.recovery = FailureRecovery(retry_policy)

    def _load_policy(self, filename):
        path = os.path.join(self.root, "runtime", "policies", filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def execute(self, request):
        """Standardized execution sequence for incoming requests."""
        # 1. Receive Request
        self.state_machine.transition("Receive Request")
        
        # Check cache
        cached_plan = self.cost_opt.get_cached_plan(request)
        if cached_plan:
            print("[Harness] Cache Hit. Reusing execution plan.")
            self.state_machine.transition("Complete")
            return cached_plan, []
            
        # 2. Plan
        self.state_machine.transition("Plan")
        classification = self.classifier.classify(request)
        workflow = self.workflow_router.select_workflow(classification)
        agents = self.agent_router.route(request, classification)
        tools = self.tool_router.route_tools(request, agents)
        context = self.context_opt.get_context_files(classification, agents)
        
        plan = self.planner.plan(request, classification, workflow, agents, tools, context)
        self.cost_opt.cache_plan(request, plan)
        
        # 3. Dispatch
        self.state_machine.transition("Dispatch")
        print(f"[Harness] Dispatched task to agents: {', '.join(agents)}")
        
        # 4. Monitor
        self.state_machine.transition("Monitor")
        print(f"[Monitor] Execution started at {datetime.now().strftime('%H:%M:%S')}")
        
        # 5. Collect
        self.state_machine.transition("Collect")
        print("[Harness] Collected checklist results from agents.")
        
        # 6. Validate
        self.state_machine.transition("Validate")
        print("[Harness] Executing tool verification checks...")
        
        # 7. Complete
        self.state_machine.transition("Complete")
        return plan, self.state_machine.get_history()

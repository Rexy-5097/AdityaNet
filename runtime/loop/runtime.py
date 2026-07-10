"""Loop Engine runtime module coordinating the iteration execution loop."""
import os
from datetime import datetime

from runtime.kernel.policy_loader import PolicyLoader
from .state_machine import LoopStateMachine
from .iteration_controller import IterationController
from .reflection import ReflectionEngine
from .improvement_planner import ImprovementPlanner
from .execution_monitor import ExecutionMonitor
from .quality_evaluator import QualityEvaluator
from .termination import LoopTermination

class LoopRuntime:
    def __init__(self, root_dir):
        self.root = root_dir
        self.state_machine = LoopStateMachine()
        
        # Load policies
        loader = PolicyLoader(root_dir)
        loop_policy = loader.load("loop.yaml")
        reflection_policy = loader.load("reflection.yaml")
        termination_policy = loader.load("termination.yaml")
        thresholds_policy = loader.load("quality_thresholds.yaml")
        
        # Initialize modules
        self.iteration_controller = IterationController()
        self.reflection = ReflectionEngine(reflection_policy)
        self.planner = ImprovementPlanner()
        self.monitor = ExecutionMonitor(termination_policy)
        self.evaluator = QualityEvaluator(thresholds_policy)
        self.termination = LoopTermination(termination_policy)

    def execute_loop(self, plan, loop_mode="Balanced"):
        """Coordinates the complete loop lifecycle."""
        # 1. Receive Plan
        self.state_machine.transition("Receive Plan")
        
        termination_reason = "COMPLETED"
        max_loops = 3
        
        while True:
            self.monitor.start_loop()
            
            # 2. Execute Cycle
            self.state_machine.transition("Execute Cycle")
            print(f"[Loop] Running iteration {self.monitor.loop_count}...")
            
            # 3. Evaluate Quality
            self.state_machine.transition("Evaluate Quality")
            # Mock evaluation for demonstration
            # In first iteration we simulate a minor failure if task is complex
            errs = ["ImportError: missing auth database dependency"] if self.monitor.loop_count == 1 and "auth" in str(plan).lower() else []
            eval_result = self.evaluator.evaluate(len(errs) == 0, len(errs))
            
            iter_info = self.iteration_controller.log_iteration(
                eval_result["score"],
                eval_result["confidence"],
                120, # mock token cost
                1.5  # mock duration
            )
            
            # 4. Validate
            self.state_machine.transition("Validate")
            
            # Check termination conditions
            monitor_status = self.monitor.evaluate_limits(loop_mode)
            stop, reason = self.termination.check_termination(
                monitor_status, eval_result, self.iteration_controller.iterations, loop_mode
            )
            
            if stop:
                termination_reason = reason
                break
                
            # 5. Reflect
            self.state_machine.transition("Reflect")
            ref_report = self.reflection.analyze_failure(iter_info, errs)
            print(f"[Reflection] Root cause identified: {ref_report['root_cause_category']}")
            
            # 6. Plan Improvement
            self.state_machine.transition("Plan Improvement")
            strategy = self.planner.select_strategy(ref_report)
            print(f"[Planner] Selected mode strategy: {strategy}")
            
            # 7. Monitor Execution
            self.state_machine.transition("Monitor Execution")

        # 8. Complete
        self.state_machine.transition("Complete")
        
        return {
            "iterations": self.iteration_controller.iterations,
            "termination_reason": termination_reason,
            "history": self.state_machine.get_history()
        }

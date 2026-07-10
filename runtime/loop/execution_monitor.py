"""Execution monitor tracking times and loop counts."""
import time

class ExecutionMonitor:
    def __init__(self, termination_policy):
        self.policy = termination_policy
        self.start_time = time.time()
        self.loop_count = 0

    def start_loop(self):
        self.loop_count += 1

    def evaluate_limits(self, loop_mode="Balanced"):
        """Ensures loop execution limits are safe."""
        elapsed = time.time() - self.start_time
        
        # Load mode limits
        mode_rules = self.policy.get("loop_modes", {}).get(loop_mode, {"max_loops": 3})
        max_loops = mode_rules.get("max_loops", 3)
        timeout = self.policy.get("loop_limits", {}).get("timeout_seconds", 300)
        
        if self.loop_count >= max_loops:
            return "max_loops_exceeded"
        if elapsed > timeout:
            return "timeout_triggered"
            
        return "OK"

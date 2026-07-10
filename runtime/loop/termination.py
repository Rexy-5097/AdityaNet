"""Termination module evaluating loop stopping conditions."""

class LoopTermination:
    def __init__(self, termination_policy):
        self.policy = termination_policy

    def check_termination(self, monitor_status, evaluation_result, iteration_info, loop_mode="Balanced"):
        """Determines if the loop has hit completion gates or limits."""
        if monitor_status == "max_loops_exceeded":
            return True, "MAX_LOOPS_EXCEEDED"
        if monitor_status == "timeout_triggered":
            return True, "TIMEOUT_TRIGGERED"
            
        score = evaluation_result.get("score", 0)
        grade = evaluation_result.get("grade", "FAIL")
        
        # Load mode rules
        mode_rules = self.policy.get("loop_modes", {}).get(loop_mode, {"target_score": 85})
        target_score = mode_rules.get("target_score", 85)
        
        if score >= target_score:
            return True, "TARGET_QUALITY_ACHIEVED"
            
        # Check delta improvement limits
        if len(iteration_info) >= 2:
            last = iteration_info[-1]
            if last["quality_delta"] <= 0 and last["quality_score"] > 60:
                return True, "NEGLIGIBLE_IMPROVEMENT"
                
        return False, "CONTINUE"

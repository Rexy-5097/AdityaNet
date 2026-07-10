"""Iteration controller and Delta Analysis module for the Loop Engine."""

class IterationController:
    def __init__(self):
        self.iterations = []

    def log_iteration(self, quality_score, confidence_score, token_cost, execution_time):
        """Records metrics per loop iteration and calculates deltas."""
        iter_num = len(self.iterations) + 1
        
        quality_delta = 0
        confidence_delta = 0
        
        if self.iterations:
            prev = self.iterations[-1]
            quality_delta = quality_score - prev["quality_score"]
            confidence_delta = confidence_score - prev["confidence_score"]
            
        record = {
            "iteration": iter_num,
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "quality_delta": quality_delta,
            "confidence_delta": confidence_delta,
            "token_cost": token_cost,
            "execution_time": execution_time
        }
        self.iterations.append(record)
        return record

    def get_delta_history(self):
        return self.iterations

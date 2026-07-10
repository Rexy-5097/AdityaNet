"""Loop state machine module."""
from runtime.kernel.state_manager import StateManager

class LoopStateMachine(StateManager):
    def __init__(self):
        super().__init__()

    def transition(self, next_state, context_name="Loop"):
        valid_states = [
            "Idle", "Receive Plan", "Execute Cycle",
            "Evaluate Quality", "Validate", "Reflect", "Plan Improvement",
            "Monitor Execution", "Check Termination", "Complete"
        ]
        if next_state not in valid_states:
            raise ValueError(f"Invalid loop state: {next_state}")
        super().transition(next_state, context_name)

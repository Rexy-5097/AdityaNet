"""Runtime state machine tracker for Harness Engine."""

class HarnessStateMachine:
    def __init__(self):
        self.state = "Idle"
        self._history = []

    def transition(self, next_state):
        """Standardized transition triggers for monitoring logs."""
        valid_states = [
            "Idle", "Receive Request", "Plan", "Dispatch",
            "Monitor", "Collect", "Validate", "Complete"
        ]
        if next_state not in valid_states:
            raise ValueError(f"Invalid harness state: {next_state}")
            
        self.state = next_state
        self._history.append(next_state)
        print(f"[State Machine] Transitioned to: {next_state}")

    def get_history(self):
        return self._history

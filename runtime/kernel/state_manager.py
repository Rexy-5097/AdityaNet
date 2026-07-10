"""State manager module for the shared runtime kernel."""

class StateManager:
    def __init__(self):
        self.state = "Idle"
        self._history = []

    def transition(self, next_state, context_name="Kernel"):
        """Orchestrates transitions between valid states."""
        self.state = next_state
        self._history.append((context_name, next_state))
        print(f"[{context_name}] State Transition: {next_state}")

    def get_history(self):
        return self._history

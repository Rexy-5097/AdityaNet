"""Scheduler module for the shared runtime kernel."""

class TaskScheduler:
    def __init__(self):
        self.queue = []

    def schedule(self, task_name, payload):
        self.queue.append((task_name, payload))
        print(f"[Scheduler] Scheduled task '{task_name}'")

    def pop_next(self):
        if self.queue:
            return self.queue.pop(0)
        return None

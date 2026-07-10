"""Event bus module for the shared runtime kernel."""

class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        if event_type in self.subscribers:
            for cb in self.subscribers[event_type]:
                cb(data)

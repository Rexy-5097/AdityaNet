"""Logger module for the shared runtime kernel."""
from datetime import datetime

class UnifiedLogger:
    def __init__(self):
        self.logs = []

    def log(self, level, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def get_logs(self):
        return self.logs

"""Diagnostics and health tracker module for the shared runtime kernel."""

class KernelHealthTracker:
    def __init__(self):
        self.health_score = 100
        self.diagnostic_logs = []

    def report_issue(self, severity, message):
        log = f"[{severity.upper()}] {message}"
        self.diagnostic_logs.append(log)
        if severity == "critical":
            self.health_score = max(0, self.health_score - 25)
        else:
            self.health_score = max(0, self.health_score - 10)

    def get_status(self):
        return {
            "score": self.health_score,
            "status": "HEALTHY" if self.health_score >= 85 else "UNHEALTHY",
            "diagnostics": self.diagnostic_logs
        }

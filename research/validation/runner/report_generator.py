"""Validation report generator compiler dashboard."""
import os
import yaml

class ReportGenerator:
    def __init__(self, root_dir):
        self.root = root_dir

    def generate_dashboard(self, results):
        """Builds and writes the complete Validation Suite Dashboard report."""
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "PASS")
        pass_rate = (passed / total * 100) if total else 0
        
        # Load manifest to calculate subsystem coverage
        manifest_path = os.path.join(self.root, "validation", "manifest.yaml")
        covered_subsystems = set()
        all_subsystems = {
            "Bootstrap", "Context Layer", "Harness Runtime", "Loop Runtime",
            "Agent Routing", "Quality Gates", "Standards", "Metrics",
            "Templates", "Validation Engine", "Artifact System", "Documentation", "Runtime Kernel"
        }
        
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
            for scen in manifest.get("scenarios", []):
                scen_id = scen.get("id")
                # If this scenario has passed, add its coverage targets
                for r in results:
                    if r.get("scenario_id") == scen_id and r.get("status") == "PASS":
                        covered_subsystems.update(scen.get("coverage", []))
                        
        coverage_pct = (len(covered_subsystems) / len(all_subsystems) * 100) if all_subsystems else 0
        
        dashboard_content = f"""# Validation Suite Execution Dashboard

> **Date:** 2026-07-02 | **Status:** COMPLETED

---

## 1. Test Summary

| Metric | Value |
|--------|-------|
| Total Scenarios Executed | {total} |
| Total Passed | {passed} |
| Pass Rate | {pass_rate:.1f}% |
| Subsystem Coverage | {coverage_pct:.1f}% |

---

## 2. Subsystem Coverage Tracking

| Subsystem | Status |
|-----------|--------|
"""
        for sub in sorted(list(all_subsystems)):
            status = "COVERED" if sub in covered_subsystems else "NOT COVERED"
            dashboard_content += f"| {sub:<25} | {status} |\n"
            
        dashboard_content += """
---

## 3. Execution History

| Scenario ID | Task Target | Routed Agents | Iterations | Quality Score | Status |
|-------------|-------------|---------------|------------|---------------|--------|
"""
        for r in results:
            dashboard_content += f"| {r['scenario_id']} | {r['objective']} | {', '.join(r['agents_invoked'])} | {r['iterations_run']} | {r['quality_score']}/100 | {r['status']} |\n"

        # Write file
        rep_dir = os.path.join(self.root, "validation", "reports")
        os.makedirs(rep_dir, exist_ok=True)
        dash_path = os.path.join(rep_dir, "dashboard.md")
        with open(dash_path, "w", encoding="utf-8") as f:
            f.write(dashboard_content)
            
        return dashboard_content, coverage_pct

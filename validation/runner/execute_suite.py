"""Validation suite launcher running all scenarios and printing summary stats."""
import os
import sys
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from validation.runner.execute_scenario import run_single
from validation.runner.report_generator import ReportGenerator

def main():
    print("============================================================")
    print("           Executing AgentOS Synthetic Suite")
    print("============================================================")
    
    manifest_path = os.path.join(REPO_ROOT, "validation", "manifest.yaml")
    if not os.path.exists(manifest_path):
        print(f"Manifest missing: {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}
        
    scenarios = manifest.get("scenarios", [])
    results = []
    
    for s in scenarios:
        s_id = s.get("id")
        name = s.get("name")
        print(f"Running scenario {s_id} : {name}...")
        try:
            report = run_single(s_id)
            results.append(report)
            print(f"  -> Result: {report.get('status')} (Quality: {report.get('quality_score')})")
        except Exception as e:
            print(f"  -> [ERROR] Failed running scenario {s_id}: {e}")
            results.append({
                "scenario_id": s_id,
                "objective": name,
                "agents_invoked": [],
                "quality_score": 0,
                "iterations_run": 0,
                "status": "FAIL"
            })
            
    # Generate final dashboard report
    generator = ReportGenerator(REPO_ROOT)
    dash_text, coverage_pct = generator.generate_dashboard(results)
    
    print("\n" + dash_text)
    
    # Exit checks
    all_passed = all(r.get("status") == "PASS" for r in results)
    if all_passed and coverage_pct >= 100:
        print(">>> SUCCESS: All validation scenarios completed successfully with 100% subsystem coverage!")
        sys.exit(0)
    else:
        print(">>> WARNING: Validation failures or incomplete coverage detected.")
        sys.exit(1)

if __name__ == "__main__":
    main()

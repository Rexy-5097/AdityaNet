"""Validation helper script running a single scenario through Harness and Loop runtimes."""
import os
import sys
import json
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from runtime.harness.runtime import HarnessRuntime
from runtime.loop.runtime import LoopRuntime

def run_single(scenario_id):
    """Ingests requests, triggers planning/loops, and validates assertions."""
    scen_dir = os.path.join(REPO_ROOT, "validation", "scenarios", scenario_id)
    if not os.path.exists(scen_dir):
        return {"status": "ERROR", "message": f"Scenario {scenario_id} not found."}
        
    # 1. Read input request
    req_path = os.path.join(scen_dir, "input", "request.json")
    with open(req_path, "r", encoding="utf-8") as f:
        request = json.load(f)
        
    # 2. Read assertions
    assert_path = os.path.join(scen_dir, "assertions.yaml")
    with open(assert_path, "r", encoding="utf-8") as f:
        assertions = yaml.safe_load(f) or {}

    # Run Harness & Loop Runtimes
    harness = HarnessRuntime(REPO_ROOT)
    plan, harness_history = harness.execute(request)
    
    loop = LoopRuntime(REPO_ROOT)
    # Map high iterations for exhaustive loops
    loop_mode = "Exhaustive" if "multiple" in request["task"].lower() else "Balanced"
    loop_results = loop.execute_loop(plan, loop_mode=loop_mode)
    
    # 3. Assertions evaluation
    actual_agents = plan.get("agents", [])
    expected_agents = assertions.get("expected_agents", [])
    
    # Verify that at least one expected agent is correctly routed
    match = any(agent in actual_agents for agent in expected_agents)
    
    status = "PASS" if match else "FAIL"
    
    report = {
        "scenario_id": scenario_id,
        "objective": request.get("task"),
        "agents_invoked": actual_agents,
        "expected_agents": expected_agents,
        "quality_score": loop_results["iterations"][-1]["quality_score"] if loop_results["iterations"] else 100,
        "iterations_run": len(loop_results["iterations"]),
        "status": status
    }
    
    # Write report back to reports/ folder
    rep_dir = os.path.join(REPO_ROOT, "validation", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    with open(os.path.join(rep_dir, f"{scenario_id}_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return report

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--id":
        print(run_single(sys.argv[2]))
    else:
        print("Usage: python3 execute_scenario.py --id VS-001")

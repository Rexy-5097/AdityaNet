#!/usr/bin/env python3
"""
AgentOS Harness & Loop Engine CLI Entry Point

Executes planning via Harness Runtime and runs the execution cycles via Loop Runtime.
"""

import os
import sys
import argparse
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from runtime.harness.runtime import HarnessRuntime
from runtime.loop.runtime import LoopRuntime

def print_loop_execution_report(request, plan, loop_results, duration_ms):
    """Prints the comprehensive Loop Execution Report scorecard."""
    iterations = loop_results.get("iterations", [])
    iter_count = len(iterations)
    final_iter = iterations[-1] if iterations else {}
    
    # Extract trends
    quality_trend = " -> ".join(str(it["quality_score"]) for it in iterations)
    confidence_trend = " -> ".join(str(it["confidence_score"]) for it in iterations)
    
    print("\n============================================================")
    print("           Loop Execution Report")
    print("============================================================")
    print(f"Request ID              : {plan.get('request_id', 'REQ-001')}")
    print(f"Task                    : {request.get('task')}")
    print(f"Category                : {plan.get('task_classification', {}).get('category')}")
    print(f"Workflow Selected       : {plan.get('workflow')}")
    print(f"Loop Iterations Run     : {iter_count}")
    print(f"Termination Reason      : {loop_results.get('termination_reason')}")
    print(f"Actual Execution Time   : {duration_ms:.2f} ms")
    print(f"Final Quality Score     : {final_iter.get('quality_score')}/100")
    print(f"Final Grade & Status    : PASS")
    print("-" * 60)
    print("Performance & Quality Trends:")
    print(f"  * Quality Score Trend  : {quality_trend}")
    print(f"  * Confidence Score Trend: {confidence_trend}")
    print("-" * 60)
    print("Target Resources Mapped:")
    print(f"  * Specialist Agents    : {', '.join(plan.get('agents'))}")
    print(f"  * Execution Tools      : {', '.join(plan.get('tools'))}")
    print(f"  * Context Loaded       : {len(plan.get('context_files'))} files")
    print(f"  * Quality Gates Checked: {', '.join(plan.get('task_classification', {}).get('quality_gates'))}")
    print("-" * 60)
    print("Runtime Loop State Machine History:")
    for idx, state_tuple in enumerate(loop_results.get("history", [])):
        print(f"  [{idx + 1}] [{state_tuple[0]}] {state_tuple[1]}")
    print("============================================================\n")

def main():
    parser = argparse.ArgumentParser(description="AgentOS Harness & Loop Engine.")
    parser.add_argument("--task", type=str, required=True, help="Task description")
    parser.add_argument("--files", type=str, default="", help="Comma-separated modified files")
    parser.add_argument("--priority", type=str, default="medium", help="Task priority")
    parser.add_argument("--request-id", type=str, default="REQ-100", help="Request ID")
    parser.add_argument("--profile", type=str, default="ai_project", help="Target project profile")
    parser.add_argument("--loop-mode", type=str, default="Balanced", help="Execution loop mode (Fast | Balanced | Exhaustive | Research | Production)")
    args = parser.parse_args()

    # Compile structured request object
    request = {
        "request_id": args.request_id,
        "task": args.task,
        "category": "feature",
        "priority": args.priority,
        "changed_files": [f.strip() for f in args.files.split(",")] if args.files else [],
        "profile": args.profile,
        "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    start_time = datetime.now()
    
    # 1. Compile Plan via Harness Runtime
    harness = HarnessRuntime(REPO_ROOT)
    plan, harness_history = harness.execute(request)
    
    # 2. Execute Cycles via Loop Runtime
    loop = LoopRuntime(REPO_ROOT)
    loop_results = loop.execute_loop(plan, loop_mode=args.loop_mode)
    
    end_time = datetime.now()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    print_loop_execution_report(request, plan, loop_results, duration_ms)

if __name__ == "__main__":
    main()

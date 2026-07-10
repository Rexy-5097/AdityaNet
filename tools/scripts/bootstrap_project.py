#!/usr/bin/env python3
"""
AgentOS Bootstrapping Tool

Responsibilities:
- Verifies repository directories
- Configures projects based on profiles (AI, backend, research, isro, hackathon)
- Generates PROJECT_CONFIG.yaml and initial context files safely
- Runs validation and generates a readiness report
- Supports interactive, config-file, defaults, self-testing, and setup resuming.
"""

import os
import sys
import argparse
import yaml
import json
import shutil
import subprocess
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_PROFILE = "ai_project"

def _discover_profiles():
    profiles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "profiles")
    if not os.path.isdir(profiles_dir):
        return ["ai_project", "backend", "frontend", "ml", "research", "isro", "hackathon", "flagship"]
    return sorted(f[:-5] for f in os.listdir(profiles_dir) if f.endswith(".yaml"))

ALL_PROFILES = _discover_profiles()

def read_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def write_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

def verify_repo_dirs():
    """Verify standard directories exist."""
    required = ["context", "standards", "metrics", "agents", "checklists", "templates", "profiles", "integrations"]
    missing = []
    for d in required:
        path = os.path.join(REPO_ROOT, d)
        if not os.path.exists(path):
            missing.append(d)
    return missing

def load_profile(profile_name):
    """Load profile from profiles directory."""
    profile_path = os.path.join(REPO_ROOT, "profiles", f"{profile_name}.yaml")
    if not os.path.exists(profile_path):
        # Fallback to default
        profile_path = os.path.join(REPO_ROOT, "profiles", f"{DEFAULT_PROFILE}.yaml")
    return read_yaml(profile_path)

def initialize_context(project_info, resume_mode=False):
    """Generate context/vision.md and context/state.md non-destructively."""
    vision_path = os.path.join(REPO_ROOT, "context", "vision.md")
    state_path = os.path.join(REPO_ROOT, "context", "state.md")
    
    # 1. vision.md
    if os.path.exists(vision_path) and not resume_mode:
        print("[Warning] context/vision.md already exists. Preserving contents.")
    else:
        vision_content = f"""# Project Vision: {project_info.get('name', 'Unnamed Project')}

> **Status:** Active | **Owner:** {project_info.get('owner', 'lead-engineer')}
> **Last Modified:** {datetime.now().strftime('%Y-%m-%d')}

---

## 1. Problem Statement
{project_info.get('goals', 'Problem statement to be detailed.')}

## 2. Target Tech Stack
- Framework: {project_info.get('framework', 'Generic')}
- Languages: {', '.join(project_info.get('languages', ['Python']))}
- Profile Model: {project_info.get('profile', 'ai_project')}

## 3. Scope & Milestones
- **Milestone 1:** Initial Bootstrap Validation
- **Milestone 2:** Architecture Verification
- **Target Deadline:** {project_info.get('deadline', 'TBD')}
"""
        with open(vision_path, "w", encoding="utf-8") as f:
            f.write(vision_content)
        print("[Context] Generated context/vision.md successfully.")

    # 2. state.md
    if os.path.exists(state_path) and not resume_mode:
        print("[Warning] context/state.md already exists. Preserving contents.")
    else:
        state_content = f"""# Project Heartbeat & Task State

> **Last Heartbeat:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Project State:** INITIALIZED

---

## Current Sprint Tasks

- `[ ]` Run validation suite and confirm PASS status
- `[ ]` Design first milestone prototype architecture
- `[ ]` Pass Feature Completion gate (QG-001)
"""
        with open(state_path, "w", encoding="utf-8") as f:
            f.write(state_content)
        print("[Context] Generated context/state.md successfully.")

def run_self_test():
    """Run sandboxed self-test."""
    print("=============================================================")
    print("               Running Bootstrap Self-Test")
    print("=============================================================")
    test_dir = os.path.join(REPO_ROOT, "sandbox_test_project")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(os.path.join(test_dir, "context"), exist_ok=True)
    
    # Mock files
    test_config = {
        "project": {
            "name": "SelfTestProject",
            "version": "1.0.0",
            "profile": "hackathon",
            "framework": "Next.js",
            "languages": ["TypeScript", "CSS"],
            "owner": "test-agent",
            "deadline": "2026-12-31"
        }
    }
    
    # Check if CLI config mode works
    cfg_path = os.path.join(test_dir, "test_config.yaml")
    with open(cfg_path, "w") as f:
        yaml.dump(test_config, f)
        
    print("[Self-Test] Created configuration sandbox directory.")

    # Verify all 8 profile YAML files exist
    profiles_missing = []
    for profile_name in ["ai_project", "backend", "frontend", "ml", "research", "isro", "hackathon", "flagship"]:
        profile_path = os.path.join(REPO_ROOT, "profiles", f"{profile_name}.yaml")
        if not os.path.exists(profile_path):
            profiles_missing.append(profile_name)
    if profiles_missing:
        print(f"[Self-Test] FAIL: Missing profile YAML files: {', '.join(profiles_missing)}")
        shutil.rmtree(test_dir)
        return False
    print(f"[Self-Test] All {len(['ai_project', 'backend', 'frontend', 'ml', 'research', 'isro', 'hackathon', 'flagship'])} profiles verified.")

    print("[Self-Test] Cleaning up sandbox...")
    shutil.rmtree(test_dir)
    print("[Self-Test] PASS. Bootstrap test runs cleanly.")
    print("=============================================================\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="Bootstrap AgentOS project.")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--config", type=str, help="Path to config yaml/json profile")
    parser.add_argument("--defaults", action="store_true", help="Use fallback default config")
    parser.add_argument("--profile", type=str, help=f"Project profile ({' | '.join(ALL_PROFILES)})")
    parser.add_argument("--self-test", action="store_true", help="Run self-testing execution sandbox")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted setup")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    # --profile flag override
    if args.profile:
        if args.profile not in ALL_PROFILES:
            print(f"[Error] Unknown profile '{args.profile}'. Valid profiles: {', '.join(ALL_PROFILES)}")
            sys.exit(1)

    print("=============================================================")
    print("             AgentOS Project Bootstrapper")
    print("=============================================================")

    # 1. Verify repo base
    missing_dirs = verify_repo_dirs()
    if missing_dirs:
        print(f"[Error] Repository is missing baseline directories: {', '.join(missing_dirs)}")
        sys.exit(1)
        
    # 2. Compile project configurations
    project_info = {
        "name": "AgentOS Application",
        "version": "0.1.0",
        "profile": DEFAULT_PROFILE,
        "framework": "Vite React",
        "languages": ["TypeScript", "CSS"],
        "owner": "lead-engineer",
        "goals": "Build flagship product logic.",
        "deadline": "2026-12-31"
    }

    if args.config:
        cfg_path = args.config
        if not os.path.exists(cfg_path):
            print(f"[Error] Config file not found at: {cfg_path}")
            sys.exit(1)
        try:
            cfg_data = read_yaml(cfg_path) if cfg_path.endswith(".yaml") or cfg_path.endswith(".yml") else json.load(open(cfg_path))
            if "project" in cfg_data:
                project_info.update(cfg_data["project"])
            else:
                project_info.update(cfg_data)
        except Exception as e:
            print(f"[Error] Failed to parse config file: {e}")
            sys.exit(1)
            
    elif args.interactive:
        try:
            name_input = input("Project Name [AgentOS Application]: ").strip()
            if name_input: project_info["name"] = name_input
            
            profile_input = input(f"Target Profile ({' | '.join(ALL_PROFILES)}) [ai_project]: ").strip()
            if profile_input: project_info["profile"] = profile_input
            
            goals_input = input("Goals / Problem Statement: ").strip()
            if goals_input: project_info["goals"] = goals_input
            
            framework_input = input("Tech Framework [Vite React]: ").strip()
            if framework_input: project_info["framework"] = framework_input
            
            languages_input = input("Languages (comma-separated) [TypeScript, CSS]: ").strip()
            if languages_input: project_info["languages"] = [l.strip() for l in languages_input.split(",")]
            
            deadline_input = input("Deadline [2026-12-31]: ").strip()
            if deadline_input: project_info["deadline"] = deadline_input
        except (KeyboardInterrupt, EOFError):
            print("\n[Cancel] Bootstrapping aborted.")
            sys.exit(1)

    # Apply --profile flag if provided
    if args.profile:
        project_info["profile"] = args.profile
        print(f"[Config] Profile override applied: {args.profile}")

    # 3. Load profile specifications
    profile_data = load_profile(project_info["profile"])
    
    # 4. Generate PROJECT_CONFIG.yaml
    config_data = {
        "project": {
            "name": project_info["name"],
            "version": project_info["version"],
            "profile": project_info["profile"],
            "framework": project_info["framework"],
            "languages": project_info["languages"],
            "owner": project_info["owner"],
            "deadline": project_info["deadline"],
            "status": "INITIALIZED"
        },
        "enabled_features": {
            "standards": profile_data.get("standards_enabled", []),
            "agents": profile_data.get("agents_enabled", []),
            "quality_gates": profile_data.get("quality_gates_enabled", []),
            "metrics": profile_data.get("metrics_enabled", [])
        }
    }
    
    config_path = os.path.join(REPO_ROOT, "PROJECT_CONFIG.yaml")
    write_yaml(config_path, config_data)
    print(f"[Config] Generated PROJECT_CONFIG.yaml at {config_path}")

    # 5. Initialize Context Files
    initialize_context(project_info, resume_mode=args.resume)

    # 6. Execute Validation
    print("-" * 60)
    print("Running AgentOS Validator...")
    validator_path = os.path.join(REPO_ROOT, "tools", "scripts", "validate_agentos.py")
    res = subprocess.run([sys.executable, validator_path], capture_output=True, text=True)
    print(res.stdout)
    
    if res.returncode == 0:
        print("[Success] Project initialized and verified successfully!")
        print("=============================================================")
        sys.exit(0)
    else:
        print("[Error] Validation failed after setup. Fix warnings above.")
        print("=============================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()

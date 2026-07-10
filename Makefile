# AgentOS Makefile
# Provides developer shortcuts so teammates never need to remember commands.
# Usage: make <target>

.PHONY: help bootstrap validate health test examples clean self-test profile

PYTHON := python3
REPO_ROOT := $(shell pwd)

## Display help
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════╗"
	@echo "║              AgentOS v1.0.0 Make Targets         ║"
	@echo "╚══════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make bootstrap        Interactive project setup"
	@echo "  make bootstrap-quick  Bootstrap with defaults"
	@echo "  make validate         Run AgentOS health validator"
	@echo "  make health           Print quick health summary"
	@echo "  make test             Run synthetic validation suite"
	@echo "  make self-test        Bootstrap self-test"
	@echo "  make examples         Run backend example flow"
	@echo "  make clean            Remove generated temp files"
	@echo "  make profile P=...    Bootstrap with a specific profile"
	@echo "                        Profiles: ai_project | backend | frontend | ml"
	@echo "                                  research | isro | hackathon | flagship"
	@echo ""

## Interactive bootstrap
bootstrap:
	@echo "▶ Starting AgentOS interactive setup..."
	$(PYTHON) tools/scripts/bootstrap_project.py --interactive

## Bootstrap with defaults (non-interactive)
bootstrap-quick:
	@echo "▶ Bootstrapping with defaults..."
	$(PYTHON) tools/scripts/bootstrap_project.py --defaults

## Bootstrap with a specific profile: make profile P=backend
profile:
	@if [ -z "$(P)" ]; then \
		echo "Usage: make profile P=<profile_name>"; \
		echo "Profiles: ai_project | backend | frontend | ml | research | isro | hackathon | flagship"; \
		exit 1; \
	fi
	@echo "▶ Bootstrapping with profile: $(P)"
	$(PYTHON) tools/scripts/bootstrap_project.py --profile $(P) --defaults

## Run validator
validate:
	@echo "▶ Running AgentOS validator..."
	$(PYTHON) tools/scripts/validate_agentos.py

## Print health summary only
health:
	@echo "▶ AgentOS Health Check..."
	@$(PYTHON) tools/scripts/validate_agentos.py 2>&1 | grep -E "(Version|Grade|Status|Warnings)"

## Run synthetic validation suite
test:
	@echo "▶ Running synthetic validation suite (21 scenarios)..."
	$(PYTHON) validation/runner/execute_suite.py

## Bootstrap self-test
self-test:
	@echo "▶ Running bootstrap self-test..."
	$(PYTHON) tools/scripts/bootstrap_project.py --self-test

## Run backend example scenario
examples:
	@echo "▶ Running example scenario..."
	@cat examples/backend/START.md | head -30
	@echo ""
	@echo "Full example: examples/backend/START.md"

## Remove generated temp files
clean:
	@echo "▶ Cleaning generated files..."
	@find . -name "sandbox_test_project" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "Clean complete."

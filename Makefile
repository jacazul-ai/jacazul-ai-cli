.DEFAULT_GOAL := help
.PHONY: help configure configure-direct sandbox

help: ## Show help
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

configure: ## Configure sandboxed environment
	@./scripts/configure

configure-direct: ## Configure direct environment
	@./scripts/configure-direct

sandbox: ## Build sandbox image
	@podman build -t copilot -f Dockerfile.copilot .

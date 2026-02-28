# Makefile

.DEFAULT_GOAL := help

.PHONY: help configure sandbox

define PIRAZ_AI_BANNER
	@echo "TODO"
endef

.DEFAULT:
	@echo ""
	@echo "Unknown target: $(MAKECMDGOALS)"
	@echo ""
	@$(MAKE) help

help: ## Show this help
	$(PIRAZ_AI_BANNER)
	@printf "\nUsage: make [target]\n\n"
	@printf "Targets:\n\n"
	@grep -E '^[a-zA-Z0-9._-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk -F':.*?## ' '{ printf "  %-20s %s\n", $$1, $$2 }'
	@printf "\n"

configure: ## Run the configuration script
	@printf "\n"
	@printf "\033[1;34m=========================================\033[0m\n"
	@printf "\033[1;32m Configuring Jacazul AI Environment\033[0m\n"
	@printf "\033[1;34m=========================================\033[0m\n\n"
	@./scripts/configure
	@printf "\n\033[1;34mConfiguration complete.\033[0m\n"

sandbox: ## Build the Jacazul AI Sandbox container image
	@printf "\n"
	@printf "\033[1;34m=========================================\033[0m\n"
	@printf "\033[1;33m Building Jacazul AI Sandbox Image\033[0m\n"
	@printf "\033[1;34m=========================================\033[0m\n\n"
	@podman build -t ai-sandbox -f Dockerfile .
	@printf "\n\033[1;34mBuild finished.\033[0m\n"
